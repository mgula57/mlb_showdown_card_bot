from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, Optional

from ..leagues.division import Division
from ..leagues.league import League

from ....shared.team import Team as ShowdownTeam

class Team(BaseModel):
    id: int

    name: Optional[str] = None
    abbreviation: Optional[str] = None
    teamCode: Optional[str] = Field(None, alias='teamCode')

    season: Optional[int | str] = None
    division: Optional[Division] = None
    league: Optional[League] = None

    active: Optional[bool] = None

    @field_validator('league', mode='before')
    def validate_league(cls, v):
        """Some teams without a league will appear as {'link': '/api/v1/league/null'} in the API response. This validator converts those to None."""
        if isinstance(v, dict) and v.get('link') == '/api/v1/league/null':
            return None
        return v
    
class TeamWithColors(Team):
    """Extension of Team model that includes primary and secondary colors for the team. These colors are used for styling purposes in the frontend."""
    
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None

    def load_colors_from_showdown_team(self):
        """Helper method to load primary and secondary colors from a ShowdownTeam object"""
        # Match the team ID to the corresponding ShowdownTeam and load colors
        showdown_team_match = next((st for st in ShowdownTeam if st.value == self.abbreviation), None)
    
        if showdown_team_match:
            self.primary_color = f"rgb({showdown_team_match.primary_color[0]}, {showdown_team_match.primary_color[1]}, {showdown_team_match.primary_color[2]})"
            self.secondary_color = f"rgb({showdown_team_match.secondary_color[0]}, {showdown_team_match.secondary_color[1]}, {showdown_team_match.secondary_color[2]})"