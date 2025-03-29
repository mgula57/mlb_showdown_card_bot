import argparse
from pprint import pprint
import os, json
from pathlib import Path
from prettytable import PrettyTable
from datetime import datetime

# MY PACKAGES
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from .baseball_ref_scraper import BaseballReferenceScraper
    from .showdown_player_card import ShowdownPlayerCard
    from .classes.stats_period import StatsPeriod, StatsPeriodType, StatsPeriodDateAggregation, convert_to_date
    from .postgres_db import PostgresDB, PlayerArchive
except ImportError:
    # USE LOCAL IMPORT 
    from baseball_ref_scraper import BaseballReferenceScraper
    from showdown_player_card import ShowdownPlayerCard
    from classes.stats_period import StatsPeriod, StatsPeriodType, StatsPeriodDateAggregation, convert_to_date
    from postgres_db import PostgresDB, PlayerArchive

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
parser.add_argument('-mc','--is_multi_colored', action='store_true', help='Use multiple colors for chart image (CLASSIC, EXPANDED only)')
parser.add_argument('-sh', '--stat_highlights_type', help='Type of stat highlights to use. (OLD_SCHOOL, MODERN, ALL)', default='NONE', type=str)
parser.add_argument('-gm','--glow_multiplier', help='Glow/Shadow multiplier for card image', default=1.0, type=float)

# STATS
parser.add_argument('-sp','--stats_period', help='Period to use for stats. Allowed options are REGULAR,DATES,POST,SPLIT', default='REGULAR', type=str)
parser.add_argument('-start','--start_date', help='Optional Start Date for stats. Only available post-1900.', default=None, type=str)
parser.add_argument('-end','--end_date', help='Optional End Date for stats. Only available post-1900.', default=None, type=str)
parser.add_argument('-spl','--split_name', help='Create a card using the splits page on baseball reference', default=None, type=str)
parser.add_argument('-co','--co_override',help='Manually select a command/out combination',default=None, type=str)
parser.add_argument('-vs','--variable_spd', action='store_true', help='Optionally toggle variable speed (2000 + 2001 sets only)')
parser.add_argument('-cv','--chart_version',help='Get alternate chart n away from most accurate',default=1)
parser.add_argument('-yrt','--show_year_text', action='store_true', help='Optionally add separate year text to the image. Applies to 2000-2005 only.')
parser.add_argument('-nick','--nickname_index', help='Optionally choose a nickname to show for images. Enter a number based on ordering from bref, max is 3', default=None, type=int)
parser.add_argument('-wotc','--is_wotc', action='store_true', help='Try loading from WOTC cards.')

# CACHE
parser.add_argument('-isl','--ignore_showdown_library', action='store_true', help='Optionally force ignore Showdown Library, will create card live.')
parser.add_argument('-ic','--ignore_cache', action='store_true', help='Ignore local cache')
parser.add_argument('-ia','--ignore_archive', action='store_true', help='Ignore postgres showdown bot archive')
parser.add_argument('-dc','--disable_cache_cleaning', action='store_true', help='Disable removal of cached files after minutes threshold.')

# ADDITIONAL OPTIONS
parser.add_argument('-his', '--show_historical_points', action='store_true', help='Optionally calculate all historical stats for player. Displays Year and Points in tabular form.')
parser.add_argument('-st', '--season_trend_date_aggregation', help='Optionally calculate season trends for player. Input should be a date aggregation to show (ex: "MONTH", "WEEK", "DAY")', default=None, type=str)

args = parser.parse_args()

