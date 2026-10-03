"""Guided Draft: a turn-based draft where each round offers a handful of similarly priced cards
for one roster need and the drafter picks one.

The draft opens with three Cornerstone rounds (Ace, Star Position Player, Closer), each with its
own price anchor and a ±50 window, then moves to Fill rounds that target the next open roster slot
with a ±10 window. Rounds are derived entirely from the team's saved roster, so the planner is
stateless — the client just asks for "the next round" after every pick is saved.
"""
import random
from dataclasses import dataclass, field

from .autofill import (
    BUCKET_QUERY_FILTERS,
    OFFENSE_POSITIONS,
    _bullpen_slot_weights,
    _existing_pts_by_bucket,
    _is_small_sample,
    _pos_matches,
    _split_extra_roster_slots,
    fetch_stratified_candidates,
)
from .team import Team, ROTATION_ROLES, BULLPEN_ROLES

# Budget split used to price each round. Mirrors the "Balanced" autofill preset
# (DEFAULT_PTS_DISTRIBUTION in frontend/src/api/userTeams.ts) — keep in sync.
GUIDED_PTS_DISTRIBUTION: dict[str, float] = {'offense': 0.52, 'rotation': 0.28, 'bullpen': 0.19, 'bench': 0.01}

# Cheapest a real card can be — reserved per still-open slot so one pick can't strand the rest
# of the draft (matches MIN_CARD_POINTS in TeamDetail.tsx and the autofill price-band floor).
MIN_CARD_POINTS = 10

# Lineup positions are offered scarcest-first, so the thin positions get filled while there's
# still budget to spend on them.
FILL_POSITION_ORDER = ['C', 'SS', 'CF', '2B', '3B', '1B', 'LF', 'RF', 'DH']
assert sorted(FILL_POSITION_ORDER) == sorted(OFFENSE_POSITIONS)

CORNERSTONE_ROLES = ('ace', 'star', 'closer')
# How Fill rounds pick the next slot: 'linear' walks FILL_POSITION_ORDER -> rotation -> bullpen ->
# bench; 'random' draws any open slot (cornerstones always come first either way).
FILL_ORDERS = ('linear', 'random')
CORNERSTONE_LABELS = {'ace': 'Ace Pitcher', 'star': 'Star Position Player', 'closer': 'Closer'}

# Spend shape per bucket as (top, bottom) multiples of the bucket's average slot price — a linear
# ramp between them, normalized so the bucket still totals its budget. Mirrors how a real roster
# spends: a star or two and some cheap fillers in the lineup, a descending rotation. The bullpen
# uses autofill's closer + descending committee shape instead (`_bullpen_slot_weights`).
_SPEND_SHAPES: dict[str, tuple[float, float]] = {
    'offense':  (1.8, 0.45),
    'rotation': (1.45, 0.6),
    'bench':    (1.5, 0.6),
}

# Price windows (± target), tried in order until enough options turn up.
CORNERSTONE_WINDOWS = (50, 75, 100)
FILL_WINDOWS = (10, 25, 50, 100)

# Search-filter vocabulary for a lineup slot (the card DB stores corner OF as one 'LF/RF').
_FIELD_POSITION_FILTER = {pos: ('LF/RF' if pos in ('LF', 'RF') else pos) for pos in OFFENSE_POSITIONS}


@dataclass
class GuidedRound:
    index: int                    # 1-based round number == roster picks so far + 1
    total: int                    # roster_size
    phase: str                    # 'cornerstone' | 'fill'
    role: str                     # 'ace' | 'star' | 'closer' | 'field' | 'rotation' | 'bullpen' | 'bench'
    label: str                    # human-readable round name, e.g. "Shortstop" / "Closer"
    position: str | None          # roster slot this round fills; None for the star (varies per option)
    target_points: int
    window: int                   # ± points actually used to find the options
    options: list[dict] = field(default_factory=list)  # [{'card': {...}, 'roster_position': 'SS'}]
    cornerstones: dict[str, bool] = field(default_factory=dict)  # role -> already covered

    def to_dict(self) -> dict:
        return {
            'round': {
                'index': self.index, 'total': self.total, 'phase': self.phase, 'role': self.role,
                'label': self.label, 'position': self.position,
            },
            'target_points': self.target_points,
            'window': self.window,
            'options': self.options,
            'cornerstones': self.cornerstones,
        }


