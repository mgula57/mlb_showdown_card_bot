from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from ..card.sets import Set
from ..card.team_builder.team import Team as BuilderTeam
from ..shared.player_position import PositionSlotParent
from .stats import Stats


class PostseasonRound(Enum):
    WILDCARD = "WC"
    DIVISIONAL = "DIV"
    CHAMPIONSHIP = "CS"
    WORLD_SERIES = "WS"

    @property
    def next_round(self) -> Optional['PostseasonRound']:
        match self.value:
            case "WC": return PostseasonRound.DIVISIONAL
            case "DIV": return PostseasonRound.CHAMPIONSHIP
            case "CS": return PostseasonRound.WORLD_SERIES
            case _: return None

    @property
    def previous_round(self) -> Optional['PostseasonRound']:
        match self.value:
            case "DIV": return PostseasonRound.WILDCARD
            case "CS": return PostseasonRound.DIVISIONAL
            case "WS": return PostseasonRound.CHAMPIONSHIP
            case _: return None

    @property
    def game_num_index_addition(self) -> int:
        match self.value:
            case "WC" : return 10000
            case "DIV": return 100000
            case "CS" : return 1000000
            case "WS" : return 10000000


class PostseasonFormat(Enum):
    WILDCARD_1 = "WC1" # WILDCARD IS BEST NON-DIVISION WINNER, GOES TO DIVISION SERIES
    WILDCARD_2 = "WC2" # 1 GAME WILDCARD
    WILDCARD_3 = "WC3" # 3 GAME WILD CARD SERIES
    CHAMPIONSHIP_SERIES = "LCS" # 2 BEST TEAMS IN EACH LEAGUE GO TO LCS
    WORLD_SERIES = "WS" # 2 BEST TEAMS GO TO WORLD SERIES
    DYNAMIC = "DYNAMIC"

    @property
    def is_wildcard_round(self) -> bool:
        match self.value:
            case "LCS" | "WS" | "WC1": return False
            case _: return True

    @property
    def teams_per_league(self) -> int:
        match self.value:
            case "WC1": return 4
            case "WC2": return 5
            case "WC3": return 6
            case "LCS": return 2
            case "WS": return 1

    @property
    def num_games_wildcard(self) -> int:
        match self.value:
            case "WC2": return 1
            case "WC3": return 3
            case _: return 0

    @property
    def num_games_division(self) -> int:
        return 5

    @property
    def num_games_championship_series(self) -> int:
        match self.value:
            case "LCS": return 5
            case _: return 7

    @property
    def num_games_world_series(self) -> int:
        return 7

    @property
    def rounds(self) -> list[PostseasonRound]:
        match self.value:
            case "WS": return [PostseasonRound.WORLD_SERIES]
            case "LCS": return [PostseasonRound.CHAMPIONSHIP, PostseasonRound.WORLD_SERIES]
            case "WC1": return [PostseasonRound.DIVISIONAL, PostseasonRound.CHAMPIONSHIP, PostseasonRound.WORLD_SERIES]
            case _: return [PostseasonRound.WILDCARD, PostseasonRound.DIVISIONAL, PostseasonRound.CHAMPIONSHIP, PostseasonRound.WORLD_SERIES]

    @property
    def year_range(self) -> list[int]:
        match self.value:
            case "WS": return list(range(1884, 1969))
            case "LCS": return list(range(1969, 1995))
            case "WC1": return list(range(1995, 2012))
            case "WC2": return list(range(2012, 2022))
            case "WC3": return list(range(2022, 2030))
            case _: return []


class SeasonSimulationConfig(BaseModel):
    """User-facing inputs for a season simulation. JSON-serializable so it can back an API endpoint."""

    year: int
    set: Set = Set._2000
    pct_of_games: Optional[float] = None
    games_limit: Optional[int] = None
    simulate_postseason: bool = True
    postseason_format: PostseasonFormat = PostseasonFormat.DYNAMIC
    seed: Optional[int] = None

    # ROSTER REQUIREMENTS
    min_pa: int = 100
    min_ip_sp: int = 50
    min_ip_rp: int = 30

    # 40-MAN ROSTER / INJURIES. REAL-SEASON TEAMS ONLY - BUILDER/TOURNAMENT TEAMS KEEP THEIR
    # USER-DEFINED ROSTERS AND ARE NEVER SUBJECT TO ROSTER LIMITS OR INJURIES.
    active_roster_size: int = 26
    full_roster_size: int = 40
    enable_injuries: bool = False
    injury_severity_multiplier: float = 1.0  # SCALES EVERY PLAYER'S HAZARD. 0.0 DISABLES INJURIES.

    # CUSTOM LEAGUE / TOURNAMENT MODE. WHEN POPULATED, SIMULATES A ROUND ROBIN
    # BETWEEN THE SUBMITTED TEAMS INSTEAD OF A REAL MLB SEASON.
    custom_teams: list[BuilderTeam] = []
    tournament_name: Optional[str] = None
    tournament_games: Optional[int] = None

    include_game_logs: bool = False
    include_box_scores: bool = False

    @property
    def is_tournament(self) -> bool:
        return len(self.custom_teams) > 0

    @property
    def league_name(self) -> str:
        return self.tournament_name or "CUSTOM LEAGUE"

    @property
    def should_collect_box_scores(self) -> bool:
        """Tournaments are small enough (tens of games) that box scores are effectively free and
        are exactly what that UI wants; a full MLB season only collects them if asked."""
        return self.include_box_scores or self.is_tournament


