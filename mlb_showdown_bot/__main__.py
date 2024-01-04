import argparse
from pprint import pprint
import os, json
from pathlib import Path

# MY PACKAGES
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from .firebase import Firebase
    from .baseball_ref_scraper import BaseballReferenceScraper
    from .showdown_player_card import ShowdownPlayerCard
    from .classes.stats_period import StatsPeriod
    from .postgres_db import PostgresDB
except ImportError:
    # USE LOCAL IMPORT 
    from firebase import Firebase
    from baseball_ref_scraper import BaseballReferenceScraper
    from showdown_player_card import ShowdownPlayerCard
    from classes.stats_period import StatsPeriod
    from postgres_db import PostgresDB

parser = argparse.ArgumentParser(description="Generate a player's MLB Showdown stats in a given year")

# REQUIRED INPUTS
parser.add_argument('-n','--name', help='The first and last name of the player',required=True)
parser.add_argument('-y','--year', help='The year of the player',required=True)

# SET
parser.add_argument('-s','--set',help='The showdown set meta to use (2000-2005)',default='2000')
parser.add_argument('-e','--era',help='The baseball era to use.',default='DYNAMIC')

# IMAGE
parser.add_argument('-url','--image_url',help='URL link to Player background image',default=None)
parser.add_argument('-path','--image_path',help='Path to Player background image on local machine',default=None)
parser.add_argument('-o_path','--image_output_path',help='Path to folder for card image output',default='')
parser.add_argument('-exp','--expansion',help='Add optional expansion logo (ex: TD, PR)',default='BS')
parser.add_argument('-ed','--edition',help='Add optional edition (Values: None, Super Season, All-Star Game, Cooperstown Collection, Holiday, Nationality, Rookie Season)',default='NONE')
parser.add_argument('-num','--set_num',help='Assign card a set number',default='')
parser.add_argument('-show','--show_image', action='store_true', help='Optionally open the final Player Card Image upon completion')
parser.add_argument('-pl','--parallel', help='Optionally add image parallel design like Rainbow Foil, Black & White, Sparkle, etc.', default='NONE', type=str)
parser.add_argument('-bor','--add_border', action='store_true', help='Optionally add border to player image')
parser.add_argument('-dark','--dark_mode', action='store_true', help='Optionally toggle dark mode (2022+ sets only)')
parser.add_argument('-sypls','--set_year_plus_one', action='store_true', help='Optionally add one to the set year on 04/05 set.')
parser.add_argument('-htl','--hide_team_logo', action='store_true', help='Optionally remove all team logos and branding.')
parser.add_argument('-sc','--secondary_color', action='store_true', help='Used secondary team color.')

# STATS
parser.add_argument('-sp','--stats_period', help='Period to use for stats. Allowed options are REGULAR,DATES,POST,SPLIT', default='REGULAR', type=str)
parser.add_argument('-start','--start_date', help='Optional Start Date for stats. Only available post-1900.', default=None, type=str)
parser.add_argument('-end','--end_date', help='Optional End Date for stats. Only available post-1900.', default=None, type=str)
parser.add_argument('-spl','--split_name', help='Create a card using the splits page on baseball reference', default=None, type=str)
parser.add_argument('-co','--co_override',help='Manually select a command/out combination',default=None, type=str)
parser.add_argument('-vs','--variable_spd', action='store_true', help='Optionally toggle variable speed (2000 + 2001 sets only)')
parser.add_argument('-o','--offset',help='Get alternate chart n away from most accurate',default=0)
parser.add_argument('-yrt','--show_year_text', action='store_true', help='Optionally add separate year text to the image. Applies to 2000-2005 only.')
parser.add_argument('-nick','--nickname_index', help='Optionally choose a nickname to show for images. Enter a number based on ordering from bref, max is 3', default=None, type=int)
parser.add_argument('-wotc','--is_wotc', action='store_true', help='Try loading from WOTC cards.')

# CACHE
parser.add_argument('-isl','--ignore_showdown_library', action='store_true', help='Optionally force ignore Showdown Library, will create card live.')
parser.add_argument('-ic','--ignore_cache', action='store_true', help='Ignore local cache')
parser.add_argument('-dc','--disable_cache_cleaning', action='store_true', help='Disable removal of cached files after minutes threshold.')


