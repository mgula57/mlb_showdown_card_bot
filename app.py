import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from pprint import pprint
from time import sleep

# INTERNAL
from mlb_showdown_bot.core.card.card_generation import generate_card

# ----------------------------------------------------------
# APP
# ----------------------------------------------------------

app = Flask(__name__)

# ALLOW FRONTEND ORIGIN (VITE DEFAULTS TO 5173)
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
CORS(app, resources={r"/*": {"origins": FRONTEND_ORIGIN}})

# ----------------------------------------------------------
# FRONT END
# ----------------------------------------------------------

@app.route('/build_custom_card', methods=["POST","GET"])
def build_custom_card():

    # SUPPORT EITHER GET OR POST
    kwargs: dict[str, str] = {}
    kwargs.update(request.args.to_dict())
    kwargs.update(request.form.to_dict())

    # SEE IF REQUEST HAS JSON DATA
    json_data = request.get_json(silent=True) or {}
    if isinstance(json_data, dict):
        kwargs.update({k: v for k, v in json_data.items()})

    # DELAY SLIGHTLY IF IMG UPLOAD TO LET THE IMAGE FINISH UPLOADING
    if kwargs.get('img_name', None):
        sleep(3)

    # RANDOM
    is_random = kwargs.get('name', '').upper() == '((RANDOM))'

    # NORMAL CARD GENERATION
    card_data = generate_card(randomize=is_random, **kwargs)
    
    return jsonify(card_data)

@app.route('/upload_card_image', methods=["POST","GET"])
def upload():
    try:
        image = request.files.get('image_file')
        name = image.filename
        image.save(os.path.join('mlb_showdown_bot', 'core', 'card', 'image_uploads', name))
    except:
        name = ''

if __name__ == '__main__':
    app.run(debug=None)
