import re
import traceback
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import ClassVar

from flask import Blueprint, g, jsonify, request

from ..core.database.postgres_db import PostgresDB
from .releases import _visible_published_release
from .user_settings import require_auth, optional_user_id
from .utils.profanity_filter import ProfanityFilter
from .utils.rate_limiter import RateLimiter

comments_bp = Blueprint('comments', __name__)

COMMENT_MAX_LENGTH = 1000
_PAGE_SIZE = 20
_REPLIES_PAGE_SIZE = 50
# Enough for a back-and-forth, not for flooding a thread
_post_limiter = RateLimiter(max_events=5, window_seconds=60)


# ------------------------------------------------------------------------
# MARK: - SUBJECTS
# ------------------------------------------------------------------------

class CommentSubject(ABC):
    """Something people can comment on. Each kind decides who can open it, whether it's taking comments,
    and who owns it (owners can remove anyone's comment on it). Adding comments to a new feature means
    adding a subclass here and to `COMMENT_SUBJECTS`."""

    subject_type: ClassVar[str]

    def __init__(self, record: dict) -> None:
        self.record = record

    @classmethod
    @abstractmethod
    def load(cls, db: PostgresDB, subject_id: str, viewer_id: str | None) -> 'CommentSubject | None':
        """The subject if this viewer can open it, else None."""

    @property
    @abstractmethod
    def owner_id(self) -> str | None: ...

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Whether its comments show and new ones can be posted."""

    def can_moderate(self, user_id: str, is_admin: bool) -> bool:
        return is_admin or (self.owner_id is not None and user_id == self.owner_id)


class ReleaseCommentSubject(CommentSubject):
    """A published release that's listed or link-only, while its owner allows comments. A private release
    only its owner can open, so there's no one to talk to."""

    subject_type = 'release'

    @classmethod
    def load(cls, db: PostgresDB, subject_id: str, viewer_id: str | None) -> 'ReleaseCommentSubject | None':
        release = _visible_published_release(db, subject_id, viewer_id)
        return cls(release) if release else None

    @property
    def owner_id(self) -> str | None:
        return self.record.get('created_by')

    @property
    def is_open(self) -> bool:
        return self.record.get('visibility') != 'private' and bool(self.record.get('allow_comments', True))


class TeamCommentSubject(CommentSubject):
    """A saved team on Browse: a user's public team or an official one. League teams are run from their league."""

    subject_type = 'team'

    @classmethod
    def load(cls, db: PostgresDB, subject_id: str, viewer_id: str | None) -> 'TeamCommentSubject | None':
        team = db.get_team(subject_id, viewer_id)
        return cls(team) if team else None

    @property
    def owner_id(self) -> str | None:
        return self.record.get('user_id')

    @property
    def is_open(self) -> bool:
        source = self.record.get('source')
        return source != 'league' and (bool(self.record.get('is_public')) or source == 'official')


COMMENT_SUBJECTS: dict[str, type[CommentSubject]] = {
    subject.subject_type: subject for subject in (ReleaseCommentSubject, TeamCommentSubject)
}
assert set(COMMENT_SUBJECTS) == set(PostgresDB.COMMENT_SUBJECT_TYPES)


# ------------------------------------------------------------------------
# MARK: - REQUEST PARSING
# ------------------------------------------------------------------------

class CommentRequest:
    """Validation for comment ids, page cursors and bodies. Each parser returns (value, error message)."""

    @staticmethod
    def is_uuid(value: str | None) -> bool:
        try:
            uuid.UUID(str(value))
            return True
        except (ValueError, TypeError):
            return False

    @classmethod
    def cursor(cls, raw: str | None) -> tuple[tuple[str, str] | None, str | None]:
        """A `next_cursor` from a previous page ("<created_at>|<id>")."""
        if not raw:
            return None, None
        created_at, _, comment_id = raw.partition('|')
        try:
            datetime.fromisoformat(created_at)
        except ValueError:
            return None, 'Invalid cursor'
        if not cls.is_uuid(comment_id):
            return None, 'Invalid cursor'
        return (created_at, comment_id), None

    @staticmethod
    def body(raw) -> tuple[str | None, str | None]:
        if not isinstance(raw, str):
            return None, 'Write a comment first.'
        # Keep paragraph breaks, not walls of blank lines
        body = re.sub(r'\n{3,}', '\n\n', raw.replace('\r\n', '\n')).strip()
        if not body:
            return None, 'Write a comment first.'
        if len(body) > COMMENT_MAX_LENGTH:
            return None, f'Comments can be up to {COMMENT_MAX_LENGTH} characters.'
        if ProfanityFilter.contains_profanity(body):
            return None, "That comment has language that isn't allowed. Edit it and try again."
        return body, None