class TeamRecord(BaseModel):
    name: str
    league: Optional[str] = None
    division: Optional[str] = None
    points: int = 0
    wins: int = 0
    losses: int = 0
    win_pct: float = 0.0
    games_back: Optional[float] = None  # None FOR DIVISION LEADER
    playoff_seeding: Optional[int] = None


class StandingsResult(BaseModel):
    divisions: dict[str, list[TeamRecord]] = {}  # KEY: DIVISION NAME, VALUE: TEAMS SORTED BY RECORD


class GameLogEntry(BaseModel):
    inning: int
    is_top: bool
    outs: int
    bases: str          # EX: "■□□"
    away_score: int
    home_score: int
    pitcher: str
    hitter: str
    pitch_roll: int
    pitch_result: str
    swing_roll: int
    swing_result: str
    detail: str = ""    # STEALS, DPS, ADVANCES, ROLL ADJUSTMENTS
    summary: str = ""   # FULL HUMAN READABLE LINE


class SimTeamIdentity(BaseModel):
    """Team branding for rendering. Real-season teams resolve this from the `shared.Team` enum
    (year-aware colors); builder/tournament teams pass their own colors straight through."""

    abbreviation: str
    name: str = ""
    primary_color: Optional[str] = None    # "rgb(r, g, b)"
    secondary_color: Optional[str] = None  # "rgb(r, g, b)"
    league: Optional[str] = None


class InningLineScore(BaseModel):
    """One row of the linescore. A side's `runs` is None when that half-inning was never played
    (e.g. the home team wins in the top of the 9th and never bats in the bottom)."""

    num: int
    ordinal_num: str
    away_runs: Optional[int] = None
    home_runs: Optional[int] = None


class TeamLineScoreTotals(BaseModel):
    runs: int = 0
    hits: int = 0
    errors: int = 0   # THE SIM DOES NOT MODEL FIELDING ERRORS - ALWAYS 0, KEPT FOR SHAPE PARITY
    left_on_base: int = 0


class LineScoreResult(BaseModel):
    innings: list[InningLineScore] = []
    scheduled_innings: int = 9
    away: TeamLineScoreTotals = TeamLineScoreTotals()
    home: TeamLineScoreTotals = TeamLineScoreTotals()


class BoxScoreBattingStats(BaseModel):
    at_bats: int = 0
    runs: int = 0
    hits: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    rbi: int = 0
    base_on_balls: int = 0
    strike_outs: int = 0
    stolen_bases: int = 0
    caught_stealing: int = 0
    ground_into_double_play: int = 0
    plate_appearances: int = 0
    summary: str = ""


class BoxScoreBatter(BaseModel):
    id: str
    name: str = ""
    position: str = ""
    batting_order: int = 0
    is_substitute: bool = False   # ALWAYS False - THE SIM HAS NO POSITION-PLAYER SUBSTITUTIONS
    is_in_lineup: bool = True
    stats: BoxScoreBattingStats = BoxScoreBattingStats()


class BoxScorePitchingStats(BaseModel):
    innings_pitched: str = "0.0"   # "5.2" FORMAT, MATCHES THE REAL MLB API
    outs: int = 0
    hits: int = 0
    runs: int = 0                  # == earned_runs - THE SIM DOES NOT DISTINGUISH UNEARNED RUNS
    earned_runs: int = 0
    base_on_balls: int = 0
    strike_outs: int = 0
    home_runs: int = 0
    batters_faced: int = 0
    era: float = 0.0
    summary: str = ""


class BoxScorePitcher(BaseModel):
    id: str
    name: str = ""
    position: str = "SP"   # "SP" | "RP"
    order: int = 0          # 0 = STARTER, THEN ORDER OF ENTRY
    is_substitute: bool = False
    entered_in_inning: Optional[float] = None
    stats: BoxScorePitchingStats = BoxScorePitchingStats()


class TeamBoxScore(BaseModel):
    team: SimTeamIdentity
    batting: list[BoxScoreBatter] = []
    pitching: list[BoxScorePitcher] = []
    batting_totals: BoxScoreBattingStats = BoxScoreBattingStats()
    pitching_totals: BoxScorePitchingStats = BoxScorePitchingStats()


