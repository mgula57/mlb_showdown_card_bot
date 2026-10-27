"""
Release Builder review: the checklist an owner sees before publishing a release. Each check
reports a pass or a problem at one of three levels (blockers stop a publish), plus where in the
builder to fix it. Publishing re-runs the blocker checks server side so they can't be skipped.
"""

import traceback
from collections import Counter
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel

from ..card.images import ImageLibrary, ImageMatchType
from ..database.postgres_db import PostgresDB
from .image_match_classifier import ImageMatchCard, ImageMatchClassifier
from .release_images import EditionCardStyle, EditionImagePlan, EditionNumbering

_ACTIVE_JOB_STATUSES = {'queued', 'running'}
# How many names/numbers a detail line lists before summarizing the rest
_DETAIL_LIST_LIMIT = 4


class ReviewLevel(str, Enum):
    BLOCKER = 'blocker'
    CHECK = 'check'
    POLISH = 'polish'


class ReviewFixTarget(BaseModel):
    """Where the builder opens to fix an item: a step of `edition_id` (or the release's own details),
    with `image_status` pre-filtering the Images step."""

    step: Literal['pool', 'images', 'style', 'details']
    edition_id: Optional[str] = None
    image_status: Optional[Literal['missing', 'stale', 'failed']] = None


class ReviewItem(BaseModel):
    id: str
    level: ReviewLevel
    edition_id: Optional[str] = None
    title: str
    detail: Optional[str] = None
    passed: bool = False
    fix: Optional[ReviewFixTarget] = None

    @property
    def is_blocking(self) -> bool:
        return self.level == ReviewLevel.BLOCKER and not self.passed


def _plural(count: int, singular: str, plural: Optional[str] = None) -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def _listed(values: list[str]) -> str:
    """'A, B, C and 2 more'"""
    shown = values[:_DETAIL_LIST_LIMIT]
    rest = len(values) - len(shown)
    if rest > 0:
        return f"{', '.join(shown)} and {rest} more"
    return shown[0] if len(shown) == 1 else f"{', '.join(shown[:-1])} and {shown[-1]}"


class EditionReview:
    """Checks for one edition (a `PostgresDB.get_edition` row)."""

    def __init__(self, edition: dict, image_rows: list[dict], image_job: Optional[dict], photo_matches: Optional[dict[str, dict]]) -> None:
        self.edition = edition
        self.edition_id: str = edition['id']
        self.cards: list[dict] = edition.get('cards') or []
        self.image_rows = image_rows
        self.image_job = image_job
        # None when photo matches weren't checked (e.g. publishing, which only needs blockers)
        self.photo_matches = photo_matches

    def items(self) -> list[ReviewItem]:
        if not self.cards:
            return [self._item('empty', ReviewLevel.BLOCKER, 'This edition has no cards',
                               'Add cards to the player pool, or delete the edition.', fix='pool')]
        return [
            *self._image_items(),
            *self._photo_items(),
            *self._numbering_items(),
            self._duplicate_players_item(),
            *self._tags_items(),
            self._style_item(),
        ]

    def _item(self, id: str, level: ReviewLevel, title: str, detail: Optional[str] = None, passed: bool = False,
              fix: Optional[str] = None, image_status: Optional[str] = None) -> ReviewItem:
        return ReviewItem(
            id=f"{self.edition_id}:{id}", level=level, edition_id=self.edition_id, title=title, detail=detail,
            passed=passed, fix=ReviewFixTarget(step=fix, edition_id=self.edition_id, image_status=image_status) if fix else None,
        )

    def _image_items(self) -> list[ReviewItem]:
        job = self.image_job or {}
        if job.get('status') in _ACTIVE_JOB_STATUSES:
            done = (job.get('completed') or 0) + (job.get('failed') or 0)
            return [self._item('images_rendering', ReviewLevel.BLOCKER, 'Images are still rendering',
                               f"{done} of {job.get('total') or 0} done. You can publish once the render finishes.", fix='images')]

        counts = Counter(status['status'] for status in EditionImagePlan(self.edition).card_statuses(self.image_rows))
        problems = [
            ('missing', f"{_plural(counts['missing'], 'image')} not rendered", "These cards have no image yet."),
            ('stale', f"{_plural(counts['stale'], 'image')} out of date", "You changed these cards after they were rendered."),
            ('failed', f"{_plural(counts['failed'], 'image')} failed to render", "Retry them from the Images step."),
        ]
        items = [
            self._item(f'images_{status}', ReviewLevel.CHECK, title, detail, fix='images', image_status=status)
            for status, title, detail in problems if counts[status]
        ]
        return items or [self._item('images', ReviewLevel.CHECK, f"All {_plural(counts['rendered'], 'image')} rendered", passed=True)]

    def _photo_items(self) -> list[ReviewItem]:
        if self.photo_matches is None:
            return []
        missing = [
            card['card_snapshot'].get('name') or 'Unknown'
            for card in self.cards
            if (self.photo_matches.get(str((card.get('card_snapshot') or {}).get('id'))) or {}).get('image_match_type') == ImageMatchType.NO_MATCH.value
        ]
        if not missing:
            return [self._item('photos', ReviewLevel.CHECK, 'Every card has a player photo', passed=True)]
        return [self._item('photos', ReviewLevel.CHECK, f"{_plural(len(missing), 'card')} with no player photo",
                           f"{_listed(missing)} will print with the silhouette.", fix='images')]

    def _numbering_items(self) -> list[ReviewItem]:
        numbering = EditionNumbering.from_attributes(self.edition.get('attributes'))
        if numbering.mode == 'none':
            return []
        numbers = [card['card_number'] for card in self.cards if card.get('card_number') is not None]
        unnumbered = len(self.cards) - len(numbers)
        items = []
        if unnumbered:
            items.append(self._item('unnumbered', ReviewLevel.CHECK, f"{_plural(unnumbered, 'card')} with no number",
                                    'Renumber the pool or number them by hand.', fix='pool'))
        gaps = sorted(set(range(1, max(numbers, default=0) + 1)) - set(numbers))
        if gaps:
            items.append(self._item('number_gaps', ReviewLevel.CHECK, f"Numbering skips {_plural(len(gaps), 'number')}",
                                    f"Missing {_listed([str(n) for n in gaps])}.", fix='pool'))
        return items or [self._item('numbering', ReviewLevel.CHECK, f"Every card is numbered, 1–{len(self.cards)}, no gaps", passed=True)]

    def _duplicate_players_item(self) -> ReviewItem:
        names: dict[str, str] = {}
        counts: Counter = Counter()
        for card in self.cards:
            snapshot = card.get('card_snapshot') or {}
            if not snapshot.get('bref_id'):
                continue
            key = f"{snapshot['bref_id']}-{snapshot.get('player_type_override') or ''}"
            counts[key] += 1
            names[key] = snapshot.get('name') or snapshot['bref_id']
        repeated = [names[key] for key, count in counts.items() if count > 1]
        if not repeated:
            return self._item('duplicates', ReviewLevel.CHECK, 'No player appears twice', passed=True)
        one = len(repeated) == 1
        return self._item('duplicates', ReviewLevel.CHECK, f"{_plural(len(repeated), 'player')} {'appears' if one else 'appear'} more than once",
                          f"{_listed(repeated)} {'has' if one else 'have'} more than one card in this edition.", fix='pool')

    def _tags_items(self) -> list[ReviewItem]:
        tags = Counter(tag for card in self.cards for tag in card.get('tags') or [])
        if not tags:
            return []
        summary = ' · '.join(f"{count} {tag}" for tag, count in tags.most_common())
        return [self._item('tags', ReviewLevel.POLISH, f"Tagged: {summary}", passed=True)]

    def _style_item(self) -> ReviewItem:
        if EditionCardStyle.from_attributes(self.edition.get('attributes')) == EditionCardStyle():
            return self._item('style', ReviewLevel.POLISH, 'Card style is the default',
                              'Fine if you meant it. Change it to give the edition its own look.', fix='style')
        return self._item('style', ReviewLevel.POLISH, 'Card style set', passed=True)


