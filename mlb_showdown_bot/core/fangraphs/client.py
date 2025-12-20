import requests
from typing import Any, Dict, List

from .exceptions import FanGraphsError
from .models import FieldingStats

from ..card.stats.stats_period import StatsPeriod

class FangraphsAPIClient:
    """Client to interact with Fangraphs API for fetching baseball statistics"""

    BASE_URL = "https://www.fangraphs.com/api"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()

    # -------------------
    # GENERAL DATA FETCHING
    # -------------------

    def _request(self, endpoint: str, params: Dict[str, Any]) -> List[Dict]:
        """Make API request and return data"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.RequestException as e:
            raise FanGraphsError(f"API request failed: {e}")
    
    
    # -------------------
    # FIELDING STATS
    # -------------------


    def fetch_fielding_stats(self, stats_period: StatsPeriod, position: str = "all", fangraphs_player_ids: list[str] = None) -> list[FieldingStats]:
        """Fetch fielding stats from Fangraphs
        
        Args:
            season: Year of the season to fetch stats for.
            position: Position to filter by (e.g., "C", "1B", "2B"). Use "all" for all positions.
            fangraphs_player_ids: List of Fangraphs player IDs to fetch stats for.
        
        Returns:
            List of fielding stats dictionaries
        """

        # PARSE INPUTS
        ids_str = ",".join(fangraphs_player_ids) if fangraphs_player_ids and len(fangraphs_player_ids) > 0 else ""
        position_str = (position if position else "all").lower()

        params = {
            "pos": position_str,
            "stats": "fld",
            "lg": "all",
            "qual": "0",
            "type": "1",                             # GETS ADVANCED FIELDING STATS
            "season1": str(stats_period.first_year), # START YEAR
            "season": str(stats_period.last_year),   # END YEAR
            "month": "0",
            "ind": "0",
            "team": "0",
            "rost": "0",
            "players": ids_str,
            "pageitems": "2000",
            "pagenum": "1",
            "sortdir": "default",
            "sortstat": "DRS",
        }
        data = self._request("leaders/major-league/data", params)

        return [FieldingStats(**item) for item in data]