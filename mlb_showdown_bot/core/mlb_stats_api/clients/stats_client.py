from pprint import pprint

from ..models.stats.leaders import LeadersGroup
from ..models.stats.enums import LeaderLeaderStatEnum, StatGroupEnum, StatTypeEnum
from ..models.stats.enums import PlayerPoolEnum
from ..base_client import BaseMLBClient
from typing import Optional, List

class StatsClient(BaseMLBClient):
    """Client for stats related endpoints - inherits all base functionality"""

    def get_leaders(self, sport_id: int = 1, season: int = None, categories: List[LeaderLeaderStatEnum] = None, statGroups: List[StatGroupEnum] = None, playerPool: PlayerPoolEnum = None, limit: Optional[int] = None, days_back: Optional[int] = None) -> List[LeadersGroup]:
        """Get list of leaders for a given sport and season"""

        params = {'sportId': sport_id}
        if season:
            params['season'] = season
        if categories:
            params['leaderCategories'] = ','.join([category.value for category in categories])
        if statGroups:
            params['statGroup'] = ','.join([stat_group.value for stat_group in statGroups])
        if playerPool:
            params['playerPool'] = playerPool.value
        if limit:
            params['limit'] = limit
        if days_back:
            params['daysBack'] = days_back
        try:
            data = self._make_request('stats/leaders', params=params)
            leaders_data = data.get('leagueLeaders', [])
            leaders_objects = [LeadersGroup(**group) for group in leaders_data]
            return leaders_objects
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Leaders not found for sportId {sport_id} and season {season}")
            raise