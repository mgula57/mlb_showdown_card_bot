from pydantic import BaseModel, Field
from typing import Optional, List

from .game import GameScheduled

class Schedule(BaseModel):
    """Model for schedule information from MLB Stats API"""

    total_items: Optional[int] = Field(None, alias='totalItems')
    total_events: Optional[int] = Field(None, alias='totalEvents')
    total_games: Optional[int] = Field(None, alias='totalGames')
    total_games_in_progress: Optional[int] = Field(None, alias='totalGamesInProgress')

    date: Optional[str] = None

    dates: Optional[List['Schedule']] = None

    games: Optional[List[GameScheduled]] = None

    @property
    def season(self) -> Optional[int]:
        """Extract season from the first game in the schedule, if available."""
        if self.games and len(self.games) > 0:
            return self.games[0].season
        return None