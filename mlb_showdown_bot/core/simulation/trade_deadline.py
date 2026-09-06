from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Optional

from .models import DeadlineTrade, SeasonSimulationConfig
from .stats import real_card_id

if TYPE_CHECKING:
    from .schedule import Schedule
    from .season import SeasonCardPool
    from .standings import Standings
    from .team import SimTeam


# A GENUINELY MID-SEASON STINT. FEWER REAL GAMES THAN THIS FOR *EITHER* THE ORIGIN OR THE
# DESTINATION CLUB AND THE PLAYER IS TREATED AS A SPRING-TRAINING / SEPTEMBER-CALLUP move - PINNED
# WHOLE TO HIS PRIMARY CLUB WITH NO DEADLINE TRADE. SCALED DOWN FOR SHORT REAL SEASONS, MIRRORING
# THE RESERVE SAMPLE-SIZE FLOORS IN `roster.py`.
_MIN_STINT_GAMES = 10

# GAMES BACK OF A PLAYOFF SPOT AT WHICH A SELLING CLUB STILL COUNTS AS "CONTENDING" AND (WHEN THE
# STANDINGS GATE IS ON) HOLDS ITS PLAYER RATHER THAN MAKING THE REAL TRADE.
_CONTENTION_GB = 8.0


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


@dataclass
class PendingMove:
    """One scheduled origin -> destination relocation, resolved to schedule keys and the id the
    player carries on the origin roster."""

    sim_player_id: str   # SimPlayer.id ON THE ORIGIN ROSTER (== card_bot.card_id FOR A REAL PLAYER)
    player_id: str       # ARCHIVE PLAYER ID ('{year}-{bref_id}'), FOR LOGGING
    origin: str          # SCHEDULE KEY
    destination: str     # SCHEDULE KEY


@dataclass
class TradeDeadlinePlan:
    # ShowdownPlayerCard.id -> SCHEDULE KEY TO ROSTER THE CARD UNDER AT SEASON START, OVERRIDING
    # `card.team`. COVERS BOTH TRADED PLAYERS (-> ORIGIN CLUB) AND NO-MOVE REASSIGNMENTS
    # (-> PRIMARY CLUB) SO A MULTI-TEAM PLAYER NEVER STARTS ON THE WRONG CLUB.
    initial_team_by_card_id: dict[str, str]
    pending_moves: list[PendingMove]


