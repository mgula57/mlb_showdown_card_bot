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

    class Config:  
        use_enum_values = True
    
    @property
    def total_points(self) -> int:
        points_unrounded = (self.ba + self.obp + self.slg + self.hr + self.defense + self.speed + self.ip + self.icons + self.out_distribution + self.bonus) * self.multi_inning_mutliplier
        
        # POINTS ARE ALWAYS ROUNDED TO NEAREST TENTH
        points_to_nearest_tenth = int(round(points_unrounded,-1))

        # POINTS CANNOT BE < 10
        points_final = 10 if points_to_nearest_tenth < 10 else points_to_nearest_tenth

        return points_final
    