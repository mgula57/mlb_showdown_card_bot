"""Capture card inputs for the snapshot cases in `cases.yaml` into `fixtures/<id>.json`.

Runs the real card pipeline (`generate_card`), so it needs the archive DB env vars and network access.
Only run when adding cases - formula changes never require re-capturing (that's what snapshots are for).

    python tests/card_snapshots/capture_fixtures.py             # capture every case
    python tests/card_snapshots/capture_fixtures.py --missing   # only cases without a fixture
    python tests/card_snapshots/capture_fixtures.py --only trout_2016
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(os.path.dirname(__file__)).parent.parent
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / 'tests'))

from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

from card_snapshots.card_snapshot import CardSnapshot, FIXTURES_DIR
from mlb_showdown_bot.core.card.card_generation import generate_card


class FixtureCapturer:
    """Builds each case through `generate_card` and stores its inputs as a fixture."""

    # SET IS IRRELEVANT TO THE INPUTS - TESTS REBUILD EVERY FIXTURE IN EVERY SET
    CAPTURE_KWARGS = {'set': '2000', 'disable_realtime': True, 'store_in_logs': False}

    def __init__(self, only: list[str] | None = None, missing_only: bool = False):
        self.only = only
        self.missing_only = missing_only

    def run(self) -> None:
        failures: dict[str, str] = {}
        for case in self.selected_cases():
            card_data, error = self.capture(case)
            if error:
                failures[case['id']] = error
                print(f"FAILED {case['id']}: {error}")
                continue
            CardSnapshot.save_fixture(case['id'], CardSnapshot.fixture_from_card_data(card_data))
            print(f"CAPTURED {case['id']}: {card_data.get('name')} {card_data.get('year')}")

        if failures:
            print(f"\n{len(failures)} case(s) failed: {', '.join(failures)}")
            sys.exit(1)

    def selected_cases(self) -> list[dict]:
        cases = CardSnapshot.load_cases()
        if self.only:
            cases = [c for c in cases if c['id'] in self.only]
        if self.missing_only:
            cases = [c for c in cases if not (FIXTURES_DIR / f"{c['id']}.json").exists()]
        return cases

    def capture(self, case: dict) -> tuple[dict | None, str | None]:
        payload = generate_card(**(case['kwargs'] | self.CAPTURE_KWARGS))
        if payload.get('error') or not payload.get('card'):
            return None, payload.get('error_for_user') or payload.get('error') or 'No card generated'
        return payload['card'], None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Capture card snapshot fixtures from the real card pipeline.')
    parser.add_argument('--only', nargs='+', help='Case ids to capture')
    parser.add_argument('--missing', action='store_true', help='Only capture cases without a fixture')
    args = parser.parse_args()
    FixtureCapturer(only=args.only, missing_only=args.missing).run()
