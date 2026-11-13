from typing import TYPE_CHECKING

from .images import DEFAULT_RENDER_FILE_FORMAT, ImageLibrary
from .showdown_player_card import ShowdownPlayerCard

if TYPE_CHECKING:
    from ..database.postgres_db import PostgresDB


class CardImageBuilder:
    """Turns stored card JSON (archive rows, client payloads, release snapshots) into a card
    ready for `generate_card_image()`: output folder and file format, the user's auto image
    libraries, and a bref id when the card only has an MLB id (auto images are keyed by bref id)."""

    def __init__(self, db: 'PostgresDB', image_libraries: list[ImageLibrary], output_folder_path: str) -> None:
        self.db = db
        self.image_libraries = image_libraries
        self.output_folder_path = output_folder_path

    def card_from_json(self, card_json: dict) -> ShowdownPlayerCard:
        card = ShowdownPlayerCard(**card_json)
        card.image.output_folder_path = self.output_folder_path
        # Stored card JSON may say PNG (rendered before JPEG); new renders always use the default
        card.image.file_format = DEFAULT_RENDER_FILE_FORMAT
        card.image.source.set_libraries(self.image_libraries)
        if not card.bref_id and card.mlb_id:
            bref_id = self.db.fetch_bref_id_for_mlb_id(card.mlb_id)
            if bref_id:
                card.bref_id = bref_id
        return card
