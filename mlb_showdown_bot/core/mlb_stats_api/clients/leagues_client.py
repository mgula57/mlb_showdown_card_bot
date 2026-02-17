
from pprint import pprint
from ..base_client import BaseMLBClient
from ..models.leagues.league import League
from ..models.leagues.standings import StandingsType
from typing import Optional, List

class LeaguesClient(BaseMLBClient):
    """Client for league related endpoints - inherits all base functionality"""
    
    def get_leagues(self, sport_id:int = 1, seasons: Optional[List[int]] = None, abbreviations: Optional[List[str]] = None) -> List[League]:
        """Get league information by ID
        
        Args:
            sport_id: MLB sport ID. Default is 1 (Major League Baseball)
            seasons: Optional list of seasons to filter the league data
            abbreviations: Optional list of league abbreviations to filter the league data (e.g. ["AL", "NL"])

        Returns:
            dict object with league details
        """

        params = {'sportId': sport_id}
        if seasons:
            params['seasons'] = ','.join(str(season) for season in seasons)
        try:
            data = self._make_request('leagues', params=params)
            all_leagues = data.get('leagues', [])

            # FILTER DOWN LEAGUES
            final_leagues = []
            for league in all_leagues:
                if abbreviations:
                    if league.get('abbreviation', 'N/A') in abbreviations:
                        final_leagues.append(League(**league))
                else:
                    final_leagues.append(League(**league))

            return final_leagues
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Leagues for sport {sport_id} not found")
            raise


    def get_standings(self, league: League, standings_type: Optional[StandingsType] = StandingsType.BY_DIVISION) -> dict:
        """Get league standings by league ID and season
        
        Args:
            league: League object containing league ID and season
            standings_type: Optional standings type to filter the results
        
        Returns:
            dict object with league standings details
        """

        params = {
            'season': league.season,
            'leagueId': league.id,
            'standingsTypes': standings_type.value if standings_type else None,
            'hydrate': 'team,league,division,roster',
        }
        try:
            data = self._make_request(f'standings', params=params)
            standings = data.get('records', [])

            # EXPORT TO JSON FILE (ONLY FOR TESTING - REMOVE LATER)
            import json
            
            with open(f'standings_{league.abbreviation}_{league.season}.json', 'w') as f:
                json.dump(data, f, indent=4)

            return standings
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Standings for season {league.season} not found")
            raise