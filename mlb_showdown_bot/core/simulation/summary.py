from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from ..shared.player_position import PlayerSubType, PlayerType
from .models import SeasonSimulationResult, SimTeamIdentity, StandingsResult, TeamRecord
from .reporting import HITTER_CATEGORIES, PITCHER_CATEGORIES
from .stats import StatCategory, Stats

# LEADERBOARD DEPTH. SMALL ON PURPOSE - THE FULL 1100-PLAYER `player_stats` LIST IS ~390 KB AND
# THE RESULT SCREEN ONLY EVER SHOWS A TOP TEN.
_LEADERBOARD_LIMIT = 10

# (STAT, IS_DESC) PER LEADERBOARD - KEYS PlayerSubType.value IN THE BUILT `top_players` DICT.
_LEADERBOARD_STATS: dict[PlayerSubType, tuple[str, bool]] = {
    PlayerSubType.POSITION_PLAYER: ('ops', True),
    PlayerSubType.STARTING_PITCHER: ('era', False),
    PlayerSubType.RELIEF_PITCHER: ('era', False),
}


class SimStatLine(BaseModel):
    """A statline with its rate stats already computed.

    `Stats` derives BA/OBP/SLG/OPS/ERA/WHIP as Python properties and OPS+/wRC+ as methods
    needing league context, so none of them survive `model_dump()`. Materializing here is what
    keeps the frontend from having to reimplement wOBA math.
    """

    id: str
    name: str
    team: Optional[str] = None
    position: Optional[str] = None
    points: int = 0
    command: float = 0
    player_type: Optional[str] = None
    stats: dict[str, float] = {}

    @classmethod
    def build(cls, stats: Stats, categories: list[StatCategory], league_stats: Optional[Stats], woba_weights: dict[str, float]) -> 'SimStatLine':
        values: dict[str, float] = {}
        for category in categories:
            value = stats.stat(category, league_stats=league_stats, woba_weights=woba_weights, combine_1b_and_1b_plus=True)
            if isinstance(value, (int, float)):
                values[category.value] = round(float(value), 3)
        return cls(
            id=stats.id, name=stats.name, team=stats.team, position=stats.position,
            points=stats.points, command=stats.command,
            player_type=stats.player_type.value if stats.player_type else None,
            stats=values,
        )


class SimGameLine(BaseModel):
    """One of the team's games, trimmed to what a schedule/streak view needs.

    Linescores and box scores are dropped - they are 3.2 MB of the 6.1 MB result and nothing on
    the season screen reads them.
    """

    date: str
    opponent: str
    opponent_identity: Optional[SimTeamIdentity] = None
    is_home: bool
    runs_scored: int
    runs_allowed: int
    is_win: bool
    wins: int      # RUNNING RECORD AFTER THIS GAME - BACKS THE 162-0 STREAK CHART
    losses: int


class SimSeriesLine(BaseModel):
    """A postseason series without its games."""

    round: str
    league: Optional[str] = None
    home_team: str
    away_team: str
    home_team_wins: int = 0
    away_team_wins: int = 0
    winner: Optional[str] = None


class SimTeamSeason(BaseModel):
    """How the user's team finished."""

    identity: Optional[SimTeamIdentity] = None
    replaced_abbr: Optional[str] = None
    wins: int = 0
    losses: int = 0
    win_pct: float = 0.0
    points: int = 0
    division: Optional[str] = None
    division_rank: Optional[int] = None
    division_size: Optional[int] = None
    games_back: Optional[float] = None
    playoff_seeding: Optional[int] = None
    made_playoffs: bool = False
    is_champion: bool = False
    longest_win_streak: int = 0
    longest_losing_streak: int = 0


