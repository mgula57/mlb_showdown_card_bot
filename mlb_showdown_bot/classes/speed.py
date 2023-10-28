
from enum import Enum

class SpeedMetric(Enum):

    SPRINT_SPEED = 'SPRINT SPEED'
    STOLEN_BASES = 'STOLEN BASES'

    @property
    def maximum_range_value(self) -> int:
        match self.name:
            case 'SPRINT_SPEED': return 31
            case 'STOLEN_BASES': return 26

    @property
    def minimum_range_value(self) -> int:
        match self.name:
            case 'SPRINT_SPEED': return 23
            case 'STOLEN_BASES': return -25

    @property
    def top_percentile_range_value(self) -> float:
        match self.name:
            case 'SPRINT_SPEED': return 25.0
            case 'STOLEN_BASES': return 18.0

    @property
    def weight(self) -> float:
        match self.name:
            case 'SPRINT_SPEED': return 0.60
            case 'STOLEN_BASES': return 0.40

    @property
    def weight_sb_outliers(self) -> float:
        match self.name:
            case 'SPRINT_SPEED': return 0.25
            case 'STOLEN_BASES': return 0.75
    
    @property
    def outlier_cutoff(self) -> int:
        match self.name:
            case 'SPRINT_SPEED': return None
            case 'STOLEN_BASES': return 21

    @property
    def threshold_max_650_pa(self) -> int:
        match self.name:
            case 'SPRINT_SPEED': return None
            case 'STOLEN_BASES': return 100