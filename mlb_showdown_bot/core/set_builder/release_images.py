"""
Release Builder edition images: resolves each card's style and set number from its edition, tracks
which stored images are out of date, owns the Supabase storage layout (and its cleanup), and runs
the background job that renders an edition's cards.
"""

import hashlib
import json
import os
import re
import shutil
import tempfile
import traceback
from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..card.card_image_builder import CardImageBuilder
from ..card.images import DEFAULT_RENDER_FILE_FORMAT, ImageLibrary
from ..database.postgres_db import PostgresDB
from ..supabase import SupabaseClientManager

# Bump when card templates/rendering change enough that every release image should re-render
# (2: JPEG instead of PNG, with 2003 transparency flattened onto white)
RENDER_VERSION = 2


# ---------------------------------------
# MARK: EDITION SETTINGS
# ---------------------------------------

class EditionCardStyle(BaseModel):
    """An edition's default card style (`attributes.style`, saved by the Card Style modal). Field
    names and defaults mirror the Custom Card Builder's `FORM_DEFAULTS` for `CARD_STYLE_KEYS`."""

    model_config = ConfigDict(extra='ignore')

    expansion: str = 'BS'
    edition: str = 'NONE'
    add_one_to_set_year: bool = False
    show_year_text: bool = False
    disable_display_text_on_card: bool = False
    image_parallel: str = 'NONE'
    image_coloring: str = 'PRIMARY'
    image_glow_multiplier: Optional[str | float] = '1'
    stat_highlights_type: Optional[str] = 'NONE'
    nickname_index: Optional[str | int] = 'NONE'
    is_bordered: bool = False
    is_dark_mode: bool = False
    hide_team_logo: bool = False

    @classmethod
    def from_attributes(cls, attributes: dict | None) -> 'EditionCardStyle':
        raw = (attributes or {}).get('style')
        return cls(**raw) if isinstance(raw, dict) else cls()

    def with_card_overrides(self, card_overrides: dict | None) -> 'EditionCardStyle':
        """This style with a release card's own tweaks (`card_overrides.style`) layered on top."""
        raw = (card_overrides or {}).get('style')
        if not isinstance(raw, dict) or not raw:
            return self
        return EditionCardStyle(**{**self.model_dump(), **raw})

    def image_fields(self) -> dict:
        """`ShowdownImage` values for this style. Mirrors the frontend's `applyCardStyleOverrides`."""
        try:
            glow_multiplier = float(self.image_glow_multiplier) or 1.0
        except (TypeError, ValueError):
            glow_multiplier = 1.0
        try:
            nickname_index = int(self.nickname_index) if self.nickname_index not in (None, '', 'NONE') else None
        except (TypeError, ValueError):
            nickname_index = None
        return {
            'expansion': self.expansion,
            'edition': self.edition,
            'add_one_to_set_year': self.add_one_to_set_year,
            'show_year_text': self.show_year_text,
            'parallel': self.image_parallel,
            'coloring': self.image_coloring,
            'glow_multiplier': glow_multiplier,
            'stat_highlights_type': self.stat_highlights_type or 'NONE',
            'nickname_index': nickname_index,
            'is_bordered': self.is_bordered,
            'is_dark_mode': self.is_dark_mode,
            'hide_team_logo': self.hide_team_logo,
        }


