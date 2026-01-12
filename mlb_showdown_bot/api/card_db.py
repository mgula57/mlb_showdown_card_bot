from flask import Blueprint, request, jsonify
from ..core.card.showdown_player_card import ShowdownPlayerCard
from ..core.database.postgres_db import PostgresDB

card_db_bp = Blueprint('card_data', __name__)

@card_db_bp.route('/cards/search', methods=["POST", "GET"])
def fetch_card_list():
    """Fetch card data from the database"""
    try:
        db = PostgresDB(is_archive=True)

        # Get query parameters
        payload = request.get_json() or {}
        card_data = db.fetch_card_list(filters = payload)
        db.close_connection()

        return jsonify(card_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@card_db_bp.route('/teams/data', methods=["GET"])
def fetch_team_data():
    """Fetch team data from the database"""
    try:
        db = PostgresDB(is_archive=True)

        team_data = db.fetch_team_data()
        db.close_connection()

        return jsonify(team_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@card_db_bp.route('/cards/card', methods=["GET"])
def fetch_card():
    """Fetch a single card by its ID"""
    try:
        db = PostgresDB(is_archive=True)
        id = request.args.get('id')
        card = db.fetch_single_card(id)
        db.close_connection()

        if card is None:
            return jsonify({'error': 'Card not found'}), 404

        return jsonify({'card': card.as_json()})

    except Exception as e:
        return jsonify({'error': str(e)}), 500