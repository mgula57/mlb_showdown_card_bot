from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, Optional

from ..leagues.division import Division
from ..leagues.league import League

class Team(BaseModel):
    id: int
    name: Optional[str] = None
    abbreviation: Optional[str] = None
    division: Optional[Division] = None
    league: Optional[League] = None

    @field_validator('league', mode='before')
    def validate_league(cls, v):
        """Some teams without a league will appear as {'link': '/api/v1/league/null'} in the API response. This validator converts those to None."""
        if isinstance(v, dict) and v.get('link') == '/api/v1/league/null':
            return None
        return v