"""Player and person-related API endpoints"""

from pprint import pprint
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..base_client import BaseMLBClient
from ..models.person import Player, FreeAgent, StatTypeEnum
from ..models.leagues.league import LeagueListEnum
from ...card.stats.stats_period import StatsPeriod, StatsPeriodYearType, PlayerType
import json

class PeopleClient(BaseMLBClient):
    """Client for person/player related endpoints - inherits all base functionality"""

    # -----------------------
    # STANDARD PLAYERS
    # -----------------------

    def search_players(self, name: str, active_status: str = 'both', limit: int = 25, seasons: Optional[List[int]] = None) -> List[Player]:
        """Search for players by name"""
        params = {
            'names': name,
            'activeStatus': active_status,
            'limit': limit
        }
        if seasons:
            params['seasons'] = ','.join(map(str, seasons))
        # Uses base client's _make_request with caching and rate limiting
        data = self._make_request('people/search', params)
        return [Player(**player_data) for player_data in data.get('people', [])]

    def get_player(self, player_id: int, primary_position: str = None, stats_period: StatsPeriod = None, include_stats: bool = True, league_list: Optional[LeagueListEnum] = None) -> Player:
        """Get player information by ID

        Args:
            player_id: MLB player ID
            primary_position: Optional primary position abbreviation for the player (e.g. 'P' for pitcher, 'OF' for outfielder). This can help with context-specific stats.
            stats_period: Optional StatsPeriod object for context-specific data
            include_stats: Whether to include basic stats in the response
            league_list: Optional LeagueListEnum for specifying league context
        
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
        is_pitcher = stats_period.player_type_for_mlb_api(primary_position) == PlayerType.PITCHER if stats_period else (primary_position.upper() == 'P' if primary_position else None)
        if include_stats:
            hydrations.extend([
                'team(league)',
            ])
            
            is_non_mlb = league_list and 'milb' in league_list.value.lower()
            types: list[StatTypeEnum] = [
            
            ] if is_non_mlb else [
                StatTypeEnum.SABERMETRICS,
                StatTypeEnum.RANKINGS_BY_YEAR,
            ]
            if stats_period:
                match stats_period.year_type:
                    case StatsPeriodYearType.SINGLE_YEAR:
                        seasons = [stats_period.year_int]
                        if is_non_mlb:
                            types.extend([StatTypeEnum.STATS_SINGLE_SEASON])
                        else:
                            types.extend([StatTypeEnum.STATS_SINGLE_SEASON, StatTypeEnum.STATS_SINGLE_SEASON_ADVANCED, StatTypeEnum.GAME_LOG])
                    case StatsPeriodYearType.FULL_CAREER:
                        types.extend([StatTypeEnum.CAREER, StatTypeEnum.CAREER_ADVANCED])
                    case StatsPeriodYearType.MULTI_YEAR:
                        seasons = stats_period.year_list
                        types.extend([StatTypeEnum.STATS_SINGLE_SEASON, StatTypeEnum.STATS_SINGLE_SEASON_ADVANCED])

                if is_pitcher:
                    types.append(StatTypeEnum.STAT_SPLITS) 
                    
            # Finalize parameters
            combined_types = ",".join([t.value for t in types])
            seasons_list_str = ",".join([str(season) for season in seasons])
            seasons_hydration = f",seasons=[{seasons_list_str}]" if len(seasons) > 0 else ""
            groups = 'pitching,fielding' if is_pitcher else 'hitting,fielding'
            league_list_hydration = f",leagueListId={league_list.value}" if league_list else ""
            sit_codes = ',sitCodes=[sp,rp]' if is_pitcher else ''
            hydrations.append(f'stats(group=[{groups}],type=[{combined_types}],team(league){seasons_hydration}{league_list_hydration}{sit_codes})')

            params['hydrate'] = ','.join(hydrations)
            if len(seasons) > 0:
                params['seasons'] = seasons_list_str
            
        try:
            data = self._make_request(f'people/{player_id}', params=params)
            if not data.get('people'):
                raise Exception(f"Player {player_id} not found")
            
            player_data = data['people'][0]

            player_object = Player(**player_data)
            
            return player_object
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Player {player_id} not found")
            raise

    def get_players(self, player_ids: List[int]) -> List[Player]:
        """Get multiple players by their IDs"""
        params = {
            'personIds': ",".join([str(pid) for pid in player_ids]),
        }
        data = self._make_request('people', params)
        return [Player(**player_data) for player_data in data.get('people', [])]

    # -----------------------
    # FREE AGENTS
    # -----------------------
    def get_free_agents(self, season: int) -> List[FreeAgent]:
        """Get list of free agent players for a given season"""
        params = {
            'season': season,
            'hydrate': 'team,person',
        }
        data = self._make_request('people/freeAgents', params)
        free_agent_list = data.get('freeAgents', [])

        free_agent_objects = [FreeAgent(**fa_data) for fa_data in free_agent_list]
                
        return sorted(free_agent_objects, key=lambda fa: (fa.sort_order if fa.sort_order is not None else 9999, fa.date_signed or datetime.max.date()))
