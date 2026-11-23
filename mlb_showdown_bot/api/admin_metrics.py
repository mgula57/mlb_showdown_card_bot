"""Admin-only analytics for the `/admin` dashboard: usage across features, accounts and
adoption, Card Builder failures and card trends, and per-user activity. Read-only, gated by
the admin allowlist (`require_admin`). Queries live in `core/database/admin_metrics.py`.

Payloads are cached for a few minutes per (view, period) since several scan the build logs;
`?refresh=1` skips the cache.
"""

import traceback
from typing import Callable

from flask import Blueprint, jsonify, request

from ..core.database.admin_metrics import AdminMetrics, clamp_period_days
from ..core.database.postgres_db import PostgresDB
from ..core.utils.ttl_cache import TTLCache
from .user_settings import require_admin

admin_metrics_bp = Blueprint('admin_metrics', __name__)

_metrics_cache: TTLCache[dict] = TTLCache(ttl_seconds=5 * 60, max_size=100)


def _respond(view: str, build: Callable[[AdminMetrics], dict | None], cache_suffix: str = ''):
    days = clamp_period_days(request.args.get('days'))
    cache_key = f"{view}:{days}:{cache_suffix}"
    if request.args.get('refresh') != '1':
        cached = _metrics_cache.get(cache_key)
        if cached is not None:
            return jsonify(cached), 200
    try:
        with PostgresDB() as db:
            payload = build(AdminMetrics(db, days=days))
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f"Couldn't load {view} metrics: {e}"}), 500
    if payload is None:
        return jsonify({'error': 'Not found'}), 404
    _metrics_cache.set(cache_key, payload)
    return jsonify(payload), 200


@admin_metrics_bp.route('/admin/metrics/overview', methods=['GET'])
@require_admin
def admin_metrics_overview():
    return _respond('overview', lambda m: m.overview())


@admin_metrics_bp.route('/admin/metrics/failures', methods=['GET'])
@require_admin
def admin_metrics_failures():
    return _respond('failures', lambda m: m.failures())


@admin_metrics_bp.route('/admin/metrics/card-trends', methods=['GET'])
@require_admin
def admin_metrics_card_trends():
    return _respond('card-trends', lambda m: m.card_trends())


@admin_metrics_bp.route('/admin/metrics/users', methods=['GET'])
@require_admin
def admin_metrics_users():
    return _respond('users', lambda m: m.users())


@admin_metrics_bp.route('/admin/metrics/users/<user_id>', methods=['GET'])
@require_admin
def admin_metrics_user_detail(user_id: str):
    return _respond('user', lambda m: m.user_detail(user_id), cache_suffix=user_id)
