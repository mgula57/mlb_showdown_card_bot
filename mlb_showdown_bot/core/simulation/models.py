from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from ..card.sets import Set
from ..card.team_builder.team import CardSource, Team as BuilderTeam
from ..shared.player_position import PlayerSubType, PositionSlotParent
from .runners import Runners
from .stats import Stats


class GameStuckError(RuntimeError):
    """Raised by `Game.simulate` when the play loop fails to make progress - a half-inning that
    never records its third out, or a game that runs far past any plausible extra-inning length.

    Almost always a bug in the chart/steal/advance logic that leaves an inning unable to end.
    Rather than let the worker thread spin until the stale-job reaper kills it with a generic
    "stopped responding" message, this fails fast and carries `context` - a small dict of game
    state (teams, inning, score, counts, last play) that the sim log stores so the failure can be
    diagnosed without the full game log.
    """

    def __init__(self, message: str, *, context: dict) -> None:
        super().__init__(message)
        self.context = context


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


class ManagerPreference(BaseModel):
    """Per-run, team-wide manager tendencies for ONE club.

    Every field is a 1-5 level with 3 = neutral. A neutral instance is a mathematical no-op at
    every decision point it touches (each derived scalar below returns the exact constant the
    engine hardcodes today), so a sim where every club is neutral is byte-identical to one with
    no manager preferences at all. Deliberately NOT persisted to a `BuilderTeam` or a DB team
    row - it is chosen per simulation, in the setup form.
    """

    steal_aggression: int = Field(default=3, ge=1, le=5)         # 1 = rarely runs, 5 = runs constantly
    baserunning_aggression: int = Field(default=3, ge=1, le=5)   # taking the extra base on hits / tag-ups
    bullpen_hook: int = Field(default=3, ge=1, le=5)             # 1 = quick hook, 5 = slow hook
    closer_usage: int = Field(default=3, ge=1, le=5)            # 1 = save-only, 5 = earlier / non-save spots

    @property
    def is_neutral(self) -> bool:
        return (
            self.steal_aggression == 3 and self.baserunning_aggression == 3
            and self.bullpen_hook == 3 and self.closer_usage == 3
        )

    # DERIVED SCALARS - EACH RETURNS ITS EXACT NO-OP VALUE AT LEVEL 3, SO THE NEUTRAL CASE IS AN
    # IDENTITY FOR EVERY DECISION POINT (SEE `PlateAppearance` / `SimPitcher` / `Bullpen`).

    @property
    def steal_attempt_factor(self) -> float:
        """Multiplies the runner's success-probability contribution to the steal-attempt %.
        {1: 0.40, 2: 0.70, 3: 1.00, 4: 1.30, 5: 1.60}"""
        return 1.0 + (self.steal_aggression - 3) * 0.30

    @property
    def advance_probability_threshold(self) -> float:
        """Minimum P(safe) at which a runner is sent for the extra base. Lower = more aggressive.
        {1: 0.74, 2: 0.62, 3: 0.50, 4: 0.38, 5: 0.26}"""
        return 0.50 - (self.baserunning_aggression - 3) * 0.12

    @property
    def hook_ip_adjustment(self) -> float:
        """Innings added to a pitcher's fatigue threshold. Negative = quicker hook.
        {1: -1.0, 2: -0.5, 3: 0.0, 4: +0.5, 5: +1.0}"""
        return (self.bullpen_hook - 3) * 0.5

    @property
    def closer_nonsave_fit_multiplier(self) -> float:
        """Replaces the hardcoded 0.5 closer-in-non-save penalty in `SimPitcher.situational_fit`.
        {1: 0.00, 2: 0.25, 3: 0.50, 4: 0.75, 5: 1.00}"""
        return 0.50 + (self.closer_usage - 3) * 0.25

    @property
    def closer_save_inning(self) -> int:
        """Earliest inning that counts as a save situation for automatic closer entry.
        {1-3: 9, 4: 8, 5: 7}"""
        return 9 - max(0, self.closer_usage - 3)


