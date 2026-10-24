from bisect import bisect_left, bisect_right
from enum import Enum
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ..database.postgres_db import ExploreDataRecord
from ..shared.player_position import Position


PLAYER_SUBTYPES = ('POSITION_PLAYER', 'STARTING_PITCHER', 'RELIEF_PITCHER')


class ShowdownBotSetPlayer(ExploreDataRecord):
    """Extended player record for set building"""

    priority_score: float = 0.0  # Weighted quality + volume + career score used for selection

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
    career: float = Field(0.0, ge=0, le=1, description="Career WAR through the set's latest year, to favor established veterans")


class TeamWeighting(str, Enum):
    """How each team's share of the set is decided"""
    EVEN = 'EVEN'  # Every team gets the same share (WOTC 2000/2001: 15-17 cards per team)
    STRENGTH = 'STRENGTH'  # Stronger teams get more cards (WOTC 2002-2005: 5-16 cards per team)


class OtherEditionsRule(str, Enum):
    """What to do with players who already have a card in another edition of the release"""
    ALLOW = 'ALLOW'  # No restriction (a base set, or a re-rated update series)
    EXCLUDE = 'EXCLUDE'  # Only players new to the release
    NEW_TEAM_ONLY = 'NEW_TEAM_ONLY'  # New players, plus repeats now on a different team (WOTC Trading Deadline)

    def blocks(self, team_id: Optional[str], existing_team_ids: Optional[List[str]]) -> bool:
        if existing_team_ids is None or self == OtherEditionsRule.ALLOW:
            return False
        return self == OtherEditionsRule.EXCLUDE or team_id in existing_team_ids


