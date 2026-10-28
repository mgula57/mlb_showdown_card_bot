import re

from pydantic import BaseModel

from ...shared.player_position import Position, PositionSlot, PositionSlotParent

_FIELDING_VALUE_RE = re.compile(r'^-?[0-9]+$')
# MATCHES challenge_generator.REQUIRED_PLAYERS_KEY (NOT IMPORTED - THAT MODULE IMPORTS THE DB LAYER)
REQUIRED_PLAYERS_KEY = 'required_players'
# Roster-level minimums on the lineup's summed infield (1B/2B/3B/SS) / outfield (LF/CF/RF)
# defense - the same totals the sim rolls double plays / extra bases against (see
# `simulation.team.Team`). Like `required_players`, they judge the whole roster rather than one
# card, so they're skipped by the per-card checks (here and in `PostgresDB.fetch_card_list`).
TEAM_DEFENSE_KEYS = {
    'min_team_defense_if': PositionSlotParent.INFIELD,
    'min_team_defense_of': PositionSlotParent.OUTFIELD,
}
ROSTER_RULE_KEYS = {REQUIRED_PLAYERS_KEY, *TEAM_DEFENSE_KEYS}
_TEAM_DEFENSE_LABELS = {PositionSlotParent.INFIELD: 'infield', PositionSlotParent.OUTFIELD: 'outfield'}


def _chart_slot_count(range_str: str | None) -> int:
    """Number of chart slots (out of 20) a `chart_ranges` entry (e.g. "12–17", "20+", "—")
    covers. Mirrors `PostgresDB._card_list_filter_clauses`'s SQL parsing of the same field, so a
    `min_chart_*`/`max_chart_*` filter behaves identically whether it's applied in SQL (the
    picker) or here (post-hoc roster validation) - including its 21+ overflow exclusion."""
    if range_str is None or range_str == '—':
        return 0
    if range_str.endswith('+'):
        return max(0, 21 - int(range_str[:-1]))
    if '–' in range_str:
        lo, hi = range_str.split('–', 1)
        return max(0, min(int(hi), 20) - int(lo) + 1)
    if int(range_str) > 20:
        return 0
    return 1


