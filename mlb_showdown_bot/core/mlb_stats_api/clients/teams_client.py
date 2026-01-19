from pydantic import BaseModel
from ..base_client import BaseMLBClient
from ..models.teams.team import Team

class TeamsClient(BaseMLBClient):
    """Client for team related endpoints - inherits all base functionality"""

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