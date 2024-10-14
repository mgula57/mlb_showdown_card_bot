from enum import Enum
from pydantic import BaseModel
from typing import Union, Optional
from collections import ChainMap
from pprint import pprint
from operator import itemgetter
import pandas as pd
import numpy as np
import os
from pathlib import Path
import math

try:
    from .value_range import ValueRange
    from .metrics import Stat
except ImportError:
    from value_range import ValueRange
    from metrics import Stat

# ---------------------------------------
# CHART CATEGORY
# ---------------------------------------

class ChartCategoryFillMethod(str, Enum):
    """Method to fill chart categories"""
    RATE = "RATE" # FILL BASED ON RATE OF REAL STATS
    PCT = "PCT" # FILL BASED ON PERCENTAGE OF TOTAL CATEGORY

class ChartCategory(str, Enum):

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
    def is_out(self) -> bool:
        return self.value in ['PU', 'SO', 'GB', 'FB']
    
    @property
    def is_filled_in_desc_order(self) -> bool:
        """Check if category is filled in descending order. Outs and BB are filled in ascending order."""
        return not self.is_out and self != ChartCategory.BB

    def is_valid_for_type(self, is_pitcher:bool) -> bool:
        """Check if category is valid for player type"""
        if is_pitcher:
            return self not in [ChartCategory._1B_PLUS, ChartCategory._3B]
        else:
            return self not in [ChartCategory.PU]

    @property
    def is_assigned_based_on_rate_stats(self) -> bool:
        """True if chart values are based on real stats per 400 PA"""
        return self.value in ['SO', 'BB', '2B', '3B', 'HR',]

    @property
    def is_over_21_results_included_in_projection(self) -> bool:
        return self.value in ['HR']
    
    @property
    def slot_limit(self) -> int:
        """Max number of results for a category. For GB/FB/PU, the cap is 2/3 out the out results (defined elsewhere)."""
        match self:
            case ChartCategory.BB: return 12 # BARRY BONDS EFFECT (HUGE WALK)
            case ChartCategory.HR: return 10
            case ChartCategory._2B: return 12
            case _: return 20

    def rounding_cutoff(self, is_pitcher:bool, set:str) -> float:
        """Decimal to round up at.
        
        Args:
            is_pitcher: If the player is a pitcher.
            is_expanded: If the chart format is expanded.
            era: Era used for the chart.
        """
        match self:
            case ChartCategory.HR:
                if is_pitcher and set in ['2000', '2001',]:
                    return 0.425
        return 0.5

    def fill_method(self, set:str, is_pitcher:bool) -> ChartCategoryFillMethod:

        # HITTER CRITERIA
        is_hitter = not is_pitcher
        is_hitter_eligible = is_hitter and self.is_out and set not in ['2001', 'CLASSIC', '2002', ] and not (set == '2000' and self == ChartCategory.SO)
        is_pitcher_eligible = is_pitcher and self.is_out and set in ['2000', '2001', 'CLASSIC'] and self != ChartCategory.PU
        if is_hitter_eligible or is_pitcher_eligible:
            return ChartCategoryFillMethod.PCT
        
        return ChartCategoryFillMethod.RATE

    def category_multiplier(self, set:str, is_pitcher:bool) -> float:
        """Multiplier for category based on set and player type"""

        # DOESNT APPLY TO RATE
        if self.fill_method(set=set, is_pitcher=is_pitcher) == ChartCategoryFillMethod.RATE:
            return 1.0
        
        is_hitter = not is_pitcher
        match set:
            case '2000':
                if is_hitter:
                    match self:
                        case ChartCategory.SO: return 1.00
                        case ChartCategory.GB: return 1.22
                        case ChartCategory.FB: return 0.78
                else:
                    match self:
                        case ChartCategory.SO: return 1.20
                        case ChartCategory.GB: return 0.97
                        case ChartCategory.FB: return 0.83
            case '2001':
                if is_pitcher:
                    match self:
                        case ChartCategory.SO: return 1.08
                        case ChartCategory.GB: return 1.07
                        case ChartCategory.FB: return 0.85
            case '2003':
                if is_hitter:
                    match self:
                        case ChartCategory.SO: return 1.07
                        case ChartCategory.GB: return 1.18
                        case ChartCategory.FB: return 0.75
            case '2004' | '2005' | 'EXPANDED':
                if is_hitter:
                    match self:
                        case ChartCategory.GB: return 1.20
                        case ChartCategory.FB: return 0.80
                        
        return 1.0
    
    def decay_rate_and_start(self, set:str, is_pitcher:bool) -> tuple[float, int]:
        """Decay rate for category based on set and player type"""

        is_hitter = not is_pitcher
        match set:
            case '2000':
                if is_hitter:
                    match self:
                        case ChartCategory.SO: return (0.50, 2)
                        case ChartCategory._1B_PLUS: return (0.60, 2)
                else:
                    match self:
                        case ChartCategory.PU: return (0.50, 3)
            case '2001':
                if is_hitter:
                    match self:
                        case ChartCategory.SO: return (0.50, 2)
                        case ChartCategory.BB: return (0.60, 6)
                else:
                    match self:
                        case ChartCategory.PU: return (0.50, 3)
            case '2002':
                if is_hitter:
                    match self:
                        case ChartCategory.SO: return (0.65, 4)
                        case ChartCategory._1B_PLUS: return (0.70, 1)
                        case ChartCategory.BB: return (0.70, 6)
                else:
                    match self:
                        case ChartCategory.PU: return (0.50, 3)
            case '2003':
                if is_hitter:
                    match self:
                        case ChartCategory.BB: return (0.72, 3)
                else:
                    match self:
                        case ChartCategory.GB: return (0.80, 8)
            case _:
                if is_hitter:
                    match self:
                        case ChartCategory._1B_PLUS: return (0.60, 3)

        return None

    def value_multiplier(self, set:str) -> float:
        match self:
            case ChartCategory.PU:
                match set:
                    case '2000': return 2.80
                    case '2001' | 'CLASSIC': return 4.0
                    case '2002': return 4.35
                    case '2003': return 2.75
                    case '2004': return 2.60
                    case '2005' | 'EXPANDED': return 3.00

        return 1.0


# ---------------------------------------
# CHART ACCURACY
# ---------------------------------------

class ChartAccuracyBreakdown(BaseModel):

    stat: Stat
    actual: float 
    comparison: float
    is_pitcher: bool
    weight: float = 1.0
    accuracy: float = 1.0
    weighted_accuracy: float = 1.0
    adjustment_pct: float = 1.0

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.calculate_accuracy_attributes()

    @property
    def summary_str(self) -> str:
        return f"{self.stat.name}: {round(self.actual, 3)} vs {round(self.comparison, 3)} ({round(self.accuracy * 100, 1)}% @{self.weight * 100}%)"
    
    @property
    def difference_multiplier(self) -> float:
        """Normalize differences for smaller ranges (ex: 1-6 vs 7-16)"""
        match self.stat:
            case Stat.COMMAND:
                return 0.5 if self.is_pitcher else 0.80
        
        return 1.0

    def calculate_accuracy_attributes(self) -> None:
        """Populate accuracy attributes for the chart accuracy breakdown"""
        diff = abs(self.actual - self.comparison) * self.difference_multiplier
        self.accuracy = 1.0 if self.actual == self.comparison else max( 1 - ( diff / ((self.actual + self.comparison) / 2) ), 0)
        self.accuracy *= self.adjustment_pct
        self.weighted_accuracy = round(self.accuracy * self.weight, 4)

# ---------------------------------------
# CHART
# ---------------------------------------

