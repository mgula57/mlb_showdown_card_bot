from typing import Any

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
def num(value: Any, default: float = 0.0) -> float:
    """Convert value to float if it's a number, otherwise return default."""
    return float(value) if isinstance(value, (int, float)) else default

def round_if_float(value: Any, digits: int = 3) -> Any:
    """Round value to specified digits if it's a float, otherwise return as is."""
    return round(value, digits) if isinstance(value, float) else value


def scale_counting_stats_to_pa_basis(stat_line: dict[str, Any], source_pa: float, target_pa: float) -> None:
    """Scale counting stats so returned values represent totals for target_pa."""
    if source_pa <= 0 or target_pa <= 0:
        return

    scale_factor = target_pa / source_pa
    for stat in COUNTING_STATS_TO_SCALE_FOR_PA_BASIS:
        if isinstance(stat_line.get(stat), (int, float)):
            stat_line[stat] = num(stat_line[stat]) * scale_factor

    stat_line["PA"] = target_pa


def recompute_derived_batting_stats(stat_line: dict[str, Any]) -> None:
    """Recompute H/TB/BA/OBP/SLG/OPS in place from 1B/2B/3B/HR/AB/BB/HBP/SF.

    Shared tail for any transform (run-value nerf, replacement-level shrinkage, ...) that
    rescales the underlying hit-type counts and needs the derived rate stats to stay consistent
    with them afterward.
    """
    one_b = num(stat_line.get("1B"))
    two_b = num(stat_line.get("2B"))
    three_b = num(stat_line.get("3B"))
    hr = num(stat_line.get("HR"))
    ab = num(stat_line.get("AB"))
    bb = num(stat_line.get("BB"))
    hbp = num(stat_line.get("HBP"))
    sf = num(stat_line.get("SF"))

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