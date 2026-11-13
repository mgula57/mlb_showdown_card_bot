"""
Release Builder foil suggestions: picks about 15% of one edition's cards to tag `FOIL`, the way WOTC
chose its foils. In the 2001 base set (60 foils of 462) every team got at least one, usually its best
card, and stronger clubs got up to four. Points alone don't explain the rest: closers, award winners,
league leaders and franchise legends were foiled over higher point cards. Expansions are smaller and
don't cover every team, so they skip the team floor and lean harder on the season.

Only suggests: the builder shows the picks and the user applies them as tags.
"""

from collections import defaultdict
from enum import Enum
from math import ceil
from typing import ClassVar, Dict, List, Optional

from pydantic import BaseModel

from ..database.postgres_db import PostgresDB
from .selection import PLAYER_SUBTYPES, SlotPosition, WeightedPlayerSelector


FOIL_TAG = 'FOIL'


class FoilSetType(str, Enum):
    """Which WOTC pattern to follow"""
    BASE = 'BASE'  # Every team gets a foil (its best card), stronger teams get more
    EXPANSION = 'EXPANSION'  # No team floor; the season's standouts


class FoilWeights(BaseModel):
    season: float  # Points and bWAR (and saves for relievers) within the card's player type
    career: float  # Career bWAR through the card's year
    notability: float  # Awards, Hall of Fame and leading the edition in a counting stat


class FoilCandidate(BaseModel):
    """The parts of a release card's snapshot that a foil pick looks at"""

    source_card_id: str
    name: str
    bref_id: Optional[str] = None
    year: Optional[int] = None
    team_id: Optional[str] = None
    player_subtype: str
    points: float = 0.0
    war: float = 0.0
    awards: List[str] = []
    is_hof: bool = False
    stats: Dict[str, float] = {}
    is_foil: bool = False

    # Stats an edition leader stands out in (WOTC foiled the 2000 AL saves leader at 160 pts)
    LEADER_STATS: ClassVar[Dict[str, Dict[str, str]]] = {
        'POSITION_PLAYER': {'real_hr': 'HR'},
        'STARTING_PITCHER': {'real_w': 'Wins', 'real_so': 'K'},
        'RELIEF_PITCHER': {'real_sv': 'Saves'},
    }

    @classmethod
    def from_release_card(cls, card: dict) -> Optional['FoilCandidate']:
        snapshot = card.get('card_snapshot') or {}
        source_card_id = card.get('source_card_id')
        if not source_card_id:
            return None
        positions = snapshot.get('positions_list') or []
        if positions:
            subtype = SlotPosition.player_subtype(SlotPosition.normalize(str(positions[0])))
        else:
            subtype = 'POSITION_PLAYER' if snapshot.get('player_type') == 'HITTER' else 'STARTING_PITCHER'
        year = str(snapshot.get('year') or '')
        stat_fields = {field for fields in cls.LEADER_STATS.values() for field in fields}
        return cls(
            source_card_id=source_card_id,
            name=snapshot.get('name') or '',
            bref_id=snapshot.get('bref_id'),
            year=int(year) if year.isdigit() else None,
            team_id=snapshot.get('team_override') or snapshot.get('team_id'),
            player_subtype=subtype,
            points=_number(snapshot.get('points')),
            war=_number(snapshot.get('real_bwar')),
            awards=[str(a) for a in snapshot.get('awards_list') or []],
            is_hof=bool(snapshot.get('is_hof')),
            stats={field: _number(snapshot.get(field)) for field in stat_fields},
            is_foil=FOIL_TAG in (card.get('tags') or []),
        )

    @property
    def player_key(self) -> str:
        """One foil per player, even with two of their seasons in the edition"""
        return self.bref_id or self.source_card_id


class FoilSuggestion(BaseModel):
    source_card_id: str
    score: float  # 0-100
    reasons: List[str]


class FoilSuggestionResult(BaseModel):
    target: int  # Foils the edition should end up with, existing ones included
    existing_count: int
    suggestions: List[FoilSuggestion]


