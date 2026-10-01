from bisect import bisect_left, bisect_right
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ..database.postgres_db import ExploreDataRecord
from ..shared.player_position import Position


PLAYER_SUBTYPES = ('POSITION_PLAYER', 'STARTING_PITCHER', 'RELIEF_PITCHER')


class ShowdownBotSetPlayer(ExploreDataRecord):
    """Extended player record for set building"""

    priority_score: float = 0.0  # Weighted quality + volume score used for selection

    set_number: Optional[int] = None  # Assigned set number for the player


# =============================================================================
# MARK: - SLOT POSITIONS
# =============================================================================

class SlotPosition:
    """Position labels used for set composition targets.

    Card position labels differ by Showdown set (2000/2001 lean on `OF`, 2004/2005 add `IF`), so
    labels are folded into a fixed set of slots before matching against targets.
    """

    HITTER_SLOTS = ['C', '1B', '2B', '3B', 'SS', 'CF', 'LF/RF', 'DH']
    PITCHER_SLOTS = ['STARTER', 'RELIEVER', 'CLOSER']
    ALL = HITTER_SLOTS + PITCHER_SLOTS

    # Folded into a single slot when a card lists it first
    _PRIMARY_ALIASES = {'CA': 'C', 'OF': 'LF/RF', 'LF': 'LF/RF', 'RF': 'LF/RF', 'IF': '2B'}
    # Generic labels that can also fill any of these slots once primary matches run out
    _SECONDARY_ELIGIBILITY = {'OF': ['CF', 'LF/RF'], 'IF': ['1B', '2B', '3B', 'SS']}

    @classmethod
    def normalize(cls, position: str) -> str:
        return cls._PRIMARY_ALIASES.get(position, position)

    @classmethod
    def player_subtype(cls, slot: str) -> str:
        match slot:
            case 'STARTER': return 'STARTING_PITCHER'
            case 'RELIEVER' | 'CLOSER': return 'RELIEF_PITCHER'
            case _: return 'POSITION_PLAYER'

    @staticmethod
    def _position_values(player: ExploreDataRecord) -> List[str]:
        return [p.value if isinstance(p, Position) else str(p) for p in (player.positions_list or [])]

    @classmethod
    def primary_slot(cls, player: ExploreDataRecord) -> Optional[str]:
        """Slot for the first position printed on the card. `positions_list` keeps card order,
        unlike the `positions_and_defense` jsonb (Postgres reorders jsonb keys)."""
        positions = cls._position_values(player)
        return cls.normalize(positions[0]) if positions else None

    @classmethod
    def eligible_slots(cls, player: ExploreDataRecord) -> List[str]:
        """Every slot the card can fill, including secondary positions"""
        slots: List[str] = []
        for position in cls._position_values(player):
            for slot in [cls.normalize(position)] + cls._SECONDARY_ELIGIBILITY.get(position, []):
                if slot not in slots:
                    slots.append(slot)
        return slots


class PositionTarget(BaseModel):
    """Share of the set that should be cards at a position, plus the average points to aim for there"""
    position: str = Field(..., description="Slot position, e.g. 'SS', 'LF/RF', 'STARTER'")
    percentage: float = Field(..., ge=0, le=1, description="Share of the whole set at this position")
    avg_points: Optional[float] = Field(None, ge=0, description="Average card points to aim for at this position (None to ignore)")

    @field_validator('position')
    @classmethod
    def validate_position(cls, position: str) -> str:
        normalized = SlotPosition.normalize(position)
        if normalized not in SlotPosition.ALL:
            raise ValueError(f"Unknown position '{position}'. Expected one of {', '.join(SlotPosition.ALL)}")
        return normalized

    @property
    def player_subtype(self) -> str:
        return SlotPosition.player_subtype(self.position)

    @classmethod
    def validate_list(cls, targets: List['PositionTarget']) -> List['PositionTarget']:
        positions = [t.position for t in targets]
        duplicates = {p for p in positions if positions.count(p) > 1}
        if duplicates:
            raise ValueError(f"Duplicate position targets: {', '.join(sorted(duplicates))}")
        total = sum(t.percentage for t in targets)
        if targets and total > 1.0 + 1e-6:
            raise ValueError(f"Position target percentages must total 100% or less, got {total:.0%}")
        return targets

    @staticmethod
    def allocate_counts(shares: Dict[str, float], total: int) -> Dict[str, int]:
        """Split `total` across keys by share (largest remainder), so rounded counts still add up"""
        share_total = sum(shares.values())
        if share_total <= 0 or total <= 0:
            return {key: 0 for key in shares}
        exact = {key: total * share / share_total for key, share in shares.items()}
        counts = {key: int(value) for key, value in exact.items()}
        leftover = total - sum(counts.values())
        for key in sorted(exact, key=lambda k: exact[k] - counts[k], reverse=True)[:leftover]:
            counts[key] += 1
        return counts