class TeamMinimums(BaseModel):
    """Cards every team gets of each player type before the rest of the set fills, so each team can field a club"""
    hitters: int = Field(0, ge=0, le=15)
    starters: int = Field(0, ge=0, le=6)
    relievers: int = Field(0, ge=0, le=10)

    def by_subtype(self) -> Dict[str, int]:
        return {'POSITION_PLAYER': self.hitters, 'STARTING_PITCHER': self.starters, 'RELIEF_PITCHER': self.relievers}

    @property
    def total(self) -> int:
        return self.hitters + self.starters + self.relievers


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
    def player_subtype(self) -> str:
        """Groups are keyed by a player subtype or a position slot"""
        return self.key if self.key in PLAYER_SUBTYPES else SlotPosition.player_subtype(self.key)

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
    # Share of a team's target that follows its strength under `TeamWeighting.STRENGTH` (the rest is an even
    # share), which keeps the spread near WOTC's 2002-2005 range instead of giving a juggernaut 3x a rebuilder
    STRENGTH_BLEND = 0.5

    def __init__(self, player_pool: List[ShowdownBotSetPlayer], set_size: int, weights: SelectionWeights,
                 team_weighting: TeamWeighting = TeamWeighting.EVEN, unique_players: bool = True):
        """`player_pool` must already carry its `priority_score` (see `score_player_pool`)"""
        self.player_pool = player_pool
        self.weights = weights
        self.unique_players = unique_players
        self.team_targets = self._team_targets(player_pool, set_size, team_weighting)
        self.team_counts: Dict[str, int] = {}
        self.team_subtype_counts: Dict[tuple, int] = {}
        self.selected_ids: set = set()
        self.selected_keys: set = set()
        self.selected: List[ShowdownBotSetPlayer] = []

    @classmethod
    def _team_targets(cls, player_pool: List[ExploreDataRecord], set_size: int, team_weighting: TeamWeighting) -> Dict[str, float]:
        """Cards each team should end up with. Strength is the team's share of positive WAR in the pool."""
        teams = sorted({p.team_id for p in player_pool if p.team_id})
        even = set_size / max(1, len(teams))
        team_war = {team: 0.0 for team in teams}
        for player in player_pool:
            if player.team_id:
                team_war[player.team_id] += max(player.war or 0.0, 0.0)
        total_war = sum(team_war.values())
        if team_weighting == TeamWeighting.EVEN or total_war <= 0:
            return {team: even for team in teams}
        return {
            team: (1 - cls.STRENGTH_BLEND) * even + cls.STRENGTH_BLEND * set_size * team_war[team] / total_war
            for team in teams
        }

    def player_key(self, player: ExploreDataRecord) -> str:
        """Identity used to keep one card per player (two-way type overrides count as separate players)"""
        if self.unique_players and player.bref_id:
            return player.bref_id_w_type_override
        return player.id

    def is_available(self, player: ExploreDataRecord) -> bool:
        return player.id not in self.selected_ids and self.player_key(player) not in self.selected_keys

    def team_subtype_count(self, team_id: str, player_subtype: str) -> int:
        return self.team_subtype_counts.get((team_id, player_subtype), 0)

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
                          quality_score_fn: Callable[[ExploreDataRecord], float],
                          career_war_fn: Callable[[ExploreDataRecord], float]) -> List[ShowdownBotSetPlayer]:
        """Attach each player's weighted quality + volume + career `priority_score`, the part of the score that
        doesn't change as the set fills"""
        scored: List[ShowdownBotSetPlayer] = []
        for subtype in PLAYER_SUBTYPES:
            players = [p for p in player_pool if p.player_subtype == subtype]
            quality = cls._percentile_ranks({p.id: quality_score_fn(p) for p in players})
            volume = cls._percentile_ranks({p.id: cls.volume(p) for p in players})
            career = cls._percentile_ranks({p.id: career_war_fn(p) for p in players})
            scored.extend(
                ShowdownBotSetPlayer(
                    **p.model_dump(),
                    priority_score=weights.quality * quality[p.id] + weights.volume * volume[p.id] + weights.career * career[p.id],
                )
                for p in players
            )
        return scored

    def _team_balance(self, team_id: str) -> float:
        """Positive while a team is under its target share, 0 at it, negative once over it. Scaled by the
        square root of the share (roughly one standard deviation for a random draw), so a 2-card swing
        matters about as much in a 100-card set as a 4-card swing in a 450-card set."""
        target = self.team_targets.get(team_id, 0.0)
        balance = (target - self.team_counts.get(team_id, 0)) / max(1.0, target) ** 0.5
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
        self.selected_keys.add(self.player_key(player))
        self.selected.append(player)
        self.team_counts[player.team_id] = self.team_counts.get(player.team_id, 0) + 1
        subtype_key = (player.team_id, player.player_subtype)
        self.team_subtype_counts[subtype_key] = self.team_subtype_counts.get(subtype_key, 0) + 1
        if group is not None:
            group.members.append(player)

    def fill(self, groups: List[SlotGroup]) -> None:
        """Greedily fill every group's remaining slots from unselected players it accepts"""
        candidates = {
            group.key: [p for p in self.player_pool if self.is_available(p) and group.accepts(p)]
            for group in groups
        }
        while True:
            best: Optional[tuple] = None
            for group in groups:
                if group.remaining == 0:
                    continue
                for player in candidates[group.key]:
                    if not self.is_available(player):
                        continue
                    score = self.score(player, group)
                    if best is None or score > best[0]:
                        best = (score, player, group)
            if best is None:
                return
            _, player, group = best
            self.add(player, group)

    def fill_team_minimums(self, groups: List[SlotGroup], minimums: TeamMinimums) -> List[str]:
        """Give every team its minimum cards of each player type before the main fill, taking each team's
        highest priority cards that still fit an open slot. Returns a warning per team that falls short."""
        shortfalls: List[str] = []
        teams = sorted(self.team_targets)
        for player_subtype, minimum in minimums.by_subtype().items():
            if minimum == 0:
                continue
            for team in teams:
                candidates = sorted(
                    (p for p in self.player_pool if p.team_id == team and p.player_subtype == player_subtype),
                    key=lambda p: p.priority_score, reverse=True
                )
                for player in candidates:
                    if self.team_subtype_count(team, player_subtype) >= minimum:
                        break
                    if not self.is_available(player):
                        continue
                    # A full position slot borrows an open slot of the same type, so late teams still get their minimum
                    group = next((g for g in groups if g.remaining and g.accepts(player)), None) \
                        or next((g for g in groups if g.remaining and g.player_subtype == player_subtype), None)
                    if group is not None:
                        self.add(player, group)
                count = self.team_subtype_count(team, player_subtype)
                if count < minimum:
                    shortfalls.append(f"{team} has {count} of {minimum} {player_subtype.replace('_', ' ').lower()}s")
        return shortfalls