class EditionNumbering(BaseModel):
    """An edition's set numbering (`attributes.numbering`, stored with the Edition Builder's
    camelCase keys). Only the parts that change the printed number are modeled."""

    model_config = ConfigDict(extra='ignore', populate_by_name=True)

    mode: str = 'manual'
    zero_pad: bool = Field(default=False, alias='zeroPad')
    prefix: str = ''

    @field_validator('zero_pad', mode='before')
    @classmethod
    def _none_is_false(cls, value) -> bool:
        return bool(value)

    @field_validator('prefix', mode='before')
    @classmethod
    def _sanitize_prefix(cls, value) -> str:
        """Up to 3 letters, uppercased (frontend `sanitizePrefix`)."""
        if not isinstance(value, str):
            return ''
        return re.sub(r'[^a-zA-Z]', '', value)[:3].upper()

    @classmethod
    def from_attributes(cls, attributes: dict | None) -> 'EditionNumbering':
        raw = (attributes or {}).get('numbering')
        return cls(**raw) if isinstance(raw, dict) else cls()

    def set_number(self, card_number: Optional[int], total_cards: int) -> Optional[str]:
        """Number printed on the card, e.g. "AS007" (frontend `formatCardNumber`). None leaves it off."""
        if self.mode == 'none' or card_number is None:
            return None
        number = str(card_number).zfill(len(str(total_cards))) if self.zero_pad else str(card_number)
        return f"{self.prefix}{number}"


# ---------------------------------------
# MARK: PER-CARD SPEC
# ---------------------------------------

@dataclass
class ReleaseCardImageSpec:
    """Everything that determines one release card's image. `render_hash` changes whenever any of
    it does, which is how stored images are known to be out of date."""

    source_card_id: str
    card_snapshot: dict
    set_number: Optional[str]
    style: EditionCardStyle
    render_hash: str = field(init=False)

    def __post_init__(self) -> None:
        inputs = {
            'version': RENDER_VERSION,
            'snapshot': self.card_snapshot,
            'image': self.style.image_fields(),
            'disable_display_text_on_card': self.style.disable_display_text_on_card,
            'set_number': self.set_number,
        }
        encoded = json.dumps(inputs, sort_keys=True, default=str).encode()
        self.render_hash = hashlib.sha1(encoded).hexdigest()[:12]

    @property
    def card_id(self) -> str:
        """Archive id to load the full card by when the snapshot doesn't embed `card_data`."""
        return self.card_snapshot.get('card_id') or self.source_card_id

    @property
    def embedded_card_json(self) -> Optional[dict]:
        """Full card JSON carried on the snapshot (e.g. algorithm re-runs), if any."""
        card_data = self.card_snapshot.get('card_data')
        return card_data if isinstance(card_data, dict) else None

    @property
    def file_stem(self) -> str:
        safe_id = re.sub(r'[^A-Za-z0-9_-]', '_', self.source_card_id)
        return f"{safe_id}-{self.render_hash}"

    def styled_card_json(self, card_json: dict) -> dict:
        """Card JSON with the edition style + set number applied and any prior render cleared.
        Mirrors the frontend's `applyCardStyleOverrides`."""
        image = {
            **(card_json.get('image') or {}),
            **self.style.image_fields(),
            'set_number': self.set_number,
            # Re-derived from edition/parallel when the image is generated
            'special_edition': 'NONE',
            # Set name only renames the output file, which the renderer controls
            'set_name': None,
            'output_file_name': None,
            'output_folder_path': None,
            'storage_path': None,
            'thumbnail_storage_path': None,
        }
        styled = {**card_json, 'image': image}
        if isinstance(card_json.get('stats_period'), dict):
            styled['stats_period'] = {
                **card_json['stats_period'],
                'disable_display_text_on_card': self.style.disable_display_text_on_card,
            }
        return styled


