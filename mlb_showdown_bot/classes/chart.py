from enum import Enum
from pydantic import BaseModel
from typing import Union, Optional

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

    def __init__(self, **data) -> None:
        super().__init__(**data)
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

    # ---------------------------------------
    # RANGES
    # ---------------------------------------

    def generate_range_strings(self) -> None:
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
                add_to_1b, num_of_results_2b = self.__calculate_ranges_over_20(dbl_per_400_pa, hr_per_400_pa)
                # DEFINE OVER 20 RANGES
                if category == ChartCategory._1B:
                    category_results += add_to_1b
                    range_end = current_chart_index + category_results - 1
                elif category == ChartCategory._2B:
                    category_results += num_of_results_2b
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

    def __calculate_ranges_over_20(self, dbl_per_400_pa:float, hr_per_400_pa:float) -> tuple[int, int]:
        """Calculates starting points of 2B and HR ranges for post 2001 cards
           whose charts expand past 20.

        Args:
          dbl_per_400_pa: Number of 2B results every 400 PA
          hr_per_400_pa: Number of HR results every 400 PA

        Returns:
          Tuple of 1b_additions, 2b results
        """

        if self.is_range_start_populated:
            hr_start = self.hr_range_start
            dbl_start = self.dbl_range_start or hr_start
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

        add_to_1b = dbl_start - 21
        hr_start_final = hr_start if (dbl_start < hr_start or self.is_range_start_populated) else dbl_start + 1
        num_of_results_2b = hr_start_final - dbl_start

        return add_to_1b, num_of_results_2b

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
    