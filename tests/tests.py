
import pandas as pd
import numpy as np
import itertools
from pprint import pprint
import operator
import os
from pathlib import Path
from .showdown_set_accuracy import ShowdownSetAccuracy
import mlb_showdown_bot.showdown_constants as sc

def analyze_baseline_weights(context,type,is_testing_current_baseline=False,ignore_volatile_categories=False, is_pts_only=False):
    """Calculate accuracy of the output produced given a set of baseline weights compared to 
       original Wizards set.

    Args:
        context: The showdown set meta to use (2000-2005).
        type: Player Type (Pitcher or Hitter).
        is_testing_current_baseline: Boolean flag for either testing the current set of weights or testing various sets of weights.
        ignore_volatile_categories: If true, ignores the more volitile categories when testing (EX: SO, 1B+, FB, ...)

    Returns:
        None
    """
    
    real_player_stats_cache_path = os.path.join(Path(os.path.dirname(__file__)),'cache','player_cache.csv')
    in_game_player_cards_path = os.path.join(Path(os.path.dirname(__file__)),'data','mlb_showdown_player_card_data.xlsx')
    wotc_player_cards = pd.read_excel(in_game_player_cards_path)
    try:
        real_player_stats_cache = pd.read_csv(real_player_stats_cache_path)
    except FileNotFoundError:
        real_player_stats_cache = pd.DataFrame(columns=['NameAndYear'])
    wotc_player_cards = wotc_player_cards[(wotc_player_cards.Year == context) & (wotc_player_cards.Set == 'BS') & (wotc_player_cards.Type == type)]
    num_players_in_set = len(wotc_player_cards)

    # TEST EITHER CURRENT BASELINE, OR TEST MULTIPLE BASELINE COMBINATIONS
    if is_testing_current_baseline:
        baseline_opponent_dict = sc.BASELINE_PITCHER if type.lower() == 'hitter' else sc.BASELINE_HITTER
        command = baseline_opponent_dict[str(context)]['command']
        outs = baseline_opponent_dict[str(context)]['outs']
        combinations = [(command,outs)]
    else:
        command_range_dict = sc.TEST_COMMAND_RANGE_PITCHER if type.lower() == 'hitter' else sc.TEST_COMMAND_RANGE_HITTER
        outs_range_dict = sc.TEST_OUT_RANGE_PITCHER if type.lower() == 'hitter' else sc.TEST_OUT_RANGE_HITTER
        commands = [i for i in np.arange(command_range_dict[str(context)]['min'], command_range_dict[str(context)]['max'], 0.1)]
        outs = [i for i in np.arange(outs_range_dict[str(context)]['min'], outs_range_dict[str(context)]['max'], 0.1)]
        combinations = [(x,y) for x in commands for y in outs]

    num_combos = len(combinations)

    current_index = 1
    pcts = {}
    perfect = {}
    categories = {}
    categories_above_below = {}
    for combo in combinations:

        print('---{}/{}---'.format(current_index, num_combos), end='\r')
        set_accuracy = ShowdownSetAccuracy(context=context, 
                                           real_player_stats_cache=real_player_stats_cache, 
                                           wotc_card_outputs=wotc_player_cards, 
                                           command_control_combo=combo, 
                                           is_only_command_outs_accuracy=False,
                                           ignore_volatile_categories=ignore_volatile_categories,
                                           is_pts_only=is_pts_only)
        pcts_added, num_perfect, category_data, category_above_below = set_accuracy.calc_set_accuracy()
        key = '{}-{}'.format(round(combo[0],1),round(combo[1],1))
        pcts[key] = pcts_added / num_players_in_set
        perfect[key] = num_perfect / num_players_in_set
        categories[key] = category_data
        categories_above_below[key] = category_above_below
        current_index += 1

    sorted_accuracy = sorted(pcts.items(), key=operator.itemgetter(1), reverse=True)
    sorted_perfect = sorted(perfect.items(), key=operator.itemgetter(1),reverse=True)
    print('-------------------- Accuracy --------------------')
    pprint(sorted_accuracy[:5])
    print('-------------------- Perfect --------------------')
    pprint(sorted_perfect[:5])
    print('-------------------- Category Breakdown --------------------')
    pprint(categories)
    print('-------------------- Category Above/Below --------------------')
    pprint(categories_above_below)