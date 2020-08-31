from flask import Flask, render_template, request
from mlb_showdown.showdown_player_card_generator import ShowdownPlayerCardGenerator
from mlb_showdown.baseball_ref_scraper import BaseballReferenceScraper
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def card_creator():
    errors = []
    showdown = None
    if request.method == "POST":
        # PARSE USER INPUTS

        try:
            name = request.form['name'].title()
            year = request.form['year']
            set = request.form['set']
            url = request.form['url']
            scraper = BaseballReferenceScraper(name=name,year=year)
            statline = scraper.player_statline()

            showdown = ShowdownPlayerCardGenerator(
                name=name,
                year=year,
                stats=statline,
                context=set,
                player_image_url=None if url == '' else url
            )
            showdown.player_image()
        except:
            errors.append(
                "Unable to create Showdown Card. Make sure the player name and year are correct."
            )
    try:
        card_image_path = os.path.join('static', 'images', showdown.image_name)
    except:
        card_image_path = None
    return render_template('main_screen.html', errors=errors, image=card_image_path)

if __name__ == '__main__':
    app.run()
