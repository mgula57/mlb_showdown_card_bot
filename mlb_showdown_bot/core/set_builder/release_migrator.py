import uuid
from dataclasses import dataclass, field
from typing import Optional

from psycopg2 import extras
from psycopg2.extras import RealDictCursor

from ..database.postgres_db import PostgresDB


class ReleaseMigrationError(ValueError):
    """The release can't be migrated (missing, owner has no account in the target, slug taken, ...)."""


@dataclass
class EditionMigration:
    """One source edition as it will land in the target: its working copy's content when the owner
    has unpublished edits, so the target gets what the owner would see after their next publish."""
    name: str
    slug: str
    attributes: dict
    cards: list[dict]
    from_working_copy: bool = False

    @property
    def custom_card_count(self) -> int:
        return sum(1 for card in self.cards if str(card.get('source_card_type') or '').upper() == 'CUSTOM')


@dataclass
class ReleaseMigrationPlan:
    """What `ReleaseMigrator.apply` will write. Built read-only, so a dry run is just printing it."""
    slug: str
    release_fields: dict
    owner_email: str
    target_owner_id: str
    editions: list[EditionMigration]
    target_release_id: Optional[str] = None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_update(self) -> bool:
        return self.target_release_id is not None

    def summary(self) -> str:
        action = f"Update unpublished release {self.target_release_id}" if self.is_update else "Create new release"
        lines = [
            f"Release   {self.release_fields.get('name')} ({self.slug})",
            f"Owner     {self.owner_email} -> target user {self.target_owner_id}",
            f"Action    {action} (lands unpublished, no image rows copied)",
            "Editions",
        ]
        for edition in self.editions:
            notes = []
            if edition.from_working_copy:
                notes.append('from working copy')
            if edition.custom_card_count:
                notes.append(f'{edition.custom_card_count} custom')
            suffix = f"  [{', '.join(notes)}]" if notes else ''
            lines.append(f"  - {edition.name} ({edition.slug}): {len(edition.cards)} cards{suffix}")
        lines.extend(f"⚠️  {warning}" for warning in self.warnings)
        return '\n'.join(lines)


