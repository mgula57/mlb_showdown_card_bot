from __future__ import annotations

from ..card.showdown_player_card import ShowdownPlayerCard
from ..shared.player_position import PlayerType


class Lineup:
    """Batting order and pitcher rotation for one team."""

    def __init__(self, batting_order: list[ShowdownPlayerCard], pitchers: list[ShowdownPlayerCard]):
        if not batting_order:
            raise ValueError("Batting order cannot be empty.")
        if not pitchers:
            raise ValueError("Pitcher list cannot be empty.")
        self.batting_order = batting_order
        self.pitchers = pitchers  # pitchers[0] = starter, rest = bullpen

    @property
    def pitcher(self) -> ShowdownPlayerCard:
        return self.pitchers[0]

    @classmethod
    def from_cards(cls, cards: list[ShowdownPlayerCard]) -> 'Lineup':
        """Pitchers (in order) build the rotation; non-pitchers form the batting order."""
        pitchers: list[ShowdownPlayerCard] = []
        batters: list[ShowdownPlayerCard] = []
        for card in cards:
            if card.player_type == PlayerType.PITCHER:
                pitchers.append(card)
            else:
                batters.append(card)
        if not pitchers:
            raise ValueError("No pitcher card found. Provide at least one card with player_type=PITCHER.")
        if not batters:
            raise ValueError("No position players found. Provide at least one non-pitcher card.")
        return cls(batting_order=batters, pitchers=pitchers)

    @classmethod
    def from_team(cls, team: 'ShowdownTeam') -> 'Lineup':  # type: ignore[name-defined]
        """Build a Lineup from a ShowdownTeam using the full rotation."""
        if not team.rotation:
            raise ValueError(f"Team '{team.name}' has no pitchers in rotation.")
        if not team.batting_order:
            raise ValueError(f"Team '{team.name}' has no position players in batting order.")
        return cls(batting_order=team.batting_order, pitchers=list(team.rotation))
