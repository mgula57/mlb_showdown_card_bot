import csv
import os
import statistics
from datetime import date, timedelta
from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field

from ..shared.player_position import PlayerSubType, PlayerType, PositionSlot


# ------------------------------------------------------------------------
# BUILDER / TAKEOVER PLAYER IDS
# ------------------------------------------------------------------------
# A builder-drafted player (a tournament custom team or a season takeover roster) is keyed in the
# stat engine under a schedule-key-prefixed id rather than the bare `card_id` its roster slot
# carries. A BOT slot's `card_id` IS the archive card's `dim_card.id`, and a real-pool player's
# sim id resolves to that same id via `card_ids` - so without the prefix a drafted card and the
# very same card fielded by its real club in the same sim would share one id, `PlayerStatsGroup`
# would seed a single line for them, and every game either one plays would merge into it,
# doubling that player's season. The prefix is stripped back off at the `SimStatLine` boundary
# (`real_card_id`) so the frontend still links each row to its real card by `card_id`.
_BUILDER_ID_PREFIX = "builder@"
_BUILDER_ID_SEP = "@"


def builder_sim_id(schedule_key: str, card_id: str) -> str:
    """The stat-engine id for a builder/takeover roster slot's player."""
    return f"{_BUILDER_ID_PREFIX}{schedule_key}{_BUILDER_ID_SEP}{card_id}"


def real_card_id(sim_id: str) -> str:
    """The bare `card_id` behind a sim player id - the identity for a real-pool player, and the
    original roster-slot `card_id` for a builder-prefixed one."""
    if sim_id.startswith(_BUILDER_ID_PREFIX):
        return sim_id.rsplit(_BUILDER_ID_SEP, 1)[-1]
    return sim_id


class StatCategory(Enum):
    PA = "pa"
    AB = "ab"
    HITS = 'h'
    PU = "pu"
    SO = "so"
    GB = "gb"
    FB = "fb"
    BB = "bb"
    SINGLES = "1b"
    SINGLE_PLUS = "1b+"
    DOUBLES = "2b"
    TRIPLES = "3b"
    HOMERUNS = "hr"
    PITCHER_ADVANTAGE = "padv"
    HITTER_ADVANTAGE = "hadv"
    OWN_CHART_OUT = "own_chart_out"
    ADVANTAGE_PCT = "advantage_pct"
    OWN_CHART_OUT_PCT = "own_chart_out_pct"
    EARNED_RUNS = "er"
    RBI = "rbi"
    RUNS = "r"
    IBB = "ibb"
    HBP = "hbp"
    SH = "sh"
    SF = "sf"
    SB = "sb"
    CS = "cs"
    BA = "ba"
    OBP = "obp"
    SLG = "slg"
    OPS = "ops"
    OPS_PLUS = "ops+"
    IP = "ip"
    WHIP = "whip"
    ERA = "era"
    SO9 = "so9"
    G = "g"
    WINS = "wins"
    LOSSES = "losses"
    RUNS_ALLOWED = "runs_allowed"
    RUNS_SCORED = "runs_scored"
    GDP = "gidp"
    GDPa = "gidpa"
    # ADVANCED STATS
    wOBA = "wOBA"
    wRAA = "wRAA"
    wRC = "wRC"
    wRC_PLUS = "wRC+"
    # NON STATS
    NAME = 'name'
    POSITION = 'position'
    TEAM = 'team'
    POINTS = 'points'
    COMMAND = 'command'

    @property
    def abbreviation(self) -> str:
        match self:
            case StatCategory.RUNS_ALLOWED: return "RA"
            case StatCategory.RUNS_SCORED: return "RS"
            case StatCategory.WINS: return "W"
            case StatCategory.LOSSES: return "L"
            case StatCategory.POSITION: return "POS"
            case StatCategory.OWN_CHART_OUT: return "OCO"
            case StatCategory.ADVANTAGE_PCT: return "ADV%"
            case StatCategory.OWN_CHART_OUT_PCT: return "OCO%"
            case _: return self.value.upper()

    @property
    def is_text(self) -> bool:
        return self in [StatCategory.NAME, StatCategory.POSITION, StatCategory.TEAM, StatCategory.COMMAND]

    @property
    def decimal_places(self) -> int:
        match self:
            case StatCategory.BA | StatCategory.OBP | StatCategory.SLG | StatCategory.OPS | StatCategory.wOBA | StatCategory.ADVANTAGE_PCT | StatCategory.OWN_CHART_OUT_PCT:
                return 3
            case StatCategory.ERA | StatCategory.WHIP: return 2
            case StatCategory.IP | StatCategory.SO9: return 1
            case _: return 0


