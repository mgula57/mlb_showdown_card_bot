from pprint import pprint
from typing import Any
from prettytable import PrettyTable
from datetime import datetime
import traceback
import json

# INTERNAL
from .showdown_player_card import ShowdownPlayerCard, ImageSource, ShowdownImage, PlayerType
from .stats.baseball_ref_scraper import BaseballReferenceScraper
from .stats.stats_period import StatsPeriod, StatsPeriodType, StatsPeriodDateAggregation
from .stats.mlb_stats_api import MLBStatsAPI
from ..database.postgres_db import PostgresDB, PlayerArchive
from .utils.shared_functions import convert_to_date

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
    final_card_payload: dict[str, Any] = {}
    
    try:

        # REMOVE IMAGE PREFIXES FROM KEYS
        kwargs = clean_kwargs(kwargs)
        
        # PREPARE STATS
        stats_period_type = kwargs.get('stats_period_type', 'REGULAR')
        stats_period = StatsPeriod(type=stats_period_type, **kwargs)
        stats: dict[str: any] = None

        # SETUP BASEBALL REFERENCE SCRAPER
        # DONT ACTUALLY RUN IT YET
        baseball_reference_stats = BaseballReferenceScraper(stats_period=stats_period, **kwargs)    
        stats = baseball_reference_stats.fetch_player_stats()

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
        image = ShowdownImage(image_source=image_source, **kwargs)
        card = ShowdownPlayerCard(stats_period=stats_period, stats=stats, realtime_game_logs=player_mlb_api_stats.game_logs, image=image, **kwargs)
        final_card_payload['card'] = card.as_json()
        
        # EXTRA OPTIONS
        show_historical_points = kwargs.get("show_historical_points", False)
        in_season_trend_aggregation = kwargs.get("season_trend_date_aggregation", None)

        if show_historical_points:
            historical_season_trends_data = generate_all_historical_yearly_cards_for_player(actual_card=card, **kwargs)
            final_card_payload["historical_season_trends"] = historical_season_trends_data

        if in_season_trend_aggregation:
            in_season_trends_data = generate_in_season_trends_for_player(actual_card=card, date_aggregation=in_season_trend_aggregation, **kwargs)
            final_card_payload["in_season_trends"] = in_season_trends_data

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
        is_error_cannot_find_bref_page = "cannot find bref page" in error_full.lower() or ''
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

        traceback.print_exc()

        final_card_payload['error'] = error_for_user
    
        return final_card_payload

def generate_all_historical_yearly_cards_for_player(actual_card:ShowdownPlayerCard, **kwargs) -> list[dict]:
    """Generate all historical yearly cards for a player."""

    if actual_card.bref_id is None:
        return []
    
    # QUERY ARCHIVE FOR PLAYER
    db = PostgresDB(is_archive=True)
    yearly_archive_data = db.fetch_all_player_year_stats_from_archive(bref_id=actual_card.bref_id, type_override=actual_card.player_type_override)
    if len(yearly_archive_data) == 0:
        return []
    
    # REMOVE `image` PREFIXES FROM KEYS
    kwargs = clean_kwargs(kwargs)

    # ITERATE THROUGH EACH YEAR
    yearly_trends_data: dict[str: dict[str: Any]] = {}
    kwargs.pop('name', None) # Remove name from kwargs to avoid confusion
    kwargs.pop('print_to_cli', None) # Remove print_to_cli from kwargs to avoid confusion
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
                **filtered_kwargs
            )
            if yearly_card.player_type != actual_card.player_type:
                continue
            yearly_trends_data[int(year_archive.year)] = yearly_card.trend_line_data()
        except Exception as e:
            print(e)
            continue # SKIP YEAR
    
    if len(yearly_trends_data) > 0 and actual_card.stats_period.year_int is not None:
        latest_historical_year = max(yearly_trends_data.keys())
        if actual_card.stats_period.year_int > latest_historical_year:
            yearly_trends_data[str(actual_card.stats_period.year_int)] = actual_card.trend_line_data()

    if actual_card.print_to_cli and len(yearly_trends_data) > 0:
        # PRINT HISTORICAL POINTS
        print("\nHISTORICAL POINTS")
        avg_points = int(round(sum([c.get('points', 0) for c in yearly_trends_data.values()]) / len(yearly_trends_data)))
        table = PrettyTable(field_names=['AVG'] + list(yearly_trends_data.keys()))
        table.add_row([str(avg_points)] + [f"{c.get('points', 0)}" for c in yearly_trends_data.values()])
        print(table)
    
    # GET ALL HISTORICAL CARDS
    return yearly_trends_data

