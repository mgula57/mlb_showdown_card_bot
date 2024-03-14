from enum import Enum
from aenum import MultiValueEnum
try:
    from .stat_highlights import StatHighlightsCategory, StatHighlightsType
except ImportError:
    from stat_highlights import StatHighlightsCategory, StatHighlightsType

class PlayerType(Enum):

    PITCHER = 'Pitcher'
    HITTER = 'Hitter'

    @classmethod
    def _missing_(cls, _):
        return cls.HITTER

    @property
    def is_pitcher(self) -> bool:
        return self.name == 'PITCHER'
    
    @property
    def is_hitter(self) -> bool:
        return self.name == 'HITTER'
    
    # ---------------------------------------
    # IMAGES
    # ---------------------------------------

    @property
    def template_color_04_05(self) -> str:
        return 'BLUE' if self.is_pitcher else 'GREEN'
    
    @property
    def override_user_input_substrings(self) -> list[str]:
        """List of allowable strings for the user to input to designate a type override."""
        match self.name:
            case "PITCHER": return ['PITCHER', 'PITCHING',]
            case "HITTER": return ['HITTER', 'HITTING',]
    
    @property
    def override_string(self) -> str:
        """Add parenthesis to the type"""
        return f"({self.name})"
        

class PlayerSubType(Enum):

    POSITION_PLAYER = 'position_player'
    STARTING_PITCHER = 'starting_pitcher'
    RELIEF_PITCHER = 'relief_pitcher'

    @property
    def is_pitcher(self) -> bool:
        return self.name in ['STARTING_PITCHER', 'RELIEF_PITCHER']

    @property
    def ip_under_5_negative_multiplier(self) -> float:
        return 1.5 if self.name == 'STARTING_PITCHER' else 1.0
    
    @property
    def nationality_chart_gradient_img_width(self) -> int:
        return 475 if self.value == 'position_player' else 680
    
    @property
    def pts_normalizer_cutoff(self) -> int:
        match self.name:
            case 'RELIEF_PITCHER': return 120
            case _: return 500

        
    # ---------------------------------------
    # STATS
    # ---------------------------------------

    def stat_highlight_categories(self, type: StatHighlightsType) -> list[StatHighlightsCategory]:
        match self:
            case PlayerSubType.STARTING_PITCHER | self.RELIEF_PITCHER:
                match type:
                    case StatHighlightsType.OLD_SCHOOL: return [
                        StatHighlightsCategory.W if self == self.STARTING_PITCHER else StatHighlightsCategory.SV,
                        StatHighlightsCategory.ERA,
                        StatHighlightsCategory.WHIP,
                        StatHighlightsCategory.IP,
                    ]
                    case StatHighlightsType.MODERN: return [
                        StatHighlightsCategory.ERA,
                        StatHighlightsCategory.FIP,
                        StatHighlightsCategory.bWAR,
                        StatHighlightsCategory.K_9,
                    ]
                    case StatHighlightsType.ALL: return [
                        StatHighlightsCategory.ERA,
                        StatHighlightsCategory.WHIP,
                        StatHighlightsCategory.IP,
                        StatHighlightsCategory.SV,
                        StatHighlightsCategory.K_9,
                        StatHighlightsCategory.bWAR,
                    ]
                    case _: return []
            case self.POSITION_PLAYER:
                match type:
                    case StatHighlightsType.OLD_SCHOOL: return [
                        StatHighlightsCategory.SLASHLINE,
                        StatHighlightsCategory.HR,
                        StatHighlightsCategory.SB,
                        StatHighlightsCategory.RBI,
                        StatHighlightsCategory._2B,
                        StatHighlightsCategory.H,
                        StatHighlightsCategory._3B,
                    ]
                    case StatHighlightsType.MODERN: return [
                        StatHighlightsCategory.bWAR,
                        StatHighlightsCategory.OPS_PLUS,
                        StatHighlightsCategory.DEFENSE,
                        StatHighlightsCategory.dWAR,
                        StatHighlightsCategory.HR,
                        StatHighlightsCategory.SLASHLINE,
                        StatHighlightsCategory.SB,
                        StatHighlightsCategory._2B,
                        StatHighlightsCategory._3B,
                        StatHighlightsCategory.H,
                    ]
                    case StatHighlightsType.ALL: return [
                        StatHighlightsCategory.SLASHLINE,
                        StatHighlightsCategory.OPS_PLUS,
                        StatHighlightsCategory.DEFENSE,
                        StatHighlightsCategory.bWAR,
                        StatHighlightsCategory.dWAR,
                        StatHighlightsCategory.HR,
                        StatHighlightsCategory.SB,
                        StatHighlightsCategory.RBI,
                        StatHighlightsCategory._2B,
                        StatHighlightsCategory._3B,
                        StatHighlightsCategory.H,
                    ]
                    case _: return []


class Position(MultiValueEnum):

    CA = 'C', 'CA'
    _1B = '1B'
    _2B = '2B'
    _3B = '3B'
    SS = 'SS'
    CF = 'CF'
    OF = 'OF'
    IF = 'IF'
    LFRF = 'LF/RF'
    DH = "DH"

    SP = "STARTER"
    RP = "RELIEVER"
    CL = "CLOSER"

    LF = "LF"
    RF = "RF"

    def value_visual(self, ca_position_name:str) -> str:
        match self.name:
            case 'CA': return ca_position_name
            case _: return self.value

    @property
    def ordering_index(self) -> int:
        match self.name:
            case 'CA': return 11
            case '_1B': return 9
            case '_2B': return 8
            case '_3B': return 7
            case 'SS': return 6
            case 'LFRF': return 5
            case 'CF': return 4
            case 'OF': return 3
            case 'IF': return 2
            case 'DH': return
            case 'SP': return 1
            case 'RP': return 1
            case 'CL': return 1
            case _: return 0

    @property
    def allowed_combinations(self) -> list[str]:
        match self.name:
            case '_2B': return ['SS','3B',]
            case '_3B': return ['SS','2B',]
            case 'SS': return ['2B','3B',]
            case _: return []

    @property
    def is_infield(self) -> bool:
        return self.name in ['_1B','_2B','_3B','SS',]
    
    @property
    def is_pitcher(self) -> bool:
        return self.name in ['SP','RP','CL']
    
    @property
    def is_hitter(self) -> bool:
        return not self.is_pitcher
    
    @property
    def is_valid_in_game(self) -> bool:
        return self.name not in ['LF', 'RF']
    
    def __repr__(self):
        return self.value