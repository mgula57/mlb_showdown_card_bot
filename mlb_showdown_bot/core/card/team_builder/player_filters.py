from pydantic import BaseModel


class PlayerFilterSet(BaseModel):
    """Evaluates an already-fetched roster card against a `player_filters`-shaped JSONB dict
    (the same shape stored on `user_teams.player_filters` and `challenge_template/instance
    .player_filters`), mirroring the generic `min_X`/`max_X`/list-membership semantics that
    `PostgresDB.fetch_card_list` applies in SQL - but evaluated in Python so a roster already
    in hand can be checked without a second DB round trip.

    Only the generic filter keys are supported here (not the SQL builder's special-cased array
    fields like `positions`/`icons`/`awards`/`is_hof`), since those aren't meaningful for the
    team/hand/year-style eligibility rules challenges use.
    """
    filters: dict = {}

    def ineligible_reason(self, card: dict) -> str | None:
        """None if `card` satisfies every filter, otherwise a human-readable reason it doesn't."""
        for key, value in self.filters.items():
            if value is None:
                continue
            if key.startswith('min_'):
                # Mirrors fetch_card_list's `coalesce({field} >= %s, true)` - a missing field
                # passes the min check (matches the picker's own query semantics).
                field = key[4:]
                actual = card.get(field)
                if actual is not None and actual < value:
                    return f"card {card.get('card_id', '?')} does not meet the minimum {field} of {value}"
            elif key.startswith('max_'):
                field = key[4:]
                actual = card.get(field)
                if actual is None or actual > value:
                    return f"card {card.get('card_id', '?')} exceeds the maximum {field} of {value}"
            elif isinstance(value, list) and value:
                actual = str(card.get(key))
                allowed = {str(v) for v in value}
                if actual not in allowed:
                    return f"card {card.get('card_id', '?')} does not match the required {key} ({', '.join(allowed)})"
        return None

    def matches(self, card: dict) -> bool:
        return self.ineligible_reason(card) is None