def generate_in_season_trends_for_player(actual_card: ShowdownPlayerCard, date_aggregation:str, **kwargs) -> dict[str: Any]:
    """Generate in-season trends for a player. Done on a weekly basis, showing points per week."""

    # REMOVE `image` PREFIXES FROM KEYS
    kwargs = clean_kwargs(kwargs)
    # ALSO REMOVE PRINT TO CLI
    kwargs.pop('print_to_cli', None)
    
    # CHECK FOR GAME LOGS
    game_logs = actual_card.stats.get(StatsPeriodType.DATE_RANGE.stats_dict_key, [])
    if len(game_logs) == 0 or actual_card.stats_period.is_multi_year:
        return {}
    
    # GET IN SEASON TRENDS
    in_season_trends_data: dict[str: dict] = {}
    year = actual_card.stats_period.year_list[0]
    player_first_date = convert_to_date(game_log_date_str=game_logs[0].get('date', game_logs[0].get('date_game', None)), year=year)
    player_last_date = convert_to_date(game_log_date_str=game_logs[-1].get('date', game_logs[-1].get('date_game', None)), year=year)
    date_ranges = StatsPeriodDateAggregation(date_aggregation.upper()).date_ranges(year=year, start_date=player_first_date, stop_date=player_last_date)
    for dr in date_ranges:
        start_date, end_date = dr
        end_date_str = end_date.strftime('%Y-%m-%d')
        end_date_minimum = min(datetime(year=int(year), month=4, day=1), datetime.now()).date()
        if end_date < end_date_minimum: continue # SKIP EARLY SEASON
        try:
            weekly_card = ShowdownPlayerCard(
                stats_period=StatsPeriod(type=StatsPeriodType.DATE_RANGE, year=str(year), start_date=start_date, end_date=end_date),
                stats=actual_card.stats,
                **kwargs,
            )
            in_season_trends_data[end_date_str] = weekly_card.trend_line_data()
        except Exception as e:
            print(e)
            continue

    # PRINT HISTORICAL POINTS
    if actual_card.print_to_cli and len(in_season_trends_data) > 0:
        print(f"\n{year} TRENDS POINTS")
        
        if len(in_season_trends_data.items()) > 8:
            # LIMIT TO LAST 8 WEEKS
            in_season_trends_data = {k: in_season_trends_data[k] for k in list(in_season_trends_data.keys())[-8:]}

        table = PrettyTable(field_names=list(in_season_trends_data.keys()))
        table.add_row([f"{c.get('points', 0)}" for c in in_season_trends_data.values()])

        print(table)

    return in_season_trends_data

def generate_random_player_id_and_year(year:str, era:str, edition:str) -> tuple[str, str]:
    """ Get Random Player Id and Year. Account for user inputs (if any).
    
    Args:
      year: User inputted year
      era: User inputted Era
      edition: User Inputted edition

    Return:
      Player Bref Id and Year
    """

    # CONNECT TO DB
    postgres_db = PostgresDB(is_archive=True)

    # IF NO CONNECTION, USE FILE
    if not postgres_db.connection:
        return None
    
    # QUERY DATABASE FOR RANDOM PLAYER
    random_player:PlayerArchive = postgres_db.fetch_random_player_stats_from_archive(year_input=year, era=era, edition=edition)
    
    # CLOSE CONNECTION
    postgres_db.close_connection()

    # RETURN RANDOM PLAYER IF MATCH WAS FOUND
    if random_player:
        return (random_player.bref_id, str(random_player.year))
