from flask import Flask, render_template, request, jsonify
from mlb_showdown.showdown_player_card_generator import ShowdownPlayerCardGenerator
from mlb_showdown.baseball_ref_scraper import BaseballReferenceScraper
import os

app = Flask(__name__)

@app.route('/')
def card_submition():
    return render_template('main_screen.html')

@app.route('/card_creation')
def card_creator():
    error = ''
    showdown = None
    try:
        # PARSE INPUTS
        name = request.args.get('name').title()
        year = str(request.args.get('year'))
        set = str(request.args.get('set'))
        url = request.args.get('url')
        print(name, year, set, '{}--'.format(url))

        # SCRAPE PLAYER DATA
        scraper = BaseballReferenceScraper(name=name,year=year)
        statline = scraper.player_statline()

        # CREATE CARD
        showdown = ShowdownPlayerCardGenerator(
            name=name,
            year=year,
            stats=statline,
            context=set,
            player_image_url=None if url == '' else url
        )
        showdown.player_image()
        card_image_path = os.path.join('static', 'images', showdown.image_name)
        return jsonify(image_path=card_image_path,error=error)

    except:
        error = "Unable to create Showdown Card. Make sure the player name and year are correct."
        return jsonify(image_path=None,error=error)

if __name__ == '__main__':
    app.run()
