import threading
import traceback
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel

from ..card.images import AutoImageFile, ImageLibrary, ImageMatchType
from ..card.sets import Set
from ..database.postgres_db import PostgresDB
from ..shared.google_drive import UserDriveFolder, fetch_image_metadata


class ImageMatchCard(BaseModel):
    """The fields of a card snapshot that decide its auto image match."""

    id: str
    year: str
    bref_id: Optional[str] = None
    mlb_id: Optional[str] = None
    team_id: Optional[str] = None
    player_type_override: Optional[str] = None

    @classmethod
    def from_snapshot(cls, snapshot: dict) -> Optional['ImageMatchCard']:
        """None for snapshots without an id or player id (ex: custom cards)."""
        if not snapshot.get('id') or not (snapshot.get('bref_id') or snapshot.get('mlb_id')):
            return None
        return cls(
            id=str(snapshot['id']),
            year=str(snapshot.get('year') or ''),
            bref_id=snapshot.get('bref_id'),
            mlb_id=str(snapshot['mlb_id']) if snapshot.get('mlb_id') else None,
            team_id=snapshot.get('team_id'),
            player_type_override=snapshot.get('player_type_override'),
        )

    @property
    def player_ids(self) -> list[str]:
        return [player_id for player_id in (self.bref_id, self.mlb_id) if player_id]


class LibraryImageIndex:
    """One library's auto images, keyed by player id (bref or MLB id)."""

    def __init__(self, files: list[AutoImageFile]) -> None:
        self.by_player_id: dict[str, list[AutoImageFile]] = defaultdict(list)
        for file in files:
            self.by_player_id[file.player_id].append(file)

    def files_for(self, card: ImageMatchCard) -> list[AutoImageFile]:
        return [file for player_id in card.player_ids for file in self.by_player_id.get(player_id, [])]

    @classmethod
    def load(cls, library: ImageLibrary) -> 'LibraryImageIndex':
        return cls(cls._showdown_bot_files() if library.is_showdown_bot else cls._user_library_files(library))

    @staticmethod
    def _showdown_bot_files() -> list[AutoImageFile]:
        """internal.dim_auto_image, plus anything added to the Drive folder since it was last synced.
        The delta is one small Drive query, so new uploads show up without a full table rebuild."""
        with PostgresDB() as db:
            files, synced_through = db.get_auto_images()
        if synced_through is None:
            return files
        recent = fetch_image_metadata(folder_id=Set._2000.player_image_gdrive_folder_id, retries=1, modified_after=synced_through) or []
        return files + [file for file in (AutoImageFile.from_file_name(f['name']) for f in recent) if file]

    @staticmethod
    def _user_library_files(library: ImageLibrary) -> list[AutoImageFile]:
        """Live listing of the user's shared folder. An unshared/missing folder has no images, like at render time."""
        try:
            listed = UserDriveFolder(library.folder_id).list_image_files()
        except Exception:
            traceback.print_exc()
            return []
        files = [file for file in (AutoImageFile.from_file_name(f['name']) for f in listed) if file and file.component in ('BG', 'CUT')]
        # A render skips a library without the player's cutout (some styles don't need the BG layer)
        players_with_cut = {file.player_id for file in files if file.component == 'CUT'}
        return [file for file in files if file.player_id in players_with_cut]


class ImageMatchClassifier:
    """Classifies cards against a user's image libraries the way an edition render searches them:
    libraries in the user's order, using the first one with any image of the player.

    Library listings are cached per process for `CACHE_TTL`, so reopening an edition is fast and
    `refresh` re-reads Drive."""

    CACHE_TTL = timedelta(minutes=10)
    _cache: dict[str, tuple[LibraryImageIndex, datetime]] = {}
    _lock = threading.Lock()

    def __init__(self, libraries: list[ImageLibrary], refresh: bool = False) -> None:
        self.libraries = libraries
        self.refresh = refresh

    @classmethod
    def _cache_key(cls, library: ImageLibrary) -> str:
        return library.folder_id or library.id

    def _index(self, library: ImageLibrary) -> tuple[LibraryImageIndex, datetime]:
        key = self._cache_key(library)
        now = datetime.now(timezone.utc)
        with self._lock:
            cached = self._cache.get(key)
        if cached and not self.refresh and now - cached[1] < self.CACHE_TTL:
            return cached
        loaded = (LibraryImageIndex.load(library), now)
        with self._lock:
            self._cache[key] = loaded
        return loaded

    def classify(self, cards: list[ImageMatchCard]) -> dict:
        """Match type and source library per card id, plus when the oldest library listing was read."""
        indexes = [(library, *self._index(library)) for library in self.libraries]
        matches: dict[str, dict] = {}
        for card in cards:
            match_type, library_name = ImageMatchType.NO_MATCH, None
            for library, index, _ in indexes:
                files = index.files_for(card)
                if not files:
                    continue
                library_name = library.name
                match_type = min(
                    (file.match_type(card.year, card.team_id, card.player_type_override) for file in files),
                    key=lambda m: m.rank,
                )
                break
            matches[card.id] = {'image_match_type': match_type.value, 'library_name': library_name}
        checked_at = min((loaded_at for _, _, loaded_at in indexes), default=datetime.now(timezone.utc))
        return {'matches': matches, 'checked_at': checked_at.isoformat()}
