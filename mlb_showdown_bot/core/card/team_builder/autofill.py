import random
from dataclasses import dataclass, field

from .team import Team, TeamRosterSlot, CardSource, PickSource, derive_lineups_rotation

# ---------------------------------------------------------------------------
# Bucket definitions
# ---------------------------------------------------------------------------

# Ordered lineup field positions to fill (one slot each)
OFFENSE_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH']

# DB query filters per bucket
BUCKET_QUERY_FILTERS: dict[str, dict] = {
    'offense': {'player_type': ['HITTER'], 'positions': ['C', '1B', '2B', '3B', 'SS', 'LF/RF', 'CF', 'DH']},
    'rotation': {'player_type': ['PITCHER'], 'positions': ['STARTER']},
    'bench':    {'player_type': ['HITTER']},
    'bullpen':  {'player_type': ['PITCHER'], 'positions': ['RELIEVER']},
}

# ---------------------------------------------------------------------------
# Strategy sort config
# ---------------------------------------------------------------------------

PITCHING_SORT: dict[str, tuple[str | None, str | None]] = {
    'high_control': ('command', 'desc'),
    'groundball':   ('chart_values_GB', 'desc'),
    'no_doubles':   ('chart_values_2B', 'asc'),
    'strikeout':    ('chart_values_SO', 'desc'),
}

HITTING_SORT: dict[str, tuple[str | None, str | None]] = {
    'high_ob': (None, None),  # computed post-fetch
    'speed':   ('speed', 'desc'),
    'slug':    ('real_slugging_perc', 'desc'),
    'contact': ('real_batting_avg', 'desc'),
}

DEFENSE_SORT: dict[str, tuple[str | None, str | None]] = {
    'low_defense':     ('defense', 'asc'),
    'medium_defense':  ('defense', 'desc'),
    'high_defense':    ('defense', 'desc'),
    'elite_defense':   ('defense', 'desc'),
}

CATCHER_DEFENSE_SORT: dict[str, tuple[str | None, str | None]] = {
    'low_catcher_defense':     ('defense', 'asc'),
    'medium_catcher_defense':  ('defense', 'desc'),
    'high_catcher_defense':    ('defense', 'desc'),
    'elite_catcher_defense':   ('defense', 'desc'),
}

# Fraction of the sorted pool to randomly sample from when a strategy is set
_STRATEGY_TIER_FRACTION = 0.4

# Gamma shape used to randomize per-slot spend targets within a bucket, so a fill doesn't
# draft every slot at ~the same point value. Mean weight is always 1.0 (normalized); lower
# shape = more spread (a stud pick offset by a bargain pick), higher = closer to uniform.
_VARIETY_SHAPE = 3.5
# Weights are clipped to this multiple of the mean before a final renormalize, so a long
# gamma tail can't starve a later slot below what any candidate could plausibly cost.
_VARIETY_WEIGHT_BOUNDS = (0.55, 1.7)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slot_weights(n: int, max_weight: float | None = None) -> list[float]:
    """Randomized per-slot spend weights, mean 1.0, summing to `n`, bounded to `max_weight`
    (defaults to `_VARIETY_WEIGHT_BOUNDS`). Clipping is applied twice: a single clip-then-
    renormalize pass can push values back outside the bound (renormalizing to restore the
    sum-to-`n` invariant scales every value, including ones already at the clip edge), so a
    second pass tightens that back down. Two passes converge well enough in practice.

    The lower bound tightens in lockstep, mirrored around 1.0, whenever `max_weight` squeezes
    the ceiling below the default — e.g. a bucket whose average target already sits close to
    the pool's max price (a thin rotation pool). Without that, a "bargain" slot could still
    undershoot by the full default margin while the compensating slot has almost no headroom
    left to make up the difference, since it's capped near the ceiling — an imbalance that's
    unrecoverable, not just off-target.
    """
    if n <= 1:
        return [1.0] * max(n, 0)
    default_lo, default_hi = _VARIETY_WEIGHT_BOUNDS
    hi = max(default_lo, default_hi if max_weight is None else max_weight)
    lo = max(default_lo, 2 - hi)
    weights = [random.gammavariate(_VARIETY_SHAPE, 1.0) for _ in range(n)]
    for _ in range(2):
        total = sum(weights) or 1.0
        weights = [max(lo, min(hi, w / total * n)) for w in weights]
    total = sum(weights) or 1.0
    return [w / total * n for w in weights]


