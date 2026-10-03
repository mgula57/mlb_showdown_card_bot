"""Offline checks for curated command/out selections (`core/card/data/command_out_selections.yaml`).

No database, no network. Run as `python tests/test_command_out_selections.py`.

Four things are under test:
  1. FILE - the YAML loads and every entry passes validation (types, valid commands, unique keys, no conflicts).
  2. GATE - selections only apply to stats periods covering the player's full season.
  3. CARD - a matching card promotes the selected combo to version 1 with its true accuracy; version 2 is the
     most accurate chart, and other sets and manual overrides are unaffected.
  4. AUDIT - stored cards are classified OK / STALE / ORPHANED / MISSING against the current selections.
"""

import os
import sys
from datetime import date
from pathlib import Path

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from mlb_showdown_bot.core.card.command_out_selections import CommandOutSelections, SelectionAuditStatus, StoredCardSelectionRecord
from mlb_showdown_bot.core.card.sets import Set
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.core.card.stats.stats_period import StatsPeriod, StatsPeriodType

SAMPLE_HITTER_STATS = {
    'type': 'Hitter', 'team_ID': 'CHC', 'bref_id': 'crowape01', 'hand': 'Left',
    'G': 155, 'GS': 150, 'PA': 640, 'AB': 590, 'H': 150, '2B': 33, '3B': 5, 'HR': 30, 'BB': 35, 'SO': 140, 'SB': 35, 'CS': 6,
    'HBP': 8, 'SF': 5, 'batting_avg': .254, 'onbase_perc': .300, 'slugging_perc': .480, 'onbase_plus_slugging': .780,
    'positions': {'CF': {'g': 150}}, 'years_played': ['2026'],
}


def test_file_loads():
    selections = CommandOutSelections.load()
    assert len(selections.entries) > 0
    for entry in selections.entries:
        assert len(entry.fingerprint) == 10
    print(f"FILE: {len(selections.entries)} selection(s) valid")


def test_full_season_gate():
    full_season_stats = {'PA': 640, 'G': 155}

    def date_range(pa: int) -> StatsPeriod:
        period = StatsPeriod(type=StatsPeriodType.DATE_RANGE, year='2026', start_date=date(2026, 3, 1), end_date=date(2026, 10, 1))
        period.stats = {'PA': pa}
        return period

    assert StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year='2026').covers_full_season(full_season_stats)
    assert date_range(pa=640).covers_full_season(full_season_stats)
    assert not date_range(pa=300).covers_full_season(full_season_stats)
    assert not StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year='2025-2026').covers_full_season(full_season_stats)
    assert not StatsPeriod(type=StatsPeriodType.POSTSEASON, year='2026').covers_full_season(full_season_stats)
    assert not StatsPeriod(type=StatsPeriodType.SPLIT, year='2026', split='vs LHP').covers_full_season(full_season_stats)
    print("GATE: full season periods only")


def test_card_applies_selection():
    selection = CommandOutSelections.load().lookup(player_ids=['crowape01'], year='2026', set=Set._2004, player_type=None)
    assert selection is not None

    def build(set: Set, **kwargs) -> ShowdownPlayerCard:
        return ShowdownPlayerCard(
            name='Pete Crow-Armstrong', year='2026', set=set, stats=dict(SAMPLE_HITTER_STATS),
            stats_period=StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year='2026'), **kwargs
        )

    card = build(Set._2004)
    assert card.selected_command_outs == selection.command_outs_concat
    assert card.command_out_selection == selection
    assert card.command_out_selection_fingerprint == selection.fingerprint
    assert card.chart.accuracy < 1.0, "Selected chart should keep its true accuracy"

    # STORED JSON ROUND TRIP
    assert ShowdownPlayerCard(**card.as_json()).command_out_selection == selection

    # NOT IN SELECTION'S SETS
    assert build(Set._2003).command_out_selection is None

    # SELECTION IS PROMOTED TO VERSION 1, SO VERSION 2 IS THE MOST ACCURATE CHART
    v2 = build(Set._2004, chart_version=2)
    most_accurate = max(card.command_out_accuracies.items(), key=lambda item: item[1])[0]
    assert v2.selected_command_outs == most_accurate and v2.command_out_selection == selection

    # MANUAL OVERRIDE TAKES PRIORITY
    manual = build(Set._2004, command_out_override=(12, 6))
    assert manual.selected_command_outs == '12-6' and manual.command_out_selection is None
    print("CARD: selection promoted to version 1; version 2 / manual override / other sets behave")


def test_audit_status():
    selections = CommandOutSelections.load()
    selection = selections.entries[0]
    card_set = selection.sets[0]

    def record(**kwargs) -> StoredCardSelectionRecord:
        fields = dict(card_id='test', bref_id=selection.player_id, year=selection.year, showdown_set=card_set, player_type='HITTER')
        return StoredCardSelectionRecord(**(fields | kwargs))

    assert selections.audit_status(record(selection_key=selection.key, selection_fingerprint=selection.fingerprint)) == SelectionAuditStatus.OK
    assert selections.audit_status(record(selection_key=selection.key, selection_fingerprint='old')) == SelectionAuditStatus.STALE
    assert selections.audit_status(record(selection_key='removed-key', selection_fingerprint='old')) == SelectionAuditStatus.ORPHANED
    assert selections.audit_status(record()) == SelectionAuditStatus.MISSING
    assert selections.audit_status(record(bref_id='someoneelse01')) is None
    print("AUDIT: OK / STALE / ORPHANED / MISSING classified")


if __name__ == '__main__':
    test_file_loads()
    test_full_season_gate()
    test_card_applies_selection()
    test_audit_status()
    print("ALL PASSED")
