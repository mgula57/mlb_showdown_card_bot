import re

from pydantic import BaseModel

from ...shared.player_position import Position

_FIELDING_VALUE_RE = re.compile(r'^-?[0-9]+$')


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
    The rest of the SQL builder's special cases (`positions`/`icons`/`awards`/`is_hof`) aren't, so
    they're still left as plain generic keys here.
    """
    filters: dict = {}

    def ineligible_reason(self, card: dict) -> str | None:
        """None if `card` satisfies every filter, otherwise a human-readable reason it doesn't."""
        for key, value in self.filters.items():
            if value is None:
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