class Stats(BaseModel):
    """A single statline (player, team-game, or league aggregate). Counting stats live in `totals`, rate stats are derived."""

    id: str
    name: str = ""
    player_type: Optional[PlayerType] = None
    player_sub_type: Optional[PlayerSubType] = None  # POSITION_PLAYER / STARTING_PITCHER / RELIEF_PITCHER - SPLITS LEADERBOARDS
    position: Optional[str] = None
    team: Optional[str] = None
    points: int = 0
    speed: int = 0
    command: float = 0
    real_ops: Optional[float] = None  # REAL LIFE OPS, USED FOR OUTLIER COMPARISONS
    is_rookie: bool = False           # REAL-LIFE ROOKIE STATUS FOR THE CARD'S YEAR - USED FOR RoY
    defense: int = 0                  # CARD'S positions_and_defense RATING AT THE PLAYER'S PRIMARY SIM POSITION
    totals: dict[str, float] = Field(default_factory=dict)
    # PLATE APPEARANCES BY THE PositionSlot VALUE THE PLAYER ACTUALLY FIELDED THAT PA (E.G. "LF"/
    # "RF"/"DH") - DISTINCT FROM `position`, WHICH IS THE CARD'S OWN (POSSIBLY COMBINED, E.G.
    # "LF/RF") PRIMARY POSITION. USED TO TELL A SEASON'S ACTUAL LF/RF/DH USAGE APART WHEN THE CARD
    # ITSELF DOESN'T DISTINGUISH THEM - SEE `AwardsBuilder.silver_sluggers`.
    positions_played: dict[str, int] = Field(default_factory=dict)

    def merge(self, stats: 'Stats') -> None:
        """Merge another statline's counting stats into this one."""
        self.merge_totals(stats.totals)
        self.merge_positions_played(stats.positions_played)

    def merge_totals(self, totals: dict[str, float]) -> None:
        for key, value in totals.items():
            self.totals[key] = self.totals.get(key, 0) + value

    def merge_positions_played(self, positions_played: dict[str, int]) -> None:
        for position, count in positions_played.items():
            self.positions_played[position] = self.positions_played.get(position, 0) + count

    def add_stat(self, category: StatCategory, value: float) -> None:
        """Increment a single counting stat in place."""
        self.totals[category.value] = self.totals.get(category.value, 0) + value

    def stat(self, category: StatCategory, league_stats: Optional['Stats'] = None, woba_weights: Optional[dict[str, float]] = None, combine_1b_and_1b_plus: bool = False):
        match category:
            case StatCategory.IP: return round(self.totals.get(category.value, 0), 1)
            case StatCategory.POINTS: return self.points
            case StatCategory.NAME: return self.name or 'N/A'
            case StatCategory.TEAM: return self.team or 'N/A'
            case StatCategory.COMMAND: return self.command
            case StatCategory.POSITION: return self.position or PositionSlot.NONE.value
            case StatCategory.BA: return self.ba
            case StatCategory.OBP: return self.obp
            case StatCategory.SLG: return self.slg
            case StatCategory.OPS: return self.ops
            case StatCategory.WHIP: return self.whip
            case StatCategory.ERA: return self.era
            case StatCategory.SO9: return self.so9
            case StatCategory.OPS_PLUS: return self.ops_plus(league_stats=league_stats)
            case StatCategory.ADVANTAGE_PCT: return self.advantage_pct
            case StatCategory.OWN_CHART_OUT_PCT: return self.own_chart_out_pct
            case StatCategory.wOBA: return self.wOBA(weights=woba_weights)
            case StatCategory.wRAA: return self.wRAA(league_stats=league_stats, weights=woba_weights)
            case StatCategory.wRC: return self.wRC(league_stats=league_stats, weights=woba_weights)
            case StatCategory.wRC_PLUS: return self.wRC_plus(league_stats=league_stats, weights=woba_weights)
            case StatCategory.SINGLES: return self.singles if combine_1b_and_1b_plus else self.totals.get(category.value, 0)
            case _: return self.totals.get(category.value, 0)

    def stat_by_key(self, key: str, league_stats: Optional['Stats'] = None, woba_weights: Optional[dict[str, float]] = None):
        """String-keyed variant of stat() for serialized/API contexts."""
        try:
            category = StatCategory(key)
        except ValueError:
            return self.totals.get(key, 0)
        return self.stat(category, league_stats=league_stats, woba_weights=woba_weights, combine_1b_and_1b_plus=True)

    @property
    def singles(self) -> float:
        return self.totals.get(StatCategory.SINGLE_PLUS.value, 0) + self.totals.get(StatCategory.SINGLES.value, 0)

    @property
    def ba(self) -> float:
        ab = float(self.stat(StatCategory.AB))
        h = float(self.stat(StatCategory.HITS))
        return round(h / ab, 3) if ab > 0 else 0.000

    @property
    def obp(self) -> float:
        h = float(self.stat(StatCategory.HITS))
        bb = float(self.stat(StatCategory.BB))
        hbp = float(self.stat(StatCategory.HBP))
        sf = float(self.stat(StatCategory.SF))
        ab = float(self.stat(StatCategory.AB))
        pa = ab + bb + hbp + sf
        return round((h + bb + hbp) / pa, 3) if pa > 0 else 0.000

    @property
    def slg(self) -> float:
        ab = float(self.stat(StatCategory.AB))
        singles = self.singles
        doubles = self.stat(StatCategory.DOUBLES) * 2
        triples = self.stat(StatCategory.TRIPLES) * 3
        homeruns = self.stat(StatCategory.HOMERUNS) * 4
        return round((singles + doubles + triples + homeruns) / ab, 3) if ab > 0 else 0.000

    @property
    def ops(self) -> float:
        return round(self.obp + self.slg, 3)

    @property
    def own_chart_pa(self) -> float:
        """PAs decided on this player's own chart (they held the pitch advantage)."""
        category = StatCategory.HITTER_ADVANTAGE if self.player_type == PlayerType.HITTER else StatCategory.PITCHER_ADVANTAGE
        return float(self.totals.get(category.value, 0))

    @property
    def advantage_pct(self) -> float:
        pa = float(self.stat(StatCategory.PA))
        return round(self.own_chart_pa / pa, 3) if pa > 0 else 0.000

    @property
    def own_chart_out_pct(self) -> float:
        own_chart_pa = self.own_chart_pa
        return round(self.totals.get(StatCategory.OWN_CHART_OUT.value, 0) / own_chart_pa, 3) if own_chart_pa > 0 else 0.000

    @property
    def whip(self) -> float:
        ip = float(self.stat(StatCategory.IP))
        walks_and_hits = float(self.stat(StatCategory.BB) + self.stat(StatCategory.HITS))
        return round(walks_and_hits / ip, 2) if ip > 0 else 0.00

    @property
    def era(self) -> float:
        ip = float(self.stat(StatCategory.IP))
        er = float(self.stat(StatCategory.EARNED_RUNS))
        return round(9 * er / ip, 2) if ip > 0 else 0.00

    @property
    def so9(self) -> float:
        ip = float(self.stat(StatCategory.IP))
        so = float(self.stat(StatCategory.SO))
        return round(9 * so / ip, 1) if ip > 0 else 0.00

    def wOBA(self, weights: Optional[dict[str, float]]) -> float:

        if weights is None or self.stat(StatCategory.PA) == 0:
            return 0.000

        return round(
            (
                (weights.get('wbb', 0) * self.stat(StatCategory.BB))
                + (weights.get('w1b', 0) * self.singles)
                + (weights.get('w2b', 0) * self.stat(StatCategory.DOUBLES))
                + (weights.get('w3b', 0) * self.stat(StatCategory.TRIPLES))
                + (weights.get('whr', 0) * self.stat(StatCategory.HOMERUNS))
                + (weights.get('runsb', 0) * self.stat(StatCategory.SB))
                + (weights.get('runcs', 0) * self.stat(StatCategory.CS)) # NOTE: CS IS ADDED HERE BECAUSE WEIGHT IS A NEGATIVE
            ) / self.stat(StatCategory.PA)
        , 3)

    def wRAA(self, league_stats: Optional['Stats'], weights: Optional[dict[str, float]]) -> float:
        if league_stats is None or weights is None:
            return 0
        league_woba = league_stats.stat(category=StatCategory.wOBA, woba_weights=weights)
        woba_scale = weights.get('wobascale', 1)
        return round(((self.wOBA(weights=weights) - league_woba) / woba_scale) * self.stat(StatCategory.PA), 0)

    def wRC(self, league_stats: Optional['Stats'], weights: Optional[dict[str, float]]) -> float:
        if league_stats is None or weights is None:
            return 0
        league_runs = league_stats.stat(StatCategory.RUNS)
        league_pa = league_stats.stat(StatCategory.PA)
        if league_pa == 0:
            return 0
        league_woba = league_stats.stat(category=StatCategory.wOBA, woba_weights=weights)
        woba_scale = weights.get('wobascale', 1)
        league_runs_per_pa = float(league_runs / league_pa)
        pa = self.stat(StatCategory.PA)
        return round( ( ( (self.wOBA(weights=weights) - league_woba) / woba_scale) + league_runs_per_pa ) * pa )

    def wRC_plus(self, league_stats: Optional['Stats'], weights: Optional[dict[str, float]]) -> float:
        if league_stats is None or weights is None:
            return 0
        league_runs = league_stats.stat(StatCategory.RUNS)
        league_pa = league_stats.stat(StatCategory.PA)
        pa = self.stat(StatCategory.PA)

        if pa == 0 or league_pa == 0:
            return 0

        league_runs_per_pa = float(league_runs / league_pa)
        league_wRC = league_stats.stat(category=StatCategory.wRC, league_stats=league_stats, woba_weights=weights)
        wRAA = self.wRAA(league_stats=league_stats, weights=weights)

        if league_wRC == 0:
            return 0

        return round( 100 * (wRAA / pa + league_runs_per_pa) / (league_wRC / league_pa) )

    @property
    def slashline(self) -> str:
        final_str = ""
        for index, stat in enumerate([self.ba, self.obp, self.slg]):
            final_str += ( str(stat).replace('0.', '.') + ("/" if index != 2 else "") )
        return final_str

    def ops_plus(self, league_stats: Optional['Stats']) -> int:
        if league_stats is None or league_stats.obp == 0 or league_stats.slg == 0:
            return 0
        return int(round(100 * ((self.obp / league_stats.obp) + (self.slg / league_stats.slg) - 1)))

    def summary_str(self, include_name: bool = False, include_hit_totals: bool = False) -> str:

        name = f"{self.name}: " if include_name else ""

        if self.player_type == PlayerType.HITTER:

            hits = self.stat(StatCategory.HITS)
            abs = self.stat(StatCategory.AB)
            walks = self.stat(StatCategory.BB)
            doubles = self.stat(StatCategory.DOUBLES)
            triples = self.stat(StatCategory.TRIPLES)
            homeruns = self.stat(StatCategory.HOMERUNS)

            walks_str = "" if walks == 0 else f"  {walks} BB"
            doubles_str = "" if doubles == 0 else f"  {doubles} 2B"
            triples_str = "" if triples == 0 else f"  {triples} 3B"
            homeruns_str = "" if homeruns == 0 else f"  {homeruns} HR"
            hit_totals = f"{hits} FOR {abs}{walks_str}{doubles_str}{triples_str}" if include_hit_totals else ""

            return f"{name}{self.slashline}{hit_totals}{homeruns_str}"
        else:
            era = self.stat(StatCategory.ERA)
            whip = self.stat(StatCategory.WHIP)
            ip = round(self.stat(StatCategory.IP))
            return f"{name} {era} ERA | {whip} WHIP | {ip} IP"