def _slot_plan(pts_target: float, n: int, candidates: list[dict], price_fn=None) -> tuple[list[float], float]:
    """Build the per-slot weight schedule for a bucket fill, plus a price ceiling.

    The ceiling is the price of the `n`-th priciest candidate, not the pool's true max — if
    several slots' weights land near the top simultaneously (expected with `n` draws), they'd
    all compete for the single most expensive card and cascade down to whatever's left,
    landing well short of target with nothing later able to recover the gap. Pricing the
    ceiling off the `n`-th candidate guarantees enough supply for every slot to plausibly
    reach it at once. Callers must still clamp each slot's *live* target to this ceiling —
    `_next_target` recomputes off the actual remaining budget as slots get picked, and small
    per-pick shortfalls (candidate granularity) can otherwise drift a later slot back over it.
    """
    price = price_fn or (lambda c: c.get('points') or 0)
    if n <= 0 or not candidates:
        return _slot_weights(n), float('inf')
    prices_desc = sorted((price(c) for c in candidates), reverse=True)
    ceiling_price = prices_desc[min(n, len(prices_desc)) - 1]
    if ceiling_price <= 0:
        return _slot_weights(n), float('inf')
    avg_target = pts_target / n
    ceiling = _VARIETY_WEIGHT_BOUNDS[1] if avg_target <= 0 else min(_VARIETY_WEIGHT_BOUNDS[1], ceiling_price / avg_target)
    return _slot_weights(n, ceiling), ceiling_price


def _next_target(pts_remaining: float, weights: list[float], i: int) -> float:
    """Target spend for slot `i`, proportional to its weight among remaining slots so the
    bucket still totals `pts_remaining` even as variety pulls individual slots off-average."""
    remaining_weight = sum(weights[i:])
    if remaining_weight <= 0:
        return pts_remaining / max(1, len(weights) - i)
    return pts_remaining * weights[i] / remaining_weight


def _ob_score(card: dict) -> float:
    cv = card.get('chart_values') or {}
    return sum(cv.get(k, 0) or 0 for k in ('BB', '1B', '2B', '3B', 'HR'))


def _strategy_rank(group: list[dict], strategy: str | None, is_pitcher: bool) -> dict[str, float]:
    """Rank-normalize `group` by `strategy`'s metric: 1.0 = best fit, 0.0 = worst. Returns {}
    for an unset/unrecognized strategy (e.g. 'balanced'), letting callers treat it as neutral."""
    if not strategy or not group:
        return {}

    if strategy in DEFENSE_SORT:
        sort_map = DEFENSE_SORT
    elif strategy in CATCHER_DEFENSE_SORT:
        sort_map = CATCHER_DEFENSE_SORT
    else:
        sort_map = PITCHING_SORT if is_pitcher else HITTING_SORT
    sort_key, direction = sort_map.get(strategy, (None, None))

    if strategy == 'high_ob':
        ordered = sorted(group, key=_ob_score, reverse=True)
    elif sort_key is None:
        return {}
    else:
        reverse = direction == 'desc'
        ordered = sorted(
            group,
            key=lambda c: (c.get(sort_key) is not None, c.get(sort_key) or 0),
            reverse=reverse,
        )

    n = len(ordered)
    if n <= 1:
        return {c['card_id']: 1.0 for c in ordered}
    return {c['card_id']: 1.0 - i / (n - 1) for i, c in enumerate(ordered)}


