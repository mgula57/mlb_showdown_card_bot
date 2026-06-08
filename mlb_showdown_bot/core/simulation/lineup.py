from __future__ import annotations

from ..card.showdown_player_card import ShowdownPlayerCard
from ..shared.player_position import PlayerType


class Lineup:
    """Batting order and designated pitcher for one team."""

    def __init__(self, batting_order: list[ShowdownPlayerCard], pitcher: ShowdownPlayerCard):
        if not batting_order:
            raise ValueError("Batting order cannot be empty.")
        self.batting_order = batting_order
        self.pitcher = pitcher

    @classmethod
    def from_cards(cls, cards: list[ShowdownPlayerCard]) -> 'Lineup':
        """First card whose player_type is PITCHER becomes the starting pitcher.
        All remaining cards form the batting order (DH-style: pitcher does not bat).
        Raises ValueError if no pitcher is found.
        """
        pitcher: ShowdownPlayerCard | None = None
        batters: list[ShowdownPlayerCard] = []
        for card in cards:
            if pitcher is None and card.player_type == PlayerType.PITCHER:
                pitcher = card
            else:
                batters.append(card)
        if pitcher is None:
            raise ValueError("No pitcher card found. Provide at least one card with player_type=PITCHER.")
        if not batters:
            raise ValueError("No position players found. Provide at least one non-pitcher card.")
        return cls(batting_order=batters, pitcher=pitcher)

    @classmethod
    def from_team(cls, team: 'ShowdownTeam') -> 'Lineup':  # type: ignore[name-defined]
        """Build a Lineup from a ShowdownTeam, using rotation[0] as starter."""
        if not team.rotation:
            raise ValueError(f"Team '{team.name}' has no pitchers in rotation.")
        if not team.batting_order:
            raise ValueError(f"Team '{team.name}' has no position players in batting order.")
        return cls(batting_order=team.batting_order, pitcher=team.rotation[0])