class FoilSuggester:
    """Ranks one edition's cards for foils and picks enough new ones to reach `FOIL_SHARE`"""

    FOIL_SHARE = 0.15
    # 2001: no team past 4 foils with 2 per team on average
    TEAM_CAP_MULTIPLIER = 2.0
    # Share of a player type's cards that count as an edition leader in a stat (at least 1)
    LEADER_SHARE = 0.03
    # A team's saves leader with at least this many counts as its closer
    CLOSER_MIN_SAVES = 20
    CLOSER_VALUE = 0.5
    # Most of the foils a pitcher type can take. Scores rank within a type, so without a cap middling
    # closers outrank good hitters (2001: 13 starters and 8 relievers of 60)
    SUBTYPE_MAX_SHARE = {'STARTING_PITCHER': 0.25, 'RELIEF_PITCHER': 0.15}

    WEIGHTS = {
        FoilSetType.BASE: FoilWeights(season=0.5, career=0.25, notability=0.25),
        FoilSetType.EXPANSION: FoilWeights(season=0.6, career=0.15, notability=0.25),
    }

    # Notability of an award by its finish (`MVP-1`, `CYA-3`, `ROY-1`/`RoY-1`); unranked awards use 0
    AWARD_VALUES = {
        'MVP': [(1, 1.0, 'MVP'), (5, 0.7, 'MVP top 5'), (10, 0.45, None), (99, 0.25, None)],
        'CYA': [(1, 1.0, 'Cy Young'), (5, 0.6, 'Cy Young top 5'), (99, 0.3, None)],
        'ROY': [(1, 0.8, 'Rookie of the Year'), (99, 0.35, 'ROY votes')],
    }
    FLAT_AWARDS = {'AS': (0.35, 'All-Star'), 'GG': (0.15, None), 'SS': (0.15, None)}
    HOF_VALUE = 0.5

    def __init__(self, cards: List[dict], set_type: FoilSetType, career_wars: Dict[str, float]):
        self.candidates = [c for c in (FoilCandidate.from_release_card(card) for card in cards) if c]
        self.set_type = set_type
        self.weights = self.WEIGHTS[set_type]
        self.career_wars = career_wars

    @classmethod
    def for_edition(cls, db: PostgresDB, cards: List[dict], set_type: FoilSetType) -> 'FoilSuggester':
        """Looks up career WAR through each card's own year (editions can mix seasons)"""
        bref_ids_by_year: Dict[int, set] = defaultdict(set)
        for card in cards:
            candidate = FoilCandidate.from_release_card(card)
            if candidate and candidate.bref_id and candidate.year:
                bref_ids_by_year[candidate.year].add(candidate.bref_id)
        career_wars = {
            cls._career_key(bref_id, year): war
            for year, bref_ids in bref_ids_by_year.items()
            for bref_id, war in db.fetch_career_wars(list(bref_ids), through_year=year).items()
        }
        return cls(cards, set_type, career_wars)

    @staticmethod
    def _career_key(bref_id: str, year: int) -> str:
        return f"{bref_id}:{year}"

    # -------------------------------------------------------------------------
    # SCORING
    # -------------------------------------------------------------------------

    def _award_notability(self, candidate: FoilCandidate) -> List[tuple]:
        """(value, reason) for each award and honor on the card"""
        values = []
        for award in candidate.awards:
            name, _, finish = award.upper().partition('-')
            if name in self.FLAT_AWARDS:
                values.append(self.FLAT_AWARDS[name])
            elif name in self.AWARD_VALUES and finish.isdigit():
                value, reason = next((v, r) for limit, v, r in self.AWARD_VALUES[name] if int(finish) <= limit)
                values.append((value, reason))
        if candidate.is_hof:
            values.append((self.HOF_VALUE, 'Hall of Famer'))
        return values

    def _leader_notability(self, group: List[FoilCandidate]) -> Dict[str, List[tuple]]:
        """(value, reason) for each stat a card leads its player type in, within this edition"""
        values: Dict[str, List[tuple]] = defaultdict(list)
        if not group:
            return values
        leader_count = max(1, round(len(group) * self.LEADER_SHARE))
        for field, label in FoilCandidate.LEADER_STATS[group[0].player_subtype].items():
            ranked = sorted((c for c in group if c.stats.get(field, 0) > 0), key=lambda c: -c.stats[field])
            for rank, candidate in enumerate(ranked[:leader_count]):
                values[candidate.source_card_id].append((0.8 if rank == 0 else 0.5, f"{label} leader" if rank == 0 else f"Top {label}"))
        if group[0].player_subtype == 'RELIEF_PITCHER':
            # WOTC foiled a club's closer even on bad teams (7 of 2001's 60 foils)
            closers: Dict[str, FoilCandidate] = {}
            for candidate in group:
                saves = candidate.stats.get('real_sv', 0)
                current = closers.get(candidate.team_id)
                if candidate.team_id and saves >= self.CLOSER_MIN_SAVES and (current is None or saves > current.stats['real_sv']):
                    closers[candidate.team_id] = candidate
            for candidate in closers.values():
                values[candidate.source_card_id].append((self.CLOSER_VALUE, 'Closer'))
        return values

    @staticmethod
    def _combine(values: List[float]) -> float:
        """Each extra honor adds to notability without passing 1"""
        remaining = 1.0
        for value in values:
            remaining *= 1 - min(1.0, value)
        return 1 - remaining

    def score(self) -> Dict[str, FoilSuggestion]:
        """Every candidate's 0-100 foil score, with the reasons worth showing"""
        percentile = WeightedPlayerSelector._percentile_ranks
        scored: Dict[str, FoilSuggestion] = {}
        for subtype in PLAYER_SUBTYPES:
            group = [c for c in self.candidates if c.player_subtype == subtype]
            if not group:
                continue
            points = percentile({c.source_card_id: c.points for c in group})
            war = percentile({c.source_card_id: c.war for c in group})
            saves = percentile({c.source_card_id: c.stats.get('real_sv', 0) for c in group})
            career_wars = {c.source_card_id: self.career_wars.get(self._career_key(c.bref_id, c.year), c.war) if c.bref_id and c.year else c.war for c in group}
            career = percentile(career_wars)
            leaders = self._leader_notability(group)
            for c in group:
                season_parts = [points[c.source_card_id], war[c.source_card_id]]
                if subtype == 'RELIEF_PITCHER':
                    season_parts.append(saves[c.source_card_id])
                season = sum(season_parts) / len(season_parts)
                honors = self._award_notability(c) + leaders.get(c.source_card_id, [])
                notability = self._combine([value for value, _ in honors])
                total = self.weights.season * season + self.weights.career * career[c.source_card_id] + self.weights.notability * notability

                reasons = [reason for _, reason in sorted(honors, key=lambda h: -h[0]) if reason]
                if career[c.source_card_id] >= 0.9 and career_wars[c.source_card_id] > 0:
                    reasons.append(f"{career_wars[c.source_card_id]:.0f} career WAR")
                scored[c.source_card_id] = FoilSuggestion(
                    source_card_id=c.source_card_id,
                    score=round(100 * total / (self.weights.season + self.weights.career + self.weights.notability), 1),
                    reasons=list(dict.fromkeys(reasons)),
                )
        return scored

    # -------------------------------------------------------------------------
    # PICKING
    # -------------------------------------------------------------------------

    def suggest(self) -> FoilSuggestionResult:
        target = max(1, round(len(self.candidates) * self.FOIL_SHARE)) if self.candidates else 0
        scores = self.score()
        existing = [c for c in self.candidates if c.is_foil]
        picked_ids = {c.source_card_id for c in existing}
        picked_players = {c.player_key for c in existing}
        team_counts: Dict[str, int] = defaultdict(int)
        subtype_counts: Dict[str, int] = defaultdict(int)
        for c in existing:
            subtype_counts[c.player_subtype] += 1
            if c.team_id:
                team_counts[c.team_id] += 1

        ranked = sorted((c for c in self.candidates if not c.is_foil), key=lambda c: -scores[c.source_card_id].score)
        suggestions: List[FoilSuggestion] = []

        def pick(candidate: FoilCandidate, reason: Optional[str] = None) -> None:
            suggestion = scores[candidate.source_card_id]
            if reason:
                suggestion.reasons.insert(0, reason)
            suggestions.append(suggestion)
            picked_ids.add(candidate.source_card_id)
            picked_players.add(candidate.player_key)
            subtype_counts[candidate.player_subtype] += 1
            if candidate.team_id:
                team_counts[candidate.team_id] += 1

        def is_open(candidate: FoilCandidate) -> bool:
            return candidate.source_card_id not in picked_ids and candidate.player_key not in picked_players

        def is_full() -> bool:
            return len(existing) + len(suggestions) >= target

        teams = {c.team_id for c in self.candidates if c.team_id}
        if self.set_type == FoilSetType.BASE:
            # Team floor: each team's best card, strongest teams first if there are more teams than foils
            team_leaders = {}
            for c in ranked:
                if c.team_id and c.team_id not in team_leaders and is_open(c):
                    team_leaders[c.team_id] = c
            for c in sorted(team_leaders.values(), key=lambda c: -scores[c.source_card_id].score):
                if is_full():
                    break
                if team_counts[c.team_id] == 0:
                    pick(c, 'Team leader')

        # Base sets cap any one team; expansions take the season's best wherever they are
        team_cap = ceil(self.TEAM_CAP_MULTIPLIER * target / len(teams)) if teams and self.set_type == FoilSetType.BASE else None

        def is_capped(candidate: FoilCandidate) -> bool:
            max_share = self.SUBTYPE_MAX_SHARE.get(candidate.player_subtype)
            return bool(
                (team_cap and candidate.team_id and team_counts[candidate.team_id] >= team_cap)
                or (max_share is not None and subtype_counts[candidate.player_subtype] >= ceil(max_share * target))
            )

        # Caps first; then anyone, so an edition that's mostly pitchers or one team still reaches the target
        for respect_caps in (True, False):
            for c in ranked:
                if is_full():
                    break
                if is_open(c) and not (respect_caps and is_capped(c)):
                    pick(c)

        return FoilSuggestionResult(target=target, existing_count=len(existing), suggestions=suggestions)


def _number(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
