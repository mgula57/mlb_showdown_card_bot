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
            response_data = response.json()
            if type(response_data) == dict and 'data' in response_data:
                return response_data['data']
            elif type(response_data) == list:
                return response_data
            
        except requests.RequestException as e:
            raise FanGraphsError(f"API request failed: {e}")
    
    
    # -------------------
    # FIELDING STATS
    # -------------------


    def fetch_leaderboard_stats(self, season_start:int, season_end:int, stat_type: str = "fld", league='MLB', position: str = "all", fangraphs_player_ids: list[str] = None) -> list[dict]:
        """Fetch fielding stats from Fangraphs
        
        Args:
            season_start: Start year of the season to fetch stats for.
            season_end: End year of the season to fetch stats for.
            stat_type: Type of stats to fetch (e.g., "fld", "bat", "pit").
            league: League to fetch stats for (e.g., "MLB", "NPB", "KBO").
            position: Position to filter by (e.g., "C", "1B", "2B"). Use "all" for all positions.
            fangraphs_player_ids: List of Fangraphs player IDs to fetch stats for.
        
        Returns:
            List of fielding stats dictionaries
        """

        # PARSE INPUTS
        fangraphs_player_ids = [str(pid) for pid in fangraphs_player_ids] if fangraphs_player_ids else []
        ids_str = ",".join(fangraphs_player_ids) if fangraphs_player_ids and len(fangraphs_player_ids) > 0 else ""
        position_str = (position if position else "all").lower()

        params = {
            "pos": position_str,
            "stats": stat_type,
            "qual": "0",
            "type": "0",
            "season": str(season_end),   # END YEAR
            "ind": "0",
            "team": "0",
            "pageitems": "2000",
            "pagenum": "1",
        }

        # LEAGUE SETTINGS
        match league.lower():
            case 'mlb':
                params.update({
                    "lg": "all",
                })
                request_url_league_path = 'major-league'
            case 'npb':
                params.update({
                    "lg": "", # EMPTY STRING FOR NPB, LEAGUE IS IN REQUEST URL
                })
                request_url_league_path = 'international/npb'
            case 'kbo':
                params.update({
                    "lg": "", # EMPTY STRING FOR KBO, LEAGUE IS IN REQUEST URL
                })
                request_url_league_path = 'international/kbo'
            case _:
                raise ValueError(f"Invalid league: {league}. Valid options are: MLB, NPB, KBO.")

        # STATS TYPE SETTINGS
        match stat_type.lower():
            case 'fld':
                params.update({
                    "season1": str(season_start), # START YEAR
                    "sortstat": "DRS",
                    "sortdir": "desc",
                    "month": "0",
                    "rost": "0",
                    "players": ids_str,
                    "type": "1",                             # GETS ADVANCED FIELDING STATS
                })

        data = self._request(f"leaders/{request_url_league_path}/data", params)

        return data