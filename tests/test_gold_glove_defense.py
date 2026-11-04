"""Offline checks for Gold Glove defense: 2026+ winners use the higher of OAA and DRS at their winning position.

No database, no network: cards are built from replacement-level stats with fielding numbers layered on top,
so this runs as `python tests/test_gold_glove_defense.py` anywhere.
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from mlb_showdown_bot.core.card.sets import Position as CardPosition, Set
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.core.card.stats.metrics import DefenseMetric
from mlb_showdown_bot.core.card.stats.normalized_player_stats import NormalizedPlayerStats, PlayerStatsNormalizer, PositionStats
from mlb_showdown_bot.core.card.stats.stats_period import StatsPeriod, StatsPeriodType
from mlb_showdown_bot.core.data.replacement_season_averages import build_replacement_level_stats_for_card
from mlb_showdown_bot.core.mlb_stats_api.models.stats.awards import Award
from mlb_showdown_bot.core.shared.player_position import Position
from types import SimpleNamespace

WALLS_SS = {'SS': {'g': 123, 'oaa': -3.0, 'drs': 21.0}}


def build_card(positions: dict, gold_glove_position: str | None, year: int = 2026, showdown_set: Set = Set._2001) -> ShowdownPlayerCard:
    stats = build_replacement_level_stats_for_card(year=2023, player_type='HITTER', positions=[Position('SS')])
    stats |= {'name': 'Test Player', 'bref_id': 'testpl01', 'positions': positions, 'G': 150, 'gold_glove_position': gold_glove_position}
    return ShowdownPlayerCard(
        name='Test Player', year=str(year), set=showdown_set, stats=stats,
        stats_period=StatsPeriod(year=str(year), type=StatsPeriodType.REGULAR_SEASON),
    )


def test_winner_uses_drs_when_it_rates_higher():
    baseline = build_card(WALLS_SS, gold_glove_position=None)
    winner = build_card(WALLS_SS, gold_glove_position='SS')

    assert winner.positions_and_defense[CardPosition.SS] > baseline.positions_and_defense[CardPosition.SS]
    assert DefenseMetric.DRS in winner.positions_and_real_life_ratings[CardPosition.SS]
    assert winner.notes == (
        'Gold Glove: SS defense is based on +21 DRS instead of -3 OAA. '
        'Winners use whichever rates higher at their winning position.'
    )
    assert baseline.notes is None


def test_winner_keeps_oaa_when_it_rates_higher():
    positions = {'SS': {'g': 157, 'oaa': 16.0, 'drs': -4.0}}
    baseline = build_card(positions, gold_glove_position=None)
    winner = build_card(positions, gold_glove_position='SS')

    assert winner.positions_and_defense == baseline.positions_and_defense
    assert DefenseMetric.OAA in winner.positions_and_real_life_ratings[CardPosition.SS]
    assert winner.notes is None


def test_only_the_winning_position_changes():
    positions = {'2B': {'g': 157, 'oaa': -5.0, 'drs': 16.0}, 'SS': {'g': 60, 'oaa': -5.0, 'drs': 16.0}}
    baseline = build_card(positions, gold_glove_position=None)
    winner = build_card(positions, gold_glove_position='2B')

    assert winner.positions_and_defense[CardPosition._2B] > baseline.positions_and_defense[CardPosition._2B]
    assert winner.positions_and_defense[CardPosition.SS] == baseline.positions_and_defense[CardPosition.SS]


def test_utility_winners_use_the_higher_metric_at_every_position():
    positions = {'2B': {'g': 100, 'oaa': -5.0, 'drs': 16.0}, 'SS': {'g': 60, 'oaa': -5.0, 'drs': 16.0}}
    baseline = build_card(positions, gold_glove_position=None)
    winner = build_card(positions, gold_glove_position='UT')

    assert winner.positions_and_defense[CardPosition._2B] > baseline.positions_and_defense[CardPosition._2B]
    assert winner.positions_and_defense[CardPosition.SS] > baseline.positions_and_defense[CardPosition.SS]
    assert winner.notes == (
        'Gold Glove: 2B defense is based on +16 DRS instead of -5 OAA, SS defense is based on +16 DRS instead of -5 OAA. '
        'Utility winners use whichever rates higher at each position.'
    )


def test_catchers_without_oaa_have_no_note():
    card = build_card({'C': {'g': 116, 'drs': 15.0}}, gold_glove_position='C')
    assert card.notes is None


def test_outfield_winner_covers_combined_of_position():
    positions = {
        'LF': {'g': 123, 'oaa': 6.0, 'drs': 21.0},
        'CF': {'g': 17, 'oaa': 0.0, 'drs': -1.0},
        'OF': {'g': 132, 'oaa': 6.0, 'drs': 20.0},
    }
    card = build_card(positions, gold_glove_position='LF', showdown_set=Set._2002)
    assert DefenseMetric.DRS in card.positions_and_real_life_ratings.get(CardPosition.OF, {})


def test_pre_2026_and_partial_seasons_are_unchanged():
    older = build_card(WALLS_SS, gold_glove_position='SS', year=2025)
    assert DefenseMetric.OAA in older.positions_and_real_life_ratings[CardPosition.SS]
    assert older.notes is None

    # SET DIRECTLY: A DATE RANGE WITHOUT GAME LOGS FALLS BACK TO THE REGULAR SEASON DURING CARD BUILD
    partial = build_card(WALLS_SS, gold_glove_position='SS')
    assert partial.gold_glove_position == 'SS'
    partial.stats_period = StatsPeriod(year='2026', type=StatsPeriodType.DATE_RANGE, start_date='2026-04-01', end_date='2026-05-31')
    assert partial.gold_glove_position is None


def test_note_is_not_duplicated_when_a_stored_card_is_rebuilt():
    winner = build_card(WALLS_SS, gold_glove_position='SS')
    original_note = winner.notes
    winner._add_gold_glove_defense_note()
    assert winner.notes == original_note


def test_award_position_is_extracted_for_single_seasons_only():
    award = Award(id='ALGG', name='Rawlings AL Gold Glove', season='2026', player={'id': 1, 'primaryPosition': {'abbreviation': 'SS'}})
    other_year = Award(id='ALGG', name='Rawlings AL Gold Glove', season='2025', player={'id': 1, 'primaryPosition': {'abbreviation': '3B'}})
    player = SimpleNamespace(awards=[other_year, award])

    single_season = StatsPeriod(year='2026', type=StatsPeriodType.REGULAR_SEASON)
    multi_year = StatsPeriod(year='2025-2026', type=StatsPeriodType.REGULAR_SEASON)
    assert PlayerStatsNormalizer._extract_gold_glove_position(player, single_season) == 'SS'
    assert PlayerStatsNormalizer._extract_gold_glove_position(player, multi_year) is None


def test_of_rollup_sums_drs():
    stats = NormalizedPlayerStats.model_construct(G=150, positions={})
    stats.inject_defensive_stats_list(
        position_stats_list=[
            PositionStats(position='LF', g=100, oaa=4.0, drs=9.0),
            PositionStats(position='RF', g=50, oaa=1.0, drs=None),
        ],
        source=None,
    )
    assert stats.positions['OF'].oaa == 5.0
    assert stats.positions['OF'].drs == 9.0


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for test in tests:
        test()
        print(f'PASS {test.__name__}')
