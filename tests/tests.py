
import pandas as pd
import numpy as np
import itertools
from pprint import pprint
import operator
import os
from pathlib import Path
from .showdown_set_accuracy import ShowdownSetAccuracy
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard, Set, PlayerType, Era, Chart
from mlb_showdown_bot.core.database.postgres_db import PostgresDB
import json 

def analyze_baseline_weights(set: Set, type: PlayerType,is_testing_current_baseline=False,ignore_volatile_categories=False, is_pts_only=False, position_filters=[], use_wotc_command_outs=False, command_out_combos=[]):
    """Calculate accuracy of the output produced given a set of baseline weights compared to 
       original Wizards set.

    Args:
        set: The showdown set meta to use (2000-2005).
        type: Player Type (Pitcher or Hitter).
        is_testing_current_baseline: Boolean flag for either testing the current set of weights or testing various sets of weights.
        ignore_volatile_categories: If true, ignores the more volitile categories when testing (EX: SO, 1B+, FB, ...)
        is_pts_only: Test only for accuracy of PTS
        position_filters: List of positions to filter down to
        use_wotc_command_outs: Boolean field to insert WOTC command/outs
        command_out_combos: Filter to test only certain Command/Out combinations

    Returns:
        None
    """
    
    # GET REAL STATS
    db = PostgresDB(is_archive=True)

    if db.connection is None:
        raise Exception('No connection to Postgres DB')
    
    player_season_stats_list = db.fetch_all_stats_from_archive(year_list=[int(set.year)-1], exclude_records_with_stats=False)

    # GET WOTC PLAYER CARDS
    file_path = os.path.join(Path(os.path.dirname(__file__)).parent, 'mlb_showdown_bot', 'wotc_cards.json')
    with open(file_path, "r") as json_file:
        wotc_data = json.load(json_file)
    
    wotc_data = {
        k: ShowdownPlayerCard(**v) for k,v in wotc_data.items() if str(v['set']) == set.value and v['image']['expansion'] == 'BS' and v['stats']['type'] == type.value and (len(position_filters) == 0 or v.get('positions_and_defense', {}).keys()[0] in position_filters)
    }
    
    num_players_in_set = len(wotc_data)

    # TEST EITHER CURRENT BASELINE, OR TEST MULTIPLE BASELINE COMBINATIONS
    opponent_type = PlayerType.PITCHER if type == PlayerType.HITTER else PlayerType.HITTER
    baseline_opponent = set.baseline_chart(player_type=opponent_type, era=Era.STEROID)
    command = baseline_opponent.command
    outs = baseline_opponent.outs
    combinations = [(command,outs)]

    num_combos = len(combinations)

    current_index = 1
    pcts = {}
    perfect = {}
    perfect_players = {}
    command_match_players = {}
    categories = {}
    categories_for_matches = {}
    categories_above_below = {}
    categories_above_below_for_matches = {}
    command_out_accuracies = {}
    command_out_above_below_for_all = {}
    positional_accuracies = {}
    positional_accuracies_above_below_for_all = {}
    for combo in combinations:

        print('---{}/{}---'.format(current_index, num_combos), end='\r')
        set_accuracy = ShowdownSetAccuracy(set=set, 
                                           real_stats=player_season_stats_list,
                                           wotc_cards=wotc_data, 
                                           command_control_combo=combo, 
                                           is_only_command_outs_accuracy=False,
                                           ignore_volatile_categories=ignore_volatile_categories,
                                           is_pts_only=is_pts_only,
                                           use_wotc_command_outs=use_wotc_command_outs,
                                           command_out_combos=command_out_combos)
        pcts_added, num_perfect, category_data, category_data_for_matches, category_above_below, category_above_below_for_matches, perfect_list, match_list, command_out_accuracy, command_out_categories_above_below, position_accuracy, position_above_below = set_accuracy.calc_set_accuracy()
        key = '{}-{}'.format(round(combo[0],1),round(combo[1],1))
        pcts[key] = pcts_added / num_players_in_set
        perfect[key] = num_perfect / num_players_in_set
        categories[key] = category_data
        categories_for_matches[key] = category_data_for_matches
        categories_above_below[key] = category_above_below
        categories_above_below_for_matches[key] = category_above_below_for_matches
        perfect_players[key] = perfect_list
        command_match_players[key] = match_list
        command_out_accuracies[key] = command_out_accuracy
        command_out_above_below_for_all[key] = command_out_categories_above_below
        positional_accuracies[key] = position_accuracy
        positional_accuracies_above_below_for_all[key] = position_above_below
        current_index += 1

    sorted_accuracy = sorted(pcts.items(), key=operator.itemgetter(1), reverse=True)
    sorted_perfect = sorted(perfect.items(), key=operator.itemgetter(1),reverse=True)
    sorted_categories = sorted(categories.items(), key = lambda x: x[1]['command-outs'],reverse=True)
    print('-------------------- Accuracy --------------------')
    pprint(sorted_accuracy[:5])
    print('-------------------- Perfect --------------------')
    pprint(sorted_perfect[:5])
    # print(perfect_players)
    print('-------------------- Category Breakdown --------------------')
    pprint(sorted_categories[:7])
    print('-------------------- Category (MATCHES) Breakdown --------------------')
    pprint(categories_for_matches)
    pprint(categories_above_below_for_matches)
    # print(command_match_players)
    print('-------------------- Category Above/Below --------------------')
    pprint(categories_above_below)
    print('-------------------- Command/Out Accuracies --------------------')
    pprint(command_out_accuracies)
    pprint(command_out_above_below_for_all)
    print('-------------------- Positional Accuracies --------------------')
    pprint(positional_accuracies)
    pprint(positional_accuracies_above_below_for_all)
