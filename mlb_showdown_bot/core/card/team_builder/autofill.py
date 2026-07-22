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
    'bullpen':  {'player_type': ['PITCHER'], 'positions': ['RELIEVER', 'STARTER']},
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

# Fraction of the sorted pool to randomly sample from when a strategy is set
_STRATEGY_TIER_FRACTION = 0.4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ob_score(card: dict) -> float:
    cv = card.get('chart_values') or {}
    return sum(cv.get(k, 0) or 0 for k in ('BB', '1B', '2B', '3B', 'HR'))


def _sort_candidates(candidates: list[dict], strategy: str | None, is_pitcher: bool) -> list[dict]:
    """Sort by strategy metric with tier-based sampling, or pure shuffle if balanced."""
    sort_map = PITCHING_SORT if is_pitcher else HITTING_SORT
    config = sort_map.get(strategy or '', (None, None))
    sort_key, direction = config

    if sort_key is None and strategy != 'high_ob':
        shuffled = candidates[:]
        random.shuffle(shuffled)
        return shuffled

    if strategy == 'high_ob':
        sorted_candidates = sorted(candidates, key=_ob_score, reverse=True)
    else:
        reverse = direction == 'desc'
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (c.get(sort_key) is not None, c.get(sort_key) or 0),
            reverse=reverse,
        )

    tier_size = max(1, int(len(sorted_candidates) * _STRATEGY_TIER_FRACTION))
    top = sorted_candidates[:tier_size]
    rest = sorted_candidates[tier_size:]
    random.shuffle(top)
    random.shuffle(rest)
    return top + rest


def _existing_card_ids(team: Team) -> set[str]:
    ids: set[str] = set()
    for slot in team.roster:
        ids.add(slot.card_id)
    for pa in team.rotation:
        ids.add(pa.card_id)
    return ids


def _pos_matches(card: dict, position: str) -> bool:
    """Check whether a hitter card can play the given field position."""
    pos_list = card.get('positions_list') or []
    if position in ('LF', 'RF'):
        return 'LF/RF' in pos_list or position in pos_list
    if position == 'DH':
        return True  # any hitter can DH
    return position in pos_list


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
) -> tuple[_BucketResult | None, set[str]]:
    """Returns (result, picked_ids). picked_ids so bench can exclude them."""
    open_positions = [p for p in OFFENSE_POSITIONS if p not in filled_positions]
    if not open_positions:
        return _BucketResult(), set()

    result = _BucketResult()
    used_ids: set[str] = set()
    pts_remaining = pts_target
    n_open = len(open_positions)

    for i, position in enumerate(open_positions):
        slots_left = n_open - i
        target_per_slot = pts_remaining / slots_left

        eligible = [
            c for c in candidates
            if c['card_id'] not in used_ids and _pos_matches(c, position)
        ]
        if not eligible:
            print(f"No eligible candidates for position {position} with {pts_remaining} pts remaining")
            return None, set()

        affordable = [c for c in eligible if (c.get('points') or 0) <= pts_remaining]
        if not affordable:
            print(f"No affordable candidates for position {position} with {pts_remaining} pts remaining")
            return None, set()

        picked = min(affordable, key=lambda c: abs((c.get('points') or 0) - target_per_slot))

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
) -> _BucketResult | None:
    open_count = max(0, min_bench - bench_count)
    if open_count == 0:
        return _BucketResult()

    result = _BucketResult()
    pts_remaining = pts_target
    used_ids: set[str] = exclude_ids.copy()

    for i in range(open_count):
        slots_left = open_count - i
        target_per_slot = pts_remaining / slots_left

        eligible = [c for c in candidates if c['card_id'] not in used_ids]
        affordable = [
            c for c in eligible
            if round((c.get('points') or 0) * bench_pts_multiplier) <= pts_remaining
        ]
        if not affordable:
            print(f"No affordable candidates for bench with {pts_remaining} pts remaining")
            return None

        picked = min(
            affordable,
            key=lambda c: abs(round((c.get('points') or 0) * bench_pts_multiplier) - target_per_slot),
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
) -> _BucketResult | None:
    all_roles = [f'SP{i}' for i in range(1, num_starters + 1)]
    open_roles = [r for r in all_roles if r not in filled_roles]
    if not open_roles:
        return _BucketResult()

    result = _BucketResult()
    pts_remaining = pts_target
    used_ids: set[str] = set()
    n_open = len(open_roles)

    # Pick starters without assigning roles yet
    picked_cards: list[dict] = []
    for i in range(n_open):
        slots_left = n_open - i
        target_per_slot = pts_remaining / slots_left

        eligible = [c for c in candidates if c['card_id'] not in used_ids]
        affordable = [c for c in eligible if (c.get('points') or 0) <= pts_remaining]
        if not affordable:
            return None

        picked = min(affordable, key=lambda c: abs((c.get('points') or 0) - target_per_slot))

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
    filled_roles: set[str],
    min_bullpen: int,
    pts_target: int,
    pts_tolerance: int,
) -> _BucketResult | None:
    # Roles: one CL + remaining as RP
    all_roles = ['CL'] + ['RP'] * (min_bullpen - 1)
    # Count already-filled bullpen slots
    already_filled = sum(
        1 for r in filled_roles if r in ('CL', 'RP') or r.startswith('RP')
    )
    open_count = max(0, min_bullpen - already_filled)
    if open_count == 0:
        return _BucketResult()

    roles_to_fill = all_roles[:open_count]

    result = _BucketResult()
    pts_remaining = pts_target
    used_ids: set[str] = set()
    n_open = len(roles_to_fill)

    for i, role in enumerate(roles_to_fill):
        slots_left = n_open - i
        target_per_slot = pts_remaining / slots_left

        eligible = [c for c in candidates if c['card_id'] not in used_ids]
        affordable = [c for c in eligible if (c.get('points') or 0) <= pts_remaining]
        if not affordable:
            return None

        picked = min(affordable, key=lambda c: abs((c.get('points') or 0) - target_per_slot))

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


