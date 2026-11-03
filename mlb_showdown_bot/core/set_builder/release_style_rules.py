"""
Release Builder edition style rules: "IF conditions THEN style" layered over an edition's default
card style (`attributes.style_rules`, saved by the Card Style modal).

Conditions store the Edition Builder pool's group labels ("Onbase 10", "300-399 PTS", "ARI"), so
`ReleaseCardDimensions` must produce exactly the labels `GROUPERS` in
`frontend/src/components/releases/poolGrouping.ts` does.
"""

import math
import re
from typing import Callable, Optional

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

# Style fields a rule can set. Mirrors `RULE_STYLE_KEYS` in `frontend/src/components/releases/editionStyle.ts`.
RULE_STYLE_KEYS = frozenset({'image_parallel', 'edition', 'image_coloring', 'show_year_text', 'is_dark_mode', 'hide_team_logo'})

# Relocated clubs grouped under their current franchise. Mirrors `FRANCHISE_CODE` in `SummaryCharts.tsx`.
FRANCHISE_CODE = {
    'MON': 'WSN',
    'FLA': 'MIA',
    'CAL': 'LAA',
    'ANA': 'LAA',
    'TBD': 'TBR',
    'OAK': 'ATH',
}

PTS_TIER_SIZE = 100


def _js_number(value) -> str:
    """A number as JavaScript's template strings print it (15.0 → "15")."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


class ReleaseCardDimensions:
    """The pool group labels one release card falls under, per dimension a rule can test."""

    def __init__(self, card: dict) -> None:
        self.snapshot: dict = card.get('card_snapshot') or {}
        self.tags: list[str] = card.get('tags') or []

    def labels(self, dimension: str) -> Optional[list[str]]:
        """The card's labels for `dimension`, or None for a dimension rules can't test."""
        keyer: Optional[Callable[[ReleaseCardDimensions], list[str]]] = self._KEYERS.get(dimension)
        return keyer(self) if keyer else None

    @property
    def _is_pitcher(self) -> bool:
        return bool(self.snapshot.get('is_pitcher'))

    def _team(self) -> list[str]:
        team = self.snapshot.get('team')
        return [FRANCHISE_CODE.get(team, team) if team else 'No Team']

    def _league(self) -> list[str]:
        return [self.snapshot.get('league') or 'Unknown']

    def _position(self) -> list[str]:
        positions = self.snapshot.get('positions_list') or []
        if positions:
            return [positions[0]]
        player_type = self.snapshot.get('player_type')
        return [player_type if player_type is not None else 'Unknown']

    def _type(self) -> list[str]:
        if not self._is_pitcher:
            return ['Position Player']
        return ['Starting Pitcher' if 'STARTER' in (self.snapshot.get('positions_list') or []) else 'Relief Pitcher']

    def _hand(self) -> list[str]:
        letter = str(self.snapshot.get('hand') or '').strip()[:1].upper()
        if not letter:
            return ['Unknown']
        if self._is_pitcher:
            return [f"{letter}HP"]
        return [f"Bats {'S' if letter == 'B' else letter}"]

    def _year(self) -> list[str]:
        # First year of the year string, like JavaScript's parseInt ("2000-2004" → 2000, "CAREER" → Unknown)
        match = re.match(r'\s*([+-]?\d+)', str(self.snapshot.get('year') or ''))
        year = int(match.group(1)) if match else 0
        return [str(year) if year else 'Unknown']

    def _hof(self) -> list[str]:
        return ['Hall of Fame' if self.snapshot.get('is_hof') else 'Not in Hall of Fame']

    def _awards(self) -> list[str]:
        awards = list(dict.fromkeys(self.snapshot.get('awards_list') or []))
        return awards or ['No Awards']

    def _nationality(self) -> list[str]:
        return [self.snapshot.get('nationality') or 'Unknown']

    def _points(self) -> list[str]:
        floor = math.floor((self.snapshot.get('points') or 0) / PTS_TIER_SIZE) * PTS_TIER_SIZE
        return [f"{floor}-{floor + PTS_TIER_SIZE - 1} PTS"]

    def _command(self) -> list[str]:
        side = 'Control' if self._is_pitcher else 'Onbase'
        return [f"{side} {_js_number(self.snapshot.get('command') or 0)}"]

    def _speed(self) -> list[str]:
        if self._is_pitcher:
            return ['Pitchers']
        return [f"Speed {_js_number(self.snapshot.get('speed') or 0)}"]

    def _ip(self) -> list[str]:
        if not self._is_pitcher:
            return ['Hitters']
        return [f"IP {_js_number(self.snapshot.get('ip') or 0)}"]

    def _tag(self) -> list[str]:
        return list(self.tags) or ['Untagged']

    _KEYERS: dict[str, Callable[['ReleaseCardDimensions'], list[str]]] = {
        'team': _team,
        'league': _league,
        'position': _position,
        'type': _type,
        'hand': _hand,
        'year': _year,
        'hof': _hof,
        'awards': _awards,
        'nationality': _nationality,
        'points': _points,
        'command': _command,
        'speed': _speed,
        'ip': _ip,
        'tag': _tag,
    }


class EditionStyleRule(BaseModel):
    """One rule: every condition (a dimension and the labels that satisfy it) must match."""

    model_config = ConfigDict(extra='ignore')

    when: dict[str, list[str]] = {}
    style: dict = {}

    @field_validator('style')
    @classmethod
    def _rule_style_keys_only(cls, style: dict) -> dict:
        return {key: value for key, value in style.items() if key in RULE_STYLE_KEYS}

    def matches(self, dimensions: ReleaseCardDimensions) -> bool:
        """Mirrors `styleRuleMatches`: needs a condition and a style, and a condition on a dimension
        rules can't test never matches."""
        conditions = {dimension: values for dimension, values in self.when.items() if values}
        if not conditions or not self.style:
            return False
        for dimension, values in conditions.items():
            labels = dimensions.labels(dimension)
            if labels is None or not any(label in values for label in labels):
                return False
        return True


class EditionStyleRules:
    """An edition's style rules, in order (a later rule wins)."""

    def __init__(self, rules: list[EditionStyleRule]) -> None:
        self.rules = rules

    @classmethod
    def from_attributes(cls, attributes: dict | None) -> 'EditionStyleRules':
        raw = (attributes or {}).get('style_rules')
        rules = []
        for rule in raw if isinstance(raw, list) else []:
            try:
                rules.append(EditionStyleRule.model_validate(rule))
            except ValidationError:
                continue
        return cls(rules)

    def style_for(self, card: dict) -> dict:
        """The style fields the matching rules set on a release card."""
        if not self.rules:
            return {}
        dimensions = ReleaseCardDimensions(card)
        style: dict = {}
        for rule in self.rules:
            if rule.matches(dimensions):
                style.update(rule.style)
        return style
