
import pandas as pd
import numpy as np
import itertools
from pprint import pprint
import operator
import os
from pathlib import Path
from mlb_showdown.showdown_set_accuracy import ShowdownSetAccuracy
import mlb_showdown.showdown_constants as sc

def analyze(context,type,is_testing_current_baseline=False):

    real_player_stats_cache_path = os.path.join(Path(os.path.dirname(__file__)).parent,'cache','player_cache.csv')
    in_game_player_cards_path = os.path.join(Path(os.path.dirname(__file__)).parent,'data','mlb_showdown_player_card_data.xlsx')
    wotc_player_cards = pd.read_excel(in_game_player_cards_path,index=False)
    try:
        real_player_stats_cache = pd.read_csv(real_player_stats_cache_path)
    except FileNotFoundError:
        real_player_stats_cache = pd.DataFrame(columns=['NameAndYear'])
    wotc_player_cards = wotc_player_cards[(wotc_player_cards.Year == context) & (wotc_player_cards.Set == 'BS') & (wotc_player_cards.Type == type)]
    totalPlayersInSet = len(wotc_player_cards)

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
    for combo in combinations:

        print('---{}/{}---'.format(current_index, num_combos), end='\r')
        set_accuracy = ShowdownSetAccuracy(context, real_player_stats_cache, wotc_player_cards, combo, is_only_command_outs_accuracy=False)
        pctsAdded, numPerfect, categoryData = set_accuracy.calc_set_accuracy()
        key = '{}-{}'.format(round(combo[0],1),round(combo[1],1))
        pcts[key] = pctsAdded / totalPlayersInSet
        perfect[key] = numPerfect / totalPlayersInSet
        categories[key] = categoryData
        current_index += 1

    sortedAccuracy = sorted(pcts.items(), key=operator.itemgetter(1), reverse=True)
    sortedPerfect = sorted(perfect.items(), key=operator.itemgetter(1),reverse=True)
    print('Accuracy:')
    pprint(sortedAccuracy[:5])
    print('Perfect:')
    pprint(sortedPerfect[:5])
    print('Category Breakdown:')
    pprint(categories)
