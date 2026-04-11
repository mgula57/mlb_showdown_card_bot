from pprint import pprint
from typing import Any
from prettytable import PrettyTable
from datetime import datetime, timedelta
import traceback
import json
import ast

# INTERNAL
from .showdown_player_card import ShowdownPlayerCard, ImageSource, ShowdownImage, PlayerType, Team, Edition
from ..data.replacement_season_averages import get_replacement_hitting_avgs, get_replacement_pitching_avgs
from .stats.baseball_ref_scraper import BaseballReferenceScraper
from .stats.stats_period import StatsPeriod, StatsPeriodType, StatsPeriodDateAggregation
from .utils.shared_functions import convert_to_date, convert_year_string_to_list
from .trends.trends import CareerTrends, InSeasonTrends, TrendDatapoint
from ..database.postgres_db import PostgresDB, PlayerArchive

# STATS
from .stats.mlb_stats_api import MLBStatsAPI
from ..mlb_stats_api import MLBStatsAPI as MLBStatsAPI_V2
from ..fangraphs.client import FangraphsAPIClient, FieldingStats
from ..statcast.client import StatcastAPIClient
from .stats.normalized_player_stats import PlayerStatsNormalizer, NormalizedPlayerStats, Datasource, PositionStats

def clean_kwargs(kwargs: dict) -> dict:
    """Clean the kwargs dictionary by removing 'image_' and 'image_source_' prefixes from keys."""
    for replacement in ['image_source_', 'image_',]:
        kwargs = {k.replace(replacement, ''): v for k, v in kwargs.items()}
    return kwargs

def check_for_preprocessed_card(**kwargs) -> ShowdownPlayerCard:
    """Check if a card with the given parameters has already been generated and stored in the database. If so, return that card instead of generating a new one."""
    
    showdown_set = kwargs.get('set', None)
    name = kwargs.get('name', None)
    year = kwargs.get('year', None)
    if not name or not showdown_set or not year:
        return None

    edition_raw = kwargs.get('edition', None)
    is_wbc = Edition(edition_raw) == Edition.WBC if edition_raw else False

    if is_wbc and str(year) in ['2025', '2026']:
        db = PostgresDB()
        return db.wbc_card_search(name, showdown_set, wbc_season=2026, exclude_mlb_players=True) # HARD CODE 2026 FOR NOW SINCE 2025 WBC NON-MLB CARDS ARE NOT AVAILABLE

    return None

