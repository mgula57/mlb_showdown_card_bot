
import pandas as pd
import numpy as np
import itertools
from pprint import pprint
import operator
import os
from pathlib import Path
from mlb_showdown.showdown_set_accuracy import ShowdownSetAccuracy

def analyze(context,type):

    real_player_stats_cache_path = os.path.join(Path(os.path.dirname(__file__)).parent,'cache','player_cache.csv')
    in_game_player_cards_path = os.path.join(Path(os.path.dirname(__file__)).parent,'data','mlb_showdown_player_card_data.xlsx')
    wotc_player_cards = pd.read_excel(in_game_player_cards_path,index=False)
    try:
        real_player_stats_cache = pd.read_csv(real_player_stats_cache_path)
    except FileNotFoundError:
        real_player_stats_cache = pd.DataFrame(columns=['NameAndYear'])
    wotc_player_cards = wotc_player_cards[(wotc_player_cards.Year == context) & (wotc_player_cards.Set == 'BS') & (wotc_player_cards.Type == type)]
    totalPlayersInSet = len(wotc_player_cards)
    commands = [i for i in np.arange(7.5,8.3,0.1)]
    outs = [i for i in np.arange(3.4,4.3,0.1)]
    pcts = {}
    perfect = {}
    categories = {}
    currentIndex = 1
    # combinations = itertools.product(commands, outs)
    combinations = [[3.4, 15.5], [3.5, 15.5], [3.2, 15.5], [3.4, 15.6]]
    numCombos = len(combinations)
    # for combo in itertools.product(commands, outs):
    for combo in combinations:

        print('---{}/{}---'.format(currentIndex, numCombos), end='\r')
        set_accuracy = ShowdownSetAccuracy(context, real_player_stats_cache, wotc_player_cards, combo, is_only_command_outs_accuracy=False)
        pctsAdded, numPerfect, categoryData = set_accuracy.calc_set_accuracy()
        key = '{}-{}'.format(round(combo[0],1),round(combo[1],1))
        pcts[key] = pctsAdded / totalPlayersInSet
        perfect[key] = numPerfect / totalPlayersInSet
        categories[key] = categoryData
        currentIndex += 1

    sortedAccuracy = sorted(pcts.items(), key=operator.itemgetter(1), reverse=True)
    sortedPerfect = sorted(perfect.items(), key=operator.itemgetter(1),reverse=True)
    print('Accuracy:')
    pprint(sortedAccuracy[:5])
    print('Perfect:')
    pprint(sortedPerfect[:5])
    print('Category Breakdown:')
    pprint(categories)
