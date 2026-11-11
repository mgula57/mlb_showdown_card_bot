import json
import traceback
from dataclasses import dataclass, field
from flask.json.provider import DefaultJSONProvider
from typing import Optional
from ..card.sets import Set
from ..card.stats.stats_period import SeasonHalf
from ..database.postgres_db import PostgresDB
from .release_card_period import ReleaseCardPeriod, ReleaseCardPeriodError


class ReleaseEditionDuplicateError(ValueError):
    """The edition can't be duplicated into the requested set."""


@dataclass
class DuplicatedEdition:
    """The new edition's create payload, plus the source cards that had no card in the target set."""
    payload: dict
    skipped: list[str] = field(default_factory=list)


class ReleaseEditionDuplicator:
    """Copies an edition's player list into another Showdown set as a new edition's create payload.

    Each Showdown Bot card is swapped for the same player-season's archived (V1) card in the target
    set; `card_bot.id` is the player-season, shared by its card in every set. A card built for half
    of its season is rebuilt for the same half in the target set (`ReleaseCardPeriod`). Other
    card-level edits (chart versions, variable speed, tags, cover picks, style overrides) are dropped.
    Card numbers carry over so the checklist keeps its order. The edition's card style and style
    rules carry over, and its scope keeps its stats period but points at the target set. Nothing is rendered.
    """

    # Edition settings copied as-is. Mirrors `attributes.style` / `attributes.style_rules` in
    # `frontend/src/components/releases/editionStyle.ts` and `attributes.numbering` in `EditionBuilder.tsx`
    COPIED_ATTRIBUTES = ('style', 'style_rules', 'numbering')
    # Mirrors `SCOPE_KEYS` in `frontend/src/components/releases/editionScope.ts`. Editions saved
    # before `attributes.scope` existed keep these in `attributes.algorithm`
    SCOPE_KEYS = ('set_size', 'years', 'showdown_sets', 'pitcher_showdown_sets', 'variable_speed', 'season_half', 'teams', 'other_editions_rule')
    BOT_SOURCE = 'BOT'

    def __init__(self, db: PostgresDB) -> None:
        self.db = db

    def duplicate(self, edition: dict, showdown_set: str, name: str) -> DuplicatedEdition:
        try:
            target_set = Set(showdown_set).value
        except ValueError:
            raise ReleaseEditionDuplicateError(f"Unknown showdown set '{showdown_set}'")
        cards, skipped = self._cards_in_set(edition.get('cards') or [], target_set)
        return DuplicatedEdition(
            payload={'name': name, 'attributes': self._attributes(edition.get('attributes') or {}, target_set), 'cards': cards},
            skipped=skipped,
        )

    def _attributes(self, source: dict, showdown_set: str) -> dict:
        attributes = {key: source[key] for key in self.COPIED_ATTRIBUTES if key in source}
        algorithm = source.get('algorithm') if isinstance(source.get('algorithm'), dict) else {}
        saved_scope = source.get('scope') if isinstance(source.get('scope'), dict) else {}
        scope = {key: value for key, value in {**algorithm, **saved_scope}.items() if key in self.SCOPE_KEYS}
        # The cards are V1s from the one target set, in the source's stats period
        attributes['scope'] = {**scope, 'showdown_sets': [showdown_set], 'pitcher_showdown_sets': None, 'variable_speed': False}
        return attributes

    def _cards_in_set(self, source_cards: list[dict], showdown_set: str) -> tuple[list[dict], list[str]]:
        """The target set's card for each source Bot card, in the source's order, and the names of
        the cards left out (non-Bot sources, no card for that season in the target set, or a half
        season that couldn't be rebuilt)."""
        season_ids = [self._season_id(card) for card in source_cards]
        wanted = list(dict.fromkeys(season_id for season_id in season_ids if season_id))
        rows = self.db.fetch_card_list({'id': wanted, 'showdown_set': [showdown_set], 'limit': max(len(wanted), 1)}) if wanted else []
        rows_by_id: dict[str, dict] = {}
        for row in rows or []:
            rows_by_id.setdefault(str(row.get('id')), row)
        halves = {season_id: self._season_half(card) for card, season_id in zip(source_cards, season_ids) if season_id}
        archived_cards = self.db.fetch_cards_for_roster_slots([
            {'card_id': row['card_id'], 'card_source': self.BOT_SOURCE}
            for season_id, row in rows_by_id.items() if halves.get(season_id) and row.get('card_id')
        ]) if any(halves.values()) else {}
        period = ReleaseCardPeriod(self.db)

        cards, skipped = [], []
        for card, season_id in zip(source_cards, season_ids):
            snapshot = card.get('card_snapshot') or {}
            label = f"{snapshot.get('name') or 'Unknown'} ({snapshot.get('year') or '?'})"
            row = rows_by_id.get(season_id) if season_id else None
            if row is None:
                skipped.append(label)
                continue
            if (half := halves.get(season_id)):
                archived_card = archived_cards.get(str(row.get('card_id')))
                try:
                    if archived_card is None:
                        raise ReleaseCardPeriodError('Card not found in the archive.')
                    # Embeds the half-season card (`card_data`) in the row
                    period.apply_to_row(row, archived_card, half)
                except ReleaseCardPeriodError as exc:
                    skipped.append(f"{label}: {exc}")
                    continue
                except Exception:
                    # One card that fails to rebuild shouldn't sink the whole duplicate
                    traceback.print_exc()
                    skipped.append(label)
                    continue
            # Serialized the way the /cards/search response is, since that's what the UI stores
            row = json.loads(json.dumps(row, default=DefaultJSONProvider.default))
            cards.append({
                'source_card_id': row['id'],
                'source_card_type': row.get('source') or self.BOT_SOURCE,
                'card_snapshot': row,
                'card_number': card.get('card_number'),
            })
        return cards, skipped

    @staticmethod
    def _season_half(card: dict) -> Optional[SeasonHalf]:
        """The half of the season the card was built for, if any."""
        half = (((card.get('card_snapshot') or {}).get('card_data') or {}).get('stats_period') or {}).get('season_half')
        try:
            return SeasonHalf(half) if half else None
        except ValueError:
            return None

    def _season_id(self, card: dict) -> str | None:
        """The card's player-season id, or None for a card with no Bot equivalent (WOTC, custom...)."""
        if str(card.get('source_card_type') or '').upper() != self.BOT_SOURCE:
            return None
        season_id = (card.get('card_snapshot') or {}).get('id') or card.get('source_card_id')
        return str(season_id) if season_id else None
