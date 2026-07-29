from typing import Optional

from ..mlb_stats_api import MLBStatsAPI
from .models import StandingsResult, TeamRecord
from .team import SimTeam


class Standings:
    """Holds the season's teams and their division/league alignment."""

    def __init__(self, year: int, tournament: str, team_leagues: dict[str, str], teams: dict[str, SimTeam], mlb_stats_api: Optional[MLBStatsAPI] = None) -> None:
        self.year = year
        self.tournament = tournament
        self.team_leagues = team_leagues
        self.teams = teams
        self.divisions_mapping = self.fetch_divisions_mapping(mlb_stats_api=mlb_stats_api)

    @property
    def all_players(self) -> list:
        players = []
        for _, team in self.teams.items():
            players += team.all_players
        return players

    def sort_teams(self, teams_dict: dict[str, SimTeam], is_desc: bool = True, excluded_teams: list[str] = []) -> list[tuple[str, SimTeam]]:
        teams_dict_filtered = {team_name: team for team_name, team in teams_dict.items() if team_name not in excluded_teams}
        return sorted(teams_dict_filtered.items(), key=lambda x: (x[1].win_pct, x[1].wins), reverse=is_desc)

    def top_team(self, divisions: list[str] = [], excluded_teams: list[str] = []) -> Optional[SimTeam]:
        top_teams = self.top_teams(num_teams=1, divisions=divisions, excluded_teams=excluded_teams)
        if top_teams is None:
            return None
        return top_teams[0]

    def top_teams(self, num_teams: int = None, divisions: list[str] = [], excluded_teams: list[str] = []) -> Optional[list[SimTeam]]:
        is_division_filter = len(divisions) > 0
        teams_included = {}
        for division, teams_dict in self.divisions_dict.items():
            if division not in divisions and is_division_filter:
                continue # SKIP DIVISION
            for team_name, team in teams_dict.items():
                if team_name not in excluded_teams:
                    teams_included[team_name] = team

        if len(teams_included) == 0:
            return None

        sorted_teams_by_wins = [team for (_, team) in self.sort_teams(teams_dict=teams_included, excluded_teams=excluded_teams)]

        # FILTER TO TOP N
        if num_teams:
            sorted_teams_by_wins = sorted_teams_by_wins[0:num_teams]

        return sorted_teams_by_wins

    @property
    def divisions_dict(self) -> dict[str, dict[str, SimTeam]]:
        """ Splits current dictionary of team data into divisions."""

        updated_data = {}
        for division, teams_list in self.divisions_mapping.items():
            division_teams_dict = {}
            for team_id in teams_list:
                if team_id in self.teams.keys():
                    division_teams_dict[team_id] = self.teams[team_id]
            if len(division_teams_dict) > 0:
                updated_data[division] = division_teams_dict

        return updated_data

    def fetch_divisions_mapping(self, mlb_stats_api: Optional[MLBStatsAPI] = None) -> dict[str, list[str]]:
        """ Division breakdowns for the given year, via the MLB Stats API. """

        if self.tournament:
            return { self.tournament: [team for team in self.team_leagues.keys()] }

        if int(self.year) < 1969:
            # PRE DIVISIONS ERA - GROUP BY LEAGUE
            return self.league_only_mapping

        try:
            client = mlb_stats_api or MLBStatsAPI()
            api_teams = client.teams.get_teams(season=int(self.year))
        except Exception:
            return self.default_division_mapping

        from ..shared.team import Team as ShowdownTeam

        divisions_dict: dict[str, list[str]] = {}
        for api_team in api_teams:
            if api_team.abbreviation is None or api_team.division is None:
                continue
            showdown_team = ShowdownTeam.map_from_mlb_api_team(api_team.abbreviation)
            team_abbr = showdown_team.value if showdown_team and showdown_team != ShowdownTeam.MLB else api_team.abbreviation
            if team_abbr not in self.teams.keys():
                continue
            # BUILD "AL EAST" STYLE NAMES - LEAGUE PREFIX IS USED FOR LEAGUE MATCHING ELSEWHERE
            from .schedule import league_abbreviation
            league_abbr = league_abbreviation(api_team.league) or self.team_leagues.get(team_abbr)
            region = api_team.division.name.split(' ')[-1].upper() if api_team.division.name else ''
            division_name = f"{league_abbr} {region}" if league_abbr and region else (api_team.division.name_short or api_team.division.name).upper()
            divisions_dict.setdefault(division_name, []).append(team_abbr)

        # FALL BACK IF THE API MAPPING DIDN'T COVER THE SEASON'S TEAMS
        mapped_teams = [team for teams in divisions_dict.values() for team in teams]
        if len(mapped_teams) < len(self.teams):
            unmapped = [team for team in self.teams.keys() if team not in mapped_teams]
            if len(unmapped) == len(self.teams):
                return self.default_division_mapping
            # PLACE STRAGGLERS IN THEIR LEAGUE
            for team in unmapped:
                league = self.team_leagues.get(team, 'MLB')
                divisions_dict.setdefault(league, []).append(team)

        return divisions_dict

    @property
    def league_only_mapping(self) -> dict[str, list[str]]:
        leagues_dict: dict[str, list[str]] = {}
        for team, league in self.team_leagues.items():
            leagues_dict.setdefault(league, []).append(team)
        return leagues_dict

    @property
    def leagues(self) -> list[str]:
        """ Unique leagues for season. Uses unique prefixes of divisions"""
        return list(set(list(self.team_leagues.values())))

    def division_leaders_list(self, league: str) -> list[SimTeam]:
        """ Returns leader of each division sorted by winning pct. """
        division_winners = [self.top_team(divisions=[division]) for division in self.divisions_dict.keys() if league == division[0:2]]
        return sorted(division_winners, key=lambda tm: (tm.win_pct, tm.wins), reverse=True)

    def divisions(self, leagues: list[str] = None) -> list[str]:
        if leagues is None:
            leagues = self.leagues

        return [division for division in self.divisions_dict.keys() if division[0:2] in leagues]

    def as_result(self) -> StandingsResult:
        divisions: dict[str, list[TeamRecord]] = {}
        for division, teams_dict in self.divisions_dict.items():
            teams_sorted = self.sort_teams(teams_dict=teams_dict)
            top_team = teams_sorted[0][1]
            records: list[TeamRecord] = []
            for team_name, team in teams_sorted:
                games_back = None if team.wins == top_team.wins else round(( abs(top_team.wins - team.wins) + abs(top_team.losses - team.losses) ) / 2.0, 1)
                records.append(team.as_record(division=division, games_back=games_back))
            divisions[division] = records
        return StandingsResult(divisions=divisions)

    @property
    def default_division_mapping(self) -> dict[str, list[str]]:
        """ Division mapping if the MLB Stats API fetch fails (modern alignment). """

        return {
            'NL EAST': ['WSN', 'NYM', 'ATL', 'MIA', 'PHI'],
            'NL CENTRAL': ['CHC', 'MIL', 'STL', 'PIT', 'CIN'],
            'NL WEST': ['ARI', 'SDP', 'COL', 'LAD', 'SFG'],
            'AL EAST': ['TBR', 'BAL', 'NYY', 'BOS', 'TOR'],
            'AL CENTRAL': ['KCR', 'CLE', 'DET', 'CHW', 'MIN'],
            'AL WEST': ['LAA', 'HOU', 'OAK', 'SEA', 'TEX'],
        }
