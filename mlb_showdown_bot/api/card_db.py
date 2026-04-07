from pprint import pprint
import os
import time
from flask import Blueprint, request, jsonify

from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard, Team
from ..core.database.postgres_db import PostgresDB

card_db_bp = Blueprint('card_data', __name__)

_HOMEPAGE_CACHE_TTL = 8 * 60 * 60  # 8 hours

_card_of_the_day_cache: dict[str, tuple[dict, float]] = {}
_CARD_OF_THE_DAY_FOLDER = "static/card_of_the_day"

_trending_cache: dict[str, tuple[list, float]] = {}
_popular_cache: dict[str, tuple[list, float]] = {}
_spotlight_cache: dict[str, tuple[list, float]] = {}  # key: "{set}:{limit}"

@card_db_bp.route('/cards/search', methods=["POST", "GET"])
def fetch_card_list():
    """Fetch card data from the database"""
    try:
        db = PostgresDB()

        # Get query parameters
        payload = request.get_json() or {}
        card_data = db.fetch_card_list(filters = payload)

        db.log_player_search(filters=payload, result_count=len(card_data or []))
        db.close_connection()

        return jsonify(card_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@card_db_bp.route('/teams/data', methods=["GET"])
def fetch_team_data():
    """Fetch team data from the database"""
    try:
        db = PostgresDB()

        team_data = db.fetch_team_data()
        db.close_connection()

        return jsonify(team_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@card_db_bp.route('/cards/card', methods=["GET"])
def fetch_card():
    """Fetch a single card by its ID"""
    try:
        db = PostgresDB()
        id = request.args.get('id')
        source = request.args.get('src', 'unknown')
        card = db.fetch_single_card(id)
        db.log_card_id_lookup(card_id=id, source=source)
        db.close_connection()

        if card is None:
            return jsonify({'error': 'Card not found'}), 404

        return jsonify({'card': card.as_json()})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@card_db_bp.route('/cards/total_count', methods=["GET"])
def fetch_total_card_count():
    """Fetch the total count of cards in the database"""
    try:
        db = PostgresDB()
        total_count = db.fetch_total_card_count()
        db.close_connection()

        return jsonify({'total_count': total_count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@card_db_bp.route('/cards/trending', methods=["GET", "POST"])
def fetch_trending_cards():
    """Fetch trending cards from the database"""
    try:
        payload = request.get_json() or {}
        showdown_set = payload.get('set') or 'default'

        cached_result, cached_at = _trending_cache.get(showdown_set, (None, 0.0))
        if cached_result is not None and (time.time() - cached_at) < _HOMEPAGE_CACHE_TTL:
            return jsonify({'trending_cards': cached_result})

        db = PostgresDB()
        trending_cards = db.fetch_trending_cards(set=showdown_set)
        db.close_connection()

        _trending_cache[showdown_set] = (trending_cards, time.time())
        return jsonify({'trending_cards': trending_cards})

    except Exception as e:
        print(f"Error fetching trending cards: {e}")
        return jsonify({'error': str(e)}), 500
    
@card_db_bp.route('/cards/popular', methods=["GET", "POST"])
def fetch_popular_cards():
    """Fetch all-time popular cards from the database"""
    try:
        payload = request.get_json() or {}
        showdown_set = payload.get('set') or 'default'

        cached_result, cached_at = _popular_cache.get(showdown_set, (None, 0.0))
        if cached_result is not None and (time.time() - cached_at) < _HOMEPAGE_CACHE_TTL:
            return jsonify({'popular_cards': cached_result})

        db = PostgresDB()
        popular_cards = db.fetch_popular_cards(set=showdown_set)
        db.close_connection()

        _popular_cache[showdown_set] = (popular_cards, time.time())
        return jsonify({'popular_cards': popular_cards})

    except Exception as e:
        print(f"Error fetching popular cards: {e}")
        return jsonify({'error': str(e)}), 500
    
@card_db_bp.route('/cards/spotlight', methods=["GET", "POST"])
def fetch_spotlight_cards():
    """Fetch spotlight cards from the database"""
    try:
        payload = request.get_json() or {}
        showdown_set = payload.get('set') or 'default'
        limit = payload.get('limit', 4)
        cache_key = f"{showdown_set}:{limit}"

        cached_result, cached_at = _spotlight_cache.get(cache_key, (None, 0.0))
        if cached_result is not None and (time.time() - cached_at) < _HOMEPAGE_CACHE_TTL:
            return jsonify({'spotlight_cards': cached_result})

        db = PostgresDB()
        spotlight_cards = db.fetch_latest_spotlight_cards(set=showdown_set, limit=limit)
        db.close_connection()

        _spotlight_cache[cache_key] = (spotlight_cards, time.time())
        return jsonify({'spotlight_cards': spotlight_cards})

    except Exception as e:
        print(f"Error fetching spotlight cards: {e}")
        return jsonify({'error': str(e)}), 500
    
@card_db_bp.route('/cards/card_of_the_day', methods=["GET", "POST"])
def fetch_card_of_the_day():
    """Fetch the card of the day from the database"""
    try:
        payload = request.get_json() or {}
        showdown_set = payload.get('set') or 'default'

        cached_result, cached_at = _card_of_the_day_cache.get(showdown_set, (None, 0.0))
        if cached_result is not None and (time.time() - cached_at) < _HOMEPAGE_CACHE_TTL:
            return jsonify({'card_of_the_day': cached_result})

        db = PostgresDB()
        card_of_the_day = db.fetch_card_of_the_day(set=showdown_set)
        db.close_connection()

        # GENERATE AN IMAGE FOR THE CARD
        os.makedirs(_CARD_OF_THE_DAY_FOLDER, exist_ok=True)
        card_json = card_of_the_day.get('card_data')
        card = ShowdownPlayerCard(**card_json)
        card.image.output_folder_path = _CARD_OF_THE_DAY_FOLDER
        card.generate_card_image()
        card_of_the_day['card_data'] = card.as_json()

        _card_of_the_day_cache[showdown_set] = (card_of_the_day, time.time())

        return jsonify({'card_of_the_day': card_of_the_day})

    except Exception as e:
        print(f"Error fetching card of the day: {e}")
        return jsonify({'error': str(e)}), 500

@card_db_bp.route('/cards/full', methods=["POST"])
def fetch_full_cards():
    """Fetch full card data for a batch of MLB player IDs."""
    try:
        payload = request.get_json() or {}
        mlb_ids = payload.get('mlb_ids', [])
        season = payload.get('season')
        showdown_set = payload.get('showdown_set', '2000')
        is_wbc = payload.get('is_wbc', False)
        overrides: dict[int, dict] = payload.get('overrides', {})  # Optional overrides for specific mlb_ids

        if not mlb_ids or not season:
            return jsonify({}), 200

        db = PostgresDB()
        card_map: dict = db.fetch_full_cards_by_mlb_id(
            mlb_ids=mlb_ids,
            is_wbc=is_wbc,
            season=int(season),
            showdown_set=showdown_set
        )
        db.close_connection()

        # Serialize: convert int keys to strings (JSON requirement)
        result = {str(k): v for k, v in card_map.items()}

        # Apply overrides to the result if provided (this allows for dynamic modification of card data without needing to update the database)
        for mlb_id_int, override_data in (overrides or {}).items():
            if str(mlb_id_int) in result:
                if not isinstance(override_data, dict):
                    continue  # Skip invalid override data
                
                team_override = override_data.get('team', None)
                if team_override:
                    # If team override, make sure it conforms to Team Enum
                    team_cleaned = Team.map_from_mlb_api_team(team_override)  # This will raise an error if the team name is invalid
                    if 'color_primary' not in override_data:
                        override_data['color_primary'] = f'rgb({team_cleaned.primary_color[0]}, {team_cleaned.primary_color[1]}, {team_cleaned.primary_color[2]})'
                        override_data['color_secondary'] = f'rgb({team_cleaned.secondary_color[0]}, {team_cleaned.secondary_color[1]}, {team_cleaned.secondary_color[2]})'
                    override_data['team'] = team_cleaned.value  # Store the standardized team name in the card data
                result[str(mlb_id_int)].update(override_data)

        return jsonify(result), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@card_db_bp.route('/cards/compact', methods=["POST"])
def fetch_compact_cards():
    """Fetch compact card data for a batch of MLB player IDs."""
    try:
        payload = request.get_json() or {}
        mlb_ids = payload.get('mlb_ids', [])
        season = payload.get('season')
        showdown_set = payload.get('showdown_set', '2000')
        is_wbc = payload.get('is_wbc', False)
        overrides: dict[int, dict] = payload.get('overrides', {})  # Optional overrides for specific mlb_ids

        if not mlb_ids or not season:
            return jsonify({}), 200

        db = PostgresDB()
        card_map = db.fetch_compact_cards_by_mlb_id(
            mlb_ids=mlb_ids,
            is_wbc=is_wbc,
            season=int(season),
            showdown_set=showdown_set,
        )
        db.close_connection()

        # Apply overrides to the card map if provided (this allows for dynamic modification of card data without needing to update the database)
        for mlb_id_int, override_data in (overrides or {}).items():
            mlb_id_str = str(mlb_id_int)
            if mlb_id_str in card_map:
                if not isinstance(override_data, dict):
                    continue  # Skip invalid override data
                
                team_override = override_data.get('team', None)
                if team_override:
                    # If team override, make sure it conforms to Team Enum
                    team_cleaned = Team.map_from_mlb_api_team(team_override)  # This will raise an error if the team name is invalid
                    if 'color_primary' not in override_data:
                        override_data['color_primary'] = f'rgb({team_cleaned.primary_color[0]}, {team_cleaned.primary_color[1]}, {team_cleaned.primary_color[2]})'
                        override_data['color_secondary'] = f'rgb({team_cleaned.secondary_color[0]}, {team_cleaned.secondary_color[1]}, {team_cleaned.secondary_color[2]})'
                    override_data['team'] = team_cleaned.value  # Store the standardized team name in the card data
                card_map[mlb_id_str].update(override_data)

        # Serialize: convert int keys to strings (JSON requirement)
        result = {str(k): v for k, v in card_map.items()}
        return jsonify(result), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@card_db_bp.route('/cards/customs/history', methods=["GET", "POST"])
def fetch_custom_card_history():
    """Fetch the history of custom cards generated by users"""
    try:
        payload = request.get_json() or {}
        user_id = payload.get('user_id')
        limit = payload.get('limit', 20)
        offset = payload.get('offset', 0)

        db = PostgresDB()
        custom_card_history = db.fetch_custom_card_history(user_ids=[user_id] if user_id else None, limit=limit, offset=offset)
        db.close_connection()

        return jsonify({'custom_card_history': custom_card_history})

    except Exception as e:
        print(f"Error fetching custom card history: {e}")
        return jsonify({'error': str(e)}), 500