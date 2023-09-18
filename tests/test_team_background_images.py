import argparse
import sys
import os
from pathlib import Path
sys.path.insert(0, '/Users/matthewgula/Documents/Python/mlb_showdown_card_bot/') # COMMENT WHEN OUT OF DEVELOPMENT
from mlb_showdown_bot.enums.team import Team
from mlb_showdown_bot.showdown_player_card import ShowdownPlayerCard

# PARSE ARGS
parser = argparse.ArgumentParser(description="Test auto-generation of team backgrounds")
parser.add_argument('-tm','--teams', help='Comma delimited list of teams to run. If blank, runs all teams.', default='', required=False, type=str)
parser.add_argument('-keep','--keep_old_images', action='store_true', help='Keeps old images in the output folder')
args = parser.parse_args()

# REMOVE OLD OUTPUT
folder_path = os.path.join(Path(os.path.dirname(__file__)),'image_output')
if args.keep_old_images == False:
    for item in os.listdir(folder_path):
        if item != '.gitkeep':
            item_path = os.path.join(folder_path, item)
            os.remove(item_path)

sets = ['2000','2001']
teams = [tm for tm in Team] if args.teams == '' else [Team(tm) for tm in args.teams.split(',')]
for team in teams[0:4]:
    for set in sets:
        showdown_card = ShowdownPlayerCard(
            name='TEST',
            year='2023',
            stats={'team_ID': team.value},
            context=set,
            run_stats=False
        )

        img = showdown_card.team_background_image()
        output_path = os.path.join(folder_path, f'{team.value}-{set}.png')
        img.save(output_path, quality=100)
