from enum import Enum

class StatHighlightsType(Enum):
    NONE = 'NONE'
    OLD_SCHOOL = 'OLD_SCHOOL'
    MODERN = 'MODERN'
    ALL = 'ALL'

    @property
    def has_image(self) -> bool:
        return self != StatHighlightsType.NONE

class StatHighlightsCategory(Enum):

    IP = 'IP'
    ERA = 'ERA'
    WHIP = 'WHIP'
    K_9 = 'K/9'
    SV = 'SV'
    FIP = 'FIP'
    W = 'W'

    SLASHLINE = 'Slashline'
    HR = 'HR'
    OPS_PLUS = 'OPS+'
    DEFENSE = "Defense"
    dWAR = 'dWAR'
    bWAR = 'bWAR'
    SB = 'SB'
    RBI = 'RBI'
    H = 'H'
    _2B = '2B'
    _3B = '3B'

    @property
    def stat_key_list(self) -> list[str]:
        match self:
            case StatHighlightsCategory.SLASHLINE: return ['batting_avg','onbase_perc','slugging_perc']
            case StatHighlightsCategory.OPS_PLUS: return ['onbase_plus_slugging_plus']
            case StatHighlightsCategory.ERA: return ['earned_run_avg']
            case StatHighlightsCategory.K_9: return ['strikeouts_per_nine']
            case StatHighlightsCategory.FIP: return ['fip']
            case StatHighlightsCategory.WHIP: return ['whip']
            case StatHighlightsCategory.DEFENSE: return ['oaa', 'drs', 'tzr',]
            case _: return [self.value]

    @property
    def visibility_threshold(self) -> float | int:
        match self:
            case StatHighlightsCategory.SB: return 20
            case StatHighlightsCategory.RBI: return 85
            case StatHighlightsCategory.HR: return 18
            case StatHighlightsCategory._2B: return 25
            case StatHighlightsCategory._3B: return 7
            case StatHighlightsCategory.SV: return 20
            case _: return None
