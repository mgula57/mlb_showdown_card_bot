import argparse
import os
import pandas as pd
# MY PACKAGES
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from .baseball_ref_scraper import BaseballReferenceScraper
    from .showdown_player_card_generator import ShowdownPlayerCardGenerator
except ImportError:
    # USE LOCAL IMPORT 
    from baseball_ref_scraper import BaseballReferenceScraper
    from showdown_player_card_generator import ShowdownPlayerCardGenerator

parser = argparse.ArgumentParser(description="Generate a player's MLB Showdown stats in a given year")
parser.add_argument('-n','--name', help='The first and last name of the player',required=True)
parser.add_argument('-y','--year', help='The year of the player',required=True)
parser.add_argument('-c','--context',help='The showdown set meta to use (2000-2005)',default='2000')
parser.add_argument('-o','--offset',help='Get alternate chart n away from most accurate',default=0)
parser.add_argument('-url','--image_url',help='URL link to Player background image',default=None)
parser.add_argument('-path','--image_path',help='Path to Player background image on local machine',default=None)
parser.add_argument('-num','--set_num',help='Assign card a set number',default='001')
parser.add_argument('-show','--show_image', action='store_true', help='Optionally open the final Player Card Image upon completion')
parser.add_argument('-cc','--is_cc', action='store_true', help='Optionally make the card Cooperstown Collection')
parser.add_argument('-ss','--is_ss', action='store_true', help='Optionally make the card Super Season')
args = parser.parse_args()

def main():
    """ Executed when running as a script """

    name = args.name.title()
    year = args.year

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
        player_image_url=args.image_url,
        player_image_path=args.image_path,
        print_to_cli=True,
        show_player_card_image=args.show_image,
        set_number=str(args.set_num)
    )

if __name__ == "__main__":
    main()