import csv
from collections import Counter, defaultdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, ClassVar, Optional

from pydantic import BaseModel

from ..card.sets import Set
from ..mlb_stats_api import MLBStatsAPI
from ..shared.player_position import PlayerType
from ..shared.team import Team as ShowdownTeam
from .awards import AwardsBuilder, SeriesMVP
from .models import GameResult, PostseasonRound, SeasonSimulationConfig, SeasonSimulationResult, SeriesResult
from .season import Season, SeasonPreload
from .stats import StatCategory, Stats
from .team import _rgb_string

# DISPLAY NAMES FOR EACH ROUND, IN BRACKET ORDER. "CHAMP" IS THE PSEUDO-ROUND FOR WINNING IT ALL.
ROUND_LABELS: dict[str, str] = {
    PostseasonRound.WILDCARD.value: "WC",
    PostseasonRound.DIVISIONAL.value: "DS",
    PostseasonRound.CHAMPIONSHIP.value: "LCS",
    PostseasonRound.WORLD_SERIES.value: "WS",
    "CHAMP": "Won WS",
}


# ------------------------------------------------------------------
# PER-RUN RECORD
# ------------------------------------------------------------------

class NotableGameTag(Enum):
    WALK_OFF = "WALK_OFF"
    EXTRA_INNINGS = "EXTRA_INNINGS"
    BLOWOUT = "BLOWOUT"


class LeaderCategory(BaseModel):
    """One postseason stat-leader category, e.g. most HR. `min_pa` gates rate stats."""

    key: str                  # Stats.stat_by_key KEY
    label: str
    player_type: PlayerType
    min_pa: int = 0
    is_rate: bool = False

    def format(self, value: float) -> str:
        return f"{value:.3f}".replace("0.", ".", 1) if self.is_rate else str(int(value))


LEADER_CATEGORIES: list[LeaderCategory] = [
    LeaderCategory(key=StatCategory.HOMERUNS.value, label="HR", player_type=PlayerType.HITTER),
    LeaderCategory(key=StatCategory.RBI.value, label="RBI", player_type=PlayerType.HITTER),
    LeaderCategory(key=StatCategory.HITS.value, label="H", player_type=PlayerType.HITTER),
    LeaderCategory(key=StatCategory.OPS.value, label="OPS", player_type=PlayerType.HITTER, min_pa=25, is_rate=True),
    LeaderCategory(key=StatCategory.SO.value, label="K", player_type=PlayerType.PITCHER),
    LeaderCategory(key=StatCategory.WINS.value, label="W", player_type=PlayerType.PITCHER),
    LeaderCategory(key=StatCategory.SAVES.value, label="SV", player_type=PlayerType.PITCHER),
]


class LeaderEntry(BaseModel):
    category: str             # LeaderCategory.label
    name: str
    team: Optional[str] = None
    value: float
    value_label: str


class SeriesOutcome(BaseModel):
    round: str                # PostseasonRound.value
    league: Optional[str] = None
    winner: str
    loser: str
    winner_wins: int
    loser_wins: int
    winner_seed: Optional[int] = None
    loser_seed: Optional[int] = None

    @property
    def score(self) -> str:
        return f"{self.winner_wins}-{self.loser_wins}"

    @classmethod
    def from_series(cls, series: SeriesResult) -> Optional['SeriesOutcome']:
        if not series.winner:
            return None
        winner_is_home = series.winner == series.home_team
        return cls(
            round=series.round.value,
            league=series.league,
            winner=series.winner,
            loser=series.away_team if winner_is_home else series.home_team,
            winner_wins=series.home_team_wins if winner_is_home else series.away_team_wins,
            loser_wins=series.away_team_wins if winner_is_home else series.home_team_wins,
            winner_seed=series.home_team_seed if winner_is_home else series.away_team_seed,
            loser_seed=series.away_team_seed if winner_is_home else series.home_team_seed,
        )


