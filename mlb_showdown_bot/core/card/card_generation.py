from pprint import pprint

# INTERNAL
from .showdown_player_card import ShowdownPlayerCard, StatsPeriod, ImageSource, ShowdownImage
from .stats.baseball_ref_scraper import BaseballReferenceScraper
from .stats.mlb_stats_api import MLBStatsAPI

def generate_card(**kwargs) -> dict:
    """Responsible for processing Showdown Bot Player Cards across API, CLI, and Web App."""

    # REMOVE `image` PREFIXES FROM KEYS
    for replacement in ['image_source_', 'image_',]:
        kwargs = { k.replace(replacement, ''): v for k, v in kwargs.items() }
    
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
    player_mlb_api_stats = MLBStatsAPI(name=name_from_stats, stats_period=stats_period, team_abbreviation=team_abbreviation, is_disabled=kwargs.get('disable_realtime', False))
    player_mlb_api_stats.populate_all_player_data()

    # PROCESS CARD
    image_source = ImageSource(**kwargs)
    image = ShowdownImage(image_source=image_source, **kwargs)
    card = ShowdownPlayerCard(stats_period=stats_period, stats=stats, image=image, **kwargs)

    return card.as_json()