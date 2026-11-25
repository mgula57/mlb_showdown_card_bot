"""In-app notifications for signed-in users: what other people did to their comments and things.

Routes call a `Notifier` after the action they notify about has been saved. Notifying is best-effort:
a failure is logged and never fails the request. Nobody is notified about their own actions. The
frontend words each `NotificationKind` (`frontend/src/api/notifications.ts`), so adding a kind means
adding it here and there.
"""

import traceback
from enum import Enum
from functools import wraps

from ..database.postgres_db import PostgresDB


class NotificationKind(str, Enum):
    # Someone replied to your comment
    COMMENT_REPLY = 'comment_reply'
    # Someone commented on your release or team (a reply in one of its threads too)
    SUBJECT_COMMENT = 'subject_comment'
    # Someone remixed your release
    RELEASE_REMIX = 'release_remix'


def _best_effort(method):
    @wraps(method)
    def wrapped(*args, **kwargs) -> None:
        try:
            method(*args, **kwargs)
        except Exception:
            traceback.print_exc()
    return wrapped


class Notifier:
    """Records notifications through an open `PostgresDB`."""

    def __init__(self, db: PostgresDB) -> None:
        self.db = db

    @_best_effort
    def comment_posted(self, comment: dict, owner_id: str | None) -> None:
        """A comment (as `PostgresDB.create_comment` returns it) on a subject `owner_id` owns. The person
        it replied to hears about it as a reply; the owner hears about it once, unless it replied to them."""
        recipients: dict[str, NotificationKind] = {}
        if comment.get('parent_id'):
            reply_target = self.db.get_comment_reply_target(comment['id'])
            if reply_target:
                recipients[reply_target] = NotificationKind.COMMENT_REPLY
        if owner_id:
            recipients.setdefault(owner_id, NotificationKind.SUBJECT_COMMENT)
        self._send(comment['user_id'], comment['subject_type'], comment['subject_id'], recipients, comment_id=comment['id'])

    @_best_effort
    def release_remixed(self, source_release: dict, remixer_id: str) -> None:
        """`remixer_id` started a remix of `source_release`. Points at the source, since the remix is
        the remixer's own until they publish it."""
        owner_id = source_release.get('created_by')
        if owner_id:
            self._send(remixer_id, 'release', str(source_release['id']), {owner_id: NotificationKind.RELEASE_REMIX})

    def _send(self, actor_id: str, subject_type: str, subject_id: str, recipients: dict[str, NotificationKind],
              comment_id: str | None = None) -> None:
        self.db.create_notifications([
            {
                'user_id': user_id, 'kind': kind.value, 'actor_id': actor_id,
                'subject_type': subject_type, 'subject_id': subject_id, 'comment_id': comment_id,
            }
            for user_id, kind in recipients.items() if user_id != actor_id
        ])