class Chart(BaseModel):

    # CHART
    command: Union[int, float]
    outs: Union[int, float] = 0
    values: dict[ChartCategory, Union[int, float]] = {}
    results: dict[int, ChartCategory] = {}
    ranges: dict[ChartCategory, str] = {}
    sb: float = 0.0

    # SET METADATA
    set: str
    era: str
    era_year_list: list[int] = []
    is_expanded: bool
    opponent: Optional['Chart'] = None
    
    # PLAYER DATA
    is_pitcher: bool
    player_subtype: Optional[str] = None
    pa: int = 400
    stats_per_400_pa: dict[str, float] = {}

    # ERA ADJUSTMENT
    obp_adjustment_factor: float = 1.0

    # ACCURACY
    command_accuracy_weight: float = 1.0
    command_out_accuracy_weight: float = 1.0
    accuracy: float = 1.0
    accuracy_breakdown: dict[Stat, ChartAccuracyBreakdown] = {}
    is_command_out_anomaly: bool = False
    chart_categories_adjusted: list[ChartCategory] = []
    command_estimated: float = None

    # SPECIAL FLAGS
    is_baseline: bool = False
    is_wotc_conversion: bool = False

    def __init__(self, **data) -> None:
        super().__init__(**data)

        wotc_chart_results = data.get('wotc_chart_results', None)
        self.is_wotc_conversion = wotc_chart_results is not None
        
        # BASELINE CHART ADJUSTMENTS
        if self.is_baseline:
            
            # POPULATE OUTS IF BASELINE CHART
            if self.outs == 0: self.update_outs_from_values()

            # POPULATE YEAR LIST
            if len(self.era_year_list) == 0: self.era_year_list = [self.set_year]

        # CONVERT FROM WOTC DATA
        if self.is_wotc_conversion:
            self.generate_values_and_results_from_wotc_data(results_list=wotc_chart_results)

        # POPULATE ESTIMATED COMMAND
        if self.command_estimated is None and not self.is_baseline and not self.is_wotc_conversion:
            self.command_estimated = self.calculate_estimated_command(mlb_avgs_df=data.get('mlb_avgs_df', None))

        # POPULATE VALUES DICT
        if len(self.values) == 0:
            self.generate_values_and_results()

        # POPULATE ACCURACY
        if len(self.stats_per_400_pa) > 0:
            self.generate_accuracy_rating()

        self.generate_range_strings()

    @property
    def is_hitter(self) -> bool:
        return not self.is_pitcher
    
    @property
    def is_classic(self) -> bool:
        """Check if chart is classic format (2000, 2001, CLASSIC)"""
        return self.set in ['2000', '2001', 'CLASSIC']

    @property
    def categories_list(self) -> list[ChartCategory]:
        if self.is_pitcher:
            # 2000 HAS 'SO' FIRST, ALL OTHER YEARS HAVE 'PU' FIRST
            firstCategory = ChartCategory.SO if self.set == '2000' else ChartCategory.PU
            secondCategory = ChartCategory.PU if self.set == '2000' else ChartCategory.SO
            return [firstCategory,secondCategory,ChartCategory.GB,ChartCategory.FB,ChartCategory.BB,ChartCategory._1B,ChartCategory._2B,ChartCategory.HR]
        else:
            # HITTER CATEGORIES
            return [ChartCategory.SO, ChartCategory.GB, ChartCategory.FB, ChartCategory.BB, ChartCategory._1B, ChartCategory._1B_PLUS, ChartCategory._2B, ChartCategory._3B, ChartCategory.HR]

    def num_values(self, category:ChartCategory) -> int:
        return self.values.get(category, 0)

    @property
    def command_name(self) -> str:
        return 'Control' if self.is_pitcher else 'Onbase'

    @property
    def command_outs_concat(self) -> str:
        return f'{self.command}-{(self.outs / self.sub_21_per_slot_worth):.0f}'

    @property
    def values_as_list(self) -> list[list[str, str]]:
        """Convert chart values and command/outs to list of lists"""
        values_list = [ [self.command_name, str(self.command)], ['Outs', str(self.outs)] ]
        values_list += [[category.value, str(round(value,2))] for category, value in self.values.items()]
        return values_list
    
    @property
    def results_as_list(self) -> list[ChartCategory]:
        
        result_list: list[ChartCategory] = []
        for _, category in dict(sorted(self.results.items(), key=itemgetter(0))).items():
            result_list.append(category)
        
        return result_list

    @property
    def has_over_21_slot_values(self) -> bool:
        return self.sub_21_per_slot_worth < 1

    @property
    def slot_values(self) -> dict[int, float]:
        
        # EACH SLOT IS WORTH 1 FOR CLASSIC
        if not self.has_over_21_slot_values:
            return { i: 1 for i in range(1, 21) }
        
        # EXPANDED CHARTS
        slot_values_dict: dict[int, float] = { i: self.sub_21_per_slot_worth for i in range(1, 21) }
        remaining_value = 20 - sum(slot_values_dict.values())
        if self.is_pitcher:

            # 2003 SET FILLS LINEARLY FROM 21-26
            if self.set == '2003':
                original_remaining_value = remaining_value
                slot_value_capped_at = 26
                num_values_to_fill = slot_value_capped_at - 20

                # Create a sequence of numbers that decrease linearly
                values = np.linspace(start=original_remaining_value/num_values_to_fill * 1.2, stop=0, num=num_values_to_fill)

                # Ensure the values sum to the original remaining value
                values = original_remaining_value * values / values.sum()

                for i, value in enumerate(values, start=21):
                    slot_values_dict[i] = value
                    remaining_value -= value

                return slot_values_dict
            
            # FILL 21+ SLOTS WITH A GEOMETRIC PROGRESSION, STARTING AT THE REMAINING VALUE / 2
            # EX: 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125, 0.00390625, 0.001953125, 0.0009765625
            # THE FORMULA OF A GEOMETRIC PROGRESSION IS: a * r^(n-1) 
            # EX: 21:  0.5 * 0.5 ^ 0 = 0.5
            #     22:  0.5 * 0.5 ^ 1 = 0.25
            #     23:  0.5 * 0.5 ^ 2 = 0.125

            slot_values_21_plus: dict[int, float] = {}
            
            match self.set:
                case '2002': 
                    decay = 0.5
                    power = 0.5
                case _: 
                    decay = 0.2
                    power = 0.9
            starting_value = remaining_value * decay
            for i in range(21, 31):
                value = starting_value * pow(power, (i-21))
                remaining_value = 20 - sum(slot_values_dict.values()) - sum(slot_values_21_plus.values())
                slot_values_21_plus[i] = min(value, remaining_value)
            
            slot_values_dict.update(slot_values_21_plus)

            # FILL THE 30TH SLOT WITH THE REMAINING VALUE
            # ALLOWS THE VALUE TO ADD UP TO EXACTLY 20
            remaining_value = 20 - sum(slot_values_dict.values())
            slot_values_dict[30] += remaining_value

            return slot_values_dict
        else:
            
            # TOTAL AMOUNT AND NUMBER OF SLOTS TO SPREAD
            n_values = 3

            # CREATE A SEQUENCE OF NUMBERS THAT DECREASE LINEARLY
            values_list = np.linspace(start=remaining_value/n_values, stop=0, num=n_values)
            # ENSURE THE VALUES SUM TO THE TOTAL
            values_list = remaining_value * values_list / values_list.sum()

            values_dict = { i: v for i, v in enumerate(values_list, start=21) }        
            slot_values_dict.update(values_dict)

            # FILL REMAINING SLOTS (20+n - 30) WITH 0
            for i in range(21+n_values, 31):
                slot_values_dict[i] = 0

            return slot_values_dict

    @property
    def sub_21_per_slot_worth(self) -> float:
        if not self.is_expanded:
            return 1
        
        # 2002 FILLS EXTRA SLOTS WITH HR FOR 21+
        if self.set == '2002':
            return 0.99
        
        if self.is_pitcher:
            match self.set:
                case '2003':
                    command_multiplier = 0.008 * ( 1 - (self.command / 6) )
                    return 0.982 + command_multiplier
                case '2004' | '2005' | 'EXPANDED':
                    command_multiplier = 0.02 * ( 1 - (self.command / 6) )
                    return 0.95 + command_multiplier
            return 0.96
        
        return 0.975

    @property
    def sub_21_total_possible_slots(self) -> float:
        if not self.is_expanded:
            return 20
        
        return 20 * self.sub_21_per_slot_worth

    @property
    def total_possible_slots(self) -> int:
        if not self.has_over_21_slot_values or self.set == '2002':
            return 20
        
        return 30

    @property
    def gb_pct(self) -> float:
        return round(self.num_values(ChartCategory.GB) / self.outs, 3)
    
    @property
    def hr_start(self) -> int:
        return len([i for i, c in self.results.items() if c != ChartCategory.HR]) + 1

    @property
    def _2b_start(self) -> int:
        return len([ r for r in self.results.values() if r not in [ChartCategory.HR, ChartCategory._2B] ]) + 1

    @property
    def outs_full(self) -> int:
        return int(round(self.outs / self.sub_21_per_slot_worth))

    @property
    def category_results_count_dict(self) -> dict[ChartCategory, int]:
        """Sum of values under 21, rounded to nearest whole number"""
        final_dict: dict[ChartCategory, int] = {}
        for slot_num, category in self.results.items():
            if slot_num > 20: continue
            final_dict[category] = final_dict.get(category, 0) + 1
        return final_dict

    @property
    def hitter_single_plus_denominator_minimum(self) -> float:
        match self.set:
            case '2000': return 2.0
            case '2001' | 'CLASSIC': return 3.2
            case '2002': return 4.0
            case '2003': return 6.0
            case '2004' | '2005' | 'EXPANDED': return 4.5
    
    @property
    def hitter_single_plus_denominator_maximum(self) -> float:
        match self.set:
            case '2000': return 9.5
            case '2001' | 'CLASSIC': return 9.6
            case '2002': return 12.5
            case '2003' | '2004': return 10.5
            case '2005' | 'EXPANDED': return 9.75

    @property
    def set_year(self) -> int:
        match self.set:
            case 'CLASSIC': return 2000
            case 'EXPANDED': return 2004
            case _: return int(self.set) - 1

    @property
    def does_set_ignore_outlier_adjustments(self) -> bool:
        return self.set in ['2003', '2004', '2005', 'EXPANDED', 'CLASSIC']
    

    # ---------------------------------------
    # GENERATE CHART ATTRIBUTES
    # ---------------------------------------

    def __round_to_nearest_slot_value(self, value:float, cutoff:float = 0.5) -> float:
        """Round value to nearest slot worth"""
        return self.__custom_round(number=value, multiple=self.sub_21_per_slot_worth, cutoff=cutoff)

    def generate_values_and_results(self) -> None:
        """Generate values dictionary and store to self """

        def add_results_to_dict(category:ChartCategory, num_results:int, current_chart_index:int) -> None:
            if num_results == 0: return
            iterator = -1 if category.is_filled_in_desc_order else 1
            for i in range(current_chart_index, current_chart_index + ( (num_results) * iterator), iterator):
                self.results[i] = category

        def fill_chart_categories(categories: list[ChartCategory], is_reversed:bool = False) -> None:
                        
            # VARIABLES USED FOR PCT FILL METHOD
            categories_total_real_results_per_400 = sum([self.stats_per_400_pa.get(c.value.lower() + '_per_400_pa', 0) for c in categories])

            current_chart_index = self.total_possible_slots if is_reversed else 1
            for chart_category in categories:

                # SKIP 1B+, THAT IS FILLED LATER
                if chart_category in [ChartCategory._1B_PLUS]: continue

                # DEFINE LIMIT FOR CATEGORY
                category_limit = chart_category.slot_limit * self.sub_21_per_slot_worth
                if chart_category.is_out and chart_category != ChartCategory.SO:
                    multiplier = 3/4 if self.is_hitter else 3/4
                    category_limit = self.outs * multiplier if self.outs > 4 else self.outs

                is_out_max = self.outs if chart_category.is_out else 20 - self.outs
                category_remaining = is_out_max - sum([v for k,v in self.values.items() if k.is_out == chart_category.is_out])
                max_values = min(category_limit, category_remaining)
                min_values = category_remaining if chart_category in [ChartCategory._1B, ChartCategory.FB] else None

                # FILL CHART CATEGORY VALUES
                # FILL METHODS:
                #   PCT: FILL BASED ON PERCENTAGE OF TOTAL CATEGORY
                #       EX: 20% OF TOTAL OUTS PER 400 PA ARE GB
                #   RATE: FILL BASED ON RATE OF REAL STATS PER 400 PA
                #       EX: 5 DOUBLES PER 400 PA DIVIDED BETWEEN PITCHER AND HITTER CHARTS
                match chart_category.fill_method(set=self.set, is_pitcher=self.is_pitcher):
                    
                    case ChartCategoryFillMethod.PCT:
                        category_results_per_400_pa = self.stats_per_400_pa.get(f'{chart_category.value.lower()}_per_400_pa', 0)
                        category_multiplier = chart_category.category_multiplier(set=self.set, is_pitcher=self.is_pitcher)
                        category_pct = (category_results_per_400_pa / categories_total_real_results_per_400) * category_multiplier
                        raw_values = category_pct * self.outs
                        values = min( max( self.__round_to_nearest_slot_value(raw_values), category_remaining if chart_category == ChartCategory.FB else 0 ), max_values )
                        results = int(round(values / self.sub_21_per_slot_worth))

                    case ChartCategoryFillMethod.RATE:

                        # CALCULATE VALUES
                        values, results, was_limited = self.calc_chart_category_values_from_rate_stats(category=chart_category, current_chart_index=current_chart_index, max_values=max_values, min_values=min_values)

                        # IF SINGLE, SPLIT INTO 1B AND 1B+
                        if chart_category == ChartCategory._1B and not self.is_pitcher:
                            single_plus_values, single_plus_results = self.__single_plus_values_and_results(total_1B_values=values, current_chart_index=current_chart_index)
                            self.values[ChartCategory._1B_PLUS] = single_plus_values
                            add_results_to_dict(category=ChartCategory._1B_PLUS, num_results=single_plus_results, current_chart_index=current_chart_index)
                            current_chart_index -= single_plus_results
                            values -= single_plus_values
                            results -= single_plus_results

                        # CHECK FOR REMAINING VALUES IF FB WAS LIMITED AND THERE ARE REMAINING VALUES
                        if chart_category == ChartCategory.FB and was_limited:
                            outs_values_pre_fb = sum([v for k,v in self.values.items() if k.is_out])
                            total_outs_remaining = self.outs - outs_values_pre_fb - values
                            if total_outs_remaining >= self.sub_21_per_slot_worth:
                                # FILL WITH GB
                                gb_values = total_outs_remaining
                                gb_results = int(round(gb_values / self.sub_21_per_slot_worth))
                                self.values[ChartCategory.GB] = self.values.get(ChartCategory.GB, 0) + values
                                add_results_to_dict(category=ChartCategory.GB, num_results=gb_results, current_chart_index=current_chart_index)
                                current_chart_index += gb_results
                
                self.values[chart_category] = values
                add_results_to_dict(category=chart_category, num_results=results, current_chart_index=current_chart_index)
                current_chart_index += (results * -1 if chart_category.is_filled_in_desc_order else results)
                
        # CALCULATE OUTS BASED ON COMMAND
        obp = self.stats_per_400_pa.get('onbase_perc', 0)
        results_per_400_pa = 400 * obp
        opponent_values = 20 - self.opponent.outs
        my_onbase_values = (results_per_400_pa - (self.opponent_advantages_per_20 * opponent_values)) / self.my_advantages_per_20
        my_out_values = max(20 - my_onbase_values, 0)
        
        # CALC OUTS FOR SLOT SIZE
        if self.outs == 0:
            self.outs, _ = self.values_and_results(value=my_out_values)

        # ITERATE THROUGH CHART CATEGORIES
        all_categories = self.categories_list
        out_categories = [c for c in all_categories if not c.is_filled_in_desc_order]
        non_out_categories = [c for c in all_categories if c.is_filled_in_desc_order][::-1] # REVERSE NON OUTS TO START WITH HR
        fill_chart_categories(out_categories)
        fill_chart_categories(non_out_categories, is_reversed=True)

        # MAKE ADJUSTMENTS IF NECESSARY
        obp_pct_diff = self.__stat_projected_vs_real_pct_diff('onbase_perc')
        slg_pct_diff = self.__stat_projected_vs_real_pct_diff('slugging_perc')
        ops_pct_diff = self.__stat_projected_vs_real_pct_diff('onbase_plus_slugging')

        # ADJUST CHARTS THAT ARE OFF IN SLG AND OPS BUT CLOSE IN OBP
        # INCREASE/DECREASE EITHER 2B, 3B, OR HR BY 1 AND INCREASE/DECREASE 1B BY 1
        has_1b_values = self.num_values(ChartCategory._1B) >= self.sub_21_per_slot_worth
        is_under_in_slg_and_ops = slg_pct_diff < 0 \
                                    and ops_pct_diff < 0  \
                                    and abs(obp_pct_diff) < 0.03 \
                                    and abs(slg_pct_diff) > 0.01 \
                                    and has_1b_values
        is_over_in_slg_and_ops = slg_pct_diff > 0 \
                                    and ops_pct_diff > 0  \
                                    and abs(obp_pct_diff) < 0.04 \
                                    and abs(slg_pct_diff) > 0.12 \
                                    and has_1b_values

        # ------------------------------
        # ADJUST CHARTS THAT ARE UNDER IN OBP BUT CLOSE IN SLG AND OPS
        # ------------------------------
        is_increase_adjustment = is_under_in_slg_and_ops and self.is_hitter
        is_decrease_adjustment = is_over_in_slg_and_ops and self.is_pitcher
        if is_increase_adjustment or is_decrease_adjustment:
            self.__adjust_slg(is_increase=is_increase_adjustment, slg_pct_diff=slg_pct_diff)

        # ------------------------------
        # 2002 POST 20 ADJUSTMENTS
        # ------------------------------
        if self.set == '2002':
            self.__apply_2002_post_20_adjustments()

        return

    def calc_chart_category_values_from_rate_stats(self, category:ChartCategory, current_chart_index:int, max_values:float, min_values:float=None) -> tuple[Union[float | int], int, bool]:
        """Get chart category values based on rate stats

        Args:
            category: Chart category to get values for.
            current_chart_index: Current index in chart.
            max_values: Max number of values to fill.
            min_values: Min number of values to fill.

        Returns:
            Float of chart category values.
            Number of chart results
        """

        real_results_per_400_pa = self.stats_per_400_pa.get(f'{category.value.lower()}_per_400_pa', 0)
        opponent_values = self.opponent.num_values(category)
        chart_values = (real_results_per_400_pa - (self.opponent_advantages_per_20 * opponent_values)) / self.my_advantages_per_20
        
        # LIMIT RESULTS TO CHART CATEGORY SLOT LIMIT
        was_limited = chart_values > max_values
        chart_values = max( min(chart_values, max_values) , min_values if min_values else min(chart_values, max_values))
        
        # IF ITS A BOOKEND CATEGORY (EX: FB) FILL WITH REMAINING VALUES
        if category == ChartCategory.FB:
            chart_values = max(max_values, chart_values)

        chart_values_rounded, results = self.values_and_results(value=chart_values, category=category, current_chart_index=current_chart_index)

        return chart_values_rounded, results, was_limited

    def __single_plus_values_and_results(self, total_1B_values:int, current_chart_index:int) -> tuple[Union[int, float], int]:
        """Fill 1B+ values on chart.

        Args:
          total_1B_values: Total 1B and 1B+ slots.
          current_chart_index: Current index in chart.

        Returns:
          Number of 1B+ chart slots.
        """

        # PITCHER HAS NO 1B+
        if self.is_pitcher:
            return 0

        # DIVIDE STOLEN BASES PER 400 PA BY A SCALER BASED ON ONBASE #
        sb = self.stats_per_400_pa.get('sb_per_400_pa', 0)
        min_onbase = 7 if self.is_expanded else 4
        max_onbase = 16 if self.is_expanded else 12
        onbase_range = ValueRange(min=min_onbase, max=max_onbase)
        min_denominator = self.hitter_single_plus_denominator_minimum
        max_denominator = self.hitter_single_plus_denominator_maximum
        onbase_pctile = onbase_range.percentile(value=self.command)
        
        # POPULATE 1B+ RESULTS
        single_plus_denominator = min_denominator + ( (max_denominator-min_denominator) * onbase_pctile )
        single_plus_values_raw = min(math.trunc(sb / single_plus_denominator), total_1B_values)
        
        # IMPLEMENT LINEAR DECAY FOR 1B+ VALUES OVER LIMIT
        single_plus_values_raw = self.__apply_linear_decay(value=single_plus_values_raw, category=ChartCategory._1B_PLUS)
        
        # UPDATE VALUES AND RESULTS
        single_plus_values_rounded, single_plus_results = self.values_and_results(value=single_plus_values_raw, category=ChartCategory._1B_PLUS, current_chart_index=current_chart_index)

        return single_plus_values_rounded, single_plus_results

    def values_and_results(self, value:float, category:ChartCategory = None, current_chart_index:int = None) -> tuple[float, int]:
        """Round value to nearest slot worth. Return rounded value and number of slots filled.

        Args:
            value: Value to round.
            category: Chart category to round for.
            current_chart_index: Current index in chart. Will effect rounding

        Returns:
            Tuple of rounded value and number of slots filled.
        """

        # APPLY DECAY RATE IF APPLICABLE
        if category is not None:
            value *= category.value_multiplier(set=self.set)
            value = self.__apply_linear_decay(value=value, category=category)

        # ROUND TO NEAREST SLOT WORTH
        rounding_cutoff = category.rounding_cutoff(is_pitcher=self.is_pitcher, set=self.set) if category else 0.5
        raw_value = max( self.__round_to_nearest_slot_value(value, rounding_cutoff) , 0)
        raw_results = int(round(raw_value / self.sub_21_per_slot_worth))

        # SKIP ROUNDING IF CATEGORY IS NONE (EX: OUTS) OR CHART IS NOT EXPANDED
        if category is None or not self.is_expanded:
            return raw_value, raw_results
        
        # ROUND TO NEAREST SLOT WORTH
        if category.is_out or current_chart_index is None:
            return raw_value, raw_results
        
        # ITERATE THROUGH EACH SLOT WORTH RESULT AND ROUND
        end = 1 if category.is_filled_in_desc_order else self.total_possible_slots
        iterator = -1 if category.is_filled_in_desc_order else 1
        values_total = 0
        num_results = 0
        diff_last_index = max(value, 0)
        for i in range(current_chart_index, end, iterator):
            slot_value = self.__slot_value(index=i)
            new_potential_total_value = values_total + slot_value
            new_potential_value_vs_original = abs(new_potential_total_value - value)
            is_out_of_bounds = category == ChartCategory.HR and i >= 27
            if new_potential_value_vs_original > diff_last_index and not is_out_of_bounds:
                break
            values_total = new_potential_total_value
            num_results += 1
            diff_last_index = new_potential_value_vs_original
        
        return values_total, num_results

    def generate_range_strings(self) -> None:
        """Use the current chart results list to generate string representations for the chart.

        Args:
          None
          
        Returns:
          None - Stores final dictionary in self.
        """

        if len(self.values) == 0 or len(self.ranges) > 0:
            return

        # CONVERT LIST TO DICT OF COUNTS
        # EX: [SO, SO, SO, GB, GB, FB, BB, 1B, 2B, HR] -> {SO: 3, GB: 2, FB: 1, BB: 1, 1B: 1, 2B: 1, HR: 1}
        chart_values = {}
        results_list = list(self.results.values())
        result_list = results_list if self.is_expanded else results_list[:20]
        for result in result_list:
            chart_values[result] = chart_values.get(result, 0) + 1
        
        # ITERATE THROUGH CHART CATEGORIES AND GENERATE RANGES
        current_chart_index = 1
        chart_ranges: dict[ChartCategory, str] = {}
        for category in self.categories_list:
            category_results = chart_values.get(category, 0)
            range_end = current_chart_index + category_results - 1
                
            if category == ChartCategory.HR and self.is_expanded:
                # ADD PLUS AFTER HR
                range = '{}+'.format(str(current_chart_index))
            elif category_results == 0:
                # EMPTY RANGE
                range = '—'
            elif category_results == 1:
                # RANGE IS CURRENT INDEX
                range = str(current_chart_index)
                current_chart_index += 1
            else:
                # MULTIPLE RESULTS
                range_start = current_chart_index
                range = '{}–{}'.format(range_start,range_end)
                current_chart_index = range_end + 1

            chart_ranges[category] = range
        
        self.ranges = chart_ranges
    
    def update_outs_from_values(self) -> None:
        """Update outs based on values"""
        out_value_list = [v for k,v in self.values.items() if k.is_out]
        self.outs = sum(out_value_list) if len(out_value_list) > 0 else 0

    def __adjust_slg(self, is_increase:bool = True, slg_pct_diff: float = 0.0) -> None:
        """Increase SLG for the category with the biggest difference between projected and real stats per 400 PA
        
        Args:
            is_increase: If True, increase SLG. If False, decrease SLG.
            slg_pct_diff: Difference between projected and real stats per 400 PA.

        Returns:
            None, adjusts self.values and self.results
        """

        category_pct_diffs: dict[ChartCategory, float] = {}
        slg_categories = [ChartCategory._2B, ChartCategory._3B, ChartCategory.HR] if is_increase else [ChartCategory._2B, ChartCategory.HR]
        for slg_cat in slg_categories:
            small_sample_cutoff = 4.0 if slg_cat == ChartCategory._3B else 5
            if self.stats_per_400_pa.get(slg_cat.value.lower() + '_per_400_pa', 0) < small_sample_cutoff: continue
            pct_diff = self.__stat_projected_vs_real_pct_diff(slg_cat.value.lower() + '_per_400_pa')
            decrease_multipler = 1 if is_increase else -1
            if (pct_diff * decrease_multipler) <= -0.01: category_pct_diffs[slg_cat] = pct_diff

        # CHECK: IF NO CATEGORIES TO ADJUST, SKIP ADJUSTMENTS
        if len(category_pct_diffs) == 0:
            return
        
        # GET CATEGORY WITH BIGGEST DIFFERENCE
        category_biggest_diff = min(category_pct_diffs, key=category_pct_diffs.get) if is_increase else max(category_pct_diffs, key=category_pct_diffs.get)
        max_index = 21 if self.total_possible_slots > 20 and self.results[21] in [ChartCategory.HR, ChartCategory._2B] else 20
        slots_category_biggest_diff = [index for index, cat in self.results.items() if cat == category_biggest_diff and index <= max_index]
        
        # HANDLE CASES WHERE PLAYER HAS 0 SLOTS FOR CATEGORY
        if len(slots_category_biggest_diff) == 0:
            # FIND NEXT SLOT AFTER LAST SLOT FOR CATEGORY
            slg_categories_after = slg_categories[slg_categories.index(category_biggest_diff)+1:]
            for slg_cat in slg_categories_after:
                indexes_for_slg_cat = [index for index, cat in self.results.items() if cat == slg_cat and index <= max_index]
                if len(indexes_for_slg_cat) > 0:
                    slots_category_biggest_diff = indexes_for_slg_cat
                    break

        min_slot_index_category_biggest_diff = min(slots_category_biggest_diff) if len(slots_category_biggest_diff) > 0 else None
        if not min_slot_index_category_biggest_diff:
            return

        # CHANGE VALUES FOR 1B AND ADJUST CATEGORY
        self.values[ChartCategory._1B] -= self.sub_21_per_slot_worth * (1 if is_increase else -1)
        self.values[category_biggest_diff] += self.sub_21_per_slot_worth * (1 if is_increase else -1)
        
        # UPDATE RESULTS DICTIONARY
        # EX: {.. 15: '1B', 16: '2B', ..} -> {.. 15: '2B', 16: '2B', ..}
        slot_indexes_1B = [index for index, cat in self.results.items() if cat == ChartCategory._1B and index <= 20]
        max_slot_index_1b = max(slot_indexes_1B) if len(slot_indexes_1B) > 0 else None
        if max_slot_index_1b:
            updated_results: dict[int, ChartCategory] = {}
            for index in self.results.keys():
                if is_increase:
                    if index >= max_slot_index_1b and index < min_slot_index_category_biggest_diff:
                        new_slot_category = category_biggest_diff if index == (min_slot_index_category_biggest_diff - 1) else self.results[index + 1]
                        updated_results[index] = new_slot_category
                else:
                    if index > max_slot_index_1b and index <= min_slot_index_category_biggest_diff:
                        new_slot_category = ChartCategory._1B if index == (max_slot_index_1b + 1) else self.results[index - 1]
                        updated_results[index] = new_slot_category
            self.results.update(updated_results)
            self.chart_categories_adjusted += [category_biggest_diff]

    def __apply_linear_decay(self, value: float | int, category: ChartCategory) -> None:
        """Apply linear decay to chart values"""
        decay_rate_and_start = category.decay_rate_and_start(set=self.set, is_pitcher=self.is_pitcher)
        if decay_rate_and_start is None:
            return value
        
        decay_rate, decay_start = decay_rate_and_start
        if value > decay_start:
            return decay_start + ((value - decay_start) * decay_rate)

        return value

    def __custom_round(self, number:float, multiple:float=1, cutoff:float=0.5):
        """Rounds a number to the nearest multiple of a specified value, based on a custom cutoff.
        
        Parameters:
            number: The number to round.
            multiple: The value to which the number is rounded (default is 1).
            cutoff: The cutoff point at which the rounding occurs (default is 0.5).
        
        Returns:
            Rounded number to the nearest specified multiple.
        """
        # SCALE THE NUMBER TO ROUND IT TO THE NEAREST MULTIPLE
        scaled_number = number / multiple
        
        # GET THE DECIMAL PART OF THE SCALED NUMBER
        decimal_part = scaled_number - int(scaled_number)
        
        # APPLY CUSTOM ROUNDING LOGIC
        if decimal_part >= cutoff:
            return (int(scaled_number) + 1) * multiple
        else:
            return int(scaled_number) * multiple

    def __apply_2002_post_20_adjustments(self) -> None:
        """Adjust chart values for 2002 set after 20
        
        2002 is unique in that it wills all slots from slot 21 - HR Start with whatever the last value was.
        Only exception is pitchers with 20 outs (rare).
        """

        # GET VALUE AT 20
        last_value = self.results.get(20, None)
        if last_value.is_out:
            possible_fill_results = [ChartCategory.BB, ChartCategory._1B, ChartCategory._2B]
            diff_vs_real_dict = { c: self.__stat_projected_vs_real_pct_diff(c.value.lower() + '_per_400_pa') for c in possible_fill_results }
            last_value = min(diff_vs_real_dict, key=diff_vs_real_dict.get)
            
        if last_value == ChartCategory.HR:
            # IF LAST VALUE IS HR, FILL 21-30 WITH HR
            for i in range(21, 31):
                self.results[i] = ChartCategory.HR
                self.values[ChartCategory.HR] = self.values.get(ChartCategory.HR, 0) + self.__slot_value(i)
            return
        
        # FILL 21+ SLOTS, STARTING WITH HR
        # ONLY COUNT THE HR SLOT FOR ACTUAL VALUES
        starting_point = 32.45 if self.is_pitcher else 27.67
        decay_rate = 0.8415 if self.is_pitcher else 0.7835
        hr_start = min( round(starting_point - (decay_rate * self.stats_per_400_pa.get('hr_per_400_pa', 0))), 27 )
        for i in range(21, 31):
            fill_category = ChartCategory.HR if i >= hr_start else last_value
            self.results[i] = fill_category
            self.values[fill_category] = self.values.get(fill_category, 0) + self.__slot_value(i)

    # ---------------------------------------
    # ACCURACY
    # ---------------------------------------

    @property
    def accuracy_stat_weights(self) -> dict[Stat, float]:
        """Get stat weights for accuracy calculation"""
        match self.set:
            case '2000':
                if self.is_hitter:
                    return {
                        Stat.OBP: 0.75,
                        Stat.SLG: 0.25,
                    }
                else:
                    return {
                        Stat.OBP: 0.60,
                        Stat.SLG: 0.20,
                        Stat.OPS: 0.20,
                    }
            case '2001' | 'CLASSIC':
                if self.is_hitter:
                    return {
                        Stat.OBP: 0.60,
                        Stat.SLG: 0.20,
                        Stat.OPS: 0.20,
                    }
                else:
                    return {
                        Stat.OBP: 0.70,
                        Stat.SLG: 0.30,
                    }
            case '2002':
                if self.is_hitter:
                    return {
                        Stat.OBP: 0.75,
                        Stat.SLG: 0.25,
                    }
                else:
                    return {
                        Stat.OBP: 0.50,
                        Stat.SLG: 0.20,
                        Stat.OPS: 0.30,
                    }
            case '2003':
                if self.is_hitter:
                    return {
                        Stat.COMMAND: 0.50,
                        Stat.OBP: 0.25,
                        Stat.SLG: 0.15,
                        Stat.OPS: 0.10,
                    }
                else:
                    return {
                        Stat.COMMAND: 0.30,
                        Stat.OBP: 0.30,
                        Stat.SLG: 0.20,
                        Stat.OPS: 0.20,
                    }
            case '2004':
                if self.is_hitter:
                    return {
                        Stat.COMMAND: 0.50,
                        Stat.OBP: 0.25,
                        Stat.SLG: 0.15,
                        Stat.OPS: 0.10,
                    }
                else:
                    return {
                        Stat.COMMAND: 0.30,
                        Stat.OBP: 0.30,
                        Stat.SLG: 0.20,
                        Stat.OPS: 0.20,
                    }
            case '2005' | 'EXPANDED':
                if self.is_hitter:
                    return {
                        Stat.COMMAND: 0.50,
                        Stat.OBP: 0.25,
                        Stat.SLG: 0.15,
                        Stat.OPS: 0.10,
                    }
                else:
                    return {
                        Stat.COMMAND: 0.30,
                        Stat.OBP: 0.30,
                        Stat.SLG: 0.20,
                        Stat.OPS: 0.20,
                    }

    def generate_accuracy_rating(self) -> None:
        """Calculate accuracy of chart based on accuracy weights. Store to self."""
        
        # CHECK ACCURACY COMPARED TO REAL LIFE
        in_game_stats_per_400_pa = self.projected_stats_per_400_pa
        weights = self.accuracy_stat_weights
        actuals_dict = dict( ChainMap({'command': self.command_estimated}, self.stats_per_400_pa) )
        measurements_dict = dict( ChainMap({'command': self.command}, in_game_stats_per_400_pa) )
        self.__calculate_accuracy_breakdown(
            actuals_dict=actuals_dict,
            measurements_dict=measurements_dict,
            weights=weights,
        )

        if self.does_set_ignore_outlier_adjustments:
            self.is_command_out_anomaly = self.is_chart_an_outlier
            return

        # REDUCE ACCURACY WHEN OUTS ARE ABOVE SOFT OUTLIER MAX AND COMMAND ABOVE SOFT OUTLIER MAX
        out_min, out_max, command_outlier_lower_bound, command_outlier_upper_bound = self.outlier_cutoffs
        outs = self.outs_full

        # ADJUST HIGH COMMAND HIGH OUTS
        if self.is_high_command_high_outs:
            self.command_out_accuracy_weight = 0.925

        # USE LINEAR DECAY TO REDUCE ACCURACY FOR OUTLIERS
        if self.is_outside_out_bounds and not self.is_elite_command_out_chart and not self.is_high_command_high_outs:

            # ADJUST DECAY RATES
            decay_rate = 0.0275
            if self.command <= (command_outlier_upper_bound - 2) and outs < out_min: # ADJUST LOWER COMMAND LOWER OUTS (EX: 8 OB 2 OUTS)
                decay_rate *= 1.60
            elif self.command >= (command_outlier_lower_bound - 2) and outs > out_max: # ADJUST LOWER COMMAND LOWER OUTS (EX: 8 OB 2 OUTS)
                decay_rate *= 1.25
            elif self.is_classic and outs > out_max: # ADJUST FOR CLASSIC SETS WITH HIGH COMMAND + OUTS (EX: 13 OB 5 OUTS)
                decay_rate *= 1.25
            
            out_comp = out_max if outs > out_max else out_min
            self.command_out_accuracy_weight = min( 1.020 - (decay_rate * abs(outs - out_comp)), 1.0 )
        
        # APPLY WEIGHTS
        # USED TO NORMALIZE CHARTS TO MATCH WOTC BUT ALSO PROVIDE FLEXIBILITY FOR OUTLIERS
        self.accuracy *= self.command_out_accuracy_weight
        self.accuracy *= self.command_accuracy_weight
        self.is_command_out_anomaly = self.is_chart_an_outlier

    def __calculate_accuracy_breakdown(self, actuals_dict:dict, measurements_dict:dict, weights:dict[Stat, float]={}) -> None:
        """Compare two dictionaries of numbers to get overall difference

        Args:
          actuals_dict: First Dictionary. Use this dict to get keys to compare.
          measurements_dict: Second Dictionary.
          weights: X times to count certain category (ex: 25% for command)

        Returns:
          Float for overall accuracy,
          Dictionary with breakdown per stat
        """

        # POPULATE ACCURACY BREAKDOWN
        for stat, weight in weights.items():
            
            actual = actuals_dict.get(stat.value, None)
            comparison = measurements_dict.get(stat.value, None)
            
            # SKIP IF NOT INCLUDED IN ACCURACY
            if actual is None or comparison is None:
                continue

            # CREATE ACCURACY BREAKDOWN OBJECT
            self.accuracy_breakdown[stat] = ChartAccuracyBreakdown(
                stat = stat,
                actual=actual,
                comparison=comparison,
                weight=weight,
                is_pitcher=self.is_pitcher,
            )

        # 2003+ ADJUST COMMAND ACCURACY FOR OUTLIERS THAT ARE ACCURATE
        command_chart_accuracy = self.accuracy_breakdown.get(Stat.COMMAND, None)
        if self.does_set_ignore_outlier_adjustments and command_chart_accuracy and self.is_chart_an_outlier:
            accuracy_command = command_chart_accuracy.accuracy
            non_command_breakdowns = [breakdown for breakdown in self.accuracy_breakdown.values() if breakdown.stat != Stat.COMMAND]
            accuracy_non_command = ( sum([breakdown.weighted_accuracy for breakdown in non_command_breakdowns]) / sum([breakdown.weight for breakdown in non_command_breakdowns]) ) if len(non_command_breakdowns) > 0 else 0
            accuracy_cutoff = 0.99 if self.is_hitter else 0.98
            accuracy_command_minimum = 0.90 if self.is_hitter else 0.30
            if accuracy_non_command > accuracy_cutoff and accuracy_command < accuracy_cutoff and accuracy_command > accuracy_command_minimum:
                command_chart_accuracy.adjustment_pct = round(accuracy_cutoff / accuracy_command, 4)
                command_chart_accuracy.calculate_accuracy_attributes()
                self.accuracy_breakdown[Stat.COMMAND] = command_chart_accuracy
                self.command_out_accuracy_weight = command_chart_accuracy.adjustment_pct
                self.is_command_out_anomaly = True
                
        # CALCULATE OVERALL ACCURACY
        overall_accuracy = sum([breakdown.weighted_accuracy for breakdown in self.accuracy_breakdown.values()]) if len(self.accuracy_breakdown) > 0 else 0
        self.accuracy = overall_accuracy
        return

    def __pct_diff(self, value_1, value_2) -> float:
        """Calculate percentage difference between two values"""
        return (value_1 - value_2) / ((value_1 + value_2) / 2)

    def __stat_projected_vs_real_pct_diff(self, stat:str) -> float:
        """Calculate projected vs real stat"""
        real_stat = self.stats_per_400_pa.get(stat, 0)
        projected_stat = self.projected_stats_per_400_pa.get(stat, 0)
        return self.__pct_diff(projected_stat, real_stat)

    @property
    def accuracy_breakdown_str(self) -> str:
        """Get accuracy breakdown string"""
        
        # NO BREAKDOWN
        if len(self.accuracy_breakdown) == 0:
            return 'No Breakdown Available'
        
        # CREATE BREAKDOWN STRINGS
        return "  ".join([breakdown.summary_str for breakdown in self.accuracy_breakdown.values()])

    @property
    def outlier_cutoffs(self) -> tuple[float, float, float, float]:
        """Get outlier cutoffs for chart. Based on Command and Onbase combination being outside the norm."""

        if self.is_pitcher:

            # DEFAULTS, NOTE COULD BE CHANGED BY SPECIAL CASES BELOW
            match self.set:
                case '2000' | '2001' | 'CLASSIC':
                    out_min = 15
                    out_max = 18
                case '2002':
                    out_min = 14
                    out_max = 19
                case '2003':
                    out_min = 15
                    out_max = 16
                case '2004' | '2005' | 'EXPANDED':
                    out_min = 15
                    out_max = 17
                
            command_outlier_upper_bound = 6 if self.is_expanded else 6
            command_outlier_lower_bound = 1 if self.is_expanded else 1

            # UPDATE FOR SPECIAL CASES
            if self.is_classic and self.command >= 6: out_min, out_max = 15, 18
            if self.is_classic and self.command == 0: out_min, out_max = 15, 17.5

        else:
            out_min = 5 if self.is_expanded else 3
            out_max = 7 if self.is_expanded else 5

            # UPDATE FOR SPECIAL CASES
            if self.is_classic and self.command > 10: out_min, out_max = 2, 3
            if self.is_classic and self.command < 8: out_min, out_max = 3, 6

            command_outlier_upper_bound = 14 if self.is_expanded else 11
            command_outlier_lower_bound = 9 if self.is_expanded else 5

        return out_min, out_max, command_outlier_lower_bound, command_outlier_upper_bound
    
    @property
    def is_outside_out_bounds(self) -> bool:
        """Check if chart is outside out bounds"""
        out_min, out_max, _, _ = self.outlier_cutoffs
        outs = self.outs / self.sub_21_per_slot_worth
        return outs < out_min or outs > out_max
    
    @property
    def is_elite_command_out_chart(self) -> bool:
        """Check if chart is an elite command out chart"""
        out_min, out_max, _, command_outlier_upper_bound = self.outlier_cutoffs
        return self.command >= command_outlier_upper_bound and (self.outs_full < out_min if self.is_hitter else self.outs_full > out_max)

    @property
    def is_high_command_high_outs(self) -> bool:
        """Check if chart is high command high outs"""
        command_soft_cap = 11 if self.is_expanded else 8
        _, out_max, _, command_outlier_upper_bound = self.outlier_cutoffs
        is_classic_and_high_command_outs = self.is_classic and self.outs_full > 4 and self.command > 10
        is_high_command_high_outs = (self.outs_full > out_max and self.command > command_soft_cap) or is_classic_and_high_command_outs
        return is_high_command_high_outs

    @property
    def is_chart_an_outlier(self) -> bool:
        """Check if chart is an outlier"""
        return self.is_elite_command_out_chart or self.is_outside_out_bounds

    # ---------------------------------------
    # ADVANTAGES
    # ---------------------------------------

    @property
    def my_advantages_per_20(self) -> int | float:
        hitter_advantages = (self.opponent.command - self.command) * (1 if self.is_pitcher else -1)
        if not self.is_pitcher:
            return hitter_advantages
        return 20 - hitter_advantages
    
    @property
    def opponent_advantages_per_20(self) -> int | float:
        return 20 - self.my_advantages_per_20

    # ---------------------------------------
    # RESULTS
    # ---------------------------------------

    def num_results_projected(self, category:ChartCategory) -> float:
        """Project real life results for a given category based on chart values.
        
        Args:
            category: ChartCategory to results for
        
        Returns:
            Number of projected results for the category.
        """

        results_per_400_pa = self.stats_per_400_pa.get(category, 0)
        if results_per_400_pa == 0:
            return 0
        opponent_values = self.opponent.num_values(category)
        results_from_opponent_chart = self.opponent_advantages_per_20 * opponent_values
        remaining_results = results_per_400_pa - results_from_opponent_chart
        if remaining_results < 0:
            return 0
        chart_results = remaining_results / self.my_advantages_per_20

        return chart_results

    def __slot_value(self, index:int) -> float:
        """Determine how many slots a result over 20 is valued at"""
        return self.slot_values.get(index, 0)
    
    # ---------------------------------------
    # REAL STATS
    # ---------------------------------------

    @property
    def projected_stats_per_400_pa(self) -> dict:
        """Predict real stats given Showdown in game chart.

        Returns:
          Dict with stats per 400 Plate Appearances.
        """

        # ----- COUNTING STATS -----

        strikeouts_per_400_pa = self.projected_stats_for_category(ChartCategory.SO)
        walks_per_400_pa = self.projected_stats_for_category(ChartCategory.BB)
        singles_per_400_pa = self.projected_stats_for_category(ChartCategory._1B) + self.projected_stats_for_category(ChartCategory._1B_PLUS)
        doubles_per_400_pa = self.projected_stats_for_category(ChartCategory._2B)
        triples_per_400_pa = self.projected_stats_for_category(ChartCategory._3B)
        home_runs_per_400_pa = self.projected_stats_for_category(ChartCategory.HR)
        popups_per_400_pa = self.projected_stats_for_category(ChartCategory.PU)
        groundouts_per_400_pa = self.projected_stats_for_category(ChartCategory.GB)
        fly_ball_outs_per_400_pa = self.projected_stats_for_category(ChartCategory.FB)
        hits_per_400_pa = singles_per_400_pa \
                            + doubles_per_400_pa \
                            + triples_per_400_pa \
                            + home_runs_per_400_pa
        
        # ----- SLASH LINE -----

        # DEFINE AT BATS
        # REMOVE REAL LIFE SACRIFICE FLIES FROM FLY BALL OUTS
        sacrifice_hits_per_400_pa = self.stats_per_400_pa.get('sh_per_400_pa', 0)
        sacrifice_flies_per_400_pa = self.stats_per_400_pa.get('sf_per_400_pa', 0)
        ibb_per_400_pa = self.stats_per_400_pa.get('ibb_per_400_pa', 0)
        at_bats = (400.0 - walks_per_400_pa - sacrifice_hits_per_400_pa - sacrifice_flies_per_400_pa)

        # BA
        batting_avg = hits_per_400_pa / at_bats

        # OBP
        obp = (hits_per_400_pa + walks_per_400_pa) / (at_bats + walks_per_400_pa + sacrifice_flies_per_400_pa)

        # SLG
        slugging_pct = self.__slugging_pct(ab=at_bats,
                                           singles=singles_per_400_pa,
                                           doubles=doubles_per_400_pa,
                                           triples=triples_per_400_pa,
                                           homers=home_runs_per_400_pa)
        # GROUP ESTIMATIONS IN DICTIONARY
        results_per_400_pa = {
            'so_per_400_pa': strikeouts_per_400_pa,
            'pu_per_400_pa': popups_per_400_pa,
            'gb_per_400_pa': groundouts_per_400_pa,
            'fb_per_400_pa': fly_ball_outs_per_400_pa,
            'bb_per_400_pa': walks_per_400_pa,
            '1b_per_400_pa': singles_per_400_pa,
            '2b_per_400_pa': doubles_per_400_pa,
            '3b_per_400_pa': triples_per_400_pa,
            'hr_per_400_pa': home_runs_per_400_pa,
            'h_per_400_pa': hits_per_400_pa,
            'sh_per_400_pa': sacrifice_hits_per_400_pa,
            'sf_per_400_pa': sacrifice_flies_per_400_pa,
            'ibb_per_400_pa': ibb_per_400_pa,
            'ab_per_400_pa': at_bats,
            'batting_avg': batting_avg,
            'onbase_perc': obp,
            'slugging_perc': slugging_pct,
            'onbase_plus_slugging': obp + slugging_pct,
            'g': self.stats_per_400_pa.get('G', 0),
        }

        return results_per_400_pa

    def projected_stats_for_category(self, category:ChartCategory, pa: int = 400) -> int | float:

        my_results = self.num_values(category)
        opponent_results = self.opponent.num_values(category)
        pa_multiplier = pa / 400
        total_projected = ( (my_results * self.my_advantages_per_20) + (opponent_results * self.opponent_advantages_per_20) ) * pa_multiplier

        return total_projected

    def __slugging_pct(self, ab:float, singles:float, doubles:float, triples:float, homers:float)  -> float:
        """ Calculate Slugging Pct"""
        return (singles + (2 * doubles) + (3 * triples) + (4 * homers)) / ab
    
    @property
    def is_overestimating_obp(self) -> bool:
        """Check if chart is overestimating OBP"""
        return self.stats_per_400_pa.get('onbase_perc', 0) > self.projected_stats_per_400_pa.get('onbase_perc', 0)
    
    # ---------------------------------------
    # RANGES
    # ---------------------------------------

    @property
    def ranges_list(self) -> list[str]:
        """List of ranges ordered as strings"""
        return [self.ranges[category] for category in self.categories_list]
    
    # ---------------------------------------
    # CONVERT FROM WOTC
    # ---------------------------------------

    @property
    def __estimated_command_x_and_y_const(self) -> tuple[float, float]:
        match self.set:
            case '2003':
                match self.player_subtype:
                    case 'starting_pitcher':
                        x =  -43.65
                        y_int = 17.03
                    case 'relief_pitcher':
                        x =  -43.24
                        y_int = 16.78
                    case 'position_player':
                        x = 36.78
                        y_int = -2.58
            case '2004': 
                match self.player_subtype:
                    case 'starting_pitcher':
                        x =  -42.49
                        y_int = 16.70
                    case 'relief_pitcher':
                        x =  -42.49
                        y_int = 16.70
                    case 'position_player':
                        x = 36.20
                        y_int = -2.3
            case '2005' | 'EXPANDED': 
                match self.player_subtype:
                    case 'starting_pitcher':
                        x =  -42.49
                        y_int = 16.70
                    case 'relief_pitcher':
                        x =  -42.49
                        y_int = 16.70
                    case 'position_player':
                        x = 35.00
                        y_int = -1.90
        return x, y_int

    def calculate_estimated_command(self, mlb_avgs_df: pd.DataFrame = None) -> float:
        """
        Estimated command based on wotc formulas and real OBP. Store in self. 
        Only applies to 2003+ sets.
        """

        def estimate_command_from_wotc(x:float, y_int:float, obp:float) -> float:
            min_command, max_command = (1 if self.is_pitcher else 7), (6 if self.is_pitcher else 16)
            command = obp * x + y_int
            return max(min( round(command, 2), max_command ), min_command)

        # ONLY APPLY TO 2003+ SETS
        if self.set not in ['2003', '2004', '2005', 'EXPANDED']:
            return None
        
        # LOAD MLB AVGS
        if mlb_avgs_df is None:
            mlb_avgs_df = self.load_mlb_league_avg_df()

        # ADJUST FORMULA BASED ON ERA
        # START BY GETTING AVGS FOR WOTC SET YEAR
        mlb_avgs_wotc_set = self.__avg_mlb_stats_dict_for_years(year_list=[self.set_year], mlb_avgs_df=mlb_avgs_df)
        x_factor, y_int = self.__estimated_command_x_and_y_const
        wotc_set_year_obp = mlb_avgs_wotc_set.get('OBP', 0)
        command_for_avg_wotc_obp = estimate_command_from_wotc(x_factor, y_int, wotc_set_year_obp)
                
        # GET AVG OBP IN PLAYER'S ERA
        years = self.era_year_list
        mlb_avgs = self.__avg_mlb_stats_dict_for_years(year_list=years, mlb_avgs_df=mlb_avgs_df)
        player_year_avg_obp = mlb_avgs.get('OBP', 0)
        if player_year_avg_obp == wotc_set_year_obp:
            return command_for_avg_wotc_obp

        # THEN ADJUST THE X_FACTOR VARIABLE TO PLAYER'S YEAR
        wotc_set_adjustment_factor = ( -1 * self.wotc_set_adjustment_factor(for_hitter_chart= not self.is_hitter) / 2 ) # OPPOSITE AS ADJUSTMENT IS FOR BASELINE
        player_year_avg_obp *= (1 + wotc_set_adjustment_factor)
        adjusted_x_factor = round( (command_for_avg_wotc_obp - y_int) / player_year_avg_obp, 2 )
        real_obp = self.stats_per_400_pa.get('onbase_perc', 0)
        command_adjusted_to_era = estimate_command_from_wotc(adjusted_x_factor, y_int, real_obp)
        
        return command_adjusted_to_era

    def generate_values_and_results_from_wotc_data(self, results_list:list[ChartCategory]) -> None:
        """Convert WOTC data to chart values and results"""

        # CONVERT WOTC DATA TO CHART DATA
        chart_values = {}
        for index, category in enumerate(results_list, start=1):
            self.results[index] = category
            current_values_for_category = chart_values.get(category, 0)
            slot_value = self.__slot_value(index=index)
            current_values_for_category += slot_value
            chart_values[category] = current_values_for_category
        
        self.values = chart_values

        # UPDATE OUTS IF EXPANDED
        if self.is_expanded:
            self.update_outs_from_values()

    # ---------------------------------------
    # ERA ADJUSTMENT
    # ---------------------------------------

    def __avg_mlb_stats_dict_for_years(self, year_list:list[int], mlb_avgs_df:pd.DataFrame = None) -> dict:
        """Get average MLB stats for a list of years"""
        if mlb_avgs_df is None: mlb_avgs_df = self.load_mlb_league_avg_df()
        mlb_avgs_df = mlb_avgs_df[mlb_avgs_df['Year'].isin(year_list)]
        mlb_avgs = mlb_avgs_df.mean().to_dict()
        return mlb_avgs

    def load_mlb_league_avg_df(self) -> pd.DataFrame:
        """Load MLB Averages for chart"""
        mlb_avgs_path = os.path.join(Path(os.path.dirname(__file__)).parent, 'data', 'mlb_averages.csv')
        mlb_avgs_df = pd.read_csv(mlb_avgs_path)
        for col in mlb_avgs_df.columns:
            if col != 'Year':
                mlb_avgs_df[col] = mlb_avgs_df[col].astype(float)
        return mlb_avgs_df

    def wotc_set_adjustment_factor(self, for_hitter_chart:bool) -> float:
        """Get adjustment factor for WOTC set"""
        
        # ADJUSTMENT_FOR_ORIGINAL_SET ACCOUNTS FOR THE FACT THAT THE ORIGINAL SET WONT SIMULATE PERFECTLY
        # EXAMPLES: 
        #   2001 SET UNDERRATES PITCHING, SO WE UNDERRATE PITCHER STATS TO MATCH
        #   2005 SET OVERRATES HITTING, SO WE ADJUST AVERAGE PITCHER OPPONENTS TO BE BETTER
        # SHOWN AS A PERCENTAGE TO APPLY. > 0 MEANS A WORSE OPPONENT
        match self.set:
            case '2000':
                return 0.0
            case '2001' | 'CLASSIC': 
                return -0.075 if for_hitter_chart else 0.00
            case '2002' | '2003' | '2004' | '2005' | 'EXPANDED': 
                return -0.10 if for_hitter_chart else -0.01

        return 0
    
    def adjust_for_era(self, era:str, year_list:list[int]) -> None:
        """Adjust chart values for era. Used for baseline charts.
        
        Args:
            era: Era to adjust for.
            year_list: List of years to use for MLB Averages.

        Returns:
            None
        """

        def mlb_pct_change_between_eras(stat: str, diff_reduction_multiplier:float = 1.0, default_value:float = None, ignore_pitcher_flip:bool = False, wotc_set_adjustment_factor:float = 0.0) -> float:
            stat_during_wotc = mlb_avgs_wotc_set.get(stat, None) * (1 + wotc_set_adjustment_factor)
            stat_to_adjust_to = mlb_avgs.get(stat, default_value)
            if np.isnan(stat_to_adjust_to):
                stat_to_adjust_to = default_value
            stat_avg = (stat_to_adjust_to + stat_during_wotc) / 2
            diff_reduced = (stat_to_adjust_to - stat_during_wotc) * diff_reduction_multiplier
            pct_change = ( diff_reduced / stat_avg )

            # REVERSE PCT CHANGE FOR PITCHERS
            if self.is_pitcher and not ignore_pitcher_flip:
                pct_change = -1 * pct_change

            return pct_change
        
        # DONT ADJUST IF ERA IS THE SAME
        if len(year_list) == 1:
            if self.set_year == year_list[0]:
                return
        
        mlb_avgs_df = self.load_mlb_league_avg_df()

        # FILTER FOR ORIGINAL YEAR
        mlb_avgs_wotc_set = self.__avg_mlb_stats_dict_for_years(year_list=[self.set_year], mlb_avgs_df=mlb_avgs_df)

        # FILTER YEAR COLUMN IN YEAR LIST
        mlb_avgs = self.__avg_mlb_stats_dict_for_years(year_list=year_list, mlb_avgs_df=mlb_avgs_df)

        # DEFINE DIFF ADJUSTMENT FACTOR
        # 50% BECAUSE OPPOSITE TYPE AND COMMAND ARE ALSO ADJUSTED
        diff_reduction_multiplier = 0.5
        wotc_set_adjustment_factor = self.wotc_set_adjustment_factor(for_hitter_chart=self.is_hitter)
        
        # ADJUST OUTS BASED ON OBP
        obp_pct_change = mlb_pct_change_between_eras(stat='OBP', diff_reduction_multiplier=diff_reduction_multiplier, wotc_set_adjustment_factor=wotc_set_adjustment_factor) # HALFED BECAUSE OPPOSITE TYPE AND COMMAND ARE ALSO ADJUSTED
        
        # DEFINE OBP ADJUSTMENT FACTOR, UPDATE OUTS AND ONBASE RESULTS
        self.obp_adjustment_factor = round(1 + obp_pct_change, 3)
        self.command = round(self.command * self.obp_adjustment_factor, 2)
        updated_values = {}
        for category, value in self.values.items():
            if self.is_pitcher:
                adjustment_factor = self.obp_adjustment_factor if category.is_out else (1 / self.obp_adjustment_factor)
            else:
                adjustment_factor = (1 / self.obp_adjustment_factor) if category.is_out else self.obp_adjustment_factor
            updated_values[category] = round(value * adjustment_factor, 4)

        # ------ ADJUST ONBASE ------

        # IGNORE 1B+ BECAUSE IT'S CALCULATED AT THE END
        onbase_categories = [ChartCategory.BB, ChartCategory._2B, ChartCategory._3B, ChartCategory.HR]
        for category in onbase_categories:
            category_pct_diff_vs_wotc = mlb_pct_change_between_eras(stat=category.value, diff_reduction_multiplier=diff_reduction_multiplier)
            updated_values[category] = round(updated_values[category] * (1 - category_pct_diff_vs_wotc), 4)
        
        # ADJUST 1B TO MAKE SURE THE TOTAL EQUALS 20
        remaining_values = 20 - sum(updated_values.values())
        if remaining_values != 0:
            updated_values[ChartCategory._1B] += remaining_values

        # ------ ADJUST OUTS ------

        total_outs_expected = sum([v for k,v in updated_values.items() if k.is_out])

        # ADJUST SO FIRST
        so_post_obp_adjustment = updated_values[ChartCategory.SO]
        so_pct_diff_vs_wotc = mlb_pct_change_between_eras(stat=ChartCategory.SO.value, diff_reduction_multiplier=diff_reduction_multiplier)
        updated_values[ChartCategory.SO] = max( round(so_post_obp_adjustment * (1 - so_pct_diff_vs_wotc), 4), 0 )

        # TEMPORARILY ADJUST OTHER OUTS TO MATCH EXPECTED TOTAL
        current_non_so_outs = max( sum([v for k,v in updated_values.items() if k.is_out and k != ChartCategory.SO]), 0)
        new_non_so_outs = total_outs_expected - updated_values[ChartCategory.SO]
        current_pct_of_total_no_so_outs = { k: v / current_non_so_outs for k,v in updated_values.items() if k.is_out and k != ChartCategory.SO }
        updated_values.update({ k: round(new_non_so_outs * pct,4) for k, pct in current_pct_of_total_no_so_outs.items() })

        # ADJUST AGAIN TO ACCOUNT FOR RATIOS
        go_ao_pct_diff_vs_wotc = mlb_pct_change_between_eras(stat='GO/AO', diff_reduction_multiplier=diff_reduction_multiplier, default_value=1.1, ignore_pitcher_flip=True)
        updated_values[ChartCategory.GB] = max( round(updated_values[ChartCategory.GB] * (1 - go_ao_pct_diff_vs_wotc), 4), 0 )

        remaining_outs_not_adjusted = total_outs_expected - sum([v for k,v in updated_values.items() if k in [ChartCategory.SO, ChartCategory.GB]])
        current_ratio_pu_pct_chart = updated_values[ChartCategory.PU] / updated_values[ChartCategory.FB]
        if_fb_pct_diff_vs_wotc = mlb_pct_change_between_eras(stat='IF/FB', diff_reduction_multiplier=diff_reduction_multiplier, default_value=0.14, ignore_pitcher_flip=True)
        pu_pct_chart_adjusted = max( round(current_ratio_pu_pct_chart * (1 - if_fb_pct_diff_vs_wotc), 4), 0 )
        updated_values[ChartCategory.PU] = pu_pct_chart_adjusted * remaining_outs_not_adjusted
        updated_values[ChartCategory.FB] = remaining_outs_not_adjusted - updated_values[ChartCategory.PU]

        # UPDATE SELF
        self.values = updated_values
        self.update_outs_from_values()
        self.era = era
