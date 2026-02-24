
from pprint import pprint
from ..base_client import BaseMLBClient
from ..models.leagues.league import League
from ..models.leagues.standings import StandingsType, Standings
from typing import Optional, List

class LeaguesClient(BaseMLBClient):
    """Client for league related endpoints - inherits all base functionality"""
    
    def get_leagues(self, sport_id:int = 1, season: Optional[int] = None, seasons: Optional[List[int]] = None, abbreviations: Optional[List[str]] = None, onlyActive: bool = True) -> List[League]:
        """Get league information by ID
        
        Args:
            sport_id: MLB sport ID. Default is 1 (Major League Baseball)
            season: Optional single season to filter the league data
            seasons: Optional list of seasons to filter the league data
            abbreviations: Optional list of league abbreviations to filter the league data (e.g. ["AL", "NL"])
            onlyActive: Optional flag to filter only active leagues. Default is True.

        Returns:
            dict object with league details
        """

        params = {'sportId': sport_id}
        if seasons:
            params['seasons'] = ','.join(str(season) for season in seasons)
        if season:
            params['season'] = season
        if onlyActive:
            params['activeStatus'] = 'Y'
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


    def get_standings(self, season: str, league_id: int, standings_type: Optional[StandingsType] = StandingsType.BY_DIVISION) -> List[Standings]:
        """Get league standings by league ID and season
        
        Args:
            league_id: ID of the league
            standings_type: Optional standings type to filter the results
        
        Returns:
            list of Standings objects with league standings details
        """

        params = {
            'season': season,
            'leagueId': league_id,
            'standingsTypes': standings_type.value if standings_type else None,
            'hydrate': 'team,league,division,roster',
        }
        try:
            data = self._make_request(f'standings', params=params)
            standings_raw = data.get('records', [])

            standings = [Standings(**record) for record in standings_raw]

            # Add primary and secondary colors to each team in the standings based on the ShowdownTeam enum
            for standing in standings:
                if standing.team_records:
                    for team_record in standing.team_records:
                        team_record.team.load_colors_from_showdown_team()
            
            return standings
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Standings for season {season} not found")
            raise