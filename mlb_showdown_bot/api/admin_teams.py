import traceback

from flask import Blueprint, g, jsonify, request

from ..core.database.postgres_db import PostgresDB
from ..core.card.team_builder.team import TeamSource, DEFAULT_LINEUP_NAME
from .user_settings import require_admin
from .user_teams import _collections_cache

admin_teams_bp = Blueprint('admin_teams', __name__)


def _bust_collections_cache() -> None:
    _collections_cache.clear()


@admin_teams_bp.route('/admin/collections', methods=['GET'])
@require_admin
def list_collections():
    """Every collection, visible or not (the public list lives at /teams/collections)."""
    try:
        with PostgresDB() as db:
            collections = db.get_team_collections(include_hidden=True)
        return jsonify(collections), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@admin_teams_bp.route('/admin/collections', methods=['POST'])
@require_admin
def upsert_collection():
    """Create or update a collection. Body: {slug, title, description?, cover_emoji?,
    sort_index?, is_visible?}."""
    try:
        payload = request.get_json(silent=True) or {}
        slug = (payload.get('slug') or '').strip().lower()
        if not slug or not payload.get('title'):
            return jsonify({'error': 'slug and title are required'}), 400
        if not slug.replace('-', '').replace('_', '').isalnum():
            return jsonify({'error': 'slug must be alphanumeric with dashes/underscores'}), 400
        with PostgresDB() as db:
            collection = db.upsert_team_collection(
                slug,
                title=payload.get('title'),
                description=payload.get('description'),
                cover_emoji=payload.get('cover_emoji'),
                sort_index=payload.get('sort_index'),
                is_visible=payload.get('is_visible'),
            )
        _bust_collections_cache()
        return jsonify(collection), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@admin_teams_bp.route('/admin/collections/<slug>', methods=['DELETE'])
@require_admin
def delete_collection(slug: str):
    try:
        with PostgresDB() as db:
            result = db.delete_team_collection(slug)
        if result == 'in_use':
            return jsonify({'error': 'Collection still has teams — move or unpublish them first'}), 409
        if result is None:
            return jsonify({'error': 'Collection not found'}), 404
        _bust_collections_cache()
        return jsonify({'success': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


def _copy_roster_and_lineups(team_row: dict) -> tuple[list[dict], list[dict]]:
    """Roster slots (marked IMPORTED, draft history dropped) + user-created lineups from a
    fetched team row, ready to hand to admin_upsert_team."""
    roster = [
        {
            'card_id': s['card_id'],
            'card_source': s['card_source'],
            'roster_position': s['roster_position'],
            'draft_order': None,
            'pick_source': 'IMPORTED',
        }
        for s in (team_row.get('roster') or [])
    ]
    lineups = [
        {'name': ln['name'], 'slots': ln.get('slots') or []}
        for ln in (team_row.get('lineups') or [])
        if ln.get('name') != DEFAULT_LINEUP_NAME
    ]
    return roster, lineups


@admin_teams_bp.route('/admin/teams/publish', methods=['POST'])
@require_admin
def publish_team():
    """Deep-copy a team into a new admin-owned ('official', public) row inside a collection.

    Body: {source_team_id, collection_slug, subtitle?, credit?, collection_sort_index?,
    strategy_deck?}. The source team is left untouched, so the admin keeps their working copy.
    """
    try:
        payload = request.get_json(silent=True) or {}
        source_team_id = payload.get('source_team_id')
        collection_slug = (payload.get('collection_slug') or '').strip().lower() or None
        if not source_team_id:
            return jsonify({'error': 'source_team_id is required'}), 400

        with PostgresDB() as db:
            source = db.get_team(source_team_id, g.user_id)
            if source is None:
                return jsonify({'error': 'Source team not found'}), 404
            # Re-publishing the same working copy overwrites its existing curated row rather
            # than spawning a duplicate.
            existing_id = db.find_published_team_id(source_team_id)
            if collection_slug and not any(
                c['slug'] == collection_slug for c in db.get_team_collections(include_hidden=True)
            ):
                return jsonify({'error': f"Unknown collection '{collection_slug}'"}), 400

            roster, lineups = _copy_roster_and_lineups(source)
            db_payload = {
                'name': source['name'],
                'abbreviation': source['abbreviation'],
                'primary_color': source.get('primary_color'),
                'secondary_color': source.get('secondary_color'),
                'source': TeamSource.OFFICIAL.value,
                'is_public': True,
                'pts_limit': source.get('pts_limit'),
                'roster_size': source.get('roster_size'),
                'min_bench': source.get('min_bench'),
                'min_bullpen': source.get('min_bullpen'),
                'num_starters': source.get('num_starters'),
                'bench_pts_multiplier': source.get('bench_pts_multiplier'),
                'allowed_sets': source.get('allowed_sets') or [],
                'allowed_sets_by_source': source.get('allowed_sets_by_source') or {},
                'allowed_card_sources': source.get('allowed_card_sources') or [],
                'collection_slug': collection_slug,
                'subtitle': payload.get('subtitle') or None,
                'credit': payload.get('credit') or None,
                'collection_sort_index': payload.get('collection_sort_index'),
                'strategy_deck': payload.get('strategy_deck') or source.get('strategy_deck') or {},
                'published_by': g.user_id,
                'origin_published_from': source_team_id,
                'roster': roster,
                'lineups': lineups,
            }
            if existing_id:
                db_payload['team_id'] = existing_id
            new_id = db.admin_upsert_team(db_payload)
            team = db.get_team(new_id, g.user_id)
        _bust_collections_cache()
        return jsonify(team), 201
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@admin_teams_bp.route('/admin/teams/<team_id>', methods=['PUT'])
@require_admin
def admin_update_team(team_id: str):
    """Update a curated team's metadata (and optionally roster/lineups) with no owner check."""
    try:
        payload = request.get_json(silent=True) or {}
        if 'collection_slug' in payload and payload['collection_slug']:
            payload['collection_slug'] = payload['collection_slug'].strip().lower()
        with PostgresDB() as db:
            ok = db.admin_update_team(team_id, payload)
            if not ok:
                return jsonify({'error': 'Team not found'}), 404
            team = db.get_team(team_id, g.user_id)
        _bust_collections_cache()
        return jsonify(team), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@admin_teams_bp.route('/admin/teams/<team_id>', methods=['DELETE'])
@require_admin
def admin_delete_team(team_id: str):
    """Unpublish: delete the curated team row (the admin's working copy is a separate row)."""
    try:
        with PostgresDB() as db:
            ok = db.admin_delete_team(team_id)
        if not ok:
            return jsonify({'error': 'Team not found'}), 404
        _bust_collections_cache()
        return jsonify({'success': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