class NotableGame(BaseModel):
    round: str
    tag: NotableGameTag
    winner: str
    loser: str
    winner_score: int
    loser_score: int
    innings: int = 9

    BLOWOUT_MARGIN: ClassVar[int] = 7

    @classmethod
    def from_game(cls, round: str, game: GameResult) -> list['NotableGame']:
        if not game.winner:
            return []
        home_won = game.winner == game.home_team
        base = dict(
            round=round, winner=game.winner, loser=game.away_team if home_won else game.home_team,
            winner_score=max(game.home_score, game.away_score), loser_score=min(game.home_score, game.away_score),
            innings=game.innings_played,
        )
        tags: list[NotableGameTag] = []
        if cls._is_walk_off(game, home_won):
            tags.append(NotableGameTag.WALK_OFF)
        if game.is_extra_innings:
            tags.append(NotableGameTag.EXTRA_INNINGS)
        if base['winner_score'] - base['loser_score'] >= cls.BLOWOUT_MARGIN:
            tags.append(NotableGameTag.BLOWOUT)
        return [cls(tag=tag, **base) for tag in tags]

    @staticmethod
    def _is_walk_off(game: GameResult, home_won: bool) -> bool:
        """The home side won while batting in the final half-inning. A home team already ahead
        after the top of the last inning never bats (its `home_runs` is None), so any scoring
        bottom half past regulation that ends the game is by definition a walk-off."""
        if not home_won or game.linescore is None or not game.linescore.innings:
            return False
        last = game.linescore.innings[-1]
        return last.num >= game.linescore.scheduled_innings and bool(last.home_runs)


class PostseasonRunRecord(BaseModel):
    """Everything worth keeping from one simulated postseason - one line of `runs.jsonl`."""

    run: int
    seed: int
    champion: Optional[str] = None
    runner_up: Optional[str] = None
    ws_score: Optional[str] = None                 # "4-2", CHAMPION'S WINS FIRST
    pennants: dict[str, str] = {}                  # LEAGUE -> PENNANT WINNER
    series: list[SeriesOutcome] = []
    series_mvps: list[SeriesMVP] = []
    leaders: list[LeaderEntry] = []
    notable_games: list[NotableGame] = []

    @property
    def ws_mvp(self) -> Optional[SeriesMVP]:
        return next((m for m in self.series_mvps if m.round == PostseasonRound.WORLD_SERIES.value), None)

    def lcs_mvp(self, league: str) -> Optional[SeriesMVP]:
        return next((m for m in self.series_mvps if m.round == PostseasonRound.CHAMPIONSHIP.value and m.league == league), None)

    @classmethod
    def from_result(cls, run: int, seed: int, result: SeasonSimulationResult) -> 'PostseasonRunRecord':
        postseason = result.postseason
        if postseason is None:
            return cls(run=run, seed=seed)

        series: list[SeriesOutcome] = []
        notable: list[NotableGame] = []
        for round_value, series_list in postseason.rounds.items():
            for s in series_list:
                outcome = SeriesOutcome.from_series(s)
                if outcome:
                    series.append(outcome)
                for game in s.games:
                    notable.extend(NotableGame.from_game(round=round_value, game=game))

        ws = next((s for s in series if s.round == PostseasonRound.WORLD_SERIES.value), None)
        return cls(
            run=run,
            seed=seed,
            champion=postseason.world_series_winner,
            runner_up=ws.loser if ws else None,
            ws_score=ws.score if ws else None,
            pennants={s.league: s.winner for s in series if s.round == PostseasonRound.CHAMPIONSHIP.value and s.league},
            series=series,
            series_mvps=AwardsBuilder(result=result).series_mvps(),
            leaders=cls._leaders(postseason.player_stats),
            notable_games=notable,
        )

    @staticmethod
    def _leaders(player_stats: list[Stats]) -> list[LeaderEntry]:
        leaders: list[LeaderEntry] = []
        for category in LEADER_CATEGORIES:
            eligible = [
                s for s in player_stats
                if s.player_type == category.player_type and s.stat_by_key(StatCategory.PA.value) >= category.min_pa
            ]
            if not eligible:
                continue
            best = max(eligible, key=lambda s: s.stat_by_key(category.key))
            value = float(best.stat_by_key(category.key))
            if value <= 0:
                continue
            leaders.append(LeaderEntry(category=category.label, name=best.name, team=best.team, value=value, value_label=category.format(value)))
        return leaders


# ------------------------------------------------------------------
# AGGREGATE SUMMARY
# ------------------------------------------------------------------

class TeamOdds(BaseModel):
    team: str
    display_name: str
    league: Optional[str] = None
    seed: Optional[int] = None
    primary_color: str
    secondary_color: str
    display_color: str                    # PRIMARY, OR SECONDARY WHEN PRIMARY IS TOO LIGHT FOR THE PAGE'S LIGHT BACKGROUND
    titles: int = 0
    title_pct: float = 0.0
    pennants: int = 0
    pennant_pct: float = 0.0
    reached_pct: dict[str, float] = {}   # ROUND_LABELS KEY -> % OF RUNS THE TEAM PLAYED IN (OR WON, FOR "CHAMP")


