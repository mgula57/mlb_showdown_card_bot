from __future__ import annotations
import random
from typing import Literal

from ..card.chart import ChartCategory
from ..card.showdown_player_card import ShowdownPlayerCard
from .base_state import advance_runners
from .models import AtBatResult
from .ruleset import SimulationRuleset

_HIT_OUTCOMES = {ChartCategory._1B, ChartCategory._1B_PLUS, ChartCategory._2B, ChartCategory._3B, ChartCategory.HR}


def resolve_at_bat(
    pitcher: ShowdownPlayerCard,
    batter: ShowdownPlayerCard,
    ruleset: SimulationRuleset,
    runners: dict[int, str],
    outs_before: int,
    batter_sbs: int = 0,
) -> tuple[AtBatResult, dict[int, str]]:
    """Roll dice and resolve an at-bat. Returns (AtBatResult, updated_runners)."""
    # Command check
    p_roll = random.randint(1, 20)
    b_roll = random.randint(1, 20)
    pitcher_wins = (p_roll + pitcher.chart.command) >= (b_roll + batter.chart.command)

    # Chart lookup — mistake pitch uses d24 when pitcher won
    if ruleset.mistake_pitch and pitcher_wins:
        chart_roll = random.randint(1, 24)
        if chart_roll > 20:
            # Mistake: hitter benefits even though pitcher won command check
            active_chart = batter.chart
            chart_owner: Literal['pitcher', 'batter'] = 'batter'
        else:
            active_chart = pitcher.chart
            chart_owner = 'pitcher'
    else:
        chart_roll = random.randint(1, 20)
        active_chart = pitcher.chart if pitcher_wins else batter.chart
        chart_owner = 'pitcher' if pitcher_wins else 'batter'

    outcome = active_chart.results.get(chart_roll, ChartCategory.GB)

    return _build_result(
        pitcher=pitcher,
        batter=batter,
        p_roll=p_roll,
        b_roll=b_roll,
        chart_owner=chart_owner,
        chart_roll=chart_roll,
        outcome=outcome,
        runners=runners,
        outs_before=outs_before,
        stolen_base_cap=ruleset.stolen_base_cap,
        batter_sbs=batter_sbs,
    )


def apply_outcome(
    pitcher: ShowdownPlayerCard,
    batter: ShowdownPlayerCard,
    outcome: ChartCategory,
    runners: dict[int, str],
    outs_before: int,
    ruleset: SimulationRuleset,
    batter_sbs: int = 0,
) -> tuple[AtBatResult, dict[int, str]]:
    """Apply a caller-provided outcome (live play). Skips dice rolls."""
    return _build_result(
        pitcher=pitcher,
        batter=batter,
        p_roll=0,
        b_roll=0,
        chart_owner='batter',  # unknown when manually applied
        chart_roll=0,
        outcome=outcome,
        runners=runners,
        outs_before=outs_before,
        stolen_base_cap=ruleset.stolen_base_cap,
        batter_sbs=batter_sbs,
    )


def _build_result(
    *,
    pitcher: ShowdownPlayerCard,
    batter: ShowdownPlayerCard,
    p_roll: int,
    b_roll: int,
    chart_owner: Literal['pitcher', 'batter'],
    chart_roll: int,
    outcome: ChartCategory,
    runners: dict[int, str],
    outs_before: int,
    stolen_base_cap: int | None,
    batter_sbs: int,
) -> tuple[AtBatResult, dict[int, str]]:
    new_runners, runs, rbi, sb_attempt, sb_success = advance_runners(
        runners=runners,
        outcome=outcome,
        batter_name=batter.name,
        outs_before=outs_before,
        stolen_base_cap=stolen_base_cap,
        batter_sbs=batter_sbs,
    )
    return AtBatResult(
        batter_name=batter.name,
        pitcher_name=pitcher.name,
        pitcher_roll=p_roll,
        batter_roll=b_roll,
        chart_owner=chart_owner,
        chart_roll=chart_roll,
        outcome=outcome,
        runs_scored=runs,
        rbi=rbi,
        is_hit=outcome in _HIT_OUTCOMES,
        stolen_base_attempt=sb_attempt,
        stolen_base_success=sb_success,
    ), new_runners
