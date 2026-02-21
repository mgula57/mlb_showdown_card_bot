from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Sport(BaseModel):
    """Sport information"""
    id: int
    link: Optional[str] = None

class SportEnum(int, Enum):
    MLB = 1
    INTERNATIONAL = 51

class SeasonDateInfo(BaseModel):
    """Season date information for league"""
    game_level_gameday_type: Optional[str] = Field(None, alias='gameLevelGamedayType')
    off_season_end_date: Optional[str] = Field(None, alias='offSeasonEndDate')
    offseason_start_date: Optional[str] = Field(None, alias='offseasonStartDate')
    pre_season_end_date: Optional[str] = Field(None, alias='preSeasonEndDate')
    pre_season_start_date: Optional[str] = Field(None, alias='preSeasonStartDate')
    season_id: Optional[str] = Field(None, alias='seasonId')
    season_level_gameday_type: Optional[str] = Field(None, alias='seasonLevelGamedayType')
    season_start_date: Optional[str] = Field(None, alias='seasonStartDate')
    spring_end_date: Optional[str] = Field(None, alias='springEndDate')
    spring_start_date: Optional[str] = Field(None, alias='springStartDate')
    
    class Config:
        populate_by_name = True

    @property
    def is_currently_spring(self) -> bool:
        """Determine if the current date is within the spring training period for this season"""
        from datetime import datetime
        
        if self.spring_start_date and self.spring_end_date:
            try:
                spring_start = datetime.strptime(self.spring_start_date, "%Y-%m-%d").date()
                spring_end = datetime.strptime(self.spring_end_date, "%Y-%m-%d").date()
                today = datetime.today().date()
                return spring_start <= today <= spring_end
            except ValueError:
                # If date parsing fails, assume not in spring
                return False
        return False

class League(BaseModel):
    """Complete league model with all MLB Stats API fields"""
    
    # Core identification
    id: int
    name: str
    abbreviation: Optional[str] = None
    name_short: Optional[str] = Field(None, alias='nameShort')
    org_code: Optional[str] = Field(None, alias='orgCode')
    link: Optional[str] = None
    
    # Status and configuration
    active: bool = True
    season: Optional[str] = None
    season_state: Optional[str] = Field(None, alias='seasonState')
    sort_order: Optional[int] = Field(None, alias='sortOrder')
    
    # League capabilities/features
    conferences_in_use: bool = Field(False, alias='conferencesInUse')
    divisions_in_use: bool = Field(False, alias='divisionsInUse')
    has_playoff_points: bool = Field(False, alias='hasPlayoffPoints')
    has_split_season: bool = Field(False, alias='hasSplitSeason')
    has_wild_card: bool = Field(False, alias='hasWildCard')
    
    # Related data
    season_date_info: Optional[SeasonDateInfo] = Field(None, alias='seasonDateInfo')
    sport: Optional[Sport] = None
    
    class Config:
        populate_by_name = True

    @property
    def is_spring_league(self) -> bool:
        """Determine if this league is a spring training league based on its abbreviation"""
        return self.abbreviation in ['GL', 'CL']
    
    @property
    def has_showdown_cards(self) -> bool:
        """Whether there are Showdown Cards able to be pulled for this league"""
        # For simplicity, we'll say that any active league in the regular season or later should have showdown cards
        return self.abbreviation in [
            'AL',
            'NL',
            'WBC', # DOESN'T ACTUALLY HAVE SHOWDOWN CARDS YET BUT LIKELY WILL IN THE FUTURE
            'NNL',
            'NN2',
            'ECL',
            'NAL',
            'AA',
            'NSL',
            'PL',
            'UA',
            'EWL',
            'ANL',
            'FL',
        ]