class SeasonSimSummary(BaseModel):
    """Everything the season result screen renders, and nothing else.

    Built in the worker straight after `simulate()` so the full ~6 MB `SeasonSimulationResult`
    can be freed and only this (~100 KB) is ever persisted.
    """

    # META
    year: int
    set: str
    seed: Optional[int] = None
    runtime_seconds: float = 0.0
    schedule_length: int = 0
    original_schedule_length: int = 0
    generated_at: datetime

    team: SimTeamSeason
    games: list[SimGameLine] = []
    players: list[SimStatLine] = []

    standings: StandingsResult
    postseason: list[SimSeriesLine] = []
    champion: Optional[str] = None

    # SCHEDULE KEY -> BRANDING, FOR EVERY TEAM IN THE LEAGUE. STANDINGS ROWS, GAME OPPONENTS AND
    # POSTSEASON SERIES ALL REFER TO TEAMS BY SCHEDULE KEY, WHICH FOR THE TAKEOVER TEAM IS THE
    # CLUB IT REPLACED - THIS IS HOW THE UI RESOLVES ANY OF THEM BACK TO A NAME AND COLORS.
    identities: dict[str, SimTeamIdentity] = {}

    # KEYED BY PlayerSubType.value ('position_player' / 'starting_pitcher' / 'relief_pitcher').
    top_players: dict[str, list[SimStatLine]] = {}

    # SIM vs REAL LEAGUE AVERAGES. EMPTY WHEN THE SEASON HAS NO REAL BASELINE.
    league_totals: dict[str, SimStatLine] = {}
    real_league_averages: dict[str, SimStatLine] = {}