# TEAMS PAINTED IN THEIR SECONDARY COLOR ON THE REPORT, ON TOP OF THE SHARED
# `Team.use_secondary_color_for_graphs` LIST - REPORT-ONLY SO CARD CHARTS ARE UNAFFECTED.
# MIL: GOLD INSTEAD OF A NAVY THAT READS THE SAME AS TBR/NYY.
_REPORT_SECONDARY_COLOR_TEAMS = {ShowdownTeam.MIL}


def _display_color(team: ShowdownTeam, year: int) -> str:
    """The team color to paint on the report's light background. Secondary when the team is
    flagged for it (see `_REPORT_SECONDARY_COLOR_TEAMS`), or when a near-white primary would
    vanish against the background and the secondary is darker."""
    def luminance(color: tuple) -> float:
        return (0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]) / 255

    primary, secondary = team.color(year=year), team.color(year=year, is_secondary=True)
    if team.use_secondary_color_for_graphs or team in _REPORT_SECONDARY_COLOR_TEAMS:
        return _rgb_string(secondary)
    return _rgb_string(secondary if luminance(primary) > 0.8 and luminance(secondary) < luminance(primary) else primary)


class MVPTally(BaseModel):
    name: str
    team: Optional[str] = None
    count: int
    best_line: str                        # value_label FROM THEIR BEST MVP SERIES


class CountedLabel(BaseModel):
    label: str
    count: int


class RecordMark(BaseModel):
    category: str
    name: str
    team: Optional[str] = None
    value_label: str
    run: int


