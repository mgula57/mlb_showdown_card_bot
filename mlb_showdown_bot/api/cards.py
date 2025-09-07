from flask import Blueprint, request, jsonify
from .utils.file_upload import process_uploaded_file, cleanup_uploaded_file
from .utils.data_conversion import convert_form_data_types
from ..core.card.card_generation import generate_card

cards_bp = Blueprint('cards', __name__)

@cards_bp.route('/build_custom_card', methods=["POST", "GET"])
def build_custom_card():
    kwargs: dict[str, str] = {}
    print(request.content_type)

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
        uploaded_file = None
        if 'image_upload' in request.files:
            file = request.files['image_upload']
            if file and file.filename != '':
                uploaded_file = process_uploaded_file(file)
                payload['image_upload'] = uploaded_file

        print(uploaded_file.get('filename') if uploaded_file else "No file uploaded")
        
        # Convert string values to appropriate types
        payload = convert_form_data_types(payload)

    else:
        # Handle regular JSON case (existing functionality)
        payload = request.get_json()
        uploaded_file = None
    
    # Add the uploaded file info to payload if present
    if uploaded_file:
        payload['image_upload'] = uploaded_file

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
        card_data = generate_card(randomize=is_random, **payload)
        
        return jsonify(card_data)
        
    except Exception as e:
        # Clean up uploaded file on error
        if uploaded_file:
            cleanup_uploaded_file(uploaded_file)
        raise
    finally:
        # Clean up uploaded file after processing
        if uploaded_file:
            cleanup_uploaded_file(uploaded_file)