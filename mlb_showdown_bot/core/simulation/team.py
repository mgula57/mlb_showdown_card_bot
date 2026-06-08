from __future__ import annotations
from dataclasses import dataclass, field

from ..card.showdown_player_card import ShowdownPlayerCard


@dataclass
class ShowdownTeam:
    """A team of ShowdownPlayerCard objects ready for simulation.

    Set/Era are intentionally NOT stored here — they belong on SimulationRuleset
    so the same team can be used across different ruleset configurations.
    """
    name: str
    team_id: int
    abbreviation: str
    season: int
    roster: list[ShowdownPlayerCard] = field(default_factory=list)
    batting_order: list[ShowdownPlayerCard] = field(default_factory=list)
    rotation: list[ShowdownPlayerCard] = field(default_factory=list)  # SP first, then RP/CL

    @property
    def starting_pitcher(self) -> ShowdownPlayerCard | None:
        return self.rotation[0] if self.rotation else None
