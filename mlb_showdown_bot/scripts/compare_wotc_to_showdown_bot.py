import math
from pydantic import BaseModel
from enum import Enum
from rich import print
import sys, os
from pathlib import Path
from prettytable import PrettyTable
from statistics import mean, median
sys.path.append(os.path.join(Path(os.path.join(os.path.dirname(__file__))).parent))
from wotc_player_cards import WotcPlayerCardSet, WotcPlayerCard, Set, PlayerType, ShowdownPlayerCard

import argparse
parser = argparse.ArgumentParser(description="Convert Original WOTC MLB Showdown Card Data to Showdown Bot Cards.")
parser.add_argument('-s','--set', type=str, help='Set to test (ex: 2000, 2001, 2005)', default='2000')
parser.add_argument('-t','--type', type=str, help='Type to test (Pitcher, Hitter)', default='Hitter')
parser.add_argument('-e','--expansions', type=str, help='Expansions to test (ex: BS)', default='BS')
parser.add_argument('-p','--show_players', action='store_true', help='Show player level breakdown')
args = parser.parse_args()

# ------------------------------
# CLASSES FOR COMPARISON
# ------------------------------

class Stat(Enum):
    OBP = "onbase_perc"
    SLG = "slugging_perc"
    COMMAND = "command"
    SPEED = "speed"

    @property
    def difference_multiplier(self) -> float:
        match self :
            case Stat.OBP: return 5
            case Stat.SLG: return 5
            case _: return 1
    
    @property
    def overall_accuracy_weight(self) -> float:
        match self :
            case Stat.OBP: return 3
            case _: return 1

    @property
    def attribute_source(self) -> str:
        """Name of attribute on the Showdown Bot object to get stat"""
        match self :
            case Stat.OBP | Stat.SLG: return "projected"
            case Stat.COMMAND: return "chart"
            case Stat.SPEED: return "speed"

