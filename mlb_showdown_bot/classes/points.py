from pydantic import BaseModel

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

    command_out_multiplier: float = 1.0
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
        return ((self.ba + self.obp + self.slg + self.hr + self.defense + self.speed + self.ip + self.icons + self.bonus) * self.multi_inning_mutliplier ) + self.out_distribution
    
    @property
    def breakdown_str(self) -> str:
        """Strings with list of all points categories"""
        
        breakdown_categories = ['ba','obp','slg','hr','defense','speed','ip','icons','out_distribution','bonus',]
        other_attributes = ['command_out_multiplier', 'normalizer', 'multi_inning_mutliplier']
        all_categories = breakdown_categories + other_attributes
        return "  ".join(f"{cat.replace('_',' ').upper()}:{round(getattr(self, cat, 0), 2)}" for cat in all_categories if getattr(self, cat, 0) != (1.0 if cat in other_attributes else 0.0) )
    