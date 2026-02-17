from pydantic import BaseModel
from ..base_client import BaseMLBClient
from ..models.teams.team import Team
from ..models.teams.roster import Roster, RosterTypeEnum

class TeamsClient(BaseMLBClient):
    """Client for team related endpoints - inherits all base functionality"""

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
            params = {'sportId': sport_id}
            if season:
                params['season'] = season
            data = self._make_request('teams', params=params)
            teams = data.get('teams', [])
            for team in teams:
                if team.get('abbreviation', '').upper() == abbreviation.upper():
                    return Team(**team)
            raise Exception(f"Team with abbreviation {abbreviation} not found")
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Teams not found")
            raise
    
    # -------------------------
    # ROSTER ENDPOINTS
    # -------------------------

    def get_team_roster(self, team_id: int, roster_type: RosterTypeEnum = RosterTypeEnum.ACTIVE) -> Roster:
        """Get team roster by team ID and roster type
        
        Args:
            team_id: MLB team ID
            roster_type: Roster type to filter the results (e.g. active, 40Man, fullSeason, etc.)
        
        Returns:
            Roster object with roster details
        """
        try:
            data = self._make_request(f'teams/{team_id}/roster', params={'rosterType': roster_type})
            if not data.get('roster'):
                raise Exception(f"Roster for team {team_id} not found")
            return Roster(**data)
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Roster for team {team_id} not found")
            raise