from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from ..shared.player_position import Position, PositionSlot, PositionSlotParent
from .inning import Inning
from .player import SimPitcher, SimPlayer
from .stats import PitchingLog


class PositionEligibility:
    """Position-slot eligibility checks shared by roster construction (`roster.py`) and lineup
    filling (`SimTeam.fill_starting_position_players`). `PositionSlot.BE` is always excluded -
    the sim tracks bench status via roster membership, not a lineup slot.
    """

    @staticmethod
    def players_for_slot(players: list[SimPlayer], position_slot: PositionSlot, excluded_player_ids: Optional[list[str]] = None) -> list[SimPlayer]:
        excluded_player_ids = excluded_player_ids or []
        valid_positions = position_slot.valid_positions
        players_eligible_for_position = []
        for player in players:
            if player.id in excluded_player_ids:
                continue
            for pos in player.positions_and_defense.keys():
                if pos in valid_positions:
                    players_eligible_for_position.append(player)
                    continue
        return players_eligible_for_position

    @staticmethod
    def counts_by_slot(players: list[SimPlayer], current_lineup_dict: Optional[dict[str, PositionSlot]] = None) -> dict[PositionSlot, float]:
        current_lineup_dict = current_lineup_dict or {}
        positions_and_count = {}
        position_slots = [
            slot for slot in PositionSlot
            if slot.is_position_player and slot != PositionSlot.BE and slot not in current_lineup_dict.values()
        ]
        outfielders_filled = len([filled_pos for filled_pos in current_lineup_dict.values() if filled_pos.is_outfield])

        for slot in position_slots:
            players_w_eligibility_list = PositionEligibility.players_for_slot(players=players, position_slot=slot, excluded_player_ids=list(current_lineup_dict.keys()))
            players_w_eligibility = len(players_w_eligibility_list)
            if slot.is_outfield:
                players_w_eligibility = 1.1 if (3 - outfielders_filled) == players_w_eligibility else players_w_eligibility
            positions_and_count[slot] = players_w_eligibility
        return positions_and_count

    @staticmethod
    def uncovered_slots(players: list[SimPlayer]) -> list[PositionSlot]:
        """Position slots (of the 8 defensive spots) with zero eligible players in the given pool."""
        defensive_slots = [PositionSlot.CA, PositionSlot._1B, PositionSlot._2B, PositionSlot._3B, PositionSlot.SS, PositionSlot.LF, PositionSlot.CF, PositionSlot.RF]
        return [slot for slot in defensive_slots if len(PositionEligibility.players_for_slot(players=players, position_slot=slot)) == 0]


class PlayerGroup(BaseModel):

    players: list[SimPlayer]
    category: PositionSlotParent = PositionSlotParent.NONE

    def player_by_id(self, player_id: str) -> Optional[SimPlayer]:
        return next((p for p in self.players if p.id == player_id), None)

    def players_for_team(self, team: str) -> list[SimPlayer]:
        return [p for p in self.players if p.team == team]


