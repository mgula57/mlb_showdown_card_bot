from pydantic import BaseModel
from enum import Enum
from rich import print as rprint
import sys, os
import statistics
from pathlib import Path
from prettytable import PrettyTable
from pprint import pprint
from statistics import mean
import pandas as pd
sys.path.append(os.path.join(Path(os.path.join(os.path.dirname(__file__))).parent))
from wotc_player_cards import WotcPlayerCardSet, WotcPlayerCard, WotcDataSource, Set, PlayerType, PlayerSubType, ShowdownPlayerCard, ChartCategory, Era, Position
import argparse
parser = argparse.ArgumentParser(description="Convert Original WOTC MLB Showdown Card Data to Showdown Bot Cards.")
parser.add_argument('-s','--sets', type=str, help='Sets to test (ex: 2000, 2001, 2005)', default='2000,2001,2002,2003,2004,2005')
parser.add_argument('-t','--types', type=str, help='Types to test (position_player, starting_pitcher, relief_pitcher)', default='position_player,starting_pitcher,relief_pitcher')
parser.add_argument('-pc','--is_pitchers_combined', action='store_true', help='Combine relievers and starters into one table')
parser.add_argument('-e','--expansions', type=str, help='Expansions to test (ex: BS)', default='BS')
parser.add_argument('-ptr','--point_range', type=str, help='Range of points to include', default=None)
parser.add_argument('-pos','--positions', type=str, help='List of positions to include, separated by a comma', default=None)
parser.add_argument('-p','--show_players', action='store_true', help='Show player level breakdown')
parser.add_argument('-nm','--names', type=str, help='List of names to show', default='')
parser.add_argument('-obp','--show_obp', action='store_true', help='Show OBP Breakdown')
parser.add_argument('-ex', '--export', action='store_true', help='Export to file')
parser.add_argument('-src','--source', type=str, help='Source of WOTC data', default='GSHEET')
args = parser.parse_args()

# ------------------------------
# CLASSES FOR COMPARISON
# ------------------------------


class Stat(Enum):
    COMMAND_OUTS = "command_outs_concat"
    OBP = "onbase_perc"
    SLG = "slugging_perc"
    OPS = "onbase_plus_slugging"
    COMMAND = "command"
    SPEED = "speed"
    POINTS = "points"
    HR_START = "hr_start"
    _2B_START = "_2b_start"
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

    @property
    def is_all_or_nothing(self) -> bool:
        return self in [Stat.COMMAND_OUTS]

    def is_valid_for_type(self, type: PlayerSubType) -> bool:
        match self:
            case Stat.PU | Stat._2B_START: return type.is_pitcher
            case Stat.SPEED | Stat._3B | Stat._1B_PLUS: return not type.is_pitcher
            case _: return True

    @property
    def difference_multiplier(self) -> float:
        match self :
            case Stat.OBP: return 5
            case Stat.SLG: return 5
            case Stat.OPS: return 5
            case _: return 1
    
    @property
    def overall_accuracy_weight(self) -> float:
        match self :
            case Stat.OBP: return 3
            case Stat.SO | Stat.PU | Stat.GB | Stat.FB | Stat._1B_PLUS: return 0.33
            case Stat.HR_START: return 0.15
            case Stat.COMMAND_OUTS: return 0.0
            case _: return 1

    @property
    def attribute_source(self) -> str:
        """Name of attribute on the Showdown Bot object to get stat"""
        match self :
            case Stat.OBP | Stat.SLG | Stat.OPS: return "projected"
            case Stat.COMMAND | Stat.HR_START | Stat._2B_START | Stat.COMMAND_OUTS: return "chart"
            case Stat.SPEED: return "speed"
            case Stat.POINTS: return "points"
            case _: return "chart.category_results_count_dict"

    @property
    def label(self) -> str:
        match self:
            case Stat.OBP | Stat.OPS | Stat.SLG | Stat.COMMAND | Stat.SPEED | Stat.POINTS | Stat.HR_START | Stat._2B_START | Stat.COMMAND_OUTS: return self.name
            case _: return self.value


