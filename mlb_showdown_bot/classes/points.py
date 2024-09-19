from pydantic import BaseModel
from typing import Optional

class Points(BaseModel):

    ba: float = 0.0
    obp: float = 0.0
    slg: float = 0.0
    hr: float = 0.0
    defense: float = 0.0
    speed: float = 0.0
    ip: float = 0.0
    icons: float = 0.0
    out_distribution: float = 0.0
    bonus: float = 0.0
    command: float = 0.0

    command_out_multiplier: float = 1.0
    position_multiplier: float = 0.0
    normalizer: float = 1.0
    allow_negatives: bool = False
    multi_inning_mutliplier: float = 1.0
    
    @property
    def total_points(self) -> int:
        
        # POINTS ARE ALWAYS ROUNDED TO NEAREST TENTH
        points_to_nearest_tenth = int(round(self.total_points_unrounded,-1))

        # POINTS CANNOT BE < 10
        points_final = 10 if points_to_nearest_tenth < 10 else points_to_nearest_tenth

        return points_final
    
    @property
    def total_points_unrounded(self):
        return ((self.ba + self.obp + self.slg + self.hr + self.defense + self.speed + self.ip + self.icons + self.bonus + self.command) * self.multi_inning_mutliplier ) + self.out_distribution
    
    @property
    def breakdown_str(self) -> str:
        """Strings with list of all points categories"""
        
        breakdown_categories = ['ba','obp','slg','hr','defense','speed','ip','icons','out_distribution','bonus','command',]
        other_attributes = ['command_out_multiplier', 'normalizer', 'multi_inning_mutliplier']
        all_categories = breakdown_categories + other_attributes
        return "  ".join(f"{cat.replace('_',' ').upper()}:{round(getattr(self, cat, 0), 2)}" for cat in all_categories if (getattr(self, cat, 0) != 1.0 if cat in other_attributes else True))
    
    def apply_decay(self, is_hitter:bool, decay_rate_and_start: Optional[float]):
        
        # DECAY RATE
        if decay_rate_and_start is None:
            return
        
        # PROCEED IF POINTS ARE > START
        decay_rate, points_start = decay_rate_and_start
        if self.total_points_unrounded <= points_start:
            return
        
        # CALCULATE AMOUNT TO REDUCE BY 
        total_above_start = self.total_points_unrounded - points_start
        total_points_after_decay = points_start + ( total_above_start * decay_rate )
        total_points_to_reduce = self.total_points_unrounded - total_points_after_decay

        # APPLY DECAY RATE TO SLASHLINES
        categories = ['ba','obp','slg',] + ['hr'] if is_hitter else []
        total_across_categories = sum(getattr(self, category, 0) for category in categories)
        for category in categories:
            current_category_points = getattr(self, category, 0)
            points_pct_of_total = current_category_points / total_across_categories
            points_to_reduce = total_points_to_reduce * points_pct_of_total
            setattr(self, category, round(current_category_points - points_to_reduce, 3))

        