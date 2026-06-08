from flask import Blueprint, request, jsonify

from ..core.database.postgres_db import PostgresDB

team_builder_bp = Blueprint('team_builder', __name__)

_ALLOWED_UPDATE_FIELDS = {'name', 'team_type', 'showdown_set', 'roster_size', 'bullpen_size', 'bench_multiplier', 'metadata'}


def _get_user_id() -> str | None:
    """Extract user_id from request context.

    Currently reads from the request body/args as a fallback while the 4.2
    auth branch (server-side JWT validation) is being merged. Once that
    middleware is in place, replace this with g.user_id populated by the
    auth decorator instead.
    """
    payload = request.get_json(silent=True) or {}
    return (
        payload.get('user_id')
        or request.args.get('user_id')
        or request.headers.get('X-User-Id')
    )


@team_builder_bp.route('/teams/builder', methods=['POST'])
def create_team():
    try:
        db = PostgresDB()
        payload = request.get_json() or {}
        user_id = _get_user_id()
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 401

        name = payload.get('name', '').strip()
        if not name:
            return jsonify({'error': 'name is required'}), 400

        team = db.create_team(
            user_id=user_id,
            name=name,
            showdown_set=payload.get('showdown_set', '2005'),
            team_type=payload.get('team_type', 'custom'),
            roster_size=int(payload.get('roster_size', 25)),
            bullpen_size=int(payload.get('bullpen_size', 7)),
            bench_multiplier=float(payload.get('bench_multiplier', 0.2)),
            metadata=payload.get('metadata'),
        )
        db.close_connection()

        if team is None:
            return jsonify({'error': 'Failed to create team'}), 500

        team = _serialize_team(team)
        return jsonify({'team': team}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@team_builder_bp.route('/teams/builder', methods=['GET'])
def list_teams():
    try:
        db = PostgresDB()
        user_id = _get_user_id()
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 401

        team_type = request.args.get('team_type')
        teams = db.list_teams_for_user(user_id=user_id, team_type=team_type)
        db.close_connection()

        return jsonify({'teams': [_serialize_team(t) for t in teams]})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@team_builder_bp.route('/teams/builder/<int:team_id>', methods=['GET'])
def get_team(team_id: int):
    try:
        db = PostgresDB()
        user_id = _get_user_id()
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 401

        team = db.get_team_with_slots(team_id=team_id, user_id=user_id)
        db.close_connection()

        if team is None:
            return jsonify({'error': 'Team not found'}), 404

        team = _serialize_team(team)
        return jsonify({'team': team})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@team_builder_bp.route('/teams/builder/<int:team_id>', methods=['PUT'])
def update_team(team_id: int):
    try:
        db = PostgresDB()
        payload = request.get_json() or {}
        user_id = _get_user_id()
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 401

        updates = {k: v for k, v in payload.items() if k in _ALLOWED_UPDATE_FIELDS}
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        ok = db.update_team(team_id=team_id, user_id=user_id, **updates)
        db.close_connection()

        if not ok:
            return jsonify({'error': 'Team not found or no changes made'}), 404

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@team_builder_bp.route('/teams/builder/<int:team_id>', methods=['DELETE'])
def delete_team(team_id: int):
    try:
        db = PostgresDB()
        user_id = _get_user_id()
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 401

        ok = db.delete_team(team_id=team_id, user_id=user_id)
        db.close_connection()

        if not ok:
            return jsonify({'error': 'Team not found'}), 404

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@team_builder_bp.route('/teams/builder/<int:team_id>/slots/<slot_key>', methods=['PUT'])
def upsert_slot(team_id: int, slot_key: str):
    try:
        db = PostgresDB()
        payload = request.get_json() or {}
        user_id = _get_user_id()
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 401

        card_source = payload.get('card_source')
        card_id = payload.get('card_id')
        card_snapshot = payload.get('card_snapshot') or {}

        if not card_source or not card_id:
            return jsonify({'error': 'card_source and card_id are required'}), 400
        if card_source not in ('bot', 'wotc'):
            return jsonify({'error': 'card_source must be bot or wotc'}), 400

        ok = db.upsert_team_slot(
            team_id=team_id,
            user_id=user_id,
            slot_key=slot_key,
            card_source=card_source,
            card_id=card_id,
            card_snapshot=card_snapshot,
        )
        db.close_connection()

        if not ok:
            return jsonify({'error': 'Team not found or access denied'}), 403

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@team_builder_bp.route('/teams/builder/<int:team_id>/slots/<slot_key>', methods=['DELETE'])
def delete_slot(team_id: int, slot_key: str):
    try:
        db = PostgresDB()
        user_id = _get_user_id()
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 401

        ok = db.delete_team_slot(team_id=team_id, user_id=user_id, slot_key=slot_key)
        db.close_connection()

        if not ok:
            return jsonify({'error': 'Slot not found'}), 404

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _serialize_team(team: dict) -> dict:
    """Convert datetime fields to ISO strings for JSON serialization."""
    result = dict(team)
    for key in ('created_at', 'updated_at'):
        if result.get(key) is not None and hasattr(result[key], 'isoformat'):
            result[key] = result[key].isoformat()
    if 'slots' in result:
        for slot in result['slots']:
            if slot.get('created_at') is not None and hasattr(slot['created_at'], 'isoformat'):
                slot['created_at'] = slot['created_at'].isoformat()
    return result
