from enum import Enum

# ---------------------------------------
# CHART CATEGORY
# ---------------------------------------

class ChartCategory(Enum):

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

class Chart:

    def __init__(self, is_pitcher:bool, set:str, command:int, outs:int, values:dict[str,int] = {}) -> None:

        self.is_pitcher:bool = is_pitcher
        self.set: str = set

        # COMMAND AND OUTS
        self.command: int = command
        self.outs: int = outs

        self.values: dict[ChartCategory, int] = {
            category: values.get(category.value) for category in ChartCategory if values.get(category, None) is not None
        }

        self.ranges: dict[ChartCategory, str] = {
        }

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
    def is_num_values_over_20(self) -> bool:
        return sum([v for v in self.values.values()]) > 20