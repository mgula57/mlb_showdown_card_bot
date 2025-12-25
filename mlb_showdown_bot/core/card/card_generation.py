from pprint import pprint
from typing import Any
from prettytable import PrettyTable
from datetime import datetime, timedelta
import traceback
import json

# INTERNAL
from .showdown_player_card import ShowdownPlayerCard, ImageSource, ShowdownImage, PlayerType, Team
from .stats.baseball_ref_scraper import BaseballReferenceScraper
from .stats.stats_period import StatsPeriod, StatsPeriodType, StatsPeriodDateAggregation
from .utils.shared_functions import convert_to_date, convert_year_string_to_list
from .trends.trends import CareerTrends, InSeasonTrends, TrendDatapoint
from ..database.postgres_db import PostgresDB, PlayerArchive

# STATS
from .stats.mlb_stats_api import MLBStatsAPI
from ..mlb_stats_api import MLBStatsAPI as MLBStatsAPI_V2
from ..fangraphs.client import FangraphsAPIClient
from ..statcast.client import StatcastAPIClient
from .stats.normalized_player_stats import PlayerStatsNormalizer, NormalizedPlayerStats, Datasource, PositionStats

def clean_kwargs(kwargs: dict) -> dict:
    """Clean the kwargs dictionary by removing 'image_' and 'image_source_' prefixes from keys."""
    for replacement in ['image_source_', 'image_',]:
        kwargs = {k.replace(replacement, ''): v for k, v in kwargs.items()}
    return kwargs

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
    stats: dict[str, Any] = {}
    card: ShowdownPlayerCard = None
    additional_logs: dict[str, Any] = {}
    final_card_payload: dict[str, Any] = {}

    # SETUP LOGGING
    log_to_db = kwargs.get('store_in_logs', False)
    card_log_db = kwargs.get('db_connection', None)
    if log_to_db:
        # CONNECT TO DB
        card_log_db = card_log_db or PostgresDB(is_archive=False)
        if not card_log_db.connection:
            card_log_db = None
            print("Failed to connect to database for logging. Continuing without logging.")
    else:
        card_log_db = None

    try:

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
        stats_period_type = kwargs.get('stats_period_type', 'REGULAR')
        stats_period = StatsPeriod(type=stats_period_type, **kwargs)
        stats: dict[str: any] = None

        expected_source = Datasource(kwargs.get('datasource', 'BREF'))
        scraper_load_time = None
        match expected_source:
            case Datasource.MLB_API:
                start_time = datetime.now()

                # PULL FROM MLB API
                # NORMALIZE FORMAT
                mlb_stats_api = MLBStatsAPI_V2()
                player_data = mlb_stats_api.build_full_player_from_search(search_name=kwargs.get('name', ''), stats_period=stats_period)
                normalized_player_stats = PlayerStatsNormalizer.from_mlb_api(player=player_data, stats_period=stats_period)

                # MLB API DOES NOT HAVE REQUIRED DEFENSIVE METRICS
                # GRAB FROM FANGRAPHS IF AVAILABLE
                if player_data.fangraphs_id:
                    fangraphs_api = FangraphsAPIClient()
                    fielding_stats_list = fangraphs_api.fetch_fielding_stats(
                        stats_period=stats_period,
                        position="all",
                        fangraphs_player_ids=[str(player_data.fangraphs_id)],
                    )
                    # INJECT INTO NORMALIZED STATS
                    position_stats = [PositionStats.from_fangraphs_fielding_stats(pos_stats) for pos_stats in fielding_stats_list]
                    normalized_player_stats.inject_defensive_stats_list(position_stats_list=position_stats, source=Datasource.FANGRAPHS)

                if stats_period.is_during_statcast_era:
                    statcast_api_client = StatcastAPIClient()
                    sprint_speed_data = statcast_api_client.fetch_sprint_speed_for_player(stats_period=stats_period, player_id=player_data.id)
                    normalized_player_stats.sprint_speed = sprint_speed_data.sprint_speed

                # TODO: EVENTUALLY PASS INTO SHOWDOWN PLAYER CARD AS CLASS
                stats = normalized_player_stats.model_dump(
                    exclude_none=True, 
                    exclude_unset=True, 
                    by_alias=True
                )
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
                        NormalizedPlayerStats(primary_datasource=Datasource.BREF, **d.stats) \
                            for d in player_archive_list \
                            if d.year in baseball_reference_stats.stats_period.year_list or baseball_reference_stats.stats_period.is_full_career
                    ]
                    if len(stats_yearly_list) > 0:
                        # COMBINE STATS FROM EACH YEAR
                        combined_stats = PlayerStatsNormalizer.combine_multi_year_stats(stats_yearly_list, stats_period=baseball_reference_stats.stats_period)
                        stats = combined_stats.model_dump(
                            exclude_none=True,
                            exclude_unset=True,
                            by_alias=True,
                        )
                        stats_period = baseball_reference_stats.stats_period
                        stats_period.year_list = [int(y) for y in combined_stats.years_played]
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

        # -----------------------------------
        # HIT MLB API FOR REALTIME STATS
        # ONLY APPLIES WHEN
        # 1. YEAR IS CURRENT YEAR
        # 2. REALTIME STATS ARE ENABLED
        # 3. STATS PERIOD IS REGULAR SEASON
        # -----------------------------------
        name_from_stats = stats.get('name', kwargs.get('name', None))
        team_abbreviation = stats.get('team_ID', None)
        is_pitcher = stats.get('type', PlayerType.HITTER.value) == PlayerType.PITCHER.value
        player_mlb_api_stats = MLBStatsAPI(
                                name=name_from_stats, stats_period=stats_period, 
                                team_abbreviation=team_abbreviation, is_pitcher=is_pitcher,
                                is_disabled=kwargs.get('disable_realtime', False)
                            )
        player_mlb_api_stats.populate_all_player_data()
        

        # PROCESS CARD
        image_source = ImageSource(**kwargs)
        image = ShowdownImage(source=image_source, **kwargs)
        card = ShowdownPlayerCard(
            stats_period=stats_period, 
            stats=stats, 
            realtime_game_logs=player_mlb_api_stats.game_logs, 
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
                latest_game_boxscore=player_mlb_api_stats.latest_game_boxscore,
                **kwargs
            )
            if in_season_trends_data:
                additional_logs["in_season_trends"] = in_season_trends_data.as_json() 
                # NEED DAY OVER DAY POINTS IN GAME BOXSCORE FOR DISPLAY PURPOSES
                game_pts_change = in_season_trends_data.pts_change.get('day', None)
                if player_mlb_api_stats.latest_game_boxscore and game_pts_change:
                    player_mlb_api_stats.latest_game_boxscore["game_player_pts_change"] = game_pts_change

        # ADD LATEST GAME BOX SCORE
        additional_logs["latest_game_box_score"] = player_mlb_api_stats.latest_game_boxscore

        # THERE WERE NO ERRORS IF WE GOT HERE
        additional_logs['error'] = None
        additional_logs['error_for_user'] = None

        # ADD ANY OTHER CONTEXTUAL LOGGING
        additional_logs['scraper_load_time'] = scraper_load_time

        # ADD CODE TO LOG CARD TO DB
        if card_log_db:
            card_log_db.log_card_submission(card=card, user_inputs=kwargs, additional_attributes=additional_logs)

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
            if is_user_year_before_player_career_start:
                error_for_user += year_range_error_message
            else:
                error_for_user += "If looking for a rookie try using their bref id as the name (ex: 'ramirjo01')"
        elif is_user_year_before_player_career_start:
            error_for_user = year_range_error_message

        print("--------- ERROR MESSAGE ---------")
        traceback.print_exc()
        print("---------------------------------")

        # ADD CODE TO LOG CARD TO DB
        if card_log_db:
            # LOG THE ERROR
            card_log_db.log_card_submission(
                card=card,  # NO FULL CARD WAS GENERATED DUE TO THE ERROR
                user_inputs=kwargs,
                additional_attributes={
                    'error': error_full,
                    'error_for_user': error_for_user,
                    'historical_season_trends': None,
                    'in_season_trends': None,
                    'latest_game_box_score': None,
                    'scraper_load_time': None,
                    'version': ''
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
    date_str_from_boxscore = latest_game_boxscore.get('date', None) if latest_game_boxscore else None
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
        end_date_minimum = min(datetime(year=int(year), month=4, day=1), datetime.now()).date()
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

def _convert_to_seasons_list(input: list | str | int) -> list[str | int]:
    """Convert input to a list of seasons."""
    if isinstance(input, int):
        return [input]
    elif isinstance(input, str):
        if input.lower() == 'career':
            return ['career']
        else:
            return convert_year_string_to_list(input)
    elif isinstance(input, list):
        return input
    else:
        return []