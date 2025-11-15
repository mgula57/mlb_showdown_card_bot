"""Player and person-related API endpoints"""

from pprint import pprint
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..base_client import BaseMLBClient
from ..models.person import Player

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

    def get_player(self, player_id: int, season: int = None, include_stats: bool = True) -> Player:
        """Get player information by ID
        
        Args:
            player_id: MLB player ID
            season: Optional season year for context-specific data
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
        if include_stats:
            hydrations.extend([
                'team(league)',
                'stats(group=[hitting,fielding,pitching],type=[yearByYear,yearByYearAdvanced,career,careerAdvanced,sabermetrics],team(league))',
            ])
        params = {
            'hydrate': ','.join(hydrations)
        }
        if season:
            params['season'] = season
        try:
            data = self._make_request(f'people/{player_id}', params=params)
            if not data.get('people'):
                raise Exception(f"Player {player_id} not found")
            return Player(**data['people'][0])
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Player {player_id} not found")
            raise
