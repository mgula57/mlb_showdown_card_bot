"""MLB Stats API - Sync-only implementation for all use cases"""

from .clients.teams_client import TeamsClient
from .clients.people_client import PeopleClient
from .models.person import Player
from typing import Optional
from pprint import pprint
import logging

# Logging
logger = logging.getLogger(__name__)

class MLBStatsAPI:
    """MLB Stats API client for all operations"""
    
    def __init__(self, **config):
        self.people = PeopleClient(**config)
        self.teams = TeamsClient(**config)

    def build_full_player_from_search(self, search_name: str, season: Optional[str] = None) -> Player:

        # Search for the player by name
        player_search_results = self.people.search_players(name=search_name)

        # If no results found, return None
        if not player_search_results or len(player_search_results) == 0:
            logger.warning(f"No players found for name: {search_name}")
            return None

        # Fetch full player details using the player ID
        player = self.people.get_player(player_id=player_search_results[0].id, season=season)

        return player

__all__ = [
    'MLBStatsAPI', 
    'Player',
    'Team',
]