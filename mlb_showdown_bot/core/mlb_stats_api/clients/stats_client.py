from pprint import pprint

from ..models.stats.leaders import LeadersGroup
from ..models.stats.enums import LeaderLeaderStatEnum, StatGroupEnum, StatTypeEnum
from ..models.stats.enums import PlayerPoolEnum
from ..base_client import BaseMLBClient
from ...shared.player_position import PlayerType
from typing import ClassVar, Dict, Optional, List

class StatsClient(BaseMLBClient):
    """Client for stats related endpoints - inherits all base functionality"""

    # Sensible defaults applied when a `player_type` is given to get_leaders() without
    # explicit `categories`/`statGroups`, so callers can just ask for "hitter" or "pitcher" leaders.
    STAT_GROUP_BY_PLAYER_TYPE: ClassVar[Dict[PlayerType, StatGroupEnum]] = {
        PlayerType.HITTER: StatGroupEnum.HITTING,
        PlayerType.PITCHER: StatGroupEnum.PITCHING,
    }
    DEFAULT_CATEGORIES_BY_PLAYER_TYPE: ClassVar[Dict[PlayerType, List[LeaderLeaderStatEnum]]] = {
        PlayerType.HITTER: [
            LeaderLeaderStatEnum.BATTING_AVERAGE,
            LeaderLeaderStatEnum.HOME_RUNS,
            LeaderLeaderStatEnum.RUNS_BATTED_IN,
            LeaderLeaderStatEnum.ON_BASE_PLUS_SLUGGING,
            LeaderLeaderStatEnum.STOLEN_BASES,
        ],
        PlayerType.PITCHER: [
            LeaderLeaderStatEnum.EARNED_RUN_AVERAGE,
            LeaderLeaderStatEnum.STRIKEOUTS,
            LeaderLeaderStatEnum.BASEBALL_WINS,
            LeaderLeaderStatEnum.SAVES,
            LeaderLeaderStatEnum.WHIP,
        ],
    }

    def get_leaders(
        self,
        sport_id: int = 1,
        season: int = None,
        categories: List[LeaderLeaderStatEnum] = None,
        statGroups: List[StatGroupEnum] = None,
        playerPool: PlayerPoolEnum = None,
        limit: Optional[int] = None,
        days_back: Optional[int] = None,
        league_id: Optional[int] = None,
        player_type: Optional[PlayerType] = None,
    ) -> List[LeadersGroup]:
        """Get list of leaders for a given sport and season

        Args:
            sport_id: MLB sport ID. Default is 1 (Major League Baseball)
            season: Season year to get leaders for
            categories: Optional list of leader categories. Defaults based on `player_type` if omitted.
            statGroups: Optional list of stat groups (hitting/pitching/fielding). Defaults based on `player_type` if omitted.
            playerPool: Optional player pool filter (e.g. QUALIFIED)
            limit: Optional number of leaders to return per category
            days_back: Optional filter to only include stats from the last X days
            league_id: Optional league ID to filter to a single league (e.g. AL=103, NL=104 - see LeagueEnum)
            player_type: Optional PlayerType (HITTER/PITCHER) used to fill in `statGroups`/`categories` when not provided
        """

        if player_type:
            statGroups = statGroups or [self.STAT_GROUP_BY_PLAYER_TYPE[player_type]]
            categories = categories or self.DEFAULT_CATEGORIES_BY_PLAYER_TYPE[player_type]

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
        if league_id:
            params['leagueId'] = league_id
        try:
            data = self._make_request('stats/leaders', params=params)
            leaders_data = data.get('leagueLeaders', [])
            leaders_objects = [LeadersGroup(**group) for group in leaders_data]
            return leaders_objects
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Leaders not found for sportId {sport_id} and season {season}")
            raise