class StatDiffClassification(Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    MATCH = "MATCH"

    @property
    def color(self) -> str:
        match self :
            case StatDiffClassification.ABOVE: return "red"
            case StatDiffClassification.BELOW: return "yellow"
            case StatDiffClassification.MATCH: return "green"

class StatComparison(BaseModel):
    stat: Stat
    wotc: int | float
    showdown: int | float
    diff: int | float = 0
    accuracy: float = 0
    classification: StatDiffClassification = None

    def __init__(self, **data) -> None:
        super().__init__(**data)

        # CALC DIFF AND ASSIGN CLASSIFICATION
        self.diff = self.showdown - self.wotc

        self.accuracy = self.pct_accuracy(n1=self.wotc, n2=self.showdown)

        if self.diff > 0: self.classification = StatDiffClassification.ABOVE
        elif self.diff < 0: self.classification = StatDiffClassification.BELOW
        else: self.classification = StatDiffClassification.MATCH

    @property
    def abs_diff(self) -> int | float:
        return abs(self.diff)
    
    def pct_accuracy(self, n1: int | float, n2: int | float) -> float:
        """Calculate percent accuracy"""
        difference = abs(n1 - n2)
        denominator = (n1 + n2) / 2.0
        return 1.0 - ( self.stat.difference_multiplier * difference / denominator )
    
    @property
    def weighted_accuracy(self) -> float:
        return self.accuracy * self.stat.overall_accuracy_weight
    

class CardComparison(BaseModel):
    wotc: WotcPlayerCard
    showdown: ShowdownPlayerCard
    stat_comparisons: dict[Stat, StatComparison] = {}

    def __init__(self, **data) -> None:
        super().__init__(**data)

        stat_to_compare = [s for s in Stat]
        for stat in stat_to_compare:
            match stat.attribute_source:
                case "projected":
                    wotc_stat = self.wotc.projected.get(stat.value, 0)
                    showdown_stat = self.showdown.projected.get(stat.value, 0)
                case "chart":
                    wotc_stat = getattr(self.wotc.chart, stat.value)
                    showdown_stat = getattr(self.showdown.chart, stat.value)
                case "speed":
                    wotc_stat = getattr(self.wotc.speed, stat.value)
                    showdown_stat = getattr(self.showdown.speed, stat.value)
            
            self.stat_comparisons[stat] = StatComparison(
                stat=stat,
                wotc=wotc_stat,
                showdown=showdown_stat
            )

    @property
    def weighted_accuracy(self) -> float:
        """Take weighted avg of accuracy for projections"""
        sum_product = sum([sc.weighted_accuracy for sc in self.stat_comparisons.values()])
        sum_weights = sum([sc.stat.overall_accuracy_weight for sc in self.stat_comparisons.values()])
        return sum_product / sum_weights
    
    @property
    def accuracy_for_print(self) -> str:
        color = "green" if self.weighted_accuracy > 0.90 else "red"
        return f"[{color}]{self.weighted_accuracy:.2%}"

    def print_table(self) -> None:
        print(f"{wotc.name} {self.accuracy_for_print}  WOTC: {wotc.chart.command_outs_concat}  Showdown: {showdown_bot.chart.command_outs_concat}  G:{wotc.stats.get('G', 0)}")
        table = PrettyTable()
        table.field_names = ['Stat', 'WOTC', 'BOT', 'Diff', 'Accuracy', 'Classification']
        for stat, comparison in self.stat_comparisons.items():
            table.add_row([stat.name, comparison.wotc, comparison.showdown, round(comparison.diff, 3), f'{comparison.accuracy:.2%}', f'{comparison.classification.value}'])
        print(table)


# ------------------------------
# 1. LOAD WOTC CARDS
# ------------------------------
set_list: list[Set] = [Set(args.set)]
expansion_list: list[str] = args.expansions.split(',')
player_types_list: list[PlayerType] = [PlayerType(args.type)]
wotc_player_card_set = WotcPlayerCardSet(sets=set_list, expansions=expansion_list, player_types=player_types_list)

# ------------------------------
# 2. LOOP THROUGH CARDS
# ------------------------------

all_comparisons: list[CardComparison] = []
for index, (id, wotc) in enumerate(wotc_player_card_set.cards.items(), 1):
    
    if len(wotc.stats) == 0:
        continue

    # CREATE SHOWDOWN BOT CARD FROM STATS
    showdown_bot = ShowdownPlayerCard(
        name=wotc.name,
        year=wotc.year,
        set=wotc.set,
        expansion=wotc.image.expansion,
        player_type=wotc.player_type,
        stats=wotc.stats
    )



    # COMPARE
    comparison = CardComparison(wotc=wotc, showdown=showdown_bot)
    all_comparisons.append(comparison)

    # PRINT
    if args.show_players:
        comparison.print_table()

# ------------------------------
# 3. SUMMARIZE ACROSS CARDS
# ------------------------------

# CREATE TABLE
print("\n\n[blue]SUMMARY ACROSS ALL CARDS")
table = PrettyTable()
table.field_names = ['Stat', 'Avg Diff', 'Med Diff', 'Avg Accuracy', 'Above', 'Below', 'Match',]

# LOOP THROUGH STATS
all_stats: list[Stat] = [s for s in Stat]
for stat in all_stats:
    
    # GET ALL COMPARISONS FOR STAT
    stat_comps = [c.stat_comparisons[stat] for c in all_comparisons if stat in c.stat_comparisons]
    
    # AGGREGATE
    avg_diff = mean([sc.diff for sc in stat_comps])
    median_diff = median([sc.diff for sc in stat_comps])
    avg_accuracy = mean([sc.accuracy for sc in stat_comps])
    above = sum([1 for sc in stat_comps if sc.classification == StatDiffClassification.ABOVE])
    below = sum([1 for sc in stat_comps if sc.classification == StatDiffClassification.BELOW])
    match = sum([1 for sc in stat_comps if sc.classification == StatDiffClassification.MATCH])

    # ADD TO TABLE
    table.add_row([stat.name, round(avg_diff, 3), round(median_diff, 3), f'{avg_accuracy:.2%}', above, below, match])

# OVERALL ACCURACY
all_accuracy = [c.weighted_accuracy for c in all_comparisons]
overall_accuracy = mean(all_accuracy)
table.add_row(['Overall', '', '', f'{overall_accuracy:.2%}', '', '', ''])
print(table)