def autofill_team(
    team: Team,
    candidates_by_bucket: dict[str, list[dict]],
    pts_distribution: dict[str, float],
    pitching_strategy: str | None,
    hitting_strategy: str | None,
    pts_tolerance: int = 200,
    max_attempts: int = 2,
    pts_target: int | None = None,
) -> dict | None:
    """
    Fill remaining roster slots using a randomized greedy algorithm.
    Returns merged roster/lineups/rotation dict on success, or None on failure.

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
    filled_bullpen_roles  = {p.role for p in team.rotation if not p.role.startswith('SP')}
    bench_count = sum(1 for s in team.roster if s.roster_position == 'BE')

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

    for _ in range(max_attempts):
        # Fresh sort/shuffle each attempt
        sorted_candidates: dict[str, list[dict]] = {}
        for bucket, raw in candidates_by_bucket.items():
            is_pitcher = bucket in ('rotation', 'bullpen')
            strategy = pitching_strategy if is_pitcher else hitting_strategy
            pool = [c for c in raw if c['card_id'] not in existing_ids]
            sorted_candidates[bucket] = _sort_candidates(pool, strategy, is_pitcher)

        offense_result, offense_ids = _fill_offense(
            sorted_candidates['offense'], filled_lineup_pos,
            offense_target, pts_tolerance,
        )
        if offense_result is None:
            print("Offense fill failed, retrying...")
            continue

        bench_result = _fill_bench(
            sorted_candidates['bench'],
            existing_ids | offense_ids,  # exclude all cards already picked
            bench_count, team.min_bench,
            bench_target, pts_tolerance,
            team.bench_pts_multiplier,
        )
        if bench_result is None:
            print("Bench fill failed, retrying...")
            continue

        rotation_result = _fill_rotation(
            sorted_candidates['rotation'], filled_rotation_roles,
            team.num_starters, rotation_target, pts_tolerance,
        )
        if rotation_result is None:
            print("Rotation fill failed, retrying...")
            continue

        bullpen_result = _fill_bullpen(
            sorted_candidates['bullpen'], filled_bullpen_roles,
            team.min_bullpen, bullpen_target, pts_tolerance,
        )
        if bullpen_result is None:
            print("Bullpen fill failed, retrying...")
            continue

        # Build merged roster
        new_roster = [s.model_dump() for s in team.roster]
        for slot in (
            offense_result.roster_slots
            + bench_result.roster_slots
            + rotation_result.roster_slots
            + bullpen_result.roster_slots
        ):
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

    return None
