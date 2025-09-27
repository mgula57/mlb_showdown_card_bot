from pydantic import BaseModel
from typing import Optional
from enum import Enum

# INTERNAL
from .utils.value_range import ValueRange

class PointsMetric(Enum):

    DEFENSE = 'defense'
    SPEED = 'speed'
    ONBASE = 'onbase'
    AVERAGE = 'average'
    SLUGGING = 'slugging'
    HOME_RUNS = 'home_runs'
    IP = 'ip'
    ICON = 'icon'
    OUT_DISTRIBUTION = 'out_distribution'
    COMMAND = 'command'

    @property
    def abbreviation(self) -> str:
        match self.name:
            case 'DEFENSE': return 'DEF'
            case 'SPEED': return 'SPD'
            case 'ONBASE': return 'OBP'
            case 'AVERAGE': return 'AVG'
            case 'SLUGGING': return 'SLG'
            case 'HOME_RUNS': return 'HR'
            case 'IP': return 'IP'
            case 'ICON': return 'ICON'
            case 'OUT_DISTRIBUTION': return 'OUT DIST'
            case 'COMMAND': return 'CMD'
            case _: return None

    @property
    def metric_name_bref(self) -> str:
        match self.name:
            case 'ONBASE': return 'onbase_perc'
            case 'AVERAGE': return 'batting_avg'
            case 'SLUGGING': return 'slugging_perc'
            case 'HOME_RUNS': return 'HR'
            case _: return None

    @property
    def is_effected_by_decay(self) -> bool:
        return self in [PointsMetric.ONBASE, PointsMetric.AVERAGE, PointsMetric.SLUGGING, PointsMetric.HOME_RUNS]

    @property
    def show_asterisk_in_pts_breakdown(self) -> bool:
        return self in [PointsMetric.ONBASE, PointsMetric.AVERAGE, PointsMetric.SLUGGING, PointsMetric.HOME_RUNS,]
    
class PointsBreakdown(BaseModel):
    
    metric: PointsMetric
    metric_category: Optional[str] = None
    points: float = 0.0
    possible_points: float = 0.0
    value: float | int = 0.0
    value_range: ValueRange = ValueRange(min=0.0, max=0.0)
    percentile: float = 0.0
    is_desc: bool = False

    adjustment: float = 0.0
    ip_multiplier: float = 1.0
    command_multiplier: float = 1.0

    @property
    def value_formatted(self) -> str:
        en_dash = '—'
        match self.metric:
            case PointsMetric.DEFENSE:
                if self.metric_category in ['CLOSER', 'DH']:
                    return en_dash
                return f'{self.value:+}'
            case PointsMetric.ONBASE | PointsMetric.SLUGGING | PointsMetric.AVERAGE: 
                return str(round(self.value,3)).replace('0.','.')
            case PointsMetric.ICON: return self.metric_category
            case PointsMetric.OUT_DISTRIBUTION: return f'{self.value * 100:.1f}%'
            case PointsMetric.HOME_RUNS: return f'{self.value:.0f}'
            case _: return f'{self.value}'
    
    @property
    def percentile_formatted(self) -> str:
        if self.metric == PointsMetric.ICON:
            return '—'
        return f'{self.percentile:.0%}'

    @property
    def metric_and_category_name(self) -> str:
        if self.metric == PointsMetric.DEFENSE:
            return self.metric_category if self.metric_category in ['CLOSER', 'DH'] else f'{self.metric.abbreviation} ({self.metric_category})'
        if self.metric == PointsMetric.ICON:
            return f"{self.metric_category} ICON"
        return self.metric.abbreviation


