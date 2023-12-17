from enum import Enum
from pydantic import BaseModel, validator
from datetime import date, datetime
from typing import Optional

class StatsPeriodType(str, Enum):

    FULL_SEASON = "FULL"
    DATE_RANGE = "DATES"
    POSTSEASON = "POST"
    SPLIT = "SPLIT"

    @property
    def uses_game_logs(self) -> bool:
        return self.name in ['DATE_RANGE', 'POSTSEASON']

    @property
    def enable_date_range(self) -> bool:
        return self.name in ['DATE_RANGE']
    
    @property
    def enable_split(self) -> bool:
        return self.name in ['SPLIT']
    
    @property
    def player_image_search_term(self) -> str:
        match self:
            case StatsPeriodType.POSTSEASON: return "(POST)"
            case _: return None


class StatsPeriod(BaseModel):

    # ATTRIBUTES
    type: StatsPeriodType = StatsPeriodType.FULL_SEASON

    # DATE RANGE
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # SPLIT
    split: Optional[str] = None

    def __init__(self, **data) -> None:

        super().__init__(**data)

        # VALIDATE ATTRIBUTES
        if not self.type.enable_date_range:
            self.start_date = None
            self.end_date = None

        if not self.type.enable_split:
            self.split = None

        if self.split:
            if len(self.split) == 0:
                self.split = None
        

    @property
    def id(self) -> str:
        values = [self.type.value, self.start_date, self.end_date, self.split]
        return "-".join([str(v) for v in values if v is not None])
    
    @property
    def is_date_range(self) -> bool:
        return self.start_date and self.end_date
    
    @property
    def string(self) -> str:
        match self.type:
            case StatsPeriodType.FULL_SEASON: return "FULL SEASON"
            case StatsPeriodType.DATE_RANGE:
                dates_formatted_list = [datetime.combine(dt, datetime.min.time()).strftime("%b %d") for dt in [self.start_date, self.end_date]]
                dates_split = " to ".join(dates_formatted_list)
                return f"({dates_split})"
            case StatsPeriodType.POSTSEASON: return f"POSTSEASON"
            case StatsPeriodType.SPLIT: return f"SPLIT ({self.split or 'N/A'})"
