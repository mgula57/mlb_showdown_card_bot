from __future__ import annotations
from enum import Enum
from pydantic import BaseModel

from ..card.showdown_player_card import ShowdownPlayerCard
from .models import AtBatResult, HalfInningResult, PlayerBoxScore
from .ruleset import SimulationRuleset


class GameStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"


class GameState(BaseModel):
    model_config = {'arbitrary_types_allowed': True}

    ruleset: SimulationRuleset

    # Lineups — embedded for full serialization portability
    away_batting_order: list[ShowdownPlayerCard]
    away_pitcher: ShowdownPlayerCard
    away_pitchers_remaining: list[ShowdownPlayerCard] = []
    home_batting_order: list[ShowdownPlayerCard]
    home_pitcher: ShowdownPlayerCard
    home_pitchers_remaining: list[ShowdownPlayerCard] = []

    # Batting cursors (persist across innings)
    away_cursor: int = 0
    home_cursor: int = 0

    # Inning progress
    completed_half_innings: list[HalfInningResult] = []
    current_half_at_bats: list[AtBatResult] = []
    current_inning: int = 1
    is_top_half: bool = True  # True = away team batting
    outs: int = 0
    runners: dict[int, str] = {}  # {1: name, 2: name, 3: name}

    # Box scores keyed by player name
    away_box: dict[str, PlayerBoxScore] = {}
    home_box: dict[str, PlayerBoxScore] = {}

    status: GameStatus = GameStatus.IN_PROGRESS

    @property
    def away_score(self) -> int:
        return sum(half.runs for half in self.completed_half_innings if half.is_top)

    @property
    def home_score(self) -> int:
        return sum(half.runs for half in self.completed_half_innings if not half.is_top)

    @property
    def current_batter(self) -> ShowdownPlayerCard:
        if self.is_top_half:
            order = self.away_batting_order
            return order[self.away_cursor % len(order)]
        order = self.home_batting_order
        return order[self.home_cursor % len(order)]

    @property
    def current_pitcher(self) -> ShowdownPlayerCard:
        return self.home_pitcher if self.is_top_half else self.away_pitcher

    @property
    def batting_team_box(self) -> dict[str, PlayerBoxScore]:
        return self.away_box if self.is_top_half else self.home_box

    @property
    def fielding_team_box(self) -> dict[str, PlayerBoxScore]:
        return self.home_box if self.is_top_half else self.away_box
