"""
Release short links: `/r/<owner>/<release>[/<edition>[/<card>]]`, where `<owner>` is the creator's
username (or their user id when they have none) and `<release>` is the release's slug, unique per owner
(so two users can both have a `2026-base`). Links shared before slugs were per owner,
`/r/<slug>[/<edition>[/<card>]]`, still resolve through the release's `legacy_slug`.
"""

from dataclasses import dataclass
from typing import Optional

from ..database.postgres_db import PostgresDB


@dataclass(frozen=True)
class ReleaseLink:
    """Where a short link points: the release, and optionally an edition (by slug) and one of its cards
    (by release card id). It doesn't check visibility; `get_release` does that."""

    release_id: str
    edition_slug: Optional[str] = None
    card_ref: Optional[str] = None

    @classmethod
    def resolve(cls, db: PostgresDB, path: str) -> Optional['ReleaseLink']:
        """The release behind the part of a short link after `/r/`, or None. The owner form is tried
        first; a path that doesn't match it falls back to the legacy form (one segment fewer)."""
        segments = [segment for segment in path.strip('/').split('/') if segment]
        if not segments or len(segments) > 4:
            return None
        if len(segments) >= 2:
            release_id = db.get_release_id_by_owner_slug(segments[0], segments[1])
            if release_id:
                return cls(release_id, *segments[2:])
        if len(segments) <= 3:
            release_id = db.get_release_id_by_legacy_slug(segments[0])
            if release_id:
                return cls(release_id, *segments[1:])
        return None

    @staticmethod
    def path(release: dict, edition_slug: Optional[str] = None, card_ref: Optional[str] = None) -> str:
        """A release's short link path, from its `share_path` (see `PostgresDB._serialize_release_row`)."""
        path = f"/r/{release['share_path']}"
        if edition_slug:
            path += f"/{edition_slug}"
            if card_ref:
                path += f"/{card_ref}"
        return path
