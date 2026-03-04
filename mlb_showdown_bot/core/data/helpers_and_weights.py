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