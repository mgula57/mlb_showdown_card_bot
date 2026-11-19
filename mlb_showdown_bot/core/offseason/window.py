from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel

from ..mlb_stats_api import MLBStatsAPI


class OffseasonWindow(BaseModel):
    """The stretch between a World Series and the next Opening Day, named for the season it leads into.

    The 2027 window runs from the day after the 2026 World Series was clinched to the day before
    the 2027 regular season opens. Both ends come from the MLB Stats API; neither is hard-coded.
    """

    season: int
    start_date: date
    end_date: date

    @classmethod
    def for_season(cls, season: int, mlb_stats_api: MLBStatsAPI) -> Optional['OffseasonWindow']:
        """The window leading into `season`, or None until the prior World Series has been won.

        None also covers a season the API has no calendar for yet.
        """
        clinch_date = mlb_stats_api.games.get_world_series_clinch_date(season=season - 1)
        calendar = mlb_stats_api.seasons.get_season(season=season)
        if not clinch_date or not calendar or not calendar.regular_season_start_date:
            return None
        return cls(
            season=season,
            start_date=date.fromisoformat(clinch_date) + timedelta(days=1),
            end_date=date.fromisoformat(calendar.regular_season_start_date) - timedelta(days=1),
        )

    @property
    def is_open(self) -> bool:
        return self.start_date <= date.today() <= self.end_date

    @property
    def query_end_date(self) -> date:
        """The window's last day, capped at today - nothing later than today has happened yet."""
        return min(self.end_date, date.today())