class Points(BaseModel):

    breakdowns: dict[str, PointsBreakdown] = {}

    command_out_multiplier: float = 1.0
    decay_rate: float = 1.0
    decay_start: int = 0
    allow_negatives: bool = False
    ip_multiplier: float = 1.0
    
    @property
    def total_points(self) -> int:
        
        # POINTS ARE ALWAYS ROUNDED TO NEAREST TENTH
        points_to_nearest_tenth = int(round(self.total_points_unrounded,-1))

        # POINTS CANNOT BE < 10
        points_final = 10 if points_to_nearest_tenth < 10 else points_to_nearest_tenth

        return points_final
    
    @property
    def total_points_unrounded(self) -> float:
        return sum([breakdown.points for breakdown in self.breakdowns.values()]) if len(self.breakdowns) > 0 else 0
    
    @property
    def breakdown_str(self) -> str:
        """Strings with list of all points categories"""
        
        category_summary = ' | '.join([f'{breakdown.metric_and_category_name}: {breakdown.points}' for breakdown in self.breakdowns.values()])
        decay_summary = f'DECAY: {round(self.decay_rate * 100)}% @({self.decay_start})' if self.decay_rate != 1.0 else ''
        ip_multiplier_summary = f'IPx: {self.ip_multiplier}' if self.ip_multiplier != 1.0 else ''
        return ' | '.join([category_summary, decay_summary, ip_multiplier_summary]).replace('|  |', '|')
    
    def add_breakdown(self, breakdown: PointsBreakdown, id_suffix: str = None) -> None:
        """Store a new breakdown in self.breakdowns
        
        Args:
            breakdown: PointsBreakdown object to store.
            id_suffix: Optional string to append to the breakdown ID.

        Returns:
            None
        """
        suffix = '-' + id_suffix if id_suffix else ""
        id = f'{breakdown.metric.name}{suffix}'
        self.breakdowns[id] = breakdown

    def apply_multi_position_adjustment(self, is_pitcher:bool, use_max_for_defense:bool = False) -> None:
        """Apply adjustment for multi-position players. 2000/2001 set take max defense, 2002+ take average defense.

        Args:
            use_max_for_defense: Boolean flag for whether to use max defense for points calculation.

        Returns:
            None
        """
        # PITCHERS CAN'T BE MULTI-POSITION
        if is_pitcher: 
            return
        
        # CHECK FOR MULTI-POSITION
        defense_breakdowns = {id: breakdown for id, breakdown in self.breakdowns.copy().items() if breakdown.metric == PointsMetric.DEFENSE}
        num_defense_breakdowns = len(defense_breakdowns)
        if num_defense_breakdowns <= 1:
            return
        
        # GET MAX OR AVERAGE DEFENSE
        if use_max_for_defense:

            # CALCULATE MAX DEFENSE BREAKDOWN
            top_position_breakdown = max(defense_breakdowns.values(), key=lambda x: x.points)

            # ADJUST DEFENSE FOR ALL BREAKDOWNS NOT ON TOP
            for id, breakdown in defense_breakdowns.items():
                if breakdown != top_position_breakdown:
                    breakdown.adjustment = -1 * breakdown.points
                    breakdown.points = 0
                    self.breakdowns[id] = breakdown

        else:
            # GET TOTAL POINTS AND TOTAL NUMBERS OF POSITIONS W NON-ZERO DEFENSE
            total_points = sum(breakdown.points for breakdown in defense_breakdowns.values())
            positions_w_non_zero_def = sorted([breakdown.metric_category for breakdown in defense_breakdowns.values() if breakdown.value != 0], key=lambda x: x)
            
            # DENIMINATOR FOR AVERAGE IS LOWER THAN TRUE AVG
            # THIS MEANS THE AVERAGE WILL BE HIGHER THAN THE TRUE AVERAGE
            use_true_avg = positions_w_non_zero_def == ['CF', 'LF/RF']
            num_positions_w_non_zero_def = 2 if use_true_avg else len(positions_w_non_zero_def)
            num_positions = max(num_positions_w_non_zero_def, 1)
            denominator = num_positions if num_positions < 2 or use_true_avg else ( (num_positions + 2) / 3.0 )
            new_total_positions_pts = round(total_points / denominator, 3)

            # APPLY ACROSS ALL POSITIONS
            for id, breakdown in defense_breakdowns.items():
                avg_points_across_points = round(new_total_positions_pts / len(defense_breakdowns), 3)
                breakdown.adjustment = avg_points_across_points - breakdown.points
                breakdown.points = avg_points_across_points
                self.breakdowns[id] = breakdown

    def apply_ip_multiplier(self, multiplier:float) -> None:
        """Apply IP multiplier to points categories. Used to adjust points for pitchers with very high or very low IP.
        
        Args:
            multiplier: Multiplier to apply to IP categories.

        Returns:
            None
        """

        if multiplier == 1.0:
            return
        
        self.ip_multiplier = multiplier
        updated_breakdowns = self.breakdowns.copy()
        for id, breakdown in updated_breakdowns.items():
            if breakdown.metric == PointsMetric.OUT_DISTRIBUTION:
                continue
            
            breakdown.points = round(breakdown.points * multiplier, 3)
            breakdown.ip_multiplier = multiplier
            
            self.breakdowns[id] = breakdown
            

    def apply_decay(self, decay_rate_and_start: Optional[tuple[float, int]] = None) -> None:
        """Apply decay rate to points categories. Used to keep points in check for high point totals.
        
        Args:
            decay_rate_and_start: Tuple of decay rate and points start for applying decay.

        Returns:
            None
        """

        # DECAY RATE
        if decay_rate_and_start is None:
            return
        
        # PROCEED IF POINTS ARE > START
        decay_rate, points_start = decay_rate_and_start
        if self.total_points_unrounded <= points_start:
            return
        
        # STORE IN SELF
        self.decay_rate = decay_rate
        self.decay_start = points_start
        
        # CALCULATE AMOUNT TO REDUCE BY 
        total_above_start = self.total_points_unrounded - points_start
        total_points_after_decay = points_start + ( total_above_start * decay_rate )
        total_points_to_reduce = self.total_points_unrounded - total_points_after_decay

        # APPLY DECAY RATE TO SLASHLINES
        breakdowns_to_decay = {id: breakdown for id, breakdown in self.breakdowns.copy().items() if breakdown.metric.is_effected_by_decay}
        if len(breakdowns_to_decay) == 0:
            return
        total_across_categories = sum([breakdown.points for breakdown in breakdowns_to_decay.values()])
        for id, breakdown in breakdowns_to_decay.items():
            current_pts = breakdown.points
            points_pct_of_total = current_pts / total_across_categories
            points_to_reduce = round(total_points_to_reduce * points_pct_of_total, 3)
            breakdown.adjustment = round(breakdown.adjustment - points_to_reduce, 3)
            breakdown.points = round(breakdown.points - points_to_reduce, 3)
            self.breakdowns[id] = breakdown

        