import hashlib
import yaml
from enum import Enum
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator
from typing import Optional

# INTERNAL
from .sets import Set, PlayerType

SELECTIONS_FILE_PATH = Path(__file__).parent / 'data' / 'command_out_selections.yaml'


class CommandOutSelection(BaseModel):
    """A curated OnBase/Control + Outs combination for a player's card in specific sets."""

    model_config = ConfigDict(frozen=True)

    key: str
    player_id: str
    year: str
    sets: list[Set]
    command: int
    outs: int = Field(ge=0, le=20)
    player_type: Optional[PlayerType] = None
    added_in: str
    note: Optional[str] = None

    @field_validator('year', mode='before')
    def clean_year(cls, year: str | int) -> str:
        return str(year).upper()

    @model_validator(mode='after')
    def validate_command_for_sets(self) -> 'CommandOutSelection':
        player_types = [self.player_type] if self.player_type else [PlayerType.HITTER, PlayerType.PITCHER]
        for card_set in self.sets:
            if not any(self.command in card_set.command_options(player_type=pt) for pt in player_types):
                raise ValueError(f"Selection '{self.key}': command {self.command} is not a valid option for set {card_set.value}")
        return self

    @property
    def command_outs_concat(self) -> str:
        """Matches `Chart.command_outs_concat` (ex: '13-8')"""
        return f'{self.command}-{self.outs}'

    @property
    def fingerprint(self) -> str:
        """Short hash of the values that drive the chart. Stamped on cards to detect stale stored cards."""
        payload = self.model_dump_json(exclude={'note', 'added_in'})
        return hashlib.sha1(payload.encode()).hexdigest()[:10]


class SelectionAuditStatus(str, Enum):
    """How a stored card compares against the current curated selections."""

    OK = "OK"               # CARD WAS BUILT WITH THE CURRENT SELECTION
    STALE = "STALE"         # SELECTION WAS EDITED AFTER THE CARD WAS BUILT
    ORPHANED = "ORPHANED"   # CARD HAS A SELECTION THAT NO LONGER EXISTS OR NO LONGER MATCHES IT
    MISSING = "MISSING"     # A SELECTION MATCHES THE CARD, BUT THE CARD WAS BUILT WITHOUT IT

    @property
    def needs_rebuild(self) -> bool:
        return self != SelectionAuditStatus.OK


class StoredCardSelectionRecord(BaseModel):
    """Selection-related fields of a stored card, used to detect cards that need rebuilding."""

    card_id: str
    bref_id: Optional[str] = None
    mlb_id: Optional[int] = None
    year: str
    showdown_set: Set
    player_type: PlayerType
    selection_key: Optional[str] = None
    selection_fingerprint: Optional[str] = None
    selected_command_outs: Optional[str] = None

    @field_validator('year', mode='before')
    def clean_year(cls, year: str | int) -> str:
        return str(year).upper()

    @property
    def player_ids(self) -> list[str]:
        return [self.bref_id, f"mlb{self.mlb_id}" if self.mlb_id else None]


class CommandOutSelections(BaseModel):
    """Collection of curated command/out selections, loaded from `data/command_out_selections.yaml`."""

    entries: list[CommandOutSelection] = []
    _index: dict[tuple[str, str, Set], list[CommandOutSelection]] = PrivateAttr(default_factory=dict)

    @model_validator(mode='after')
    def validate_and_index(self) -> 'CommandOutSelections':
        keys = [entry.key for entry in self.entries]
        duplicate_keys = sorted(set(k for k in keys if keys.count(k) > 1))
        if duplicate_keys:
            raise ValueError(f"Duplicate command/out selection keys: {duplicate_keys}")

        for entry in self.entries:
            for card_set in entry.sets:
                index_key = (entry.player_id, entry.year, card_set)
                existing = self._index.setdefault(index_key, [])
                # ONLY ONE ENTRY PER PLAYER/YEAR/SET/TYPE. AN UNTYPED ENTRY CONFLICTS WITH EVERYTHING
                conflicts = [e for e in existing if e.player_type is None or entry.player_type is None or e.player_type == entry.player_type]
                if conflicts:
                    raise ValueError(f"Selections '{conflicts[0].key}' and '{entry.key}' both claim {entry.player_id} {entry.year} {card_set.value}")
                existing.append(entry)
        return self

    @classmethod
    @lru_cache(maxsize=1)
    def load(cls) -> 'CommandOutSelections':
        raw = yaml.safe_load(SELECTIONS_FILE_PATH.read_text()) or []
        return cls(entries=raw)

    def lookup(self, player_ids: list[str], year: str, set: Set, player_type: PlayerType) -> Optional[CommandOutSelection]:
        """Find the selection for a player's card, if one exists.

        Args:
          player_ids: Ids the player can be referenced by (bref id and/or "mlb{mlb_id}").
          year: Year string of the card.
          set: Card set.
          player_type: Player type of the card (HITTER, PITCHER).

        Returns:
          The matching selection, or None.
        """
        for player_id in [pid for pid in player_ids if pid]:
            for entry in self._index.get((player_id, str(year).upper(), set), []):
                if entry.player_type is None or entry.player_type == player_type:
                    return entry
        return None

    def audit_status(self, record: StoredCardSelectionRecord) -> Optional[SelectionAuditStatus]:
        """Compare a stored card against the current selections.

        Args:
          record: Selection-related fields of the stored card.

        Returns:
          The card's status, or None if no selection is involved with the card.
        """
        expected = self.lookup(player_ids=record.player_ids, year=record.year, set=record.showdown_set, player_type=record.player_type)

        if record.selection_key is None:
            return SelectionAuditStatus.MISSING if expected else None
        if expected is None or expected.key != record.selection_key:
            return SelectionAuditStatus.ORPHANED
        if expected.fingerprint != record.selection_fingerprint:
            return SelectionAuditStatus.STALE
        return SelectionAuditStatus.OK
