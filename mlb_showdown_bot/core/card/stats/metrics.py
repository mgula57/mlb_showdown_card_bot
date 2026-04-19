from enum import Enum

class DefenseMetric(Enum):

    OAA = 'oaa'
    DRS = 'drs'
    TZR = 'tzr'
    DWAR = 'dWAR'
    FLD_PCT = 'fld_pct'
    
    def range_min(self, position_str:str, set_str:str) -> float:
        """ Returns the minimum range value for the given position """
        multiplier = 1.0
        match position_str:
            case 'C':
                match set_str:
                    case '2000' | 'CLASSIC': multiplier = 1.1
            case '2B': 
                match set_str:
                    case '2000' | '2001'| 'CLASSIC': multiplier = 1.3
                    case '2004' | '2005' | 'EXPANDED': multiplier = 1.3
            case 'SS': 
                match set_str:
                    case '2000' | '2001' | 'CLASSIC': multiplier = 1.3
                    case '2004' | '2005' | 'EXPANDED': multiplier = 1.2
            case '3B': 
                match set_str:
                    case '2000' | '2001' | '2002' | 'CLASSIC': multiplier = 1.2
            case 'LF' | 'RF': 
                match set_str:
                    case '2000' | '2001' | 'CLASSIC': multiplier = 1.3
                    case '2002': multiplier = 1.1
            case 'OF': 
                match set_str:
                    case '2000' | '2001' | 'CLASSIC': multiplier = 1.3
            case 'CF':
                match set_str:
                    case '2000': multiplier = 1.3
                    case '2001' | 'CLASSIC': multiplier = 1.3
                    case '2002': multiplier = 1.5

        min_basis = -1 * self.range_max(position_str, set_str)
        match self:
            case DefenseMetric.DWAR:
                match position_str:
                    case 'LF' | 'RF' | 'CF': min_basis *= 1.5
                    case 'OF': min_basis *= 1.5
            case DefenseMetric.OAA:
                match position_str:
                    case 'LF' | 'RF': min_basis *= 1.3
            case DefenseMetric.FLD_PCT:
                match position_str: # DOESN'T USE MIN-BASE, JUST STATIC CUTOFFS
                    case 'C':              return 0.980
                    case '1B':             return 0.988
                    case '2B':             return 0.955
                    case '3B':             return 0.942
                    case 'SS':             return 0.950
                    case 'LF' | 'RF':     return 0.970
                    case 'CF':             return 0.978
                    case 'OF':             return 0.972
                    case _:                return 0.970
                
        return (min_basis * multiplier)

    def range_max(self, position_str:str, set_str:str) -> float:
        """ Returns the maximum range value for the given position """
        multiplier = 1.0
        match position_str:
            case 'C': 
                match set_str:
                    case '2004' | '2005' | 'EXPANDED': multiplier = 1.25
                    case _: multiplier = 1.3
            case '2B': 
                match set_str:
                    case '2000' | '2001' | 'CLASSIC': multiplier = 1.4
                    case '2004' | '2005' | 'EXPANDED': multiplier = 1.3
            case 'SS':
                match set_str:
                    case '2000' | '2001' | 'CLASSIC': multiplier = 1.4
                    case '2003': multiplier = 1.2
                    case '2004' | '2005' | 'EXPANDED': multiplier = 1.3
            case '3B': 
                match set_str:
                    case '2000' | '2001' | '2002' | 'CLASSIC': multiplier = 1.2
            case 'LF' | 'RF': 
                match set_str:
                    case '2000' | '2001' | '2002' | 'CLASSIC': multiplier = 1.3
            case 'OF': 
                match set_str:
                    case '2000' | '2001' | '2002' | 'CLASSIC': multiplier = 1.3
            case 'CF':
                match set_str:
                    case '2000' | '2001' | '2002' | 'CLASSIC': multiplier = 1.3
        match self:
            case DefenseMetric.OAA:
                match position_str:
                    case 'LF' | 'RF' | 'OF': basis = 10
                    case _: basis = 16
                return basis * multiplier
            case DefenseMetric.DRS: return 19 * multiplier
            case DefenseMetric.TZR: return 17 * multiplier
            case DefenseMetric.DWAR: 
                match position_str:
                    case 'C': basis = 2.25
                    case 'LF' | 'RF' | 'CF' | 'OF': basis = 1.25
                    case _: basis = 2.0
                return basis * multiplier
            case DefenseMetric.FLD_PCT:
                match position_str:
                    case 'C':          return 1.000
                    case '1B':         return 1.000
                    case '2B':         return 0.994
                    case '3B':         return 0.978
                    case 'SS':         return 0.989
                    case 'LF' | 'RF':  return 0.998
                    case 'CF':         return 0.999
                    case 'OF':         return 0.998
                    case _:            return 0.994

    def range_total_values(self, position_str:str, set_str:str) -> float:
        return self.range_max(position_str, set_str) - self.range_min(position_str, set_str)

    @property
    def is_rate_stat(self) -> bool:
        """ Returns True if the metric is a rate stat (like fielding percentage) rather than a counting stat (like OAA) """
        return self in {DefenseMetric.FLD_PCT}

    @property
    def first_base_plus_2_cutoff(self) -> float:
        """ For 1B, use a static cutoff instead of range """
        match self.value:
            case 'oaa': return 13
            case 'drs': return 17
            case 'tzr': return 16
            case 'dWAR': return 1.5
            case 'fld_pct': return 1.001 # MAKE IMPOSSIBLE TO GET +2 FOR FLD_PCT SINCE IT'S A RATE STAT

    @property
    def first_base_plus_1_cutoff(self) -> int:
        """ For 1B, use a static cutoff instead of range """
        match self.value:
            case 'oaa': return 2
            case 'drs': return 4
            case 'tzr': return 4
            case 'dWAR': return -0.25
            case 'fld_pct': return 0.992
    
    @property
    def first_base_minus_1_cutoff(self) -> float:
        """ For 1B, use a static cutoff instead of range. -1 1B defense only applies to 2022 set and beyond."""
        match self.value:
            case 'oaa': return -5
            case 'drs': return -5
            case 'tzr': return -5
            case 'dWAR': return -1.0
            case 'fld_pct': return 0.975
    
    @property
    def over_max_multiplier(self) -> float:
        """ Reduces outliers in OAA by reducing values over the defense maximum """
        return 0.5 if self == DefenseMetric.OAA else 0.85
    
class Stat(Enum):

    BA = 'batting_avg'
    OBP = 'onbase_perc'
    SLG = 'slugging_perc'
    OPS = 'onbase_plus_slugging'
    COMMAND = 'command'

    # USED FOR TOTALS
    OVERALL = 'overall'
