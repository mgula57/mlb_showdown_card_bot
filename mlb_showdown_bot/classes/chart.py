from enum import Enum
from pydantic import BaseModel
from typing import Union, Optional
from pprint import pprint

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
    
    def expanded_over_20_result_factor_multiplier(self, set: str) -> float:
        # FOR 2002, ONLY WEIGHT HR
        if set == '2002':
            return 1.0 if self == ChartCategory.HR else 0.0
        
        match self:
            case ChartCategory._1B: return 0.0
            case _: return 1.0

# ---------------------------------------
# CHART
# ---------------------------------------

class Chart(BaseModel):

    is_pitcher: bool
    set: str
    is_expanded: bool
    command: Union[int, float]
    outs: Union[int, float]
    sb: float = 0.0
    values: dict[ChartCategory, Union[int, float]] = {}
    ranges: dict[ChartCategory, str] = {}
    dbl_per_400_pa: Optional[float] = None
    trpl_per_400_pa: Optional[float] = None
    hr_per_400_pa: Optional[float] = None
    dbl_range_start: Optional[int] = None
    trpl_range_start: Optional[int] = None
    hr_range_start: Optional[int] = None

    results: list[ChartCategory] = []
    stats_per_400_pa: dict[ChartCategory, float] = {}
    opponent: Optional['Chart'] = None

    def __init__(self, **data) -> None:
        super().__init__(**data)
        if len(self.values) > 0 and len(self.results) == 0:
            self.generate_results_list()
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
    def is_range_start_populated(self) -> bool:
        return self.hr_range_start

    @property
    def hr_start(self) -> int:
        return len([r for r in self.results if r != ChartCategory.HR]) + 1

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
                    
                    next_addition = projected_result_added + self.__slot_value(num_past_20=num_past_20-1)
                    # CHECK IF NEXT RESULT WILL PUT US OVER PROJECTED
                    if projected_result_added >= sub_21_projected_results:
                        break

        return over_20_results_added

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
            
            if result == category and last_category_under_21 != category:
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

    def generate_range_strings_old(self) -> None:
        """Use the current chart to generate string representations for the chart 
        Ex: 
          - SO: 3 -> SO: 1-3
          - GB: 2 -> GB: 4-5
          - FB: 3 -> FB: 6-8
          - ...

        Args:
          None
          
        Returns:
          None - Stores final dictionary in self.
        """

        if len(self.values) == 0 or len(self.ranges) > 0:
            return
        
        # FILL IN NULLS WITH 0'S
        dbl_per_400_pa = self.dbl_per_400_pa if self.dbl_per_400_pa else 0.0
        trpl_per_400_pa = self.trpl_per_400_pa if self.trpl_per_400_pa else 0.0
        hr_per_400_pa = self.hr_per_400_pa if self.hr_per_400_pa else 0.0

        current_chart_index = 1
        chart_ranges: dict[ChartCategory, str] = {}
        for category in self.categories_list:
            category_results = self.num_values(category)
            range_end = current_chart_index + category_results - 1

            # HANDLE RANGES > 20
            if self.is_expanded and range_end >= 20 and self.is_pitcher:
                add_to_bb, add_to_1b, add_to_2b = self.__calculate_ranges_over_20(dbl_per_400_pa, hr_per_400_pa)
                # DEFINE OVER 20 RANGES
                match category:
                    case ChartCategory.BB:
                        category_results += add_to_bb
                        range_end = current_chart_index + category_results - 1                    
                    case ChartCategory._1B:
                        category_results += add_to_1b
                        range_end = current_chart_index + category_results - 1
                    case ChartCategory._2B:
                        category_results += add_to_2b
                        range_end = current_chart_index + category_results - 1
            
            # HANDLE ERRORS WITH SMALL SAMPLE SIZE 2000/2001 FOR SMALL ONBASE
            if not self.is_expanded and range_end > 20:
                range_end = 20
                
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

        # FILL IN ABOVE 20 RESULTS IF APPLICABLE
        if self.is_expanded and self.num_values(ChartCategory.HR) < 1 and not self.is_pitcher:
            chart_ranges_updated = self.__hitter_chart_above_20(chart_ranges, dbl_per_400_pa, trpl_per_400_pa, hr_per_400_pa)
            self.ranges = chart_ranges_updated
        else:
            self.ranges = chart_ranges

    def __calculate_ranges_over_20(self, dbl_per_400_pa:float, hr_per_400_pa:float) -> tuple[int, int, int]:
        """Calculates starting points of 2B and HR ranges for post 2001 cards
           whose charts expand past 20.

        Args:
          dbl_per_400_pa: Number of 2B results every 400 PA
          hr_per_400_pa: Number of HR results every 400 PA

        Returns:
          Tuple of bb_additions, 1b_additions, 2b results
        """

        if self.is_range_start_populated:
            hr_start = self.hr_range_start
            dbl_start = self.dbl_range_start
        else:
            # HR
            if hr_per_400_pa >= 13:
                hr_start = 21
            elif hr_per_400_pa >= 11:
                hr_start = 22
            elif hr_per_400_pa >= 8.5:
                hr_start = 23
            elif hr_per_400_pa >= 7.0:
                hr_start = 24
            elif hr_per_400_pa >= 5.0:
                hr_start = 25
            elif hr_per_400_pa >= 3.0:
                hr_start = 26
            else:
                hr_start = 27

            # 2B
            if dbl_per_400_pa >= 13:
                dbl_start = 21
            elif dbl_per_400_pa >= 9.0:
                dbl_start = 22
            elif dbl_per_400_pa >= 5.5:
                dbl_start = 23
            else:
                dbl_start = 24

        add_to_bb = 0
        add_to_1b = (dbl_start if dbl_start else hr_start) - 21
        add_to_2b = 0

        # 0 2B RESULTS
        is_2b_results_and_no_hr = self.num_values(ChartCategory._2B) > 0 and self.num_values(ChartCategory.HR) == 0 and hr_start
        if is_2b_results_and_no_hr:
            add_to_2b = hr_start - 21
        elif dbl_start:
            hr_start = hr_start if (dbl_start < hr_start or self.is_range_start_populated) else dbl_start + 1
            add_to_2b = hr_start - dbl_start - 1            
        elif hr_start is not None:
            if self.values.get(ChartCategory._1B, 0) == 0 and self.values.get(ChartCategory._2B, 0) == 0:
                add_to_bb = hr_start - 21
                add_to_1b = 0
            else:
                add_to_1b = hr_start - 21

        return add_to_bb, add_to_1b, add_to_2b

    def __hitter_chart_above_20(self, current_chart_ranges:dict[ChartCategory, str], dbl_per_400_pa:float, trpl_per_400_pa:float, hr_per_400_pa:float) -> dict[str, str]:
        """If a hitter has remaining result categories above 20, populate them.
        Only for sets > 2001.

        Args:
            chart: Chart object.
            chart_ranges: Dict with visual representation of range per result category
            dbl_per_400_pa: Number of 2B results every 400 PA
            trpl_per_400_pa: Number of 3B results every 400 PA
            hr_per_400_pa: Number of HR results every 400 PA

        Returns:
            Dict of ranges for each result category.
        """
        # VALIDATE THAT CHART HAS VALUES ABOVE 20
        if self.num_values(ChartCategory.HR) > 0:
            return current_chart_ranges

        # STATIC THRESHOLDS FOR END HR #
        # THIS COULD BE MORE PROBABILITY BASED, BUT SEEMS LIKE ORIGINAL SETS USED STATIC METHODOLOGY
        # NOTE: 2002 HAS MORE EXTREME RANGES
        is_2002 = self.set == '2002'
        threshold_adjustment = 0 if is_2002 else -3
        if hr_per_400_pa < 1.0:
            hr_end = 27
        elif hr_per_400_pa < 2.5 and is_2002: # RESTRICT TO 2002
            hr_end = 26
        elif hr_per_400_pa < 3.75 and is_2002: # RESTRICT TO 2002
            hr_end = 25
        elif hr_per_400_pa < 4.75 + threshold_adjustment:
            hr_end = 24
        elif hr_per_400_pa < 6.25 + threshold_adjustment:
            hr_end = 23
        elif hr_per_400_pa < 7.5 + threshold_adjustment:
            hr_end = 22
        else:
            hr_end = 21
        current_chart_ranges[ChartCategory.HR] = '{}+'.format(hr_end)

        # SPLIT REMAINING OVER 20 SPACES BETWEEN 1B, 2B, AND 3B
        remaining_slots = hr_end - 21
        is_remaining_slots = remaining_slots > 0
        is_last_under_20_result_3b = self.num_values(ChartCategory._3B) > 0
        is_last_under_20_result_2b = not is_last_under_20_result_3b and self.num_values(ChartCategory._2B) > 0

        if is_remaining_slots:
            # FILL WITH 3B
            if is_last_under_20_result_3b:
                current_range_start = current_chart_ranges[ChartCategory._3B][0:2]
                new_range_end = hr_end - 1
                range_updated = '{}–{}'.format(current_range_start,new_range_end)
                current_chart_ranges[ChartCategory._3B] = range_updated
            # FILL WITH 2B (AND POSSIBLY 3B)
            elif is_last_under_20_result_2b:
                new_range_end = hr_end - 1
                if trpl_per_400_pa >= 3.5:
                    # GIVE TRIPLE 21-HR
                    triple_range = '21' if remaining_slots == 1 else '21-{}'.format(new_range_end)
                    current_chart_ranges[ChartCategory._3B] = triple_range
                else:
                    # GIVE 2B-HR
                    current_range_start = current_chart_ranges[ChartCategory._2B][0:2]
                    range_updated = '{}–{}'.format(current_range_start,new_range_end)
                    current_chart_ranges[ChartCategory._2B] = range_updated
            # FILL WITH 1B (AND POSSIBLY 2B AND 3B)
            else:
                new_range_end = hr_end - 1
                if trpl_per_400_pa + dbl_per_400_pa == 0:
                    # FILL WITH 1B
                    category_1b = ChartCategory._1B_PLUS if self.num_values(ChartCategory._1B_PLUS) > 0 else ChartCategory._1B
                    current_range_start = current_chart_ranges[category_1b][0:2]
                    # CHECK FOR IF SOMEHOW PLAYER HAS 0 1B TOO
                    if current_range_start == '—':
                        current_range_start = '21'
                    range_updated = '{}–{}'.format(current_range_start,new_range_end)
                    current_chart_ranges[category_1b] = range_updated
                else:
                    # SPLIT BETWEEN 2B AND 3B
                    dbl_pct = dbl_per_400_pa / (trpl_per_400_pa + dbl_per_400_pa)
                    dbl_slots = int(round((remaining_slots * dbl_pct)))
                    trpl_slots = remaining_slots - dbl_slots

                    # FILL 2B
                    dbl_range = '21' if dbl_slots == 1 else '21-{}'.format(20 + dbl_slots)
                    dbl_range = '—' if dbl_slots == 0 else dbl_range
                    current_chart_ranges[ChartCategory._2B] = dbl_range

                    # FILL 3B
                    trpl_start = 21 + dbl_slots
                    trpl_range = str(trpl_start) if trpl_slots == 1 else '{}-{}'.format(trpl_start, trpl_start + trpl_slots - 1)
                    trpl_range = '—' if trpl_slots == 0 else trpl_range
                    current_chart_ranges[ChartCategory._3B] = trpl_range
        return current_chart_ranges

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
    