from pprint import pprint

from ..base_client import BaseMLBClient
from ..models.sports.sport import Sport, SportEnum
from typing import Optional, List

class SportsClient(BaseMLBClient):
    """Client for sports related endpoints - inherits all base functionality"""

    def get_sports(self, season_id: Optional[int] = None, onlyActive: bool = True) -> List[Sport]:
        """Get list of sports (ex: MLB, INT, NLB)"""

        params = {}
        if onlyActive:
            params = {'activeStatus': 'Y'}
        if season_id is not None:
            params['season'] = season_id
        try:
            data = self._make_request('sports', params=params)
            sports_data = data.get('sports', [])
            sports_objects = [Sport(**sport) for sport in sports_data if sport.get('id', -1) in [x.value for x in SportEnum]]

            # CHANGE NAME OF `INT` TO WBC
            for sport in sports_objects:
                print(sport.name)
                if sport.abbreviation == "INT":
                    sport.abbreviation = "WBC"
                    sport.name = "World Baseball Classic"

            sports_objects.sort(key=lambda s: s.sort_order, reverse=False)
            return sports_objects
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Sports not found")
            raise