class TradeDeadline:
    """Relocates real mid-season acquisitions on an era-appropriate deadline date.

    Constructed only when `config.enable_trade_deadline`. The plan is computed up front from each
    multi-team player's archived club history (`SeasonCardPool.team_history`): which club he starts
    on, and whether a deadline move is scheduled. `apply()` performs the surviving moves once,
    mid-loop, mutating the live `SimTeam`s.

    Fully deterministic - no rng is touched and players are processed in a fixed (sorted) order, so
    a seeded run stays reproducible. Season stat totals are unaffected: one card, one statline that
    simply accrues on whichever club the player is on at the time.
    """

    def __init__(self, config: SeasonSimulationConfig, schedule: 'Schedule', card_pool: 'SeasonCardPool') -> None:
        self.config = config
        self.deadline_date = self.deadline_date_for(config.year)
        real_games = (schedule.original_games_per_team or 162)
        self._min_stint = max(1, round(_MIN_STINT_GAMES * min(1.0, real_games / 162.0)))
        self.plan = self._build_plan(schedule, card_pool)
        self.applied = False

    @staticmethod
    def deadline_date_for(year: int) -> date:
        """Era-approximate non-waiver trade deadline. Pre-1986 it fell in mid-June; July 31 ever
        since. The 1986-2019 August waiver-trade window is not modelled."""
        return date(year, 6, 15) if year <= 1985 else date(year, 7, 31)

    # ------------------------------------------------------------------
    # PLANNING
    # ------------------------------------------------------------------

    def _build_plan(self, schedule: 'Schedule', card_pool: 'SeasonCardPool') -> TradeDeadlinePlan:
        valid_clubs = set(schedule.unique_team_names)
        takeover_clubs = set(self.config.all_takeovers.keys())
        initial: dict[str, str] = {}
        moves: list[PendingMove] = []

        for player_id, (team_list, games) in sorted(card_pool.team_history.items()):
            card = card_pool.cards_by_player_id.get(player_id)
            if card is None:
                continue

            clubs = [club for club in _dedupe(team_list) if club in valid_clubs]
            if len(clubs) < 2:
                continue
            origin, destination = clubs[0], clubs[-1]
            if origin == destination or origin in takeover_clubs or destination in takeover_clubs:
                continue

            card_team = card.team.value if card.team else None
            primary = max(games, key=games.get) if games else destination

            # NOT A REAL MID-SEASON SPLIT (CUP OF COFFEE, SEPTEMBER CALLUP THEN DEALT, SPRING-
            # TRAINING TRADE): PIN HIM TO HIS PRIMARY CLUB FOR THE WHOLE SIM, NO TRADE.
            if games.get(origin, 0) < self._min_stint or games.get(destination, 0) < self._min_stint:
                if primary in valid_clubs and primary != card_team:
                    initial[card.id] = primary
                continue

            initial[card.id] = origin
            moves.append(PendingMove(
                sim_player_id=card_pool.archive_card_ids.get(card.id, card.id),
                player_id=player_id,
                origin=origin,
                destination=destination,
            ))

        return TradeDeadlinePlan(initial_team_by_card_id=initial, pending_moves=moves)

    # ------------------------------------------------------------------
    # APPLYING
    # ------------------------------------------------------------------

    def apply(self, standings: 'Standings', teams: dict[str, 'SimTeam'], game_date: date) -> list[DeadlineTrade]:
        """Perform every scheduled move whose selling club isn't held back by the standings gate.
        Idempotent - `applied` is set on the first call and callers check it before invoking."""
        self.applied = True
        trades: list[DeadlineTrade] = []
        gate = self.config.trade_deadline_respects_standings

        for move in self.plan.pending_moves:
            origin = teams.get(move.origin)
            destination = teams.get(move.destination)
            if origin is None or destination is None:
                continue
            if gate and self._is_contending(standings, move.origin):
                continue

            player = origin.release_player(move.sim_player_id)
            if player is None:
                continue  # ON THE IL, OR NOT ON THE ACTIVE ROSTER/RESERVES - LEAVE HIM PUT
            from_record = f"{origin.wins}-{origin.losses}"
            to_record = f"{destination.wins}-{destination.losses}"
            destination.acquire_player(player)

            trades.append(DeadlineTrade(
                date=game_date,
                player_id=real_card_id(player.id),
                player_name=player.name,
                position=player.primary_position.value if player.positions_list else "",
                player_type=player.player_type.value,
                from_team=move.origin,
                to_team=move.destination,
                from_team_record=from_record,
                to_team_record=to_record,
            ))

        return trades

    def _is_contending(self, standings: 'Standings', abbr: str, threshold: float = _CONTENTION_GB) -> bool:
        """Within `threshold` games of the best record in the club's own league - a deliberately
        simple proxy for "still in a race". Being the league's best is `games_back` 0, i.e.
        contending. A club with no resolvable league is compared against the whole field."""
        team = standings.teams.get(abbr)
        if team is None:
            return False

        league = standings.team_leagues.get(abbr)
        league_clubs = [
            club for clubs_by_abbr in standings.divisions_dict.values() for club in clubs_by_abbr.values()
            if league is None or standings.team_leagues.get(club.name) == league
        ] or list(standings.teams.values())

        leader = max(league_clubs, key=lambda t: (t.win_pct, t.wins))
        games_back = (abs(leader.wins - team.wins) + abs(leader.losses - team.losses)) / 2.0
        return games_back <= threshold