NEUTRAL_MANAGER = ManagerPreference()


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

    # SEASON TAKEOVER. A BUILDER TEAM REPLACES ONE REAL CLUB IN AN OTHERWISE REAL MLB SEASON,
    # INHERITING ITS SCHEDULE, DIVISION AND OPPONENTS. DELIBERATELY SEPARATE FROM `custom_teams`,
    # WHICH SWAPS THE ENTIRE LEAGUE OUT FOR A ROUND ROBIN - THE TWO ARE MUTUALLY EXCLUSIVE.
    #
    # `takeover_team`/`takeover_replaces_abbr` ARE THE ORIGINAL SINGLE-TAKEOVER FIELDS (STILL
    # HOW A TEAM CHALLENGE RUN POPULATES THIS). `takeovers` IS THE OPEN-SIM GENERALIZATION - ANY
    # NUMBER OF CLUBS REPLACED IN ONE RUN, KEYED BY ERA-CORRECT SCHEDULE ABBREVIATION. USE
    # `all_takeovers` TO READ EITHER FORM WITHOUT CARING WHICH POPULATED IT.
    takeover_team: Optional[BuilderTeam] = None
    takeover_replaces_abbr: Optional[str] = None  # ERA-CORRECT ABBREVIATION, E.G. "TBD" FOR 1998
    takeovers: dict[str, BuilderTeam] = {}  # ERA-CORRECT ABBREVIATION -> BUILDER TEAM

    include_game_logs: bool = False
    include_box_scores: bool = False

    # REST-OF-SEASON PROJECTION. WHEN ENABLED, EVERY CLUB'S REAL RECORD AS OF `resume_as_of_date`
    # (DEFAULT: TODAY) SEEDS ITS SIMULATED ONE, AND ONLY GAMES AFTER THAT DATE ARE SIMULATED - SEE
    # `Schedule`'s `start_date` AND `Season._build_season_teams`'s SEEDING.
    resume_from_real_season: bool = False
    resume_as_of_date: Optional[date] = None
    # ADDITIONALLY MERGE EACH PLAYER'S REAL SEASON STATS TO DATE INTO THEIR SIMULATED TOTALS -
    # ONLY MEANINGFUL WHEN `resume_from_real_season` IS ALSO SET. A SEPARATE FLAG FROM THAT ONE
    # SINCE THE ARCHIVE HOLDS ONE CURRENT SNAPSHOT PER PLAYER-YEAR, NOT A HISTORY - THE MERGED
    # STATS REFLECT "AS OF THE ARCHIVE'S LAST SCRAPE", WHICH MAY NOT LINE UP WITH
    # `resume_as_of_date` EXACTLY, SO A USER WHO ONLY WANTS SEEDED STANDINGS CAN SKIP THIS.
    merge_real_stats: bool = False

    # STANDINGS PTS DISPLAY. A BUILDER/TOURNAMENT TEAM'S BENCH SLOTS COST LESS THAN THEIR CARD'S
    # FULL POINTS AT DRAFT TIME (SEE `Team.bench_pts_multiplier`), SO THE RAW SUM OF EVERY ACTIVE
    # PLAYER'S POINTS OVERSTATES WHAT THE TEAM ACTUALLY SPENT. DEFAULT ON - IT IS A NO-OP FOR
    # REAL-SEASON TEAMS (NO `bench_player_ids`/`bench_pts_multiplier` IS EVER SET FOR THOSE), SO
    # THIS ONLY CHANGES DISPLAYED PTS FOR BUILDER/TOURNAMENT/TAKEOVER ROSTERS.
    apply_bench_pts_multiplier_to_points: bool = True

    # MANAGER PREFERENCE. PER-RUN ONLY - NEVER PERSISTED TO A BuilderTeam OR A DB TEAM ROW.
    # `manager_preference` PAIRS WITH `takeover_team` (A TEAM CHALLENGE RUN); `manager_preferences`
    # PAIRS WITH `takeovers` (AN OPEN SIM), KEYED BY THE SAME ERA-CORRECT SCHEDULE ABBREVIATION.
    # A CLUB WITH NO ENTRY (EVERY REAL CLUB, ALWAYS) PLAYS NEUTRAL, WHICH IS A NO-OP. USE
    # `all_manager_preferences` TO READ EITHER FORM.
    manager_preference: Optional[ManagerPreference] = None
    manager_preferences: dict[str, ManagerPreference] = {}

    @property
    def all_manager_preferences(self) -> dict[str, ManagerPreference]:
        """Every club with a custom manager this run, keyed by schedule abbreviation. Mirrors
        `all_takeovers` - merges the legacy single field with the dict, dict wins on collision."""
        merged: dict[str, ManagerPreference] = {}
        if self.manager_preference is not None and self.takeover_replaces_abbr:
            merged[self.takeover_replaces_abbr] = self.manager_preference
        merged.update(self.manager_preferences)
        return merged

    @property
    def is_tournament(self) -> bool:
        return len(self.custom_teams) > 0

    @property
    def all_takeovers(self) -> dict[str, BuilderTeam]:
        """Every club replaced by a builder team this run, keyed by schedule abbreviation.

        Merges the legacy single-takeover fields with `takeovers` so every existing caller (a
        Team Challenge run, which only ever sets `takeover_team`/`takeover_replaces_abbr`) keeps
        working unchanged, while an open sim can populate `takeovers` directly with any number of
        clubs. `takeovers` wins on a key collision.
        """
        merged: dict[str, BuilderTeam] = {}
        if self.takeover_team is not None and self.takeover_replaces_abbr:
            merged[self.takeover_replaces_abbr] = self.takeover_team
        merged.update(self.takeovers)
        return merged

    @property
    def is_takeover(self) -> bool:
        return len(self.all_takeovers) > 0

    @property
    def card_sources(self) -> dict[str, str]:
        """card_id -> CardSource.value for every builder-drafted player in this sim (tournament
        custom teams and/or any takeover roster). Every other statline belongs to a real-season
        card straight from the bot archive - `CardSource.BOT` is the correct default for those,
        not just an absence of data, so callers resolving a player's source should fall back to
        it rather than leaving `card_source` unset.
        """
        sources: dict[str, str] = {}
        for team in self.custom_teams:
            sources.update({slot.card_id: slot.card_source.value for slot in team.roster})
        for team in self.all_takeovers.values():
            sources.update({slot.card_id: slot.card_source.value for slot in team.roster})
        return sources

    @property
    def league_name(self) -> str:
        return self.tournament_name or "CUSTOM LEAGUE"

    @property
    def should_collect_box_scores(self) -> bool:
        """Tournaments are small enough (tens of games) that box scores are effectively free and
        are exactly what that UI wants; a full MLB season only collects them if asked."""
        return self.include_box_scores or self.is_tournament