class EditionImagePlan:
    """The image spec for every card in an edition (a `PostgresDB.get_edition` row)."""

    def __init__(self, edition: dict) -> None:
        self.edition_id: str = edition['id']
        self.release_id: str = edition['release_id']
        style = EditionCardStyle.from_attributes(edition.get('attributes'))
        numbering = EditionNumbering.from_attributes(edition.get('attributes'))
        cards = edition.get('cards') or []
        self.specs: list[ReleaseCardImageSpec] = [
            ReleaseCardImageSpec(
                source_card_id=card['source_card_id'],
                card_snapshot=card.get('card_snapshot') or {},
                set_number=numbering.set_number(card.get('card_number'), len(cards)),
                style=style.with_card_overrides(card.get('card_overrides')),
            )
            for card in cards if card.get('source_card_id')
        ]

    def card_statuses(self, image_rows: list[dict]) -> list[dict]:
        """Each card's image state, given the edition's `release_card_images` rows:
        rendered (current), stale (an older render is shown), failed (current inputs failed), or missing."""
        rows_by_id = {row['source_card_id']: row for row in image_rows}
        statuses = []
        for spec in self.specs:
            row = rows_by_id.get(spec.source_card_id) or {}
            if row.get('render_hash') == spec.render_hash:
                status = 'rendered'
            elif row.get('failed_hash') == spec.render_hash:
                status = 'failed'
            elif row.get('storage_path'):
                status = 'stale'
            else:
                status = 'missing'
            statuses.append({
                'source_card_id': spec.source_card_id,
                'set_number': spec.set_number,
                'status': status,
                'storage_path': row.get('storage_path'),
                'thumbnail_path': row.get('thumbnail_path'),
                'error': row.get('error') if status == 'failed' else None,
                'rendered_at': row.get('rendered_at'),
            })
        return statuses

    def specs_needing_render(self, image_rows: list[dict], source_card_ids: Optional[list[str]] = None) -> list[ReleaseCardImageSpec]:
        """Specs whose stored image is missing or out of date, optionally limited to some cards.
        Failed cards are retried."""
        rendered_hashes = {row['source_card_id']: row.get('render_hash') for row in image_rows}
        requested = set(source_card_ids) if source_card_ids else None
        return [
            spec for spec in self.specs
            if (requested is None or spec.source_card_id in requested)
            and rendered_hashes.get(spec.source_card_id) != spec.render_hash
        ]


# ---------------------------------------
# MARK: STORAGE
# ---------------------------------------

class ReleaseImageStorage:
    """Supabase storage layout for release images: `releases/{release_id}/{edition_id}/{file}`.
    File names include the render hash, so a re-render is a new URL (no stale CDN copies) and the
    file it replaces is deleted."""

    BUCKET = 'card_images'
    ROOT = 'releases'
    # File names include the render hash, so a path's content never changes: cache for a year,
    # letting repeat views/downloads hit Supabase's cheaper cached egress
    CACHE_CONTROL_SECONDS = str(365 * 24 * 60 * 60)

    def __init__(self) -> None:
        self._manager: Optional[SupabaseClientManager] = None

    @property
    def manager(self) -> SupabaseClientManager:
        # Created on first use, so cleanup with nothing to delete never builds a client
        if self._manager is None:
            self._manager = SupabaseClientManager()
        return self._manager

    @classmethod
    def folder(cls, release_id: str, edition_id: Optional[str] = None) -> str:
        return f"{cls.ROOT}/{release_id}/{edition_id}" if edition_id else f"{cls.ROOT}/{release_id}"

    @classmethod
    def public_url(cls, path: str) -> str:
        """Public URL of a file in the bucket (frontend `cardImagePublicUrl`)."""
        return f"{os.getenv('SUPABASE_URL', '').rstrip('/')}/storage/v1/object/public/{cls.BUCKET}/{path}"

    @classmethod
    def image_paths(cls, release_id: str, edition_id: str, spec: ReleaseCardImageSpec) -> tuple[str, str]:
        """(full-size path, thumbnail path). The thumbnail name matches `ShowdownPlayerCard._thumbnail_file_name`."""
        folder = cls.folder(release_id, edition_id)
        extension = DEFAULT_RENDER_FILE_FORMAT.extension
        return f"{folder}/{spec.file_stem}.{extension}", f"{folder}/{spec.file_stem}-thumb.{extension}"

    def upload(self, local_path: str, destination_path: str) -> None:
        result = self.manager.upload_file(self.BUCKET, local_path, destination_path, overwrite=True, cache_control=self.CACHE_CONTROL_SECONDS)
        if not result.get('success'):
            raise RuntimeError(f"Upload failed: {result.get('error')}")

    def delete(self, paths: list[Optional[str]]) -> None:
        """Best-effort delete. Anything that fails is left for `ReleaseImageJanitor`."""
        paths = [path for path in paths if path]
        if not paths:
            return
        failed = self.manager.delete_files(self.BUCKET, paths)
        if failed:
            print(f"Failed to delete {len(failed)} release image files (left for cleanup).")

    def list_paths(self, release_id: str, edition_id: Optional[str] = None) -> list[str]:
        return self.manager.list_file_paths(self.BUCKET, self.folder(release_id, edition_id))

    def delete_folder(self, release_id: str, edition_id: Optional[str] = None) -> None:
        """Delete every file for a release (or one of its editions), e.g. after it's deleted."""
        try:
            self.delete(self.list_paths(release_id, edition_id))
        except Exception:
            traceback.print_exc()

    def delete_unreferenced(self, release_id: str, edition_id: str, referenced_paths: set[str]) -> int:
        """Delete files in an edition's folder that no image row points to (e.g. an upload whose
        row write never happened). Returns how many were deleted."""
        orphans = [path for path in self.list_paths(release_id, edition_id) if path not in referenced_paths]
        self.delete(orphans)
        return len(orphans)

    @staticmethod
    def row_paths(rows: list[dict]) -> list[str]:
        return [path for row in rows for path in (row.get('storage_path'), row.get('thumbnail_path')) if path]


