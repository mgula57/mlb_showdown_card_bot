from enum import Enum
from pydantic import BaseModel, validator
from datetime import date, datetime
from typing import Optional

class StatsPeriodType(str, Enum):

    REGULAR_SEASON = "REGULAR"
    DATE_RANGE = "DATES"
    POSTSEASON = "POST"
    SPLIT = "SPLIT"

    @property
    def uses_game_logs(self) -> bool:
        return self in [StatsPeriodType.DATE_RANGE, StatsPeriodType.POSTSEASON]

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

    @property
    def show_text_on_card_image(self) -> bool:
        return self not in [StatsPeriodType.REGULAR_SEASON]
    
    @property
    def is_regular_season_games_stat_needed(self) -> bool:
        return self not in [StatsPeriodType.REGULAR_SEASON]


class StatsPeriod(BaseModel):

    # ATTRIBUTES
    type: StatsPeriodType = StatsPeriodType.REGULAR_SEASON

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
            self.split = self.split.strip()
            if len(self.split) == 0:
                self.split = None
        

    @property
    def id(self) -> str:
        values = [self.type.value, self.start_date, self.end_date, self.split]
        return "-".join([str(v).replace('/','-') for v in values if v is not None])
    
    @property
    def is_date_range(self) -> bool:
        return self.start_date and self.end_date
    
    @property
    def string(self) -> str:
        match self.type:
            case StatsPeriodType.REGULAR_SEASON: return "REGULAR SEASON"
            case StatsPeriodType.DATE_RANGE:
                dates_formatted_list = [datetime.combine(dt, datetime.min.time()).strftime("%b %d") for dt in [self.start_date, self.end_date]]
                dates_split = " to ".join(dates_formatted_list)
                if len(dates_formatted_list) == 2:
                    if dates_formatted_list[0] == dates_formatted_list[1]:
                        return f"{dates_formatted_list[0]}"
                return f"{dates_split}"
            case StatsPeriodType.POSTSEASON: return f"POSTSEASON"
            case StatsPeriodType.SPLIT: return f"SPLIT ({self.split or 'N/A'})"
    
    @property
    def empty_message(self) -> str:
        match self.type:
            case StatsPeriodType.REGULAR_SEASON: return "No regular season data available"
            case StatsPeriodType.DATE_RANGE: return f"No data found from {self.string.replace('(', '').replace(')','')}"
            case StatsPeriodType.POSTSEASON: return f"No postseason data available"
            case StatsPeriodType.SPLIT: return f"Split '{self.split or 'N/A'}' not found"

    def reset(self) -> None:
        self.type = StatsPeriodType.REGULAR_SEASON
        self.start_date = None
        self.end_date = None
        self.split = None
