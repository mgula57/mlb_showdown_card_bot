from ..card.showdown_player_card import ShowdownPlayerCard
from ..database.postgres_db import PostgresDB


class ReleaseCustomCardError(ValueError):
    """The custom card can't be added to a release (e.g. it no longer exists)."""


class ReleaseCustomCard:
    """Turns a card from the user's Custom Card Builder history (`log_custom_card_bot`) into a
    release card snapshot, so date range, multi-year and other one-off cards can join an edition.

    Custom cards have no `card_bot` row, so the snapshot is built from the card itself: the same
    card-derived columns a rebuilt card gets, plus the identity columns `card_bot` takes from the
    stats archive. The full card JSON is embedded (`card_data`), which is what image renders,
    the card detail and team/league roster lookups read instead of the archive.
    """

    SOURCE = 'CUSTOM'

    def __init__(self, db: PostgresDB) -> None:
        self.db = db

    def snapshot(self, custom_card_id: str) -> dict:
        card = self.db.fetch_cards_for_roster_slots([{'card_id': custom_card_id, 'card_source': self.SOURCE}]).get(str(custom_card_id))
        if card is None:
            raise ReleaseCustomCardError('Custom card not found.')
        return {
            **self._identity_columns(card, str(custom_card_id)),
            **card.card_bot_columns(),
        }

    def _identity_columns(self, card: ShowdownPlayerCard, custom_card_id: str) -> dict:
        """The `card_bot` columns that come from the stats archive rather than the card. `year` is an
        int column there, so a multi-year card files under its first year; `card_year` (from
        `card_bot_columns`) keeps the full year string, e.g. "2000-2004"."""
        year_list = card.stats_period.year_list
        return {
            'source': self.SOURCE,
            'id': custom_card_id,
            # No archived card to point at: the snapshot's `card_data` is the card
            'card_id': None,
            'name': card.name,
            'year': min(year_list) if year_list else int(str(card.year)[:4]),
            'bref_id': card.bref_id or None,
            'mlb_id': card.mlb_id,
            'player_type': card.player_type.name if card.player_type else None,
            'team': card.team.value if card.team else None,
            'team_id': card.team.value if card.team else None,
            'league': card.league,
            'showdown_set': card.set.value,
            'is_two_way': False,
        }
