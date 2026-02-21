from pprint import pprint

from ..models.seasons.season import Season
from ..base_client import BaseMLBClient
from typing import Optional, List

class SeasonsClient(BaseMLBClient):
    """Client for season related endpoints - inherits all base functionality"""

    def get_seasons(self, sport_id: int = 1) -> List[Season]:
        """Get list of seasons for a given sport"""

        params = {'sportId': sport_id}
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