class SimTeamIdentity(BaseModel):
    """Team branding for rendering. Real-season teams resolve this from the `shared.Team` enum
    (year-aware colors); builder/tournament teams pass their own colors straight through."""

    abbreviation: str
    name: str = ""
    primary_color: Optional[str] = None    # "rgb(r, g, b)"
    secondary_color: Optional[str] = None  # "rgb(r, g, b)"
    league: Optional[str] = None


class TeamRecord(BaseModel):
    name: str  # SCHEDULE KEY. FOR A TAKEOVER TEAM THIS IS THE CLUB IT REPLACED - RENDER `identity`
    identity: Optional[SimTeamIdentity] = None
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


class PitcherAppearance(BaseModel):
    """A pitcher who has already appeared when a takeover begins, in order of entry.

    `start_inning`/`end_inning` are `Inning.inning_num_full` values (inning number plus the
    fraction of outs recorded, so 5.33 is one out into the 5th). `SimPitcher.innings_pitched`
    is simply `end - start` in those units, so the faithful way to seed a real pitcher is
    `start_inning = <current inning_num_full> - <real innings pitched>` rather than the inning
    they actually entered - that way `is_tired` reads their true workload.
    """

    player_id: str
    start_inning: float = 1.0
    end_inning: Optional[float] = None   # None = STILL IN THE GAME
    runs_allowed: int = 0


