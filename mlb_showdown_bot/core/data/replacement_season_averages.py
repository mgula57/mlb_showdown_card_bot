from copy import deepcopy
from typing import Any

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

# -----------------------------------
# MARK: - HELPER FUNCTIONS
# -----------------------------------
def _num(value: Any, default: float = 0.0) -> float:
    """Convert value to float if it's a number, otherwise return default."""
    return float(value) if isinstance(value, (int, float)) else default

def _round_if_float(value: Any, digits: int = 3) -> Any:
    """Round value to specified digits if it's a float, otherwise return as is."""
    return round(value, digits) if isinstance(value, float) else value


# -----------------------------------
# MARK: - CALCULATE REPLACEMENT-LEVEL AVERAGES
# -----------------------------------

def get_replacement_hitting_avgs(
    year: int,
    runs_below_avg: float = 20.0,
    pa_basis: float = 600.0,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build replacement-level batting environment from league averages.

    Replacement is applied as a fixed run gap:
        target_run_rate = league_run_rate - (runs_below_avg / pa_basis)

    Examples:
        - WAR-style baseline: runs_below_avg=20, pa_basis=600
        - Equivalent on 400 PA basis: runs_below_avg=13.333, pa_basis=400
    """
    if year not in MLB_SEASON_AVGS:
        raise KeyError(f"No league averages found for year {year}")

    if pa_basis <= 0:
        raise ValueError("pa_basis must be > 0")

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
    target_run_rate = max(0.0, league_run_rate - (runs_below_avg / pa_basis))

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

    stat_line["_replacement_runs_below_avg"] = runs_below_avg
    stat_line["_replacement_pa_basis"] = pa_basis
    stat_line["_replacement_hit_scale"] = hit_scale

    for key, value in list(stat_line.items()):
        stat_line[key] = _round_if_float(value)

    return stat_line


def build_replacement_hitting_table(
    runs_below_avg: float = 20.0,
    pa_basis: float = 600.0,
    weights: dict[str, float] | None = None,
) -> dict[int, dict[str, Any]]:
    """Build replacement-level table for all seasons in MLB_SEASON_AVGS."""
    return {
        year: get_replacement_hitting_avgs(
            year=year,
            runs_below_avg=runs_below_avg,
            pa_basis=pa_basis,
            weights=weights,
        )
        for year in MLB_SEASON_AVGS
    }


def get_replacement_pitching_avgs(
    year: int,
    runs_above_avg: float = 20.0,
    pa_basis: float = 600.0,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build replacement-level pitching environment from league averages.

    Replacement pitcher baseline is worse than average and therefore allows
    more run value per PA.
    """
    if year not in MLB_SEASON_AVGS:
        raise KeyError(f"No league averages found for year {year}")

    if pa_basis <= 0:
        raise ValueError("pa_basis must be > 0")

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
    target_run_rate = league_run_rate + (runs_above_avg / pa_basis)

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

    if isinstance(base_line.get("R/G"), (int, float)):
        stat_line["R/G"] = _num(base_line.get("R/G")) * ratio
        stat_line["R"] = stat_line["R/G"]

    stat_line["_replacement_runs_above_avg"] = runs_above_avg
    stat_line["_replacement_pa_basis"] = pa_basis
    stat_line["_replacement_hit_scale"] = hit_scale

    for key, value in list(stat_line.items()):
        stat_line[key] = _round_if_float(value)

    return stat_line


def build_replacement_pitching_table(
    runs_above_avg: float = 20.0,
    pa_basis: float = 600.0,
    weights: dict[str, float] | None = None,
) -> dict[int, dict[str, Any]]:
    """Build replacement-level pitching table for all seasons in MLB_SEASON_AVGS."""
    return {
        year: get_replacement_pitching_avgs(
            year=year,
            runs_above_avg=runs_above_avg,
            pa_basis=pa_basis,
            weights=weights,
        )
        for year in MLB_SEASON_AVGS
    }

# Convenience preset (WAR-style ~20 runs below average / 600 PA)
MLB_REPLACEMENT_HITTING_AVGS = build_replacement_hitting_table()
MLB_REPLACEMENT_PITCHING_AVGS = build_replacement_pitching_table()
