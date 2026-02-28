from copy import deepcopy
from typing import Any

from ..shared.player_position import PlayerType, Position, PlayerSubType

from .mlb_season_averages import MLB_SEASON_AVGS

# -----------------------------------
# MARK: - REPLACEMENT-LEVEL WEIGHTS
# -----------------------------------
DEFAULT_LINEAR_WEIGHTS: dict[str, float] = {
    "BB": 0.69,
    "HBP": 0.72,
    "1B": 0.88,
    "2B": 1.25,
    "3B": 1.60,
    "HR": 2.05,
}

REPLACEMENT_RUN_GAP_PA_BASIS = 600.0

COUNTING_STATS_TO_SCALE_FOR_PA_BASIS: tuple[str, ...] = (
    "1B",
    "2B",
    "3B",
    "AB",
    "BB",
    "BIP",
    "CS",
    "GDP",
    "H",
    "HBP",
    "HR",
    "IBB",
    "R",
    "RBI",
    "SB",
    "SF",
    "SH",
    "SO",
    "TB",
)

# -----------------------------------
# MARK: - HELPER FUNCTIONS
# -----------------------------------
def _num(value: Any, default: float = 0.0) -> float:
    """Convert value to float if it's a number, otherwise return default."""
    return float(value) if isinstance(value, (int, float)) else default

def _round_if_float(value: Any, digits: int = 3) -> Any:
    """Round value to specified digits if it's a float, otherwise return as is."""
    return round(value, digits) if isinstance(value, float) else value


def _scale_counting_stats_to_pa_basis(stat_line: dict[str, Any], source_pa: float, target_pa: float) -> None:
    """Scale counting stats so returned values represent totals for target_pa."""
    if source_pa <= 0 or target_pa <= 0:
        return

    scale_factor = target_pa / source_pa
    for stat in COUNTING_STATS_TO_SCALE_FOR_PA_BASIS:
        if isinstance(stat_line.get(stat), (int, float)):
            stat_line[stat] = _num(stat_line[stat]) * scale_factor

    stat_line["PA"] = target_pa


def convert_replacement_stats_to_pa_basis(stats: dict[str, Any], pa_basis: float) -> dict[str, Any]:
    """Convert replacement stat line to a target PA basis.

    Core replacement calculations are calibrated on a fixed 600 PA run-gap basis.
    Use this function to convert resulting counting stats to a display/calculation basis.
    """
    if pa_basis <= 0:
        raise ValueError("pa_basis must be > 0")

    converted_stats = deepcopy(stats)
    source_pa = _num(converted_stats.get("PA"), default=REPLACEMENT_RUN_GAP_PA_BASIS)
    _scale_counting_stats_to_pa_basis(stat_line=converted_stats, source_pa=source_pa, target_pa=pa_basis)
    converted_stats["_converted_pa_basis"] = pa_basis

    for key, value in list(converted_stats.items()):
        converted_stats[key] = _round_if_float(value)

    return converted_stats


# -----------------------------------
# MARK: - CALCULATE REPLACEMENT-LEVEL AVERAGES
# -----------------------------------

