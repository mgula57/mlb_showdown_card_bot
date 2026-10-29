from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class Season(BaseModel):
    
    season_id: int | str = Field(..., alias='seasonId')
    has_wildcard: Optional[bool] = Field(None, alias='hasWildcard')
    regular_season_start_date: Optional[str] = Field(None, alias='regularSeasonStartDate')
    regular_season_end_date: Optional[str] = Field(None, alias='regularSeasonEndDate')
    post_season_start_date: Optional[str] = Field(None, alias='postSeasonStartDate')
    post_season_end_date: Optional[str] = Field(None, alias='postSeasonEndDate')
    season_end_date: Optional[str] = Field(None, alias='seasonEndDate')

    # Not from the MLB API: set by /seasons/list once the World Series has a winner, which is
    # usually before season_end_date (that's the scheduled Game 7 date).
    postseason_complete: bool = False