class PostseasonBatchSummary(BaseModel):
    year: int
    set: str
    runs: int
    generated_at: datetime
    rounds: list[str] = []                # ROUND_LABELS KEYS PRESENT, BRACKET ORDER
    teams: list[TeamOdds] = []            # SORTED BY TITLES DESC
    ws_mvps: list[MVPTally] = []
    lcs_mvps: list[MVPTally] = []
    ws_matchups: list[CountedLabel] = []
    ws_lengths: list[CountedLabel] = []   # "4-0" .. "4-3"
    titles_by_seed: list[CountedLabel] = []
    single_postseason_records: list[RecordMark] = []
    notable_counts: dict[str, int] = {}   # NotableGameTag.value -> TOTAL ACROSS ALL RUNS

    @property
    def title_leader(self) -> Optional[TeamOdds]:
        return self.teams[0] if self.teams else None

    @classmethod
    def from_records(cls, year: int, set: str, records: list[PostseasonRunRecord]) -> 'PostseasonBatchSummary':
        num_runs = max(len(records), 1)

        def pct(count: int) -> float:
            return round(100 * count / num_runs, 1)

        # WHICH ROUNDS EACH TEAM PLAYED IN, PER RUN - A TEAM WITH A BYE FIRST APPEARS IN THE DS.
        reached: dict[str, Counter] = defaultdict(Counter)
        league_by_team: dict[str, str] = {}
        seed_by_team: dict[str, int] = {}
        for record in records:
            for s in record.series:
                for team, team_seed in ((s.winner, s.winner_seed), (s.loser, s.loser_seed)):
                    reached[team][s.round] += 1
                    if team_seed is not None:
                        seed_by_team[team] = team_seed
                    if s.league:
                        league_by_team[team] = s.league
            if record.champion:
                reached[record.champion]["CHAMP"] += 1

        rounds_present = [key for key in ROUND_LABELS if any(key in counts for counts in reached.values())]
        titles = Counter(r.champion for r in records if r.champion)
        pennants = Counter(team for r in records for team in r.pennants.values())

        teams = [
            TeamOdds(
                team=team,
                display_name=ShowdownTeam(team).nickname or team,
                league=league_by_team.get(team),
                seed=seed_by_team.get(team),
                primary_color=_rgb_string(ShowdownTeam(team).color(year=year)),
                secondary_color=_rgb_string(ShowdownTeam(team).color(year=year, is_secondary=True)),
                display_color=_display_color(ShowdownTeam(team), year=year),
                titles=titles[team], title_pct=pct(titles[team]),
                pennants=pennants[team], pennant_pct=pct(pennants[team]),
                reached_pct={key: pct(counts[key]) for key in rounds_present},
            )
            for team, counts in reached.items()
        ]
        teams.sort(key=lambda t: (-t.titles, -t.pennants, t.league or "", t.seed or 99))

        return cls(
            year=year,
            set=set,
            runs=len(records),
            generated_at=datetime.now(),
            rounds=rounds_present,
            teams=teams,
            ws_mvps=cls._mvp_tally([r.ws_mvp for r in records]),
            lcs_mvps=cls._mvp_tally([m for r in records for m in r.series_mvps if m.round == PostseasonRound.CHAMPIONSHIP.value]),
            ws_matchups=cls._counted(" vs ".join(sorted([r.champion, r.runner_up])) for r in records if r.champion and r.runner_up),
            ws_lengths=sorted(cls._counted(r.ws_score for r in records if r.ws_score), key=lambda c: c.label, reverse=True),
            titles_by_seed=sorted(
                cls._counted(f"#{seed_by_team[r.champion]} seed" for r in records if r.champion in seed_by_team),
                key=lambda c: c.label,
            ),
            single_postseason_records=cls._records(records),
            notable_counts=dict(Counter(g.tag.value for r in records for g in r.notable_games)),
        )

    @staticmethod
    def _counted(labels) -> list[CountedLabel]:
        return [CountedLabel(label=label, count=count) for label, count in Counter(labels).most_common()]

    @staticmethod
    def _mvp_tally(mvps: list[Optional[SeriesMVP]]) -> list[MVPTally]:
        # KEYED BY PERSON (NAME + TEAM), NOT CARD ID - A TWO-WAY PLAYER (E.G. OHTANI) HAS SEPARATE
        # HITTER AND PITCHER CARDS WITH DIFFERENT IDS, BUT HIS MVPS COUNT AS ONE PLAYER'S EITHER WAY.
        by_player: dict[tuple[str, Optional[str]], list[SeriesMVP]] = defaultdict(list)
        for mvp in mvps:
            if mvp is not None:
                by_player[(mvp.player.name, mvp.team)].append(mvp)
        tallies = [
            MVPTally(
                name=wins[0].player.name, team=wins[0].team, count=len(wins),
                best_line=max(wins, key=lambda m: m.value).value_label,
            )
            for wins in by_player.values()
        ]
        return sorted(tallies, key=lambda t: -t.count)

    @staticmethod
    def _records(records: list[PostseasonRunRecord]) -> list[RecordMark]:
        """Best single-postseason mark in each leader category across every run."""
        marks: list[RecordMark] = []
        for category in LEADER_CATEGORIES:
            candidates = [(r.run, entry) for r in records for entry in r.leaders if entry.category == category.label]
            if not candidates:
                continue
            run, best = max(candidates, key=lambda c: c[1].value)
            marks.append(RecordMark(category=category.label, name=best.name, team=best.team, value_label=best.value_label, run=run))
        return marks


# ------------------------------------------------------------------
# RUNNER
# ------------------------------------------------------------------