def generate_card(**kwargs) -> dict[str, Any]:
    """
    Responsible for processing Showdown Bot Player Cards across API, CLI, and Web App.
    
    Output is a JSON object containing the following objects:
    - `card`: ShowdownPlayerCard object with all stats
    - `historical_season_trends`: List of historical yearly cards for the player, if `show_historical_points` is True
    - `in_season_trends`: Dictionary of in-season trends for the player, if `season_trend_date_aggregation` is provided
    - `latest_game_box_score`: Box score data for the player's latest game, if available
    - `error`: Error message if an error occurs during card generation, otherwise None

    Args:
        **kwargs: Keyword arguments that can include:
            - name: Name of the player (required)
            - year: Year of the player (required)
            - ... (other parameters as needed for card generation)
    
    Returns:
        A dictionary containing the card data and any additional information.
        If an error occurs, it will contain an 'error' key with the error message.
    """

    # SETUP KNOWN PARAMETERS
    stats: dict[str, Any] = kwargs.get('stats', None)
    card: ShowdownPlayerCard = None
    additional_logs: dict[str, Any] = {}
    final_card_payload: dict[str, Any] = {}

    # SETUP LOGGING
    log_to_db = kwargs.get('store_in_logs', False)
    db_for_logs = kwargs.get('db_connection', None)
    user_id = kwargs.get('user_id', None)
    if log_to_db:
        # CONNECT TO DB
        db_for_logs = db_for_logs or PostgresDB()
        if not db_for_logs.connection:
            db_for_logs = None
            print("Failed to connect to database for logging. Continuing without logging.")
    else:
        db_for_logs = None

    try:

        # LOG ORIGINAL NAME
        # WE LOG THIS BEFORE ANY PROCESSING BECAUSE WE WANT TO CAPTURE EXACTLY WHAT THE USER INPUT, EVEN IF IT CAUSED AN ERROR LATER ON
        kwargs['name_original'] = kwargs.get('name', None)

        # ADD RANDOM PLAYER ID AND YEAR IF NEEDED
        if kwargs.get('randomize', False):
            # GET RANDOM PLAYER ID AND YEAR
            random_player = generate_random_player(**kwargs)
            if random_player is None:
                raise Exception("Random Player Generation Failed")
            kwargs['name'] = random_player.bref_id
            kwargs['year'] = str(random_player.year)

        # REPLACE NAME WITH PLAYER ID IF PROVIDED
        disable_player_id = kwargs.get('datasource', 'BREF') == 'MLB_API' # TODO: REMOVE THIS LATER
        if kwargs.get('player_id', None) and not disable_player_id:
            kwargs['name'] = kwargs['player_id']

        # REMOVE IMAGE PREFIXES FROM KEYS
        kwargs = clean_kwargs(kwargs)

        # RAISE ERROR IF YEAR IS NOT PROVIDED BY USER OR SHUFFLE
        if kwargs.get('year', None) is None:
            raise Exception("Year is a required input.")
        
        # PREPARE STATS
        expected_source = Datasource(kwargs.get('datasource', 'BREF'))
        if expected_source == Datasource.MANUAL:
            if not stats:
                raise Exception("Stats must be provided when datasource is MANUAL.")
            
            try:
                try:
                    stats = json.loads(stats)
                except json.JSONDecodeError:
                    # Fall back to ast.literal_eval to support Python dict syntax (single quotes)
                    stats = ast.literal_eval(stats)
                kwargs.pop('stats') # Remove stats from kwargs since it's not needed beyond this point and can cause issues with ShowdownPlayerCard initialization
            except Exception as e:
                stats = {}
                raise Exception(f"Failed to parse stats JSON: {str(e)}")
        else:
            if stats is None and 'stats' in kwargs:
                kwargs.pop('stats')
        
        stats_period_type = kwargs.get('stats_period_type', 'REGULAR')
        stats_period = StatsPeriod(type=stats_period_type, **kwargs)

        # CHECK FOR YEAR IN THE FUTURE AND WBC
        edition_raw = kwargs.get('edition', None)
        edition = Edition(edition_raw) if edition_raw else None
        if edition == Edition.WBC and stats_period.year_int and stats_period.year_int == 2026 and datetime.now().month < 4:
            kwargs['year'] = '2025' # TEMPORARY FIX TO ALLOW WBC 2025 NON-MLB CARDS TO BE GENERATED BEFORE THE 2025 SEASON STARTS. WILL BE REMOVED ONCE 2025 WBC CARDS ARE AVAILABLE.
            stats_period = StatsPeriod(type=stats_period_type, **kwargs)

        # CHECK FOR PRE-PROCESSED CARD IN DB
        preprocessed_card = check_for_preprocessed_card(**kwargs)
        if preprocessed_card:
            
            # RESET IMAGE SETTINGS TO WHAT USER INPUTTED
            image_source = ImageSource(**kwargs)
            image = ShowdownImage(source=image_source, **kwargs)
            preprocessed_card.image = image
            preprocessed_card.generate_card_image(show=kwargs.get('show_image', False))

            if kwargs.get('print_to_cli', False): preprocessed_card.print_player()

            additional_logs['error'] = None
            additional_logs['error_for_user'] = None
            if db_for_logs: db_for_logs.log_custom_card_submission(card=preprocessed_card, user_inputs=kwargs, additional_attributes=additional_logs)

            final_card_payload = additional_logs
            final_card_payload['card'] = preprocessed_card.as_json()

            return final_card_payload # STOP PROCESSING

        
        scraper_load_time = None

        match expected_source:
            case Datasource.MLB_API:
                start_time = datetime.now()

                # PULL FROM MLB API
                # NORMALIZE FORMAT
                mlb_stats_api = MLBStatsAPI_V2()
                league = kwargs.get('league', 'MLB')
                # Strip all extra overrides from the search name (ex: "Shohei Ohtani (Pitching)" -> "Shohei Ohtani") to improve MLB API search results. MLB API is very bad at handling extra characters in the search query.
                search_name = kwargs.get('name', '')
                if search_name:
                    search_name = search_name.split('(')[0].strip()
                player_data = mlb_stats_api.build_full_player_from_search(search_name=search_name, stats_period=stats_period, league=league)
                if player_data is None:
                    raise Exception(f"Player not found in MLB API with name: {kwargs.get('name', '')} and year: {kwargs.get('year', '')}")
                normalized_player_stats = PlayerStatsNormalizer.from_mlb_api(player=player_data, stats_period=stats_period)

                # MLB API DOES NOT HAVE REQUIRED DEFENSIVE METRICS
                # GRAB FROM FANGRAPHS IF AVAILABLE
                has_pulled_fangraphs_defense = False
                defense_empty_warning = "Failed to fetch defensive stats. Using league avg for defense instead."
                if player_data.fangraphs_id and normalized_player_stats.type == PlayerType.HITTER:
                    try:
                        fangraphs_api = FangraphsAPIClient()
                        fielding_stats_list = fangraphs_api.fetch_leaderboard_stats(
                            stat_type="fld",
                            stats_period=stats_period,
                            position="all",
                            fangraphs_player_ids=[str(player_data.fangraphs_id)],
                        )
                        # INJECT INTO NORMALIZED STATS
                        position_stats = [PositionStats.from_fangraphs_fielding_stats(FieldingStats(**pos_stats)) for pos_stats in fielding_stats_list]
                        normalized_player_stats.inject_defensive_stats_list(position_stats_list=position_stats, source=Datasource.FANGRAPHS)
                        has_pulled_fangraphs_defense = True
                    except Exception as e:
                        if normalized_player_stats.warnings is None:
                            normalized_player_stats.warnings = []
                        if player_data.positions and len(player_data.positions) > 0 \
                            and list(player_data.positions.keys()) != ['DH']: # IF THE PLAYER HAS NO POSITIONS OR IS A DH, WE DON'T NEED TO WARN ABOUT MISSING DEFENSE
                            
                            normalized_player_stats.warnings.append(defense_empty_warning)

                # IF FANGRAPHS FAILS, USE STATCAST DEFENSE IF AVAILABLE
                if not has_pulled_fangraphs_defense and normalized_player_stats.type == PlayerType.HITTER and stats_period.is_during_statcast_era:
                    statcast_api_client = StatcastAPIClient()
                    oaa_dict = statcast_api_client.fetch_defense_for_player(stats_period=stats_period, mlb_player_id=player_data.id)
                    normalized_player_stats.inject_statcast_oaa(oaa_stats=oaa_dict)
                    if len(oaa_dict) > 0 and normalized_player_stats.warnings and defense_empty_warning in normalized_player_stats.warnings:
                        normalized_player_stats.warnings.remove(defense_empty_warning)
                        
                if not normalized_player_stats.bref_id and player_data.id:
                    db = PostgresDB(is_archive=True)
                    bref_id = db.fetch_bref_id_for_mlb_id(player_data.id)
                    db.close_connection()
                    normalized_player_stats.add_bref_id(bref_id)

                if stats_period.is_during_statcast_era and normalized_player_stats.type == PlayerType.HITTER:
                    statcast_api_client = StatcastAPIClient()
                    sprint_speed_data = statcast_api_client.fetch_sprint_speed_for_player(stats_period=stats_period, player_id=player_data.id)
                    normalized_player_stats.sprint_speed = sprint_speed_data.sprint_speed if sprint_speed_data else None

                # TODO: EVENTUALLY PASS INTO SHOWDOWN PLAYER CARD AS CLASS
                stats = normalized_player_stats.as_dict()
                stats_period.source = 'MLB Stats API'
                scraper_load_time = (datetime.now() - start_time).total_seconds()

            case Datasource.BREF:

                # SETUP BASEBALL REFERENCE SCRAPER
                baseball_reference_stats = BaseballReferenceScraper(stats_period=stats_period, **kwargs)

                # FOR MULTI-YEAR CARDS, FIRST CHECK ARCHIVE DB
                if baseball_reference_stats.stats_period.is_multi_year and not baseball_reference_stats.ignore_archive:
                    db = PostgresDB(is_archive=True)
                    player_archive_list: list[PlayerArchive] = db.fetch_all_player_year_stats_from_archive(
                        bref_id=baseball_reference_stats.baseball_ref_id,
                        type_override=baseball_reference_stats.player_type_override
                    ) or []
                    db.close_connection()

                    # FILTER TO YEARS IN STATS PERIOD
                    stats_yearly_list = [
                        NormalizedPlayerStats(primary_datasource=Datasource.BREF, year_id=str(d.year), **( d.stats | ({'year_ID': str(d.year)} if d.stats.get('year_ID', None) is None else {}) )) \
                            for d in player_archive_list \
                            if (d.year in baseball_reference_stats.stats_period.year_list or baseball_reference_stats.stats_period.is_full_career) \
                                and d.stats is not None and len(d.stats) > 0
                    ]
                    if len(stats_yearly_list) > 0:
                        # COMBINE STATS FROM EACH YEAR
                        combined_stats = PlayerStatsNormalizer.combine_multi_year_stats(stats_yearly_list, stats_period=baseball_reference_stats.stats_period)
                        stats = combined_stats.as_dict()
                        stats_period = baseball_reference_stats.stats_period
                        stats_period.year_list = [int(y.year_id) for y in stats_yearly_list]
                        stats_period.source = 'Archive'
                    
                # FETCH STATS THE OLD WAY
                if not stats:
                    stats = baseball_reference_stats.fetch_player_stats()

                    # UPDATE STATS PERIOD BASED ON BREF STATS
                    stats_period = baseball_reference_stats.stats_period
                    stats['warnings'] = baseball_reference_stats.warnings
                    scraper_load_time = baseball_reference_stats.load_time

                # ALWAYS APPLY THESE
                kwargs['player_type_override'] = baseball_reference_stats.player_type_override
                kwargs['team_override'] = baseball_reference_stats.team_override

            case Datasource.MANUAL:
                """"""

        # -----------------------------------
        # HIT MLB API FOR REALTIME STATS
        # ONLY APPLIES WHEN
        # 1. YEAR IS CURRENT YEAR
        # 2. REALTIME STATS ARE ENABLED
        # 3. STATS PERIOD IS REGULAR SEASON
        # -----------------------------------
        game_boxscore: dict = None
        existing_game_logs = stats.get('game_logs', None) or []
        pull_latest_game_data = expected_source in [Datasource.MLB_API] \
                                and stats_period.is_this_year \
                                and not kwargs.get('disable_realtime', False) \
                                and stats_period.check_for_realtime_stats \
                                and len(existing_game_logs) > 0
        if pull_latest_game_data:
            try:
                latest_game = existing_game_logs[-1]
                game_date_str = latest_game.get('date', None)
                game_pk = latest_game.get('game_pk', None)
                if game_pk and game_date_str and datetime.strptime(game_date_str, "%Y-%m-%d").date() >= (datetime.now().date() - timedelta(days=1)):
                    mlb_stats_api = MLBStatsAPI_V2()
                    game_boxscore = mlb_stats_api.games.get_game_boxscore(game_pk)
            except Exception as e:
                print("Error loading game: ", e)

        # IF WBC CARD, WE HAVE TO CHECK THE DB FOR WHAT TEAM THEY WERE ON:
        edition_str = kwargs.get('edition', None)
        edition = Edition(edition_str) if edition_str else None
        if edition and edition == Edition.WBC:
            db = PostgresDB()
            wbc_team_info = db.fetch_wbc_team_for_player(bref_id=baseball_reference_stats.baseball_ref_id, year=stats_period.year_int)
            if wbc_team_info:
                wbc_team_abbreviation, wbc_team_year = wbc_team_info
                kwargs['wbc_team'] = wbc_team_abbreviation
                kwargs['wbc_year'] = wbc_team_year
            else:
                # Remove edition and warn user
                kwargs.pop('edition', None)
                stats['warnings'] = stats.get('warnings', []) + ["Could not find WBC team for this player in the database. Double check the player was a part of a WBC roster in the year provided or following year. Note that non-MLB WBC players are only available for 2025/2026."]

        # PROCESS CARD
        image_source = ImageSource(**kwargs)
        image = ShowdownImage(source=image_source, **kwargs)
        card = ShowdownPlayerCard(
            stats_period=stats_period, 
            stats=stats, 
            realtime_game_logs=[game_boxscore] if game_boxscore else None, 
            image=image,
            warnings=stats.get('warnings', []),
            **kwargs
        )

        # EXTRA OPTIONS
        show_historical_points = kwargs.get("show_historical_points", False)
        in_season_trend_aggregation = kwargs.get("season_trend_date_aggregation", None)

        if show_historical_points:
            historical_season_trends_data = generate_all_historical_yearly_cards_for_player(actual_card=card, **kwargs)
            additional_logs["historical_season_trends"] = historical_season_trends_data.as_json() if historical_season_trends_data else None

        if in_season_trend_aggregation:
            in_season_trends_data = generate_in_season_trends_for_player(
                actual_card=card, 
                date_aggregation=in_season_trend_aggregation, 
                latest_game_boxscore=game_boxscore,
                **kwargs
            )
            if in_season_trends_data:
                additional_logs["in_season_trends"] = in_season_trends_data.as_json() 
                # NEED DAY OVER DAY POINTS IN GAME BOXSCORE FOR DISPLAY PURPOSES
                game_pts_change = in_season_trends_data.pts_change.get('day', None)
                if game_boxscore and game_pts_change:
                    game_boxscore['game_player_pts_change'] = game_pts_change

        # ADD LATEST GAME BOX SCORE
        additional_logs["latest_game_box_score"] = game_boxscore

        # THERE WERE NO ERRORS IF WE GOT HERE
        additional_logs['error'] = None
        additional_logs['error_for_user'] = None

        # ADD ANY OTHER CONTEXTUAL LOGGING
        additional_logs['scraper_load_time'] = scraper_load_time

        # ADD CODE TO LOG CARD TO DB
        if db_for_logs:
            db_for_logs.log_custom_card_submission(card=card, user_inputs=kwargs, additional_attributes=additional_logs)

        # CONVERT CARD TO DICT AND RETURN IT
        final_card_payload = additional_logs
        final_card_payload['card'] = card.as_json()

        return final_card_payload

    except Exception as e:

        error_full = str(e)[:250]

        # INPUTS
        name = kwargs.get('name', 'Unknown Player')
        year = kwargs.get('year', 'Unknown Year')
        stats = stats or {}

        # HELPFUL CONTEXT FOR ERRORS
        try: input_year_int = int(year)
        except: input_year_int = None
        player_years_as_strings = stats.get('years_played', [])
        player_years_as_ints = [int(y) for y in player_years_as_strings]
        first_year = min(player_years_as_ints) if len(player_years_as_ints) > 0 else 0
        last_year = max(player_years_as_ints) if len(player_years_as_ints) > 0 else 9999

        # CHANGE LAST YEAR TO CURRENT YEAR IF ARCHIVE IS AS OF LAST YEAR
        # ONLY APPLIES IF MLB SEASON HAS STARTED AND ITS BEFORE NOVEMBER
        current_year = datetime.now().year
        current_month = datetime.now().month
        if last_year == (current_year - 1) and current_month >= 3 and current_month < 11:
            last_year = current_year

        # FINAL BOOLS
        is_user_year_before_player_career_start = input_year_int < first_year if input_year_int else False
        is_error_cannot_find_bref_page = "cannot find bref page" in (error_full.lower() or '')
        is_error_too_many_requests_to_bref = "429 - TOO MANY REQUESTS TO " in error_full.upper() and "baseball-ref" in error_full.lower()

        # ERROR SENT TO USER
        error_for_user = error_full
        year_range_error_message = f"The year you selected ({year}) falls outside of {name}'s career span, which is from {first_year} to {last_year}."
        if is_error_too_many_requests_to_bref:
            # ALERT USER THAT BREF IS LOCKING OUT THE BOT
            error_for_user = "There have been too many Bot requests to bref in the last hour. Try again in 30-60 mins."
        elif is_error_cannot_find_bref_page:
            # TRY TO GIVE CONTEXT INTO WHY A BASEBALL REFERENCE PAGE WAS NOT FOUND FOR THE NAME/YEAR
            error_for_user = "Player/year not found on Baseball Reference. "
            edition_raw = kwargs.get('edition', None)
            edition = edition_raw if edition_raw and type(edition_raw) == Edition else Edition(edition_raw)
            if is_user_year_before_player_career_start:
                error_for_user += year_range_error_message
            elif edition == Edition.WBC:
                error_for_user += "For non-MLB WBC players, customs are only available for 2025/2026. For MLB WBC players, double check the player was a part of a WBC roster in the year provided or following year."
            else:
                error_for_user += "If looking for a rookie try using their bref id as the name (ex: 'ramirjo01')"
        elif is_user_year_before_player_career_start:
            error_for_user = year_range_error_message

        print("--------- ERROR MESSAGE ---------")
        traceback.print_exc()
        print("---------------------------------")

        # ADD CODE TO LOG CARD TO DB
        if db_for_logs:
            # LOG THE ERROR
            db_for_logs.log_custom_card_submission(
                card=card,  # NO FULL CARD WAS GENERATED DUE TO THE ERROR
                user_inputs=kwargs,
                additional_attributes={
                    'error': error_full,
                    'error_for_user': error_for_user,
                    'historical_season_trends': None,
                    'in_season_trends': None,
                    'latest_game_box_score': None,
                    'scraper_load_time': None,
                    'version': '',
                    'user_id': user_id,
                }
            )

        final_card_payload = {
            'card': card.as_json() if card else None,  # NO FULL CARD WAS GENERATED DUE TO THE ERROR
            'error': error_full,
            'error_for_user': error_for_user,
            'historical_season_trends': None,
            'in_season_trends': None,
            'latest_game_box_score': None,
        }
    
        return final_card_payload

