from enum import Enum

class StatHighlightsType(Enum):
    NONE = 'NONE'
    CLASSIC = 'CLASSIC'
    MODERN = 'MODERN'
    ALL = 'ALL'

    @property
    def has_image(self) -> bool:
        return self != StatHighlightsType.NONE

class StatHighlightsCategory(Enum):

    G = 'G'
    GS = 'GS'

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
    def sort_rating_multiplier(self) -> float:
        match self:
            case StatHighlightsCategory.SLASHLINE: return 5.0
            case StatHighlightsCategory.ERA: return 5.0
            case StatHighlightsCategory.WHIP: return 3.0
            case StatHighlightsCategory.G: return 10.0
            case StatHighlightsCategory.GS: return 10.0
            case StatHighlightsCategory.IP: return 2.0
            case StatHighlightsCategory.OPS_PLUS: return 2.0
            case StatHighlightsCategory.RBI: return 0.85
            case StatHighlightsCategory.SV: return 1.1
            case StatHighlightsCategory.bWAR: return 1.1
            case _: return 1.0

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
    def cutoff_for_positive_sort_rating(self) -> float | int:
        """Value for a player to qualify for 1.0 sort rating"""
        match self:
            case StatHighlightsCategory.SB: return 17
            case StatHighlightsCategory.RBI: return 85
            case StatHighlightsCategory.HR: return 20
            case StatHighlightsCategory._2B: return 30
            case StatHighlightsCategory._3B: return 6
            case StatHighlightsCategory.SV: return 20
            case StatHighlightsCategory.H: return 170
            case StatHighlightsCategory.W: return 10
            case StatHighlightsCategory.K_9: return 8.5
            case StatHighlightsCategory.FIP: return 3.5
            case StatHighlightsCategory.bWAR: return 5.0
            case StatHighlightsCategory.dWAR: return 0.5
            case _: return None

    @property
    def is_pa_metric(self) -> bool:
        return self in [
            StatHighlightsCategory.HR,
            StatHighlightsCategory.SB,
            StatHighlightsCategory.RBI,
            StatHighlightsCategory.H,
            StatHighlightsCategory._2B,
            StatHighlightsCategory._3B,
        ]
    
    @property
    def is_lower_better(self) -> bool:
        return self in [
            StatHighlightsCategory.ERA,
            StatHighlightsCategory.WHIP,
            StatHighlightsCategory.FIP,
        ]
