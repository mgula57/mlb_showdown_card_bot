import argparse
import os
import cloudscraper
from bs4 import BeautifulSoup
from pprint import pprint
import sys

sys.path.append('..')
from postgres_db import PostgresDB

parser = argparse.ArgumentParser(description="Search baseball reference for best auto images to add.")
parser.add_argument('-hof','--hof', action='store_true', help='Only Hall of Fame Players', required=False)
parser.add_argument('-ys','--year_start', help='Optional year start filter', type=int, required=False, default=None)
parser.add_argument('-ye','--year_end', help='Optional year end filter', type=int, required=False, default=None)
parser.add_argument('-l','--limit', help='Optional limit', type=int, required=False, default=None)
parser.add_argument('-yt', '--filter_year_threshold', help='Optional year threshold filter', required=False, action='store_true', default=False)
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

def fetch_player_data() -> list[dict]:

    # LIST OF YEAR INTS FROM 1900 TO NOW
    year_list = list(range(1900, 2024))
    
    # FILTER OUT YEARS BETWEEN YEAR START AND YEAR END ARGS
    if args.year_start is not None:
        year_list = [year for year in year_list if year >= args.year_start]
    if args.year_end is not None:
        year_list = [year for year in year_list if year <= args.year_end]

    db = PostgresDB(is_archive=True)

    if db.connection is None:
        print("ERROR: NO CONNECTION TO DB")
    
    war_field = "(case when length((stats->>'bWAR')) = 0 then 0.0 else (stats->>'bWAR')::float end)"
    player_data = db.fetch_all_stats_from_archive(year_list=year_list, limit=args.limit, order_by=war_field, exclude_records_with_stats=False)

    return player_data


# GRAB DATA FROM BREF
image_list = fetch_image_file_list()
player_data = fetch_player_data()

for player in player_data:

    name = player['name']
    bref_id = player['bref_id']
    year = player['year']
    team = player['team_id']
    bwar = player['stats']['bWAR']
    is_hof = player['stats'].get('is_hof', False)
    hof_str = 'HOF' if is_hof else ''

    # SKIP IF PLAYER IS IN IMAGE LIST
    images = [image for image in image_list if bref_id in image and f'({team})' in image and (abs(int(image.split('-')[1]) - year) <= 7 if args.filter_year_threshold else True)]
    if len(images) > 0:
        continue

    # HOF CHECK
    if args.hof and not is_hof:
        continue

    # PRINT PLAYER'S NAME, TEAM, AND YEAR
    print(f"{name} {team} {year} {bwar} {hof_str}")