class CompletedHalfInning(BaseModel):
    """A half-inning already played before a takeover. Only the runs matter - they are what the
    linescore renders; outs and baserunners are gone by definition."""

    inning: int
    is_top: bool
    runs: int = 0


class TeamStartState(BaseModel):
    runs_scored: int = 0
    hits: int = 0                                        # CARRIED INTO THE LINESCORE ONLY - NOT INTO PLAYER STATS
    lineup_index: int = 0                                # 0-8, THE SPOT OF THE *NEXT* BATTER
    pitchers_used: list[PitcherAppearance] = []          # IN ORDER OF ENTRY


class GameStartState(BaseModel):
    """Mid-game state for a game the simulation is resuming rather than starting.

    Absent means simulate from the first pitch, which is every season/tournament game.
    """

    inning: int = 1
    is_top: bool = True
    outs: int = 0
    runs: int = 0                                        # RUNS ALREADY IN *THIS* HALF-INNING
    runners: Runners = Field(default_factory=Runners)
    completed_innings: list[CompletedHalfInning] = []
    away: TeamStartState = Field(default_factory=TeamStartState)
    home: TeamStartState = Field(default_factory=TeamStartState)


class RunnerRef(BaseModel):
    """A baserunner's identity and associated base. `base` is 1-3 for a runner still on, 4 for one
    who scored, and the base they were retired trying to reach for one who was thrown/forced out.

    `reason` is only meaningful on `GameLogEntry.scored` / `.retired` and tells a replay which of a
    plate appearance's beats the event belongs to: "steal" (pre-pitch) | "advance" (post-hit
    extra-base send) | "forced" (erased on the swing itself, e.g. a DP or fielder's choice) for a
    retired runner; "swing" | "advance" for one who scored. Empty on logs written before the
    per-beat split existed - consumers then treat the whole entry as a single beat."""
    id: str
    name: str
    base: int
    reason: str = ""