def main():
    """ Executed when running as a script """

    name = args.name.title()
    year = args.year
    set = args.set
    command_out_override = None if args.co_override is None else tuple([int(x) for x in args.co_override.split('-')])

    stats_period = StatsPeriod(
        type=args.stats_period,
        year=year,
        start_date=args.start_date,
        end_date=args.end_date,
        split=args.split_name
    )
    scraper = BaseballReferenceScraper(name=name,year=year,stats_period=stats_period,ignore_cache=args.ignore_cache, disable_cleaning_cache=args.disable_cache_cleaning)
    
    # -----------------------------------
    # FETCH REAL STATS FROM EITHER:
    #  1. ARCHIVE: HISTORICAL DATA IN POSTGRES DB
    #  2. SCRAPER: LIVE REQUEST FOR BREF/SAVANT DATA
    # -----------------------------------
    player_archive: PlayerArchive = None
    full_career_player_archive_list: list[PlayerArchive] = None
    archive_load_time: float = None
    statline: dict[str: any] = None
    data_source = 'Scraper'
    if not args.ignore_archive:
        postgres_db = PostgresDB(is_archive=True)
        player_archive, archive_load_time = postgres_db.fetch_player_stats_from_archive(year=scraper.year_input, bref_id=scraper.baseball_ref_id, team_override=scraper.team_override, type_override=scraper.player_type_override, stats_period_type=stats_period.type)
        full_career_player_archive_list = postgres_db.fetch_all_player_year_stats_from_archive(bref_id=scraper.baseball_ref_id, type_override=scraper.player_type_override)
        postgres_db.close_connection()
    
    if player_archive:
        statline = player_archive.stats
        data_source = 'Archive'
    else:
        statline = scraper.player_statline()
        data_source = scraper.source

    # -----------------------------------
    # BUILD AS WOTC CARD IF FLAGGED
    # -----------------------------------
    showdown: ShowdownPlayerCard = None
    if args.is_wotc:

        # LOAD FROM JSON
        file_path = os.path.join(Path(os.path.dirname(__file__)), 'data', 'wotc_player_card_set.json')
        with open(file_path, "r") as json_file:
            wotc_set_data = json.load(json_file)

        # MATCH ON ID
        fields = [args.year, scraper.baseball_ref_id, args.set, args.expansion,]
        if scraper.player_type_override:
            fields.append(scraper.player_type_override)
        showdown_card_id = "-".join(fields)

        # GET CARD
        wotc_card_data: dict = wotc_set_data.get('cards', {}).get(showdown_card_id, None)
        if wotc_card_data:
            showdown = ShowdownPlayerCard(**wotc_card_data)
            showdown.print_player()
            if args.show_image:
                showdown.card_image(show=True)
            pts = showdown.calculate_points(projected=showdown.projected, positions_and_defense=showdown.positions_and_defense, speed_or_ip=showdown.ip if showdown.is_pitcher else showdown.speed.speed)
            print(f"\nProjected PTS: {pts.total_points}  Actual PTS: {showdown.points}  Diff: {showdown.points - pts.total_points}")
            print(f"{pts.breakdown_str}")

    # -----------------------------------
    # CREATE SHOWDOWN CARD
    # -----------------------------------
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
            chart_version=args.chart_version,
            player_image_url=args.image_url,
            player_image_path=args.image_path,
            player_type_override=scraper.player_type_override,
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
            is_multi_colored=args.is_multi_colored,
            stat_highlights_type=args.stat_highlights_type,
            glow_multiplier=args.glow_multiplier,
            source=data_source,
            disable_cache_cleaning=args.disable_cache_cleaning,
            nickname_index=args.nickname_index,
            ignore_cache=args.ignore_cache,
            warnings=scraper.warnings
        )

    # -----------------------------------
    # PRINT HISTORICAL POINTS
    # -----------------------------------
    historical_load_time = 0.0
    historical_load_start_time = datetime.now()
    if args.show_historical_points and full_career_player_archive_list:
        # PRINT EACH YEAR'S CARD
        points_per_year: dict[int, int] = {}
        for archive in full_career_player_archive_list:

            hist_showdown = ShowdownPlayerCard(
                name=name,
                year=archive.year,
                stats_period=StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=str(archive.year)),
                stats=archive.stats,
                set=set,
                era=args.era,
                expansion=args.expansion,
                edition=args.edition,
                player_type_override=scraper.player_type_override,
                print_to_cli=False,
                command_out_override=command_out_override,
                is_variable_speed_00_01=args.variable_spd,
                source=data_source,
                disable_cache_cleaning=args.disable_cache_cleaning,
                nickname_index=args.nickname_index,
                ignore_cache=args.ignore_cache,
                warnings=scraper.warnings
            )
            if hist_showdown.player_type != showdown.player_type:
                continue
            points_per_year[str(archive.year)] = hist_showdown.points

        # PRINT HISTORICAL POINTS
        print("\nHISTORICAL POINTS")
        avg_points = int(round(sum(points_per_year.values()) / len(points_per_year)))
        table = PrettyTable(field_names=['AVG'] + list(points_per_year.keys()))
        table.add_row([str(avg_points)] + [f"{pts}" for pts in points_per_year.values()])
        print(table)

        historical_load_time = round((datetime.now() - historical_load_start_time).total_seconds(),2)

    # -----------------------------------
    # SHOW SEASON TRENDS (IF AVAILABLE)
    # -----------------------------------
    season_trends_load_time = 0.0
    season_trends_load_start_time = datetime.now()
    game_logs = statline.get(StatsPeriodType.DATE_RANGE.stats_dict_key, [])
    is_single_year = False if showdown is None else len(showdown.year_list) == 1
    try: date_aggregation = StatsPeriodDateAggregation(args.season_trend_date_aggregation)
    except: date_aggregation = None
    if date_aggregation and len(game_logs) > 0 and is_single_year:
        year = showdown.year_list[0]
        player_first_date = convert_to_date(game_log_date_str=game_logs[0].get('date', game_logs[0].get('date_game', None)), year=year)
        player_last_date = convert_to_date(game_log_date_str=game_logs[-1].get('date', game_logs[-1].get('date_game', None)), year=year)
        points_per_date: dict[str, int] = {}
        date_ranges = date_aggregation.date_ranges(year=year, start_date=player_first_date, stop_date=player_last_date)
        for dr in date_ranges:
            start_date, end_date = dr
            trends_showdown = ShowdownPlayerCard(
                name=name,
                year=str(year),
                stats_period=StatsPeriod(type=StatsPeriodType.DATE_RANGE, year=str(year), start_date=start_date, end_date=end_date),
                stats=statline,
                set=set,
                era=args.era,
                expansion=args.expansion,
                edition=args.edition,
                player_type_override=scraper.player_type_override,
                print_to_cli=False,
                command_out_override=command_out_override,
                is_variable_speed_00_01=args.variable_spd,
                source=data_source,
                disable_cache_cleaning=args.disable_cache_cleaning,
                nickname_index=args.nickname_index,
                ignore_cache=args.ignore_cache,
                warnings=scraper.warnings
            )
            if trends_showdown.stats_period.stats is None:
                print(f"NO STATS FOR {start_date} - {end_date}")
                continue

            points_per_date[end_date.strftime("%m/%d/%Y")] = trends_showdown.points

        # PRINT HISTORICAL POINTS
        print("\nSEASON TRENDS POINTS")
        # CUTOFF POINTS_PER_DATE TO FIRST 5 AND LAST 5
        if len(points_per_date) > 10:
            points_per_date = dict(list(points_per_date.items())[:5] + [('...', '...')] + list(points_per_date.items())[-5:])
        table = PrettyTable(field_names=list(points_per_date.keys()))
        table.add_row([f"{pts}" for pts in points_per_date.values()])
        print(table)

        season_trends_load_time = round((datetime.now() - season_trends_load_start_time).total_seconds(),2)


    # PRINT TOTAL LOAD TIME
    total_load_time = (scraper.load_time if scraper.load_time else 0.00) \
                        + (showdown.load_time if showdown.load_time else 0.00) \
                        + (archive_load_time if archive_load_time else 0.0) \
                        + historical_load_time + season_trends_load_time
    print(f"LOAD TIME: {total_load_time:.2f}s")

if __name__ == "__main__":
    main()