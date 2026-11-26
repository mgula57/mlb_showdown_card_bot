"""The signed-in user's notifications (the header bell). Notifications are created by the routes whose
actions they report, through `core/notifications.Notifier`."""

import traceback

from flask import Blueprint, g, jsonify, request

from ..core.database.postgres_db import PostgresDB
from ..core.supabase.realtime_broadcast import RealtimeBroadcaster
from .comments import CommentRequest
from .user_settings import require_auth

notifications_bp = Blueprint('notifications', __name__)

_PAGE_SIZE = 20
# Enough for any one click in the panel
_MAX_IDS_PER_READ = 100


@notifications_bp.route('/notifications', methods=['GET'])
@require_auth
def get_notifications():
    """A page of notifications, newest first, plus the unread count. `cursor` is a previous page's `next_cursor`."""
    try:
        before, error = CommentRequest.cursor(request.args.get('cursor'))
        if error:
            return jsonify({'error': error}), 400
        with PostgresDB() as db:
            page = db.get_notifications(g.user_id, limit=_PAGE_SIZE, before=before)
            page['unread_count'] = db.count_unread_notifications(g.user_id)
        return jsonify(page), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@notifications_bp.route('/notifications/unread_count', methods=['GET'])
@require_auth
def get_unread_notification_count():
    """The bell's count, and the Realtime channel that pings when it changes (null when Realtime
    notifications aren't set up, so the bell only polls)."""
    try:
        with PostgresDB() as db:
            return jsonify({
                'unread_count': db.count_unread_notifications(g.user_id),
                'realtime_topic': RealtimeBroadcaster.notifications_topic(g.user_id),
            }), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@notifications_bp.route('/notifications/read', methods=['POST'])
@require_auth
def mark_notifications_read():
    """Mark the given `ids` read, or every notification when `ids` is left out. Returns the new unread count."""
    try:
        payload = request.get_json(silent=True) or {}
        ids = payload.get('ids') if isinstance(payload, dict) else None
        if ids is not None:
            if not isinstance(ids, list) or len(ids) > _MAX_IDS_PER_READ or not all(CommentRequest.is_uuid(i) for i in ids):
                return jsonify({'error': 'Invalid ids'}), 400
        with PostgresDB() as db:
            db.mark_notifications_read(g.user_id, ids)
            return jsonify({'unread_count': db.count_unread_notifications(g.user_id)}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
