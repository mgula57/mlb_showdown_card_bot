from pprint import pprint

from ..models.seasons.season import Season
from ..base_client import BaseMLBClient
from typing import Optional, List

class SeasonsClient(BaseMLBClient):
    """Client for season related endpoints - inherits all base functionality"""

    def get_seasons(self, sport_id: int = 1, league_id: Optional[int] = None, season: Optional[int] = None) -> List[Season]:
        """Get list of seasons for a given sport"""

        params = {'sportId': sport_id}
        if league_id:
            params['leagueId'] = league_id
        if season:
            params['season'] = season
        try:
            data = self._make_request('seasons/all', params=params)
            seasons_data = data.get('seasons', [])
            seasons_objects = [Season(**season) for season in seasons_data]
            seasons_objects.sort(key=lambda s: s.season_id, reverse=True)
            return seasons_objects
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Seasons not found for sportId {sport_id}")
            raise

    def get_season(self, season: int, sport_id: int = 1) -> Optional[Season]:
        """Get a single season's calendar (start/end, All-Star break halves). Unlike `seasons/all`, this
        endpoint filters by season and includes the half boundaries."""

        data = self._make_request('seasons', params={'sportId': sport_id, 'season': season})
        seasons_data = data.get('seasons', [])
        return Season(**seasons_data[0]) if seasons_data else None
