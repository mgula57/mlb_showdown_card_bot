from typing import Optional
from ..card.showdown_player_card import ShowdownPlayerCard
from ..database.postgres_db import PostgresDB


class ReleaseCardRebuildError(ValueError):
    """The card can't be rebuilt as requested (e.g. a chart version it doesn't have)."""


class ReleaseCardRebuilder:
    """Swaps a release card's snapshot for the same card at another chart version.

    The chart version decides which command/outs chart the card uses, and with it the card's
    command, outs, projections and points - so unlike style it can't sit on top of the snapshot
    as an override. Version 1 restores the archived card as-is (no formula drift from re-running
    it); other versions re-run the archived card through the current algorithm at that version
    and embed the result in the snapshot. A variable speed card stays variable speed either way.
    """

    MAX_CHART_VERSION = 5
    # Rendered-image outputs of the stored card - a rebuilt chart needs its own image. An output
    # folder would also render one server-side during the build.
    _IMAGE_OUTPUT_FIELDS = ('output_file_name', 'output_folder_path', 'storage_path', 'thumbnail_storage_path')

    def __init__(self, db: PostgresDB) -> None:
        self.db = db

    def snapshot_at_chart_version(self, snapshot: dict, source_card_type: str, chart_version: int) -> dict:
        """A new snapshot for the card at `chart_version`. Raises ReleaseCardRebuildError when the
        card has no chart versions (WOTC) or no chart at that version."""
        if str(source_card_type).upper() != 'BOT':
            raise ReleaseCardRebuildError('Only Showdown Bot cards have chart versions.')
        if not 1 <= chart_version <= self.MAX_CHART_VERSION:
            raise ReleaseCardRebuildError(f'Chart version must be between 1 and {self.MAX_CHART_VERSION}.')
        card_id = snapshot.get('card_id')
        if not card_id:
            raise ReleaseCardRebuildError('Card is missing its archived card id.')

        is_variable_speed = bool(snapshot.get('is_variable_speed_00_01') or (snapshot.get('card_data') or {}).get('is_variable_speed_00_01'))
        if chart_version == 1:
            archived_row = self._archived_row(card_id, is_variable_speed)
            if archived_row is not None:
                return {**{k: v for k, v in snapshot.items() if k != 'card_data'}, **archived_row}

        card = self._rebuilt_card(snapshot, card_id, chart_version, is_variable_speed)
        return {**snapshot, **card.card_bot_columns(), 'is_variable_speed_00_01': card.is_variable_speed_00_01}

    def _archived_row(self, card_id: str, is_variable_speed: bool) -> Optional[dict]:
        """The card's `card_bot` row, as manual add / the algorithm snapshot it"""
        rows = self.db.fetch_card_list({'card_id': [card_id], 'limit': 1, 'variable_speed': is_variable_speed})
        return rows[0] if rows else None

    def _rebuilt_card(self, snapshot: dict, card_id: str, chart_version: int, is_variable_speed: bool) -> ShowdownPlayerCard:
        card_data = snapshot.get('card_data')
        if not card_data:
            archived_card = self.db.fetch_cards_for_roster_slots([{'card_id': card_id, 'card_source': 'BOT'}]).get(str(card_id))
            if archived_card is None:
                raise ReleaseCardRebuildError('Card not found in the archive.')
            card_data = archived_card.as_json()
        if card_data.get('is_wotc'):
            raise ReleaseCardRebuildError('Only Showdown Bot cards have chart versions.')

        image = {k: v for k, v in (card_data.get('image') or {}).items() if k not in self._IMAGE_OUTPUT_FIELDS}
        try:
            return ShowdownPlayerCard.rebuilt_from_card_data({**card_data, 'image': image, 'chart_version': chart_version, 'is_variable_speed_00_01': is_variable_speed})
        except IndexError:
            # `_most_accurate_chart` indexes the ranked charts by version
            raise ReleaseCardRebuildError(f"This card doesn't have a chart version {chart_version}.")
