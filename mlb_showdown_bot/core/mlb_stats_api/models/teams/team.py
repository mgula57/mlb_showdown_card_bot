from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

from .division import Division
from .league import League

class Team(BaseModel):
    id: int
    name: Optional[str] = None
    abbreviation: Optional[str] = None
    division: Optional[Division] = None
    league: Optional[League] = None