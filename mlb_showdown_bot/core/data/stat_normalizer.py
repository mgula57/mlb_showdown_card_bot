from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

from .mlb_season_averages import MLB_SEASON_AVGS
from .helpers_and_weights import REPLACEMENT_RUN_GAP_PA_BASIS, num
from .replacement_season_averages import get_replacement_hitting_avgs, get_replacement_pitching_avgs
from .stat_reduction import shrink_stats_toward_baseline

# OUTCOME COUNTS A BASELINE NEEDS - SHRINKAGE BLENDS EACH ONE'S PER-PA RATE
BASELINE_OUTCOME_STATS: tuple[str, ...] = ("BB", "HBP", "1B", "2B", "3B", "HR", "SO")
# EXTRA COUNTS SUMMED INTO A PLAYER BASELINE SO ITS SLASH LINE CAN BE SUMMARIZED
BASELINE_SUMMARY_STATS: tuple[str, ...] = ("AB", "SF")

# A RELIEVER'S FULL SEASON IS ~60 IP, NOT A HITTER'S/STARTER'S 600 PA
RELIEVER_FULL_SAMPLE_IP = 60.0


class StatNormalizerType(str, Enum):
    """What a small real sample gets regressed toward (see `StatNormalizer`).

    League-based options build the baseline from that year's league environment. Player-based
    options build it from the player's own other archived seasons, falling back to replacement
    level when the player has none (ex: a rookie).
    """

    REPLACEMENT_LEVEL = "REPLACEMENT_LEVEL"
    LEAGUE_AVERAGE = "LEAGUE_AVERAGE"
    PLAYER_CAREER = "PLAYER_CAREER"
    PLAYER_LAST_YEAR = "PLAYER_LAST_YEAR"
    PLAYER_TRAILING_3 = "PLAYER_TRAILING_3"
    PLAYER_TRAILING_5 = "PLAYER_TRAILING_5"

    @property
    def label(self) -> str:
        match self:
            case StatNormalizerType.REPLACEMENT_LEVEL: return "Replacement Level"
            case StatNormalizerType.LEAGUE_AVERAGE: return "League Average"
            case StatNormalizerType.PLAYER_CAREER: return "Player Career Avg"
            case StatNormalizerType.PLAYER_LAST_YEAR: return "Player Last Year"
            case StatNormalizerType.PLAYER_TRAILING_3: return "Player Trailing 3 Years"
            case StatNormalizerType.PLAYER_TRAILING_5: return "Player Trailing 5 Years"

    @property
    def is_player_based(self) -> bool:
        return self.value.startswith("PLAYER_")

    @property
    def trailing_seasons(self) -> Optional[int]:
        """Number of prior seasons to use. None means every other season (career)."""
        match self:
            case StatNormalizerType.PLAYER_LAST_YEAR: return 1
            case StatNormalizerType.PLAYER_TRAILING_3: return 3
            case StatNormalizerType.PLAYER_TRAILING_5: return 5
            case _: return None

    # -----------------------------------
    # MARK: - BASELINES
    # -----------------------------------

    def league_baseline(self, year: int, is_pitcher: bool) -> dict[str, Any]:
        """Baseline stat line from the league environment. Raises KeyError for an unknown year."""
        match self:
            case StatNormalizerType.LEAGUE_AVERAGE:
                if year not in MLB_SEASON_AVGS:
                    raise KeyError(f"No league averages found for year {year}")
                return MLB_SEASON_AVGS[year]
            case _:
                return get_replacement_pitching_avgs(year=year) if is_pitcher else get_replacement_hitting_avgs(year=year)

    def player_baseline(self, seasons: dict[int, dict[str, Any]], card_years: list[int]) -> Optional[dict[str, float]]:
        """Sum the player's prior/other seasons into one baseline stat line.

        Args:
          seasons: Season stats keyed by year, already filtered to the card's player type.
          card_years: Years the card itself is built from. These never count toward the baseline.

        Returns:
          Summed outcome counts + PA, or None if no qualifying season has any PA.
        """
        if not self.is_player_based or len(card_years) == 0:
            return None

        other_years = sorted(y for y in seasons if y not in card_years)
        if self.trailing_seasons:
            # MOST RECENT SEASONS PLAYED BEFORE THE CARD (SKIPS A MISSED SEASON, EX: INJURY)
            other_years = [y for y in other_years if y < min(card_years)][-self.trailing_seasons:]

        baseline = {stat: 0.0 for stat in ("PA", *BASELINE_OUTCOME_STATS, *BASELINE_SUMMARY_STATS)}
        for year in other_years:
            for stat in baseline:
                baseline[stat] += num(seasons[year].get(stat))
        if baseline["PA"] <= 0:
            return None

        baseline["_years"] = other_years
        return baseline

    # -----------------------------------
    # MARK: - SAMPLE SIZE
    # -----------------------------------

    @staticmethod
    def full_sample_pa(year: int, is_reliever: bool) -> float:
        """PA at which a real sample is trusted outright. Relievers use ~60 IP worth of batters faced."""
        if not is_reliever:
            return REPLACEMENT_RUN_GAP_PA_BASIS
        league_pa_per_game = num(MLB_SEASON_AVGS.get(year, {}).get("PA"), default=38.0)
        return round(RELIEVER_FULL_SAMPLE_IP * league_pa_per_game / 9.0)


# -----------------------------------
# MARK: - SUMMARY
# -----------------------------------

class StatNormalizerSummaryStat(BaseModel):
    """One rate stat for the real sample, the baseline, and the blend the card is built from."""
    stat: str
    real: float
    baseline: float
    blended: float


