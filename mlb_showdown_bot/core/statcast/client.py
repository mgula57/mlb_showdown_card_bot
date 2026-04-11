import io
import csv
import cloudscraper
import requests
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import re
import json
from ..card.stats.stats_period import StatsPeriod
from .models import StatcastLeaderboardEntry

_LEADERBOARD_CACHE: dict[tuple, tuple[list, datetime]] = {}
_LEADERBOARD_CACHE_TTL = timedelta(hours=8)

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
    
    def html_for_url(self, url:str) -> str:
        """Make request for URL to get HTML

        Args:
          url: URL for the request.

        Raises:
          TimeoutError: 502 - BAD GATEWAY
          TimeoutError: 429 - TOO MANY REQUESTS TO BASEBALL REFERENCE

        Returns:
          HTML string for URL request.
        """

        scraper = cloudscraper.create_scraper()
        html = scraper.get(url)

        if html.status_code == 502:
            self.error = "502 - BAD GATEWAY"
            raise TimeoutError(self.error)
        if html.status_code == 429:
            website = url.split('//')[1].split('/')[0]
            self.error = f"429 - TOO MANY REQUESTS TO {website}. PLEASE TRY AGAIN IN A FEW MINUTES."
            raise TimeoutError(self.error)

        return html.text
    
    # -------------------
    # SPRINT SPEED 
    # -------------------

    def fetch_sprint_speed_leaderboard(self, season: Optional[int] = None, min_opportunities: int = 0) -> list[StatcastLeaderboardEntry]:
        """Fetch sprint speed leaderboard from Statcast
        
        Args:
            season: Year of the leaderboard.
            min_opportunities: Minimum opportunities to filter players.
        
        Returns:
            List of sprint speed stats dictionaries
        """

        cache_key = (season, min_opportunities)
        now = datetime.now(timezone.utc)
        cached = _LEADERBOARD_CACHE.get(cache_key)
        if cached and now < cached[1]:
            print("Serving sprint speed leaderboard from cache")
            return cached[0]

        params = {
            "year": season,
            "min_opportunities": min_opportunities,
        }

        data = self._request("leaderboard/sprint_speed", params)
        leaderboard_entries = [StatcastLeaderboardEntry(**entry) for entry in data]

        _LEADERBOARD_CACHE[cache_key] = (leaderboard_entries, now + _LEADERBOARD_CACHE_TTL)
        return leaderboard_entries
    
    def fetch_sprint_speed_for_player(self, stats_period: StatsPeriod, player_id: int) -> StatcastLeaderboardEntry:
        """Fetch sprint speed for a specific player from Statcast
        
        Args:
            stats_period: StatsPeriod object defining the time frame.
            player_id: MLB player ID.
        
        Returns:
            Sprint speed stats dictionary for the player
        """

        leaderboard = self.fetch_sprint_speed_leaderboard(season=stats_period.year_int, min_opportunities=0)
        for entry in leaderboard:
            if entry.player_id == player_id:
                return entry
        
        print(f"Sprint speed data for player {player_id} not found")
        return None
    

    # -------------------
    # FIELDING
    # -------------------
    def fetch_defense_for_player(self, stats_period: StatsPeriod, mlb_player_id: int) -> Dict:
        """Fetch fielding stats for a specific player from Statcast
        
        Args:
            stats_period: StatsPeriod object defining the time frame.
            mlb_player_id: MLB player ID.
        
        Returns:
            Fielding stats dictionary for the player
        """

        # DATA ONLY AVAILABLE 2016+
        if stats_period.last_year < 2016:
            return {}
        
        player_detail_url = f'https://baseballsavant.mlb.com/savant-player/{mlb_player_id}?stats=statcast-r-fielding-mlb'
        player_detail_html = self.html_for_url(url=player_detail_url)
        fielding_data_extracted = re.search('infieldDefense: (.*),',player_detail_html)
        if fielding_data_extracted:
            fielding_data_grouped = fielding_data_extracted.group(1)
            fielding_data_jsons = json.loads(fielding_data_grouped)
            fielding_data = {}
            for fielding_row in fielding_data_jsons:
                team_abbr = fielding_row['fld_abbreviation']
                is_year_match = int(fielding_row['year']) in stats_period.year_list
                is_team_row = stats_period.team_override.value == team_abbr if stats_period.team_override else team_abbr != 'NA'
                if is_year_match and is_team_row:
                    position = fielding_row['pos_name_short']
                    ooa = fielding_row['outs_above_average']
                    if ooa:                              
                        ooa_rounded = round(ooa, 3)
                        if position in fielding_data.keys():
                            # POSITION IS ALREADY IN JSON, ADD TO IT
                            fielding_data[position] += ooa_rounded
                        else:
                            fielding_data[position] = ooa_rounded
                        # IF OF POSITION, ADD TO TOTAL OF DEFENSE
                        if position in ['LF','CF','RF']:
                            if 'OF' in fielding_data.keys():
                                # POSITION IS ALREADY IN JSON, ADD TO IT
                                fielding_data['OF'] += ooa_rounded
                            else:
                                fielding_data['OF'] = ooa_rounded
            return fielding_data