class SimStatLine(BaseModel):
    """A statline with its rate stats already computed.

    `Stats` derives BA/OBP/SLG/OPS/ERA/WHIP as Python properties and OPS+/wRC+ as methods
    needing league context, so none of them survive `model_dump()`. Materializing here is what
    keeps the frontend from having to reimplement wOBA math. Lives next to `Stats` (rather than in
    `summary.py`, where it's consumed) so `awards.py` can build these without a circular import
    between `summary.py` and `awards.py`.
    """

    id: str
    name: str
    team: Optional[str] = None
    position: Optional[str] = None
    points: int = 0
    command: float = 0
    player_type: Optional[str] = None
    stats: dict[str, float] = {}
    # ID OF THE ROSTER SLOT'S CardSource, WHEN THIS PLAYER IS ON THE TAKEOVER TEAM'S OWN ROSTER -
    # THE SAME (card_id, card_source) PAIR `useCardMap` FETCHES ROSTER CARDS WITH ON THE FRONTEND.
    card_source: Optional[str] = None

    @classmethod
    def build(cls, stats: 'Stats', categories: list[StatCategory], league_stats: Optional['Stats'], woba_weights: dict[str, float], card_source: Optional[str] = None) -> 'SimStatLine':
        values: dict[str, float] = {}
        for category in categories:
            value = stats.stat(category, league_stats=league_stats, woba_weights=woba_weights, combine_1b_and_1b_plus=True)
            if isinstance(value, (int, float)):
                values[category.value] = round(float(value), 3)
        return cls(
            # A BUILDER/TAKEOVER PLAYER IS KEYED INTERNALLY UNDER A PREFIXED id (SEE `builder_sim_id`);
            # THE FRONTEND LINKS ROWS TO REAL CARDS BY `card_id`, SO EXPOSE THE BARE ONE HERE.
            id=real_card_id(stats.id), name=stats.name, team=stats.team, position=stats.position,
            points=stats.points, command=stats.command,
            player_type=stats.player_type.value if stats.player_type else None,
            stats=values, card_source=card_source,
        )


