import argparse
import os
import dotenv
import pandas as pd
from pprint import pprint
from pathlib import Path
from datetime import datetime
from pandas import json_normalize
from unidecode import unidecode
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.append('..')
from mlb_showdown_bot.core.database.postgres_db import PostgresDB, PlayerArchive
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard, StatsPeriod, StatsPeriodType, ShowdownImage, StatHighlightsType
from mlb_showdown_bot.core.shared.player_position import PlayerType

parser = argparse.ArgumentParser(description="Export Showdown Bot Data to a CSV file.")
parser.add_argument('-hof','--hof', action='store_true', help='Only Hall of Fame Players', required=False)
parser.add_argument('-ys','--year_start', help='Optional year start filter', type=int, required=False, default=None)
parser.add_argument('-ye','--year_end', help='Optional year end filter', type=int, required=False, default=None)
parser.add_argument('-l','--limit', help='Optional limit', type=int, required=False, default=None)
parser.add_argument('-s','--sets', help='Showdown Set(s) to use', required=False, default='CLASSIC,EXPANDED,2000,2001,2002,2003,2004,2005')
args = parser.parse_args()

def year_list() -> list[int]:
    current_year = datetime.now().year
    year_list = list(range(1884, current_year + 1))

    # FILTER OUT YEARS BETWEEN YEAR START AND YEAR END ARGS
    if args.year_start is not None:
        year_list = [year for year in year_list if year >= args.year_start]
    if args.year_end is not None:
        year_list = [year for year in year_list if year <= args.year_end]
    
    return year_list

def fetch_player_data(year_list: list[int]) -> list[PlayerArchive]:
    print("FETCHING DATA...")

    db = PostgresDB(is_archive=True)

    if db.connection is None:
        print("ERROR: NO CONNECTION TO DB")
    
    player_data = db.fetch_all_stats_from_archive(year_list=year_list, limit=args.limit, order_by='year', exclude_records_with_stats=False)

    return player_data

def convert_to_showdown_cards(player_data: list[PlayerArchive], sets: list[str]) -> list[ShowdownPlayerCard]:
    print("CONVERTING TO SHOWDOWN CARDS...")
    showdown_cards = []
    for set in sets:
        print(f'\nSET: {set}')
        total_players = len(player_data)
        for index, player in enumerate(player_data, 1):
            type_override_raw = player.player_type_override
            type_override = PlayerType.PITCHER if type_override_raw else None
            name = player.name
            year = str(player.year)
            stats = player.stats
            set = set

            stats_period = StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=year)
            image = ShowdownImage(stat_highlights_type=StatHighlightsType.ALL)

            if player.bref_id in ['howelha01', 'dunnja01','sudhowi01','mercewi01'] and type_override_raw == '(pitcher)':
                continue
            
            # SKIP PLAYERS WITH 0 PA
            if stats.get('PA', 0) == 0:
                continue

            print(f"  {index}/{total_players}: {name: <30}", end="\r")
            try:
                showdown = ShowdownPlayerCard(
                    name=name, year=year, stats=stats, stats_period=stats_period,
                    set=set, player_type_override=type_override, print_to_cli=False,
                    image=image
                )
            except Exception as e:
                print(f"\nERROR CREATING SHOWDOWN CARD FOR {name} ({year}) - {e}")
                continue
            
            showdown_cards.append(showdown)
            
    return showdown_cards

def upload_to_database(showdown_cards: list[ShowdownPlayerCard]):
    print("UPLOADING TO DATABASE...")

    db = PostgresDB(is_archive=True)

    if db.connection is None:
        print("ERROR: NO CONNECTION TO DB")
        return

    db.upload_to_card_data(showdown_cards=showdown_cards, batch_size=1000)


# FETCH DATA
years = year_list()
player_data = fetch_player_data(year_list=years)

# CONVERT TO SHOWDOWN CARDS
sets_list = args.sets.split(',')
showdown_cards = convert_to_showdown_cards(player_data, sets_list)

upload_to_database(showdown_cards)
