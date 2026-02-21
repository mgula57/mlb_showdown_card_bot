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