class StatsGroup:
    """A keyed collection of statlines (per player id or per game id)."""

    def __init__(self, year: int, name: str = "") -> None:
        self.name = name
        self.year = year
        self.stats: dict[str, Stats] = {}

    @classmethod
    def from_stats_list(cls, year: int, stats_list: list[Stats], name: str = "") -> 'StatsGroup':
        group = cls(year=year, name=name)
        group.stats = {stats.id: stats for stats in stats_list}
        return group

    def update_stats_for_player(self, player, additional_stats: Stats) -> None:
        self.update_individual_stats(id=player.id, stats=additional_stats)

    def merge(self, additional_stats_group: 'StatsGroup') -> None:
        self.merge_stats_dict(stats_dict=additional_stats_group.stats)

    def merge_stats_dict(self, stats_dict: dict[str, Stats]) -> None:
        """MERGES DICT WITH MULTIPLE PLAYER STATS"""
        for id, stats in stats_dict.items():
            self.update_individual_stats(id=id, stats=stats)

    def update_individual_stats(self, id: str, stats: Stats) -> None:
        if id in self.stats.keys():
            self.stats[id].merge(stats)
        else:
            self.stats[id] = stats

    def stats_for_id(self, id: str) -> Stats:
        return self.stats.get(id, Stats(id=id))

    def aggregated_stats(self, type: PlayerType, name: str = "SIM") -> Stats:
        total_stats = Stats(id=name, name=name, player_type=type)
        for stats in self.stats.values():
            if stats.player_type == type:
                total_stats.merge(stats)
        return total_stats

    def avg_for_stat(self, type: PlayerType, category: StatCategory, decimal_places: int = 0) -> float:
        return round(statistics.mean([stats.stat(category) for stats in self.stats.values() if stats.player_type == type]), decimal_places)

    def top_players(self, type: PlayerType, stat: StatCategory, limit: int = 5, is_desc: bool = True, min_ip = 0, min_pa = 0) -> list[Stats]:
        """Ordered list of player statlines filtered by playing time minimums."""
        league_stats = self.aggregated_stats(type=type)
        woba_weights = load_woba_weights(year=self.year)
        stats_sorted = sorted(
            [stats for stats in self.stats.values() if (stats.player_type == type and stats.stat(StatCategory.IP) >= min_ip and stats.stat(StatCategory.PA) >= min_pa)],
            key=lambda stats: stats.stat(stat, league_stats=league_stats, woba_weights=woba_weights),
            reverse=is_desc
        )
        return stats_sorted[:limit] if limit else stats_sorted

    def stats_list_for_type(self, type: PlayerType) -> list[Stats]:
        return [stats for stats in self.stats.values() if (stats.player_type == type)]


