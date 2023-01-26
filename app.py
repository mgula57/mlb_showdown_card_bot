from flask import Flask, render_template, request, jsonify, Response
from mlb_showdown_bot.firebase import Firebase
from mlb_showdown_bot.showdown_player_card_generator import ShowdownPlayerCardGenerator
from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
import os
import pandas as pd
from pathlib import Path
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
    is_holiday = db.Column(db.Boolean)
    is_dark_mode = db.Column(db.Boolean)
    is_rookie_season = db.Column(db.Boolean)
    is_variable_spd_00_01 = db.Column(db.Boolean)
    is_random = db.Column(db.Boolean)
    is_automated_image = db.Column(db.Boolean)
    is_foil = db.Column(db.Boolean)
    is_stats_loaded_from_library = db.Column(db.Boolean)
    is_img_loaded_from_library = db.Column(db.Boolean)
    add_year_container = db.Column(db.Boolean)
    ignore_showdown_library = db.Column(db.Boolean)

    def __init__(self, name, year, set, is_cooperstown, is_super_season, img_url, img_name, error, is_all_star_game, expansion, stats_offset, set_num, is_holiday, is_dark_mode, is_rookie_season, is_variable_spd_00_01, is_random, is_automated_image, is_foil, is_stats_loaded_from_library, is_img_loaded_from_library, add_year_container, ignore_showdown_library):
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
        self.is_holiday = is_holiday
        self.is_dark_mode = is_dark_mode
        self.is_rookie_season = is_rookie_season
        self.is_variable_spd_00_01 = is_variable_spd_00_01
        self.is_random = is_random
        self.is_automated_image = is_automated_image
        self.is_foil = is_foil
        self.is_stats_loaded_from_library = is_stats_loaded_from_library
        self.is_img_loaded_from_library = is_img_loaded_from_library
        self.add_year_container = add_year_container
        self.ignore_showdown_library = ignore_showdown_library

