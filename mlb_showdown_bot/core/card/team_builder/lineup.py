from dataclasses import dataclass
from typing import Optional


# Normalization bounds for the raw inputs. Values outside these clamp to 0..1 so a
# single extreme card can't dominate the ordering.
_COMMAND_MAX   = 16.0   # hitter on-base command tops out around 16
_OUTS_MAX      = 20.0   # chart is 20 slots wide
_SPEED_MAX     = 25.0
_OBP_FLOOR     = 0.250
_OBP_CEILING   = 0.450
_SLG_FLOOR     = 0.300
_SLG_CEILING   = 0.650
_POINTS_MAX    = 600.0  # only used as a slugging fallback


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass
class LineupCandidate:
    """A single hitter eligible for the batting order, with the stats needed to place them.

    Stats are optional because the team query only hydrates BOT and WOTC cards; WBC and
    CUSTOM slots arrive with nulls and fall back to a neutral score so they sort last
    rather than raising.
    """
    card_id: str
    card_source: str
    field_position: str
    command: Optional[int] = None
    outs: Optional[int] = None
    speed: Optional[int] = None
    points: Optional[int] = None
    onbase_perc: Optional[float] = None
    slugging_perc: Optional[float] = None

    @property
    def has_stats(self) -> bool:
        return self.command is not None or self.onbase_perc is not None

    @property
    def on_base_score(self) -> float:
        """0..1. Blends the card's own chart (what actually decides the game) with real OBP."""
        card_score: Optional[float] = None
        if self.command is not None and self.outs is not None:
            card_score = (
                _clamp(self.command / _COMMAND_MAX) + _clamp((_OUTS_MAX - self.outs) / _OUTS_MAX)
            ) / 2

        real_score: Optional[float] = None
        if self.onbase_perc is not None:
            real_score = _clamp((self.onbase_perc - _OBP_FLOOR) / (_OBP_CEILING - _OBP_FLOOR))

        scores = [s for s in (card_score, real_score) if s is not None]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def power_score(self) -> float:
        """0..1. Real slugging when known, otherwise points as a rough proxy."""
        if self.slugging_perc is not None:
            return _clamp((self.slugging_perc - _SLG_FLOOR) / (_SLG_CEILING - _SLG_FLOOR))
        if self.points is not None:
            return _clamp(self.points / _POINTS_MAX)
        return 0.0

    @property
    def speed_score(self) -> float:
        return _clamp(self.speed / _SPEED_MAX) if self.speed is not None else 0.0

    @property
    def overall_score(self) -> float:
        return self.on_base_score + self.power_score


class LineupBuilder:
    """Builds a conventional 1-9 batting order from a team's nine lineup slots.

    Encodes standard baseball construction: on-base and speed at the top, the best
    all-around hitter third, power in the middle, the rest descending, and the pitcher
    ninth whenever the team is not using a DH.
    """

    # Weight applied to speed when choosing the leadoff hitter.
    LEADOFF_SPEED_WEIGHT = 0.4

    def __init__(self, candidates: list[LineupCandidate], pitcher: Optional[LineupCandidate] = None):
        self.candidates = candidates
        self.pitcher = pitcher

    def build(self) -> list[dict]:
        """Return LineupSlot dicts (card_id, card_source, field_position, batting_order)."""
        remaining = list(self.candidates)
        ordered: list[LineupCandidate] = []

        def take(key) -> None:
            if not remaining:
                return
            pick = max(remaining, key=key)
            remaining.remove(pick)
            ordered.append(pick)

        # 1: on-base with speed  |  2: pure on-base  |  3: best all-around
        take(lambda c: c.on_base_score + self.LEADOFF_SPEED_WEIGHT * c.speed_score)
        take(lambda c: c.on_base_score)
        take(lambda c: c.overall_score)
        # 4-5: power
        take(lambda c: c.power_score)
        take(lambda c: c.power_score)
        # 6-9: everyone else, best first
        ordered.extend(sorted(remaining, key=lambda c: c.overall_score, reverse=True))

        # The pitcher always hits last when there is no DH.
        if self.pitcher is not None:
            ordered.append(self.pitcher)

        return [
            {
                'card_id': c.card_id,
                'card_source': c.card_source,
                'field_position': c.field_position,
                'batting_order': i + 1,
            }
            for i, c in enumerate(ordered)
        ]
