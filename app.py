from flask import Flask, render_template, request, jsonify
from mlb_showdown_bot.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
from mlb_showdown_bot.postgres_db import PostgresDB
from mlb_showdown_bot.classes.stats_period import StatsPeriod, StatsPeriodType, StatsPeriodDateAggregation, convert_to_date
import os
import pandas as pd
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from pprint import pprint
from time import sleep
from typing import Any

# ----------------------------------------------------------
# DATABASE
# ----------------------------------------------------------

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
    bref_id = db.Column(db.String(64))
    team = db.Column(db.String(32))
    data_source = db.Column(db.String(64))
    image_source = db.Column(db.String(64))
    scraper_load_time = db.Column(db.Numeric(10,2))
    card_load_time = db.Column(db.Numeric(10,2))
    is_secondary_color = db.Column(db.Boolean)
    nickname_index = db.Column(db.Integer)
    period = db.Column(db.String(64))
    period_start_date = db.Column(db.String(64))
    period_end_date = db.Column(db.String(64))
    period_split = db.Column(db.String(64))
    is_multi_colored = db.Column(db.Boolean)
    stat_highlights_type = db.Column(db.String(64))
    glow_multiplier = db.Column(db.Numeric(10,2))

    def __init__(self, name, year, set, is_cooperstown, is_super_season, img_url, img_name, error, is_all_star_game, expansion, stats_offset, set_num, is_holiday, is_dark_mode, is_rookie_season, is_variable_spd_00_01, is_random, is_automated_image, is_foil, is_stats_loaded_from_library, is_img_loaded_from_library, add_year_container, ignore_showdown_library, set_year_plus_one, edition, hide_team_logo, date_override, era, image_parallel, bref_id, team, data_source, image_source, scraper_load_time, card_load_time, is_secondary_color, nickname_index, period, period_start_date, period_end_date, period_split, is_multi_colored, stat_highlights_type, glow_multiplier):
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
        self.bref_id = bref_id
        self.team = team
        self.data_source = data_source
        self.image_source = image_source
        self.scraper_load_time = scraper_load_time
        self.card_load_time = card_load_time
        self.is_secondary_color = is_secondary_color
        self.nickname_index = nickname_index
        self.period = period
        self.period_start_date = period_start_date
        self.period_end_date = period_end_date
        self.period_split = period_split
        self.is_multi_colored = is_multi_colored
        self.stat_highlights_type = stat_highlights_type
        self.glow_multiplier = glow_multiplier

def log_card_submission_to_db(name, year, set, img_url, img_name, error, expansion, stats_offset, set_num, is_dark_mode, is_variable_spd_00_01, is_random, is_automated_image, is_foil, is_stats_loaded_from_library, is_img_loaded_from_library, add_year_container, ignore_showdown_library, set_year_plus_one, edition, hide_team_logo, date_override, era, image_parallel, bref_id, team, data_source, image_source, scraper_load_time, card_load_time, is_secondary_color, nickname_index, period, period_start_date, period_end_date, period_split, is_multi_colored, stat_highlights_type, glow_multiplier):
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
            image_parallel=image_parallel,
            bref_id = bref_id,
            team = team,
            data_source = data_source,
            image_source = image_source,
            scraper_load_time=scraper_load_time,
            card_load_time=card_load_time,
            is_secondary_color=is_secondary_color,
            nickname_index=nickname_index,
            period=period, 
            period_start_date=period_start_date, 
            period_end_date=period_end_date, 
            period_split=period_split,
            is_multi_colored=is_multi_colored,
            stat_highlights_type=stat_highlights_type,
            glow_multiplier=glow_multiplier
        )
        db.session.add(card_log)
        db.session.commit()
    except Exception as error:
        print('ERROR LOGGING TO DATABASE')
        print(error)
        return None


# ----------------------------------------------------------
# FRONT END
# ----------------------------------------------------------

@app.route('/')
def card_submission():
    return render_template('index.html')