def _real_stats_to_totals(raw_stats: dict, player_type: PlayerType) -> dict[str, float]:
    """Archive-style raw stats (uppercase bref keys, e.g. `PlayerArchive.stats`) -> a
    `Stats.totals`-shaped counting-stat dict, ready for `Stats.merge_totals`.

    Filters down to `StatCategory` keys and lowercases them; for a pitcher, also converts bref's
    `.1`/`.2` partial-inning IP notation to thirds and derives `er` from `earned_run_avg`, since
    not every archive row carries a raw ER counting field. Shared by `real_life_stats_to_compare_to_sim`
    (a full season's real stats, for the CLI's `--show_real_life_comparison`) and
    `PlayerStatsGroup.merge_real_season_stats` (a rest-of-season projection's real-to-date stats).
    """
    allowed_stats_str = [s.value.lower() for s in StatCategory] + ['earned_run_avg']
    stats = {k.lower(): v for k, v in raw_stats.items() if k.lower() in allowed_stats_str and isinstance(v, (int, float))}
    if player_type == PlayerType.PITCHER:
        ip = stats.get('ip', 0.0)
        integer_part = int(ip)
        # ROUNDED - bref's FRACTIONAL NOTATION IS ALWAYS EXACTLY .0/.1/.2, BUT e.g. `62.1 - 62`
        # LANDS ON 0.10000000000000142 IN FLOATING POINT, SO AN UNROUNDED `== 0.1` CHECK MISSES IT
        # AND SILENTLY DROPS THE PARTIAL INNING.
        fractional_part = round(ip - integer_part, 2)
        if fractional_part == 0.1:
            ip = integer_part + (1 / 3)
        elif fractional_part == 0.2:
            ip = integer_part + (2 / 3)
        else:
            ip = integer_part
        stats['er'] = int(round((stats.get('earned_run_avg', 0.0) * ip / 9)))
        stats['ip'] = ip
        stats.pop('earned_run_avg', None)
    return stats