def _sort_candidates(
    candidates: list[dict],
    is_pitcher: bool,
    pitching_strategy: str | None = None,
    hitting_strategy: str | None = None,
    defense_strategy: str | None = None,
    catcher_defense_strategy: str | None = None,
) -> list[dict]:
    """Sort by a rank-blend of every strategy set at once, with tier-based sampling, or pure
    shuffle if none apply. A hitting strategy and a defense strategy set together both shape
    the sort (via averaged rank) rather than one silently discarding the other. For position
    players, catchers use catcher_defense_strategy (falling back to defense_strategy) in place
    of defense_strategy, still blended with hitting_strategy."""
    if is_pitcher:
        groups: list[tuple[list[dict], list[str]]] = [
            (candidates, [pitching_strategy] if pitching_strategy else []),
        ]
    else:
        catchers = [c for c in candidates if 'C' in (c.get('positions_list') or [])]
        non_catchers = [c for c in candidates if 'C' not in (c.get('positions_list') or [])]
        catcher_def = catcher_defense_strategy or defense_strategy
        groups = [
            (catchers, [s for s in (catcher_def, hitting_strategy) if s]),
            (non_catchers, [s for s in (defense_strategy, hitting_strategy) if s]),
        ]

    sorted_candidates = []
    for group, strategies in groups:
        if not group:
            continue

        ranks = [r for r in (_strategy_rank(group, s, is_pitcher) for s in strategies) if r]
        if not ranks:
            shuffled = group[:]
            random.shuffle(shuffled)
            sorted_candidates.extend(shuffled)
            continue

        def combined_score(c: dict, ranks=ranks) -> float:
            return sum(r.get(c['card_id'], 0.5) for r in ranks) / len(ranks)

        group_sorted = sorted(group, key=combined_score, reverse=True)
        tier_size = max(1, int(len(group_sorted) * _STRATEGY_TIER_FRACTION))
        top = group_sorted[:tier_size]
        rest = group_sorted[tier_size:]
        random.shuffle(top)
        random.shuffle(rest)
        sorted_candidates.extend(top + rest)

    return sorted_candidates


def _existing_card_ids(team: Team) -> set[str]:
    ids: set[str] = set()
    for slot in team.roster:
        ids.add(slot.card_id)
    for pa in team.rotation:
        ids.add(pa.card_id)
    return ids


def _existing_source_counts(team: Team) -> dict[str, int]:
    """Seed source-balance counts from cards already on the team (manual picks count too)."""
    counts: dict[str, int] = {}
    for slot in team.roster:
        counts[slot.card_source.value] = counts.get(slot.card_source.value, 0) + 1
    for pa in team.rotation:
        counts[pa.card_source.value] = counts.get(pa.card_source.value, 0) + 1
    return counts


def _pick_balanced(candidates: list[dict], closeness_key, source_counts: dict[str, int] | None) -> dict:
    """Pick the candidate closest to the per-slot points target (per `closeness_key`),
    preferring whichever card source is currently least represented on the team so autofill
    doesn't lean entirely on one source just because it happens to have denser coverage near
    the target points."""
    if source_counts:
        sources_here = {c.get('_card_source', 'BOT').upper() for c in candidates}
        if len(sources_here) > 1:
            least = min(source_counts.get(s, 0) for s in sources_here)
            preferred_sources = {s for s in sources_here if source_counts.get(s, 0) == least}
            preferred = [c for c in candidates if c.get('_card_source', 'BOT').upper() in preferred_sources]
            if preferred:
                candidates = preferred

    picked = min(candidates, key=closeness_key)
    if source_counts is not None:
        src = picked.get('_card_source', 'BOT').upper()
        source_counts[src] = source_counts.get(src, 0) + 1
    return picked


def _pos_matches(card: dict, position: str) -> bool:
    """Check whether a hitter card can play the given field position."""
    pos_list = card.get('positions_list') or []
    if position in ('LF', 'RF'):
        return 'LF/RF' in pos_list or position in pos_list
    if position == 'DH':
        return True  # any hitter can DH
    return position in pos_list


