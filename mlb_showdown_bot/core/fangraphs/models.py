from pydantic import BaseModel, Field, validator
from typing import Optional

class FieldingStats(BaseModel):
    """Fielding statistics from FanGraphs"""
    
    # Player attributes
    player_name: str = Field(alias="PlayerName")
    name: str = Field(alias="Name")  # Raw name with HTML tags
    team: str = Field(alias="Team")  # Raw team with HTML tags  
    position: str = Field(alias="Pos")
    player_id: int = Field(alias="playerid")
    mlb_stats_id: Optional[int] = Field(None, alias="xMLBAMID")
    season: int = Field(alias="Season")
    
    # Key game information
    games: float = Field(alias="G")
    games_started: float = Field(alias="GS") 
    innings: float = Field(alias="Inn")
    
    # Advanced defensive metrics (your key stats)
    drs: Optional[float] = Field(None, alias="DRS")  # Defensive Runs Saved
    oaa: Optional[float] = Field(None, alias="OAA")  # Outs Above Average
    uzr: Optional[float] = Field(None, alias="UZR")  # Ultimate Zone Rating
    uzr_150: Optional[float] = Field(None, alias="UZR/150")  # UZR per 150 games
    tz: Optional[float] = Field(None, alias="TZ")    # Total Zone (TZR equivalent)
    
    # Basic fielding stats
    fielding_percentage: Optional[float] = Field(None, alias="FP")
    errors: Optional[float] = Field(None, alias="E")
    