class ReleaseMigrator:
    """Copies a release built in one database (DEV, `DATABASE_URL_LOGS`) into another (PROD,
    `DATABASE_URL_ARCHIVE`) as an unpublished release, so its owner can review, render images and
    publish it there through the normal Release Builder flow.

    - Owner: matched by email across the two Supabase projects' `auth.users`.
    - Ids: the target gets fresh release/edition ids. Image files live under
      `releases/{release_id}/{edition_id}/`, so sharing ids could let one side's cleanup delete the
      other's renders. Card ids come from `_upsert_release_cards`, stable per (edition, source card).
    - Re-runs: the target release is found by slug + owner and synced in place (editions matched by
      slug), but only while it has never been published there. After that it's edited in PROD.
    - Not copied: image rows/files, publish state and versions, likes/saves/views/comments, remix parent.
    """

    def __init__(self, source_db: PostgresDB, target_db: PostgresDB, slug: str) -> None:
        if not source_db.connection or not target_db.connection:
            raise ReleaseMigrationError("Both databases must be connected.")
        self.source_db = source_db
        self.target_db = target_db
        self.slug = slug

    # ---------------------------------------------------------------------
    # MARK: - PLAN (READ-ONLY)
    # ---------------------------------------------------------------------

    def plan(self) -> ReleaseMigrationPlan:
        self._check_target_schema()
        release = self._source_release()
        owner_email = self._source_owner_email(release['created_by'])
        target_owner_id = self._target_user_id(owner_email)
        plan = ReleaseMigrationPlan(
            slug=self.slug,
            release_fields=PostgresDB._release_payload_fields(release),
            owner_email=owner_email,
            target_owner_id=target_owner_id,
            editions=self._source_editions(release['id']),
            target_release_id=self._existing_target_release_id(target_owner_id),
        )
        if not plan.editions:
            raise ReleaseMigrationError(f"Release '{self.slug}' has no live editions to migrate.")
        if release.get('fork_parent_id'):
            plan.warnings.append("Remix credit (fork_parent_id) is not carried over: the parent release doesn't exist in the target.")
        custom_count = sum(edition.custom_card_count for edition in plan.editions)
        if custom_count:
            plan.warnings.append(
                f"{custom_count} CUSTOM card(s) point at source custom-card log ids. They render from their embedded "
                "card_data, but re-adding them from the Custom Card Builder in the target won't match."
            )
        return plan

    def _check_target_schema(self) -> None:
        with self.target_db.connection.cursor() as cur:
            cur.execute("SELECT to_regclass('internal.releases'), to_regclass('internal.release_cards')")
            if None in cur.fetchone():
                raise ReleaseMigrationError(
                    "The target database has no release tables. Deploy the Release Builder there first "
                    "(or run `showdown_bot database build_releases_tables --env prod`)."
                )

    def _source_release(self) -> dict:
        with self.source_db.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM internal.releases WHERE slug = %s AND retired_at IS NULL", (self.slug,))
            row = cur.fetchone()
        if not row:
            raise ReleaseMigrationError(f"No live release with slug '{self.slug}' in the source database.")
        return dict(row)

    def _source_owner_email(self, user_id: str) -> str:
        with self.source_db.connection.cursor() as cur:
            cur.execute("SELECT email FROM auth.users WHERE id::text = %s", (user_id,))
            row = cur.fetchone()
        if not row or not row[0]:
            raise ReleaseMigrationError(f"The release owner ({user_id}) has no email in the source auth.users.")
        return row[0]

    def _target_user_id(self, email: str) -> str:
        with self.target_db.connection.cursor() as cur:
            cur.execute("SELECT id::text FROM auth.users WHERE lower(email) = lower(%s)", (email,))
            rows = cur.fetchall()
        if len(rows) != 1:
            problem = 'no account' if not rows else f'{len(rows)} accounts'
            raise ReleaseMigrationError(f"Found {problem} for {email} in the target auth.users.")
        return rows[0][0]

    def _source_editions(self, release_id: str) -> list[EditionMigration]:
        """Live editions, oldest first, skipping ones the owner staged for removal. An edition with a
        working copy takes the copy's name, settings and cards."""
        with self.source_db.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT e.slug, COALESCE(d.id, e.id) AS content_id, COALESCE(d.name, e.name) AS name,
                       COALESCE(d.attributes, e.attributes) AS attributes, d.id IS NOT NULL AS from_working_copy
                  FROM internal.release_editions e
                  LEFT JOIN internal.release_editions d ON d.draft_of = e.id
                 WHERE e.release_id = %s AND e.draft_of IS NULL AND e.retired_at IS NULL AND NOT e.pending_removal
                 ORDER BY e.created_at
            """, (release_id,))
            editions = [dict(row) for row in cur.fetchall()]
            for edition in editions:
                cur.execute(f"""
                    SELECT {PostgresDB._RELEASE_CARD_COPY_COLUMNS} FROM internal.release_cards
                     WHERE edition_id = %s AND retired_at IS NULL ORDER BY {PostgresDB._RELEASE_CARD_NUMBER_ORDER}
                """, (edition['content_id'],))
                edition['cards'] = [dict(row) for row in cur.fetchall()]
        return [
            EditionMigration(
                name=edition['name'], slug=edition['slug'], attributes=edition['attributes'] or {},
                cards=edition['cards'], from_working_copy=edition['from_working_copy'],
            )
            for edition in editions
        ]

    def _existing_target_release_id(self, target_owner_id: str) -> Optional[str]:
        """The target release a previous run created, or None if the slug is free. Raises when the
        slug belongs to someone else, or when the earlier copy has since been published or retired."""
        with self.target_db.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT r.id::text, r.created_by, r.retired_at IS NOT NULL AS retired,
                       r.published_version > 0 OR EXISTS (
                           SELECT 1 FROM internal.release_editions e WHERE e.release_id = r.id AND e.published_at IS NOT NULL
                       ) AS published
                  FROM internal.releases r WHERE r.slug = %s
            """, (self.slug,))
            row = cur.fetchone()
        if not row:
            return None
        if row['created_by'] != target_owner_id:
            raise ReleaseMigrationError(f"Slug '{self.slug}' is already taken in the target by another user's release.")
        if row['retired']:
            raise ReleaseMigrationError(f"The target release '{self.slug}' was deleted (retired); its slug stays reserved.")
        if row['published']:
            raise ReleaseMigrationError(
                f"The target release '{self.slug}' has been published there. Make further changes in the target, "
                "since syncing could pull cards out from under teams holding them."
            )
        return row['id']

    # ---------------------------------------------------------------------
    # MARK: - APPLY
    # ---------------------------------------------------------------------

    def apply(self, plan: ReleaseMigrationPlan) -> tuple[str, list[str]]:
        """Write the plan to the target in one transaction. Returns (target release id, image paths
        left unreferenced by editions this sync removed). Those files are only reported, not deleted:
        local storage credentials may not point at the target's Supabase project."""
        db = self.target_db
        with db.transaction() as cur:
            release_id = self._upsert_release(cur, plan)
            kept_slugs = [edition.slug for edition in plan.editions]
            cur.execute("""
                SELECT id FROM internal.release_editions
                 WHERE release_id = %s AND draft_of IS NULL AND NOT (slug = ANY(%s))
            """, (release_id, kept_slugs))
            removed_ids = [str(uuid.UUID(str(row[0]))) for row in cur.fetchall()]
            orphaned_paths: list[str] = []
            if removed_ids:
                # uuid.UUID-validated literals, so safe for _delete_editions' trusted condition string
                orphaned_paths = db._delete_editions(cur, release_id, f"id IN ({', '.join(repr(i) for i in removed_ids)})")
            for edition in plan.editions:
                edition_id = self._upsert_edition(cur, release_id, edition)
                PostgresDB._upsert_release_cards(cur, edition_id, edition.cards)
        return release_id, orphaned_paths

    @staticmethod
    def _upsert_release(cur, plan: ReleaseMigrationPlan) -> str:
        fields = plan.release_fields
        if plan.is_update:
            set_clause = ', '.join(f"{key} = %s" for key in fields)
            cur.execute(
                f"UPDATE internal.releases SET {set_clause}, updated_at = NOW() WHERE id = %s",
                list(fields.values()) + [plan.target_release_id],
            )
            return plan.target_release_id
        columns = ', '.join(['created_by', 'slug'] + list(fields))
        placeholders = ', '.join(['%s'] * (2 + len(fields)))
        cur.execute(
            f"INSERT INTO internal.releases ({columns}) VALUES ({placeholders}) RETURNING id",
            [plan.target_owner_id, plan.slug] + list(fields.values()),
        )
        return str(cur.fetchone()[0])

    @staticmethod
    def _upsert_edition(cur, release_id: str, edition: EditionMigration) -> str:
        """Update the target edition with this slug, or create it. `cards_version` goes up so a
        Release Builder tab open on the old content can't save over the sync."""
        cur.execute("""
            UPDATE internal.release_editions
               SET name = %s, attributes = %s, cards_version = cards_version + 1, updated_at = NOW()
             WHERE release_id = %s AND slug = %s AND draft_of IS NULL AND retired_at IS NULL
            RETURNING id
        """, (edition.name, extras.Json(edition.attributes), release_id, edition.slug))
        row = cur.fetchone()
        if row:
            return str(row[0])
        cur.execute("""
            INSERT INTO internal.release_editions (release_id, name, attributes, slug)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (release_id, edition.name, extras.Json(edition.attributes), edition.slug))
        return str(cur.fetchone()[0])
