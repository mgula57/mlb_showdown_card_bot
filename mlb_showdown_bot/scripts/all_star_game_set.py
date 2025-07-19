import sys, os
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from time import sleep

sys.path.append('..')
from mlb_showdown_bot.core.card.stats.baseball_ref_scraper import BaseballReferenceScraper
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard, StatsPeriod, Set, StatHighlightsType, Edition, ShowdownImage

parser = argparse.ArgumentParser(description="Create an all star game set for cards.")
parser.add_argument('-y','--year', type=int, help='Year to use for cards.', required=True)
parser.add_argument('-s','--sets', type=str, help='Single value or list of sets to process for', required=True)
args = parser.parse_args()

# LOAD ROSTER FILE
path = os.getenv('ALL_STAR_ROSTER_PATH')
roster_pd = pd.read_csv(path, index_col=False)

# CREATE FOLDER FOR RUN
run_folder_path = os.path.join(Path(os.path.dirname(__file__)),'output', f'{args.year}', 'ASG', str(datetime.now()))
os.makedirs(run_folder_path, exist_ok=True)

# RUN THROUGH ROSTER PER SET
sets = [Set(x) for x in args.sets.split(',')]
for set in sets:
    
    # CREATE FOLDER FOR SET
    print(set.value)
    set_folder_path = os.path.join(run_folder_path, set.value)
    os.makedirs(set_folder_path, exist_ok=True)
    
    # CREATE A CARD FOR EACH PLAYER
    for index, row in roster_pd.iterrows():
        
        # CARD INFO
        
        player_name: str = row['Name']
        bref_id:str = row['Bref Id']
        year_str = str(args.year)
        card_number = index+1
        print(f"  {str(card_number).zfill(3)}/{len(roster_pd)}: {player_name[:12].ljust(20)}", end='\r')
        
        # GRAB DATA
        stats_period = StatsPeriod(
            type='DATES',
            year=year_str,
            start_date=f"{args.year}-03-01",
            end_date=f"{args.year}-07-16", # CHANGE THIS PER YEAR
        )
        bref_scraper = BaseballReferenceScraper(
            name=bref_id, 
            year=year_str, 
            stats_period=stats_period, 
            disable_cleaning_cache=True, 
            disable_stats_period_range_updates=True,
            cache_folder_path=os.path.join(Path(os.path.dirname(__file__)),'cache')
        )
        stats = bref_scraper.player_statline()

        # CREATE CARD
        showdown = ShowdownPlayerCard(
            name = player_name,
            year = year_str,
            stats_period = bref_scraper.stats_period or stats_period,
            stats=stats,
            set=set,
            print_to_cli=False,
            set_name = 'All Star Game',
            is_variable_speed_00_01=False,
            disable_cache_cleaning=True,
            image = ShowdownImage(
                edition=Edition.ALL_STAR_GAME,
                set_number=str(card_number).zfill(3), is_bordered=True, 
                stat_highlights_type=StatHighlightsType.ALL,
                output_folder_path=set_folder_path,
                output_file_name=f"{str(card_number).zfill(3)}_{player_name}.png",
            ),
        )

        if bref_scraper.source != 'Local Cache':
            sleep(2.5)
