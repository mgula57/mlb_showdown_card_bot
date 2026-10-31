"""
Release Builder card patches: the small edits a set builder makes over and over (a card number, a
tag, a cover pick, a per-card style tweak) save as just those fields, instead of re-sending every
card snapshot in the edition. Anything that changes which cards are in the edition, or a card's
snapshot, still saves the full list (`PUT /editions/<id>`).
"""

from collections import Counter
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReleaseCardPatch(BaseModel):
    """One card's changed fields. Only the fields sent are applied (`changes`)."""

    model_config = ConfigDict(extra='forbid')

    source_card_id: str = Field(min_length=1)
    card_number: Optional[int] = None
    tags: Optional[list[str]] = None
    preview_rank: Optional[int] = Field(None, ge=1, le=3)
    card_overrides: Optional[dict] = None

    def changes(self) -> dict:
        """The fields this patch sets, by name (a field sent as null clears it)."""
        return {field: getattr(self, field) for field in self.model_fields_set if field != 'source_card_id'}


class ReleaseCardNumbers:
    """Card numbers are unique per edition (`unique_card_number`)."""

    @staticmethod
    def duplicate_error(cards) -> Optional[str]:
        """Why a card list can't be saved because two cards share a number, else None. Repeated
        source cards are skipped, as the full save's upsert keeps only the first."""
        if not isinstance(cards, list):
            return None
        seen_source_ids: set = set()
        counts: Counter = Counter()
        for card in cards:
            if not isinstance(card, dict):
                continue
            source_card_id = card.get('source_card_id')
            if source_card_id and source_card_id in seen_source_ids:
                continue
            seen_source_ids.add(source_card_id)
            if card.get('card_number') is not None:
                counts[card['card_number']] += 1
        duplicates = sorted(number for number, count in counts.items() if count > 1)
        if not duplicates:
            return None
        listed = ', '.join(f"#{number}" for number in duplicates[:5]) + (f" and {len(duplicates) - 5} more" if len(duplicates) > 5 else '')
        return f"Two cards can't share a number: {listed} {'is' if len(duplicates) == 1 else 'are'} used more than once."

    @classmethod
    def patched_duplicate_error(cls, current: dict[str, Optional[int]], patches: list[ReleaseCardPatch]) -> Optional[str]:
        """`duplicate_error` for the edition's numbers (`current`, by source card id) after `patches`."""
        numbers = dict(current)
        for patch in patches:
            if 'card_number' in patch.model_fields_set and patch.source_card_id in numbers:
                numbers[patch.source_card_id] = patch.card_number
        return cls.duplicate_error([{'source_card_id': source_id, 'card_number': number} for source_id, number in numbers.items()])