class GameResult(BaseModel):
    index: int
    date: date
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0
    winner: Optional[str] = None
    log: list[GameLogEntry] = []

    home_team_identity: Optional[SimTeamIdentity] = None
    away_team_identity: Optional[SimTeamIdentity] = None
    linescore: Optional[LineScoreResult] = None
    home_box_score: Optional[TeamBoxScore] = None
    away_box_score: Optional[TeamBoxScore] = None
    innings_played: int = 9
    is_extra_innings: bool = False


class SeriesResult(BaseModel):
    round: PostseasonRound
    league: Optional[str] = None
    home_team: str
    away_team: str
    home_team_seed: Optional[int] = None
    away_team_seed: Optional[int] = None
    home_team_wins: int = 0
    away_team_wins: int = 0
    winner: Optional[str] = None
    games: list[GameResult] = []


class PostseasonResult(BaseModel):
    format: PostseasonFormat
    rounds: dict[str, list[SeriesResult]] = {}  # KEY: PostseasonRound VALUE
    world_series_winner: Optional[str] = None


class TransactionType(Enum):
    INJURY = "IL"
    ACTIVATION = "ACT"
    CALLUP = "UP"
    OPTION = "DOWN"


class Transaction(BaseModel):
    """A single 40-man roster move (injury, activation, callup, or option). JSON-serializable
    for the API and the CLI `--show_transactions` table."""

    date: date
    team: str
    type: TransactionType
    player_id: str
    player_name: str
    position: str = ""                                    # PRIMARY POSITION STRING
    group: PositionSlotParent = PositionSlotParent.NONE
    il_days: Optional[int] = None
    return_date: Optional[date] = None
    games_missed: Optional[int] = None                     # ESTIMATED FROM il_days * SCHEDULE DENSITY, SET ON THE INJURY TRANSACTION
    related_player_id: Optional[str] = None                # THE REPLACEMENT / THE PLAYER REPLACED
    related_player_name: Optional[str] = None
    detail: str = ""


class OutlierEntry(BaseModel):
    id: str
    name: str
    player_type: str
    sim_ops: float
    real_ops: float
    diff: float


class SeasonSimulationResult(BaseModel):
    """Full output of a season simulation. JSON-serializable for API/frontend use."""

    config: SeasonSimulationConfig
    started_at: datetime
    ended_at: datetime

    schedule_length: int
    original_schedule_length: int
    stats_min_pa: int
    stats_min_ip: int

    standings: StandingsResult
    player_stats: list[Stats] = []
    league_totals: dict[str, Stats] = {}          # KEY: PlayerType VALUE
    real_league_averages: dict[str, Stats] = {}   # KEY: PlayerType VALUE (EMPTY FOR TOURNAMENTS)
    woba_weights: dict[str, float] = {}

    games: list[GameResult] = []
    postseason: Optional[PostseasonResult] = None
    transactions: list[Transaction] = []

    @property
    def runtime_seconds(self) -> float:
        return (self.ended_at - self.started_at).total_seconds()

    def top_players(self, player_type: str, stat: str, limit: int = 20, is_desc: bool = True, min_pa: int = 0, min_ip: int = 0) -> list[Stats]:
        """Ordered leaderboard filtered by playing time minimums."""
        league_stats = self.league_totals.get(player_type)
        eligible = [
            s for s in self.player_stats
            if s.player_type is not None and s.player_type.value == player_type
            and s.stat_by_key('pa') >= min_pa and s.stat_by_key('ip') >= min_ip
        ]
        eligible.sort(key=lambda s: s.stat_by_key(stat, league_stats=league_stats, woba_weights=self.woba_weights), reverse=is_desc)
        return eligible[:limit] if limit else eligible

    def top_outliers(self, player_type: str, limit: int = 5, is_desc: bool = True, min_pa: int = 0, min_ip: int = 0) -> list[OutlierEntry]:
        """Largest sim vs real-life OPS gaps."""
        entries: list[OutlierEntry] = []
        for s in self.player_stats:
            if s.player_type is None or s.player_type.value != player_type or s.real_ops is None:
                continue
            if s.stat_by_key('pa') < min_pa or s.stat_by_key('ip') < min_ip:
                continue
            entries.append(OutlierEntry(
                id=s.id, name=s.name, player_type=player_type,
                sim_ops=s.ops, real_ops=s.real_ops, diff=round(s.ops - s.real_ops, 3),
            ))
        entries.sort(key=lambda e: e.diff, reverse=is_desc)
        return entries[:limit] if limit else entries

    def transactions_for_team(self, team: str) -> list[Transaction]:
        return [t for t in self.transactions if t.team == team]

    def injury_summary_by_team(self) -> dict[str, dict[str, int]]:
        """Per-team counts of IL stints, total games missed, and callups."""
        summary: dict[str, dict[str, int]] = {}
        for t in self.transactions:
            team_summary = summary.setdefault(t.team, {"stints": 0, "games_missed": 0, "callups": 0})
            if t.type == TransactionType.INJURY:
                team_summary["stints"] += 1
                team_summary["games_missed"] += t.games_missed or 0
            elif t.type == TransactionType.CALLUP:
                team_summary["callups"] += 1
        return summary
