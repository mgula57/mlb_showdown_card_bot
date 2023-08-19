from flask import Flask, render_template, request, jsonify, Response
from mlb_showdown_bot.firebase import Firebase
from mlb_showdown_bot.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from pprint import pprint


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
    set_year_plus_one = db.Column(db.Boolean)
    edition = db.Column(db.String(64))
    hide_team_logo = db.Column(db.Boolean)
    date_override = db.Column(db.String(256))
    era = db.Column(db.String(64))
    image_parallel = db.Column(db.String(64))

    def __init__(self, name, year, set, is_cooperstown, is_super_season, img_url, img_name, error, is_all_star_game, expansion, stats_offset, set_num, is_holiday, is_dark_mode, is_rookie_season, is_variable_spd_00_01, is_random, is_automated_image, is_foil, is_stats_loaded_from_library, is_img_loaded_from_library, add_year_container, ignore_showdown_library, set_year_plus_one, edition, hide_team_logo, date_override, era, image_parallel):
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
        self.set_year_plus_one = set_year_plus_one
        self.edition = edition
        self.hide_team_logo = hide_team_logo
        self.date_override = date_override
        self.era = era
        self.image_parallel = image_parallel

def log_card_submission_to_db(name, year, set, img_url, img_name, error, expansion, stats_offset, set_num, is_dark_mode, is_variable_spd_00_01, is_random, is_automated_image, is_foil, is_stats_loaded_from_library, is_img_loaded_from_library, add_year_container, ignore_showdown_library, set_year_plus_one, edition, hide_team_logo, date_override, era, image_parallel):
    """SEND LOG OF CARD SUBMISSION TO DB"""
    try:
        card_log = CardLog(
            name=name,
            year=year,
            set=set,
            is_cooperstown=False,
            is_super_season=False,
            img_url=img_url,
            img_name=img_name,
            error=error,
            is_all_star_game=False,
            expansion=expansion,
            stats_offset=stats_offset,
            set_num=set_num,
            is_holiday=False,
            is_dark_mode=is_dark_mode,
            is_rookie_season=False,
            is_variable_spd_00_01=is_variable_spd_00_01,
            is_random=is_random,
            is_automated_image=is_automated_image,
            is_foil=is_foil,
            is_stats_loaded_from_library=is_stats_loaded_from_library,
            is_img_loaded_from_library=is_img_loaded_from_library,
            add_year_container=add_year_container,
            ignore_showdown_library=ignore_showdown_library,
            set_year_plus_one=set_year_plus_one,
            edition=edition,
            hide_team_logo=hide_team_logo,
            date_override=date_override,
            era=era,
            image_parallel=image_parallel
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
    img_url = None
    img_name = None
    set_num = None
    expansion = None
    offset = None
    add_img_border = None
    is_dark_mode = None
    is_variable_spd_00_01 = None
    is_random = None
    is_foil = False
    is_stats_loaded_from_library = None
    is_img_loaded_from_library = None
    add_year_container = None
    ignore_showdown_library = None
    set_year_plus_one = None
    hide_team_logo = None
    edition = None
    date_override = None
    era = None
    image_parallel = None

    try:
        # PARSE INPUTS
        error = 'Input Error. Please Try Again'
        name = request.args.get('name').title()
        year = str(request.args.get('year'))
        # if ' (' in year and ')' in year:
        #     month, day = year.split('(')[1].split(')')[0].split('/')
        #     year = year.split(' ')[0]
        #     date_override = f'{month.zfill(2)}-{day.zfill(2)}-{year}'
        set = str(request.args.get('set')).upper()
        url = request.args.get('url')
        try:
            offset = int(request.args.get('offset'))
            offset = 4 if offset > 4 else offset
            offset = 0 if offset < 0 else offset
        except:
            offset = 0
        img = request.args.get('img_name')
        set_num = str(request.args.get('set_num'))
        expansion_raw = str(request.args.get('expansion'))
        edition_raw = str(request.args.get('edition'))
        era_raw = str(request.args.get('era'))
        img_parallel_raw = str(request.args.get('img_parallel', 'NONE'))
        is_border = request.args.get('addBorder').lower() == 'true' if request.args.get('addBorder') else False
        dark_mode = request.args.get('is_dark_mode').lower() == 'true' if request.args.get('is_dark_mode') else False
        is_variable_spd_00_01 = request.args.get('is_variable_spd_00_01').lower() == 'true' if request.args.get('is_variable_spd_00_01') else False
        year_container = request.args.get('add_year_container').lower() == 'true' if request.args.get('add_year_container') else False
        set_yr_p1 = request.args.get('set_year_plus_one').lower() == 'true' if request.args.get('set_year_plus_one') else False
        hide_team = request.args.get('hide_team_logo').lower() == 'true' if request.args.get('hide_team_logo') else False
        ignore_sl = request.args.get('ignore_showdown_library').lower() == 'true' if request.args.get('ignore_showdown_library') else False
        is_random = name.upper() == '((RANDOM))'
        if is_random:
            # IF RANDOMIZED, ADD RANDOM NAME AND YEAR
            name, year = random_player_id_and_year()

        # LOAD PLAYER DATA
        error = 'Error loading player data. Make sure the player name and year are correct'
        scraper = BaseballReferenceScraper(name=name,year=year)
        img_url = None if url == '' else url
        img_name = None if img == '' else img
        set_number = set_num
        expansion = "FINAL" if expansion_raw == '' else expansion_raw
        edition = "NONE" if edition_raw == '' else edition_raw
        era = "DYNAMIC" if era_raw == '' else era_raw
        add_img_border = is_border if is_border else False
        is_dark_mode = dark_mode if dark_mode else False
        is_variable_speed_00_01 = is_variable_spd_00_01 if is_variable_spd_00_01 else False
        is_foil = False
        image_parallel = img_parallel_raw
        add_year_container = year_container if year_container else False
        set_year_plus_one = set_yr_p1 if set_yr_p1 else False
        hide_team_logo = hide_team if hide_team else False
        ignore_showdown_library = ignore_sl if ignore_sl else False
        trends_data = None
        statline = None

        # CREATE CARD
        error = "Error - Unable to create Showdown Card data."

        try:
            db = Firebase()
            # trends_collection_name = f'trends_{year}_{set}'
            # trends_data = db.query_firestore(trends_collection_name, document=scraper.baseball_ref_id_used_for_trends)
            # if date_override:
            #     statline = db.query_firestore(trends_collection_name, document=scraper.baseball_ref_id_used_for_trends, sub_collection=db.trends_full_stats_subcollection_name, sub_document=date_override)
            #     if statline is None:
            #         date_override = None
            showdown = db.load_showdown_card(
                ignore_showdown_library=ignore_showdown_library,
                bref_id = scraper.baseball_ref_id,
                year=year,
                context=set,
                expansion=expansion,
                edition=edition,
                player_image_path=img_name,
                player_image_url=img_url,
                offset=offset,
                set_number=set_number,
                add_image_border=add_img_border,
                is_dark_mode=is_dark_mode,
                is_variable_speed_00_01=is_variable_speed_00_01,
                image_parallel=image_parallel,
                team_override=scraper.team_override,
                set_year_plus_one=set_year_plus_one,
                pitcher_override=scraper.pitcher_override,
                hitter_override=scraper.hitter_override,
                hide_team_logo=hide_team_logo,
                date_override=date_override,
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
            if statline is None:
                try:
                    statline = scraper.player_statline()
                except:
                    if scraper.error:
                        error = scraper.error
            showdown = ShowdownPlayerCard(
                name=name,
                year=year,
                stats=statline,
                context=set,
                expansion=expansion,
                edition=edition,
                player_image_path=img_name,
                player_image_url=img_url,
                offset=offset,
                set_number=set_number,
                add_image_border=add_img_border,
                is_dark_mode=is_dark_mode,
                is_variable_speed_00_01=is_variable_speed_00_01,
                image_parallel=image_parallel,
                add_year_container=add_year_container,
                set_year_plus_one=set_year_plus_one,
                hide_team_logo=hide_team_logo,
                date_override=date_override,
                era=era,
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
            showdown.card_image()
            card_image_path = os.path.join('static', 'output', showdown.image_name)
        player_command = "Control" if showdown.is_pitcher else "Onbase"
        player_era = showdown.era.title()
        player_stats_data = showdown.player_data_for_html_table()
        player_points_data = showdown.points_data_for_html_table()
        player_accuracy_data = showdown.accuracy_data_for_html_table()
        player_ranks_data = showdown.rank_data_for_html_table()
        opponent_data = showdown.opponent_data_for_html_table()
        opponent_type = "Hitter" if showdown.is_pitcher else "Pitcher"
        radar_labels, radar_values = showdown.radar_chart_labels_as_values()
        radar_color = showdown.radar_chart_color()
        is_automated_image = showdown.is_automated_image
        player_name = showdown.name
        player_year = showdown.year
        player_context = showdown.context
        bref_url = showdown.bref_url
        shOPS_plus = showdown.projected['onbase_plus_slugging_plus'] if 'onbase_plus_slugging_plus' in showdown.projected else None
        name = player_name if is_random else name # LOG ACTUAL NAME IF IS RANDOMIZED PLAYER

        trends_diff = 0
        if trends_data:
            # IF TRENDS DATA EXISTS, CHECK IF CURRENT DAYS DATA IS INCLUDED. 
            # IF NOT, INCLUDE DATA FROM CARD GENERATED ABOVE
            current_date = datetime.now().strftime('%m-%d-%Y')
            if current_date not in trends_data.keys():
                player_data = showdown.__dict__
                included_keys = ['positions_and_defense', 'points', 'speed', 'chart', 'ip']
                reduced_player_data = {key: player_data[key] for key in included_keys}
                reduced_player_data['chart'] = {key: reduced_player_data['chart'][key] for key in ['command','outs']}
                trends_data[current_date] = reduced_player_data
            # SEE IF THE PLAYER WENT UP OR DOWN DAY OVER DAY
            dates_list = list(trends_data.keys())
            dates_list.sort(reverse=True)
            if len(dates_list) > 1:
                latest_pts = trends_data[dates_list[0]]['points']
                last_pts = trends_data[dates_list[1]]['points']
                trends_diff = latest_pts - last_pts
        
        # PARSE ERRORS AND SEND OUTPUT TO LOGS
        error = showdown.img_loading_error[:250] if showdown.img_loading_error else ''
        if len(error) > 0:
            print(error)
        log_card_submission_to_db(
            name=name,
            year=year,
            set=set,
            img_url=img_url,
            img_name=img_name,
            error=error,
            expansion=expansion,
            stats_offset=offset,
            set_num=set_num,
            is_dark_mode=is_dark_mode,
            is_variable_spd_00_01=is_variable_speed_00_01,
            is_random=is_random,
            is_automated_image=is_automated_image,
            is_foil=is_foil,
            is_stats_loaded_from_library=is_stats_loaded_from_library,
            is_img_loaded_from_library=is_img_loaded_from_library,
            add_year_container=add_year_container,
            ignore_showdown_library=ignore_showdown_library,
            set_year_plus_one=set_year_plus_one,
            edition=edition,
            hide_team_logo=hide_team_logo,
            date_override=date_override,
            era=era,
            image_parallel=image_parallel
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
            trends_data=trends_data,
            trends_diff=trends_diff,
            opponent=opponent_data,
            opponent_type=opponent_type,
            era=player_era,
            image_parallel=image_parallel
        )

    except Exception as e:
        error_full = str(e)[:250]
        print(error_full)
        log_card_submission_to_db(
            name=name,
            year=year,
            set=set,
            img_url=img_url,
            img_name=img_name,
            error=error_full,
            expansion=expansion,
            stats_offset=offset,
            set_num=set_num,
            is_dark_mode=is_dark_mode,
            is_variable_spd_00_01=is_variable_spd_00_01,
            is_random=is_random,
            is_automated_image=is_automated_image,
            is_foil=is_foil,
            is_stats_loaded_from_library=is_stats_loaded_from_library,
            is_img_loaded_from_library=is_img_loaded_from_library,
            add_year_container=add_year_container,
            ignore_showdown_library=ignore_showdown_library,
            set_year_plus_one=set_year_plus_one,
            edition=edition,
            hide_team_logo=hide_team_logo,
            date_override=date_override,
            era=era,
            image_parallel=image_parallel
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
            trends_data=None,
            trends_diff=0,
            opponent=None,
            opponent_type=None,
            era=None,
            image_parallel=None,
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
