import traceback
from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from ..core.database.postgres_db import PostgresDB
from ..core.set_builder.showdown_bot_set import AlgorithmPreviewRequest
from ..core.set_builder.wotc_set_profile import WotcSetProfile
from .user_settings import require_auth, optional_user_id

releases_bp = Blueprint('releases', __name__)


@releases_bp.route('/releases', methods=['GET'])
@require_auth
def get_releases():
    try:
        db = PostgresDB()
        releases = db.get_releases(g.user_id)
        db.close_connection()
        return jsonify(releases), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases', methods=['POST'])
@require_auth
def create_release():
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        if not payload.get('name'):
            return jsonify({'error': 'name is required'}), 400
        db = PostgresDB()
        release_id = db.create_release(g.user_id, payload)
        release = db.get_release(release_id, g.user_id)
        db.close_connection()
        return jsonify(release), 201
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>', methods=['GET'])
def get_release(release_id: str):
    try:
        user_id = optional_user_id()
        db = PostgresDB()
        release = db.get_release(release_id, user_id)
        db.close_connection()
        if release is None:
            return jsonify({'error': 'Release not found'}), 404
        return jsonify(release), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>', methods=['PUT'])
@require_auth
def update_release(release_id: str):
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        db = PostgresDB()
        updated = db.update_release(release_id, g.user_id, payload)
        if not updated:
            db.close_connection()
            return jsonify({'error': 'Release not found or not owned by user'}), 404
        release = db.get_release(release_id, g.user_id)
        db.close_connection()
        return jsonify(release), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>', methods=['DELETE'])
@require_auth
def delete_release(release_id: str):
    try:
        db = PostgresDB()
        deleted = db.delete_release(release_id, g.user_id)
        db.close_connection()
        if not deleted:
            return jsonify({'error': 'Release not found or not owned by user'}), 404
        return jsonify({'success': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/public', methods=['GET'])
def get_public_releases():
    try:
        limit = min(request.args.get('limit', 50, type=int), 200)
        offset = request.args.get('offset', 0, type=int)
        db = PostgresDB()
        releases = db.get_public_releases(limit=limit, offset=offset)
        db.close_connection()
        return jsonify(releases), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions', methods=['POST'])
@require_auth
def create_edition(release_id: str):
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        if not payload.get('name'):
            return jsonify({'error': 'name is required'}), 400
        db = PostgresDB()
        edition_id = db.create_edition(release_id, g.user_id, payload)
        if edition_id is None:
            db.close_connection()
            return jsonify({'error': 'Release not found or not owned by user'}), 404
        edition = db.get_edition(edition_id, g.user_id)
        db.close_connection()
        return jsonify(edition), 201
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>', methods=['GET'])
def get_edition(release_id: str, edition_id: str):
    try:
        user_id = optional_user_id()
        db = PostgresDB()
        edition = db.get_edition(edition_id, user_id)
        db.close_connection()
        if edition is None or edition['release_id'] != release_id:
            return jsonify({'error': 'Edition not found'}), 404
        return jsonify(edition), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>', methods=['PUT'])
@require_auth
def update_edition(release_id: str, edition_id: str):
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        db = PostgresDB()
        updated = db.update_edition(edition_id, g.user_id, payload)
        if not updated:
            db.close_connection()
            return jsonify({'error': 'Edition not found or not owned by user'}), 404
        edition = db.get_edition(edition_id, g.user_id)
        db.close_connection()
        return jsonify(edition), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>', methods=['DELETE'])
@require_auth
def delete_edition(release_id: str, edition_id: str):
    try:
        db = PostgresDB()
        deleted = db.delete_edition(edition_id, g.user_id)
        db.close_connection()
        if not deleted:
            return jsonify({'error': 'Edition not found or not owned by user'}), 404
        return jsonify({'success': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/algorithm/wotc_profiles', methods=['GET'])
def get_wotc_set_profiles():
    """Position counts and average points of each WOTC base set, used as Algorithm blueprints"""
    try:
        profiles = WotcSetProfile.load_all()
        return jsonify([profile.model_dump() for profile in profiles.values()]), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/algorithm/preview', methods=['POST'])
@require_auth
def preview_algorithm(release_id: str, edition_id: str):
    """Run ShowdownBotSet against the request config and return a preview player pool.
    Does not persist anything to the edition — the frontend commits the result via the
    existing PUT /editions/<edition_id> `cards` mechanism.

    Admins can pass `rerun_cards: true` to rebuild each selected card through the current
    `ShowdownPlayerCard` algorithm instead of returning the archived version."""
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400

        rerun_cards = bool(payload.pop('rerun_cards', False))
        if rerun_cards and not getattr(g, 'is_admin', False):
            return jsonify({'error': 'Admin access required to re-run cards'}), 403

        db = PostgresDB()
        edition = db.get_edition(edition_id, g.user_id)
        if edition is None or edition['release_id'] != release_id:
            db.close_connection()
            return jsonify({'error': 'Edition not found'}), 404

        try:
            algorithm_request = AlgorithmPreviewRequest(**payload)
            showdown_set = algorithm_request.to_showdown_bot_set()
        except ValidationError as exc:
            db.close_connection()
            return jsonify({'error': str(exc)}), 400

        players = showdown_set.build_preview_rows(db, rerun_cards=rerun_cards)
        db.close_connection()

        return jsonify({
            'players': players,
            'summary': {
                'requested_set_size': showdown_set.set_size,
                'actual_count': len(players),
                'warnings': showdown_set.warnings,
            },
        }), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
