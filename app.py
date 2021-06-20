from flask import Flask, render_template, request, jsonify, Response
from mlb_showdown_bot.showdown_player_card_generator import ShowdownPlayerCardGenerator
from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
import os
import re
import json
import sys
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# SETUP DB
uri = os.environ.get('DATABASE_URL')
if uri:
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CardLog(db.Model):
    __tablename__ = 'card_log'

    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    year = db.Column(db.Text)
    set = db.Column(db.String(8))
    is_cooperstown = db.Column(db.Boolean)
    is_super_season = db.Column(db.Boolean)
    img_url = db.Column(db.String(2048))
    img_name = db.Column(db.String(512))
    error = db.Column(db.String(256))
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    is_all_star_game = db.Column(db.Boolean)
    expansion = db.Column(db.Text)
    stats_offset = db.Column(db.Integer)
    set_num = db.Column(db.Text)

    def __init__(self, name, year, set, is_cooperstown, is_super_season, img_url, img_name, error, is_all_star_game, expansion, stats_offset, set_num):
        """ DEFAULT INIT FOR DB OBJECT """
        self.name = name
        self.year = year
        self.set = set
        self.is_cooperstown = is_cooperstown
        self.is_super_season = is_super_season
        self.is_all_star_game = is_all_star_game
        self.img_url = img_url
        self.img_name = img_name
        self.error = error
        self.is_all_star_game = is_all_star_game
        self.expansion = expansion
        self.stats_offset = stats_offset
        self.set_num = set_num

def log_card_submission_to_db(name, year, set, is_cooperstown, is_super_season, img_url, img_name, error, is_all_star_game, expansion, stats_offset, set_num):
    """SEND LOG OF CARD SUBMISSION TO DB"""
    try:
        card_log = CardLog(
            name=name,
            year=year,
            set=set,
            is_cooperstown=is_cooperstown,
            is_super_season=is_super_season,
            img_url=img_url,
            img_name=img_name,
            error=error,
            is_all_star_game=is_all_star_game,
            expansion=expansion,
            stats_offset=stats_offset,
            set_num=set_num
        )
        db.session.add(card_log)
        db.session.commit()
    except Exception as error:
        print('ERROR LOGGING TO DATABASE')
        print(error)
        return None


@app.route('/')
def card_submission():
    return render_template('index.html')

@app.route('/card_creation')
def card_creator():

    error = ''
    showdown = None
    name = None
    year = None
    set = None
    is_cooperstown = None
    is_super_season = None
    is_all_star_game = None
    img_url = None
    img_name = None
    set_num = None
    expansion = None
    offset = None

    try:
        # PARSE INPUTS
        error = 'Input Error. Please Try Again'
        name = request.args.get('name').title()
        year = str(request.args.get('year'))
        set = str(request.args.get('set'))
        url = request.args.get('url')
        is_cc = request.args.get('cc').lower() == 'true'
        is_ss = request.args.get('ss').lower() == 'true'
        is_asg = request.args.get('asg').lower() == 'true'
        try:
            offset = int(request.args.get('offset'))
            offset = 4 if offset > 4 else offset
            offset = 0 if offset < 0 else offset
        except:
            offset = 0
        img = request.args.get('img_name')
        set_num = str(request.args.get('set_num'))
        expansion_raw = str(request.args.get('expansion'))

        # SCRAPE PLAYER DATA
        error = 'Error loading player data. Make sure the player name and year are correct'
        scraper = BaseballReferenceScraper(name=name,year=year)
        statline = scraper.player_statline()
        is_cooperstown = is_cc if is_cc else False
        is_super_season = is_ss if is_ss else False
        is_all_star_game = is_asg if is_asg else False
        img_url = None if url == '' else url
        img_name = None if img == '' else img
        set_number = year if set_num == '' else set_num
        expansion = "BS" if expansion_raw == '' else expansion_raw

        # CREATE CARD
        error = "Error - Unable to create Showdown Card data."
        showdown = ShowdownPlayerCardGenerator(
            name=name,
            year=year,
            stats=statline,
            context=set,
            expansion=expansion,
            player_image_path=img_name,
            player_image_url=img_url,
            is_cooperstown=is_cooperstown,
            is_super_season=is_super_season,
            is_all_star_game=is_all_star_game,
            offset=offset,
            set_number=set_number,
            is_running_in_flask=True
        )
        error = "Error - Unable to create Showdown Card Image."
        showdown.player_image()
        card_image_path = os.path.join('static', 'output', showdown.image_name)
        player_stats_data = showdown.player_data_for_html_table()

        error = ''
        log_card_submission_to_db(
            name=name,
            year=year,
            set=set,
            is_cooperstown=is_cooperstown,
            is_super_season=is_super_season,
            img_url=img_url,
            img_name=img_name,
            error=error,
            is_all_star_game=is_all_star_game,
            expansion=expansion,
            stats_offset=offset,
            set_num=set_num
        )
        return jsonify(image_path=card_image_path,error=error,player_stats=player_stats_data)

    except:
        log_card_submission_to_db(
            name=name,
            year=year,
            set=set,
            is_cooperstown=is_cooperstown,
            is_super_season=is_super_season,
            img_url=img_url,
            img_name=img_name,
            error=error,
            is_all_star_game=is_all_star_game,
            expansion=expansion,
            stats_offset=offset,
            set_num=set_num
        )
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
    app.run(debug=False)
