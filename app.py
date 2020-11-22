from flask import Flask, render_template, request, jsonify, Response
from mlb_showdown_bot.showdown_player_card_generator import ShowdownPlayerCardGenerator
from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
import os
import sys

app = Flask(__name__)

@app.route('/')
def card_submition():
    return render_template('index.html')

@app.route('/card_creation')
def card_creator():
    error = ''
    showdown = None
    try:
        # PARSE INPUTS
        error = 'Input Error. Please Try Again'
        name = request.args.get('name').title()
        year = str(request.args.get('year'))
        set = str(request.args.get('set'))
        url = request.args.get('url')
        is_cc = request.args.get('cc').lower() == 'true'
        is_ss = request.args.get('ss').lower() == 'true'
        try:
            offset = int(request.args.get('offset'))
            offset = 4 if offset > 4 else offset
            offset = 0 if offset < 0 else offset
        except:
            offset = 0
        img = request.args.get('img_name')
        # SCRAPE PLAYER DATA
        error = 'Error loading player data. Make sure the player name and year are correct'
        scraper = BaseballReferenceScraper(name=name,year=year)
        statline = scraper.player_statline()

        # CREATE CARD
        error = "Error - Unable to create Showdown Card data."
        showdown = ShowdownPlayerCardGenerator(
            name=name,
            year=year,
            stats=statline,
            context=set,
            player_image_path=None if img == '' else img,
            player_image_url=None if url == '' else url,
            is_cooperstown=is_cc if is_cc else False,
            is_super_season=is_ss if is_ss else False,
            offset=offset,
            is_running_in_flask=True
        )
        error = "Error - Unable to create Showdown Card Image."
        showdown.player_image()
        card_image_path = os.path.join('static', 'output', showdown.image_name)
        player_stats_data = showdown.player_data_for_html_table()

        error = ''
        return jsonify(image_path=card_image_path,error=error,player_stats=player_stats_data)

    except:
        return jsonify(image_path=None,error=error,player_stats=None)

@app.route('/upload', methods=["POST","GET"])
def upload():
    try:
        image = request.files.get('image_file')
        name = image.filename
        image.save(os.path.join('mlb_showdown_bot', 'uploads', image.filename))
    except:
        name = ''

if __name__ == '__main__':
    app.run()
