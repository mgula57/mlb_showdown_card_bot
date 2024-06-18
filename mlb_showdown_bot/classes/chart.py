from enum import Enum
from pydantic import BaseModel
from typing import Union, Optional
from pprint import pprint
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

    def expanded_over_20_result_factor_multiplier(self, set: str) -> float:
        # FOR 2002, ONLY WEIGHT HR
        if set == '2002':
            return 1.0 if self == ChartCategory.HR else 0.0
        
        match self:
            case ChartCategory._1B: return 0.0
            case _: return 1.0

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
    outs: Union[int, float]
    values: dict[ChartCategory, Union[int, float]] = {}
    ranges: dict[ChartCategory, str] = {}
    results: list[ChartCategory] = []
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
            self.generate_values_dict()

        # POPULATE RESULTS LIST
        if len(self.values) > 0 and len(self.results) == 0:
            self.generate_results_list()

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
        return f'{self.command}-{self.outs}'

    @property
    def values_as_list(self) -> list[list[str, str]]:
        """Convert chart values and command/outs to list of lists"""
        values_list = [ [self.command_name, str(self.command)], ['outs', str(self.outs)] ]
        values_list += [[category.value, str(round(value,2))] for category, value in self.values.items()]
        return values_list
    
    @property
    def gb_pct(self) -> float:
        return round(self.num_values(ChartCategory.GB) / self.outs, 3)
    
    @property
    def hr_start(self) -> int:
        return len([r for r in self.results if r != ChartCategory.HR]) + 1

    @property
    def _2b_start(self) -> int:
        return len([ r for r in self.results if r not in [ChartCategory.HR, ChartCategory._2B] ]) + 1

    @property
    def hitter_so_results_soft_cap(self) -> int:
        match self.set:
            case '2002': return 4
            case _: return 3

    @property
    def hitter_so_results_hard_cap(self) -> int:
        match self.set:
            case '2000': return 5
            case '2002': return 7
            case _: return 6

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

    def generate_values_dict(self) -> None:
        """Generate values dictionary and store to self

        """

        for stat, results_per_400_pa in self.stats_per_400_pa.items():

            # SKIP IF NOT CHART CATEGORY
            category_name = stat[:2].upper()
            if category_name not in [c.value for c in ChartCategory]:
                continue

            # STOLEN BASES HAS NO OPPONENT RESULTS
            if category_name == 'SB':
                self.sb = round(results_per_400_pa / self.stats_per_400_pa['pct_of_400_pa'], 3)
                continue
        
            # CHART CATEGORY ENUM
            chart_category = ChartCategory(category_name)

            # SKIP 3B IF PITCHER
            if self.is_pitcher and chart_category == ChartCategory._3B:
                self.values[chart_category] = 0
                continue

            opponent_values = self.opponent.num_values(chart_category)
            chart_results = (results_per_400_pa - (self.opponent_advantages_per_20 * opponent_values)) / self.my_advantages_per_20

            if chart_category == ChartCategory.SO:
                chart_results = self.__so_results(current_so=chart_results, num_out_slots=self.outs)
            
            # HANDLE CASE OF < 0
            chart_results = max(chart_results, 0)

            # WE ROUND THE PREDICTED RESULTS (2.4 -> 2, 2.5 -> 3)
            chart_results_decimal = chart_results % 1
            chart_rounding_cutoff = chart_category.rounding_cutoff(is_pitcher=self.is_pitcher, is_expanded=self.is_expanded, era=self.era)
            rounded_results = math.ceil(chart_results) if chart_results_decimal > chart_rounding_cutoff else math.floor(chart_results)            
            
            # LIMIT RESULTS TO CHART CATEGORY SLOT LIMIT
            rounded_results = min(rounded_results, chart_category.slot_limit)
            
            # STORE VALUES
            self.values[chart_category] = rounded_results

        # FILL "OUT" CATEGORIES (PU, GB, FB)
        out_slots_remaining = self.outs - float(self.num_values(ChartCategory.SO))
        pu, gb, fb = self.__out_results(out_slots_remaining=out_slots_remaining)
        self.values.update({
            ChartCategory.PU: pu,
            ChartCategory.GB: gb,
            ChartCategory.FB: fb,
        })

        # CALCULATE HOW MANY SPOTS ARE LEFT TO FILL 1B AND 1B+
        remaining_slots = self.remaining_slots(excluded_categories=[ChartCategory._1B])
        self.check_and_fix_value_overage(excluded_categories=[ChartCategory._1B])
        remaining_slots = self.remaining_slots(excluded_categories=[ChartCategory._1B]) # RE-CHECK
        remaining_slots_qad = 0 if remaining_slots < 0 else remaining_slots

        # FILL 1B AND 1B+
        stolen_bases = int(self.stats_per_400_pa.get('sb_per_400_pa',0))
        single_results, single_plus_results = self.__single_and_single_plus_results(remaining_slots=remaining_slots_qad, sb=stolen_bases)
        self.values.update({
            ChartCategory._1B: single_results,
            ChartCategory._1B_PLUS: single_plus_results,
        })

    def __out_results(self, out_slots_remaining:int) -> tuple[int, int, int]:
        """Determine distribution of out results for Player.

        Args:
          gb_pct: Percent Ground Outs vs Air Outs.
          popup_pct: Percent hitting into a popup.
          out_slots_remaining: Total # Outs - SO
          slg: Real-life stats slugging percent.
          era_override: Optionally override the era used for baseline opponents.

        Returns:
          Tuple of PU, GB, FB out result ints.
        """

        # SET DEFAULTS FOR EMPTY DATA, BASED ON SLG
        gb_pct = self.stats_per_400_pa.get('GO/AO', None)
        popup_pct = self.stats_per_400_pa.get('IF/FB', None)
        if gb_pct is None or popup_pct is None:
            slg_range = ValueRange(min = 0.250, max = 0.500)
            slg_percentile = slg_range.percentile(value=self.stats_per_400_pa.get('slugging_perc', None))
            multiplier = 1.0 if slg_percentile < 0 else 1.0 - slg_percentile
            gb_pct = gb_pct if gb_pct else round(1.5 * max(multiplier, 0.5),3)
            popup_pct = popup_pct if popup_pct else round(0.16 * max(multiplier, 0.5),3)

        if out_slots_remaining > 0:
            # SPLIT UP REMAINING SLOTS BETWEEN GROUND AND AIR OUTS
            gb_outs = int(round((out_slots_remaining / (gb_pct + 1)) * gb_pct * self.gb_multiplier))
            air_outs = out_slots_remaining - gb_outs
            # FOR PU, ADD A MULTIPLIER TO ALIGN MORE WITH OLD SCHOOL CARDS
            pu_multiplier = self.pu_multiplier
            pu_outs = 0 if not self.is_pitcher else int(math.ceil(air_outs*popup_pct*pu_multiplier))
            pu_outs = int(air_outs if pu_outs > air_outs else pu_outs)
            fb_outs = int(air_outs-pu_outs)
        else:
            fb_outs = 0
            pu_outs = 0
            gb_outs = 0

        return pu_outs, gb_outs, fb_outs

    def __so_results(self, current_so:int, num_out_slots:int) -> int:
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

    def __single_and_single_plus_results(self, remaining_slots:int, sb:int) -> tuple[int, int]:
        """Fill 1B and 1B+ categories on chart.

        Args:
          remaining_slots: Remaining slots out of 20.
          sb: Stolen bases per 400 PA

        Returns:
          Tuple of 1B, 1B+ result ints.
        """

        # PITCHER HAS NO 1B+
        if self.is_pitcher:
            return remaining_slots, 0

        # DIVIDE STOLEN BASES PER 400 PA BY A SCALER BASED ON ONBASE #
        min_onbase = 7 if self.is_expanded else 4
        max_onbase = 16 if self.is_expanded else 12
        onbase_range = ValueRange(min=min_onbase, max=max_onbase)
        min_denominator = self.hitter_single_plus_denominator_minimum
        max_denominator = self.hitter_single_plus_denominator_maximum
        onbase_pctile = onbase_range.percentile(value=self.command)
        single_plus_denominator = min_denominator + ( (max_denominator-min_denominator) * onbase_pctile )
        single_plus_results_raw = math.trunc(sb / single_plus_denominator)

        # MAKE SURE 1B+ IS NOT OVER REMAINING SLOTS
        single_plus_results = single_plus_results_raw if single_plus_results_raw <= remaining_slots else remaining_slots
        single_results = remaining_slots - single_plus_results

        return single_results, single_plus_results

    def generate_results_list(self) -> None:
        """Convert chart values dict to list of Chart Results
        Add 21+ results for expanded charts

        Args:
            None

        Returns:
            List of Chart categories up to 30
        """

        # 1-20 RESULTS
        results_list: list[ChartCategory] = []
        for chart_category in ChartCategory:
            results = self.num_values(chart_category)
            if results > 0:
                results_list += [chart_category] * int(results)
        last_result = results_list[-1]

        # FILL 21-30 WITH LAST RESULT
        fill_with_last_result = not self.is_expanded or last_result == ChartCategory.HR or not self.is_pitcher
        if fill_with_last_result:
            # FILL WITH LAST RESULT
            results_list += [last_result] * (30 - len(results_list))
            self.results = results_list
            return
        
        over_20_results: list[ChartCategory] = [ChartCategory.HR] * 2

        # CALCULATE HR START
        hr_max_pitcher = 30 - len(over_20_results)
        over_20_results += self.__num_21_plus_chart_results(ChartCategory.HR, start=hr_max_pitcher)
        if len(over_20_results) >= 10:
            # REVERSE OVER 20 RESULTS
            over_20_results = over_20_results[::-1]
            self.results = results_list + over_20_results[:10]
            return 
        
        # FILL IN REMAINING SLOTS
        remaining_slots = max(10 - len(over_20_results), 0)
        match self.set:
            case '2002':
                # FILL REMAINING SLOTS WITH LAST RESULT
                over_20_results += [last_result] * remaining_slots
                
            case _:
                # FILL IN 2B, 1B, BB
                for category in [ChartCategory._2B, ChartCategory._1B, ChartCategory.BB]:
                    remaining_slots = max(10 - len(over_20_results), 0)
                    if remaining_slots == 0:
                        continue
                    
                    if category == last_result:
                        over_20_results += [category] * remaining_slots
                    else:
                        over_20_results += self.__num_21_plus_chart_results(category, start=20 + remaining_slots)

        # REVERSE OVER 20 RESULTS AND STORE IN SELF
        over_20_results = over_20_results[::-1]
        self.results = results_list + over_20_results[:10]

        return 

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
        result_list = self.results if self.is_expanded else self.results[:20]
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
        return
    

    # ---------------------------------------
    # ACCURACY
    # ---------------------------------------

    def generate_accuracy_rating(self) -> None:
        """Calculate accuracy of chart based on accuracy weights. Store to self."""
        
        # CHECK ACCURACY COMPARED TO REAL LIFE
        in_game_stats_per_400_pa = self.projected_stats_per_400_pa()
        weights = self.stat_accuracy_weights
        accuracy = self.__accuracy_between_dicts(
            actuals_dict=self.stats_per_400_pa,
            measurements_dict=in_game_stats_per_400_pa,
            weights=weights,
            only_use_weight_keys=True
        )
        
        # QA: CHANGE ACCURACY TO 0 IF CHART DOESN'T ADD UP TO 20
        accuracy = 0.0 if self.is_num_values_over_20 else accuracy

        # ADD WEIGHTING OF ACCURACY
        # LIMITS AMOUNT OF RESULTS PER SET FOR CERTAIN COMMAND/OUT COMBINATIONS
        weight = self.command_out_accuracy_weight
        accuracy = accuracy * weight

        # REDUCE ACCURACY FOR CHARTS WITH NON 0 REMAINING SLOTS
        if self.remaining_slots() != 0:
            accuracy = -5.0

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

    def __num_21_plus_chart_results(self, category:ChartCategory, start:int) -> list[ChartCategory]:
        """Calculate number of 21+ results for expanded charts for a particular category.
        
        Args:
            category: ChartCategory to calculate 21+ results for.
            start: Which chart result index (ex: 28) to start at.
        
        Returns:
            List of chart results added to over_20_results.
        """

        over_20_results_added: list[ChartCategory] = []
        sub_21_projected_results = self.num_results_projected(category)
        projected_result_added = 0
        plus_21_range_start = start - 20
        
        for num_past_20 in range(plus_21_range_start, 0, -1):
            match self.set:
                case '2002' | '2003':
                    result_factor = self.result_factor(num_past_20=num_past_20, category=category)
                    projected_result_added += result_factor
                    over_20_results_added.append(category)

                    # CHECK IF NEXT RESULT WILL PUT US OVER PROJECTED
                    if projected_result_added + result_factor >= sub_21_projected_results:
                        break
                case _: 

                    over_20_results_added.append(category)
                    if sub_21_projected_results == 0:
                        break
                    
                    slot_value = self.__slot_value(num_past_20=num_past_20)
                    projected_result_added += slot_value
                    
                    next_addition = self.__slot_value(num_past_20=num_past_20-1)
                    check_vs_next_value = category in [ChartCategory._2B]
                    comparison_results = projected_result_added + (next_addition if check_vs_next_value else 0)

                    # CHECK IF NEXT RESULT WILL PUT US OVER PROJECTED
                    if comparison_results >= sub_21_projected_results:
                        break

        return over_20_results_added

    def __slot_value(self, num_past_20: int) -> float:
        """Determine how many slots a result over 20 is valued at"""
        
        # Return 0 if CLASSIC
        if not self.is_expanded:
            return 0
        
        match self.set:
            case _:
                if num_past_20 >= 8: return 0
                elif num_past_20 == 7: return 0.03
                else:
                    _slot_value = 0.03
                    for i in range(1, 8-num_past_20):
                        _slot_value += 0.06
                    return _slot_value

    def result_factor(self, num_past_20:int, category: ChartCategory) -> float:
        """Calculate probability of over 20 result for expanded charts"""
        pitcher_max = 5 if self.set == '2002' else 6
        max_command = pitcher_max if self.is_pitcher else 16
        command_percentile = min(self.command / max_command, 1)

        # REDUCE PROBABILITIES FOR HIGHER COMMAND
        # STARTING DENOMINATOR: DENOMINATOR FOR HIGHEST COMMAND (EX: 6, 16)
        # MAX_ADDITION: SMALLEST DENOMINATOR ADDITION POSSIBLE. APPLIES TO LOWEST COMMAND.
        match self.set:
            case '2002': 
                starting_denominator = 15
                max_addition = 30
            case '2003':
                starting_denominator = 13
                max_addition = 33
            case _:
                starting_denominator = 15
                max_addition = 30
        
        final_starting_point = starting_denominator + (max_addition * (1-command_percentile))
        return (1 / (final_starting_point + num_past_20)) * category.expanded_over_20_result_factor_multiplier(self.set)

    def total_over_20_results(self, category:ChartCategory) -> int:
        """Calculate total number of over 20 results. Weigh number by result factor based on index"""

        # NONE FOR CLASSIC
        if not self.is_expanded:
            return 0
        
        total_results = 0
        last_category_under_21 = self.results[19]
        for i, result in enumerate(self.results[20:30], 1):
            
            if result == category: #and last_category_under_21 != category:
                match self.set:
                    case '2002' | '2003':
                        total_results += self.result_factor(num_past_20=i, category=category)
                    case _:
                        total_results += self.__slot_value(num_past_20=i)

        
        return total_results
    
    # ---------------------------------------
    # REAL STATS
    # ---------------------------------------

    def projected_stats_per_400_pa(self) -> dict:
        """Predict real stats given Showdown in game chart.

        Args:
          chart: Chart object.

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

        my_results = self.num_values(category) + self.total_over_20_results(category)
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
    # QA
    # ---------------------------------------
    
    def remaining_slots(self, excluded_categories:list[ChartCategory] = []) -> int:
        """ Calculate how many chart slots remain.
        
        Args:
          excluded_categories: Optional list of categories to exclude from the count.
        
        Returns:
          Int for remaining slots.
        """

        return 20 - (sum([v for c, v in self.values.items() if c not in excluded_categories]))
    
    def check_and_fix_value_overage(self, excluded_categories:list[ChartCategory] = []) -> None:
        """ If there are over 20 chart slots used, attempt to fix by reducing BB.
        
        Args:
          excluded_categories: Optional list of categories to exclude from the count.
        
        Returns:
          None
        """

        remaining_slots = self.remaining_slots(excluded_categories=excluded_categories)

        # CHART IS COMPLIANT, RETURN
        if remaining_slots >= 0:
            return

        # FIX BARRY BONDS EFFECT (HUGE WALK)
        walk_results = self.num_values(ChartCategory.BB)
        if walk_results >= abs(remaining_slots):
            self.values[ChartCategory.BB] = walk_results - abs(remaining_slots)

    @property
    def is_num_values_over_20(self) -> bool:
        return self.remaining_slots() < 0
    