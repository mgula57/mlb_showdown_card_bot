"""Golden snapshot checks for `ShowdownPlayerCard` formula outputs.

No database, no network: every fixture in `card_snapshots/fixtures/` (real players captured once from the
archive) is rebuilt in every Set and compared exactly against `card_snapshots/snapshots/`.

    pytest tests/test_card_snapshots.py                      # check
    pytest tests/test_card_snapshots.py --update-snapshots   # accept intentional formula changes
    python tests/test_card_snapshots.py                      # check + summary of changed fields

When a formula change is intentional, update the snapshots and commit their diff alongside the change.
"""

import os
import sys
from collections import Counter
from pathlib import Path

TESTS_DIR = Path(os.path.dirname(__file__))
sys.path.append(str(TESTS_DIR.parent))
sys.path.append(str(TESTS_DIR))

import pytest

from card_snapshots.card_snapshot import CardSnapshot
from mlb_showdown_bot.core.card.sets import Set


def build_snapshots(case_id: str) -> dict[str, dict]:
    fixture = CardSnapshot.load_fixture(case_id)
    return {s.value: CardSnapshot.from_card(CardSnapshot.build_card(fixture, s)) for s in Set}


def snapshot_diffs(case_id: str, actual: dict[str, dict]) -> list[str] | None:
    """Diff lines prefixed with the set, or None when the case has no stored snapshot yet."""
    expected = CardSnapshot.load_snapshots(case_id)
    if expected is None:
        return None
    return [f'[{set_value}] {line}' for set_value, snapshot in actual.items() for line in CardSnapshot.diff(expected.get(set_value), snapshot)]


@pytest.mark.parametrize('case_id', CardSnapshot.fixture_ids())
def test_card_snapshot(case_id: str, request: pytest.FixtureRequest):
    actual = build_snapshots(case_id)
    if request.config.getoption('--update-snapshots'):
        CardSnapshot.save_snapshots(case_id, actual)
        return

    diffs = snapshot_diffs(case_id, actual)
    assert diffs is not None, f'No snapshot for {case_id}. Run with --update-snapshots to create it.'
    assert not diffs, f'{case_id} card outputs changed ({len(diffs)}):\n' + '\n'.join(diffs)


def test_every_case_has_fixture():
    case_ids = {case['id'] for case in CardSnapshot.load_cases()}
    missing = sorted(case_ids - set(CardSnapshot.fixture_ids()))
    assert not missing, f'Cases without fixtures (run capture_fixtures.py --missing): {missing}'


if __name__ == '__main__':
    changed_fields: Counter[str] = Counter()
    changed_cases = 0
    for case_id in CardSnapshot.fixture_ids():
        diffs = snapshot_diffs(case_id, build_snapshots(case_id))
        if diffs is None:
            print(f'{case_id}: NO SNAPSHOT')
            continue
        if diffs:
            changed_cases += 1
            print(f'\n{case_id} ({len(diffs)} changes)\n  ' + '\n  '.join(diffs))
            # GROUP BY FIELD, IGNORING THE SET PREFIX AND CHART CATEGORY LEAVES (EX: chart.ranges)
            changed_fields.update('.'.join(line.split('] ', 1)[1].split(':')[0].split('.')[:2]) for line in diffs)

    print(f'\n{changed_cases} case(s) changed')
    for field, count in changed_fields.most_common():
        print(f'  {field}: {count}')
    sys.exit(1 if changed_cases else 0)
