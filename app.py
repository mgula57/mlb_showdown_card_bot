import os
from flask import Flask, render_template, request, jsonify
from pprint import pprint
from time import sleep

# INTERNAL
from mlb_showdown_bot.core.card.card_generation import generate_card

# ----------------------------------------------------------
# APP
# ----------------------------------------------------------

app = Flask(__name__)

# ----------------------------------------------------------
# FRONT END
# ----------------------------------------------------------

@app.route('/')
def card_submission():
    return render_template('index.html')

@app.route('/card_creation')
def card_creator():

    # CONVERT ALL REQUEST ARGS TO DICT
    kwargs = request.args.to_dict()

    # DELAY SLIGHTLY IF IMG UPLOAD TO LET THE IMAGE FINISH UPLOADING
    if kwargs.get('img_name', None):
        sleep(3)

    # RANDOM
    is_random = kwargs.get('name', '').upper() == '((RANDOM))'

    # NORMAL CARD GENERATION
    card_data = generate_card(randomize=is_random, **kwargs)
    
    return jsonify(card_data)

@app.route('/upload', methods=["POST","GET"])
def upload():
    try:
        image = request.files.get('image_file')
        name = image.filename
        image.save(os.path.join('mlb_showdown_bot', 'core', 'card', 'image_uploads', name))
    except:
        name = ''

if __name__ == '__main__':
    app.run(debug=None)