@app.route('/card_creation')
def card_creator():

    # -----------------
    # FIELDS
    # -----------------

    # USER INPUTS
    name: str = None
    year: str = None
    set: str = None
    set_number: str = None
    expansion: str = None
    edition: str = None
    era: str = None
    chart_version: int = None
    image_parallel: str = None

    # PERIOD
    period_type: str = None
    period_start_date: str = None
    period_end_date: str = None
    period_split: str = None

    # OPTIONAL ADD-ONS
    img_url: str = None
    img_name: str = None
    add_img_border: bool = None
    is_dark_mode: bool = None
    is_variable_speed_00_01: bool = None
    show_year_text: bool = None
    ignore_showdown_library: bool = None
    set_year_plus_one: bool = None
    hide_team_logo: bool = None
    date_override: str = None
    is_secondary_color: bool = None
    ignore_cache: bool = None
    nickname_index: int = None
    is_multi_colored: bool = None
    stat_highlights_type: str = None
    glow_multiplier: float = None

    # RANDOMIZER
    is_random: bool = None
    
    # DERIVED FROM SHOWDOWN CARD CLASS
    is_automated_image: bool = False
    is_stats_loaded_from_library: bool = False
    is_img_loaded_from_library: bool = False
    bref_id: str = None
    team: str = None
    data_source: str = None
    image_source: str = None
    scraper_load_time: float = None
    card_load_time: float = None

    error: str = ''

    try:
        
        # -----------------
        # 1. PARSE INPUTS
        # -----------------

        error = 'Input Error. Please Try Again'

        # INPUTS
        name = request.args.get('name', '').title()
        year = str(request.args.get('year', ''))
        set = str(request.args.get('set', '')).upper()
        set_number = str(request.args.get('set_num', ''))
        expansion = str(request.args.get('expansion', 'BS'))
        edition = str(request.args.get('edition', 'NONE'))
        era = str(request.args.get('era', 'DYNAMIC'))
        chart_version = int(request.args.get('offset', 0)) + 1
        image_parallel = str(request.args.get('parallel', 'NONE'))

        period_type = request.args.get('period', None)
        period_start_date = request.args.get('period_start_date', None)
        period_end_date = request.args.get('period_end_date', None)
        period_split = request.args.get('period_split', None)

        # OPTIONALS
        img_url = request.args.get('url', None)
        img_name = request.args.get('img_name', None)
        add_img_border = request.args.get('addBorder', '').lower() == 'true'
        is_dark_mode = request.args.get('is_dark_mode', '').lower() == 'true'
        is_variable_speed_00_01 = request.args.get('is_variable_spd_00_01', '').lower() == 'true'
        show_year_text = request.args.get('show_year_text', '').lower() == 'true'
        ignore_showdown_library = request.args.get('ignore_showdown_library', '').lower() == 'true'
        set_year_plus_one = request.args.get('set_year_plus_one', '').lower() == 'true'
        hide_team_logo = request.args.get('hide_team_logo', '').lower() == 'true'
        is_secondary_color = request.args.get('is_secondary_color', '').lower() == 'true'
        is_multi_colored = request.args.get('is_multi_colored', '').lower() == 'true'
        ignore_cache = request.args.get('ignore_cache', '').lower() == 'true'
        nickname_index = request.args.get('nickname_index', None)
        nickname_index = None if len(str(nickname_index or '')) == 0 else nickname_index
        stat_highlights_type = request.args.get('stat_highlights_type', 'NONE')
        glow_multiplier = request.args.get('glow_multiplier', None)
        glow_multiplier = 1.0 if len(str(glow_multiplier or '')) == 0 else float(glow_multiplier)

        # DELAY SLIGHTLY IF IMG UPLOAD TO LET THE IMAGE FINISH UPLOADING
        if img_name:
            sleep(3)

        # RANDOM
        is_random = name.upper() == '((RANDOM))'
        if is_random:
            # IF RANDOMIZED, ADD RANDOM NAME AND YEAR
            name, year = random_player_id_and_year()

        # DEFINE PERIOD
        stats_period = StatsPeriod(type=period_type, year=year, start_date=period_start_date, end_date=period_end_date, split=period_split)

        # -----------------
        # 2. QUERY PLAYER STATS
        # -----------------
        error = 'Error loading player data. Make sure the player name and year are correct'
        scraper = BaseballReferenceScraper(name=name,year=year,stats_period=stats_period,ignore_cache=ignore_cache)
        statline: dict = None

        # IF NO CACHED SHOWDOWN CARD, FETCH REAL STATS FROM EITHER:
        #  1. ARCHIVE: HISTORICAL DATA IN POSTGRES DB
        #  2. SCRAPER: LIVE REQUEST FOR BREF/SAVANT DATA
        archived_data = None
        postgres_db = PostgresDB(is_archive=True)
        yearly_archive_data = postgres_db.fetch_all_player_year_stats_from_archive(bref_id=scraper.baseball_ref_id, type_override=scraper.player_type_override)
        if not ignore_cache:
            archived_data, archive_load_time = postgres_db.fetch_player_stats_from_archive(year=scraper.year_input, bref_id=scraper.baseball_ref_id, team_override=scraper.team_override, type_override=scraper.player_type_override, stats_period_type=stats_period.type)
        postgres_db.close_connection()

        # CHECK FOR ARCHIVED STATLINE. IF IT DOESN'T EXIST, QUERY BASEBALL REFERENCE / BASEBALL SAVANT
        if archived_data:
            statline = archived_data.stats
            data_source = 'Archive'
        else:
            data_source = 'Baseball Reference'
            try:
                statline = scraper.player_statline()
                data_source = scraper.source
            except:
                if scraper.error:
                    error = scraper.error   

        # -----------------
        # 3. RUN SHOWDOWN CARD
        # -----------------
        showdown_card = ShowdownPlayerCard(
            name=name,
            year=year,
            stats=statline,
            set=set,
            expansion=expansion,
            edition=edition,
            era=era,
            stats_period=stats_period,
            player_image_path=img_name,
            player_image_url=img_url,
            player_type_override=scraper.player_type_override,
            chart_version=chart_version,
            set_number=set_number,
            add_image_border=add_img_border,
            is_dark_mode=is_dark_mode,
            is_variable_speed_00_01=is_variable_speed_00_01,
            parallel=image_parallel,
            show_year_text=show_year_text,
            set_year_plus_one=set_year_plus_one,
            hide_team_logo=hide_team_logo,
            date_override=date_override,
            use_secondary_color=is_secondary_color,
            is_multi_colored=is_multi_colored,
            stat_highlights_type=stat_highlights_type,
            glow_multiplier=glow_multiplier,
            is_running_in_flask=True,
            source=data_source,
            nickname_index=nickname_index,
            ignore_cache=ignore_cache,
            warnings=scraper.warnings
        )

        # -----------------
        # 4. GENERATE CARD IMAGE
        # -----------------
        error = "Error - Unable to create Showdown Card Image."
        cached_img_link = showdown_card.cached_img_link()
        if cached_img_link:
            # USE IMAGE FROM GDRIVE
            card_image_path = cached_img_link
            is_img_loaded_from_library = True
        else:
            # GENERATE THE IMAGE
            is_img_loaded_from_library = False
            showdown_card.card_image()
            card_image_path = os.path.join('static', 'output', showdown_card.image.output_file_name)

        # -----------------
        # 5. CALCULATE TRENDS DATA
        # -----------------

        # YEARLY TRENDS
        yearly_trends_data: dict[str: dict[str: Any]] = None
        if len(yearly_archive_data) > 0:
            yearly_trends_data = {}
            for year_archive in yearly_archive_data:

                # BUILD SHOWDOWN CARD
                try:
                    yearly_card = ShowdownPlayerCard(
                        name=name, year=str(year_archive.year), stats=year_archive.stats, set=set, era=era,
                        stats_period=StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=str(year_archive.year)),
                        player_type_override=year_archive.player_type_override,
                        is_variable_speed_00_01=is_variable_speed_00_01,
                        is_running_in_flask=True,
                    )
                    if yearly_card.player_type != showdown_card.player_type:
                        continue
                    yearly_trends_data[str(year_archive.year)] = yearly_card.trend_line_data()
                except Exception as e:
                    print(e)
                    continue # SKIP YEAR
            
            if len(yearly_trends_data) > 0:
                latest_historical_year = max(yearly_trends_data.keys())
                if showdown_card.year > latest_historical_year:
                    yearly_trends_data[str(showdown_card.year)] = showdown_card.trend_line_data()

        # WEEKLY IN SEASON TRENDS
        in_season_trends_data: dict[str: Any] = None
        game_logs = statline.get(StatsPeriodType.DATE_RANGE.stats_dict_key, [])
        is_single_year = len(showdown_card.year_list) == 1
        if len(game_logs) > 0 and is_single_year:
            # GET IN SEASON TRENDS
            in_season_trends_data = {}
            year = showdown_card.year_list[0]
            player_first_date = convert_to_date(game_log_date_str=game_logs[0].get('date', game_logs[0].get('date_game', None)), year=year)
            player_last_date = convert_to_date(game_log_date_str=game_logs[-1].get('date', game_logs[-1].get('date_game', None)), year=year)
            date_ranges = StatsPeriodDateAggregation.WEEK.date_ranges(year=year, start_date=player_first_date, stop_date=player_last_date)
            for dr in date_ranges:
                start_date, end_date = dr
                end_date_str = end_date.strftime('%Y-%m-%d')
                try:
                    weekly_card = ShowdownPlayerCard(
                        name=name, year=str(year), stats=statline, set=set, era=era,
                        stats_period=StatsPeriod(type=StatsPeriodType.DATE_RANGE, year=str(year), start_date=start_date, end_date=end_date),
                        player_type_override=scraper.player_type_override,
                        is_variable_speed_00_01=is_variable_speed_00_01,
                        is_running_in_flask=True,
                    )
                    in_season_trends_data[end_date_str] = weekly_card.trend_line_data()
                except Exception as e:
                    print(e)
                    continue
        
        # -----------------
        # 6. SETUP METADATA SHOWN NEXT TO CARD
        # -----------------
        player_command = showdown_card.command_type
        player_era = showdown_card.era.value.title()
        player_stats_data = showdown_card.player_data_for_html_table()
        player_points_data = showdown_card.points_data_for_html_table()
        player_chart_versions_data = showdown_card.chart_accuracy_data_for_html_table()
        player_edition = showdown_card.image.edition.name.replace('_', ' ')
        opponent_data = showdown_card.opponent_data_for_html_table()
        opponent_type = "Hitter" if showdown_card.is_pitcher else "Pitcher"
        radar_labels, radar_values = showdown_card.radar_chart_labels_as_values()
        radar_color = showdown_card.radar_chart_color()
        is_automated_image = showdown_card.image.source.is_automated
        player_name = showdown_card.name
        player_year = showdown_card.year
        player_set = showdown_card.set.value
        bref_url = showdown_card.bref_url
        bref_id = showdown_card.bref_id
        team = showdown_card.team.value
        data_source = showdown_card.source
        image_source = showdown_card.image.source.type.value
        scraper_load_time = archive_load_time if data_source == 'Archive' else scraper.load_time
        card_load_time = showdown_card.load_time
        shOPS_plus = showdown_card.projected.get('onbase_plus_slugging_plus', None)
        name = player_name if is_random else name # LOG ACTUAL NAME IF IS RANDOMIZED PLAYER
        
        # PARSE ERRORS AND SEND OUTPUT TO LOGS
        error = showdown_card.image.error[:250] if showdown_card.image.error else ''
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
            stats_offset=chart_version,
            set_num=set_number,
            is_dark_mode=is_dark_mode,
            is_variable_spd_00_01=is_variable_speed_00_01,
            is_random=is_random,
            is_automated_image=is_automated_image,
            is_foil=False, # DEPRECATED
            is_stats_loaded_from_library=is_stats_loaded_from_library,
            is_img_loaded_from_library=is_img_loaded_from_library,
            add_year_container=show_year_text,
            ignore_showdown_library=ignore_showdown_library,
            set_year_plus_one=set_year_plus_one,
            edition=edition,
            hide_team_logo=hide_team_logo,
            date_override=date_override,
            era=era,
            image_parallel=image_parallel,
            bref_id=bref_id,
            team=team,
            data_source=data_source,
            image_source=image_source,
            scraper_load_time=scraper_load_time,
            card_load_time=card_load_time,
            is_secondary_color=is_secondary_color,
            nickname_index=nickname_index,
            period=period_type,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
            period_split=period_split,
            is_multi_colored=is_multi_colored,
            stat_highlights_type=stat_highlights_type,
            glow_multiplier=glow_multiplier
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
            player_chart_versions=player_chart_versions_data,
            player_name=player_name,
            player_year=player_year,
            player_set=player_set,
            bref_url=bref_url,
            radar_labels=radar_labels,
            radar_values=radar_values,
            radar_color=radar_color,
            shOPS_plus=shOPS_plus,
            yearly_trends_data=yearly_trends_data,
            in_season_trends_data=in_season_trends_data,
            trends_diff=0,
            opponent=opponent_data,
            opponent_type=opponent_type,
            era=player_era,
            edition=player_edition,
            expansion=expansion,
            chart_version=chart_version,
            image_parallel=image_parallel,
            period=showdown_card.stats_period.string,
            warnings=showdown_card.warnings
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
            stats_offset=chart_version,
            set_num=set_number,
            is_dark_mode=is_dark_mode,
            is_variable_spd_00_01=is_variable_speed_00_01,
            is_random=is_random,
            is_automated_image=is_automated_image,
            is_foil=False, # DEPRECATED
            is_stats_loaded_from_library=is_stats_loaded_from_library,
            is_img_loaded_from_library=is_img_loaded_from_library,
            add_year_container=show_year_text,
            ignore_showdown_library=ignore_showdown_library,
            set_year_plus_one=set_year_plus_one,
            edition=edition,
            hide_team_logo=hide_team_logo,
            date_override=date_override,
            era=era,
            image_parallel=image_parallel,
            bref_id=bref_id,
            team=team,
            data_source=data_source,
            image_source=image_source,
            scraper_load_time=scraper_load_time,
            card_load_time=card_load_time,
            is_secondary_color=is_secondary_color,
            nickname_index=nickname_index,
            period=period_type,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
            period_split=period_split,
            is_multi_colored=is_multi_colored,
            stat_highlights_type=stat_highlights_type,
            glow_multiplier=glow_multiplier
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
            player_chart_versions=None,
            player_name=None,
            player_year=None,
            player_set=None,
            bref_url=None,
            radar_labels=None,
            radar_values=None,
            radar_color=None,
            shOPS_plus=None,
            yearly_trends_data=None,
            in_season_trends_data=None,
            trends_diff=0,
            opponent=None,
            opponent_type=None,
            era=None,
            edition=None,
            expansion=None,
            chart_version=None,
            image_parallel=None,
            period=None,
            warnings=[]
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
    app.run(debug=True)
