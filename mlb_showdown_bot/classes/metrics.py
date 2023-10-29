from enum import Enum

class DefenseMetric(Enum):

    OAA = 'oaa'
    DRS = 'drs'
    TZR = 'tzr'
    DWAR = 'dWAR'
    
    @property
    def range_min(self) -> float:
        match self.value:
            case 'oaa': return -16
            case 'drs': return -20
            case 'tzr': return -18
            case 'dWAR': return -2.5

    @property
    def range_max(self) -> float:
        match self.value:
            case 'oaa': return 16
            case 'drs': return 20
            case 'tzr': return 18
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
        return 0.5 if self.value == 'oaa' else 1.0
    
class Stat(Enum):

    BA = 'batting_avg'
    OBP = 'onbase_perc'
    SLG = 'slugging_perc'

class PointsMetric(Enum):

    DEFENSE = 'defense'
    SPEED = 'speed'
    ONBASE = 'onbase'
    AVERAGE = 'average'
    SLUGGING = 'slugging'
    HOME_RUNS = 'home_runs'
    IP = 'ip'
    OUT_DISTRIBUTION = 'out_distribution'

    @property
    def points_breakdown_attr_name(self) -> str:
        match self.name:
            case 'DEFENSE': return 'defense'
            case 'SPEED': return 'speed'
            case 'ONBASE': return 'obp'
            case 'AVERAGE': return 'ba'
            case 'SLUGGING': return 'slg'
            case 'HOME_RUNS': return 'hr'
            case 'IP': return 'ip'
            case 'OUT_DISTRIBUTION': return 'out_distribution'

    @property
    def metric_name_bref(self) -> str:
        match self.name:
            case 'ONBASE': return 'onbase_perc'
            case 'AVERAGE': return 'batting_avg'
            case 'SLUGGING': return 'slugging_perc'
            case 'HOME_RUNS': return 'hr_per_650_pa'
            case _: return None