class ReleaseReview:
    """The full checklist for a release the user owns: each edition's checks, then the release's own."""

    def __init__(self, db: PostgresDB, release: dict, user_id: str, image_libraries: Optional[list[ImageLibrary]] = None) -> None:
        self.db = db
        self.release = release
        self.user_id = user_id
        # Photo checks search these libraries; None skips them (they can read Google Drive)
        self.image_libraries = image_libraries

    def run(self) -> list[ReviewItem]:
        editions = [
            edition for edition in (self.db.get_edition(e['id'], self.user_id) for e in self.release.get('editions') or [])
            if edition is not None
        ]
        photo_matches = self._photo_matches(editions)
        items: list[ReviewItem] = []
        for edition in editions:
            items.extend(EditionReview(
                edition,
                image_rows=self.db.get_release_card_images(edition['id']),
                image_job=self.db.get_latest_release_image_job(edition['id']),
                photo_matches=photo_matches,
            ).items())
        items.extend(self._release_items(editions))
        return items

    def _photo_matches(self, editions: list[dict]) -> Optional[dict[str, dict]]:
        if self.image_libraries is None:
            return None
        cards = {
            card.id: card for edition in editions for rc in edition.get('cards') or []
            if (card := ImageMatchCard.from_snapshot(rc.get('card_snapshot') or {}))
        }
        try:
            return ImageMatchClassifier(self.image_libraries).classify(list(cards.values()))['matches']
        except Exception:
            # A Drive hiccup drops the photo check rather than the whole review
            traceback.print_exc()
            return None

    def _release_items(self, editions: list[dict]) -> list[ReviewItem]:
        items = []
        if not editions:
            items.append(ReviewItem(id='no_editions', level=ReviewLevel.BLOCKER, title='This release has no editions',
                                    detail='Add an edition and fill its player pool first.'))
        if not (self.release.get('description') or '').strip():
            items.append(ReviewItem(id='description', level=ReviewLevel.POLISH, title='No description',
                                    detail='It shows under the name on the release list.', fix=ReviewFixTarget(step='details')))
        picked = sum(1 for edition in editions for card in edition.get('cards') or [] if card.get('preview_rank'))
        if picked:
            items.append(ReviewItem(id='cover_cards', level=ReviewLevel.POLISH, passed=True,
                                    title=f"You picked {_plural(picked, 'cover card')}"))
        elif any(edition.get('cards') for edition in editions):
            items.append(ReviewItem(id='cover_cards', level=ReviewLevel.POLISH, title='Cover cards picked for you',
                                    detail="The release tile shows the highest-point cards. Pick your own from a card's image.",
                                    fix=ReviewFixTarget(step='images', edition_id=editions[0]['id'])))
        return items