class PlayerStatsGroup(StatsGroup):
    """StatsGroup seeded with identity statlines for a list of live SimPlayers."""

    def __init__(self, players: list, year: int, name: str = "") -> None:
        self.players = players
        super().__init__(year=year, name=name)
        self.stats = {
            p.id: Stats(
                id=p.id, name=p.name, player_type=p.player_type, player_sub_type=p.player_sub_type, position=p.primary_position.value,
                team=p.team, points=p.points, speed=p.speed, command=p.chart.command,
                real_ops=p.real_ops,
                is_rookie=p.card.stats_for_card.get('is_rookie', False),
                defense=p.card.positions_and_defense.get(p.primary_position, 0),
            )
            for p in self.players
        }

    def player_for_id(self, id: str):
        players_w_id = [p for p in self.players if p.id == id]
        return players_w_id[0] if players_w_id else None

    def real_life_stats_to_compare_to_sim(self, type: PlayerType, name: str = "REAL") -> Stats:
        total_stats = Stats(id=name, name=name, player_type=type)
        players_in_sim = list(self.stats.keys())
        for player in self.players:
            is_included = player.player_type == type and player.id in players_in_sim
            if is_included:
                total_stats.merge_totals(_real_stats_to_totals(player.stats, type))
        return total_stats

    def merge_real_season_stats(self, raw_stats_by_id: dict[str, dict]) -> int:
        """Merge each player's real archive statline into their totals - a rest-of-season
        projection's seed for individual stat lines, the counterpart to `Season._build_season_teams`
        seeding each club's win-loss record. Simulated games accumulate on top afterward.

        Only players already in this group (i.e. on a simulated roster) are affected - anything
        else in `raw_stats_by_id` is ignored. Team attribution needs no special handling: both a
        player's sim roster placement (`ShowdownPlayerCard.team`) and their archive row's team are
        independently derived from the same `stats['team_ID']`, so a mid-season-traded player's
        merged totals land on the same club the sim already has them rostered under.

        Returns how many players were merged, for a status message.
        """
        merged = 0
        for player_id, stats_obj in self.stats.items():
            raw = raw_stats_by_id.get(player_id)
            if not raw:
                continue
            stats_obj.merge_totals(_real_stats_to_totals(raw, stats_obj.player_type))
            merged += 1
        return merged


