import argparse
from datetime import datetime
import os
from pprint import pprint
import sys
from pathlib import Path
from prettytable import PrettyTable
sys.path.append(os.path.join(Path(os.path.join(os.path.dirname(__file__))).parent))
from postgres_db import PostgresDB, PlayerArchive

parser = argparse.ArgumentParser(description="Search baseball reference for best auto images to add.")
parser.add_argument('-hof','--hof', action='store_true', help='Only Hall of Fame Players', required=False)
parser.add_argument('-v','--mvp', action='store_true', help='Only MVPs', required=False)
parser.add_argument('-cy','--cya', action='store_true', help='Only CYAs', required=False)
parser.add_argument('-gg','--gold_glove', action='store_true', help='Only Gold Glove Winners', required=False)
parser.add_argument('-ys','--year_start', help='Optional year start filter', type=int, required=False, default=None)
parser.add_argument('-ye','--year_end', help='Optional year end filter', type=int, required=False, default=None)
parser.add_argument('-l','--limit', help='Optional limit', type=int, required=False, default=None)
parser.add_argument('-tm', '--team', help='Optional team filter', required=False, default=None)
parser.add_argument('-yt', '--year_threshold', help='Optional year threshold. Only includes images that are <= the threshold.', required=False, type=int, default=None)
parser.add_argument('-sort', '--sort', help='Optional sort field', required=False, default='bWar')
args = parser.parse_args()

def fetch_image_file_list() -> list[str]:
    file_names = []
    path = os.environ.get('AUTO_IMAGE_PATH', None)
    if not path:
        return []
    
    for _, _, files in os.walk(path):
        for name in files:
            file_names.append(name)
    return file_names

def fetch_player_data() -> list[PlayerArchive]:

    # LIST OF YEAR INTS FROM 1900 TO NOW
    # GET CURRENT YEAR
    current_year = datetime.now().year
    year_list = list(range(1900, current_year + 1))
    
    # FILTER OUT YEARS BETWEEN YEAR START AND YEAR END ARGS
    if args.year_start is not None:
        year_list = [year for year in year_list if year >= args.year_start]
    if args.year_end is not None:
        year_list = [year for year in year_list if year <= args.year_end]

    db = PostgresDB(is_archive=True)

    if db.connection is None:
        print("ERROR: NO CONNECTION TO DB")
    
    war_field = f"(case when length((stats->>'{args.sort}')) = 0 then 0.0 else (stats->>'{args.sort}')::float end)"
    player_data = db.fetch_all_stats_from_archive(year_list=year_list, limit=args.limit, order_by=war_field, exclude_records_with_stats=False)

    return player_data


# GRAB DATA FROM BREF
image_list = fetch_image_file_list()
player_data = fetch_player_data()

if len(player_data) == 0:
    print("NO PLAYERS FOUND")

player_tbl = PrettyTable(field_names=['Player', 'Team', 'Year', 'Position', 'G', 'GS', 'bWAR', 'OPS', 'ERA', 'HOF', 'MVP', 'CYA'])

for player in player_data:
    
    bwar = player.stats.get('bWAR', 0)
    is_hof = player.stats.get('is_hof', False)
    awards = player.stats.get('award_summary', '').split(',')
    games = str(player.g)
    games_started = str(player.gs or '-')
    era = str(player.stats.get('earned_run_avg', '-'))
    ops = str(player.stats.get('onbase_plus_slugging', '-')).replace('0.','.')
    mvp_str = 'X' if 'MVP-1' in awards else ''
    cy_str = 'X' if 'CYA-1' in awards else ''
    hof_str = 'X' if is_hof else ''

    # SKIP IF PLAYER IS IN IMAGE LIST
    images = [image for image in image_list if player.bref_id in image and f'({player.team_id})' in image and (abs(int(image.split('-')[1]) - player.year) <= args.year_threshold if args.year_threshold is not None else True)]    
    if len(images) > 0:
        continue

    # TEAM CHECK
    if args.team and args.team != player.team_id: continue

    # HOF CHECK
    if args.hof and not is_hof: continue

    # MVP CHECK
    if args.mvp and 'MVP-1' not in awards: continue

    # CYA CHECK
    if args.cya and 'CYA-1' not in awards: continue

    # GG CHECK
    if args.gold_glove and 'GG' not in awards: continue

    # PRINT PLAYER'S NAME, TEAM, AND YEAR
    player_tbl.add_row([
        player.name,
        player.team_id,
        player.year,
        ",".join(player.primary_positions),
        games,
        games_started,
        bwar,
        ops,
        era,
        hof_str,
        mvp_str,
        cy_str
    ])

print(player_tbl)