def _diagnose_bucket_failure(
    bucket: str,
    candidates: list[dict],
    used_ids: set[str],
    pts_remaining: int,
    bench_pts_multiplier: float = 1.0,
) -> str:
    """Diagnose why a bucket couldn't be filled and return a detailed error message."""
    available = [c for c in candidates if c['card_id'] not in used_ids]
    if not available:
        return f"No {bucket} players available in candidate pool"

    # Apply multiplier for bench bucket
    price_fn = (lambda c: round((c.get('points') or 0) * bench_pts_multiplier)) if bucket == 'bench' else (lambda c: c.get('points') or 0)
    prices = [price_fn(c) for c in available]
    cheapest = min(prices)

    if cheapest > pts_remaining:
        return f"Cheapest available {bucket} player costs {cheapest} pts, but only {pts_remaining} pts remaining in budget"
    else:
        return f"Unable to complete {bucket} fill within tolerance (budget constraints)"


# ---------------------------------------------------------------------------
# Per-bucket fill functions
# ---------------------------------------------------------------------------

@dataclass
class _BucketResult:
    # Only the roster is accumulated — lineups and rotation are derived from it.
    roster_slots: list[TeamRosterSlot] = field(default_factory=list)
    pts_used: int = 0


def _card_source(card: dict) -> CardSource:
    """Derive CardSource from the _card_source tag set by the fetch layer."""
    raw = (card.get('_card_source') or 'BOT').upper()
    try:
        return CardSource(raw)
    except ValueError:
        return CardSource.BOT


def _fill_offense(
    candidates: list[dict],
    filled_positions: set[str],
    pts_target: int,
    pts_tolerance: int,
    source_counts: dict[str, int] | None = None,
) -> tuple[_BucketResult | None, set[str]]:
    """Returns (result, picked_ids). picked_ids so bench can exclude them."""
    open_positions = [p for p in OFFENSE_POSITIONS if p not in filled_positions]
    if not open_positions:
        return _BucketResult(), set()

    result = _BucketResult()
    used_ids: set[str] = set()
    pts_remaining = pts_target
    n_open = len(open_positions)
    weights, max_price = _slot_plan(pts_target, n_open, candidates)

    for i, position in enumerate(open_positions):
        target_per_slot = min(_next_target(pts_remaining, weights, i), max_price)

        eligible = [
            c for c in candidates
            if c['card_id'] not in used_ids and _pos_matches(c, position)
        ]
        if not eligible:
            return None, set()

        affordable = [c for c in eligible if (c.get('points') or 0) <= pts_remaining]
        if not affordable:
            return None, set()

        picked = _pick_balanced(
            affordable,
            lambda c: abs((c.get('points') or 0) - target_per_slot),
            source_counts,
        )

        card_id = picked['card_id']
        pts = picked.get('points') or 0
        src = _card_source(picked)
        used_ids.add(card_id)
        pts_remaining -= pts
        result.pts_used += pts

        result.roster_slots.append(TeamRosterSlot(
            card_id=card_id, card_source=src, roster_position=position,
            pick_source=PickSource.AUTOFILL,
        ))

    if abs(result.pts_used - pts_target) > pts_tolerance:
        return None, set()

    return result, used_ids


def _fill_bench(
    candidates: list[dict],
    exclude_ids: set[str],
    bench_count: int,
    min_bench: int,
    pts_target: int,
    pts_tolerance: int,
    bench_pts_multiplier: float,
    source_counts: dict[str, int] | None = None,
) -> _BucketResult | None:
    open_count = max(0, min_bench - bench_count)
    if open_count == 0:
        return _BucketResult()

    result = _BucketResult()
    pts_remaining = pts_target
    used_ids: set[str] = exclude_ids.copy()
    bench_price = lambda c: round((c.get('points') or 0) * bench_pts_multiplier)
    weights, max_price = _slot_plan(pts_target, open_count, candidates, bench_price)

    for i in range(open_count):
        target_per_slot = min(_next_target(pts_remaining, weights, i), max_price)

        eligible = [c for c in candidates if c['card_id'] not in used_ids]
        affordable = [
            c for c in eligible
            if round((c.get('points') or 0) * bench_pts_multiplier) <= pts_remaining
        ]
        if not affordable:
            print(f"No affordable candidates for bench with {pts_remaining} pts remaining")
            return None

        picked = _pick_balanced(
            affordable,
            lambda c: abs(round((c.get('points') or 0) * bench_pts_multiplier) - target_per_slot),
            source_counts,
        )

        card_id = picked['card_id']
        pts = picked.get('points') or 0
        used_ids.add(card_id)
        effective_pts = round(pts * bench_pts_multiplier)
        pts_remaining -= effective_pts
        result.pts_used += effective_pts

        result.roster_slots.append(TeamRosterSlot(
            card_id=card_id, card_source=_card_source(picked), roster_position='BE',
            pick_source=PickSource.AUTOFILL,
        ))

    if abs(result.pts_used - pts_target) > pts_tolerance:
        return None
    return result


