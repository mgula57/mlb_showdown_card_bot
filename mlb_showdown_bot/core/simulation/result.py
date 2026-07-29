from enum import Enum

class Result(Enum):
    PU = "pu"
    SO = "so"
    GB = "gb"
    FB = "fb"
    BB = "bb"
    SINGLE = "1b"
    SINGLE_PLUS = "1b+"
    DOUBLE = "2b"
    TRIPLE = "3b"
    HOMERUN = "hr"
    PITCHER_ADVANTAGE = "padv"
    HITTER_ADVANTAGE = "hadv"
    OUT = "out"
    SAFE = "safe"
    NONE = "na"

    @property
    def is_out(self):
        return self.name in ['PU','SO','GB','FB','OUT']
    
    @property
    def is_hit(self):
        return self.name in ['SINGLE','SINGLE_PLUS','DOUBLE','TRIPLE','HOMERUN']
    
    @property
    def is_advanceable(self):
        return self.name in ['FB'] or self.is_hit
    
    @property
    def count_as_pa(self):
        return self.name not in ['NONE']
    
    @property
    def count_as_ab(self):
        return self.name not in ['BB','NONE']

    @property
    def bases(self):
        match self.name:
            case 'SINGLE' | 'BB' | 'SINGLE_PLUS': return 1
            case 'DOUBLE': return 2
            case 'TRIPLE': return 3
            case 'HOMERUN': return 4
            case _: return 0