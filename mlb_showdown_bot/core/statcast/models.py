from pydantic import BaseModel, Field
from typing import Optional

class StatcastLeaderboardEntry(BaseModel):
    """Model for a single entry in a Statcast leaderboard"""
    
    player_id: int = Field(..., alias='player_id')
    player_name: str = Field(..., alias='last_name, first_name')
    team: str = Field(..., alias='team')
    team_id: int = Field(..., alias='team_id')
    position: str = Field(..., alias='position')
    sprint_speed: Optional[float] = Field(None, alias='sprint_speed')  # in feet per second
