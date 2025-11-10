from flask import Blueprint, jsonify
from ..core.card.showdown_player_card import ShowdownPlayerCard
from ..core.database.postgres_db import PostgresDB

feature_status_bp = Blueprint('feature_status', __name__)

@feature_status_bp.route('/feature_status', methods=["GET"])
def fetch_feature_statuses():
    """Fetch feature statuses from the database"""
    try:
        db = PostgresDB()

        # Check feature status
        feature_status = db.get_feature_statuses()
        
        return jsonify(feature_status or {}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