@dataclass
class _RoundSpec:
    """What the next round is asking for, before any candidates are fetched."""
    phase: str
    role: str
    label: str
    position: str | None
    bucket: str                   # autofill bucket this round spends from
    query_filters: dict
    target_points: int
    windows: tuple[int, ...]
    # Broader query tried only if `query_filters` can't fill the round at any window.
    fallback_filters: dict | None = None


_POSITION_LABELS = {
    'C': 'Catcher', '1B': 'First Base', '2B': 'Second Base', '3B': 'Third Base', 'SS': 'Shortstop',
    'LF': 'Left Field', 'CF': 'Center Field', 'RF': 'Right Field', 'DH': 'Designated Hitter',
    'RP': 'Bullpen', 'BE': 'Bench',
}


class GuidedDraftPlanner:
    """Works out a team's next Guided Draft round and samples its options."""

    OPTION_COUNT = 4
    SAMPLE_PER_BAND = 40
    # Last-resort sample across the whole affordable range, when no window around the target
    # turns up enough cards (e.g. a top-tier closer target above any reliever in the pool).
    SAMPLE_FALLBACK = 300

    def __init__(
        self,
        team: Team,
        existing_card_points: dict[str, int],
        card_sources: list[str],
        sets_by_source: dict[str, list[str]],
        active_filters: dict,
        pts_target: int | None = None,
        user_id: str | None = None,
        order: str = 'linear',
    ):
        self.team = team
        self.existing_card_points = existing_card_points
        self.card_sources = card_sources
        self.sets_by_source = sets_by_source
        self.active_filters = active_filters
        self.pts_limit = team.pts_limit or pts_target or 0
        self.user_id = user_id
        self.order = order if order in FILL_ORDERS else 'linear'

        roster = team.roster
        self.field_filled = {s.roster_position for s in roster if s.roster_position in OFFENSE_POSITIONS}
        self.rotation_filled = {s.roster_position for s in roster if s.roster_position in ROTATION_ROLES}
        self.bullpen_count = sum(1 for s in roster if s.roster_position in BULLPEN_ROLES)
        self.bench_count = sum(1 for s in roster if s.roster_position == 'BE')
        self.drafted_ids = {s.card_id for s in roster}

        extra = max(0, team.roster_size - (len(OFFENSE_POSITIONS) + team.num_starters + team.min_bench + team.min_bullpen))
        bench_extra, bullpen_extra = _split_extra_roster_slots(extra, team.min_bench, team.min_bullpen)
        self.bench_target = team.min_bench + bench_extra
        self.bullpen_target = team.min_bullpen + bullpen_extra

        self.spent_by_bucket = _existing_pts_by_bucket(team, {}, team.bench_pts_multiplier, existing_card_points)
        # Seeded per team + round so re-requesting the same round prices it the same way.
        self._rng = random.Random(f'{team.team_id}:{len(roster)}')

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def next_round(self, db) -> GuidedRound | None:
        """The next round with sampled options, or None once the roster is full."""
        if len(self.team.roster) >= self.team.roster_size:
            return None
        spec = self._next_spec()
        options, window = self._sample_options(db, spec)
        return GuidedRound(
            index=len(self.team.roster) + 1,
            total=self.team.roster_size,
            phase=spec.phase,
            role=spec.role,
            label=spec.label,
            position=spec.position,
            target_points=spec.target_points,
            window=window,
            options=options,
            cornerstones=self.cornerstone_coverage,
        )

    @property
    def cornerstone_coverage(self) -> dict[str, bool]:
        return {
            'ace': bool(self.rotation_filled),
            'star': bool(self.field_filled),
            'closer': self.bullpen_count > 0,
        }

    # ------------------------------------------------------------------
    # Round selection
    # ------------------------------------------------------------------

    def _next_spec(self) -> _RoundSpec:
        # Cornerstones open the draft: offered while fewer than three picks are in and that role
        # isn't already covered (a manually-started team skips straight past the ones it has).
        if len(self.team.roster) < len(CORNERSTONE_ROLES):
            coverage = self.cornerstone_coverage
            for role in CORNERSTONE_ROLES:
                if not coverage[role]:
                    return self._cornerstone_spec(role)
        return self._fill_spec()

    def _cornerstone_spec(self, role: str) -> _RoundSpec:
        # Each cornerstone takes the top tier of its bucket's spend shape.
        if role == 'ace':
            return _RoundSpec('cornerstone', role, CORNERSTONE_LABELS[role], self._first_open_rotation_role(),
                              'rotation', BUCKET_QUERY_FILTERS['rotation'], self._slot_target('rotation', top=True),
                              CORNERSTONE_WINDOWS)
        if role == 'star':
            return _RoundSpec('cornerstone', role, CORNERSTONE_LABELS[role], None,
                              'offense', BUCKET_QUERY_FILTERS['offense'], self._slot_target('offense', top=True),
                              CORNERSTONE_WINDOWS)
        return _RoundSpec('cornerstone', role, CORNERSTONE_LABELS[role], 'RP',
                          'bullpen', {'player_type': ['PITCHER'], 'positions': ['CLOSER']},
                          self._slot_target('bullpen', top=True), CORNERSTONE_WINDOWS,
                          # Some sets tag few true closers — fall back to any reliever.
                          fallback_filters=BUCKET_QUERY_FILTERS['bullpen'])

    def _fill_spec(self) -> _RoundSpec:
        slots = self._open_fill_slots()
        slot = random.choice(slots) if self.order == 'random' else slots[0]
        return self._fill_spec_for(slot)

    def _open_fill_slots(self) -> list[str]:
        """Every still-open roster slot, one entry per slot, in linear draft order: lineup
        (scarcest first), rotation, bullpen, bench. Repeats are intentional — a random pick
        from this list is weighted by how many slots each need still has open."""
        slots = [p for p in FILL_POSITION_ORDER if p not in self.field_filled]
        # Starters are re-ordered by points server-side on save, so the first open role is as
        # good as any — repeat it once per open starter.
        slots += [self._first_open_rotation_role()] * self._open_rotation_count()
        slots += ['RP'] * max(0, self.bullpen_target - self.bullpen_count)
        slots += ['BE'] * max(0, self.bench_target - self.bench_count)
        # Past both effective targets (a manual pick overfilled one bucket) the last slots are
        # drafter's-choice slack — offer bullpen arms.
        return slots or ['RP']

    def _fill_spec_for(self, slot: str) -> _RoundSpec:
        # Lineup and bench slots draw a random remaining tier (stars and bargains land anywhere);
        # rotation and bullpen take the top remaining tier, so they fill in descending order.
        if slot in OFFENSE_POSITIONS:
            filters = BUCKET_QUERY_FILTERS['offense'] if slot == 'DH' \
                else {'player_type': ['HITTER'], 'positions': [_FIELD_POSITION_FILTER[slot]]}
            return self._fill(slot, 'field', 'offense', filters, self._slot_target('offense', top=False))

        if slot in ROTATION_ROLES:
            return self._fill(slot, 'rotation', 'rotation', BUCKET_QUERY_FILTERS['rotation'],
                              self._slot_target('rotation', top=True), label=f'Starting Pitcher ({slot})')

        if slot == 'RP':
            return self._fill('RP', 'bullpen', 'bullpen', BUCKET_QUERY_FILTERS['bullpen'],
                              self._slot_target('bullpen', top=True))

        return self._fill('BE', 'bench', 'bench', BUCKET_QUERY_FILTERS['bench'], self._slot_target('bench', top=False))

    def _fill(self, position: str, role: str, bucket: str, filters: dict, target_points: int, label: str | None = None) -> _RoundSpec:
        return _RoundSpec('fill', role, label or _POSITION_LABELS.get(position, position), position,
                          bucket, filters, target_points, FILL_WINDOWS)

    # ------------------------------------------------------------------
    # Budget
    # ------------------------------------------------------------------

    def _slot_target(self, bucket: str, top: bool) -> int:
        """Raw-PTS target for the next pick from `bucket`, shaped like a real roster's spend.

        The bucket's spend shape (one tier per slot) is laid over its picks so far: each existing
        pick claims the tier nearest its actual price, and this round prices off one of the tiers
        left — the top one, or a random one (seeded per team + round, so re-asking for the same
        round gives the same target). Targets are a share of the bucket's *remaining* budget, so
        the bucket still lands on its total however earlier picks over- or under-shot.
        """
        filled = self._filled_costs(bucket)
        n_total = len(filled) + self._open_count(bucket)
        tiers = sorted(self._spend_shape(bucket, n_total), reverse=True)
        avg = self.pts_limit * GUIDED_PTS_DISTRIBUTION[bucket] / n_total
        for cost in filled:
            if len(tiers) <= 1:
                break
            ratio = cost / avg if avg > 0 else 0
            tiers.remove(min(tiers, key=lambda t: abs(t - ratio)))
        tier = tiers[0] if top else self._rng.choice(tiers)
        target = self._bucket_remaining(bucket) * tier / sum(tiers)
        # Bench PTS count against the budget at the multiplier, so the raw card target scales up.
        if bucket == 'bench':
            target /= self.team.bench_pts_multiplier or 1.0
        return self._clamp(target, bucket)

    @staticmethod
    def _spend_shape(bucket: str, n: int) -> list[float]:
        """`n` per-slot spend weights for `bucket` (mean 1.0, summing to `n`)."""
        if n <= 1:
            return [1.0]
        if bucket == 'bullpen':
            return _bullpen_slot_weights(n, with_closer=True)
        hi, lo = _SPEND_SHAPES[bucket]
        ramp = [hi - (hi - lo) * i / (n - 1) for i in range(n)]
        scale = n / sum(ramp)
        return [w * scale for w in ramp]

    def _filled_costs(self, bucket: str) -> list[float]:
        """Budget cost of each pick already in `bucket` (bench at the bench multiplier)."""
        positions = {
            'offense': set(OFFENSE_POSITIONS),
            'rotation': set(ROTATION_ROLES),
            'bullpen': set(BULLPEN_ROLES),
            'bench': {'BE'},
        }[bucket]
        mult = self.team.bench_pts_multiplier if bucket == 'bench' else 1.0
        return [
            (self.existing_card_points.get(s.card_id) or 0) * mult
            for s in self.team.roster if s.roster_position in positions
        ]

    def _open_count(self, bucket: str) -> int:
        """Open slots left in `bucket` — at least 1, since a round is being priced from it."""
        return max(1, self._raw_open_count(bucket))

    def _raw_open_count(self, bucket: str) -> int:
        return max(0, {
            'offense': len(OFFENSE_POSITIONS) - len(self.field_filled),
            'rotation': self._open_rotation_count(),
            'bullpen': self.bullpen_target - self.bullpen_count,
            'bench': self.bench_target - self.bench_count,
        }[bucket])

    def _bucket_remaining(self, bucket: str) -> float:
        """Budget `bucket` still has to spend, rebalanced so the open buckets together always
        account for exactly the team's remaining budget.

        Each bucket's nominal remaining is its share of the budget minus what it has spent. A
        bucket that finished under (or over) its share would otherwise strand that difference —
        e.g. a lineup that came in 300 PTS cheap leaves 300 PTS unspent forever. Scaling the
        still-open buckets' nominal remaining to the global remaining hands that slack to the
        rest of the draft, and on the last open slot targets exactly what's left."""
        def nominal(b: str) -> float:
            return max(0.0, self.pts_limit * GUIDED_PTS_DISTRIBUTION[b] - self.spent_by_bucket[b])

        # The bucket being priced always counts, even past its target (overflow 'RP' slack).
        open_buckets = [b for b in GUIDED_PTS_DISTRIBUTION if b == bucket or self._raw_open_count(b) > 0]
        global_remaining = max(0.0, self.pts_limit - sum(self.spent_by_bucket.values()))
        total_nominal = sum(nominal(b) for b in open_buckets)
        if total_nominal <= 0:
            # Every open bucket has already spent its share: split what's left by share instead.
            total_share = sum(GUIDED_PTS_DISTRIBUTION[b] for b in open_buckets)
            return global_remaining * GUIDED_PTS_DISTRIBUTION[bucket] / total_share
        return global_remaining * nominal(bucket) / total_nominal

    def _clamp(self, target: float, bucket: str) -> int:
        return int(max(MIN_CARD_POINTS, min(target, self._max_points(bucket))))

    def _max_points(self, bucket: str) -> float:
        """Most raw PTS a pick from `bucket` can cost while still leaving MIN_CARD_POINTS for
        every other open slot (bench slots reserve at the bench multiplier) — same rule as the
        draft panel's "Fits my roster" cap."""
        mult = self.team.bench_pts_multiplier
        spent_total = sum(self.spent_by_bucket.values())
        open_total = self.team.roster_size - len(self.team.roster)
        open_bench = max(0, self.bench_target - self.bench_count)
        other_bench = max(0, open_bench - (1 if bucket == 'bench' else 0))
        other_non_bench = max(0, open_total - open_bench - (0 if bucket == 'bench' else 1))
        cap_budget = self.pts_limit - spent_total - other_non_bench * MIN_CARD_POINTS - other_bench * MIN_CARD_POINTS * mult
        return cap_budget / mult if bucket == 'bench' and mult > 0 else cap_budget

    def _open_rotation_count(self) -> int:
        return max(0, self.team.num_starters - len(self.rotation_filled))

    def _first_open_rotation_role(self) -> str | None:
        return next((r for r in ROTATION_ROLES[:self.team.num_starters] if r not in self.rotation_filled), None)

    # ------------------------------------------------------------------
    # Options
    # ------------------------------------------------------------------

    def _sample_options(self, db, spec: _RoundSpec) -> tuple[list[dict], int]:
        """Widen the price window until OPTION_COUNT eligible cards turn up (or the widest window
        is exhausted, in which case whatever was found is offered)."""
        best: list[dict] = []
        best_window = spec.windows[0]
        # Never offer a card that would blow the budget, however wide the window gets — unless
        # nothing is affordable at all, in which case the cheapest band is still shown.
        max_points = max(MIN_CARD_POINTS, int(self._max_points(spec.bucket)))
        for filters in filter(None, (spec.query_filters, spec.fallback_filters)):
            for window in spec.windows:
                lo = max(MIN_CARD_POINTS, spec.target_points - window)
                hi = min(spec.target_points + window, max_points)
                pool = fetch_stratified_candidates(
                    db, filters, self.active_filters, self.card_sources, self.sets_by_source,
                    bands=[(lo, hi, self.SAMPLE_PER_BAND)], columns=None, user_id=self.user_id,
                )
                options = self._pick_options(pool, spec)
                if len(options) > len(best):
                    best, best_window = options, window
                if len(best) >= self.OPTION_COUNT:
                    return best, best_window

        # Nothing priced near the target: offer whatever affordable cards come closest to it,
        # reporting the window as how far the furthest option landed from the target.
        for filters in filter(None, (spec.query_filters, spec.fallback_filters)):
            pool = fetch_stratified_candidates(
                db, filters, self.active_filters, self.card_sources, self.sets_by_source,
                bands=[(MIN_CARD_POINTS, max_points, self.SAMPLE_FALLBACK)], columns=None, user_id=self.user_id,
            )
            options = self._pick_options(pool, spec, closest_to=spec.target_points)
            if len(options) > len(best):
                best = options
                best_window = max(abs((o['card'].get('points') or 0) - spec.target_points) for o in options)
            if len(best) >= self.OPTION_COUNT:
                break
        return best, best_window

    def _pick_options(self, pool: list[dict], spec: _RoundSpec, closest_to: int | None = None) -> list[dict]:
        candidates = []
        seen_players: set[str] = set()
        random.shuffle(pool)
        if closest_to is not None:
            pool.sort(key=lambda c: abs((c.get('points') or 0) - closest_to))
        elif spec.role != 'bench':
            # Full-sample seasons first (bench is exempt, same as autofill), small samples only as filler.
            pool.sort(key=_is_small_sample)
        for card in pool:
            if card['card_id'] in self.drafted_ids:
                continue
            slot = self._slot_for(card, spec)
            if slot is None:
                continue
            # One card per player per round, so the options are real alternatives.
            player_key = str(card.get('bref_id') or card.get('mlb_id') or card.get('name') or card['card_id'])
            if player_key in seen_players:
                continue
            seen_players.add(player_key)
            candidates.append({'card': card, 'roster_position': slot})
            if len(candidates) >= self.OPTION_COUNT:
                break
        return sorted(candidates, key=lambda o: o['card'].get('points') or 0, reverse=True)

    def _slot_for(self, card: dict, spec: _RoundSpec) -> str | None:
        """Roster slot an option would be drafted into, or None if it can't fill this round."""
        if spec.role == 'star':
            # The star lands at the first open field position it can play, falling back to DH.
            for pos in card.get('positions_list') or []:
                for slot in (('LF', 'RF') if pos == 'LF/RF' else (pos,)):
                    if slot in OFFENSE_POSITIONS and slot != 'DH' and slot not in self.field_filled:
                        return slot
            return 'DH' if 'DH' not in self.field_filled else None
        if spec.role == 'field' and not _pos_matches(card, spec.position):
            return None
        return spec.position

