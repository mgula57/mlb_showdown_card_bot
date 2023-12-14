import argparse
import pandas as pd
import sys
import json
from math import isnan
from pprint import pprint
import os
from pathlib import Path

sys.path.append('..')
from showdown_player_card import ShowdownPlayerCard
from classes.sets import Set, Era
from classes.chart import Chart, ChartCategory
from classes.metadata import Speed
from classes.player_position import PlayerType

parser = argparse.ArgumentParser(description="Convert Original WOTC MLB Showdown Card Data to Showdown Bot Cards.")
parser.add_argument('-path','--export_path', help='Path for exporting data', type=str, required=False)
args = parser.parse_args()

# ---------------------------------
# 1. LOAD CSV WITH ORIGINAL CARD DATA
# ---------------------------------

sheet_link = 'https://docs.google.com/spreadsheets/d/1WCrgXHIH0-amVd5pDPbhoMVnlhLuo1hU620lYCnh0VQ/edit#gid=0'
export_url = sheet_link.replace('/edit#gid=', '/export?format=csv&gid=')
df_wotc_cards = pd.read_csv(export_url)

# ---------------------------------
# 2. CONVERT TO LIST OF DICTS
# ---------------------------------

list_of_dicts: list[dict[str, any]] = df_wotc_cards.to_dict(orient='records')

# ---------------------------------
# 3. CREATE LIST OF SHOWDOWN OBJECTS
# ---------------------------------

dupes = []
showdown_card_data: dict[str, ShowdownPlayerCard] = {}
total_cards = len(list_of_dicts)
for index, wotc_data in enumerate(list_of_dicts, 1):

    if int(wotc_data.get('Set')) < 2002 and wotc_data.get('Expansion') == 'PM':
        continue

    print(f"  {index:<4}/{total_cards}  {wotc_data['Name']:<30}", end="\r")

    # CONVERT KEYS TO SNAKECASE, REMOVE NULLS
    bot_data: dict = {k.lower().replace(' ', '_'): v for k,v in wotc_data.items() if type(v) is str or not isnan(v)}

    # DERIVE REQUIRED FIELDS
    set = Set(str(bot_data['set']))
    set_year = int(set.year)
    bot_data['set'] = set
    bot_data['era'] = Era.STEROID.value
    bot_data['set_number'] = str(bot_data['set_number'])
    if bot_data['expansion'] == 'BS':
        bot_data['year'] = str(set_year - 1)
    else:
        ss_year = bot_data.get('ss_year', None)
        bot_data['year'] = str(int(ss_year) if ss_year else set_year)
    bot_data['stats'] = {}
    bot_data['source'] = 'WOTC'
    bot_data['disable_running_card'] = True
    bot_data['is_wotc'] = True
    bot_data['set_year_plus_one'] = True

    # TYPE
    player_type = PlayerType(bot_data['player_type'])
    bot_data['player_type'] = player_type

    # SPEED
    speed = bot_data['speed']
    if speed < set.speed_c_cutoff:
        letter = 'C'
    elif speed < 18:
        letter = 'B'
    else:
        letter = 'A'
    bot_data['speed'] = Speed(speed=speed, letter=letter)

    # POSITIONS
    positions_and_defense: dict[str, int] = {}
    for i in range(1, 4):
        position = bot_data.get(f'position{i}', None)
        if position:
            defense = bot_data.get(f'fielding{i}', 0)
            positions_and_defense[position] = defense
    bot_data['positions_and_defense'] = positions_and_defense

    # ICONS
    icons: list[str] = []
    for i in range(1, 5):
        icon = bot_data.get(f'icon{i}', None)
        if icon:
            icons.append(icon)
    bot_data['icons'] = icons

    # CHART
    possible_above_20_values = [bot_data.get(f, 0) for f in ['2b','3b','hr']]
    dbl_range_start, trpl_range_start, hr_range_start = ( (v if v > 20 else None) for v in possible_above_20_values)
    chart_values = {ChartCategory(k.upper()): (v if v < 20 else 0) for k,v in bot_data.items() if k in ['pu','so','gb','fb','bb','1b','1b+','2b','3b','hr']}
    chart = Chart(
        is_pitcher = player_type.is_pitcher,
        set = set.value,
        is_expanded = set.has_expanded_chart,
        command = bot_data['command'],
        outs = bot_data['outs'],
        values = chart_values,
        dbl_range_start = dbl_range_start, 
        trpl_range_start = trpl_range_start, 
        hr_range_start = hr_range_start
    )
    bot_data['chart'] = chart
    bot_data['stats'] = {'type': player_type.value}
    
    showdown_card = ShowdownPlayerCard(**bot_data)

    # ADD PROJECTIONS
    proj_opponent_chart, proj_my_advantages_per_20, proj_opponent_advantages_per_20 = showdown_card.opponent_stats_for_calcs(command=showdown_card.chart.command)
    chart_results_per_400_pa = showdown_card.chart_to_results_per_400_pa(chart=showdown_card.chart, my_advantages_per_20=proj_my_advantages_per_20, opponent_chart=proj_opponent_chart, opponent_advantages_per_20=proj_opponent_advantages_per_20)
    showdown_card.projected = showdown_card.projected_statline(stats_per_400_pa=chart_results_per_400_pa, command=showdown_card.chart.command)
    
    # ADD ESTIMATED PTS
    est_pts = showdown_card.calculate_points(projected=showdown_card.projected, positions_and_defense=showdown_card.positions_and_defense, speed_or_ip=showdown_card.ip if showdown_card.is_pitcher else showdown_card.speed.speed)

    if showdown_card.id in showdown_card_data.keys():
        dupes.append(showdown_card.id)

    showdown_json = showdown_card.as_json()
    showdown_json['est_points'] = est_pts.total_points
    
    showdown_card_data[showdown_card.id] = showdown_json

# ---------------------------------
# 4. CONVERT TO JSON
# ---------------------------------

file_path = os.path.join(Path(os.path.dirname(__file__)).parent,'wotc_cards.json')
with open(file_path, "w") as json_file:
    json.dump(showdown_card_data, json_file, indent=4, ensure_ascii=False)