def generate_all_historical_yearly_cards_for_player(actual_card:ShowdownPlayerCard, **kwargs) -> CareerTrends:
    """Generate all historical yearly cards for a player."""

    if actual_card.bref_id is None:
        return None
    
    # QUERY ARCHIVE FOR PLAYER
    db = PostgresDB(is_archive=True)
    yearly_archive_data = db.fetch_all_player_year_stats_from_archive(bref_id=actual_card.bref_id, type_override=actual_card.player_type_override)
    if len(yearly_archive_data) == 0:
        return None

    # ITERATE THROUGH EACH YEAR
    yearly_trends_data: dict[str, TrendDatapoint] = {}
    kwargs.pop('name', None) # Remove name from kwargs to avoid confusion
    kwargs.pop('print_to_cli', None) # Remove print_to_cli from kwargs to avoid confusion
    kwargs.pop('show_image', None) # Remove show_image from kwargs to avoid confusion
    kwargs.pop('chart_version', None) # Remove year from kwargs to avoid confusion
    
    for year_archive in yearly_archive_data:

        # BUILD SHOWDOWN CARD
        try:
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in [
                "name", "year", "stats", "stats_period", "player_type_override",
            ]}
            yearly_card = ShowdownPlayerCard(
                name=year_archive.name, 
                year=str(year_archive.year), 
                stats=year_archive.stats,
                stats_period=StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=str(year_archive.year)),
                player_type_override=year_archive.player_type_override,
                print_to_cli=False,
                show_image=False,
                chart_version=1,
                **filtered_kwargs
            )
            if yearly_card.player_type != actual_card.player_type:
                continue
            yearly_trends_data[int(year_archive.year)] = yearly_card.trend_line_data()
        except Exception as e:
            print(e)
            continue # SKIP YEAR
    
    # ADD CURRENT YEAR
    if len(yearly_trends_data) > 0 and actual_card.stats_period.year_int is not None:
        latest_historical_year = max(yearly_trends_data.keys())
        if actual_card.stats_period.year_int > latest_historical_year:
            yearly_trends_data[str(actual_card.stats_period.year_int)] = actual_card.trend_line_data()

    if actual_card.print_to_cli and len(yearly_trends_data) > 0:
        # PRINT HISTORICAL POINTS
        print("\nHISTORICAL POINTS")
        avg_points = int(round(sum([c.points for c in yearly_trends_data.values()]) / len(yearly_trends_data)))
        table = PrettyTable(field_names=['AVG'] + list(yearly_trends_data.keys()))
        table.add_row([str(avg_points)] + [f"{c.points}" for c in yearly_trends_data.values()])
        print(table)
    
    # GET ALL HISTORICAL CARDS
    return CareerTrends(yearly_trends=yearly_trends_data)