def _load_subject(db: PostgresDB, subject_type: str, subject_id: str, viewer_id: str | None) -> CommentSubject | None:
    subject_class = COMMENT_SUBJECTS.get(subject_type)
    if subject_class is None or not CommentRequest.is_uuid(subject_id):
        return None
    return subject_class.load(db, subject_id, viewer_id)


_CLOSED_RESPONSE = {'enabled': False, 'comments': [], 'next_cursor': None, 'total': 0}


# ------------------------------------------------------------------------
# MARK: - ROUTES
# ------------------------------------------------------------------------

@comments_bp.route('/comments/<subject_type>/<subject_id>', methods=['GET'])
def get_comments(subject_type: str, subject_id: str):
    """A page of top-level comments with their first replies. `enabled` is False when the subject isn't
    taking comments (e.g. its owner turned them off), and no comments come back."""
    try:
        before, error = CommentRequest.cursor(request.args.get('cursor'))
        if error:
            return jsonify({'error': error}), 400
        with PostgresDB() as db:
            subject = _load_subject(db, subject_type, subject_id, optional_user_id())
            if subject is None:
                return jsonify({'error': 'Not found'}), 404
            if not subject.is_open:
                return jsonify(_CLOSED_RESPONSE), 200
            page = db.get_comments(subject_type, subject_id, limit=_PAGE_SIZE, before=before)
        return jsonify({'enabled': True, **page}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@comments_bp.route('/comments/replies/<comment_id>', methods=['GET'])
def get_comment_replies(comment_id: str):
    """The rest of a thread: its replies after `cursor` (the last one already shown), oldest first."""
    try:
        if not CommentRequest.is_uuid(comment_id):
            return jsonify({'error': 'Comment not found'}), 404
        after, error = CommentRequest.cursor(request.args.get('cursor'))
        if error:
            return jsonify({'error': error}), 400
        with PostgresDB() as db:
            # A deleted top-level comment can still have live replies
            parent = db.get_comment(comment_id, include_deleted=True)
            if parent is None or parent['parent_id']:
                return jsonify({'error': 'Comment not found'}), 404
            subject = _load_subject(db, parent['subject_type'], parent['subject_id'], optional_user_id())
            if subject is None or not subject.is_open:
                return jsonify({'error': 'Comment not found'}), 404
            page = db.get_comment_replies(comment_id, after=after, limit=_REPLIES_PAGE_SIZE)
        return jsonify(page), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@comments_bp.route('/comments/<subject_type>/<subject_id>', methods=['POST'])
@require_auth
def create_comment(subject_type: str, subject_id: str):
    """Post a comment, or a reply with `parent_id` (any comment in the thread; replies stay one level deep)."""
    try:
        payload = request.get_json(silent=True) or {}
        body, error = CommentRequest.body(payload.get('body'))
        if error:
            return jsonify({'error': error}), 400
        parent_id = payload.get('parent_id')
        if parent_id is not None and not CommentRequest.is_uuid(parent_id):
            return jsonify({'error': 'That comment is no longer there.'}), 404
        with PostgresDB() as db:
            subject = _load_subject(db, subject_type, subject_id, g.user_id)
            if subject is None:
                return jsonify({'error': 'Not found'}), 404
            if not subject.is_open:
                return jsonify({'error': 'Comments are turned off here.'}), 403
            # Checked last, so a rejected comment doesn't use up the allowance
            if not _post_limiter.allow(g.user_id):
                return jsonify({'error': "You're commenting fast. Wait a minute and try again."}), 429
            comment = db.create_comment(subject_type, subject_id, g.user_id, body, parent_id)
        if comment is None:
            return jsonify({'error': 'That comment is no longer there.'}), 404
        return jsonify(comment), 201
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@comments_bp.route('/comments/<comment_id>', methods=['DELETE'])
@require_auth
def delete_comment(comment_id: str):
    """Its author, the subject's owner or an admin can delete a comment."""
    try:
        if not CommentRequest.is_uuid(comment_id):
            return jsonify({'error': 'Comment not found'}), 404
        with PostgresDB() as db:
            comment = db.get_comment(comment_id)
            if comment is None:
                return jsonify({'error': 'Comment not found'}), 404
            is_author = comment['user_id'] == g.user_id
            if not is_author:
                subject = _load_subject(db, comment['subject_type'], comment['subject_id'], g.user_id)
                if subject is None or not subject.can_moderate(g.user_id, g.is_admin):
                    return jsonify({'error': "You can't delete that comment."}), 403
            db.delete_comment(comment_id, g.user_id)
        return jsonify({'deleted': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
