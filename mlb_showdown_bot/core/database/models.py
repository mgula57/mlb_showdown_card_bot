
from flask_sqlalchemy import SQLAlchemy

# DECLARE DB OBJECT
db = SQLAlchemy()

# CARD LOG MODEL
class CardLog(db.Model):
    """ Model for logging card submissions to the database. """
    
    __tablename__ = 'card_log'

    # COLUMNS
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
    error_for_user = db.Column(db.String(256))

    # CONSTRUCTOR
    def __init__(self, name, year, set, is_cooperstown, is_super_season, img_url, img_name, 
                 error, is_all_star_game, expansion, stats_offset, set_num, is_holiday, is_dark_mode, 
                 is_rookie_season, is_variable_spd_00_01, is_random, is_automated_image, is_foil, is_stats_loaded_from_library, 
                 is_img_loaded_from_library, add_year_container, ignore_showdown_library, set_year_plus_one, edition, 
                 hide_team_logo, date_override, era, image_parallel, bref_id, team, data_source, image_source, 
                 scraper_load_time, card_load_time, is_secondary_color, nickname_index, 
                 period, period_start_date, period_end_date, period_split, 
                 is_multi_colored, stat_highlights_type, glow_multiplier, error_for_user):
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
        self.error_for_user = error_for_user

def log_card_submission_to_db(name, year, set, img_url, img_name, error, expansion, stats_offset, 
                              set_num, is_dark_mode, is_variable_spd_00_01, is_random, is_automated_image, 
                              is_foil, is_stats_loaded_from_library, is_img_loaded_from_library, add_year_container, 
                              ignore_showdown_library, set_year_plus_one, edition, hide_team_logo, date_override, era, 
                              image_parallel, bref_id, team, data_source, image_source, scraper_load_time, card_load_time, 
                              is_secondary_color, nickname_index, period, period_start_date, period_end_date, period_split, 
                              is_multi_colored, stat_highlights_type, glow_multiplier, error_for_user):
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
            glow_multiplier=glow_multiplier,
            error_for_user=error_for_user
        )
        db.session.add(card_log)
        db.session.commit()
    except Exception as error:
        print(f"Error logging card submission to DB: {error}")
        return None