def generate_in_season_trends_for_player(actual_card: ShowdownPlayerCard, date_aggregation:str, team_override:Team | str = None, latest_game_boxscore:dict=None, **kwargs) -> InSeasonTrends:
    """Generate in-season trends for a player. Done on a weekly or monthly basis, showing points per week."""

    # REMOVE PRINT TO CLI
    kwargs.pop('print_to_cli', None)
    kwargs.pop('show_image', None)
    kwargs.pop('chart_version', None)
    
    # CHECK FOR GAME LOGS
    game_logs = actual_card.stats.get(StatsPeriodType.DATE_RANGE.stats_dict_key, [])
    if len(game_logs) == 0 or actual_card.stats_period.is_multi_year:
        return None
    
    # FILTER TO SINGLE TEAM IF OVERRIDE IS PROVIDED
    if team_override:
        team_filter_value = team_override.value if isinstance(team_override, Team) else team_override
        game_logs = [gl for gl in game_logs if gl.get('team_ID', 'n/a') == team_filter_value]

    # DEFINE THE OBJECT
    in_season_trends = InSeasonTrends(cumulative_trends_date_aggregation=date_aggregation.upper())

    # GET IN SEASON TRENDS
    year = actual_card.stats_period.year_list[0]
    player_first_date = convert_to_date(game_log_date_str=game_logs[0].get('date', game_logs[0].get('date_game', None)), year=year)
    player_last_date = convert_to_date(game_log_date_str=game_logs[-1].get('date', game_logs[-1].get('date_game', None)), year=year)
    
    # DEFINE DATE RANGES
    date_ranges = StatsPeriodDateAggregation(date_aggregation.upper()).date_ranges(year=year, start_date=player_first_date, stop_date=player_last_date)
    date_str_from_boxscore = latest_game_boxscore.get('datetime', {}).get('official_date', None) if latest_game_boxscore else None
    is_day_over_day_comparison = False
    if date_str_from_boxscore:
        # IF LATEST GAME DATE = THE PLAYER LAST DATE:
        # ADD A TREND POINT FOR THE LATEST GAME'S DATE -1
        date_from_boxscore = convert_to_date(game_log_date_str=date_str_from_boxscore, year=year)
        if date_from_boxscore == player_last_date:
            yesterday = date_from_boxscore - timedelta(days=1)
            # APPEND AT SECOND TO LAST POSITION
            date_ranges.insert(-1, (player_first_date, yesterday))
            is_day_over_day_comparison = True

    in_season_trends_data: dict[str, TrendDatapoint] = {}
    for dr in date_ranges:
        start_date, end_date = dr
        end_date_str = end_date.strftime('%Y-%m-%d')
        end_date_minimum = min(datetime(year=int(year), month=3, day=28), datetime.now()).date()
        if end_date < end_date_minimum: continue # SKIP EARLY SEASON
        try:
            weekly_card = ShowdownPlayerCard(
                stats_period=StatsPeriod(type=StatsPeriodType.DATE_RANGE, year=str(year), start_date=start_date, end_date=end_date),
                stats=actual_card.stats,
                chart_version=1,
                **kwargs,
            )
            in_season_trends_data[end_date_str] = weekly_card.trend_line_data()
        except Exception as e:
            print(e)
            continue

    # RETURN NONE IF NO TRENDS FOUND
    trends_data_count = len(in_season_trends_data)
    if trends_data_count == 0:
        return None
    
    # STORE INSIDE OBJECT
    in_season_trends.cumulative_trends = in_season_trends_data

    # ADD COMPARISONS
    if trends_data_count > 1:

        # CARDS USED FOR COMPARISON
        current_card = in_season_trends.cumulative_trends[list(in_season_trends.cumulative_trends.keys())[-1]]
        last_card = in_season_trends.cumulative_trends[list(in_season_trends.cumulative_trends.keys())[-2]]

        # DAY
        if is_day_over_day_comparison:
            # GET THE LAST TWO DAYS
            in_season_trends.pts_change['day'] = int(current_card.points - last_card.points)

        # WEEK
        last_weeks_card = in_season_trends.cumulative_trends[list(in_season_trends.cumulative_trends.keys())[-3]] if is_day_over_day_comparison and trends_data_count > 2 else last_card
        in_season_trends.pts_change['week'] = int(current_card.points - last_weeks_card.points)

    # PRINT HISTORICAL POINTS
    if actual_card.print_to_cli and len(in_season_trends.cumulative_trends) > 0:
        print(f"\n{year} TRENDS POINTS")

        if len(in_season_trends.cumulative_trends.items()) > 8:
            # LIMIT TO LAST 8 WEEKS
            in_season_trends.cumulative_trends = {k: in_season_trends.cumulative_trends[k] for k in list(in_season_trends.cumulative_trends.keys())[-8:]}

        table = PrettyTable(field_names=list(in_season_trends.cumulative_trends.keys()))
        table.add_row([f"{c.points}" for c in in_season_trends.cumulative_trends.values()])

        print(table)

        pts_change = in_season_trends.pts_change.get('day', None)
        if pts_change is not None:
            print(f"Day over Day: {'+' if pts_change > 0 else ''}{int(pts_change)}")

    return in_season_trends

