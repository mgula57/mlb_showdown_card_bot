from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import date

# Models
from .generic import EnumGeneric, XRefIdData
from .position import Position
from .teams.team import Team
from .stats.stats import StatGroup, StatSplit
from .stats.enums import StatGroupEnum, StatTypeEnum
from .stats.awards import Award

class Person(BaseModel):
    
    # Basic identification
    id: int
    full_name: Optional[str] = Field(None, alias='fullName')
    first_name: Optional[str] = Field(None, alias='firstName')
    last_name: Optional[str] = Field(None, alias='lastName')
    
    # Personal information
    birth_state_province: Optional[str] = Field(None, alias='birthStateProvince')
    birth_country: Optional[str] = Field(None, alias='birthCountry')
    nationality: Optional[str] = None

    # Calculated fields for compliance with old data source
    mlb_url: Optional[str] = None 


class Player(Person):
    """Extended Person model for players with additional fields"""
    
    # Hydrations
    # Additional fields can be added here based on the hydrations used in the API requests
    stats: Optional[List[StatGroup]] = None
    awards: Optional[List[Award]] = None
    current_team: Optional[Team] = Field(None, alias='currentTeam')
    xref_ids: Optional[List[XRefIdData]] = Field(None, alias='xrefIds')

    # Other endpoints for more context
    active: Optional[bool] = None
    primary_position: Optional[Position] = Field(None, alias='primaryPosition')
    rookie_seasons: Optional[List[str]] = Field(None, alias='rookieSeasons')

    # Stats
    positions: Optional[Dict[str, Any]] = None # EX: {'SS': {'position': 'Shortstop', 'gamesPlayed': 120}, ...}
    rankings: Optional[Dict[str, Any]] = None # EX: 5TH IN 2025 NL HRS 

    bat_side: Optional[EnumGeneric] = Field(None, alias='batSide') # EX: Left, Right
    pitch_hand: Optional[EnumGeneric] = Field(None, alias='pitchHand') # EX: Left, Right

    # Missing Attributes
    # WAR (bWAR, dWAR)
    # Nationality Abbreviation
    # OPS+ (have wRC+ instead in sabermetrics)
    # Thresholds (hr, so, sb, w)
    # Leader (hr, sb, so)
    # Defensive Metrics (DRS, TZR, OAA)

    def model_post_init(self, __context):
        """Post-init processing to set calculated fields"""
        self.mlb_url = f"https://www.mlb.com/player/{self.id}"

    # -------------------------------

    def get_stat_splits(self, group_type: StatGroupEnum, type: StatTypeEnum, seasons: list[str | int]) -> Optional[List[StatSplit]]:
        """Retrieve a specific StatsGroup by type"""
        
        # Check if stats are available
        if not self.stats:
            print(f"No stats available for player in seasons: {seasons}")
            return None
        
        # Find the correct stats group
        final_list: List[StatSplit] = []
        for stats_group in self.stats:
            # print(f"Checking stats group: {stats_group.group.display_name} = {group_type.value} | {stats_group.type.display_name} = {type.value}")
            if stats_group.group.display_name == group_type.value and stats_group.type.display_name == type.value:

                for split in stats_group.splits:
                    is_included = group_type == StatTypeEnum.CAREER or int(split.season) in seasons
                    if is_included:
                        final_list.append(split)

        if not final_list or len(final_list) == 0:
            print(f"No stats found for group type: {group_type}, type: {type}, seasons: {seasons}")
            return None
        
        return final_list
    
    @property
    def fangraphs_id(self) -> Optional[int]:
        """Retrieve the Fangraphs ID from xrefIds if available"""
        if not self.xref_ids:
            return None
        
        for xref in self.xref_ids:
            if xref.xref_type.lower() == 'fangraphs':
                try:
                    return int(xref.xref_id)
                except ValueError:
                    return None
            
        return None
    

class FreeAgent(BaseModel):
    """Model for free agents"""
    
    player: Player
    position: Position
    original_team: Optional[Team] = Field(None, alias='originalTeam')
    new_team: Optional[Team] = Field(None, alias='newTeam')
    date_declared: Optional[date] = Field(None, alias='dateDeclared')
    date_signed: Optional[date] = Field(None, alias='dateSigned')
    notes: Optional[str] = None
    sort_order: Optional[int] = Field(None, alias='sortOrder')  # For internal sorting purposes
    
    @field_validator('new_team', mode='before')
    def validate_new_team(cls, v):
        """Null out new_team if it's a dict with only a 'link' key"""
        if isinstance(v, dict) and len(v) == 1 and 'link' in v:
            return None
        return v
    
    @field_validator('original_team', mode='before')
    def validate_original_team(cls, v):
        """Null out original_team if it's a dict with only a 'link' key"""
        if isinstance(v, dict) and len(v) == 1 and 'link' in v:
            return None
        return v
