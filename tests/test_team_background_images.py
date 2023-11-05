import argparse
import sys
import os
from pathlib import Path
from pprint import pprint
sys.path.insert(0, '/Users/matthewgula/Documents/Python/mlb_showdown_card_bot/') # COMMENT WHEN OUT OF DEVELOPMENT
from mlb_showdown_bot.classes.team import Team
from mlb_showdown_bot.classes.sets import Set
from mlb_showdown_bot.showdown_player_card import ShowdownPlayerCard

# PARSE ARGS
parser = argparse.ArgumentParser(description="Test auto-generation of team backgrounds")
parser.add_argument('-tm','--teams', help='Comma delimited list of teams to run. If blank, runs all teams.', default='', required=False, type=str)
parser.add_argument('-s','--sets', help='Comma delimited list of sets to run. If blank, runs all sets (2000, 2001).', default='2000,2001', required=False, type=str)
parser.add_argument('-keep','--keep_old_images', action='store_true', help='Keeps old images in the output folder')
parser.add_argument('-cn','--color_names', action='store_true', help='Run only color names analysis.')
args = parser.parse_args()

# REMOVE OLD OUTPUT
folder_path = os.path.join(Path(os.path.dirname(__file__)),'image_output')
if args.keep_old_images == False:
    for item in os.listdir(folder_path):
        if item != '.gitkeep':
            item_path = os.path.join(folder_path, item)
            os.remove(item_path)

# TEAM BACKGROUND IMAGES
sets: list[Set] = [Set(set) for set in args.sets.split(',')]
teams: list[Team] = [tm for tm in Team] if args.teams == '' else [Team(tm) for tm in args.teams.split(',')]
color_names_dict = {}
for team in teams:
    years_dict = { '0': '2023' }
    for index, year_range in team.logo_historical_year_range_dict.items():
        years_dict[index] = str(min(year_range))
    for set in sets:
        for index, year in years_dict.items():
            for color in ['Primary', 'Secondary']:
                is_secondary = color == 'Secondary'
                showdown_card = ShowdownPlayerCard(
                    name='TEST',
                    year=year,
                    stats={'team_ID': team.value,},
                    set=set,
                    run_stats=False,
                    use_secondary_color=is_secondary,
                    disable_running_card=True
                )

                if args.color_names:
                    color_name = showdown_card.team.color_name(year=year, is_secondary=is_secondary)
                    color_count = color_names_dict.get(color_name, 0)
                    color_count += 1
                    color_names_dict[color_name] = color_count
                else:
                    img = showdown_card.team_background_image()
                    output_path = os.path.join(folder_path, f'{team.value}-{set}-{index}-{color}.png')
                    img.save(output_path, quality=100)

if args.color_names:
    pprint(sorted(color_names_dict.items(), key=lambda x: x[1], reverse=True))
