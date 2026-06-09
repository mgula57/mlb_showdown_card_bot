from __future__ import annotations
from pydantic import BaseModel

from ..card.sets import Set


class SimulationRuleset(BaseModel):
    game_set: Set
    innings: int = 9
    extra_innings: bool = False
    # When True, pitcher's chart roll uses d24 instead of d20.
    # Rolls 21-24 are "mistake pitches" — the hitter's chart is used for the result
    # even though the pitcher won the command check.
    mistake_pitch: bool = False
    stolen_base_cap: int | None = None  # max SB per player per game; None = no cap
    starter_fatigue_outs: int | None = 18  # hook starter after this many outs (18 = 6 IP); None = no limit
    use_strategy_cards: bool = False    # Phase 2 placeholder, not yet implemented

    @classmethod
    def classic(cls) -> 'SimulationRuleset':
        return cls(game_set=Set.CLASSIC)

    @classmethod
    def expanded(cls) -> 'SimulationRuleset':
        return cls(game_set=Set.EXPANDED)

    @classmethod
    def mistake_pitch_expanded(cls) -> 'SimulationRuleset':
        return cls(game_set=Set.EXPANDED, mistake_pitch=True)
