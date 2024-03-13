from pydantic import BaseModel
from enum import Enum
from rich import print as rprint
import sys, os
from pathlib import Path
from prettytable import PrettyTable
from statistics import mean, median
sys.path.append(os.path.join(Path(os.path.join(os.path.dirname(__file__))).parent))
from wotc_player_cards import WotcPlayerCardSet, WotcPlayerCard, Set, PlayerType, ShowdownPlayerCard

import argparse
parser = argparse.ArgumentParser(description="Convert Original WOTC MLB Showdown Card Data to Showdown Bot Cards.")
parser.add_argument('-s','--sets', type=str, help='Sets to test (ex: 2000, 2001, 2005)', default='2000,2001,2002,2003,2004,2005')
parser.add_argument('-t','--types', type=str, help='Types to test (Pitcher, Hitter)', default='Hitter,Pitcher')
parser.add_argument('-e','--expansions', type=str, help='Expansions to test (ex: BS)', default='BS')
parser.add_argument('-p','--show_players', action='store_true', help='Show player level breakdown')
parser.add_argument('-nm','--names', type=str, help='List of names to show', default='')
args = parser.parse_args()

# ------------------------------
# CLASSES FOR COMPARISON
# ------------------------------


class Stat(Enum):
    OBP = "onbase_perc"
    SLG = "slugging_perc"
    COMMAND = "command"
    SPEED = "speed"
    PU = "PU"
    SO = "SO"
    GB = "GB"
    FB = "FB"
    BB = "BB"
    _1B = "1B"
    _1B_PLUS = "1B+"
    _2B = "2B"
    _3B = "3B"
    HR = "HR"

    def is_valid_for_type(self, type: PlayerType) -> bool:
        match self:
            case Stat.PU: return type == PlayerType.PITCHER
            case Stat.SPEED | Stat._3B | Stat._1B_PLUS: return type == PlayerType.HITTER
            case _: return True

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
            case Stat.SO | Stat.PU | Stat.GB | Stat.FB: return 0.33
            case _: return 1

    @property
    def attribute_source(self) -> str:
        """Name of attribute on the Showdown Bot object to get stat"""
        match self :
            case Stat.OBP | Stat.SLG: return "projected"
            case Stat.COMMAND: return "chart"
            case Stat.SPEED: return "speed"
            case _: return "chart.values"

    @property
    def label(self) -> str:
        match self:
            case Stat.OBP | Stat.SLG | Stat.COMMAND | Stat.SPEED: return self.name
            case _: return self.value


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


class ConsoleColor(Enum):
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    END = '\033[0m'


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

        # MATCH
        if n1 == n2:
            return 1.0

        difference = abs(n1 - n2)
        denominator = (n1 + n2) / 2.0

        # AVOID DIVIDE BY 0
        if denominator == 0:
            return 0
        
        # SPECIAL CASES
        if denominator in [0.5, 1.5] and self.stat not in [Stat.OBP, Stat.SLG]:
            denominator = 1.0
            difference -= 0.5
        
        pct_diff = ( self.stat.difference_multiplier * difference / denominator )
        return 1.0 - pct_diff
    
    @property
    def weighted_accuracy(self) -> float:
        return self.accuracy * self.stat.overall_accuracy_weight
    

class CardComparison(BaseModel):
    wotc: WotcPlayerCard
    showdown: ShowdownPlayerCard
    showdown_matching_command_outs: ShowdownPlayerCard
    stat_comparisons: dict[Stat, StatComparison] = {}

    def __init__(self, **data) -> None:
        super().__init__(**data)

        stat_to_compare = [s for s in Stat if s.is_valid_for_type(self.wotc.player_type)]
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
                case "chart.values":
                    wotc_stat = self.wotc.chart.values.get(stat.value, 0)
                    showdown_stat = self.showdown_matching_command_outs.chart.values.get(stat.value, 0)
            
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
        rprint(f"{wotc.name} {self.accuracy_for_print}  WOTC: {wotc.chart.command_outs_concat}  Showdown: {showdown_bot.chart.command_outs_concat}  G:{wotc.stats.get('G', 0)}")
        table = PrettyTable()
        table.field_names = ['Stat', 'WOTC', 'BOT', 'Diff', 'Accuracy', 'Classification']
        for stat, comparison in self.stat_comparisons.items():
            table.add_row([stat.name, comparison.wotc, comparison.showdown, round(comparison.diff, 3), f'{comparison.accuracy:.2%}', f'{comparison.classification.value}'])
        print(table)



# ------------------------------
# 1. LOAD WOTC CARDS
# ------------------------------
set_list: list[Set] = [Set(s) for s in args.sets.split(',')]
expansion_list: list[str] = args.expansions.split(',')
player_types_list: list[PlayerType] = [PlayerType(t) for t in args.types.split(',')]
wotc_player_card_set = WotcPlayerCardSet(sets=set_list, expansions=expansion_list, player_types=player_types_list)

# ------------------------------
# 2. LOOP THROUGH SETS, TYPES, CARDS
# ------------------------------
all_set_comparisons_dict: dict[Set, dict[PlayerType, list[CardComparison]]] = {}

