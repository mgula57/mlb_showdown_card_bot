
import argparse
import os
import pandas as pd
# MY PACKAGES
from mlb_showdown.baseball_ref_scraper import BaseballReferenceScraper
from mlb_showdown.showdown_player_card_generator import ShowdownPlayerCardGenerator
from mlb_showdown.tests import analyze

parser = argparse.ArgumentParser(description="Get a player's stats for a year")
parser.add_argument('-n','--name', metavar='N',
                    help='The first and last name of the player')
parser.add_argument('-y','--year', metavar='Y',
                    help='The year of the player')
parser.add_argument('-c','--context', metavar='C',
                    help='The showdown year to output')
parser.add_argument('-o','--offset', metavar='O',
                    help='Get alternate chart n away from most accurate',default=0)
parser.add_argument('-cc','--is_cc', metavar='H',
                    help='Optionally make the card Cooperstown Collection',default=False)
parser.add_argument('-ss','--is_ss', metavar='S',
                    help='Optionally make the card Super Season',default=False)
parser.add_argument('-t','--test', metavar='T',
                    help='Boolean flag for whether to run accuracy test against original set',default=False)
parser.add_argument('-pt','--player_type', metavar='P',
                    help='Choose either Hitter or Pitcher to test',default='Hitter')
args = parser.parse_args()

def showdown_player_stats(is_from_cache=False):

    name = args.name.title()
    year = args.year

    if is_from_cache:
        real_player_stats_cache_path = os.path.join(os.path.dirname(__file__),'cache','player_cache.csv')
        name_year_string = '{} - {}'.format(name,str(year))
        try:
            real_player_stats_cache = pd.read_csv(real_player_stats_cache_path)
        except FileNotFoundError:
            print("No Local Cache File")
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
    if args.test:
        analyze(int(args.context), args.player_type, True)
    else:
        showdown_player_stats()
