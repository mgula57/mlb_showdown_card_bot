from __future__ import annotations
from ..card.chart import ChartCategory


def advance_runners(
    runners: dict[int, str],
    outcome: ChartCategory,
    batter_name: str,
    outs_before: int,
    stolen_base_cap: int | None = None,
    batter_sbs: int = 0,
) -> tuple[dict[int, str], int, int, bool, bool | None]:
    """Compute the new base state and scoring after an at-bat outcome.

    Returns:
        (new_runners, runs_scored, rbi, stolen_base_attempt, stolen_base_success)
    """
    match outcome:
        case ChartCategory.HR:
            runs = len(runners) + 1
            return {}, runs, runs, False, None

        case ChartCategory._3B:
            runs = len(runners)
            return {3: batter_name}, runs, runs, False, None

        case ChartCategory._2B:
            runs = sum(1 for b in (2, 3) if b in runners)
            new_runners: dict[int, str] = {2: batter_name}
            if 1 in runners:
                new_runners[3] = runners[1]
            return new_runners, runs, runs, False, None

        case ChartCategory._1B:
            runs = 1 if 3 in runners else 0
            new_runners = {1: batter_name}
            if 2 in runners:
                new_runners[3] = runners[2]
            if 1 in runners:
                new_runners[2] = runners[1]
            return new_runners, runs, runs, False, None

        case ChartCategory._1B_PLUS:
            # Apply single first, then attempt steal of 2B if open
            runs = 1 if 3 in runners else 0
            new_runners = {1: batter_name}
            if 2 in runners:
                new_runners[3] = runners[2]
            if 1 in runners:
                new_runners[2] = runners[1]
            # Steal attempt only if 2B is unoccupied and under the cap
            at_cap = stolen_base_cap is not None and batter_sbs >= stolen_base_cap
            if 2 not in new_runners and not at_cap:
                del new_runners[1]
                new_runners[2] = batter_name
                return new_runners, runs, runs, True, True
            return new_runners, runs, runs, True, False

        case ChartCategory.BB:
            new_runners, runs = _walk_advance(runners, batter_name)
            return new_runners, runs, runs, False, None

        case ChartCategory.SO | ChartCategory.PU:
            return dict(runners), 0, 0, False, None

        case ChartCategory.GB:
            # Out; runner on 3B scores if fewer than 2 outs
            if outs_before < 2 and 3 in runners:
                new_runners = {b: r for b, r in runners.items() if b != 3}
                return new_runners, 1, 1, False, None
            return dict(runners), 0, 0, False, None

        case ChartCategory.FB:
            # Out; runner on 3B tags up and scores if fewer than 2 outs
            if outs_before < 2 and 3 in runners:
                new_runners = {b: r for b, r in runners.items() if b != 3}
                return new_runners, 1, 1, False, None
            return dict(runners), 0, 0, False, None

        case _:
            return dict(runners), 0, 0, False, None


def _walk_advance(runners: dict[int, str], batter_name: str) -> tuple[dict[int, str], int]:
    """Force-advance runners on a walk. Only runners in a continuous chain from 1B are pushed."""
    new_runners: dict[int, str] = {}
    runs = 0

    if 1 in runners:
        if 2 in runners:
            if 3 in runners:
                # Bases loaded: force all runners
                runs = 1
                new_runners[3] = runners[2]
                new_runners[2] = runners[1]
            else:
                # 1B and 2B: 2B advances to 3B, 1B advances to 2B
                new_runners[3] = runners[2]
                new_runners[2] = runners[1]
        else:
            # Only 1B occupied (chain stops): 1B advances to 2B; 3B (if present) stays
            new_runners[2] = runners[1]
            if 3 in runners:
                new_runners[3] = runners[3]
    else:
        # 1B empty: no chain; all existing runners stay
        new_runners = dict(runners)

    new_runners[1] = batter_name
    return new_runners, runs