def _fill_rotation(
    candidates: list[dict],
    filled_roles: set[str],
    num_starters: int,
    pts_target: int,
    pts_tolerance: int,
    source_counts: dict[str, int] | None = None,
) -> _BucketResult | None:
    all_roles = [f'SP{i}' for i in range(1, num_starters + 1)]
    open_roles = [r for r in all_roles if r not in filled_roles]
    if not open_roles:
        return _BucketResult()

    result = _BucketResult()
    pts_remaining = pts_target
    used_ids: set[str] = set()
    n_open = len(open_roles)
    weights, max_price = _slot_plan(pts_target, n_open, candidates)

    # Pick starters without assigning roles yet
    picked_cards: list[dict] = []
    for i in range(n_open):
        target_per_slot = min(_next_target(pts_remaining, weights, i), max_price)

        eligible = [c for c in candidates if c['card_id'] not in used_ids]
        affordable = [c for c in eligible if (c.get('points') or 0) <= pts_remaining]
        if not affordable:
            return None

        picked = _pick_balanced(
            affordable,
            lambda c: abs((c.get('points') or 0) - target_per_slot),
            source_counts,
        )

        used_ids.add(picked['card_id'])
        pts_remaining -= picked.get('points') or 0
        result.pts_used += picked.get('points') or 0
        picked_cards.append(picked)

    if abs(result.pts_used - pts_target) > pts_tolerance:
        return None

    # Assign SP1, SP2, … in descending points order (best arm gets the top spot)
    picked_cards.sort(key=lambda c: c.get('points') or 0, reverse=True)
    for card, role in zip(picked_cards, open_roles):
        card_id = card['card_id']
        src = _card_source(card)
        result.roster_slots.append(TeamRosterSlot(
            card_id=card_id, card_source=src, roster_position=role,
            pick_source=PickSource.AUTOFILL,
        ))

    return result


def _fill_bullpen(
    candidates: list[dict],
    already_filled: int,
    min_bullpen: int,
    pts_target: int,
    pts_tolerance: int,
    source_counts: dict[str, int] | None = None,
) -> _BucketResult | None:
    # The bullpen is drafted free-form now — no closer slot, every arm is a generic 'RP', so
    # the caller passes how many arms are already on the roster rather than a set of roles.
    all_roles = ['RP'] * min_bullpen
    open_count = max(0, min_bullpen - already_filled)
    if open_count == 0:
        return _BucketResult()

    roles_to_fill = all_roles[:open_count]

    result = _BucketResult()
    pts_remaining = pts_target
    used_ids: set[str] = set()
    n_open = len(roles_to_fill)
    weights, max_price = _slot_plan(pts_target, n_open, candidates)

    for i, role in enumerate(roles_to_fill):
        target_per_slot = min(_next_target(pts_remaining, weights, i), max_price)

        eligible = [c for c in candidates if c['card_id'] not in used_ids]
        affordable = [c for c in eligible if (c.get('points') or 0) <= pts_remaining]
        if not affordable:
            return None

        picked = _pick_balanced(
            affordable,
            lambda c: abs((c.get('points') or 0) - target_per_slot),
            source_counts,
        )

        card_id = picked['card_id']
        pts = picked.get('points') or 0
        src = _card_source(picked)
        used_ids.add(card_id)
        pts_remaining -= pts
        result.pts_used += pts

        result.roster_slots.append(TeamRosterSlot(
            card_id=card_id, card_source=src, roster_position=role,
            pick_source=PickSource.AUTOFILL,
        ))

    if abs(result.pts_used - pts_target) > pts_tolerance:
        return None
    return result


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def _existing_pts_by_bucket(team: Team, cardmap: dict[str, dict], bench_pts_multiplier: float) -> dict[str, int]:
    """Return points already spent per bucket by slots already on the team."""
    def pts(card_id: str) -> int:
        return cardmap.get(card_id, {}).get('points') or 0

    offense_pos = set(OFFENSE_POSITIONS)
    return {
        'offense':  sum(pts(s.card_id) for s in team.roster if s.roster_position in offense_pos),
        'bench':    sum(round(pts(s.card_id) * bench_pts_multiplier) for s in team.roster if s.roster_position == 'BE'),
        'rotation': sum(pts(p.card_id) for p in team.rotation if p.role.startswith('SP')),
        'bullpen':  sum(pts(p.card_id) for p in team.rotation if not p.role.startswith('SP')),
    }


