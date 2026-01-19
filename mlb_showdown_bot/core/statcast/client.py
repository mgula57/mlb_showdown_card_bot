import io
import csv
import requests
from typing import Any, Dict, List

from ..card.stats.stats_period import StatsPeriod
from .models import StatcastLeaderboardEntry

class StatcastAPIClient:
    """Client to interact with Statcast API for fetching baseball statistics"""

    BASE_URL = "https://baseballsavant.mlb.com"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()

    # -------------------
    # GENERAL DATA FETCHING
    # -------------------

    def _request(self, endpoint: str, params: Dict[str, Any]) -> List[Dict]:
        """Make API request and return data"""
        url = f"{self.BASE_URL}/{endpoint}"

        # ALWAYS ADD CSV TRUE TO PARAMS
        params['csv'] = 'true'
        
        try:
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # USE DICTREADER TO CONVERT CSV TO LIST OF DICTS
            csv_content = io.StringIO(response.content.decode('utf-8-sig'))
            reader = csv.DictReader(csv_content)
            data = list(reader)

            return data
        except requests.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    
    # -------------------
    # SPRINT SPEED 
    # -------------------

    def fetch_sprint_speed_leaderboard(self, stats_period: StatsPeriod, min_opportunities: int = 0) -> list[StatcastLeaderboardEntry]:
        """Fetch sprint speed leaderboard from Statcast
        
        Args:
            stats_period: StatsPeriod object defining the time frame.
            min_opportunities: Minimum opportunities to filter players.
        
        Returns:
            List of sprint speed stats dictionaries
        """
        
        # PARSE INPUTS
        season = stats_period.year_int if stats_period.year_int else None

        params = {
            "year": season,
            "min_opportunities": min_opportunities,
        }

        data = self._request("leaderboard/sprint_speed", params)

        leaderboard_entries = [StatcastLeaderboardEntry(**entry) for entry in data]

        return leaderboard_entries
    
    def fetch_sprint_speed_for_player(self, stats_period: StatsPeriod, player_id: int) -> StatcastLeaderboardEntry:
        """Fetch sprint speed for a specific player from Statcast
        
        Args:
            stats_period: StatsPeriod object defining the time frame.
            player_id: MLB player ID.
        
        Returns:
            Sprint speed stats dictionary for the player
        """

        leaderboard = self.fetch_sprint_speed_leaderboard(stats_period, min_opportunities=0)
        for entry in leaderboard:
            if entry.player_id == player_id:
                return entry
        
        raise Exception(f"Sprint speed data for player {player_id} not found")