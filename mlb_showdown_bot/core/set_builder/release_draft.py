"""
Release Builder drafts: once a release has been published, its owner edits private working copies
of its editions (`release_editions.draft_of`) instead of the live ones, so people browsing or
drafting from it never see a half-finished edit. Publishing folds the copies back in; this module
works out what changed and who it affects for the Review step, and drives start / discard / publish.
"""

from typing import Optional

from pydantic import BaseModel, PrivateAttr, computed_field

from ..database.postgres_db import PostgresDB


class CardChange(BaseModel):
    name: str
    detail: str
    # Saved teams holding the live card (removed and changed cards only)
    team_count: int = 0
    # The live release card, for counting those teams
    _release_card_id: Optional[str] = PrivateAttr(default=None)


class EditionChanges(BaseModel):
    """What publishing would change in one edition, comparing its working copy to the live edition."""

    # The edition being edited: the working copy, or a never-published edition itself
    edition_id: str
    name: str
    renamed_from: Optional[str] = None
    is_new: bool = False
    # The owner deleted this published edition; publishing retires it (every card counts as removed)
    is_removed: bool = False
    added: list[CardChange] = []
    removed: list[CardChange] = []
    changed: list[CardChange] = []
    renumbered: int = 0
    # Tags, cover picks and per-card style tweaks
    details_changed: int = 0
    settings_changed: bool = False

    @computed_field
    @property
    def has_changes(self) -> bool:
        return bool(
            self.is_new or self.is_removed or self.renamed_from or self.added or self.removed or self.changed
            or self.renumbered or self.details_changed or self.settings_changed
        )

    def summary(self) -> dict:
        """The compact record kept with the published version."""
        return {
            'name': self.name, 'renamed_from': self.renamed_from, 'is_new': self.is_new, 'is_removed': self.is_removed,
            'added': len(self.added), 'removed': len(self.removed), 'changed': len(self.changed),
            'renumbered': self.renumbered,
        }


class ReleaseChanges(BaseModel):
    editions: list[EditionChanges] = []
    # Distinct saved teams holding any removed / changed card
    removed_team_count: int = 0
    changed_team_count: int = 0

    @computed_field
    @property
    def has_changes(self) -> bool:
        return any(edition.has_changes for edition in self.editions)


def _card_detail(snapshot: dict) -> str:
    parts = [f"{snapshot.get('year') or ''} {snapshot.get('team_id') or ''}".strip()]
    if snapshot.get('points') is not None:
        parts.append(f"{snapshot['points']} pts")
    return ' · '.join(part for part in parts if part)


class ReleaseDraft:
    """A release's unpublished work, for its owner. `release` is a `PostgresDB.get_release` row."""

    def __init__(self, db: PostgresDB, release: dict, user_id: str) -> None:
        self.db = db
        self.release = release
        self.user_id = user_id

    @property
    def is_staged(self) -> bool:
        """Edits go through working copies once the release has been published."""
        return (self.release.get('published_version') or 0) > 0

    def working_edition_ids(self) -> list[str]:
        """The editions as the owner is building them: each one's working copy if it has one. Editions
        staged for removal are left out, since publishing retires them."""
        return [
            (edition.get('draft') or {}).get('id') or edition['id']
            for edition in self.release.get('editions') or [] if not edition.get('pending_removal')
        ]

    def changes(self) -> Optional[ReleaseChanges]:
        """What publishing would change, or None before the first publish (everything is new then)."""
        if not self.is_staged:
            return None
        editions = [self._edition_changes(edition) for edition in self.release.get('editions') or []]
        return self._with_team_counts([edition for edition in editions if edition is not None])

    def _edition_changes(self, summary: dict) -> Optional[EditionChanges]:
        draft_id = (summary.get('draft') or {}).get('id')
        if summary.get('pending_removal'):
            live = self.db.get_edition(summary['id'], self.user_id)
            if live is None:
                return None
            return EditionChanges(
                edition_id=live['id'], name=live['name'], is_removed=True,
                removed=[self._live_card_change(c, _card_detail(c['card_snapshot'])) for c in live['cards']],
            )
        if summary.get('published_at') is None:
            working = self.db.get_edition(summary['id'], self.user_id)
            if working is None:
                return None
            return EditionChanges(
                edition_id=working['id'], name=working['name'], is_new=True,
                added=[CardChange(name=c['card_snapshot'].get('name') or 'Unknown', detail=_card_detail(c['card_snapshot'])) for c in working['cards']],
            )
        if not draft_id:
            return EditionChanges(edition_id=summary['id'], name=summary['name'])
        live = self.db.get_edition(summary['id'], self.user_id)
        working = self.db.get_edition(draft_id, self.user_id)
        if live is None or working is None:
            return None
        return self._compare(live, working)

    def _compare(self, live: dict, working: dict) -> EditionChanges:
        live_cards = {c['source_card_id']: c for c in live['cards'] if c.get('source_card_id')}
        working_cards = {c['source_card_id']: c for c in working['cards'] if c.get('source_card_id')}
        changes = EditionChanges(
            edition_id=working['id'], name=working['name'],
            renamed_from=live['name'] if live['name'] != working['name'] else None,
            settings_changed=(live.get('attributes') or {}).get('style') != (working.get('attributes') or {}).get('style')
                or (live.get('attributes') or {}).get('numbering') != (working.get('attributes') or {}).get('numbering'),
        )
        for source_id, card in working_cards.items():
            snapshot = card['card_snapshot']
            before = live_cards.get(source_id)
            if before is None:
                changes.added.append(CardChange(name=snapshot.get('name') or 'Unknown', detail=_card_detail(snapshot)))
                continue
            if before['card_snapshot'] != snapshot:
                changes.changed.append(self._live_card_change(before, f"Was {_card_detail(before['card_snapshot'])}, now {_card_detail(snapshot)}"))
            if before.get('card_number') != card.get('card_number'):
                changes.renumbered += 1
            if any(before.get(key) != card.get(key) for key in ('tags', 'preview_rank', 'card_overrides')):
                changes.details_changed += 1
        for source_id, card in live_cards.items():
            if source_id not in working_cards:
                changes.removed.append(self._live_card_change(card, _card_detail(card['card_snapshot'])))
        return changes

    @staticmethod
    def _live_card_change(live_card: dict, detail: str) -> CardChange:
        change = CardChange(name=live_card['card_snapshot'].get('name') or 'Unknown', detail=detail)
        change._release_card_id = live_card['id']
        return change

    def _with_team_counts(self, editions: list[EditionChanges]) -> ReleaseChanges:
        removed = [change for edition in editions for change in edition.removed]
        changed = [change for edition in editions for change in edition.changed]
        per_card, _ = self.db.count_teams_holding_release_cards([c._release_card_id for c in removed + changed])
        for change in removed + changed:
            change.team_count = per_card.get(change._release_card_id, 0)
        _, removed_teams = self.db.count_teams_holding_release_cards([c._release_card_id for c in removed])
        _, changed_teams = self.db.count_teams_holding_release_cards([c._release_card_id for c in changed])
        return ReleaseChanges(editions=editions, removed_team_count=removed_teams, changed_team_count=changed_teams)