class PlayerFilterSet(BaseModel):
    """Evaluates an already-fetched roster card against a `player_filters`-shaped JSONB dict
    (the same shape stored on `user_teams.player_filters` and `challenge_template/instance
    .player_filters`), mirroring the generic `min_X`/`max_X`/list-membership semantics that
    `PostgresDB.fetch_card_list` applies in SQL - but evaluated in Python so a roster already
    in hand can be checked without a second DB round trip.

    Also mirrors two of the SQL builder's special-cased fields - `min_fielding`/`max_fielding`
    (best rating across every position the card is rated at, or - with a `_if`/`_of`/`_ca` suffix,
    e.g. `min_fielding_if` - narrowed to one coarse defensive group: infield, outfield, or catcher)
    and `min_chart_*`/`max_chart_*` (chart slot count for a category) - since both are meaningful
    eligibility rules for a challenge (e.g. a defense-first or strikeout-heavy themed template).
    Any key can also take a `_hitters` suffix (e.g. `min_speed_hitters`, `min_fielding_if_hitters`,
    `min_chart_hr_hitters`) to apply it to hitters only, exempting pitchers, or a `_catchers`
    suffix (e.g. `max_fielding_ca_catchers`) to apply it to catchers only, exempting everyone else.
    The rest of the SQL builder's special cases (`positions`/`icons`/`awards`/`is_hof`) aren't, so
    they're still left as plain generic keys here.
    """
    filters: dict = {}

    def missing_required_players(self, roster: list[dict]) -> list[str]:
        """Display names (falling back to bref ids) of every `required_players` entry with no card
        in `roster` (any slot, bench included). A card id is `{year}-{bref_id}-{set}`, so the
        middle segment is the player; the year/set are already pinned by the other filters."""
        on_roster = {str(slot.get('card_id', '')).split('-')[1] for slot in roster if str(slot.get('card_id', '')).count('-') >= 2}
        return [
            entry.get('name') or entry['bref_id']
            for entry in (self.filters.get(REQUIRED_PLAYERS_KEY) or [])
            if entry['bref_id'] not in on_roster
        ]

    @staticmethod
    def team_defense_totals(roster: list[dict]) -> dict[PositionSlotParent, int]:
        """Summed in-game defense of the lineup's infield and outfield, each player read at his
        assigned `roster_position` (falling back to IF/OF group ratings, as the sim does via
        `PositionSlot.valid_positions`). Slots without defense (C, DH, bench, pitchers) are skipped."""
        totals = {parent: 0 for parent in _TEAM_DEFENSE_LABELS}
        for slot in roster:
            position_slot = next((ps for ps in PositionSlot if ps.value == slot.get('roster_position')), None)
            if position_slot is None or position_slot.parent not in totals:
                continue
            positions = slot.get('positions_and_defense') or {}
            rating = next((positions[p.value] for p in position_slot.valid_positions if p.value in positions), 0)
            if _FIELDING_VALUE_RE.match(str(rating)):
                totals[position_slot.parent] += int(rating)
        return totals

    def team_defense_shortfalls(self, roster: list[dict]) -> list[str]:
        """Human-readable reasons `roster` misses a `min_team_defense_*` rule, e.g. "infield defense
        of 8, under the minimum of 10" - empty when every rule is met (or none are set)."""
        rules = {parent: self.filters[key] for key, parent in TEAM_DEFENSE_KEYS.items() if self.filters.get(key) is not None}
        if not rules:
            return []
        totals = self.team_defense_totals(roster)
        return [
            f"{_TEAM_DEFENSE_LABELS[parent]} defense of {totals[parent]}, under the minimum of {minimum}"
            for parent, minimum in rules.items()
            if totals[parent] < minimum
        ]

    def ineligible_reason(self, card: dict) -> str | None:
        """None if `card` satisfies every filter, otherwise a human-readable reason it doesn't."""
        for key, value in self.filters.items():
            if value is None or key in ROSTER_RULE_KEYS:
                continue
            if key.endswith('_hitters'):
                # Hitters-only variant of the base filter - mirrors the SQL builder's
                # `(player_type = 'PITCHER' OR (<base filter>))`.
                if str(card.get('player_type') or '').upper() == 'PITCHER':
                    continue
                reason = PlayerFilterSet(filters={key.removesuffix('_hitters'): value}).ineligible_reason(card)
                if reason is not None:
                    return reason
                continue
            if key.endswith('_catchers'):
                # Catchers-only variant - mirrors the SQL builder's
                # `(NOT <rated at catcher> OR (<base filter>))`: anyone not rated at C passes.
                catcher_keys = Position.fielding_group_values('ca')
                if not any(pos in catcher_keys for pos in (card.get('positions_and_defense') or {})):
                    continue
                reason = PlayerFilterSet(filters={key.removesuffix('_catchers'): value}).ineligible_reason(card)
                if reason is not None:
                    return reason
                continue
            if key in ('min_fielding', 'max_fielding') or key.startswith(('min_fielding_', 'max_fielding_')):
                is_min = key.startswith('min_fielding')
                group = key[len('min_fielding_'):] if key.startswith('min_fielding_') else key[len('max_fielding_'):] if key.startswith('max_fielding_') else None
                position_keys = Position.fielding_group_values(group) if group is not None else None
                if group is not None and position_keys is None:
                    continue  # unrecognized group suffix - not a real filter, ignore rather than error
                positions = card.get('positions_and_defense') or {}
                if position_keys is not None:
                    positions = {pos: val for pos, val in positions.items() if pos in position_keys}
                ratings = [int(v) for v in positions.values() if _FIELDING_VALUE_RE.match(str(v))]
                if not any((r >= value if is_min else r <= value) for r in ratings):
                    bound = 'minimum' if is_min else 'maximum'
                    where = f" at {group}" if group is not None else " at any position"
                    return f"card {card.get('card_id', '?')} does not meet the {bound} fielding of {value}{where}"
            elif key.startswith('min_chart_') or key.startswith('max_chart_'):
                is_min = key.startswith('min_chart_')
                category = (key[len('min_chart_'):] if is_min else key[len('max_chart_'):]).upper()
                ranges = card.get('chart_ranges') or {}
                count = _chart_slot_count(ranges.get(category))
                if is_min and count < value:
                    return f"card {card.get('card_id', '?')} has {count} {category} chart slots, under the minimum of {value}"
                if not is_min and count > value:
                    return f"card {card.get('card_id', '?')} has {count} {category} chart slots, over the maximum of {value}"
            elif key.startswith('min_'):
                # Mirrors fetch_card_list's `({field} >= %s OR {field} IS NULL)` - a missing field
                # passes the min check (matches the picker's own query semantics).
                field = key[4:]
                actual = card.get(field)
                if actual is None:
                    return f"card {card.get('card_id', '?')} has a blank {field} of {value}"
                try:
                    actual_number = float(actual)
                    actual_value = float(value)
                except (TypeError, ValueError):
                    return f"card {card.get('card_id', '?')} has an invalid value for {field}"
                if actual_number < actual_value:
                    return f"card {card.get('card_id', '?')} does not meet the minimum {field} of {value}"
            elif key.startswith('max_'):
                field = key[4:]
                actual = card.get(field)
                if actual is None:
                    return f"card {card.get('card_id', '?')} has a blank {field} of {value}"
                try:
                    actual_number = float(actual)
                    actual_value = float(value)
                except (TypeError, ValueError):
                    return f"card {card.get('card_id', '?')} has an invalid value for {field}"
                if actual_number > actual_value:
                    return f"card {card.get('card_id', '?')} exceeds the maximum {field} of {value}"
            elif isinstance(value, list) and value:
                actual = str(card.get(key))
                allowed = {str(v) for v in value}
                if actual not in allowed:
                    return f"card {card.get('card_id', '?')} does not match the required {key} ({', '.join(allowed)})"
        return None

    def matches(self, card: dict) -> bool:
        return self.ineligible_reason(card) is None