for set in set_list:
    
    for type in player_types_list:
        stats_for_type = [s for s in Stat if s.is_valid_for_type(type)]
        set_comparisons: list[CardComparison] = []
        set_type_player_set = {id: card for id, card in wotc_player_card_set.cards.items() if card.set == set and card.player_type == type}
        for index, (id, wotc) in enumerate(set_type_player_set.items(), 1):
            
            # SKIP IF NO STATS
            if len(wotc.stats) == 0:
                continue

            # SKIP IF PA < 200
            if (wotc.stats.get('PA', 0) < 300 or wotc.stats.get('G', 0) < 100 ) and wotc.player_type == PlayerType.HITTER:
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

            showdown_bot_matching_command_outs = ShowdownPlayerCard(
                name=wotc.name,
                year=wotc.year,
                set=wotc.set,
                expansion=wotc.image.expansion,
                player_type=wotc.player_type,
                stats=wotc.stats,
                command_out_override=(wotc.chart.command, wotc.chart.outs),
            )

            # COMPARE
            comparison = CardComparison(wotc=wotc, showdown=showdown_bot, showdown_matching_command_outs=showdown_bot_matching_command_outs)
            set_comparisons.append(comparison)

            # PRINT
            show_player = ( args.names == '' or wotc.name in args.names ) and args.show_players
            if show_player:
                comparison.print_table()

        # ------------------------------
        # 3. SUMMARIZE SET ACCURACY
        # ------------------------------

        # CREATE TABLE
        print(f"\n\n{set} SUMMARY ({type.value})\n")
        table = PrettyTable()
        table.field_names = ['Stat', 'Avg Diff', 'Med Diff', 'Avg Accuracy', 'Above', 'Below', 'Match', 'Largest Diff']

        # LOOP THROUGH STATS
        for stat in stats_for_type:
            
            # GET ALL COMPARISONS FOR STAT
            stat_comps = [c.stat_comparisons[stat] for c in set_comparisons if stat in c.stat_comparisons]
            
            # AGGREGATE
            avg_diff = mean([sc.diff for sc in stat_comps])
            median_diff = median([sc.diff for sc in stat_comps])
            avg_accuracy = mean([sc.accuracy for sc in stat_comps])
            above = sum([1 for sc in stat_comps if sc.classification == StatDiffClassification.ABOVE])
            below = sum([1 for sc in stat_comps if sc.classification == StatDiffClassification.BELOW])
            match = sum([1 for sc in stat_comps if sc.classification == StatDiffClassification.MATCH])
            largest_diff = round(max([sc.abs_diff for sc in stat_comps]),3) or 0
            largest_diff_name = f"{next((c.wotc.name for c in set_comparisons if c.stat_comparisons[stat].abs_diff == largest_diff), '')} ({largest_diff})"

            # ACCURACY COLOR
            if avg_accuracy > 0.90: accuracy_color = ConsoleColor.GREEN
            elif avg_accuracy > 0.70: accuracy_color = ConsoleColor.YELLOW
            else: accuracy_color = ConsoleColor.RED

            # AVG DIFF COLOR
            if avg_accuracy > 0.95: diff_color = ConsoleColor.GREEN
            elif avg_diff > 0: diff_color = ConsoleColor.YELLOW
            else: diff_color = ConsoleColor.RED

            # ADD TO TABLE
            table.add_row([stat.label, f'{diff_color.value}{round(avg_diff, 3):.3f}{ConsoleColor.END.value}', round(median_diff, 3), f'{accuracy_color.value}{avg_accuracy:.2%}{ConsoleColor.END.value}', above, below, match, largest_diff_name])

        # OVERALL ACCURACY
        all_accuracy = [c.weighted_accuracy for c in set_comparisons]
        matches = len([c for c in set_comparisons if c.weighted_accuracy == 1.0])
        least_accurate = list(sorted(set_comparisons, key=lambda x: x.weighted_accuracy))[0:3]
        largest_diff_names = ', '.join([f'{c.wotc.name} ({c.weighted_accuracy:.2%})' for c in least_accurate])
        overall_accuracy = mean(all_accuracy)
        table.add_row(['Overall', '', '', f'{overall_accuracy:.2%}', '', '', matches, largest_diff_names])
        print(table)

        # ------------------------------
        # 4. ADD TO CROSS SET STATS
        # ------------------------------
        updated_set_comparisons = all_set_comparisons_dict.get(set, {})
        updated_set_comparisons[type] = set_comparisons
        all_set_comparisons_dict[set] = updated_set_comparisons

# ------------------------------
# 5. SUMMARIZE ACROSS ALL SETS
# ------------------------------
if len(set_list) > 1:
    table = PrettyTable()
    table.field_names = ['Set', 'Type', 'Accuracy',]
    for set, player_type_comparisons in all_set_comparisons_dict.items():

        for player_type, comparisons in player_type_comparisons.items():

            all_accuracy = [c.weighted_accuracy for c in comparisons]
            overall_set_accuracy = mean(all_accuracy)

            # ACCURACY COLOR
            if overall_set_accuracy > 0.90: accuracy_color = ConsoleColor.GREEN
            elif overall_set_accuracy > 0.75: accuracy_color = ConsoleColor.YELLOW
            else: accuracy_color = ConsoleColor.RED

            table.add_row([set.value, player_type.value, f'{accuracy_color.value}{overall_set_accuracy:.2%}{ConsoleColor.END.value}'])
    print(table)