def generate_random_player(**kwargs) -> PlayerArchive:
    """ Get Random Player Id and Year. Account for user inputs (if any).
    
    Args:
        **kwargs: Keyword arguments that can include:
            - year: Year of the player (optional)
            - era: Era of the player (optional)
            - edition: Edition of the player (optional)

    Return:
      Player Bref Id and Year
    """

    # CONNECT TO DB
    postgres_db = PostgresDB(is_archive=True)

    # IF NO CONNECTION, USE FILE
    if not postgres_db.connection:
        return (None, None)
    
    # QUERY DATABASE FOR RANDOM PLAYER
    random_player:PlayerArchive = postgres_db.fetch_random_player_stats_from_archive(
        year_input=kwargs.get('year', None),
        era=kwargs.get('era', None),
        edition=kwargs.get('edition', None)
    )

    # CLOSE CONNECTION
    postgres_db.close_connection()

    # RETURN RANDOM PLAYER IF MATCH WAS FOUND
    if random_player:
        return random_player

def generate_cards(player_ids: list[str], years: list[int], **kwargs) -> list[ShowdownPlayerCard]:
    """Generate multiple cards for a list of player ids and a year. Only works with MLB API datasource.

    Args:
        player_ids: List of player ids to generate cards for
        years: List of years to generate cards for
        **kwargs: Keyword arguments to pass to card generation function

    Returns:
        List of generated ShowdownPlayerCard objects
    """

    # Remove stats kwarg since we will be pulling stats from the MLB API
    if 'stats' in kwargs:
        kwargs.pop('stats')

    # Pull stats across player ids
    mlb_api = MLBStatsAPI_V2()
    player_stats = mlb_api.build_players_from_id_list(
        player_ids=player_ids,
        seasons=years
    )
    if len(player_stats.players) == 0:
        print("No players found for the provided player ids and years.")
        return []

    # Get statcast sprint speed data for all players if applicable
    statcast_api_client = StatcastAPIClient()
    sprint_speed_data = statcast_api_client.fetch_sprint_speed_leaderboard(years[0])

    # Get Fangraphs defensive stats for all players if applicable
    fangraphs_api = FangraphsAPIClient()
    fielding_stats_list = fangraphs_api.fetch_leaderboard_stats(
        stat_type="fld",
        season_start=years[0],
        season_end=years[-1],
        position="all",
        fangraphs_player_ids=player_stats.fangraphs_ids,
    )

    # Generate cards for each player
    final_cards: list[ShowdownPlayerCard] = []
    for player_data in player_stats.players:
        try:
            normalized_player_stats = PlayerStatsNormalizer.from_mlb_api(
                player=player_data, 
                stats_period=StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=str(years[0]))
            )

            # Inject sprint speed if available
            if sprint_speed_data and normalized_player_stats.type == PlayerType.HITTER:
                player_sprint_speed_data = next((s for s in sprint_speed_data if s.player_id == player_data.id), None)
                if player_sprint_speed_data:
                    normalized_player_stats.sprint_speed = player_sprint_speed_data.sprint_speed

            # Inject defensive stats if available
            position_stats = [PositionStats.from_fangraphs_fielding_stats(FieldingStats(**pos_stats)) for pos_stats in fielding_stats_list if pos_stats.get('xMLBAMID', None) == player_data.id]
            if position_stats and normalized_player_stats.type == PlayerType.HITTER:
                normalized_player_stats.inject_defensive_stats_list(position_stats_list=position_stats, source=Datasource.FANGRAPHS)

            if normalized_player_stats.is_missing_stats:
                print(f"Skipping card generation for {player_data.full_name} in {years[0]} due to missing stats.")
                continue

            card = ShowdownPlayerCard(
                name=player_data.full_name,
                stats_period=StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=str(years[0])), 
                stats=normalized_player_stats.as_dict(), 
                image=ShowdownImage(**kwargs),
                **kwargs
            )
            final_cards.append(card)
        except Exception as e:
            import traceback
            traceback.print_exc()
            continue
    
    return final_cards