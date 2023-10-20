
from enum import Enum

class Icon(Enum):

    # HITTER
    S = "S"
    G = "G"
    HR = "HR"
    SB = "SB"

    # PITCHER
    CY = "CY"
    _20 = "20"
    K = "K"
    RP = "RP"

    # BOTH
    V = "V"
    R = "R"
    RY = "RY"

    @property
    def stat_category(self) -> str:
        match self.value:
            case 'K': return 'SO'
            case 'RP': return 'SV'
            case 'HR': return 'HR'
            case 'SB': return 'SB'
            case "20": return "W"
            case _: return None

    @property
    def accolade_search_term(self) -> str:
        match self.value:
            case 'K': return 'SO'
            case 'RP': return 'SAVES'
            case 'HR': return 'HR'
            case 'SB': return 'SB'
            case _: return None
    
    @property
    def award_str(self) -> str:
        match self.value:
            case 'S': return 'SS'
            case 'G': return 'GG'
            case 'V': return 'MVP-1'
            case 'CY': return 'CYA-1'
            case 'RY': return 'ROY-1'
            case _: return None

    @property
    def is_stat_based(self) -> bool:
        return self.stat_category is not None
    
    @property
    def is_league_leader_based(self) -> bool:
        return self.value in ['K', 'RP', 'HR', 'SB']
    
    @property
    def is_award_based(self) -> bool:
        return self.award_str is not None
    
    @property
    def stat_value_requirement(self) -> int:
        match self.value:
            case "20": return 20
            case _: return None

    def is_available(self, is_pitcher:bool) -> bool:
        if is_pitcher:
            return self.value in ['G','CY','20','K','RP','V','R','RY',]
        else:
            return self.value in ['S','G','HR','SB','V','R','RY',]

    @property
    def points(self) -> int:
        match self.value:
            case 'R': return 0
            case 'G' | 'S' | 'SB' | 'RY' | 'RP' | 'K' | '20': return 15
            case 'V' | 'HR' | 'CY': return 20
            case _: return 0
