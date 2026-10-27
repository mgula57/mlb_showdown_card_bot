import json
import re
from collections import defaultdict
from pathlib import Path

from flask.json.provider import DefaultJSONProvider

from ..database.postgres_db import PostgresDB


class ReleaseImporter:
    """Loads a locally built set export (`set build --export_data` JSON) into the Release Builder:
    one release, one edition per image edition (base cards + each expansion), with card snapshots
    pulled from card_bot so they match cards added through the Edition Builder UI."""

    BASE_EDITION_CODE = 'NONE'

    def __init__(self, json_path: str, release_name: str, user_id: str, db: PostgresDB, base_edition_name: str = 'Base Set', publish: bool = False) -> None:
        self.release_name = release_name
        self.user_id = user_id
        self.db = db
        self.base_edition_name = base_edition_name
        self.publish = publish
        with open(Path(json_path)) as f:
            self.cards: list[dict] = list(json.load(f).values())

    # ---------------------------------------------------------------------
    # MARK: - GROUPING
    # ---------------------------------------------------------------------

    @property
    def showdown_set(self) -> str:
        sets = {c['set'] for c in self.cards}
        if len(sets) != 1:
            raise ValueError(f"Expected a single showdown set in the export, found {sorted(sets)}")
        return sets.pop()

    def cards_by_edition(self) -> dict[str, list[dict]]:
        """Export cards grouped by image edition code (NONE for base cards), sorted by set number."""
        groups: dict[str, list[dict]] = defaultdict(list)
        for card in self.cards:
            groups[card['image'].get('edition') or self.BASE_EDITION_CODE].append(card)
        for cards in groups.values():
            cards.sort(key=self._card_number)
        # BASE EDITION FIRST, EXPANSIONS ALPHABETICAL
        return dict(sorted(groups.items(), key=lambda kv: (kv[0] != self.BASE_EDITION_CODE, kv[0])))

    def edition_name(self, edition_code: str) -> str:
        return self.base_edition_name if edition_code == self.BASE_EDITION_CODE else edition_code

    def edition_attributes(self, edition_code: str) -> dict:
        """Manual numbering that reproduces the export's set numbers (e.g. 001, CC01)."""
        prefix = '' if edition_code == self.BASE_EDITION_CODE else edition_code
        return {'numbering': {'mode': 'manual', 'zeroPad': True, 'prefix': prefix}}

    @staticmethod
    def _card_number(card: dict) -> int | None:
        digits = re.sub(r'\D', '', str(card['image'].get('set_number') or ''))
        return int(digits) if digits else None

    # ---------------------------------------------------------------------
    # MARK: - SNAPSHOTS
    # ---------------------------------------------------------------------

    @staticmethod
    def _card_key(year, bref_id: str, is_pitcher: bool) -> tuple[int, str, bool]:
        return (int(year), bref_id, bool(is_pitcher))

    def fetch_snapshots(self) -> dict[tuple[int, str, bool], dict]:
        """card_bot records for every export card, keyed by (year, bref_id, is_pitcher).
        Serialized the same way the /cards/search response is, since that's what the UI stores."""
        records = self.db.fetch_card_list(filters={
            'source': 'BOT',
            'showdown_set': [self.showdown_set],
            'year': sorted({str(c['year']) for c in self.cards}),
            'bref_id': sorted({c['bref_id'] for c in self.cards}),
            'limit': 5000,
        })
        snapshots: dict[tuple[int, str, bool], dict] = {}
        for record in records:
            key = self._card_key(record['year'], record['bref_id'], record['is_pitcher'])
            if key in snapshots:
                raise ValueError(f"Multiple card_bot rows for {key} - expected one per card")
            snapshots[key] = json.loads(json.dumps(record, default=DefaultJSONProvider.default))
        return snapshots

    def build_edition_cards(self, cards: list[dict], snapshots: dict[tuple[int, str, bool], dict]) -> list[dict]:
        edition_cards = []
        for card in cards:
            key = self._card_key(card['year'], card['bref_id'], card['player_type'] == 'Pitcher')
            snapshot = snapshots.get(key)
            if snapshot is None:
                raise ValueError(f"No card_bot row for {card['name']} {key}")
            edition_cards.append({
                'card_number': self._card_number(card),
                'source_card_id': snapshot['id'],
                'source_card_type': snapshot['source'],
                'card_snapshot': snapshot,
                'tags': card.get('tags') or [],
            })
        return edition_cards

    # ---------------------------------------------------------------------
    # MARK: - IMPORT
    # ---------------------------------------------------------------------

    def _find_or_create_release(self) -> dict:
        existing = next((r for r in self.db.get_releases(self.user_id) if r['name'] == self.release_name), None)
        if existing:
            print(f"Updating existing release '{self.release_name}' ({existing['id']})")
            return existing
        release_id = self.db.create_release(self.user_id, {'name': self.release_name, 'default_showdown_set': self.showdown_set})
        print(f"Created release '{self.release_name}' ({release_id})")
        return self.db.get_release(release_id, self.user_id)

    def run(self) -> str:
        """Create or update the release and each edition's card list. Returns the release id."""
        editions = self.cards_by_edition()
        snapshots = self.fetch_snapshots()
        # VALIDATE EVERY EDITION BEFORE WRITING ANYTHING
        edition_cards = {code: self.build_edition_cards(cards, snapshots) for code, cards in editions.items()}

        release = self._find_or_create_release()
        existing_editions = {e['name']: e for e in release.get('editions', [])}
        for code, cards in edition_cards.items():
            name = self.edition_name(code)
            payload = {'name': name, 'attributes': self.edition_attributes(code), 'cards': cards}
            if name in existing_editions:
                self.db.update_edition(existing_editions[name]['id'], self.user_id, payload)
                action = 'Updated'
            else:
                self.db.create_edition(release['id'], self.user_id, payload)
                action = 'Created'
            print(f"  {action} edition '{name}': {len(cards)} cards")
        self.db.set_release_published(release['id'], self.user_id, self.publish)
        return release['id']