# ---------------------------------------
# MARK: RENDER JOB
# ---------------------------------------

class ReleaseImageJobCancelled(Exception):
    """The job row left the running state (user cancel or stale-job reaper) mid-render."""


class EditionImageRenderer:
    """Renders an edition's missing/out-of-date card images and uploads them one at a time, so the
    Images grid fills in as the job runs. Runs on a background thread with its own DB connection."""

    # Cards loaded from the archive per query, keeping only a batch of full cards in memory
    FETCH_BATCH_SIZE = 25

    def __init__(self, db: PostgresDB, job_id: str, edition: dict, image_libraries: list[ImageLibrary], source_card_ids: Optional[list[str]] = None) -> None:
        self.db = db
        self.job_id = job_id
        self.plan = EditionImagePlan(edition)
        self.image_libraries = image_libraries
        self.source_card_ids = source_card_ids
        self.storage = ReleaseImageStorage()
        self.completed = 0
        self.failed = 0

    @property
    def edition_id(self) -> str:
        return self.plan.edition_id

    def run(self) -> None:
        """Render every target card. Raises `ReleaseImageJobCancelled` if the job is cancelled."""
        self._clean_up_edition()
        targets = self.plan.specs_needing_render(self.db.get_release_card_images(self.edition_id), self.source_card_ids)
        self._write_progress(total=len(targets))

        output_folder_path = tempfile.mkdtemp(prefix='release-images-')
        try:
            builder = CardImageBuilder(db=self.db, image_libraries=self.image_libraries, output_folder_path=output_folder_path)
            for start in range(0, len(targets), self.FETCH_BATCH_SIZE):
                batch = targets[start:start + self.FETCH_BATCH_SIZE]
                card_jsons = self._card_jsons(batch)
                for spec in batch:
                    if self._render(builder, spec, card_jsons.get(spec.source_card_id)):
                        self.completed += 1
                    else:
                        self.failed += 1
                    self._write_progress()
        finally:
            shutil.rmtree(output_folder_path, ignore_errors=True)

    def _write_progress(self, total: Optional[int] = None) -> None:
        if not self.db.update_release_image_job_progress(self.job_id, completed=self.completed, failed=self.failed, total=total):
            raise ReleaseImageJobCancelled()

    def _clean_up_edition(self) -> None:
        """Self-heal before rendering: drop rows for cards no longer in the edition, then delete
        any file in the edition's folder that no row points to."""
        self.storage.delete(self.db.delete_release_card_images_not_in_edition(self.edition_id))
        try:
            referenced = set(ReleaseImageStorage.row_paths(self.db.get_release_card_images(self.edition_id)))
            self.storage.delete_unreferenced(self.plan.release_id, self.edition_id, referenced)
        except Exception:
            # A failed sweep only leaves orphans for the next one
            traceback.print_exc()

    def _card_jsons(self, specs: list[ReleaseCardImageSpec]) -> dict[str, dict]:
        """Full card JSON per source card id: embedded on the snapshot, else loaded from the archive."""
        card_jsons = {spec.source_card_id: spec.embedded_card_json for spec in specs if spec.embedded_card_json}
        to_fetch = {spec.card_id: spec.source_card_id for spec in specs if spec.source_card_id not in card_jsons}
        if to_fetch:
            for card_id, card in self.db.fetch_cards_by_ids(list(to_fetch.keys())).items():
                card_jsons[to_fetch[card_id]] = card.as_json()
        return card_jsons

    def _render(self, builder: CardImageBuilder, spec: ReleaseCardImageSpec, card_json: Optional[dict]) -> bool:
        """Render, upload, and record one card. Returns False (recording the error) if it failed."""
        if card_json is None:
            self.db.record_release_card_image_failure(self.edition_id, spec.source_card_id, spec.render_hash, 'Card not found in the archive.')
            return False

        storage_path, thumbnail_path = ReleaseImageStorage.image_paths(self.plan.release_id, self.edition_id, spec)
        local_paths = [os.path.join(builder.output_folder_path, os.path.basename(path)) for path in (storage_path, thumbnail_path)]
        try:
            card = builder.card_from_json(spec.styled_card_json(card_json))
            card.image.output_file_name = os.path.basename(storage_path)
            # Makes save_image write the thumbnail too; uploading is done here, to the release folder
            card.image.upload_to_supabase = True
            card.disable_cache_cleaning = True
            card.generate_card_image()
            self.storage.upload(local_paths[0], storage_path)
            self.storage.upload(local_paths[1], thumbnail_path)
        except Exception as exc:
            traceback.print_exc()
            self.db.record_release_card_image_failure(self.edition_id, spec.source_card_id, spec.render_hash, str(exc)[:500])
            return False
        finally:
            for local_path in local_paths:
                if os.path.exists(local_path):
                    os.remove(local_path)

        replaced_paths = self.db.save_release_card_image(self.edition_id, spec.source_card_id, spec.render_hash, storage_path, thumbnail_path)
        if replaced_paths is None:
            # Removed from the edition mid-render
            self.storage.delete([storage_path, thumbnail_path])
        else:
            self.storage.delete([path for path in replaced_paths if path not in (storage_path, thumbnail_path)])
        return True


