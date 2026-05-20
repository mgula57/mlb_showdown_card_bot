import traceback
from flask import Blueprint, g, jsonify, request
from .user_settings import require_auth
from ..core.database.postgres_db import PostgresDB

gallery_bp = Blueprint('gallery', __name__)


@gallery_bp.route('/user/gallery', methods=['GET'])
@require_auth
def get_gallery():
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        set_name = request.args.get('set_name') or None
        player_name = request.args.get('player_name') or None
        year = request.args.get('year') or None
        player_type = request.args.get('player_type') or None
        db = PostgresDB()
        gallery = db.get_user_gallery(
            g.user_id, limit=limit, offset=offset,
            set_name=set_name, player_name=player_name,
            year=year, player_type=player_type,
        )
        db.close_connection()
        return jsonify({'gallery': gallery, 'has_more': len(gallery) == limit}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@gallery_bp.route('/user/gallery/<int:gallery_id>', methods=['DELETE'])
@require_auth
def delete_gallery_card(gallery_id: int):
    try:
        db = PostgresDB()
        deleted = db.delete_user_gallery_card(g.user_id, gallery_id)
        db.close_connection()
        if deleted:
            return jsonify({'success': True}), 200
        return jsonify({'error': 'Card not found or access denied'}), 404
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
