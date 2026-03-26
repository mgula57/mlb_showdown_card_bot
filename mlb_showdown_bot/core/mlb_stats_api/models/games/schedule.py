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
    
    def add_team_colors(self):
        """Helper method to add team colors to each game in the schedule. This is used to ensure that team colors are included in the schedule response for styling purposes in the frontend."""
        
        for game in self.games or []:
            if game.teams:
                if game.teams.away and game.teams.away.team:
                    game.teams.away.team.load_colors_from_showdown_team()
                    if not game.teams.away.team.primary_color and not game.teams.away.team.secondary_color:
                        game.teams.away.team.load_color_from_country()
                if game.teams.home and game.teams.home.team:
                    game.teams.home.team.load_colors_from_showdown_team()
                    if not game.teams.home.team.primary_color and not game.teams.home.team.secondary_color:
                        game.teams.home.team.load_color_from_country()

        for date in self.dates or []:
            date.add_team_colors()