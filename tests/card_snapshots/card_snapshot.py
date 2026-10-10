"""Golden snapshots of card formula outputs, used by `tests/test_card_snapshots.py`.

A FIXTURE is the inputs of a real card (stats, stats period, overrides), captured once from the
archive by `capture_fixtures.py`. A SNAPSHOT is the formula outputs (chart, points, speed, defense...)
of that fixture rebuilt in every Set by the current code. Any difference between the two is a
formula change - either a regression, or an intentional change accepted via `--update-snapshots`.
"""

import json
from pathlib import Path
from typing import Any

import yaml

from mlb_showdown_bot.core.card.sets import Set
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard

ROOT = Path(__file__).parent
CASES_PATH = ROOT / 'cases.yaml'
FIXTURES_DIR = ROOT / 'fixtures'
SNAPSHOTS_DIR = ROOT / 'snapshots'

# IMAGE FIELDS THAT CAN AFFECT CARD OUTPUT (EX: CURATED COMMAND/OUT SELECTIONS ARE KEYED BY EXPANSION)
FIXTURE_IMAGE_FIELDS = ('edition', 'expansion', 'parallel', 'special_edition')

# INPUTS THAT ONLY CONTROL PRESENTATION OR SIDE EFFECTS (IMAGES, UPLOADS, LOGGING, REALTIME DATA)
FIXTURE_EXCLUDED_FIELDS = frozenset([
    'set', 'image', 'realtime_game_logs', 'is_running_on_website', 'show_image', 'print_to_cli',
    'user_id', 'rank', 'pct_rank', 'points_change', 'notes', 'nicknames',
])

FLOAT_DECIMALS = 4


class CardSnapshot:
    """Extracts, stores and compares the formula outputs of a card."""

    # ------------------------------------------------------------------------
    # FIXTURES
    # ------------------------------------------------------------------------

    @staticmethod
    def fixture_from_card_data(card_data: dict) -> dict:
        """Reduce a card payload (`ShowdownPlayerCard.as_json()`) to the inputs needed to rebuild it."""
        excluded = ShowdownPlayerCard.REBUILT_FIELDS | FIXTURE_EXCLUDED_FIELDS
        fixture = {k: v for k, v in card_data.items() if k not in excluded}
        image = card_data.get('image') or {}
        fixture['image'] = {k: image[k] for k in FIXTURE_IMAGE_FIELDS if k in image}
        return fixture

    @staticmethod
    def build_card(fixture: dict, set: Set) -> ShowdownPlayerCard:
        """Rebuild a fixture through the current card algorithm in the given set."""
        return ShowdownPlayerCard.rebuilt_from_card_data(fixture | {'set': set.value})

    @staticmethod
    def fixture_ids() -> list[str]:
        return sorted(path.stem for path in FIXTURES_DIR.glob('*.json'))

    @staticmethod
    def load_fixture(case_id: str) -> dict:
        return CardSnapshot._read_json(FIXTURES_DIR / f'{case_id}.json')

    @staticmethod
    def save_fixture(case_id: str, fixture: dict) -> None:
        CardSnapshot._write_json(FIXTURES_DIR / f'{case_id}.json', fixture)

    @staticmethod
    def load_cases() -> list[dict]:
        with open(CASES_PATH) as f:
            return yaml.safe_load(f)

    # ------------------------------------------------------------------------
    # SNAPSHOTS
    # ------------------------------------------------------------------------

    @staticmethod
    def from_card(card: ShowdownPlayerCard) -> dict:
        """Formula outputs worth guarding. Excludes version, warnings, images and accuracy internals."""
        data = card.as_json()
        chart = data.get('chart') or {}
        points_breakdown = data.get('points_breakdown') or {}
        snapshot = {
            'player_type': data.get('player_type'),
            'player_sub_type': data.get('player_sub_type'),
            'selected_command_outs': data.get('selected_command_outs'),
            'command_out_selection': (data.get('command_out_selection') or {}).get('key'),
            'chart': {
                'command': chart.get('command'),
                'outs': chart.get('outs'),
                'outs_full': chart.get('outs_full'),
                'sb': chart.get('sb'),
                'ranges': chart.get('ranges'),
                'values': chart.get('values'),
                'is_command_out_anomaly': chart.get('is_command_out_anomaly'),
            },
            'points': data.get('points'),
            'points_breakdown': {
                'breakdowns': {k: b.get('points') for k, b in (points_breakdown.get('breakdowns') or {}).items()},
                **{k: points_breakdown.get(k) for k in ('command_out_multiplier', 'decay_rate', 'decay_start', 'ip_multiplier')},
            },
            'speed': data.get('speed'),
            'positions_and_defense': data.get('positions_and_defense'),
            'ip': data.get('ip'),
            'hand': data.get('hand'),
            'icons': data.get('icons'),
            'projected': data.get('projected'),
        }
        return CardSnapshot._round_floats(snapshot)

    @staticmethod
    def load_snapshots(case_id: str) -> dict[str, dict] | None:
        path = SNAPSHOTS_DIR / f'{case_id}.json'
        return CardSnapshot._read_json(path) if path.exists() else None

    @staticmethod
    def save_snapshots(case_id: str, snapshots: dict[str, dict]) -> None:
        CardSnapshot._write_json(SNAPSHOTS_DIR / f'{case_id}.json', snapshots)

    @staticmethod
    def diff(expected: Any, actual: Any, path: str = '') -> list[str]:
        """Readable list of differences, one line per changed leaf (ex: `chart.ranges.HR: 18-20 -> 19-20`)."""
        if isinstance(expected, dict) and isinstance(actual, dict):
            lines = []
            for key in sorted(set(expected) | set(actual), key=str):
                child_path = f'{path}.{key}' if path else str(key)
                if key not in actual:
                    lines.append(f'{child_path}: {expected[key]!r} -> (missing)')
                elif key not in expected:
                    lines.append(f'{child_path}: (missing) -> {actual[key]!r}')
                else:
                    lines += CardSnapshot.diff(expected[key], actual[key], child_path)
            return lines
        return [] if expected == actual else [f'{path}: {expected!r} -> {actual!r}']

    # ------------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------------

    @staticmethod
    def _round_floats(value: Any) -> Any:
        """Round floats so float-repr noise across platforms doesn't register as a change."""
        if isinstance(value, float):
            return round(value, FLOAT_DECIMALS)
        if isinstance(value, dict):
            return {k: CardSnapshot._round_floats(v) for k, v in value.items()}
        if isinstance(value, list):
            return [CardSnapshot._round_floats(v) for v in value]
        return value

    @staticmethod
    def _read_json(path: Path) -> dict:
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True, default=str)
            f.write('\n')