class GameLogEntry(BaseModel):
    inning: int
    is_top: bool
    outs: int
    bases: str          # EX: "■□□"
    away_score: int
    home_score: int
    pitcher: str
    # PLAYER IDS SO A RENDERED LOG CAN RESOLVE CARDS. THE ID SPACE IS WHATEVER THE SimTeam WAS BUILT
    # WITH: A BUILDER TEAM'S card_id, OR AN MLB PLAYER ID FOR A REAL-GAME SIM.
    pitcher_id: str = ""
    hitter: str
    hitter_id: str = ""
    runs_scored: int = 0   # RUNS ON THIS PLATE APPEARANCE - AVOIDS INFERRING A SCORING PLAY BY DIFFING SCORES
    pitch_roll: int
    pitch_result: str
    swing_roll: int
    swing_result: str
    # READER-FACING NARRATION, WORDED LIKE THE MLB FEED SO A SIMULATED PLAY LOG READS THE SAME AS
    # A REAL ONE. `detail`/`summary` BELOW STAY AS THEY WERE - THEY ARE THE CLI'S DICE-LEVEL VIEW.
    event: str = ""         # BADGE LABEL, EX: "Single", "Grounded Into DP"
    description: str = ""   # EX: "Freddy Fermin singles. Gavin Sheets to 2nd."
    detail: str = ""    # STEALS, DPS, ADVANCES, ROLL ADJUSTMENTS
    summary: str = ""   # FULL HUMAN READABLE LINE
    # RUNNER IDENTITY. `bases` ABOVE IS OCCUPANCY ONLY - THESE MAKE THE POST-PA BASE STATE
    # ADDRESSABLE BY PLAYER, WHICH IS WHAT LETS A REPLAY SLIDE A NAMED CARD FROM FIRST TO SECOND
    # RATHER THAN FADING ONE OCCUPANCY SQUARE OUT AND ANOTHER IN. EMPTY ON LOGS WRITTEN BEFORE
    # THIS EXISTED - CONSUMERS FALL BACK TO OCCUPANCY-ONLY WHEN SO.
    bases_detail: list[RunnerRef] = Field(default_factory=list)
    scored: list[RunnerRef] = Field(default_factory=list)
    retired: list[RunnerRef] = Field(default_factory=list)
    # POST-PHASE BASE SNAPSHOTS FOR A REPLAY THAT ANIMATES BASERUNNING APART FROM THE SWING. SAME
    # SHAPE AS `bases_detail`, EMITTED ONLY WHEN THAT PHASE ACTUALLY MOVED SOMEONE SO SIMPLE PLAYS
    # AND OLDER STORED SIMS STAY BYTE-FOR-BYTE THE SAME (None = "no split needed, use one beat").
    #   bases_after_steal - after pre-pitch steal attempts resolve
    #   bases_after_swing  - after the ball-in-play advancement + any DP, BEFORE extra-base sends
    bases_after_steal: Optional[list[RunnerRef]] = None
    bases_after_swing: Optional[list[RunnerRef]] = None


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
    stats_min_ip: int      # QUALIFYING IP FOR STARTERS
    stats_min_ip_rp: int   # QUALIFYING IP FOR RELIEVERS/CLOSERS - LOWER, SINCE THEY THROW FAR FEWER INNINGS

    standings: StandingsResult
    player_stats: list[Stats] = []
    league_totals: dict[str, Stats] = {}          # KEY: PlayerType VALUE
    real_league_averages: dict[str, Stats] = {}   # KEY: PlayerType VALUE (EMPTY FOR TOURNAMENTS)
    woba_weights: dict[str, float] = {}

    games: list[GameResult] = []
    postseason: Optional[PostseasonResult] = None
    transactions: list[Transaction] = []

    # SCHEDULE ABBREVIATION -> (WINS, LOSSES) EACH CLUB STARTED THIS RUN WITH. EMPTY (EVERY CLUB
    # STARTED 0-0) UNLESS `config.resume_from_real_season` - SEE `Season._build_season_teams`.
    seeded_records: dict[str, tuple[int, int]] = {}

    # LEAST-STALE stats_modified_date ACROSS EVERY MERGED PLAYER'S REAL STATLINE. NONE UNLESS
    # `config.merge_real_stats` - SEE `PlayerLoader.load_real_season_stats`. SURFACE THIS RATHER
    # THAN `config.resume_as_of_date` WHEN DESCRIBING WHAT THE MERGED STATS COVER.
    real_stats_as_of: Optional[datetime] = None

    @property
    def runtime_seconds(self) -> float:
        return (self.ended_at - self.started_at).total_seconds()

    def top_players(self, player_type: str, stat: str, limit: int = 20, is_desc: bool = True, min_pa: int = 0, min_ip: int = 0, player_sub_type: Optional[PlayerSubType] = None) -> list[Stats]:
        """Ordered leaderboard filtered by playing time minimums. `player_sub_type` further restricts
        to STARTING_PITCHER/RELIEF_PITCHER (or POSITION_PLAYER), used to split leaderboards by role."""
        league_stats = self.league_totals.get(player_type)
        eligible = [
            s for s in self.player_stats
            if s.player_type is not None and s.player_type.value == player_type
            and s.stat_by_key('pa') >= min_pa and s.stat_by_key('ip') >= min_ip
            and (player_sub_type is None or s.player_sub_type == player_sub_type)
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