def get_replacement_hitting_avgs(
    year: int,
    runs_below_avg: float = 30.0,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build replacement-level batting environment from league averages.

    Replacement is applied as a fixed run gap:
        target_run_rate = league_run_rate - (runs_below_avg / 600)

    Examples:
        - WAR-style baseline: runs_below_avg=30 over 600 PA
        - To convert output to another PA basis, use convert_replacement_stats_to_pa_basis(...)
    """
    if year not in MLB_SEASON_AVGS:
        raise KeyError(f"No league averages found for year {year}")

    stat_line = deepcopy(MLB_SEASON_AVGS[year])
    linear_weights = weights or DEFAULT_LINEAR_WEIGHTS

    pa = _num(stat_line.get("PA"))
    if pa <= 0:
        raise ValueError(f"Invalid PA value for year {year}")

    rates = {
        "BB": _num(stat_line.get("BB")) / pa,
        "HBP": _num(stat_line.get("HBP")) / pa,
        "1B": _num(stat_line.get("1B")) / pa,
        "2B": _num(stat_line.get("2B")) / pa,
        "3B": _num(stat_line.get("3B")) / pa,
        "HR": _num(stat_line.get("HR")) / pa,
    }

    league_run_rate = sum(rates[key] * linear_weights[key] for key in ("BB", "HBP", "1B", "2B", "3B", "HR"))
    target_run_rate = max(0.0, league_run_rate - (runs_below_avg / REPLACEMENT_RUN_GAP_PA_BASIS))

    fixed_component = rates["BB"] * linear_weights["BB"] + rates["HBP"] * linear_weights["HBP"]
    hit_component = sum(rates[key] * linear_weights[key] for key in ("1B", "2B", "3B", "HR"))

    if hit_component <= 0:
        hit_scale = 0.0
    else:
        hit_scale = max(0.0, (target_run_rate - fixed_component) / hit_component)

    for stat in ("1B", "2B", "3B", "HR"):
        if isinstance(stat_line.get(stat), (int, float)):
            stat_line[stat] = _num(stat_line[stat]) * hit_scale

    ab = _num(stat_line.get("AB"))
    bb = _num(stat_line.get("BB"))
    hbp = _num(stat_line.get("HBP"))
    sf = _num(stat_line.get("SF"))

    one_b = _num(stat_line.get("1B"))
    two_b = _num(stat_line.get("2B"))
    three_b = _num(stat_line.get("3B"))
    hr = _num(stat_line.get("HR"))

    hits = one_b + two_b + three_b + hr
    total_bases = one_b + (2 * two_b) + (3 * three_b) + (4 * hr)

    stat_line["H"] = hits
    stat_line["TB"] = total_bases

    if ab > 0:
        stat_line["BA"] = hits / ab
        stat_line["SLG"] = total_bases / ab

    obp_denom = ab + bb + hbp + sf
    if obp_denom > 0:
        stat_line["OBP"] = (hits + bb + hbp) / obp_denom

    if isinstance(stat_line.get("OBP"), (int, float)) and isinstance(stat_line.get("SLG"), (int, float)):
        stat_line["OPS"] = _num(stat_line["OBP"]) + _num(stat_line["SLG"])

    ratio = (target_run_rate / league_run_rate) if league_run_rate > 0 else 0.0
    base_line = MLB_SEASON_AVGS[year]
    if isinstance(base_line.get("R/G"), (int, float)):
        stat_line["R/G"] = _num(base_line.get("R/G")) * ratio
        stat_line["R"] = stat_line["R/G"]
    if isinstance(base_line.get("RBI"), (int, float)):
        stat_line["RBI"] = _num(base_line.get("RBI")) * ratio

    _scale_counting_stats_to_pa_basis(stat_line=stat_line, source_pa=pa, target_pa=REPLACEMENT_RUN_GAP_PA_BASIS)

    stat_line["_replacement_runs_below_avg"] = runs_below_avg
    stat_line["_replacement_pa_basis"] = REPLACEMENT_RUN_GAP_PA_BASIS
    stat_line["_replacement_hit_scale"] = hit_scale

    for key, value in list(stat_line.items()):
        stat_line[key] = _round_if_float(value)

    return stat_line


def build_replacement_hitting_table(
    runs_below_avg: float = 30.0,
    weights: dict[str, float] | None = None,
) -> dict[int, dict[str, Any]]:
    """Build replacement-level table for all seasons in MLB_SEASON_AVGS."""
    return {
        year: get_replacement_hitting_avgs(
            year=year,
            runs_below_avg=runs_below_avg,
            weights=weights,
        )
        for year in MLB_SEASON_AVGS
    }


def get_replacement_pitching_avgs(
    year: int,
    runs_above_avg: float = 30.0,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build replacement-level pitching environment from league averages.

    Replacement pitcher baseline is worse than average and therefore allows
    more run value per PA.
    """
    if year not in MLB_SEASON_AVGS:
        raise KeyError(f"No league averages found for year {year}")

    stat_line = deepcopy(MLB_SEASON_AVGS[year])
    linear_weights = weights or DEFAULT_LINEAR_WEIGHTS

    pa = _num(stat_line.get("PA"))
    if pa <= 0:
        raise ValueError(f"Invalid PA value for year {year}")

    rates = {
        "BB": _num(stat_line.get("BB")) / pa,
        "HBP": _num(stat_line.get("HBP")) / pa,
        "1B": _num(stat_line.get("1B")) / pa,
        "2B": _num(stat_line.get("2B")) / pa,
        "3B": _num(stat_line.get("3B")) / pa,
        "HR": _num(stat_line.get("HR")) / pa,
    }

    league_run_rate = sum(rates[key] * linear_weights[key] for key in ("BB", "HBP", "1B", "2B", "3B", "HR"))
    target_run_rate = league_run_rate + (runs_above_avg / REPLACEMENT_RUN_GAP_PA_BASIS)

    fixed_component = rates["BB"] * linear_weights["BB"] + rates["HBP"] * linear_weights["HBP"]
    hit_component = sum(rates[key] * linear_weights[key] for key in ("1B", "2B", "3B", "HR"))

    if hit_component <= 0:
        hit_scale = 1.0
    else:
        hit_scale = max(0.0, (target_run_rate - fixed_component) / hit_component)

    for stat in ("1B", "2B", "3B", "HR"):
        if isinstance(stat_line.get(stat), (int, float)):
            stat_line[stat] = _num(stat_line[stat]) * hit_scale

    base_line = MLB_SEASON_AVGS[year]

    if isinstance(stat_line.get("SO"), (int, float)) and hit_scale > 0:
        stat_line["SO"] = _num(base_line.get("SO")) / hit_scale

    if isinstance(stat_line.get("SO9"), (int, float)) and hit_scale > 0:
        stat_line["SO9"] = _num(base_line.get("SO9")) / hit_scale

    one_b = _num(stat_line.get("1B"))
    two_b = _num(stat_line.get("2B"))
    three_b = _num(stat_line.get("3B"))
    hr = _num(stat_line.get("HR"))
    hits = one_b + two_b + three_b + hr
    total_bases = one_b + (2 * two_b) + (3 * three_b) + (4 * hr)

    stat_line["H"] = hits
    stat_line["TB"] = total_bases

    ab = _num(stat_line.get("AB"))
    bb = _num(stat_line.get("BB"))
    hbp = _num(stat_line.get("HBP"))
    sf = _num(stat_line.get("SF"))

    if ab > 0:
        stat_line["BA"] = hits / ab
        stat_line["SLG"] = total_bases / ab

    obp_denom = ab + bb + hbp + sf
    if obp_denom > 0:
        stat_line["OBP"] = (hits + bb + hbp) / obp_denom

    if isinstance(stat_line.get("OBP"), (int, float)) and isinstance(stat_line.get("SLG"), (int, float)):
        stat_line["OPS"] = _num(stat_line["OBP"]) + _num(stat_line["SLG"])

    ratio = (target_run_rate / league_run_rate) if league_run_rate > 0 else 1.0
    if isinstance(base_line.get("ERA"), (int, float)):
        stat_line["ERA"] = _num(base_line.get("ERA")) * ratio

    if isinstance(base_line.get("WHIP"), (int, float)):
        stat_line["WHIP"] = _num(base_line.get("WHIP")) * ratio

    # MAKE GO/AO RATIOS FAVOR AO MORE
    if isinstance(base_line.get("GO/AO"), (int, float)):
        base_go_ao = _num(base_line.get("GO/AO"))
        adjusted_go_ao = base_go_ao * (0.65)  # Shift towards more fly balls for worse pitchers
        stat_line["GO/AO"] = adjusted_go_ao

    if isinstance(base_line.get("R/G"), (int, float)):
        stat_line["R/G"] = _num(base_line.get("R/G")) * ratio
        stat_line["R"] = stat_line["R/G"]

    _scale_counting_stats_to_pa_basis(stat_line=stat_line, source_pa=pa, target_pa=REPLACEMENT_RUN_GAP_PA_BASIS)

    stat_line["_replacement_runs_above_avg"] = runs_above_avg
    stat_line["_replacement_pa_basis"] = REPLACEMENT_RUN_GAP_PA_BASIS
    stat_line["_replacement_hit_scale"] = hit_scale

    for key, value in list(stat_line.items()):
        stat_line[key] = _round_if_float(value)

    return stat_line


def build_replacement_pitching_table(
    runs_above_avg: float = 30.0,
    weights: dict[str, float] | None = None,
) -> dict[int, dict[str, Any]]:
    """Build replacement-level pitching table for all seasons in MLB_SEASON_AVGS."""
    return {
        year: get_replacement_pitching_avgs(
            year=year,
            runs_above_avg=runs_above_avg,
            weights=weights,
        )
        for year in MLB_SEASON_AVGS
    }


def build_replacement_level_stats_for_card(
    year: int,
    player_type: PlayerType,
    positions: list[Position] | None = None,
    runs_below_avg: float = 30.0,
    pa_basis: float = 600.0,
    weights: dict[str, float] | None = None,
    original_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create stats that are compatible with card generation based on replacement-level averages."""
    
    if type(player_type) == str:
        player_type = PlayerType(player_type)
        
    # Define subtype:
    if player_type == PlayerType.PITCHER:
        subtype = PlayerSubType.STARTING_PITCHER if positions and Position.SP in positions else PlayerSubType.RELIEF_PITCHER
    else:
        subtype = PlayerSubType.POSITION_PLAYER

    if original_stats is None:
        if player_type == PlayerType.HITTER:
            original_stats = get_replacement_hitting_avgs(year, runs_below_avg, weights)
        else:
            original_stats = get_replacement_pitching_avgs(year, runs_below_avg, weights)

    if pa_basis != REPLACEMENT_RUN_GAP_PA_BASIS:
        original_stats = convert_replacement_stats_to_pa_basis(stats=original_stats, pa_basis=pa_basis)
    
    card_stats = dict(original_stats)
    card_stats["name"] = f"Replacement {player_type.value} {year}"
    card_stats["type"] = player_type.value
    card_stats["year_ID"] = str(year)
    card_stats["team_ID"] = card_stats.get("team_ID") or "MLB"
    card_stats["lg_ID"] = card_stats.get("lg_ID") or "MLB"
    card_stats["PA"] = card_stats.get("PA") or pa_basis
    card_stats["G"] = int(162 * (pa_basis / 650))  # Scale games based on PA basis (assuming 650 PA ~ full season)
    if player_type == PlayerType.PITCHER:
        card_stats["GS"] = int(30 * (pa_basis / 650)) if subtype == PlayerSubType.STARTING_PITCHER else 0
        card_stats["SV"] = 0
        card_stats["IP"] = float(int((180 if subtype == PlayerSubType.STARTING_PITCHER else 65) * (pa_basis / 650)))
        card_stats["IP/GS"] = 5 if subtype == PlayerSubType.STARTING_PITCHER else 0
    card_stats["hand"] = card_stats.get("hand") or "Right"
    card_stats["hand_throw"] = card_stats.get("hand_throw") or "Right"
    card_stats["award_summary"] = card_stats.get("award_summary") or ""
    card_stats["positions"] = (
        {"P": {"g": card_stats["G"]}} if player_type == PlayerType.PITCHER 
        else ( {"DH": {"g": card_stats["G"]}} if positions is None else {pos.value: {"g": card_stats["G"], 'drs': -12 * (pa_basis / 650)} for pos in positions} )
    )

    card_stats["batting_avg"] = card_stats.get("batting_avg") if card_stats.get("batting_avg") is not None else card_stats.get("BA", 0)
    card_stats["onbase_perc"] = card_stats.get("onbase_perc") if card_stats.get("onbase_perc") is not None else card_stats.get("OBP", 0)
    card_stats["slugging_perc"] = card_stats.get("slugging_perc") if card_stats.get("slugging_perc") is not None else card_stats.get("SLG", 0)
    card_stats["onbase_plus_slugging"] = card_stats.get("onbase_plus_slugging") if card_stats.get("onbase_plus_slugging") is not None else card_stats.get("OPS", 0)

    return card_stats

# Convenience preset (WAR-style ~20 runs below average / 600 PA)
MLB_REPLACEMENT_HITTING_AVGS = build_replacement_hitting_table()
MLB_REPLACEMENT_PITCHING_AVGS = build_replacement_pitching_table()
