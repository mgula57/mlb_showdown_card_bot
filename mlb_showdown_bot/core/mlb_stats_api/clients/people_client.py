"""Player and person-related API endpoints"""

from pprint import pprint
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..base_client import BaseMLBClient
from ..models.person import Player, StatTypeEnum
from ...card.stats.stats_period import StatsPeriod, StatsPeriodYearType
import json

class PeopleClient(BaseMLBClient):
    """Client for person/player related endpoints - inherits all base functionality"""

    def search_players(self, name: str, active_status: str = 'both', limit: int = 25) -> List[Player]:
        """Search for players by name"""
        params = {
            'names': name,
            'activeStatus': active_status,
            'limit': limit
        }
        # Uses base client's _make_request with caching and rate limiting
        data = self._make_request('people/search', params)
        return [Player(**player_data) for player_data in data.get('people', [])]

    def get_player(self, player_id: int, stats_period: StatsPeriod = None, include_stats: bool = True) -> Player:
        """Get player information by ID

        Args:
            player_id: MLB player ID
            stats_period: Optional StatsPeriod object for context-specific data
            include_stats: Whether to include basic stats in the response
        
        Returns:
            Person object with player details
        """
        hydrations = [
            'currentTeam',
            'rookieSeasons',
            'awards',
            'xrefId',
        ]
        params: Dict[str, Any] = {}
        seasons: Optional[List[int]] = []
        if include_stats:
            hydrations.extend([
                'team(league)',
            ])
            
            types: list[StatTypeEnum] = [
                StatTypeEnum.SABERMETRICS,
                StatTypeEnum.RANKINGS_BY_YEAR,
            ]
            if stats_period:
                match stats_period.year_type:
                    case StatsPeriodYearType.SINGLE_YEAR:
                        seasons = [stats_period.year_int]
                        types.extend([StatTypeEnum.STATS_SINGLE_SEASON, StatTypeEnum.STATS_SINGLE_SEASON_ADVANCED, StatTypeEnum.GAME_LOG])
                    case StatsPeriodYearType.FULL_CAREER:
                        types.extend([StatTypeEnum.CAREER, StatTypeEnum.CAREER_ADVANCED])
                    case StatsPeriodYearType.MULTI_YEAR:
                        seasons = stats_period.year_list
                        types.extend([StatTypeEnum.STATS_SINGLE_SEASON, StatTypeEnum.STATS_SINGLE_SEASON_ADVANCED])
                    
            # Finalize parameters
            combined_types = ",".join([t.value for t in types])
            seasons_list_str = ",".join([str(season) for season in seasons])
            seasons_hydration = f",seasons=[{seasons_list_str}]" if len(seasons) > 0 else ""
            hydrations.append(f'stats(group=[hitting,fielding,pitching],type=[{combined_types}],team(league){seasons_hydration})')

            params['hydrate'] = ','.join(hydrations)
            if len(seasons) > 0:
                params['seasons'] = seasons_list_str
            
        try:
            data = self._make_request(f'people/{player_id}', params=params)
            if not data.get('people'):
                raise Exception(f"Player {player_id} not found")
            
            player_data = data['people'][0]

            player_object = Player(**player_data)
            
            # EXPORT TO JSON
            with open(f'/Users/matthewgula/Desktop/player_{player_object.full_name}.json', 'w') as f:
                json.dump(player_data, f, indent=4)
            
            return player_object
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Player {player_id} not found")
            raise