class StatDiffClassification(Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    MATCH = "MATCH"
    NONE = "NONE"

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
    BLACK = '\033[30m'
    END = '\033[0m'


class StatComparison(BaseModel):
    stat: Stat
    wotc: int | float | str
    bot: int | float | str
    diff: int | float = 0
    accuracy: float = 0
    classification: StatDiffClassification = None

    def __init__(self, **data) -> None:
        super().__init__(**data)

        if self.stat.is_all_or_nothing:
            self.diff = 1 if self.wotc == self.bot else 0
            self.accuracy = 1 if self.wotc == self.bot else 0
            self.classification = StatDiffClassification.MATCH if self.diff == 1 else (StatDiffClassification.NONE if self.stat.is_all_or_nothing else StatDiffClassification.BELOW)
            return 

        # CALC DIFF AND ASSIGN CLASSIFICATION
        self.diff = self.bot - self.wotc

        self.accuracy = self.pct_accuracy(n1=self.wotc, n2=self.bot)

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
        if denominator in [0.5, 1.5] and self.stat not in [Stat.OBP, Stat.SLG, Stat.OPS]:
            denominator = 1.0
            difference -= 0.5
        
        pct_diff = ( self.stat.difference_multiplier * difference / denominator )
        return 1.0 - pct_diff
    
    @property
    def weighted_accuracy(self) -> float:
        return self.accuracy * self.stat.overall_accuracy_weight
    

class CardComparison(BaseModel):
    wotc: WotcPlayerCard
    bot: ShowdownPlayerCard
    bot_matching_command_outs: ShowdownPlayerCard
    stat_comparisons: dict[Stat, StatComparison] = {}
    overall_accuracy: float = 1.0

    def __init__(self, **data) -> None:
        super().__init__(**data)

        stats_to_compare = [s for s in Stat if s.is_valid_for_type(self.wotc.player_sub_type)]
        for stat in stats_to_compare:
            match stat.attribute_source:
                case "points":
                    wotc_stat = self.wotc.points
                    bot_stat = self.wotc.points_estimated
                case "projected":
                    wotc_stat = self.wotc.projected.get(stat.value, 0)
                    bot_stat = self.bot.projected.get(stat.value, 0)
                case "chart":
                    wotc_stat = getattr(self.wotc.chart, stat.value)
                    bot_stat = getattr(self.bot_matching_command_outs.chart, stat.value) if stat in [Stat.HR_START, Stat._2B_START] else getattr(self.bot.chart, stat.value) 
                case "speed":
                    wotc_stat = getattr(self.wotc.speed, stat.value)
                    bot_stat = getattr(self.bot.speed, stat.value)
                case "chart.category_results_count_dict":
                    wotc_stat = self.wotc.chart.category_results_count_dict.get(stat.value, 0) + (self.wotc.chart.category_results_count_dict.get(Stat._1B_PLUS.value, 0) if stat == Stat._1B else 0)
                    bot_stat = self.bot_matching_command_outs.chart.category_results_count_dict.get(stat.value, 0) + (self.bot_matching_command_outs.chart.category_results_count_dict.get(Stat._1B_PLUS.value, 0) if stat == Stat._1B else 0)
            
            self.stat_comparisons[stat] = StatComparison(
                stat=stat,
                wotc=wotc_stat,
                bot=bot_stat
            )
        
        self.overall_accuracy = self.weighted_accuracy

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
        rprint(f"{wotc.name} {self.accuracy_for_print}  WOTC: {wotc.chart.command_outs_concat}  Bot: {showdown_bot.chart.command_outs_concat}  G:{wotc.stats.get('G', 0)}")
        table = PrettyTable()
        table.field_names = ['Stat', 'WOTC', 'BOT', 'Diff', 'Accuracy', 'Classification']
        for stat, comparison in self.stat_comparisons.items():
            table.add_row([stat.name, comparison.wotc, comparison.bot, round(comparison.diff, 3), f'{comparison.accuracy:.2%}', f'{comparison.classification.value}'])
        print(table)

    def as_json(self) -> dict:
        """
        Convert wotc and bot data to json data for export. 
        Does not include stat comparisons
        """

        data: dict = {'overall_accuracy': self.overall_accuracy}
        wotc_fields_to_include = ['name', 'set', 'year', 'player_type',]
        common_fields_to_include = ['chart.command_outs_concat', 'chart.outs', 'points', 'projected', 'speed.speed', 'chart.ranges']
        for type in ['wotc', 'bot', 'bot_matching_command_outs']:
            card: ShowdownPlayerCard = getattr(self, type)
            data.update({f'{type}_{field}': (getattr(getattr(card, field.split('.')[0]), field.split('.')[1]) if '.' in field else getattr(card, field)) for field in common_fields_to_include})
            if type == 'wotc':
                card_as_json = card.model_dump(mode='json')
                data.update({f'{field}': card_as_json.get(field, None) for field in wotc_fields_to_include})
                data['player_sub_type'] = card.player_sub_type.name
                data['stats'] = {k: v for k, v in card.stats.items() if k not in ['accolades', 'positions',]}
        return data

def color_classification(accuracy: float, green_cutoff: float = 0.9, yellow_cutoff: float = 0.7) -> ConsoleColor:
    if accuracy > green_cutoff: return ConsoleColor.GREEN
    elif accuracy > yellow_cutoff: return ConsoleColor.YELLOW
    else: return ConsoleColor.RED
    
def onbase_table(comparisons: list[CardComparison]) -> PrettyTable:
    obps_for_command_outs: dict[str, dict[str, list[float]]] = {}
    for source in ['wotc', 'bot']:
        for c in comparisons:
            card = c.wotc if source == 'wotc' else c.bot
            key = card.chart.command_outs_concat
            real_obp = card.stats.get('onbase_perc', 0.00)
            command_out_obp_dict = obps_for_command_outs.get(key, {})
            if key not in obps_for_command_outs:
                obps_for_command_outs[key] = command_out_obp_dict
            source_obp_list = command_out_obp_dict.get(source, [])
            source_obp_list.append(real_obp)
            obps_for_command_outs[key][source] = source_obp_list
    table = PrettyTable()
    table.field_names = ['Command-Outs', 'WOTC', 'BOT', 'Diff', 'Accuracy', 'Classification', 'WOTC Range', 'BOT Range', 'WOTC Count', 'BOT Count']
    sorted_obps_for_command_outs = sorted(obps_for_command_outs.items(), key=lambda x: statistics.mean(x[1].get('bot', [0])), reverse=True)
    for command_outs, obp_dict in sorted_obps_for_command_outs:
        
        # AVG OBP
        wotc_avg_obp = mean(obp_dict.get('wotc', [])) if len(obp_dict.get('wotc', [])) > 0 else 0
        bot_avg_obp = mean(obp_dict.get('bot', [])) if len(obp_dict.get('bot', [])) > 0 else 0
        is_one_sided = wotc_avg_obp == 0 or bot_avg_obp == 0
        
        # RANGE
        wotc_obp_range = f"{min(obp_dict['wotc']):.3f} - {max(obp_dict['wotc']):.3f}" if len(obp_dict.get('wotc', [])) > 0 else 0
        bot_obp_range = f"{min(obp_dict['bot']):.3f} - {max(obp_dict['bot']):.3f}" if len(obp_dict.get('bot', [])) > 0 else 0

        # COUNTS
        wotc_count = len(obp_dict.get('wotc', []))
        bot_count = len(obp_dict.get('bot', []))

        # DIFF AND ACCURACY
        diff = bot_avg_obp - wotc_avg_obp
        accuracy = 0.00 if is_one_sided else 1 - ( abs(diff) / ((wotc_avg_obp + bot_avg_obp) / 2) )
        accuracy_color = ConsoleColor.BLACK if is_one_sided else color_classification(accuracy=accuracy, green_cutoff=0.99, yellow_cutoff=0.96)
        classification = StatDiffClassification.MATCH if accuracy >= 0.99 or is_one_sided else StatDiffClassification.BELOW if diff < 0 else StatDiffClassification.ABOVE
        classification_color = ConsoleColor.BLACK if is_one_sided else ConsoleColor.RED if classification == StatDiffClassification.ABOVE else ConsoleColor.YELLOW if classification == StatDiffClassification.BELOW else ConsoleColor.GREEN
        table.add_row([
            command_outs, f'{wotc_avg_obp:.3f}', f'{bot_avg_obp:.3f}', f'{diff:.3f}', 
            f'{accuracy_color.value}{accuracy:.2%}{ConsoleColor.END.value}', 
            f'{classification_color.value}{classification.value}{ConsoleColor.END.value}',
            wotc_obp_range, bot_obp_range,
            wotc_count, bot_count
        ])
    return table

def suggested_command_out_opponent(set: Set, is_pitcher: bool, comparisons: list[CardComparison]) -> PrettyTable:

    # LIST OBP FOR EACH COMMAND OUT
    obps_for_command_outs: dict[str, list[float]] = {}
    for c in comparisons:
        card = c.wotc
        key = card.chart.command_outs_concat
        real_obp = card.stats.get('onbase_perc', 0.00)
        command_out_obp_list: list[float] = obps_for_command_outs.get(key, [])
        command_out_obp_list.append(real_obp)
        obps_for_command_outs[key] = command_out_obp_list
    
    # AGGREGATE TO AVG OBP
    avg_obps_for_command_outs: dict[str, float] = {key: mean(obp_list) for key, obp_list in obps_for_command_outs.items() if len(obp_list) > 1 }

    # CALCULATE PROJECTIONS FOR EACH COMMAND OUT COMBINATION, COMPARE TO AVG OBP
    table = PrettyTable()
    table.field_names = ['Command-Outs', 'WOTC AVG OBP', 'MOST ACCRUATE OBP', 'MOST ACCURATE OPPONENT', 'DIFF']
    test_opponent_command_out_combinations = set.test_command_out_combinations(is_pitcher=not is_pitcher)
    command_out_opponent_accuracies: dict[str, dict[str: float]] = {}
    for command_out, avg_obp in avg_obps_for_command_outs.items():
        command, outs = [int(c) for c in command_out.split('-')]

        # PROJECT OBP FOR EACH PROJECTION
        obp_projections: dict[str, float] = {}
        for opponent_command, opponent_outs in test_opponent_command_out_combinations:

            # DEFINE MATCHUP
            onbase = opponent_command if is_pitcher else command
            control = command if is_pitcher else opponent_chart
            hitter_onbase_results = 20 - (opponent_outs if is_pitcher else outs)
            pitcher_onbase_results = 20 - (outs if is_pitcher else opponent_outs)

            # CALCULATE ADVANTAGE
            prob_hitter_advantage = (onbase-control) / 20.0
            prob_pitcher_advantage = 1.0 - prob_hitter_advantage

            # ADD PROBABILITY OF RESULT FOR BOTH PATHS (HITTER ADV AND PITCHER ADV)
            hitter_rate = prob_hitter_advantage * (hitter_onbase_results / 20)
            pitcher_rate = prob_pitcher_advantage * (pitcher_onbase_results / 20)
            obp = hitter_rate + pitcher_rate

            obp_projections[f'{round(opponent_command,1)}-{round(opponent_outs,1)}'] = round(obp, 4)

        # ADD TO OVERALL
        command_out_opponent_accuracies[command_out] = obp_projections

        # SORT BY DIFFERENCE FROM AVG_OBP
        sorted_projections = sorted(obp_projections.items(), key=lambda x: abs(avg_obp - x[1]))
        table.add_row([command_out, f'{avg_obp:.3f}', sorted_projections[0][1], sorted_projections[0][0], f'{abs(avg_obp - obp_projections[sorted_projections[0][0]]):.3f}'])
    
    # BEST OPPONENT ACROSS ALL COMMAND OUTS
    best_opponent_accuracies: dict[str, float] = {}
    for command, outs in test_opponent_command_out_combinations:
        command_out_str = f'{round(command, 1)}-{round(outs, 1)}'
        all_diffs = []
        for command_out, obp_dict in command_out_opponent_accuracies.items():
            wotc_avg = avg_obps_for_command_outs.get(command_out, 0)
            obp = obp_dict.get(command_out_str, 0)
            diff = round(abs(wotc_avg - obp), 4)
            all_diffs.append(diff)
        best_opponent_accuracies[command_out_str] = mean(all_diffs)
    best_opponent_accuracies = sorted(best_opponent_accuracies.items(), key=lambda x: x[1])[:5]
    table.add_row(['BEST OPPONENTS', '', '', '', ' | '.join([b[0] for b in best_opponent_accuracies])])
    return table


def accuracy_table(stats: list[Stat], comparisons: list[CardComparison]) -> PrettyTable:
    table = PrettyTable()
    table.field_names = ['Stat', 'Avg Diff', 'Avg Accuracy', 'Above', 'Below', 'Ratio', 'Match (0s)', 'Match', 'Tot', 'Match %', 'Largest Diff']

    # LOOP THROUGH STATS
    for stat in stats:
        
        # GET ALL COMPARISONS FOR STAT
        stat_comps = [c.stat_comparisons[stat] for c in comparisons if stat in c.stat_comparisons]

        # AGGREGATE
        diffs_list = [abs(sc.diff) if stat == Stat.POINTS else sc.diff for sc in stat_comps]
        avg_diff = mean(diffs_list) if len(diffs_list) > 0 else 0
        accuracy_comps = [sc.accuracy for sc in stat_comps]
        avg_accuracy = mean(accuracy_comps) if len(accuracy_comps) > 0 else 0
        above = sum([1 for sc in stat_comps if sc.classification == StatDiffClassification.ABOVE])
        below = sum([1 for sc in stat_comps if sc.classification == StatDiffClassification.BELOW])
        match = sum([1 for sc in stat_comps if sc.classification == StatDiffClassification.MATCH])
        match_zeros = sum([1 for sc in stat_comps if sc.classification == StatDiffClassification.MATCH and sc.wotc == 0])
        matches_no_zeros = match - match_zeros
        match_pool = len(stat_comps) - match_zeros
        match_pct = matches_no_zeros / match_pool if match_pool > 0 else 0

        # ABOVE/BELOW/BALANCED
        above_below_ratio = above / (above + below) if above + below > 0 else 0
        is_balanced = (above_below_ratio > 0.48 and above_below_ratio < 0.52) or match_pct > 0.85 or abs(above - below) < 5
        above_below = 'BALANCED' if is_balanced else 'BELOW' if above_below_ratio < 0.5 else 'ABOVE'
        above_below_color = ConsoleColor.GREEN if above_below == 'BALANCED' else ConsoleColor.RED if above_below == 'ABOVE' else ConsoleColor.YELLOW

        largest_diff = round(max([sc.abs_diff for sc in stat_comps]) if len(stat_comps) > 0 else 0,3) or 0
        largest_diff_name = f"{next((f'{c.wotc.first_initial}. {c.wotc.last_name}' for c in comparisons if round(c.stat_comparisons[stat].abs_diff if stat in c.stat_comparisons else 0,3) == round(largest_diff,3)), '')} ({largest_diff})"

        # COLORS
        accuracy_color = color_classification(accuracy=avg_accuracy)
        diff_color = color_classification(accuracy=avg_accuracy, green_cutoff=0.95, yellow_cutoff=0.0)
        match_color = color_classification(accuracy=match_pct, green_cutoff=0.80, yellow_cutoff=0.35)

        # ADD TO TABLE
        table.add_row(
            [stat.label, f'{diff_color.value}{round(avg_diff, 3):.3f}{ConsoleColor.END.value}', f'{accuracy_color.value}{avg_accuracy:.2%}{ConsoleColor.END.value}', 
            above, below, f'{above_below_color.value}{above_below}{ConsoleColor.END.value}', 
            match_zeros, match, match_pool,
            f'{match_color.value}{match_pct:.2%}{ConsoleColor.END.value}', largest_diff_name])

    # OVERALL ACCURACY
    all_accuracy = [c.weighted_accuracy for c in comparisons]
    total = len(all_accuracy)
    matches = len([c for c in comparisons if c.weighted_accuracy == 1.0])
    least_accurate = list(sorted(comparisons, key=lambda x: x.weighted_accuracy))[0:3]
    largest_diff_names = '\n'.join([f'{c.wotc.first_initial}. {c.wotc.last_name} ({c.weighted_accuracy:.2%})' for c in least_accurate])
    overall_accuracy = mean(all_accuracy)
    table.add_row(['Overall', '', f'{overall_accuracy:.2%}', '', '', '', '', matches, total, '', largest_diff_names])
    
    return table

# ------------------------------
# 1. LOAD WOTC CARDS
# ------------------------------
set_list: list[Set] = [Set(s) for s in args.sets.split(',')]
expansion_list: list[str] = args.expansions.split(',')
pts_split = args.point_range.split('-') if args.point_range else None
points_included: list[int] = list(range(int(pts_split[0]), int(pts_split[1]) + 1, 10)) if pts_split else None
player_sub_types_filter: list[PlayerSubType] = [PlayerSubType(t) for t in args.types.split(',')]
player_types_list: list[PlayerType] = ([PlayerType.HITTER] if any([not t.is_pitcher for t in player_sub_types_filter]) else []) + ([PlayerType.PITCHER] if any([t.is_pitcher for t in player_sub_types_filter]) else [])
wotc_player_card_set = WotcPlayerCardSet(source=args.source, sets=set_list, player_types=[t for t in PlayerType] if args.export else player_types_list)
if args.export:
    wotc_player_card_set.export_to_local_file(formats=['csv', 'json'])

# ------------------------------
# 2. LOOP THROUGH SETS, TYPES, CARDS
# ------------------------------
all_set_comparisons_dict: dict[Set, dict[str, list[CardComparison]]] = {}

for set in set_list:
    
    for type in PlayerType:
        
        # TYPE BASED DATA
        stats_for_type = [s for s in Stat if s.is_valid_for_type(type)]

        sub_types = [st for st in type.sub_types]
        all_subtype_comps: list[StatComparison] = []
        for sub_type in sub_types:

            # PRINT OUTPUT
            print_output = sub_type in player_sub_types_filter

            # CHECK OPPONENT CHART
            opponent_type = type.opponent_type
            opponent_chart = set.wotc_baseline_chart(opponent_type)
            filled_slots = round(sum(opponent_chart.values.values()), 2)
            if filled_slots != 20:
                remaining_slots = 20 - filled_slots
                suggestion_str = 'remove' if remaining_slots < 0 else 'add'
                if print_output:
                    rprint(f"\n[yellow]Chart does not add up to 20 for {set.value} {opponent_type.value}[/yellow] ({filled_slots}/20). Please {suggestion_str} {abs(round(remaining_slots,2))} slots")
            
            chart_outs = round(sum([v for c, v in opponent_chart.values.items() if c.is_out]), 2)
            listed_outs = round(opponent_chart.outs, 2)
            if chart_outs != listed_outs:
                if print_output:
                    rprint(f"\n[yellow]Outs do not match for {set.value} {opponent_type.value}[/yellow] ({chart_outs}/{listed_outs})")
            
            set_comparisons: list[CardComparison] = []
            set_type_player_set = {id: card for id, card in wotc_player_card_set.cards.items() if card.set == set and card.player_sub_type == sub_type and card.image.expansion in expansion_list}
            wotc_command_list = [c.chart.command for c in set_type_player_set.values()]
            for index, (id, wotc) in enumerate(set_type_player_set.items(), 1):
                
                # SKIP IF PLAYER FALLS UNDER FILTERS
                is_no_stats = len(wotc.stats) == 0
                match wotc.player_sub_type:
                    case PlayerSubType.POSITION_PLAYER:
                        is_small_sample_size = (wotc.stats.get('PA', 0) < 300 or wotc.stats.get('G', 0) < 100 )
                    case PlayerSubType.STARTING_PITCHER:
                        is_small_sample_size = (wotc.stats.get('IP', 0) < 50 or wotc.stats.get('PA', 0) < 150 )
                    case PlayerSubType.RELIEF_PITCHER:
                        is_small_sample_size = (wotc.stats.get('IP', 0) < 30 or wotc.stats.get('PA', 0) < 100 )
                is_excluded_pts_filter = False if not points_included else wotc.points not in points_included
                is_excluded_positions_filter = False if not args.positions else not any([True for p in wotc.positions_and_defense.keys() if p in [Position(p) for p in args.positions.split(',')]])
                if is_small_sample_size or is_no_stats or is_excluded_pts_filter:
                    continue

                # CREATE SHOWDOWN BOT CARD FROM STATS
                stats = wotc.stats.copy()
                if len(stats) > 0:
                    stats['BB'] = stats.get('BB', 0) - stats.get('HBP', 0)
                
                commands_excluded = [c for c in range(0,17) if c not in wotc_command_list]
                showdown_bot = ShowdownPlayerCard(name=wotc.name,year=wotc.year,set=wotc.set,expansion=wotc.image.expansion,player_type=wotc.player_type,stats=stats,commands_excluded=commands_excluded)
                showdown_bot_matching_command_outs = ShowdownPlayerCard(name=wotc.name,year=wotc.year,set=wotc.set,expansion=wotc.image.expansion,player_type=wotc.player_type,stats=stats,command_out_override=(wotc.chart.command, wotc.chart.outs))

                # COMPARE
                comparison = CardComparison(wotc=wotc, bot=showdown_bot, bot_matching_command_outs=showdown_bot_matching_command_outs)
                set_comparisons.append(comparison)

                # PRINT
                show_player = ( args.names == '' or wotc.name in args.names ) and args.show_players
                if show_player and print_output:
                    comparison.print_table()

            # ADD TO SUBTYPES COMBO (FOR PITCHERS)
            if args.is_pitchers_combined:
                all_subtype_comps += set_comparisons

            # ------------------------------
            # 3. SUMMARIZE SET ACCURACY
            # ------------------------------
                
            # OBP AVGS PER COMMAND/OUTS
            if (not args.is_pitchers_combined or not type.is_pitcher) and args.show_obp:
                obp_table = onbase_table(comparisons=set_comparisons)
                if print_output:
                    print(f"\n\n{set} ONBASE SUMMARY ({sub_type.name.replace('_', ' ')}S)")
                    print(obp_table)

                suggested_table = suggested_command_out_opponent(set=set, is_pitcher=type.is_pitcher, comparisons=set_comparisons)
                if print_output:
                    print(f"\n\n{set} SUGGESTED ONBASE SUMMARY ({type.name.replace('_', ' ')}S)")
                    print(suggested_table)

            # CREATE ACCURACY TABLE
            table = accuracy_table(stats=stats_for_type, comparisons=set_comparisons)
            if print_output:
                print(f"\n\n{set} SUMMARY ({sub_type.name.replace('_', ' ')}S)")
                print(table)

            # ------------------------------
            # 4. ADD TO CROSS SET STATS
            # ------------------------------
            type_value = PlayerType.PITCHER.name if type.is_pitcher and args.is_pitchers_combined else type.name
            updated_set_comparisons = all_set_comparisons_dict.get(set, {})
            current_type_set_comps = updated_set_comparisons.get(type_value, [])
            updated_set_comparisons[type_value] = current_type_set_comps + set_comparisons
            all_set_comparisons_dict[set] = updated_set_comparisons            
        
        # CROSS SUBTYPE TOTALS
        if args.is_pitchers_combined and type.is_pitcher:

            if args.show_obp:
                obp_table = onbase_table(comparisons=all_subtype_comps)
                if print_output:
                    print(f"\n\n{set} ONBASE SUMMARY ({type.name.replace('_', ' ')}S)")
                    print(obp_table)

                suggested_table = suggested_command_out_opponent(set=set, is_pitcher=type.is_pitcher, comparisons=all_subtype_comps)
                if print_output:
                    print(f"\n\n{set} SUGGESTED ONBASE SUMMARY ({type.name.replace('_', ' ')}S)")
                    print(suggested_table)

            table = accuracy_table(stats=stats_for_type, comparisons=all_subtype_comps)
            if print_output:
                print(f"\n\n{set} SUMMARY ({type.name.replace('_', ' ')}S)")
                print(table)

# ------------------------------
# 5. SUMMARIZE ACROSS ALL SETS
# ------------------------------
table = PrettyTable()
table.field_names = ['Set', 'Type', 'Accuracy',]
flattened_comparisons: list[CardComparison] = []
for set, player_type_comparisons in all_set_comparisons_dict.items():

    for player_type, comparisons in player_type_comparisons.items():

        flattened_comparisons += comparisons
        all_accuracy = [c.weighted_accuracy for c in comparisons]
        overall_set_accuracy = mean(all_accuracy)

        # ACCURACY COLOR
        if overall_set_accuracy > 0.90: accuracy_color = ConsoleColor.GREEN
        elif overall_set_accuracy > 0.75: accuracy_color = ConsoleColor.YELLOW
        else: accuracy_color = ConsoleColor.RED

        table.add_row([set.value, player_type, f'{accuracy_color.value}{overall_set_accuracy:.2%}{ConsoleColor.END.value}'])
if len(set_list) > 1:
    print(table)

# ------------------------------
# 5. OUTPUT TO FILE
# ------------------------------
if args.export:
    # FLATTEN STATS COMPARISONS
    flattened_stat_comp_data: list[dict] = []
    for card_comp in flattened_comparisons:
        data = card_comp.as_json()
        for stat_to_pop in ['accolades', 'years_played', 'summary',]:
            data['stats'].pop(stat_to_pop, None)
        for stat_comp in card_comp.stat_comparisons.values():
            stat_data = stat_comp.model_dump(mode="json")
            stat_data.update(data)
            flattened_stat_comp_data.append(stat_data)
    df = pd.json_normalize(flattened_stat_comp_data, sep='.', max_level=None)
    export_path = Path(os.path.join(Path(os.path.join(os.path.dirname(__file__)), 'output', 'stat_comparisons.csv')))
    df.to_csv(export_path, index=False)