class Bullpen(PlayerGroup):

    players: list[SimPitcher]
    pitching_log: PitchingLog = Field(default_factory=PitchingLog)
    closer_id: Optional[str] = None            # EXPLICIT CLOSER FROM BUILDER TEAM "CP" ROLE
    role_order: dict[str, int] = {}            # OPTIONAL EXPLICIT BULLPEN RANKING FROM BUILDER ROLES (SU < MR < LONG)
    _closer: Optional[SimPitcher] = None       # RESOLVED ONCE, SEE `closer`

    def __init__(self, **data) -> None:
        data['category'] = PositionSlotParent.BULLPEN
        super().__init__(**data)

    @property
    def closer(self) -> SimPitcher:
        """The bullpen's closer. Fixed once the roster is built, so it's resolved lazily and cached."""
        if self._closer is None:
            explicit_closer = self.player_by_id(self.closer_id) if self.closer_id else None
            if explicit_closer:
                self._closer = explicit_closer
            else:
                closers = [p for p in self.players if p.has_position(Position.CL)]
                self._closer = sorted(closers if len(closers) > 0 else self.players, key=lambda x: x.points, reverse=True)[0]
        return self._closer

    @property
    def setup_man(self) -> SimPitcher:
        return self.reliever(0)

    def reliever(self, index: int) -> Optional[SimPitcher]:
        if index > ( len(self.players) - 1 ):
            return None

        return sorted([p for p in self.players if p != self.closer], key=lambda x: (x.points, x.chart.command), reverse=True)[index]

    def pitchers_available(self, game_date: date, reverse_sort = False, available_ids: Optional[set[str]] = None) -> list[SimPitcher]:
        """Ordered list of pitchers not used in game yet. Best pitchers first (lowest opponent OPS).

        Args:
          available_ids: Pre-computed rest-eligible pitcher ids. Bullpen availability only changes
            between games, so callers compute this once per game rather than per plate appearance.
        """

        if available_ids is None:
            # REMOVE PITCHERS USED RECENTLY
            unavailable = self.pitching_log.pitcher_ids_with_recent_workload(game_date=game_date, days_back=2, ip_cutoff=2)
            available_ids = {p.id for p in self.players if p.id not in unavailable}

        available = [pitcher for pitcher in self.players if (pitcher.start_inning is None and pitcher.id in available_ids)]

        def sort_key(pitcher: SimPitcher):
            if self.role_order:
                return (self.role_order.get(pitcher.id, 99), pitcher.projected.get('onbase_plus_slugging', 0))
            return (pitcher.projected.get('onbase_plus_slugging', 0), -1 * pitcher.chart.command)

        return sorted(available, key=sort_key, reverse=reverse_sort)

    def suggested_reliever(self, game_date: date, inning: Inning, runs_scored: int, runs_allowed: int, available_ids: Optional[set[str]] = None) -> Optional[SimPitcher]:
        """ Uses context of the game situation to suggest which reliever is the best fit. """

        # CHECK IF THERE ARE AVAILABLE RELIEVERS
        available_pitchers = self.pitchers_available(game_date=game_date, available_ids=available_ids)
        num_available_pitchers = len(available_pitchers)
        if num_available_pitchers == 0:
            return None

        # DEFINE VARIABLES USED IN ALGORITHM
        is_closer_available = self.closer in available_pitchers
        run_diff = runs_scored - runs_allowed
        is_save_situation = inning.inning >= 9 and runs_scored >= runs_allowed and run_diff >= 0

        # --- CLOSER ---
        # PLAY THE CLOSER WHEN IT'S THE 9TH INNING AND IT'S A SAVE SITUATION OR HOLD SITUATION
        if is_save_situation and is_closer_available:
            return self.closer

        # SCORE EACH CANDIDATE ONCE RATHER THAN RE-DERIVING INSIDE THE SORT COMPARATOR
        recent_ip = self.pitching_log.recent_ip_by_pitcher(game_date=game_date, days_back=3)
        closer = self.closer
        scored = [
            (
                pitcher.situational_fit(
                    ops_index=index, total_pitchers=num_available_pitchers, run_diff=run_diff,
                    inning=inning.inning, recent_ip=recent_ip.get(pitcher.id, 0.0),
                    is_save_situation=is_save_situation, is_closer=closer is pitcher,
                ),
                index,
                pitcher,
            )
            for index, pitcher in enumerate(available_pitchers)
        ]
        # HIGHEST FIT WINS; INDEX BREAKS TIES SO ORDERING STAYS DETERMINISTIC
        return max(scored, key=lambda t: (t[0], -t[1]))[2]

    def remove_player(self, player_id: str) -> Optional[SimPitcher]:
        """Remove a pitcher from the bullpen (e.g. for an IL move). Invalidates the cached closer."""
        removed = self.player_by_id(player_id)
        if removed is None:
            return None
        self.players = [p for p in self.players if p.id != player_id]
        if self.closer_id == player_id:
            self.closer_id = None
        self._closer = None
        return removed

    def add_player(self, pitcher: SimPitcher) -> None:
        """Add a pitcher to the bullpen (e.g. a callup). Invalidates the cached closer."""
        self.players.append(pitcher)
        self._closer = None


class Rotation(PlayerGroup):

    players: list[SimPitcher]
    pitcher_index: int = 0

    def __init__(self, **data) -> None:
        data['category'] = PositionSlotParent.ROTATION
        super().__init__(**data)

    def move_to_next_pitcher_index(self) -> None:
        num_pitchers = len(self.players)
        self.pitcher_index = 0 if self.pitcher_index == (num_pitchers - 1) else (self.pitcher_index + 1)

    @property
    def current_pitcher(self) -> SimPitcher:
        return self.players[self.pitcher_index]

    def index_for_id(self, player_id: str) -> Optional[int]:
        for index, pitcher in enumerate(self.players):
            if pitcher.id == player_id:
                return index
        return None

    def replace_at_index(self, index: int, pitcher: SimPitcher) -> SimPitcher:
        """Swap the pitcher at a rotation slot in place and return the one replaced.

        `pitcher_index` is a positional round robin advanced once per team-game in
        `SimTeam.finalize_stats_post_game` - removing an element from `players` would silently
        shift every subsequent starter's turn, so rotation moves must always replace in place.
        """
        replaced = self.players[index]
        self.players[index] = pitcher
        return replaced
