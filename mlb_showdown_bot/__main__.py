import argparse
import os

# MY PACKAGES
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from .firebase import Firebase
    from .baseball_ref_scraper import BaseballReferenceScraper
    from .showdown_player_card_generator import ShowdownPlayerCardGenerator
except ImportError:
    # USE LOCAL IMPORT 
    from firebase import Firebase
    from baseball_ref_scraper import BaseballReferenceScraper
    from showdown_player_card_generator import ShowdownPlayerCardGenerator

parser = argparse.ArgumentParser(description="Generate a player's MLB Showdown stats in a given year")
parser.add_argument('-n','--name', help='The first and last name of the player',required=True)
parser.add_argument('-y','--year', help='The year of the player',required=True)
parser.add_argument('-c','--context',help='The showdown set meta to use (2000-2005)',default='2000')
parser.add_argument('-o','--offset',help='Get alternate chart n away from most accurate',default=0)
parser.add_argument('-url','--image_url',help='URL link to Player background image',default=None)
parser.add_argument('-path','--image_path',help='Path to Player background image on local machine',default=None)
parser.add_argument('-o_path','--image_output_path',help='Path to folder for card image output',default='')
parser.add_argument('-num','--set_num',help='Assign card a set number',default='')
parser.add_argument('-show','--show_image', action='store_true', help='Optionally open the final Player Card Image upon completion')
parser.add_argument('-cc','--is_cc', action='store_true', help='Optionally make the card Cooperstown Collection')
parser.add_argument('-ss','--is_ss', action='store_true', help='Optionally make the card Super Season')
parser.add_argument('-asg','--is_asg', action='store_true', help='Optionally make the card All Star Game')
parser.add_argument('-rs','--is_rookie_season', action='store_true', help='Optionally make the card have a rookie season logo')
parser.add_argument('-co','--co_override',help='Manually select a command/out combination',default='', type=str)
parser.add_argument('-exp','--expansion',help='Add optional expansion logo (ex: TD, PR)',default='FINAL')
parser.add_argument('-bor','--add_border', action='store_true', help='Optionally add border to player image')
parser.add_argument('-dark','--dark_mode', action='store_true', help='Optionally toggle dark mode (2022+ sets only)')
parser.add_argument('-vs','--variable_spd', action='store_true', help='Optionally toggle variable speed (2000 + 2001 sets only)')
parser.add_argument('-foil','--is_foil', action='store_true', help='Optionally add overlay with animated foil effect. Saves images as GIF.')
parser.add_argument('-yc','--add_year_container', action='store_true', help='Optionally add year container box. Applies to 2000-2003 only.')
parser.add_argument('-sypls','--set_year_plus_one', action='store_true', help='Optionally add one to the set year on 04/05 set.')
parser.add_argument('-isl','--ignore_showdown_library', action='store_true', help='Optionally force ignore Showdown Library, will create card live.')

args = parser.parse_args()

def main():
    """ Executed when running as a script """

    name = args.name.title()
    year = args.year
    context = args.context
    command_out_override = None if args.co_override == '' else tuple([int(x) for x in args.co_override.split('-')])

    scraper = BaseballReferenceScraper(name=name,year=year)
    # CHECK FOR CACHED STATS
    db = Firebase()
    cached_player_card = db.load_showdown_card(
        ignore_showdown_library=args.ignore_showdown_library,
        bref_id = scraper.baseball_ref_id,
        year=year,
        context=context,
        expansion=args.expansion, 
        player_image_path=args.image_path,
        player_image_url=args.image_url,
        is_cooperstown=args.is_cc,
        is_super_season=args.is_ss,
        is_rookie_season=args.is_rookie_season,
        is_all_star_game=args.is_asg,
        is_holiday=False, 
        offset=args.offset,
        set_number=str(args.set_num),
        add_image_border=args.add_border,
        is_dark_mode=args.dark_mode,
        is_variable_speed_00_01=args.variable_spd,
        is_foil=args.is_foil,
        team_override=scraper.team_override,
        set_year_plus_one=args.set_year_plus_one,
        pitcher_override = scraper.pitcher_override,
        hitter_override = scraper.hitter_override,
        is_running_in_flask=False
    )
    db.close_session()
    if cached_player_card:
        cached_player_card.print_player()
        if args.show_image:
            cached_player_card.player_image(show=True)

    else:
        statline = scraper.player_statline()
        showdown = ShowdownPlayerCardGenerator(
            name=name,
            year=year,
            stats=statline,
            is_cooperstown=args.is_cc,
            is_super_season=args.is_ss,
            is_all_star_game=args.is_asg,
            is_rookie_season=args.is_rookie_season,
            context=context,
            expansion=args.expansion,
            offset=args.offset,
            player_image_url=args.image_url,
            player_image_path=args.image_path,
            card_img_output_folder_path=args.image_output_path,
            print_to_cli=True,
            show_player_card_image=args.show_image,
            set_number=str(args.set_num),
            command_out_override=command_out_override,
            add_image_border=args.add_border,
            is_dark_mode=args.dark_mode,
            is_variable_speed_00_01=args.variable_spd,
            is_foil=args.is_foil,
            add_year_container=args.add_year_container,
            set_year_plus_one=args.set_year_plus_one
        )

if __name__ == "__main__":
    main()