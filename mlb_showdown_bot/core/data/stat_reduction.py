from copy import deepcopy
from typing import Any

from .helpers_and_weights import (
    DEFAULT_LINEAR_WEIGHTS, REPLACEMENT_RUN_GAP_PA_BASIS,
    num, round_if_float, scale_counting_stats_to_pa_basis
)


def nerf_stats_by_run_value(
    stats: dict[str, Any],
    runs_below_avg: float,
    is_pitcher: bool,
    run_gap_pa_basis: float = REPLACEMENT_RUN_GAP_PA_BASIS,
    weights: dict[str, float] | None = None,
    target_pa_basis: float | None = None,
) -> dict[str, Any]:
    """Reduce an arbitrary stat line by a fixed run gap rate.

    This function is independent of season league averages and can be applied to
    any stat dictionary that includes at least:
      - PA
      - BB, HBP, 1B, 2B, 3B, HR

        The reduction is calibrated as:
            - hitters: target_run_rate = source_run_rate - (runs_below_avg / run_gap_pa_basis)
            - pitchers: target_run_rate = source_run_rate + (runs_below_avg / run_gap_pa_basis)

    Notes:
      - BB and HBP rates are kept fixed.
      - Hit outcomes (1B/2B/3B/HR) are scaled proportionally to hit the target run rate.
      - If ``target_pa_basis`` is supplied, counting stats are scaled to that PA basis.
    """
    if run_gap_pa_basis <= 0:
        raise ValueError("run_gap_pa_basis must be > 0")

    stat_line = deepcopy(stats)
    linear_weights = weights or DEFAULT_LINEAR_WEIGHTS

    pa = num(stat_line.get("PA"))
    if pa <= 0:
        raise ValueError("stats must include PA > 0")

    rates = {
        "BB": num(stat_line.get("BB")) / pa,
        "HBP": num(stat_line.get("HBP")) / pa,
        "1B": num(stat_line.get("1B")) / pa,
        "2B": num(stat_line.get("2B")) / pa,
        "3B": num(stat_line.get("3B")) / pa,
        "HR": num(stat_line.get("HR")) / pa,
    }

    source_run_rate = sum(rates[key] * linear_weights[key] for key in ("BB", "HBP", "1B", "2B", "3B", "HR"))
    rate_adjustment = runs_below_avg / run_gap_pa_basis
    if is_pitcher:
        target_run_rate = max(0.0, source_run_rate + rate_adjustment)
    else:
        target_run_rate = max(0.0, source_run_rate - rate_adjustment)

    fixed_component = rates["BB"] * linear_weights["BB"] + rates["HBP"] * linear_weights["HBP"]
    hit_component = sum(rates[key] * linear_weights[key] for key in ("1B", "2B", "3B", "HR"))

    if hit_component <= 0:
        hit_scale = 0.0
    else:
        hit_scale = max(0.0, (target_run_rate - fixed_component) / hit_component)

    for stat in ("1B", "2B", "3B", "HR"):
        if isinstance(stat_line.get(stat), (int, float)):
            stat_line[stat] = num(stat_line[stat]) * hit_scale

    ab = num(stat_line.get("AB"))
    bb = num(stat_line.get("BB"))
    hbp = num(stat_line.get("HBP"))
    sf = num(stat_line.get("SF"))

    one_b = num(stat_line.get("1B"))
    two_b = num(stat_line.get("2B"))
    three_b = num(stat_line.get("3B"))
    hr = num(stat_line.get("HR"))

    hits = one_b + two_b + three_b + hr
    total_bases = one_b + (2 * two_b) + (3 * three_b) + (4 * hr)

    stat_line["H"] = hits
    stat_line["TB"] = total_bases

    if ab > 0:
        stat_line["batting_avg"] = hits / ab
        stat_line["slugging_perc"] = total_bases / ab

    obp_denom = ab + bb + hbp + sf
    if obp_denom > 0:
        stat_line["onbase_perc"] = (hits + bb + hbp) / obp_denom

    if isinstance(stat_line.get("onbase_perc"), (int, float)) and isinstance(stat_line.get("slugging_perc"), (int, float)):
        stat_line["onbase_plus_slugging"] = num(stat_line["onbase_perc"]) + num(stat_line["slugging_perc"])

    ratio = (target_run_rate / source_run_rate) if source_run_rate > 0 else 0.0
    for run_stat in ("R/G", "R", "RBI"):
        if isinstance(stat_line.get(run_stat), (int, float)):
            stat_line[run_stat] = num(stat_line[run_stat]) * ratio

    if target_pa_basis is not None:
        if target_pa_basis <= 0:
            raise ValueError("target_pa_basis must be > 0")
        scale_counting_stats_to_pa_basis(stat_line=stat_line, source_pa=pa, target_pa=target_pa_basis)

    stat_line["_run_rate_adjustment_runs_below_avg"] = runs_below_avg
    stat_line["_run_rate_adjustment_is_pitcher"] = is_pitcher
    stat_line["_run_rate_adjustment_pa_basis"] = run_gap_pa_basis
    stat_line["_run_rate_adjustment_hit_scale"] = hit_scale
    stat_line["_run_rate_adjustment_source_run_rate"] = source_run_rate
    stat_line["_run_rate_adjustment_target_run_rate"] = target_run_rate

    for key, value in list(stat_line.items()):
        stat_line[key] = round_if_float(value)

    return stat_line