# ---------------------------------------
# MARK: JANITOR
# ---------------------------------------

class ReleaseImageJanitor:
    """Release-wide storage sweep: deletes folders of releases/editions that no longer exist and
    files no image row points to. A safety net for best-effort deletes that failed."""

    def __init__(self, db: PostgresDB, dry_run: bool = False) -> None:
        self.db = db
        self.dry_run = dry_run
        self.storage = ReleaseImageStorage()

    def run(self) -> int:
        """Returns how many files were (or, in a dry run, would be) deleted."""
        all_paths = self.storage.manager.list_file_paths(ReleaseImageStorage.BUCKET, ReleaseImageStorage.ROOT)
        referenced = set(ReleaseImageStorage.row_paths(self.db.get_all_release_card_image_paths()))
        # A running job uploads each file just before recording it, so its edition is left alone
        active_folders = tuple(
            f"{ReleaseImageStorage.folder(job['release_id'], job['edition_id'])}/"
            for job in self.db.get_active_release_image_jobs()
        )
        orphans = [path for path in all_paths if path not in referenced and not path.startswith(active_folders)]
        print(f"{len(all_paths)} release image files, {len(orphans)} unreferenced.")
        if orphans and not self.dry_run:
            self.storage.delete(orphans)
        return len(orphans)