def _split_extra_roster_slots(extra: int, min_bench: int, min_bullpen: int) -> tuple[int, int]:
    """Split roster slots beyond the fixed minimums (9 lineup + num_starters + min_bench +
    min_bullpen) between bench and bullpen, in the same ratio as their configured minimums —
    e.g. min_bullpen=4, min_bench=2 sends extras 2:1 in bullpen's favor. Falls back to an even
    split when both minimums are 0. Returns (bench_extra, bullpen_extra)."""
    if extra <= 0:
        return 0, 0
    total = min_bench + min_bullpen
    if total <= 0:
        bullpen_extra = extra // 2
        return extra - bullpen_extra, bullpen_extra
    bullpen_extra = min(extra, round(extra * min_bullpen / total))
    return extra - bullpen_extra, bullpen_extra


def autofill_team(
    team: Team,
    candidates_by_bucket: dict[str, list[dict]],
    pts_distribution: dict[str, float],
    pitching_strategy: str | None,
    hitting_strategy: str | None,
    defense_strategy: str | None = None,
    catcher_defense_strategy: str | None = None,
    pts_tolerance: int = 200,
    max_attempts: int = 8,
    pts_target: int | None = None,
) -> dict | tuple[None, str]:
    """
    Fill remaining roster slots using a randomized greedy algorithm.
    Returns merged roster/lineups/rotation dict on success, or (None, error_msg) on failure.

    candidates_by_bucket: {bucket_name: [card_dicts]} fetched by the endpoint
    pts_distribution: fractions summing to 1.0 keyed by bucket name
    pts_target: one-off budget to use when the team itself has no pts_limit set
    """
    pts_limit = team.pts_limit or pts_target or 0
    existing_ids = _existing_card_ids(team)

    filled_lineup_pos = set()
    if team.lineups:
        filled_lineup_pos = {s.field_position for s in team.lineups[0].slots}

    filled_rotation_roles = {p.role for p in team.rotation if p.role.startswith('SP')}
    filled_bullpen_count  = sum(1 for p in team.rotation if not p.role.startswith('SP'))
    bench_count = sum(1 for s in team.roster if s.roster_position == 'BE')

    # roster_size may allow more than the fixed minimums (9 lineup + num_starters + min_bench
    # + min_bullpen) — any slack gets distributed across bench/bullpen so autofill actually
    # fills the roster instead of stopping at the configured floor.
    base_min_roster = len(OFFENSE_POSITIONS) + team.num_starters + team.min_bench + team.min_bullpen
    extra_slots = max(0, team.roster_size - base_min_roster)
    bench_extra, bullpen_extra = _split_extra_roster_slots(extra_slots, team.min_bench, team.min_bullpen)
    effective_min_bench   = team.min_bench + bench_extra
    effective_min_bullpen = team.min_bullpen + bullpen_extra

    # Build a flat cardmap so we can look up points for existing picks
    cardmap: dict[str, dict] = {}
    for cards in candidates_by_bucket.values():
        for c in cards:
            cardmap[c['card_id']] = c

    existing_pts = _existing_pts_by_bucket(team, cardmap, team.bench_pts_multiplier)

    offense_target  = max(0, round(pts_limit * pts_distribution.get('offense',  0.50)) - existing_pts['offense'])
    rotation_target = max(0, round(pts_limit * pts_distribution.get('rotation', 0.27)) - existing_pts['rotation'])
    bullpen_target  = max(0, round(pts_limit * pts_distribution.get('bullpen',  0.18)) - existing_pts['bullpen'])
    bench_target    = max(0, round(pts_limit * pts_distribution.get('bench',    0.05)) - existing_pts['bench'])

    # Only worth balancing across sources if candidates were actually pulled from more than
    # one — a single-source pool (or team) just falls through to plain greedy picking.
    all_sources = {(c.get('_card_source') or 'BOT').upper() for c in cardmap.values()}
    track_balance = len(all_sources) > 1

    for _ in range(max_attempts):
        # Fresh sort/shuffle, and a fresh balance tally seeded from cards already on the
        # team, each attempt.
        source_counts = _existing_source_counts(team) if track_balance else None

        sorted_candidates: dict[str, list[dict]] = {}
        for bucket, raw in candidates_by_bucket.items():
            is_pitcher = bucket in ('rotation', 'bullpen')
            pool = [c for c in raw if c['card_id'] not in existing_ids]
            sorted_candidates[bucket] = _sort_candidates(
                pool, is_pitcher,
                pitching_strategy=pitching_strategy,
                hitting_strategy=hitting_strategy,
                defense_strategy=defense_strategy,
                catcher_defense_strategy=catcher_defense_strategy,
            )

        offense_result, offense_ids = _fill_offense(
            sorted_candidates['offense'], filled_lineup_pos,
            offense_target, pts_tolerance, source_counts,
        )
        if offense_result is None:
            last_failure = _diagnose_bucket_failure('lineup', sorted_candidates['offense'], set(), offense_target)
            continue

        bench_result = _fill_bench(
            sorted_candidates['bench'],
            existing_ids | offense_ids,  # exclude all cards already picked
            bench_count, effective_min_bench,
            bench_target, pts_tolerance,
            team.bench_pts_multiplier, source_counts,
        )
        if bench_result is None:
            last_failure = _diagnose_bucket_failure('bench', sorted_candidates['bench'], existing_ids | offense_ids, bench_target, team.bench_pts_multiplier)
            continue

        rotation_result = _fill_rotation(
            sorted_candidates['rotation'], filled_rotation_roles,
            team.num_starters, rotation_target, pts_tolerance, source_counts,
        )
        if rotation_result is None:
            last_failure = _diagnose_bucket_failure('rotation', sorted_candidates['rotation'], set(), rotation_target)
            continue

        bullpen_result = _fill_bullpen(
            sorted_candidates['bullpen'], filled_bullpen_count,
            effective_min_bullpen, bullpen_target, pts_tolerance, source_counts,
        )
        if bullpen_result is None:
            last_failure = _diagnose_bucket_failure('bullpen', sorted_candidates['bullpen'], set(), bullpen_target)
            continue

        # Build merged roster. Autofilled slots get a draft_order continuing from the team's
        # existing max, so they show up in the Draft History tab alongside manual picks.
        new_roster = [s.model_dump() for s in team.roster]
        next_draft_order = max([0, *(s.draft_order or 0 for s in team.roster)]) + 1
        for slot in (
            offense_result.roster_slots
            + bench_result.roster_slots
            + rotation_result.roster_slots
            + bullpen_result.roster_slots
        ):
            slot.draft_order = next_draft_order
            next_draft_order += 1
            new_roster.append(slot.model_dump())

        # Lineups and rotation both fall out of the merged roster, so derive rather than
        # assemble them in parallel. Any user-created lineups on the team are preserved.
        existing_lineups, new_rotation = derive_lineups_rotation(
            new_roster,
            [
                {'name': ln.name, 'slots': [s.model_dump() for s in ln.slots]}
                for ln in team.stored_lineups
            ],
        )

        return {
            'roster': new_roster,
            'lineups': existing_lineups,
            'rotation': new_rotation,
        }

    # All attempts exhausted
    last_failure = last_failure if 'last_failure' in locals() else 'Unable to complete roster after all attempts'
    return (None, f"{last_failure}. Try adjusting your points targets, strategy, or removing some manual picks.")
