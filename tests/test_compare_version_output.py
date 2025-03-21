
# CURRENT
from mlb_showdown_bot_pip.showdown_player_card import ShowdownPlayerCard as ShowdownPlayerCardCurrent
from mlb_showdown_bot_pip.version import __version__ as current_version

# NEW
from pathlib import Path
import os, sys
sys.path.append(os.path.join(Path(os.path.join(os.path.dirname(__file__))).parent))
from mlb_showdown_bot.showdown_player_card import Set, ShowdownPlayerCard as ShowdownPlayerCardNew
from mlb_showdown_bot.postgres_db import PostgresDB, PlayerArchive
from mlb_showdown_bot.version import __version__ as old_version

if old_version == current_version:
    raise Exception(f"Versions are the same | {old_version} | {current_version}")

import argparse
from pprint import pprint

# PARSE ARGS
parser = argparse.ArgumentParser(description="Check changes between old and new versions of Showdown Bot.")
parser.add_argument('-y','--years', help='Which year(s) to test for', type=str, required=True)
parser.add_argument('-s', '--sets', help='List of sets to include', type=str, default='2000,2001,2002,2003,2004,2005,CLASSIC,EXPANDED')
parser.add_argument('-sd','--show_detail', action='store_true', help='Show player detail into failures')
args = parser.parse_args()

from time import sleep

if __name__ == "__main__":

    years_as_list = [int(yr) for yr in args.years.split(',')]
    sets_as_list = [Set(set) for set in args.sets.replace(' ','').split(',')]
    postgres_db = PostgresDB(is_archive=True)
    player_list = postgres_db.fetch_all_stats_from_archive(year_list=years_as_list, exclude_records_with_stats=False)
    player_stats_list: list[PlayerArchive] = [p for p in player_list if p.stats is not None]
    postgres_db.close_connection()

    for set in sets_as_list:

        all_failures = {}
        num_players = len(player_stats_list)
        for player_archive in player_stats_list:

            # PLAYER
            name = player_archive.name
            year = str(player_archive.year)
            stats = player_archive.stats.copy()

            # --- NEW ---
            try:
                showdown_new = ShowdownPlayerCardNew(
                    name=name,
                    year=year,
                    stats=stats,
                    set=set,
                    print_to_cli=False,
                )
            except Exception as e:
                print(name, '(new)', e)
        
            # --- OLD ---
            try:
                showdown_current = ShowdownPlayerCardCurrent(
                    name=name,
                    year=year,
                    stats=stats,
                    set=set,
                    print_to_cli=False
                )
            except Exception as e:
                print(name, '(old)', e)
                continue
        
            # CHECK FOR MATCH

            # PROJECTED
            player_match_failures = {}

            # COMMAND/OUTS
            new_command_outs = f"{showdown_new.chart.command}-{showdown_new.chart.outs}"
            old_command_outs = f"{showdown_current.chart.command}-{showdown_current.chart.outs}"
            if new_command_outs != old_command_outs:
                player_match_failures['command-outs'] = {'new': new_command_outs, 'old': old_command_outs}

            # POINTS
            new_points = showdown_new.points
            old_points = showdown_current.points
            if new_points != old_points:
                player_match_failures['points'] = {'new': new_points, 'old': old_points}

            # POSITIONS AND DEFENSE
            new_defense_and_positions = showdown_new.positions_and_defense_as_string(is_horizontal=True)
            old_defense_and_positions = showdown_current.positions_and_defense_as_string(is_horizontal=True)
            if new_defense_and_positions != old_defense_and_positions:
                player_match_failures['defense'] = {'new': new_defense_and_positions, 'old': old_defense_and_positions}

            if len(player_match_failures) > 0:
                all_failures[name] = player_match_failures
        
        # PRINT RESULTS
        print(f"----- {set} ------")

        num_failures = len(all_failures)
        num_success = num_players - num_failures
        pct_success = round(num_success / num_players * 100, 1)
        print(f"{num_success}/{num_players} ({pct_success}%)")

        if args.show_detail:
            for name, failures in all_failures.items():
                print(f"{name} FAILED")
                pprint(failures)
        

