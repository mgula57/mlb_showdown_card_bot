import traceback
from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from ..core.database.postgres_db import PostgresDB
from ..core.card.showdown_player_card import ShowdownPlayerCard
from ..core.set_builder.showdown_bot_set import AlgorithmPreviewRequest
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

        showdown_set.build_set_player_list()

        final_players = showdown_set.final_players or []
        set_numbers_by_id = {p.id: p.set_number for p in final_players}
        ids = list(set_numbers_by_id.keys())

        players = []
        if ids:
            raw_rows = db.fetch_card_list({'id': ids, 'showdown_set': showdown_set.showdown_sets, 'limit': len(ids)})
            for row in raw_rows:
                row['algorithm_set_number'] = set_numbers_by_id.get(row.get('id'))
                players.append(row)
            players.sort(key=lambda r: r.get('algorithm_set_number') or 0)

        if rerun_cards and players:
            showdown_set.warnings.extend(_rerun_preview_cards(db, players))

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


def _rerun_preview_cards(db: PostgresDB, players: list[dict]) -> list[str]:
    """Rebuild each preview row's archived card through the current algorithm, overwriting the
    row's card-derived columns in place. Rows that fail keep their archived card. Returns warnings."""
    archived_cards = db.fetch_cards_for_roster_slots(
        [{'card_id': row['card_id'], 'card_source': 'BOT'} for row in players if row.get('card_id')]
    )
    failed_names: list[str] = []
    changed_count = 0
    for row in players:
        archived = archived_cards.get(str(row.get('card_id')))
        if archived is None:
            failed_names.append(row.get('name') or row.get('id'))
            continue
        try:
            rebuilt = ShowdownPlayerCard.rebuilt_from_card_data(archived.as_json())
        except Exception:
            traceback.print_exc()
            failed_names.append(row.get('name') or row.get('id'))
            continue

        points_diff = (rebuilt.points or 0) - (row.get('points') or 0)
        if points_diff:
            changed_count += 1
        if row.get('points_change_yoy') is not None:
            row['points_change_yoy'] += points_diff
        row.update(rebuilt.card_bot_columns())

    warnings = [f"Re-ran {len(players) - len(failed_names)} cards through the current algorithm ({changed_count} changed points)."]
    if failed_names:
        warnings.append(f"Could not re-run {len(failed_names)} cards, kept archived versions: {', '.join(failed_names)}")
    return warnings
