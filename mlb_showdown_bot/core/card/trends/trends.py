
from pydantic import BaseModel
from typing import Optional

class TrendDatapoint(BaseModel):
    """Stores information about a single trend datapoint"""

    # DATES
    start_date: str
    end_date: str

    # SHARED ACROSS TYPES
    team: str
    points: float
    command_type: str
    command: int
    outs: int
    year: int
    color: str
    shOPS_plus: Optional[float] = None
    double: Optional[str] = None

    # HITTER ONLY
    hr: Optional[str] = None
    speed: Optional[str] = None
    defense: Optional[str] = None

    # PITCHER ONLY
    ip: Optional[int] = None
    so: Optional[str] = None


class InSeasonTrends(BaseModel):
    """Stores in-season trend data for a player"""

    # TRENDS
    cumulative_trends_date_aggregation: str = 'WEEK'
    cumulative_trends: dict[str, TrendDatapoint] = None

    # ATTRIBUTES
    pts_change: Optional[dict[str, int]] = {}

    def as_json(self) -> dict:
        return self.model_dump(mode="json", exclude_none=True)
    
class CareerTrends(BaseModel):
    """Stores career trend data for a player"""

    yearly_trends: dict[str | int, TrendDatapoint] = None

    def as_json(self) -> dict:
        return self.model_dump(mode="json", exclude_none=True)