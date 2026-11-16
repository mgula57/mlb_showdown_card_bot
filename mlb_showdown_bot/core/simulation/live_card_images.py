"""
Rendered card images for live games, made on demand: the board can show the pitcher and hitter as
full Showdown cards instead of the compact `CardItem`, with the swing's result lit up on the chart.

A card is rendered with the viewer's image libraries the first time anyone asks for it, at a display
size, and stored under a hash of everything that shapes the image (`LiveCardImageSpec`). The same
card with the same libraries is never rendered twice, across games and viewers.
"""

import hashlib
import json
import os
import shutil
import tempfile
import threading
from dataclasses import dataclass, field
import requests
from PIL import Image

from ..card.card_image_builder import CardImageBuilder
from ..card.images import DEFAULT_RENDER_FILE_FORMAT, ImageLibrary
from ..card.showdown_player_card import ShowdownPlayerCard
from ..database.postgres_db import PostgresDB
from ..set_builder.release_images import RENDER_VERSION, ReleaseImageStorage


@dataclass
class LiveCardImageSpec:
    """One card as one viewer sees it. `render_hash` changes whenever the image would."""

    card_json: dict
    image_libraries: list[ImageLibrary]
    render_hash: str = field(init=False)

    def __post_init__(self) -> None:
        inputs = {
            'version': RENDER_VERSION,
            'card': self.card_json,
            # Order matters: the first library with the player's image wins
            'libraries': [library.id for library in self.image_libraries],
        }
        encoded = json.dumps(inputs, sort_keys=True, default=str).encode()
        self.render_hash = hashlib.sha1(encoded).hexdigest()[:16]

    @property
    def storage_path(self) -> str:
        return f"{LiveCardImages.FOLDER}/{self.render_hash}.{DEFAULT_RENDER_FILE_FORMAT.extension}"


class LiveCardImages:
    """Renders (or finds the stored render of) a live game's card for a viewer."""

    FOLDER = 'games/cards'
    # Wide enough to read the chart on a board corner card, at a fraction of full size's weight
    DISPLAY_WIDTH = 744

    # Hashes known to be in storage, so repeat requests skip the existence check
    _stored: set[str] = set()
    # One render per hash at a time; a second request for it waits, then finds it stored
    _locks: dict[str, threading.Lock] = {}
    _locks_guard = threading.Lock()

    def __init__(self, image_libraries: list[ImageLibrary]) -> None:
        self.image_libraries = image_libraries
        self.storage = ReleaseImageStorage()

    def image_json(self, card: ShowdownPlayerCard) -> dict:
        """The card's image URL and where its chart results (`chart_cell_boxes`) and command
        (`command_box`) sit on it, rendering it first if it isn't stored yet."""
        spec = LiveCardImageSpec(card_json=card.as_json(), image_libraries=self.image_libraries)
        with self._lock_for(spec.render_hash):
            if not self._is_stored(spec):
                self._render(spec)
        return {
            'image_url': ReleaseImageStorage.public_url(spec.storage_path),
            'chart_cells': card.chart_cell_boxes(),
            'command_box': card.command_box(),
        }

    @classmethod
    def _lock_for(cls, render_hash: str) -> threading.Lock:
        with cls._locks_guard:
            return cls._locks.setdefault(render_hash, threading.Lock())

    @classmethod
    def _is_stored(cls, spec: LiveCardImageSpec) -> bool:
        if spec.render_hash in cls._stored:
            return True
        try:
            response = requests.head(ReleaseImageStorage.public_url(spec.storage_path), timeout=5)
            is_stored = response.status_code == 200
        except requests.RequestException:
            is_stored = False
        if is_stored:
            cls._stored.add(spec.render_hash)
        return is_stored

    def _render(self, spec: LiveCardImageSpec) -> None:
        output_folder_path = tempfile.mkdtemp(prefix='live-card-images-')
        try:
            with PostgresDB() as db:
                builder = CardImageBuilder(db=db, image_libraries=self.image_libraries, output_folder_path=output_folder_path)
                card = builder.card_from_json(self._unrendered(spec.card_json))
            card.image.output_file_name = os.path.basename(spec.storage_path)
            card.disable_cache_cleaning = True
            card.generate_card_image()
            print(f"Rendered live game card {card.name} ({card.set.value}) in {card.load_time}s")

            local_path = os.path.join(output_folder_path, card.image.output_file_name)
            self._shrink_to_display_size(local_path)
            self.storage.upload(local_path, spec.storage_path)
            type(self)._stored.add(spec.render_hash)
        finally:
            shutil.rmtree(output_folder_path, ignore_errors=True)

    @staticmethod
    def _unrendered(card_json: dict) -> dict:
        """Card JSON with any earlier render's output cleared, so this one writes where it's told."""
        image = {
            **(card_json.get('image') or {}),
            'set_name': None,
            'output_file_name': None,
            'output_folder_path': None,
            'storage_path': None,
            'thumbnail_storage_path': None,
        }
        return {**card_json, 'image': image}

    @classmethod
    def _shrink_to_display_size(cls, path: str) -> None:
        with Image.open(path) as image:
            if image.width <= cls.DISPLAY_WIDTH:
                return
            height = round(image.height * cls.DISPLAY_WIDTH / image.width)
            resized = image.resize((cls.DISPLAY_WIDTH, height), Image.Resampling.LANCZOS)
        resized.save(path, **DEFAULT_RENDER_FILE_FORMAT.save_kwargs)