class SeasonSummaryBuilder:
    """Projects a `SeasonSimulationResult` down to the fields the result screen needs.

    The parallel of `SeasonReport`, which can only print. Column sets are shared with it so the
    web tables and the CLI tables never drift.
    """

    def __init__(self, result: SeasonSimulationResult, team_abbr: str) -> None:
        self.result = result
        self.team_abbr = team_abbr  # SCHEDULE KEY OF THE TEAM THE SUMMARY IS CENTERED ON

    @property
    def roster_player_ids(self) -> Optional[set[str]]:
        """Player ids on a takeover team's roster.

        Statlines report the builder team's own abbreviation, which is deliberately not the
        schedule key the takeover runs under, so matching on team would find nothing here.
        Roster slot `card_id`s are the ids `from_builder_team` assigns its players, so membership
        is the exact filter. None for a plain season sim, where matching on team is correct.
        """
        takeover_team = self.result.config.takeover_team
        if takeover_team is None:
            return None
        return {slot.card_id for slot in takeover_team.roster}

    def build(self) -> SeasonSimSummary:
        result = self.result
        record, division, rank, size = self._find_record()
        games = self._build_games()
        postseason = self._build_postseason()

        return SeasonSimSummary(
            year=result.config.year,
            set=result.config.set.value,
            seed=result.config.seed,
            runtime_seconds=round(result.runtime_seconds, 1),
            schedule_length=result.schedule_length,
            original_schedule_length=result.original_schedule_length,
            generated_at=result.ended_at,
            team=self._build_team_season(record, division, rank, size, games, postseason),
            games=games,
            players=self._build_players(),
            standings=result.standings,
            postseason=postseason,
            identities=self._build_identities(),
            champion=result.postseason.world_series_winner if result.postseason else None,
            top_players={sub_type.value: self._leaderboard(sub_type) for sub_type in PlayerSubType},
            league_totals=self._league_lines(result.league_totals),
            real_league_averages=self._league_lines(result.real_league_averages),
        )

    # ------------------------------------------------------------------
    # TEAM
    # ------------------------------------------------------------------

    def _build_identities(self) -> dict[str, SimTeamIdentity]:
        return {
            record.name: record.identity
            for records in self.result.standings.divisions.values()
            for record in records
            if record.identity is not None
        }

    def _find_record(self) -> tuple[Optional[TeamRecord], Optional[str], Optional[int], Optional[int]]:
        """The team's standings row plus where it finished in its division."""
        for division, records in self.result.standings.divisions.items():
            for index, record in enumerate(records):
                if record.name == self.team_abbr:
                    return record, division, index + 1, len(records)
        return None, None, None, None

    def _build_team_season(self, record: Optional[TeamRecord], division: Optional[str], rank: Optional[int], size: Optional[int], games: list[SimGameLine], postseason: list[SimSeriesLine]) -> SimTeamSeason:
        postseason_teams = {
            team
            for series in postseason
            for team in (series.home_team, series.away_team)
        }
        champion = self.result.postseason.world_series_winner if self.result.postseason else None
        wins, losses = self._longest_streaks(games)

        if record is None:
            return SimTeamSeason(replaced_abbr=self.team_abbr, longest_win_streak=wins, longest_losing_streak=losses)

        return SimTeamSeason(
            identity=record.identity,
            replaced_abbr=self.team_abbr,
            wins=record.wins,
            losses=record.losses,
            win_pct=record.win_pct,
            points=record.points,
            division=division,
            division_rank=rank,
            division_size=size,
            games_back=record.games_back,
            playoff_seeding=record.playoff_seeding,
            made_playoffs=self.team_abbr in postseason_teams,
            is_champion=champion == self.team_abbr,
            longest_win_streak=wins,
            longest_losing_streak=losses,
        )

    @staticmethod
    def _longest_streaks(games: list[SimGameLine]) -> tuple[int, int]:
        best_win = best_loss = run = 0
        last: Optional[bool] = None
        for game in games:
            run = run + 1 if game.is_win == last else 1
            last = game.is_win
            if game.is_win:
                best_win = max(best_win, run)
            else:
                best_loss = max(best_loss, run)
        return best_win, best_loss

    # ------------------------------------------------------------------
    # GAMES
    # ------------------------------------------------------------------

    def _build_games(self) -> list[SimGameLine]:
        lines: list[SimGameLine] = []
        wins = losses = 0
        for game in self.result.games:
            is_home = game.home_team == self.team_abbr
            if not is_home and game.away_team != self.team_abbr:
                continue
            scored = game.home_score if is_home else game.away_score
            allowed = game.away_score if is_home else game.home_score
            is_win = scored > allowed
            wins, losses = (wins + 1, losses) if is_win else (wins, losses + 1)
            lines.append(SimGameLine(
                date=str(game.date),
                opponent=game.away_team if is_home else game.home_team,
                opponent_identity=game.away_team_identity if is_home else game.home_team_identity,
                is_home=is_home,
                runs_scored=scored,
                runs_allowed=allowed,
                is_win=is_win,
                wins=wins,
                losses=losses,
            ))
        return lines

    # ------------------------------------------------------------------
    # STATS
    # ------------------------------------------------------------------

    def _categories(self, player_type: PlayerType) -> list[StatCategory]:
        return HITTER_CATEGORIES if player_type == PlayerType.HITTER else PITCHER_CATEGORIES

    def _line(self, stats: Stats, player_type: PlayerType) -> SimStatLine:
        return SimStatLine.build(
            stats=stats,
            categories=self._categories(player_type),
            league_stats=self.result.league_totals.get(player_type.value),
            woba_weights=self.result.woba_weights,
        )

    def _build_players(self) -> list[SimStatLine]:
        """Only the team's own players - the other 29 clubs' statlines are dropped."""
        roster_ids = self.roster_player_ids
        on_team = (
            (lambda stats: stats.id in roster_ids) if roster_ids is not None
            else (lambda stats: stats.team == self.team_abbr)
        )
        lines = [
            self._line(stats, stats.player_type)
            for stats in self.result.player_stats
            if stats.player_type is not None and on_team(stats)
        ]
        return sorted(lines, key=lambda line: (line.player_type or '', -line.points))

    def _leaderboard(self, player_sub_type: PlayerSubType) -> list[SimStatLine]:
        player_type = player_sub_type.parent_type
        stat, is_desc = _LEADERBOARD_STATS[player_sub_type]
        min_ip = 0
        if player_type == PlayerType.PITCHER:
            min_ip = self.result.stats_min_ip_rp if player_sub_type == PlayerSubType.RELIEF_PITCHER else self.result.stats_min_ip
        leaders = self.result.top_players(
            player_type=player_type.value, stat=stat, limit=_LEADERBOARD_LIMIT, is_desc=is_desc,
            min_pa=self.result.stats_min_pa if player_type == PlayerType.HITTER else 0,
            min_ip=min_ip, player_sub_type=player_sub_type,
        )
        return [self._line(stats, player_type) for stats in leaders]

    def _league_lines(self, totals: dict[str, Stats]) -> dict[str, SimStatLine]:
        lines: dict[str, SimStatLine] = {}
        for type_value, stats in totals.items():
            try:
                player_type = PlayerType(type_value)
            except ValueError:
                continue
            lines[type_value] = self._line(stats, player_type)
        return lines

    # ------------------------------------------------------------------
    # POSTSEASON
    # ------------------------------------------------------------------

    def _build_postseason(self) -> list[SimSeriesLine]:
        if self.result.postseason is None:
            return []
        return [
            SimSeriesLine(
                round=round_value,
                league=series.league,
                home_team=series.home_team,
                away_team=series.away_team,
                home_team_wins=series.home_team_wins,
                away_team_wins=series.away_team_wins,
                winner=series.winner,
            )
            for round_value, series_list in self.result.postseason.rounds.items()
            for series in series_list
        ]