# =============================================================================
# MARK: - WEIGHTS
# =============================================================================

class SelectionWeights(BaseModel):
    """Relative importance (0-1) of each factor when choosing the next card for the set"""
    quality: float = Field(1.0, ge=0, le=1, description="WAR plus All-Star/award bonuses")
    volume: float = Field(0.5, ge=0, le=1, description="Playing time: PA for hitters, IP for pitchers")
    team_balance: float = Field(0.75, ge=0, le=1, description="Keep each team near an even share of the set")
    points_fit: float = Field(1.0, ge=0, le=1, description="Steer each position toward its target average points (position targets only)")


# =============================================================================
# MARK: - SLOT GROUPS
# =============================================================================

class SlotGroup:
    """A bucket of set slots (a position or a whole player type) with a card quota and an optional
    average points target"""

    # Points distance at which a card no longer earns any points-fit credit
    POINTS_FIT_RANGE = 150.0

    def __init__(self, key: str, target: int, accepts: Callable[[ExploreDataRecord], bool], avg_points: Optional[float] = None):
        self.key = key
        self.target = target
        self.accepts = accepts
        self.avg_points = avg_points
        self.members: List[ExploreDataRecord] = []

    @property
    def remaining(self) -> int:
        return max(0, self.target - len(self.members))

    @property
    def actual_avg_points(self) -> Optional[float]:
        points = [p.points for p in self.members if p.points is not None]
        return sum(points) / len(points) if points else None

    def points_fit(self, points: Optional[int]) -> float:
        """0-1 credit for how close a card's points are to the average the remaining slots need for
        the group to land on its target. The needed average drifts after every pick, so a star
        pulls the group toward cheaper cards and vice versa."""
        if self.avg_points is None or points is None or self.remaining == 0:
            return 0.0
        current_points = sum(p.points or 0 for p in self.members)
        needed_avg = (self.avg_points * self.target - current_points) / self.remaining
        return 1.0 - min(1.0, abs(points - needed_avg) / self.POINTS_FIT_RANGE)


# =============================================================================
# MARK: - SELECTOR
# =============================================================================