args = parser.parse_args()

def main():
    """ Executed when running as a script """

    name = args.name.title()
    year = args.year
    set = args.set
    command_out_override = None if args.co_override is None else tuple([int(x) for x in args.co_override.split('-')])

    stats_period = StatsPeriod(
        type=args.stats_period,
        start_date=args.start_date,
        end_date=args.end_date,
        split=args.split_name
    )
    scraper = BaseballReferenceScraper(name=name,year=year,stats_period=stats_period,ignore_cache=args.ignore_cache, disable_cleaning_cache=args.disable_cache_cleaning)
    
    # FETCH REAL STATS FROM EITHER:
    #  1. ARCHIVE: HISTORICAL DATA IN POSTGRES DB
    #  2. SCRAPER: LIVE REQUEST FOR BREF/SAVANT DATA
    postgres_db = PostgresDB(is_archive=True)
    archived_statline, archive_load_time = postgres_db.fetch_player_stats_from_archive(year=scraper.year_input, bref_id=scraper.baseball_ref_id, team_override=scraper.team_override, type_override=scraper.player_type_override, stats_period_type=stats_period.type)
    postgres_db.close_connection()
    if archived_statline:
        statline = archived_statline
        data_source = 'Archive'
    else:
        statline = scraper.player_statline()
        data_source = scraper.source

    # WOTC CARD
    showdown: ShowdownPlayerCard = None
    if args.is_wotc:

        # LOAD FROM JSON
        file_path = os.path.join(Path(os.path.dirname(__file__)),'wotc_cards.json')
        with open(file_path, "r") as json_file:
            wotc_data = json.load(json_file)
        
        # MATCH ON ID
        fields = [args.year, scraper.baseball_ref_id, args.set, args.expansion,]
        if scraper.player_type_override:
            fields.append(scraper.player_type_override)
        showdown_card_id = "-".join(fields)

        wotc_card:dict = wotc_data.get(showdown_card_id, None)
        if wotc_card:
            wotc_card['stats'] = statline
            showdown = ShowdownPlayerCard(**wotc_card)
            showdown.accolades = showdown.parse_accolades()
            showdown.print_player()
            if args.show_image:
                showdown.card_image(show=True)
            pts = showdown.calculate_points(projected=showdown.projected, positions_and_defense=showdown.positions_and_defense, speed_or_ip=showdown.ip if showdown.is_pitcher else showdown.speed.speed)
            print(f"Projected PTS: {pts.total_points}  Actual PTS: {showdown.points}  Diff: {showdown.points - pts.total_points}")

    # CREATE SHOWDOWN CARD FROM STATLINE
    stats_period = scraper.stats_period or stats_period
    if showdown is None:
        showdown = ShowdownPlayerCard(
            name=name,
            year=year,
            stats_period=stats_period,
            stats=statline,
            set=set,
            era=args.era,
            expansion=args.expansion,
            edition=args.edition,
            offset=args.offset,
            player_image_url=args.image_url,
            player_image_path=args.image_path,
            card_img_output_folder_path=args.image_output_path,
            print_to_cli=True,
            show_image=args.show_image,
            set_number=str(args.set_num),
            command_out_override=command_out_override,
            add_image_border=args.add_border,
            is_dark_mode=args.dark_mode,
            is_variable_speed_00_01=args.variable_spd,
            parallel=args.parallel,
            show_year_text=args.show_year_text,
            set_year_plus_one=args.set_year_plus_one,
            hide_team_logo=args.hide_team_logo,
            use_secondary_color=args.secondary_color,
            source=data_source,
            disable_cache_cleaning=args.disable_cache_cleaning,
            nickname_index=args.nickname_index,
            ignore_cache=args.ignore_cache,
            warnings=scraper.warnings
        )

    # PRINT TOTAL LOAD TIME
    total_load_time = (scraper.load_time if scraper.load_time else 0.00) + (showdown.load_time if showdown.load_time else 0.00) + (archive_load_time if archive_load_time else 0.0)
    print(f"LOAD TIME: {total_load_time}s")

if __name__ == "__main__":
    main()