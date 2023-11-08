import argparse
import sys
sys.path.insert(0, '/Users/matthewgula/Documents/Python/mlb_showdown_card_bot/') # COMMENT WHEN OUT OF DEVELOPMENT
from mlb_showdown_bot.classes.sets import Set, Era, PlayerType
from mlb_showdown_bot.classes.chart import ChartCategory

# PARSE ARGS
parser = argparse.ArgumentParser(description="Test set constants")
args = parser.parse_args()

# TEST COMMAND OUT COMBINATIONS PER ERA
for type in PlayerType:
    for set in Set:
        print(f'---- {set.value} {type} ----')
        for era in Era:
            excluded = era in [Era.STEROID]
            if not excluded:
            
                chart = set.baseline_chart(player_type=type, era=era)
                remaining_slots = round(chart.remaining_slots(excluded_categories=[ChartCategory.SO]) - chart.outs, 2)
                if remaining_slots != 0:
                    print(f"{remaining_slots} ({era.name}-{type.value})")