class StatNormalizerSummary(BaseModel):
    """How much of the card came from the real sample vs. the normalizer's baseline, for display."""
    type: StatNormalizerType # EFFECTIVE TYPE (REPLACEMENT_LEVEL WHEN A PLAYER TYPE HAD NO OTHER SEASONS)
    label: str
    real_weight: float
    real_pa: float
    full_sample_pa: float
    baseline_years: Optional[list[int]] = None
    stats: list[StatNormalizerSummaryStat] = []

    @staticmethod
    def _rate_stats(stat_line: dict[str, Any], pa_per_ip: Optional[float]) -> dict[str, float]:
        """K%/OBP/SLG/OPS (+ WHIP when `pa_per_ip` is given) from a stat line's outcome counts."""
        pa = num(stat_line.get("PA"))
        if pa <= 0:
            return {}
        bb, hbp, sf = num(stat_line.get("BB")), num(stat_line.get("HBP")), num(stat_line.get("SF"))
        singles, doubles, triples, hr = (num(stat_line.get(stat)) for stat in ("1B", "2B", "3B", "HR"))
        hits = singles + doubles + triples + hr
        ab = num(stat_line.get("AB")) or (pa - bb - hbp - sf)
        obp_denom = ab + bb + hbp + sf
        obp = (hits + bb + hbp) / obp_denom if obp_denom > 0 else 0.0
        slg = (singles + 2 * doubles + 3 * triples + 4 * hr) / ab if ab > 0 else 0.0
        rates = {"OPS": obp + slg, "OBP": obp, "SLG": slg, "K%": num(stat_line.get("SO")) / pa}
        if pa_per_ip:
            # BASELINE WHIP IS AT THE REAL SAMPLE'S BATTERS PER INNING, SO THE BLEND IS A STRAIGHT WEIGHTED MIX
            rates["WHIP"] = (hits + bb) / pa * pa_per_ip
        return rates

    @classmethod
    def build(cls, type: StatNormalizerType, real: dict[str, Any], baseline: dict[str, Any], blended: dict[str, Any], full_sample_pa: float, real_ip: Optional[float] = None) -> 'StatNormalizerSummary':
        real_pa = num(real.get("PA"))
        pa_per_ip = (real_pa / real_ip) if real_ip else None
        real_rates, baseline_rates, blended_rates = (cls._rate_stats(line, pa_per_ip) for line in (real, baseline, blended))
        return cls(
            type=type,
            label=type.label,
            real_weight=round(num(blended.get("_baseline_shrink_real_weight"), default=1.0), 3),
            real_pa=real_pa,
            full_sample_pa=full_sample_pa,
            baseline_years=baseline.get("_years", None),
            stats=[
                StatNormalizerSummaryStat(stat=stat, real=round(real_rates[stat], 3), baseline=round(baseline_rates[stat], 3), blended=round(blended_rates[stat], 3))
                for stat in real_rates if stat in baseline_rates and stat in blended_rates
            ],
        )


# -----------------------------------
# MARK: - NORMALIZER
# -----------------------------------

class StatNormalizer(BaseModel):
    """Regresses a card's small real sample toward a baseline, weighted by how small the sample is.

    Attributes:
      type: What the sample is regressed toward.
      baseline: Pre-fetched player history for player-based types (see `card_generation.fetch_stat_normalizer_baseline`).
      summary: Real vs. baseline blend from the last `normalize` call, for display.
    """
    type: StatNormalizerType
    baseline: Optional[dict] = None
    summary: Optional[StatNormalizerSummary] = None

    @classmethod
    def from_input(cls, value: Any) -> Optional['StatNormalizer']:
        """Parse a user input (type string, enum, dict, or StatNormalizer), treating empty/"NONE" as no normalizer."""
        if value is None or isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(**value)
        value_str = str(value.value if isinstance(value, StatNormalizerType) else value).strip().upper()
        if value_str in ("", "NONE", "FALSE"):
            return None
        return cls(type=StatNormalizerType(value_str))

    def normalize(self, stats: dict[str, Any], year: int, is_pitcher: bool, real_ip: Optional[float] = None) -> tuple[dict[str, Any], list[str]]:
        """Regress `stats` toward this normalizer's baseline and store the blend in `summary`.

        Args:
          stats: Real stat line the card is built from.
          year: Season for league-based baselines and the reliever full-sample PA.
          is_pitcher: Whether to use the pitching replacement baseline and flag relievers.
          real_ip: Real innings pitched (decimal), for the WHIP summary.

        Returns:
          Tuple of the normalized stats and warnings to show on the card.
        """
        type = self.type
        warnings: list[str] = []
        baseline = self.baseline if type.is_player_based else None
        if type.is_player_based and not baseline:
            seasons_searched = f"seasons before {year}" if type.trailing_seasons else "other seasons"
            warnings.append(f"No {seasons_searched} were found for this player to use for {type.label}. Stats were regressed toward Replacement Level instead.")
            type = StatNormalizerType.REPLACEMENT_LEVEL
        baseline = baseline or type.league_baseline(year=year, is_pitcher=is_pitcher)

        is_reliever = is_pitcher and num(stats.get("GS")) < 0.5 * num(stats.get("G"))
        full_sample_pa = StatNormalizerType.full_sample_pa(year=year, is_reliever=is_reliever)
        normalized_stats = shrink_stats_toward_baseline(stats=stats, baseline=baseline, full_sample_pa=full_sample_pa)

        self.summary = StatNormalizerSummary.build(type=type, real=stats, baseline=baseline, blended=normalized_stats, full_sample_pa=full_sample_pa, real_ip=real_ip)
        warnings.append(f"Stats have been normalized toward {type.label}.")
        return normalized_stats, warnings
