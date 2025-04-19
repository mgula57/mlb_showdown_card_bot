from enum import Enum

class DefenseMetric(Enum):

    OAA = 'oaa'
    DRS = 'drs'
    TZR = 'tzr'
    DWAR = 'dWAR'
    
    @property
    def range_min(self) -> float:
        return (-1 * self.range_max)

    @property
    def range_max(self) -> float:
        match self.value:
            case 'oaa': return 16
            case 'drs': return 19
            case 'tzr': return 17
            case 'dWAR': return 2.5

    @property
    def range_total_values(self) -> float:
        return self.range_max - self.range_min

    @property
    def first_base_plus_2_cutoff(self) -> float:
        """ For 1B, use a static cutoff instead of range """
        match self.value:
            case 'oaa': return 13
            case 'drs': return 17
            case 'tzr': return 15
            case 'dWAR': return 0.8

    @property
    def first_base_plus_1_cutoff(self) -> int:
        """ For 1B, use a static cutoff instead of range """
        match self.value:
            case 'oaa': return 2
            case 'drs': return 4
            case 'tzr': return 4
            case 'dWAR': return -0.25
    
    @property
    def first_base_minus_1_cutoff(self) -> float:
        """ For 1B, use a static cutoff instead of range. -1 1B defense only applies to 2022 set and beyond."""
        match self.value:
            case 'oaa': return -5
            case 'drs': return -5
            case 'tzr': return -5
            case 'dWAR': return -1.0
    
    @property
    def over_max_multiplier(self) -> float:
        """ Reduces outliers in OAA by reducing values over the defense maximum """
        return 0.5 if self == DefenseMetric.OAA else 0.6
    
class Stat(Enum):

    BA = 'batting_avg'
    OBP = 'onbase_perc'
    SLG = 'slugging_perc'
    OPS = 'onbase_plus_slugging'
    COMMAND = 'command'