class PitchingLog(BaseModel):

    daily_appearances: dict[date, dict[str, float]] = {}       # KEY: DATE, VALUE: {PITCHER ID: IP}

    def log_pitcher_stats(self, game_date: date, stats: list[Stats]) -> None:
        for statline in stats:

            # ACCUMULATE, DON'T OVERWRITE: A TEAM CAN PLAY TWICE ON ONE DATE (DOUBLEHEADER), AND BOTH
            # OUTINGS COUNT TOWARD THE PITCHER'S WORKLOAD FOR REST PURPOSES.
            data_for_day = self.daily_appearances.get(game_date, {})
            data_for_day[statline.id] = data_for_day.get(statline.id, 0) + statline.stat(StatCategory.IP)
            self.daily_appearances[game_date] = data_for_day

    def recent_ip_by_pitcher(self, game_date: date, days_back: int) -> dict[str, float]:
        """Innings thrown per pitcher over the last `days_back` days (inclusive of game_date)."""
        totals: dict[str, float] = {}
        for offset in range(days_back + 1):
            for pitcher_id, ip in self.daily_appearances.get(game_date - timedelta(days=offset), {}).items():
                totals[pitcher_id] = totals.get(pitcher_id, 0) + ip
        return totals

    def pitcher_ids_with_recent_workload(self, game_date: date, days_back: int, ip_cutoff: float) -> dict[str, float]:
        """Pitchers whose innings over the last `days_back` days meet or exceed `ip_cutoff`.

        Walks only the dates in the window via `daily_appearances` rather than scanning every
        pitcher's full season log, so cost stays constant as the season grows.
        """

        totals = self.recent_ip_by_pitcher(game_date=game_date, days_back=days_back)
        return {pid: ip for pid, ip in totals.items() if ip >= ip_cutoff}


# ------------------------------------------------------------------------
# REAL LIFE REFERENCE DATA (real_stats/*.csv)
# ------------------------------------------------------------------------

_REAL_STATS_DIR = os.path.join(os.path.dirname(__file__), 'real_stats')

@lru_cache(maxsize=None)
def load_woba_weights(year: int) -> dict[str, float]:
    """Fangraphs wOBA weights for a season, keyed by lowercased column name."""
    with open(os.path.join(_REAL_STATS_DIR, 'league_wOBA_weights.csv'), encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if int(row['Season']) == int(year):
                return {k.lower(): (float(v) if v not in (None, '') else 0) for k, v in row.items()}
    return {}

@lru_cache(maxsize=None)
def load_real_league_avgs(year: int, type: PlayerType) -> Stats:
    """Actual MLB league totals for a season, used to benchmark sim accuracy."""
    columns = ['IP','HR','BB','IBB','HBP','H','ER','SO','G'] if type == PlayerType.PITCHER else ['PA','AB','R','H','1B','2B','3B','HR','RBI','SB','CS','BB','SO','HBP','SF','IBB','G','GDP']
    file_name = f'league_averages_{type.value.lower()}.csv'
    with open(os.path.join(_REAL_STATS_DIR, file_name), encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if int(row['Year']) == int(year):
                totals = {col.lower(): float(row[col]) if row.get(col) not in (None, '') else 0 for col in columns if col in row}
                return Stats(id="LG AVG", name="REAL", player_type=type, totals=totals)
    raise ValueError(f"Empty Stats for {year}")
