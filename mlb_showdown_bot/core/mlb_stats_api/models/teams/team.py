from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, Optional

from ..leagues.division import Division
from ..leagues.league import League

from ....shared.team import Team as ShowdownTeam
from ....shared.nationality import Nationality

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
    tertiary_color: Optional[str] = None

    def load_colors_from_showdown_team(self):
        """Helper method to load primary and secondary colors from a ShowdownTeam object"""
        # Match the team ID to the corresponding ShowdownTeam and load colors
        showdown_team_match = next((st for st in ShowdownTeam if st.value == self.abbreviation), None)
    
        if showdown_team_match:
            self.primary_color = f"rgb({showdown_team_match.primary_color[0]}, {showdown_team_match.primary_color[1]}, {showdown_team_match.primary_color[2]})"
            self.secondary_color = f"rgb({showdown_team_match.secondary_color[0]}, {showdown_team_match.secondary_color[1]}, {showdown_team_match.secondary_color[2]})"

    def load_color_from_country(self):
        """Helper method to load colors, assuming the team is a national team, based on the country code in the team name. This is used for international teams that may not have a corresponding ShowdownTeam."""

        if not self.abbreviation:
            print(f"Warning: Cannot load colors for team {self.name} - no abbreviation provided to determine country code.")
            return
        
        nationality_match = next((nat for nat in Nationality if nat.three_letter_mlb_api_code == self.abbreviation), None)

        if nationality_match:
            
            self.primary_color = f"rgb({nationality_match.primary_color[0]}, {nationality_match.primary_color[1]}, {nationality_match.primary_color[2]})"
            self.secondary_color = f"rgb({nationality_match.secondary_color[0]}, {nationality_match.secondary_color[1]}, {nationality_match.secondary_color[2]})"
            if nationality_match.colors and len(nationality_match.colors) > 2:
                self.tertiary_color = f"rgb({nationality_match.colors[2][0]}, {nationality_match.colors[2][1]}, {nationality_match.colors[2][2]})"
        else:
            print(f"Warning: Could not load colors for team {self.name} with abbreviation {self.abbreviation} - no matching ShowdownTeam or Nationality found.")