class WeightedPlayerSelector:
    """Fills slot groups one card at a time, always taking the (group, card) pair with the best
    weighted score. Quality and volume are percentile ranks within each player subtype, so pitchers
    and hitters compete on the same 0-1 scale. Team balance and points fit are recomputed after each
    pick, which keeps teams even and lets each position's point average converge on its target."""

    # Team balance is clipped so one runaway team can't dominate every other factor
    MAX_TEAM_PENALTY = 2.0

    def __init__(self, player_pool: List[ShowdownBotSetPlayer], set_size: int, weights: SelectionWeights):
        """`player_pool` must already carry its `priority_score` (see `score_player_pool`)"""
        self.player_pool = player_pool
        self.weights = weights
        teams = {p.team_id for p in player_pool if p.team_id}
        self.team_target = set_size / max(1, len(teams))
        self.team_counts: Dict[str, int] = {}
        self.selected_ids: set = set()
        self.selected: List[ShowdownBotSetPlayer] = []

    # -------------------------------------------------------------------------
    # SCORING
    # -------------------------------------------------------------------------

    @staticmethod
    def volume(player: ExploreDataRecord) -> float:
        """Playing time in the unit that matters for the player's role"""
        match player.player_subtype:
            case 'POSITION_PLAYER':
                return float(player.pa or player.g or 0)
            case 'STARTING_PITCHER':
                return float(player.real_ip or 0)
            case _:
                # Spot starts inflate a reliever's IP, so roughly strip them out
                return max(0.0, float(player.real_ip or 0) - 5.0 * (player.gs or 0))

    @staticmethod
    def _percentile_ranks(values: Dict[str, float]) -> Dict[str, float]:
        """0-1 rank of each value within the group (ties share the midpoint rank)"""
        if len(values) <= 1:
            return {key: 1.0 for key in values}
        ordered = sorted(values.values())
        denominator = len(ordered) - 1
        return {
            key: ((bisect_left(ordered, value) + bisect_right(ordered, value) - 1) / 2) / denominator
            for key, value in values.items()
        }

    @classmethod
    def score_player_pool(cls, player_pool: List[ExploreDataRecord], weights: SelectionWeights,
                          quality_score_fn: Callable[[ExploreDataRecord], float]) -> List[ShowdownBotSetPlayer]:
        """Attach each player's weighted quality + volume `priority_score`, the part of the score that
        doesn't change as the set fills"""
        scored: List[ShowdownBotSetPlayer] = []
        for subtype in PLAYER_SUBTYPES:
            players = [p for p in player_pool if p.player_subtype == subtype]
            quality = cls._percentile_ranks({p.id: quality_score_fn(p) for p in players})
            volume = cls._percentile_ranks({p.id: cls.volume(p) for p in players})
            scored.extend(
                ShowdownBotSetPlayer(**p.model_dump(), priority_score=weights.quality * quality[p.id] + weights.volume * volume[p.id])
                for p in players
            )
        return scored

    def _team_balance(self, team_id: str) -> float:
        """Positive while a team is under an even share, 0 at it, negative once over it. Scaled by the
        square root of the share (roughly one standard deviation for a random draw), so a 2-card swing
        matters about as much in a 100-card set as a 4-card swing in a 450-card set."""
        balance = (self.team_target - self.team_counts.get(team_id, 0)) / max(1.0, self.team_target) ** 0.5
        return max(-self.MAX_TEAM_PENALTY, balance)

    def score(self, player: ShowdownBotSetPlayer, group: SlotGroup) -> float:
        return (
            player.priority_score
            + self.weights.team_balance * self._team_balance(player.team_id)
            + self.weights.points_fit * group.points_fit(player.points)
        )

    # -------------------------------------------------------------------------
    # SELECTION
    # -------------------------------------------------------------------------

    def add(self, player: ShowdownBotSetPlayer, group: Optional[SlotGroup] = None) -> None:
        self.selected_ids.add(player.id)
        self.selected.append(player)
        self.team_counts[player.team_id] = self.team_counts.get(player.team_id, 0) + 1
        if group is not None:
            group.members.append(player)

    def fill(self, groups: List[SlotGroup]) -> None:
        """Greedily fill every group's remaining slots from unselected players it accepts"""
        candidates = {
            group.key: [p for p in self.player_pool if p.id not in self.selected_ids and group.accepts(p)]
            for group in groups
        }
        while True:
            best: Optional[tuple] = None
            for group in groups:
                if group.remaining == 0:
                    continue
                for player in candidates[group.key]:
                    if player.id in self.selected_ids:
                        continue
                    score = self.score(player, group)
                    if best is None or score > best[0]:
                        best = (score, player, group)
            if best is None:
                return
            _, player, group = best
            self.add(player, group)
