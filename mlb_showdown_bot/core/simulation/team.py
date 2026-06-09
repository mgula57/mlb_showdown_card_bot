from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from ..card.showdown_player_card import ShowdownPlayerCard


# ---------------------------------------------------------------------------
# Simulation-ready team
# ---------------------------------------------------------------------------

@dataclass
class ShowdownTeam:
    """A team of ShowdownPlayerCard objects ready for simulation.

    Set/Era are intentionally NOT stored here — they belong on SimulationRuleset
    so the same team can be used across different ruleset configurations.

    team_id, abbreviation, and season are optional metadata that are populated
    when building from the MLB Stats API but may be absent for user-created teams.
    """
    name: str
    roster: list[ShowdownPlayerCard] = field(default_factory=list)
    batting_order: list[ShowdownPlayerCard] = field(default_factory=list)
    rotation: list[ShowdownPlayerCard] = field(default_factory=list)  # SP first, then RP/CL
    team_id: int | None = None
    abbreviation: str | None = None
    season: int | None = None

    @property
    def starting_pitcher(self) -> ShowdownPlayerCard | None:
        return self.rotation[0] if self.rotation else None


# ---------------------------------------------------------------------------
# Saved-team models (DB persistence layer)
# ---------------------------------------------------------------------------

class SavedTeamSlot(BaseModel):
    """One roster slot in a user-built team.

    Mirrors a row in internal.team_builder_slots.
    slot_key examples: 'CA', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH',
                       'SP1'–'SP5', 'RP1'–'RP7', 'BE1'–'BE4'.
    card_id is the archive composite key: '{year}-{bref_id}-{type_override}'.
    """
    id: int
    team_id: int
    slot_key: str
    card_source: Literal['bot', 'wotc']
    card_id: str
    card_snapshot: dict | None = None
    created_at: datetime | None = None


class SavedTeam(BaseModel):
    """A user-built team persisted in the database.

    Mirrors a row in internal.team_builder_teams plus its related slots.
    Use SavedTeam.from_db(data) to construct from the dict returned by
    PostgresDB.get_team_with_slots().
    """
    id: int
    user_id: str
    name: str
    showdown_set: str = 'EXPANDED'
    team_type: str = 'custom'
    roster_size: int = 25
    bullpen_size: int = 7
    bench_multiplier: float = 0.2
    metadata: dict | None = None
    slots: list[SavedTeamSlot] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_db(cls, data: dict) -> 'SavedTeam':
        """Construct from a dict returned by PostgresDB.get_team_with_slots()."""
        return cls.model_validate(data)

    @property
    def filled_slots(self) -> list[SavedTeamSlot]:
        return [s for s in self.slots if s.card_id]

    @property
    def inferred_season(self) -> int | None:
        """Best-effort season from slot snapshots; None if not determinable."""
        for slot in self.filled_slots:
            if slot.card_snapshot:
                year = slot.card_snapshot.get('year')
                if year:
                    try:
                        return int(year)
                    except (ValueError, TypeError):
                        pass
        return None
