from enum import Enum
from pydantic import BaseModel
from typing import Union, Optional
from pprint import pprint
import numpy as np
import math

try:
    from .value_range import ValueRange
except ImportError:
    from value_range import ValueRange

# ---------------------------------------
# CHART CATEGORY
# ---------------------------------------

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
        """Max number of results for a category"""
        match self:
            case ChartCategory.BB: return 12 # BARRY BONDS EFFECT (HUGE WALK)
            case ChartCategory.HR: return 10
            case ChartCategory._2B: return 12
            case _: return 20

    def rounding_cutoff(self, is_pitcher:bool, is_expanded:bool, era:str) -> float:
        """Decimal to round up at.
        
        Args:
            is_pitcher: If the player is a pitcher.
            is_expanded: If the chart format is expanded.
            era: Era used for the chart.
        """
        match self:
            case ChartCategory.HR:
                if is_pitcher:
                    match era:
                        case 'STEROID ERA': 
                            if is_expanded: return 0.85
                            else: return 0.5
                        case 'STATCAST ERA' | 'PITCH CLOCK ERA': return 0.70
                        case _: return 0.75
        return 0.5


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
    is_expanded: bool
    opponent: Optional['Chart'] = None
    gb_multiplier: float = 1.0
    pu_multiplier: float = 1.0
    
    # PLAYER DATA
    is_pitcher: bool
    pa: int = 400
    stats_per_400_pa: dict[str, float] = {}

    # ACCURACY
    stat_accuracy_weights: dict[str, float] = {}
    command_out_accuracy_weight: float = 1.0
    accuracy: float = 1.0

    def __init__(self, **data) -> None:
        super().__init__(**data)

        # POPULATE VALUES DICT
        if len(self.values) == 0:
            self.generate_values_and_results()

        # POPULATE ACCURACY
        if len(self.stats_per_400_pa) > 0:
            self.generate_accuracy_rating()

        self.generate_range_strings()

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
        values_list = [ [self.command_name, str(self.command)], ['outs', str(self.outs)] ]
        values_list += [[category.value, str(round(value,2))] for category, value in self.values.items()]
        return values_list
    
    @property
    def slot_values(self) -> dict[int, float]:
        
        # EACH SLOT IS WORTH 1 FOR CLASSIC
        if not self.is_expanded:
            return { i: 1 for i in range(1, 21) }
        
        # EXPANDED CHARTS
        slot_values_dict: dict[int, float] = { i: self.sub_21_per_slot_worth for i in range(1, 21) }

        # FILL 21+ SLOTS WITH A GEOMETRIC PROGRESSION, STARTING AT 0.5
        # EX: 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125, 0.00390625, 0.001953125, 0.0009765625
        # THE FORMULA OF A GEOMETRIC PROGRESSION IS: a * r^(n-1) 
        # EX: 21:  0.5 * 0.5 ^ 0 = 0.5
        #     22:  0.5 * 0.5 ^ 1 = 0.25
        #     23:  0.5 * 0.5 ^ 2 = 0.125
        slot_values_dict.update( {( 20 + i ): ( 0.5 * pow(0.5, (i-1)) ) for i in range(1, 11)} )

        # FILL THE 30TH SLOT WITH THE REMAINING VALUE
        # ALLOWS THE VALUE TO ADD UP TO EXACTLY 20
        remaining_value = 20 - sum(slot_values_dict.values())
        slot_values_dict[30] += remaining_value

        return slot_values_dict

    @property
    def sub_21_per_slot_worth(self) -> float:
        if not self.is_expanded:
            return 1
        
        return 0.99

    @property
    def sub_21_total_possible_slots(self) -> float:
        if not self.is_expanded:
            return 20
        
        return 20 * self.sub_21_per_slot_worth

    @property
    def total_possible_slots(self) -> int:
        if not self.is_expanded:
            return 20
        
        return 30

    @property
    def gb_pct(self) -> float:
        return round(self.num_values(ChartCategory.GB) / self.outs, 3)
    
    @property
    def hr_start(self) -> int:
        return len([r for r in self.results.keys() if r != ChartCategory.HR]) + 1

    @property
    def _2b_start(self) -> int:
        return len([ r for r in self.results.keys() if r not in [ChartCategory.HR, ChartCategory._2B] ]) + 1

    @property
    def hitter_so_results_soft_cap(self) -> int:
        match self.set:
            case '2002': return 4 * self.sub_21_per_slot_worth
            case _: return 3 * self.sub_21_per_slot_worth

    @property
    def hitter_so_results_hard_cap(self) -> int:
        match self.set:
            case '2000': return 5 * self.sub_21_per_slot_worth
            case '2002': return 7 * self.sub_21_per_slot_worth
            case _: return 6 * self.sub_21_per_slot_worth

    @property
    def hitter_single_plus_denominator_minimum(self) -> float:
        match self.set:
            case '2000' | '2001' | 'CLASSIC': return 3.2
            case '2002': return 7.0
            case '2003': return 6.0
            case '2004' | '2005' | 'EXPANDED': return 5.5
    
    @property
    def hitter_single_plus_denominator_maximum(self) -> float:
        match self.set:
            case '2000' | '2001' | 'CLASSIC': return 9.6
            case '2002': return 10.5
            case '2003' | '2004': return 10.5
            case '2005' | 'EXPANDED': return 9.75

    # ---------------------------------------
    # GENERATE CHART ATTRIBUTES
    # ---------------------------------------

    def generate_values_and_results(self) -> None:
        """Generate values dictionary and store to self

        """

        def add_results_to_dict(category:ChartCategory, num_results:int, current_chart_index:int) -> None:
            iterator = -1 if category.is_filled_in_desc_order else 1
            for i in range(current_chart_index, current_chart_index + ( (num_results+1) * iterator), iterator):
                self.results[i] = category

        def fill_chart_categories(categories: list[ChartCategory], is_reversed:bool = False) -> None:
            current_chart_index = self.total_possible_slots if is_reversed else 1
            for chart_category in categories:

                # SKIP 1B+, THAT IS FILLED LATER
                if chart_category in [ChartCategory._1B_PLUS]: continue

                # DEFINE LIMIT FOR CATEGORY
                category_limit = chart_category.slot_limit * self.sub_21_per_slot_worth
                is_out_max = self.outs if chart_category.is_out else 20 - self.outs
                category_remaining = is_out_max - sum([v for k,v in self.values.items() if k.is_out == chart_category.is_out])
                max_values = min(category_limit, category_remaining)
                min_values = category_remaining if chart_category == ChartCategory._1B else None

                # CALCULATE VALUES
                values, results = self.calc_chart_category_values_from_rate_stats(category=chart_category, current_chart_index=current_chart_index, max_values=max_values, min_values=min_values)
                
                # IF SINGLE, SPLIT INTO 1B AND 1B+
                if chart_category == ChartCategory._1B and not self.is_pitcher:
                    single_plus_values, single_plus_results = self.__single_plus_values_and_results(total_1B_values=values, current_chart_index=current_chart_index)
                    self.values[ChartCategory._1B_PLUS] = single_plus_values
                    add_results_to_dict(category=ChartCategory._1B_PLUS, num_results=single_plus_results, current_chart_index=current_chart_index)
                    current_chart_index -= single_plus_results
                    values -= single_plus_values
                    results -= single_plus_results
                
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
        self.outs, _ = self.values_and_results(my_out_values)

        # ITERATE THROUGH CHART CATEGORIES
        all_categories = self.categories_list
        out_categories = [c for c in all_categories if not c.is_filled_in_desc_order]
        non_out_categories = [c for c in all_categories if c.is_filled_in_desc_order][::-1] # REVERSE NON OUTS TO START WITH HR
        fill_chart_categories(out_categories)
        fill_chart_categories(non_out_categories, is_reversed=True)

        return

    def calc_chart_category_values_from_rate_stats(self, category:ChartCategory, current_chart_index:int, max_values:float, min_values:float=None) -> Union[float | int]:
        """Get chart category values based on rate stats

        Args:
            category: Chart category to get values for.
            current_chart_index: Current index in chart.
            max_values: Max number of values to fill.
            min_values: Min number of values to fill.

        Returns:
            Float of chart category values.
        """

        real_results_per_400_pa = self.stats_per_400_pa.get(f'{category.value.lower()}_per_400_pa', 0)
        opponent_values = self.opponent.num_values(category)
        chart_values = max( (real_results_per_400_pa - (self.opponent_advantages_per_20 * opponent_values)) / self.my_advantages_per_20, 0 )
        
        # LIMIT RESULTS TO CHART CATEGORY SLOT LIMIT
        chart_values = max( min(chart_values, max_values) , min_values if min_values else 0)
        chart_values_rounded, results = self.values_and_results(value=chart_values, category=category, current_chart_index=current_chart_index)

        if category == ChartCategory.SO:
            chart_values_rounded = self.__so_values(current_so=chart_values_rounded, num_out_slots=self.outs)
            results = int(round(chart_values_rounded / self.sub_21_per_slot_worth))

        return chart_values_rounded, results

    def __so_values(self, current_so:int, num_out_slots:int) -> Union[int, float]:
        """Update SO chart value to account for outliers and maximums

        Args:
          current_so: Number of slots currently occupied
          num_out_slots: Total numbers of slots for outs available.

        Returns:
          Updated SO chart slots.
        """

        # FOR PITCHERS, SIMPLY RETURN CURRENT SO NUMBER
        if self.is_pitcher:
            return min(current_so, num_out_slots)
        
        # --- HITTERS ---
        hard_limit_hitter = min(num_out_slots, self.hitter_so_results_hard_cap)
        soft_limit_hitter = self.hitter_so_results_soft_cap
        
        # IF HITTER'S STRIKEOUTS ARE UNDER SOFT LIMIT, RETURN CURRENT RESULTS
        if current_so < soft_limit_hitter:
            return min(current_so, hard_limit_hitter)
        
        # IF PLAYER HAS SMALL SAMPLE SIZE, USE SOFT LIMIT AS HARD CAP
        real_pa = self.pa
        if real_pa < 100:
            return min(current_so, hard_limit_hitter, soft_limit_hitter)
        
        # IF PLAYER IS OVER THE SOFT LIMIT, SCALE BACK RESULTS TOWARDS SOFT CAP AND USE FLOOR INSTEAD OF ROUND
        if current_so > soft_limit_hitter:
            multiplier = 0.80
            current_so *= multiplier
            current_so = max(soft_limit_hitter, current_so) # MAKE SURE MULTIPLIER DOESN'T MOVE CARD UNDER SOFT LIMIT
            current_so = math.floor(current_so)
            return min(current_so, hard_limit_hitter)

        return min(current_so, hard_limit_hitter)

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

        # ROUND TO NEAREST SLOT WORTH
        raw_value = round(value / self.sub_21_per_slot_worth) * self.sub_21_per_slot_worth
        raw_results = int(round(raw_value / self.sub_21_per_slot_worth))
        if category is None or not self.is_expanded:
            return raw_value, raw_results
        
        # ROUND TO NEAREST SLOT WORTH
        if category.is_out or current_chart_index is None:
            return raw_value, raw_results
        
        # ITERATE THROUGH EACH SLOT WORTH RESULT AND ROUND
        end = 1 if category.is_filled_in_desc_order else self.total_possible_slots
        iterator = -1 if category.is_filled_in_desc_order else 1
        value_updated = 0
        num_results = 0
        for i in range(current_chart_index, end, iterator):
            slot_value = self.__slot_value(index=i)
            next_slot_value = self.__slot_value(index=i + iterator)
            rounded_vs_original_diff = (value_updated + slot_value) - value
            if rounded_vs_original_diff >= (next_slot_value / 2):
                break
            value_updated += slot_value
            num_results += 1
        
        return value_updated, num_results

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
    

    # ---------------------------------------
    # ACCURACY
    # ---------------------------------------

    def generate_accuracy_rating(self) -> None:
        """Calculate accuracy of chart based on accuracy weights. Store to self."""
        
        # CHECK ACCURACY COMPARED TO REAL LIFE
        in_game_stats_per_400_pa = self.projected_stats_per_400_pa
        weights = self.stat_accuracy_weights
        accuracy = round(self.__accuracy_between_dicts(
            actuals_dict=self.stats_per_400_pa,
            measurements_dict=in_game_stats_per_400_pa,
            weights=weights,
            only_use_weight_keys=True
        ), 4)

        # ADD WEIGHTING OF ACCURACY
        # LIMITS AMOUNT OF RESULTS PER SET FOR CERTAIN COMMAND/OUT COMBINATIONS
        weight = self.command_out_accuracy_weight
        accuracy = accuracy * weight

        # REDUCE ACCURACY FOR CHARTS WITH NUM OUTS OUT OF NORM
        if self.is_pitcher:
            out_min = 14 if self.is_expanded else 14
            out_max = 18 if self.is_expanded else 18
            command_outlier_upper_bound = 6 if self.is_expanded else 6
            command_outlier_lower_bound = 1 if self.is_expanded else 1
        else:
            out_min = 5 if self.is_expanded else 2
            out_max = 7 if self.is_expanded else 5
            command_outlier_upper_bound = 15 if self.is_expanded else 11
            command_outlier_lower_bound = 9 if self.is_expanded else 5

        outs = self.outs / self.sub_21_per_slot_worth
        is_outside_out_bounds = outs < out_min or outs > out_max
        is_outlier = (self.command <= command_outlier_lower_bound and outs > out_max) or (self.command >= command_outlier_upper_bound and outs < out_max)
        if is_outside_out_bounds and not is_outlier:
            accuracy /= 2

        self.accuracy = accuracy

    def __accuracy_between_dicts(self, actuals_dict:dict, measurements_dict:dict, weights:dict={}, all_or_nothing:list[str]=[], only_use_weight_keys:bool=False) -> float:
        """Compare two dictionaries of numbers to get overall difference

        Args:
          actuals_dict: First Dictionary. Use this dict to get keys to compare.
          measurements_dict: Second Dictionary.
          weights: X times to count certain category (ex: 3x for command)
          all_or_nothing: List of category names to compare as a boolean 1 or 0 instead
                          of pct difference.
          only_use_weight_keys: Bool for whether to only count an accuracy there is a weight associated
          era_override: Optionally override the era used for baseline opponents.

        Returns:
          Float for overall accuracy
        """

        denominator = len((weights if only_use_weight_keys else actuals_dict).keys())
        accuracies = 0

        # CALCULATE CATEGORICAL ACCURACY
        metrics_and_accuracies: dict[str, float] = {}
        for key, value1 in actuals_dict.items():
            
            evaluate_key = key in measurements_dict.keys()
            evaluate_key = key in weights.keys() if only_use_weight_keys else evaluate_key
            if evaluate_key:
                value2 = measurements_dict[key]

                if key in all_or_nothing:
                    accuracy_for_key = 1 if value1 == value2 else 0
                else:
                    denominator = value1
                    # ACCURACY IS 100% IF BOTH ARE EQUAL (IF STATEMENT TO AVOID 0'S)
                    if value1 == value2:
                        accuracy_for_key = 1.0
                    else:
                        # CAN'T DIVIDE BY 0, SO USE OTHER VALUE AS BENCHMARK
                        if value1 == 0: denominator = value2
                        accuracy_for_key = (value1 - abs(value1 - value2) ) / denominator

                # APPLY WEIGHTS
                weight = float(weights[key]) if key in weights.keys() else 1
                denominator += (weight - 1) if key in weights.keys() else 0
                weighted_accuracy = (accuracy_for_key * weight)
                accuracies += weighted_accuracy

                metrics_and_accuracies[key] = round(accuracy_for_key, 3)

        overall_accuracy = accuracies / denominator

        return overall_accuracy

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

        # MATCHUP VALUES
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
        # SLASH LINE

        # BA
        batting_avg = hits_per_400_pa / (400.0 - walks_per_400_pa)

        # OBP
        onbase_results_per_400_pa = walks_per_400_pa + hits_per_400_pa
        obp = onbase_results_per_400_pa / 400.0

        # SLG
        slugging_pct = self.__slugging_pct(ab=400-walks_per_400_pa,
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
            'ab_per_400_pa': 400 - walks_per_400_pa,
            'batting_avg': batting_avg,
            'onbase_perc': obp,
            'slugging_perc': slugging_pct,
            'onbase_plus_slugging': obp + slugging_pct,
        }

        return results_per_400_pa

    def projected_stats_for_category(self, category:ChartCategory, pa: int = 400) -> int | float:

        my_results = self.num_values(category)
        opponent_results = self.opponent.num_values(category)
        pa_multiplier = pa / 400
        return ( (my_results * self.my_advantages_per_20) + (opponent_results * self.opponent_advantages_per_20) ) * pa_multiplier

    def __slugging_pct(self, ab:float, singles:float, doubles:float, triples:float, homers:float)  -> float:
        """ Calculate Slugging Pct"""
        return (singles + (2 * doubles) + (3 * triples) + (4 * homers)) / ab
    
    # ---------------------------------------
    # RANGES
    # ---------------------------------------

    @property
    def ranges_list(self) -> list[str]:
        """List of ranges ordered as strings"""
        return [self.ranges[category] for category in self.categories_list]
    

    # ---------------------------------------
    # GB/PU PERCENTS
    # ---------------------------------------

    @property
    def slg_multiplier_for_ratios(self) -> float:
        """Calculate percentile of slugging percent"""
        slg_range = ValueRange(min = 0.250, max = 0.500)
        slg_percentile = slg_range.percentile(value=self.stats_per_400_pa.get('slugging_perc', None))
        multiplier = 1.0 if slg_percentile < 0 else 1.0 - slg_percentile
        return multiplier

    @property
    def gb_pct(self) -> float:
        """Calculate gb -> fb ratio. Fills gaps if data is not available of bref"""
        gb_pct = self.stats_per_400_pa.get('GO/AO', None)
        if gb_pct is None:
            multiplier = self.slg_multiplier_for_ratios
            gb_pct = gb_pct if gb_pct else round(1.5 * max(multiplier, 0.5),3)
    
        return gb_pct
    
    @property
    def pu_pct(self) -> float:
        """Calculate infield fb -> outfield fb ratio. Fills gaps if data is not available of bref"""
        pu_pct = self.stats_per_400_pa.get('IF/FB', None)
        if pu_pct is None:
            multiplier = self.slg_multiplier_for_ratios
            popup_pct = popup_pct if popup_pct else round(0.16 * max(multiplier, 0.5),3)
    
        return pu_pct

    