import pprint
import hashlib
import json
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
from .utils.file_upload import process_uploaded_file, cleanup_uploaded_file
from .utils.data_conversion import convert_form_data_types
from ..core.card.card_generation import generate_card, generate_cards
from ..core.card.showdown_player_card import ShowdownPlayerCard

cards_bp = Blueprint('cards', __name__)

CARDS_CACHE_TTL = timedelta(hours=8)
_cards_cache: dict[str, tuple[dict, datetime]] = {}


@cards_bp.route('/build_custom_card', methods=["POST", "GET"])
def build_custom_card():
    kwargs: dict[str, str] = {}

    # Check if this is a multipart form (file upload) or JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Handle file upload case
        payload = {}
        
        # Get form data
        for key, value in request.form.items():
            if key in ['image_source']:
                continue
            payload[key] = value
        
        # Handle file upload
        uploaded_file_data = None
        if 'image_upload' in request.files:
            file = request.files['image_upload']
            if file and file.filename != '':
                uploaded_file_data = process_uploaded_file(file)
                payload['image_path'] = uploaded_file_data.get('path', None)
        
        # Convert string values to appropriate types
        payload = convert_form_data_types(payload)

    else:
        # Handle regular JSON case (existing functionality)
        payload = request.get_json()
        uploaded_file_data = None

    kwargs.update(request.args.to_dict())
    kwargs.update(request.form.to_dict())

    # See if request has JSON data
    json_data = request.get_json(silent=True) or {}
    if isinstance(json_data, dict):
        kwargs.update({k: v for k, v in json_data.items()})

    # Random
    is_random = kwargs.get('name', '').upper() == '((RANDOM))'

    try:
        # Normal card generation
        card_data = generate_card(randomize=is_random, store_in_logs=True, **payload)

        return jsonify(card_data)
        
    except Exception as e:
        # Clean up uploaded file on error
        if uploaded_file_data:
            cleanup_uploaded_file(uploaded_file_data)
        raise
    finally:
        # Clean up uploaded file after processing
        if uploaded_file_data:
            cleanup_uploaded_file(uploaded_file_data)

@cards_bp.route('/build_image_for_card', methods=["POST", "GET"])
def build_image_for_card():
    """Generate image for existing card data"""
    from ..core.database.postgres_db import PostgresDB

    try:
        payload = request.get_json()
        if not payload or 'card' not in payload:
            return jsonify({'error': 'No card data provided'}), 400

        card_json = payload['card']
        card = ShowdownPlayerCard(**card_json)

        card.image.output_folder_path = "static/output"

        # PRODUCE IMAGE AND UPDATE DATASET
        card.generate_card_image()
        payload['card'] = card.as_json()

        # LOGGING
        db = PostgresDB()
        db.log_card_image_generation(card_id=card.id)

        return jsonify(payload)

    except Exception as e:
        print(f"Error in build_image_for_card: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'error_for_user': 'Failed to generate card image'
        }), 500

@cards_bp.route('/build_cards', methods=["POST"])
def build_cards():
    """
    Generate multiple cards from a batch request.
    Requests should include a dict with these required fields at minimum:
    {
        "cards": [
            {
                "player_id": "12345",
                "name": "Player Name",
                "year": "2026",
                "set": "2005"
            },
            ...
        ]
    }
    """
    try:
        payload = request.get_json()
        if not payload or 'requested_cards' not in payload:
            return jsonify({'error': 'No cards data provided'}), 400

        cache_key = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        now = datetime.now(timezone.utc)
        cached = _cards_cache.get(cache_key)
        if cached and now < cached[1]:
            print("Serving build_cards from cache")
            return jsonify(cached[0]), 200

        cards_data = payload['requested_cards']
        generated_cards = []
        for card_kwargs in cards_data:

            try:
                card_data = generate_card(
                    datasource='MLB_API',
                    disable_realtime=True,
                    store_in_logs=False,
                    **card_kwargs
                )
                generated_cards.append(card_data)
            except Exception as e:
                print(f"Error generating card for {card_kwargs.get('name', 'unknown')}: {str(e)}")
                import traceback
                traceback.print_exc()
                generated_cards.append({
                    'error': str(e),
                    'error_for_user': f"Failed to generate card for {card_kwargs.get('name', 'unknown')}"
                })

        result = {'cards': generated_cards}
        _cards_cache[cache_key] = (result, now + CARDS_CACHE_TTL)
        return jsonify(result)

    except Exception as e:
        print(f"Error in build_cards: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'error_for_user': 'Failed to generate cards'
        }), 500
    
@cards_bp.route('/build_cards_from_ids', methods=["POST"])
def build_cards_from_ids():
    """Helper function to build cards from a list of player IDs. This can be used for batch generation from the CLI or other sources."""

    try:
        payload = request.get_json()
        ids = payload.get('ids', [])
        season = payload.get('season', None)
        card_settings = payload.get('card_settings', {})
        generated_cards = generate_cards(player_ids=ids, years=[season] if season else None, **card_settings)

        generate_cards_data = [{'card': card.as_json()} for card in generated_cards]

        return jsonify({'cards': generate_cards_data}), 200

    except Exception as e:
        print(f"Error in build_cards_from_ids: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'error_for_user': 'Failed to generate cards from IDs'
        }), 500