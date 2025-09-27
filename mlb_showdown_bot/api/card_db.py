from flask import Blueprint, request, jsonify
from ..core.card.showdown_player_card import ShowdownPlayerCard
from ..core.database.postgres_db import PostgresDB

cards_bp = Blueprint('card_data', __name__)

@cards_bp.route('/cards/data', methods=["POST", "GET"])
def fetch_card_data():
    """Fetch card data from the database"""
    try:
        db = PostgresDB(is_archive=True)

        # Get query parameters
        payload = request.get_json() or {}
        card_data = db.fetch_card_data(filters = payload)
        db.close_connection()

        return jsonify(card_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500