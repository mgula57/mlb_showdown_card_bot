from pydantic import BaseModel
from typing import ClassVar, Optional
from ..base_client import BaseMLBClient
from ..models.teams.team import Team
from ..models.teams.roster import Roster, RosterTypeEnum

class TeamsClient(BaseMLBClient):
    """Client for team related endpoints - inherits all base functionality"""

    # BREF-style abbreviations for defunct franchises that the MLB Stats API reports differently.
    # e.g. it reuses 'MIL' for the Milwaukee Braves (1953-1965), the same code as the modern
    # Brewers, and reports 'WAS' (not 'WSH') for the original Washington Senators (1901-1960).
    # The `season` filter on the request disambiguates which franchise comes back.
    BREF_TO_MLB_API_ABBREVIATION: ClassVar[dict[str, str]] = {
        'MLN': 'MIL',
        'WSH': 'WAS',
    }

    # -------------------------
    # TEAMS LIST
    # -------------------------
    def get_teams(self, sport_id: int = 1, season: int = None, league_id: int = None, onlyActive: bool = False) -> list[Team]:
        """Get list of teams for a given sport and season"""

        params = {'sportId': sport_id}
        if season:
            params['season'] = season
        if league_id:
            params['leagueId'] = league_id
        if onlyActive:
            params['activeStatus'] = 'Y'
        try:
            data = self._make_request('teams', params=params)
            teams_data = data.get('teams', [])
            return [Team(**team) for team in teams_data]
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Teams not found for sportId {sport_id} and season {season}")
            raise

    # -------------------------
    # TEAM ENDPOINTS
    # -------------------------
    def get_team(self, team_id: int) -> Team:
        """Get team information by ID
        
        Args:
            team_id: MLB team ID
        
        Returns:
            Team object with team details
        """
        hydrations = [
            'league',
            'division',
        ]
        params = {}
        if hydrations:
            params['hydrate'] = ','.join(hydrations)

        try:
            data = self._make_request(f'teams/{team_id}', params=params)
            if not data.get('teams'):
                raise Exception(f"Team {team_id} not found")
            return Team(**data['teams'][0])
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Team {team_id} not found")
            raise

    def find_team_for_abbreviation(self, abbreviation: str, sport_id: int = 1, season: int = None) -> Team:
        """Find team information by abbreviation (e.g. NYY for New York Yankees)
        
        Args:
            abbreviation: Team abbreviation to search for
            sport_id: MLB sport ID. Default is 1 (Major League Baseball).
            season: Season year to filter teams by.
        
        Returns:
            Team object with team details
        """
        try:
            mlb_api_abbreviation = self.BREF_TO_MLB_API_ABBREVIATION.get(abbreviation.upper(), abbreviation)
            params = {'sportId': sport_id}
            if season:
                params['season'] = season
            data = self._make_request('teams', params=params)
            teams = data.get('teams', [])
            for team in teams:
                if team.get('abbreviation', '').upper() == mlb_api_abbreviation.upper():
                    return Team(**team)
            raise Exception(f"Team with abbreviation {abbreviation} not found")
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Teams not found")
            raise
    
    # -------------------------
    # ROSTER ENDPOINTS
    # -------------------------

    def get_team_roster(self, team_id: int, season: str = None, date: str = None, roster_type: RosterTypeEnum = RosterTypeEnum.ACTIVE) -> Roster:
        """Get team roster by team ID and roster type
        
        Args:
            team_id: MLB team ID
            season: Season year to filter the roster by.
            date: Specific date to filter the roster by. Format should be YYYY-MM-DD.
            roster_type: Roster type to filter the results (e.g. active, 40Man, fullSeason, etc.)
        
        Returns:
            Roster object with roster details
        """
        try:
            params = {'rosterType': roster_type}
            if season:
                params['season'] = season
            if date:
                params['date'] = date
            data = self._make_request(f'teams/{team_id}/roster', params=params)
            if not data.get('roster'):
                raise Exception(f"Roster for team {team_id} not found")
            return Roster(**data)
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Roster for team {team_id} not found")
            raise