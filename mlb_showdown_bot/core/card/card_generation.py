from pprint import pprint
from typing import Any
from prettytable import PrettyTable
from datetime import datetime

# INTERNAL
from .showdown_player_card import ShowdownPlayerCard, ImageSource, ShowdownImage, PlayerType
from .stats.baseball_ref_scraper import BaseballReferenceScraper
from .stats.stats_period import StatsPeriod, StatsPeriodType, StatsPeriodDateAggregation
from .stats.mlb_stats_api import MLBStatsAPI
from ..database.postgres_db import PostgresDB
from .utils.shared_functions import convert_to_date

def clean_kwargs(kwargs: dict) -> dict:
    """Clean the kwargs dictionary by removing 'image_' and 'image_source_' prefixes from keys."""
    for replacement in ['image_source_', 'image_',]:
        kwargs = {k.replace(replacement, ''): v for k, v in kwargs.items()}
    return kwargs

def generate_card(**kwargs) -> ShowdownPlayerCard:
    """Responsible for processing Showdown Bot Player Cards across API, CLI, and Web App."""

    # REMOVE `image` PREFIXES FROM KEYS
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

    return card

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
    for year_archive in yearly_archive_data:

        # BUILD SHOWDOWN CARD
        try:
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in [
                "name", "year", "stats", "stats_period", "player_type_override"
            ]}
            yearly_card = ShowdownPlayerCard(
                name=year_archive.name, 
                year=str(year_archive.year), 
                stats=year_archive.stats,
                stats_period=StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=str(year_archive.year)),
                player_type_override=year_archive.player_type_override,
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