class PostseasonBatch:
    """Simulates one season's postseason `runs` times from the real final standings and logs a
    `PostseasonRunRecord` per run to `runs.jsonl` as each one finishes, so a crash or Ctrl-C
    keeps every completed run and `resume=True` picks up where it left off.

    Built on the `resume_from_real_postseason` mode: no regular-season games are simulated, the
    bracket is seeded from real standings, and any real postseason games already played are
    locked in (see `RealPostseasonBracket`). The card pool loads once and is shared by every run.
    """

    RUNS_FILE = "runs.jsonl"
    RUNS_CSV_FILE = "runs.csv"
    SUMMARY_FILE = "summary.json"
    HTML_FILE = "summary.html"
    PDF_FILE = "summary.pdf"
    IMAGE_STEM = "summary"

    def __init__(self, year: int, set: str, runs: int, base_seed: int, out_dir: Optional[Path] = None) -> None:
        self.year = year
        self.set = Set(set)
        self.runs = runs
        self.base_seed = base_seed
        self.out_dir = Path(out_dir or f"sim_output/postseason_{year}_{self.set.value}")

    @property
    def runs_path(self) -> Path:
        return self.out_dir / self.RUNS_FILE

    def image_paths(self, image_format: str) -> list[Path]:
        """One path per summary sheet, e.g. `summary_1.png`, `summary_2.png` - matches
        `PostseasonBatchReport.SHEET_COUNT`."""
        from .postseason_batch_report import PostseasonBatchReport

        return [self.out_dir / f"{self.IMAGE_STEM}_{page}.{image_format}" for page in range(1, PostseasonBatchReport.SHEET_COUNT + 1)]

    @property
    def config(self) -> SeasonSimulationConfig:
        # SAME SHAPE `api/sim.py` BUILDS FOR A POSTSEASON-ONLY RESUME: IT ALWAYS IMPLIES
        # `resume_from_real_season` AND ALWAYS MERGES REAL STATS (OTHERWISE `league_totals` WOULD
        # BE EMPTY AND THE SERIES MVP MATH WOULD HAVE NO LEAGUE BASELINE).
        return SeasonSimulationConfig(
            year=self.year,
            set=self.set,
            simulate_postseason=True,
            resume_from_real_season=True,
            resume_from_real_postseason=True,
            merge_real_stats=True,
        )

    def load_records(self) -> list[PostseasonRunRecord]:
        if not self.runs_path.exists():
            return []
        with open(self.runs_path) as f:
            return [PostseasonRunRecord.model_validate_json(line) for line in f if line.strip()]

    def run(
        self,
        resume: bool = False,
        status_callback: Optional[Callable[[str], None]] = None,
        run_callback: Optional[Callable[[PostseasonRunRecord, int], None]] = None,
    ) -> list[PostseasonRunRecord]:
        """Simulate every outstanding run. `run_callback(record, total)` fires after each one."""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        records = self.load_records() if resume else []
        if not resume and self.runs_path.exists():
            self.runs_path.unlink()
        done = {r.run for r in records}
        pending = [i for i in range(1, self.runs + 1) if i not in done]
        if not pending:
            return records

        config = self.config
        preload = SeasonPreload.load(config=config, status_callback=status_callback)
        mlb_stats_api = MLBStatsAPI()

        with open(self.runs_path, 'a') as f:
            for run in pending:
                seed = self.base_seed + run - 1
                season = Season(config=config.model_copy(update={'seed': seed}), mlb_stats_api=mlb_stats_api, preload=preload)
                record = PostseasonRunRecord.from_result(run=run, seed=seed, result=season.simulate())
                f.write(record.model_dump_json() + "\n")
                f.flush()
                records.append(record)
                if run_callback:
                    run_callback(record, len(pending))

        return sorted(records, key=lambda r: r.run)

    def write_outputs(
        self, records: list[PostseasonRunRecord], status_callback: Optional[Callable[[str], None]] = None,
        image_format: Optional[str] = "png",
    ) -> PostseasonBatchSummary:
        """Aggregate `records` and write summary.json, runs.csv, summary.html and (when Chrome is
        available) summary.pdf plus one image per sheet (`summary_1.<image_format>`,
        `summary_2.<image_format>`, ...). `image_format` is a Chrome-screenshottable extension
        ("png" or "jpg"/"jpeg"); pass None to skip image export."""
        from .postseason_batch_report import PostseasonBatchReport

        self.out_dir.mkdir(parents=True, exist_ok=True)
        summary = PostseasonBatchSummary.from_records(year=self.year, set=self.set.value, records=records)
        (self.out_dir / self.SUMMARY_FILE).write_text(summary.model_dump_json(indent=2))

        with open(self.out_dir / self.RUNS_CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['run', 'seed', 'champion', 'runner_up', 'ws_score', 'al_pennant', 'nl_pennant', 'ws_mvp', 'alcs_mvp', 'nlcs_mvp'])
            for r in records:
                mvp_names = [m.player.name if m else '' for m in (r.ws_mvp, r.lcs_mvp('AL'), r.lcs_mvp('NL'))]
                writer.writerow([r.run, r.seed, r.champion, r.runner_up, r.ws_score, r.pennants.get('AL', ''), r.pennants.get('NL', '')] + mvp_names)

        html_path = self.out_dir / self.HTML_FILE
        html_path.write_text(PostseasonBatchReport(summary=summary).render())
        skipped_pdf = PostseasonBatchReport.write_pdf(html_path=html_path, pdf_path=self.out_dir / self.PDF_FILE)
        if skipped_pdf and status_callback:
            status_callback(f"SKIPPED PDF: {skipped_pdf}")

        if image_format:
            skipped_images = PostseasonBatchReport.write_images(html_path=html_path, image_paths=self.image_paths(image_format))
            if skipped_images and status_callback:
                status_callback(f"SKIPPED IMAGES: {skipped_images}")

        return summary
