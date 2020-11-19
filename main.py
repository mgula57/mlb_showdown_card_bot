
import argparse
import os
import pandas as pd
# MY PACKAGES
from mlb_showdown.baseball_ref_scraper import BaseballReferenceScraper
from mlb_showdown.showdown_player_card_generator import ShowdownPlayerCardGenerator

parser = argparse.ArgumentParser(description="Generate a player's MLB Showdown stats in a given year")
parser.add_argument('-n','--name', help='The first and last name of the player')
parser.add_argument('-y','--year', help='The year of the player')
parser.add_argument('-c','--context',help='The showdown set meta to use (2000-2005)',default='2000')
parser.add_argument('-o','--offset',help='Get alternate chart n away from most accurate',default=0)
parser.add_argument('-cc','--is_cc', action='store_true', help='Optionally make the card Cooperstown Collection')
parser.add_argument('-ss','--is_ss', action='store_true', help='Optionally make the card Super Season')
parser.add_argument('-ch','--use_cache', action='store_true', help='Load player stats from cache')
args = parser.parse_args()

def create_showdown_player_card():

    name = args.name.title()
    year = args.year

    if args.use_cache:
        real_player_stats_cache_path = os.path.join(os.path.dirname(__file__),'cache','player_cache.csv')
        name_year_string = '{} - {}'.format(name,str(year))
        try:
            real_player_stats_cache = pd.read_csv(real_player_stats_cache_path)
        except FileNotFoundError:
            print("ERROR: No Local Cache File Found")
        is_player_stats_in_cache = name_year_string in real_player_stats_cache.NameAndYear.values
        real_player_stats = real_player_stats_cache[real_player_stats_cache.NameAndYear == name_year_string]
        real_player_stats = real_player_stats.where(pd.notnull(real_player_stats), 0)
        statline = real_player_stats.to_dict('records')[0]
    else:
        scraper = BaseballReferenceScraper(name=name,year=year)
        statline = scraper.player_statline()

    showdown = ShowdownPlayerCardGenerator(
        name=name,
        year=year,
        stats=statline,
        is_cooperstown=args.is_cc,
        is_super_season=args.is_ss,
        context=args.context,
        offset=args.offset,
        printOutput=True
    )

if __name__ == "__main__":
    create_showdown_player_card()
