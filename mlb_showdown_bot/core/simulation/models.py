from __future__ import annotations
from pydantic import BaseModel
from typing import Literal

from ..card.chart import ChartCategory


class AtBatResult(BaseModel):
    batter_name: str
    pitcher_name: str
    pitcher_roll: int   # 0 if outcome was manually applied
    batter_roll: int    # 0 if outcome was manually applied
    chart_owner: Literal['pitcher', 'batter']
    chart_roll: int     # 0 if outcome was manually applied
    outcome: ChartCategory
    runs_scored: int
    rbi: int
    is_hit: bool
    stolen_base_attempt: bool
    stolen_base_success: bool | None = None  # None when no attempt made


class HalfInningResult(BaseModel):
    inning: int
    is_top: bool  # True = away team batting
    at_bats: list[AtBatResult] = []

    @property
    def runs(self) -> int:
        return sum(ab.runs_scored for ab in self.at_bats)

    @property
    def hits(self) -> int:
        return sum(1 for ab in self.at_bats if ab.is_hit)


class PlayerBoxScore(BaseModel):
    name: str
    # hitting
    ab: int = 0
    hits: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    walks: int = 0
    rbi: int = 0
    strikeouts: int = 0
    stolen_bases: int = 0
    # pitching (None if position player)
    outs_recorded: int | None = None
    runs_allowed: int | None = None
    pitcher_strikeouts: int | None = None
    pitcher_walks: int | None = None

    @property
    def innings_pitched(self) -> float | None:
        if self.outs_recorded is None:
            return None
        whole = self.outs_recorded // 3
        remainder = self.outs_recorded % 3
        return float(f"{whole}.{remainder}")


class GameResult(BaseModel):
    game_set: str
    away_score: int
    home_score: int
    innings: list[HalfInningResult] = []
    away_box: list[PlayerBoxScore] = []
    home_box: list[PlayerBoxScore] = []

    @property
    def winner(self) -> Literal['away', 'home', 'tie']:
        if self.away_score > self.home_score:
            return 'away'
        if self.home_score > self.away_score:
            return 'home'
        return 'tie'

    def score_by_inning(self, is_away: bool) -> list[int]:
        return [half.runs for half in self.innings if half.is_top == is_away]