def log_card_submission_to_db(name, year, set, is_cooperstown, is_super_season, img_url, img_name, error, is_all_star_game, expansion, stats_offset, set_num, is_holiday, is_dark_mode, is_rookie_season, is_variable_spd_00_01, is_random, is_automated_image, is_foil, is_stats_loaded_from_library, is_img_loaded_from_library, add_year_container, ignore_showdown_library):
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
            set_num=set_num,
            is_holiday=is_holiday,
            is_dark_mode=is_dark_mode,
            is_rookie_season=is_rookie_season,
            is_variable_spd_00_01=is_variable_spd_00_01,
            is_random=is_random,
            is_automated_image=is_automated_image,
            is_foil=is_foil,
            is_stats_loaded_from_library=is_stats_loaded_from_library,
            is_img_loaded_from_library=is_img_loaded_from_library,
            add_year_container=add_year_container,
            ignore_showdown_library=ignore_showdown_library
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
    is_automated_image = False
    is_stats_loaded_from_library = False
    is_img_loaded_from_library = False
    showdown = None
    name = None
    year = None
    set = None
    is_cooperstown = None
    is_super_season = None
    is_rookie_season = None
    is_all_star_game = None
    is_holiday = None
    img_url = None
    img_name = None
    set_num = None
    expansion = None
    offset = None
    add_img_border = None
    is_dark_mode = None
    is_variable_spd_00_01 = None
    is_random = None
    is_foil = None
    is_stats_loaded_from_library = None
    is_img_loaded_from_library = None
    add_year_container = None
    ignore_showdown_library = None

    try:
        # PARSE INPUTS
        error = 'Input Error. Please Try Again'
        name = request.args.get('name').title()
        year = str(request.args.get('year'))
        set = str(request.args.get('set')).upper()
        url = request.args.get('url')
        is_cc = request.args.get('cc').lower() == 'true' if request.args.get('cc') else False
        is_ss = request.args.get('ss').lower() == 'true' if request.args.get('ss') else False
        is_rs = request.args.get('rs').lower() == 'true' if request.args.get('rs') else False
        is_asg = request.args.get('asg').lower() == 'true' if request.args.get('asg') else False
        is_hol = request.args.get('is_holiday').lower() == 'true' if request.args.get('is_holiday') else False
        try:
            offset = int(request.args.get('offset'))
            offset = 4 if offset > 4 else offset
            offset = 0 if offset < 0 else offset
        except:
            offset = 0
        img = request.args.get('img_name')
        set_num = str(request.args.get('set_num'))
        expansion_raw = str(request.args.get('expansion'))
        is_border = request.args.get('addBorder').lower() == 'true' if request.args.get('addBorder') else False
        dark_mode = request.args.get('is_dark_mode').lower() == 'true' if request.args.get('is_dark_mode') else False
        is_variable_spd_00_01 = request.args.get('is_variable_spd_00_01').lower() == 'true' if request.args.get('is_variable_spd_00_01') else False
        foil = request.args.get('is_foil').lower() == 'true' if request.args.get('is_foil') else False
        year_container = request.args.get('add_year_container').lower() == 'true' if request.args.get('add_year_container') else False
        ignore_sl = request.args.get('ignore_showdown_library').lower() == 'true' if request.args.get('ignore_showdown_library') else False
        is_random = name.upper() == '((RANDOM))'
        if is_random:
            # IF RANDOMIZED, ADD RANDOM NAME AND YEAR
            name, year = random_player_id_and_year()

        # LOAD PLAYER DATA
        error = 'Error loading player data. Make sure the player name and year are correct'
        scraper = BaseballReferenceScraper(name=name,year=year)
        is_cooperstown = is_cc if is_cc else False
        is_super_season = is_ss if is_ss else False
        is_rookie_season = is_rs if is_rs else False
        is_all_star_game = is_asg if is_asg else False
        is_holiday = is_hol if is_hol else False
        img_url = None if url == '' else url
        img_name = None if img == '' else img
        set_number = set_num
        expansion = "FINAL" if expansion_raw == '' else expansion_raw
        add_img_border = is_border if is_border else False
        is_dark_mode = dark_mode if dark_mode else False
        is_variable_speed_00_01 = is_variable_spd_00_01 if is_variable_spd_00_01 else False
        is_foil = foil if foil else False
        add_year_container = year_container if year_container else False
        ignore_showdown_library = ignore_sl if ignore_sl else False

        # CREATE CARD
        error = "Error - Unable to create Showdown Card data."

        try:
            db = Firebase()
            showdown = db.load_showdown_card(
                ignore_showdown_library=ignore_showdown_library,
                bref_id = scraper.baseball_ref_id,
                year=year,
                context=set,
                expansion=expansion,
                player_image_path=img_name,
                player_image_url=img_url,
                is_cooperstown=is_cooperstown,
                is_super_season=is_super_season,
                is_rookie_season=is_rookie_season,
                is_all_star_game=is_all_star_game,
                is_holiday=is_holiday,
                offset=offset,
                set_number=set_number,
                add_image_border=add_img_border,
                is_dark_mode=is_dark_mode,
                is_variable_speed_00_01=is_variable_speed_00_01,
                is_foil=is_foil,
                team_override=scraper.team_override,
                pitcher_override=scraper.pitcher_override,
                hitter_override=scraper.hitter_override,
                is_running_in_flask=True
            )
            db.close_session()
        except:
            showdown = None
            
        if showdown:
            is_stats_loaded_from_library = True
        else:
            is_stats_loaded_from_library = False
            error = 'Error loading player data. Make sure the player name and year are correct'
            statline = scraper.player_statline()
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
                is_rookie_season=is_rookie_season,
                is_all_star_game=is_all_star_game,
                is_holiday=is_holiday,
                offset=offset,
                set_number=set_number,
                add_image_border=add_img_border,
                is_dark_mode=is_dark_mode,
                is_variable_speed_00_01=is_variable_speed_00_01,
                is_foil=is_foil,
                add_year_container=add_year_container,
                is_running_in_flask=True
            )
        error = "Error - Unable to create Showdown Card Image."
        cached_img_link = showdown.cached_img_link()
        if cached_img_link:
            # USE IMAGE FROM GDRIVE
            card_image_path = cached_img_link
            is_img_loaded_from_library = True
        else:
            # GENERATE THE IMAGE
            is_img_loaded_from_library = False
            showdown.player_image()
            card_image_path = os.path.join('static', 'output', showdown.image_name)
        player_command = "Control" if showdown.is_pitcher else "Onbase"
        player_stats_data = showdown.player_data_for_html_table()
        player_points_data = showdown.points_data_for_html_table()
        player_accuracy_data = showdown.accuracy_data_for_html_table()
        player_ranks_data = showdown.rank_data_for_html_table()
        radar_labels, radar_values = showdown.radar_chart_labels_as_values()
        radar_color = showdown.radar_chart_color()
        is_automated_image = showdown.is_automated_image
        player_name = showdown.name
        player_year = showdown.year
        player_context = showdown.context
        bref_url = showdown.bref_url
        shOPS_plus = showdown.projected['onbase_plus_slugging_plus'] if 'onbase_plus_slugging_plus' in showdown.projected else None
        name = player_name if is_random else name # LOG ACTUAL NAME IF IS RANDOMIZED PLAYER
        error = showdown.img_loading_error[:250] if showdown.img_loading_error else ''
        if len(error) > 0:
            print(error)
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
            set_num=set_num,
            is_holiday=is_holiday,
            is_dark_mode=is_dark_mode,
            is_rookie_season=is_rookie_season,
            is_variable_spd_00_01=is_variable_speed_00_01,
            is_random=is_random,
            is_automated_image=is_automated_image,
            is_foil=is_foil,
            is_stats_loaded_from_library=is_stats_loaded_from_library,
            is_img_loaded_from_library=is_img_loaded_from_library,
            add_year_container=add_year_container,
            ignore_showdown_library=ignore_showdown_library
        )
        return jsonify(
            image_path=card_image_path,
            error=error,
            is_automated_image=is_automated_image,
            is_img_loaded_from_library=is_img_loaded_from_library,
            is_stats_loaded_from_library=is_stats_loaded_from_library,
            player_command=player_command,
            player_stats=player_stats_data, 
            player_points=player_points_data,
            player_accuracy=player_accuracy_data,
            player_ranks=player_ranks_data,
            player_name=player_name,
            player_year=player_year,
            player_context=player_context,
            bref_url=bref_url,
            radar_labels=radar_labels,
            radar_values=radar_values,
            radar_color=radar_color,
            shOPS_plus=shOPS_plus,
        )

    except Exception as e:
        error_full = str(e)[:250]
        print(error_full)
        log_card_submission_to_db(
            name=name,
            year=year,
            set=set,
            is_cooperstown=is_cooperstown,
            is_super_season=is_super_season,
            img_url=img_url,
            img_name=img_name,
            error=error_full,
            is_all_star_game=is_all_star_game,
            expansion=expansion,
            stats_offset=offset,
            set_num=set_num,
            is_holiday=is_holiday,
            is_dark_mode=is_dark_mode,
            is_rookie_season=is_rookie_season,
            is_variable_spd_00_01=is_variable_spd_00_01,
            is_random=is_random,
            is_automated_image=is_automated_image,
            is_foil=is_foil,
            is_stats_loaded_from_library=is_stats_loaded_from_library,
            is_img_loaded_from_library=is_img_loaded_from_library,
            add_year_container=add_year_container,
            ignore_showdown_library=ignore_showdown_library
        )
        return jsonify(
            image_path=None,
            error=error,
            is_automated_image=is_automated_image,
            is_img_loaded_from_library=is_img_loaded_from_library,
            is_stats_loaded_from_library=is_stats_loaded_from_library,
            player_command=None,
            player_stats=None,
            player_points=None,
            player_accuracy=None,
            player_ranks=None,
            player_name=None,
            player_year=None,
            player_context=None,
            bref_url=None,
            radar_labels=None,
            radar_values=None,
            radar_color=None,
            shOPS_plus=None,
        )

@app.route('/upload', methods=["POST","GET"])
def upload():
    try:
        image = request.files.get('image_file')
        name = image.filename
        image.save(os.path.join('mlb_showdown_bot', 'uploads', name))
    except:
        name = ''

def random_player_id_and_year():
    random_players_filepath = os.path.join(Path(os.path.dirname(__file__)),'random_players.csv')
    random_players_pd = pd.read_csv(random_players_filepath, index_col=None)
    random_players_qualified = random_players_pd[(random_players_pd['games_played'] > 50) | (random_players_pd['games_pitched'] > 20)]
    random_player_sample = random_players_qualified.sample(1).to_dict('records')[0]

    return random_player_sample['player_id'], str(random_player_sample['year'])

if __name__ == '__main__':
    app.run(debug=False)
