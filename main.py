
import argparse
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
parser.add_argument('-t','--test', metavar='T',
                    help='Get alternate chart n away from most accurate',default=False)
args = parser.parse_args()

def showdown_player_stats():

    scraper = BaseballReferenceScraper(name=args.name.title(),year=args.year)
    statline = scraper.player_statline()

    showdown = ShowdownPlayerCardGenerator(
        name=args.name,
        year=args.year,
        stats=statline,
        context=args.context,
        offset=args.offset,
        printOutput=True
    )

if __name__ == "__main__":
    # execute only if run as a script
    if args.test:
        analyze(int(args.context), 'Hitter')
    else:
        showdown_player_stats()
