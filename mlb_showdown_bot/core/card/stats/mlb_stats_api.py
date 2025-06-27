
import requests
from pprint import pprint
from datetime import datetime, date, timedelta
from pydantic import BaseModel
from typing import Optional

# INTERNAL
from .stats_period import StatsPeriod, convert_to_date
from ...shared.team import Team

class MLBStatsAPI(BaseModel):

    # METADATA
    stats_period: StatsPeriod # STATS YEAR AND RANGE
    name: Optional[str] = None # PLAYER NAME
    team_abbreviation: Optional[str] = None # TEAM ABBREVIATION
    is_pitcher: Optional[bool] = None # TRUE IF PITCHER, FALSE IF HITTER

    # FROM THE API
    player_id: Optional[int] = None # PLAYER ID FROM MLB API
    player_metadata: Optional[dict] = None
    game_logs: Optional[list[dict]] = None
    latest_game_boxscore: Optional[dict] = None

    # MARKED IF DISABLED
    is_disabled: bool = False
    
    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    @property
    def _map_mlb_api_stat_names_to_bref(self) -> dict[str, str]:
        return {
            'atBats': 'AB',
            'baseOnBalls': 'BB',
            'battersFaced': 'batters_faced',
            'caughtStealing': 'CS',
            'doubles': '2B',
            'earnedRuns': 'ER',
            'era': 'earned_run_avg',
            'gamesPlayed': 'G',
            'gamesStarted': 'GS',
            'groundIntoDoublePlay': 'GIDP',
            'groundOutsToAirouts': 'GO/AO',
            'hitByPitch': 'HBP',
            'hits': 'H',
            'homeRuns': 'HR',
            'inningsPitched': 'IP',
            'intentionalWalks': 'IBB',
            'plateAppearances': 'PA',
            'rbi': 'RBI',
            'runs': "R",
            'sacBunts': 'SH',
            'sacFlies': 'SF',
            'saves': 'SV',
            'stolenBases': 'SB',
            'strikeOuts': 'SO',
            'totalBases': 'TB',
            'triples': '3B',
            'whip': 'whip',

            # DISABLED DUE TO DOUBLE COUNTING
            # 'avg': 'batting_avg',
            # 'slg': 'slugging_perc',
            # 'obp': 'onbase_perc',
            # 'ops': 'onbase_plus_slugging',
        }

    @property
    def _mlb_api_stats_datatype_dict(self) -> dict[str, str]:
        """
        Maps the MLB API stats data types to the expected data types for the game logs.
        """
        return {
            'avg': 'float',
            'obp': 'float',
            'ops': 'float',
            'slg': 'float',
            'era': 'float',
            'whip': 'float',
            'inningsPitched': 'float',
            'date': 'str',  # Date is stored as a string in the format YYYY-MM-DD
            'game_pk': 'int',
            'game_number': 'int',
        }

    @property
    def player_type_group(self) -> str:
        """
        Returns the player type group based on whether the player is a pitcher or hitter.
        """
        if self.is_pitcher:
            return 'pitching'
        return 'hitting'

    # ------------------------------------
    # GENERIC API FUNCTIONS
    # ------------------------------------

    def _get_mlb_stats_api_data(self, endpoint:str, params:dict = None) -> dict:
        """
        Generic function to get data from the MLB Stats API.
        
        Args:
            endpoint (str): The endpoint to hit.
            params (dict, optional): Additional parameters to pass to the API.
        
        Returns:
            dict: The response data from the API.
        """
        base_url = "https://statsapi.mlb.com/api/v1/"
        url = f"{base_url}{endpoint}"
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data from MLB Stats API. Status code: {response.status_code}")
        
        return response.json()

    # ------------------------------------
    # API ENDPOINT QUERIES
    # ------------------------------------

    def populate_all_player_data(self) -> dict:
        """
        Pulls player data from the MLB API based on the player name and team.
        Stores results to self
        """

        # DON'T RUN IF DISABLED
        if self.is_disabled:
            return

        # DONT RUN IF NAME OF YEAR IS NOT SET
        if self.name is None or self.stats_period.year_int is None:
            return 
        
        # DONT RUN IF THE STATS PERIOD IS OUTSIDE OF THE BOUNDS OF:
        #  1. CURRENT YEAR
        #  2. USER INPUT DATE MIN/MAX
        if not self.stats_period.check_for_realtime_stats:
            return
        
        # PLAYER METADATA
        self.player_metadata = self._get_player_metadata()
        if not self.player_metadata: return
        self.player_id = self.player_metadata.get('id', None)
        if not self.player_id: return

        # PLAYER GAME LOGS
        self.game_logs = self._get_player_game_logs()
        if not self.game_logs: return

        # UPDATE THE STATS PERIOD SOURCE
        self.stats_period.source += ', MLB Stats API'

        # PARSE LATEST PLAYER GAME ID
        latest_game_player_stats = self.game_logs[-1] if len(self.game_logs) > 0 else None
        if not latest_game_player_stats: return None
        latest_game_id = latest_game_player_stats.get('game_pk', None)
        if not latest_game_id: return None

        # GET LATEST GAME BOX SCORE
        game_date = latest_game_player_stats.get('date', None)
        latest_game_player_stats.update({
            'name': self.name,
        })
        additional_details = {'game_player_summary': latest_game_player_stats}
        self.latest_game_boxscore = self._get_game_boxscore(game_pk=latest_game_id, game_date=game_date, additional_details=additional_details)

        return

    def _get_game_boxscore(self, game_pk:str, game_date:str, additional_details:dict) -> dict:
        """
        Gets the game status data for a given game PK.

        Args:
            game_pk (str): The game PK.
            game_date (str): The date of the game.
            additional_details (dict): Additional details to add to the game data.

        Returns:
            dict: The game status data.
        """
        if game_pk is None:
            return
        
        game_data = self._get_mlb_stats_api_data(endpoint=f'game/{game_pk}/linescore')
        if not game_data: return None
        
        # EXTRACT RELEVANT GAME INFO
        # DATA COMES IN LIKE:
        # {
        #   'balls': 2,
        #   'strikes': 2,
        #   'outs': 1,
        #   'isTopInning': True,
        #   'currentInning': 9,
        #   'currentInningOrdinal': '9th',
        #   'defense': {'batter': {'fullName': 'Tommy Edman',
        #                          'id': 669242,
        #                          'link': '/api/v1/people/669242'},
        #               'battingOrder': 1,
        #               'pitcher': {'fullName': 'Tanner Scott',
        #                           'id': 656945,
        #                           'link': '/api/v1/people/656945'},
        #               ...
        #   'offense': {'batter': {'fullName': 'Andrew McCutchen',
        #                          'id': 457705,
        #                          'link': '/api/v1/people/457705'},
        #               'battingOrder': 3,
        #               'team': {'id': 134,
        #                        'link': '/api/v1/teams/134',
        #                        'name': 'Pittsburgh Pirates'}},
        #   'teams': {'away': {'errors': 1, 'hits': 8, 'leftOnBase': 8, 'runs': 4},
        #             'home': {'errors': 0, 'hits': 11, 'leftOnBase': 8, 'runs': 8}}}
        #    ...
        # }

        # SIMPLIFY/UNNEST DATA
        is_top_inning = game_data.get('isTopInning', None)
        teams_subkey_home = 'defense' if is_top_inning else 'offense'
        teams_subkey_away = 'offense' if is_top_inning else 'defense'
        team_id_home = game_data.get(teams_subkey_home, {}).get('team', {}).get('id', None)
        team_id_away = game_data.get(teams_subkey_away, {}).get('team', {}).get('id', None)
        team_data_home = self._get_team_data(team_id_home)
        team_data_away = self._get_team_data(team_id_away)
        if team_data_home is None or team_data_away is None:
            return None
        
        # MOVE DATAPOINTS TO TOP LEVEL
        #  - CURRENT HITTER NAME
        #  - CURRENT HITTER BATTING ORDER
        #  - CURRENT PITCHER NAME
        #  - RUNS HOME TEAM
        #  - RUNS AWAY TEAM
        pitcher_name = game_data.get('defense', {}).get('pitcher', {}).get('fullName', None)
        batter_name = game_data.get('offense', {}).get('batter', {}).get('fullName', None)
        batter_batting_order = game_data.get('offense', {}).get('battingOrder', None)
        runs_home = game_data.get('teams', {}).get('home', {}).get('runs', None)
        runs_away = game_data.get('teams', {}).get('away', {}).get('runs', None)
        
        # EXTRACT TEAM ABBREVATIONS/COLORS
        team_data_home = team_data_home.get('abbreviation', None)
        team_data_away = team_data_away.get('abbreviation', None)
        team_data_home_color = Team(team_data_home).rgb_color_for_html(year=datetime.now().year)
        team_data_away_color = Team(team_data_away).rgb_color_for_html(year=datetime.now().year)

        # LOGIC TO TELL IF GAME HAS ENDED
        current_inning = game_data.get('currentInning', 0)
        current_inning_ordinal = game_data.get('currentInningOrdinal', '1st')
        current_outs = game_data.get('outs', 0)
        is_game_over = False
        if current_inning >= 9:
            if is_top_inning:
                # CHECK IF HOME TEAM IS WINNING AND OUTS ARE 3
                if runs_home > runs_away and current_outs == 3:
                    is_game_over = True
            else:
                # CHECK IF AWAY TEAM IS WINNING AND OUTS ARE 3
                if runs_away > runs_home and current_outs == 3:
                    is_game_over = True
                # CHECK IF HOME TEAM IS WINNING
                if runs_home > runs_away:
                    is_game_over = True
        
        current_inning_visual = "FINAL" if is_game_over else f'{"▲" if is_top_inning else "▼"} {current_inning_ordinal}'
        game_date_short = game_date[5:].replace('-', '/')
        if game_date_short.startswith('0'):
            game_date_short = game_date_short[1:]
            game_date_short = game_date_short.replace('/0', '/')

        game_data.update({
            'game_pk': game_pk,
            'date': game_date,
            'date_short': game_date_short,
            'home_team_abbreviation': team_data_home,
            'away_team_abbreviation': team_data_away,
            'home_team_id': team_id_home,
            'away_team_id': team_id_away,
            'home_team_runs': runs_home,
            'away_team_runs': runs_away,
            'home_team_color': team_data_home_color,
            'away_team_color': team_data_away_color,
            'current_batter_name': batter_name,
            'current_batter_batting_order': batter_batting_order,
            'current_pitcher_name': pitcher_name,
            'has_game_ended': is_game_over,
            'current_inning_visual': current_inning_visual,
        })
        game_data.update(additional_details)
        
        return game_data
    
    def _get_teams_data(self, team_ids:list[int] = None, team_abbrevations:list[str] = None) -> list[dict]:
        """
        Gets the teams data from the MLB API.

        Args:
            team_ids (list, optional): List of team IDs to filter by. Defaults to None.
            team_abbrevations (list, optional): List of team abbreviations to filter by. Defaults to None.

        Returns:
            list[dict]: A list of team data dictionaries. Each dictionary contains information about a team.
        """
        params = {'sportId': 1, 'activeStatus': 'Y'}
        if self.stats_period.year_int is not None:
            params['season'] = self.stats_period.year_int
        data = self._get_mlb_stats_api_data(endpoint='teams', params=params)
        
        # EXTRACT TEAM INFO
        team_data_list: list[dict] = data.get('teams', None)
        if not team_data_list: return None
        
        # FILTER TEAM DATA
        if team_ids is not None:
            team_data = [team for team in team_data_list if team.get('id', '') in team_ids]
        elif team_abbrevations is not None:
            team_data = [team for team in team_data_list if team.get('abbreviation', '') in team_abbrevations]
        else:
            team_data = team_data_list
        
        if len(team_data) == 0:
            return None
        
        return team_data

    def _get_team_data(self, team_id:int) -> dict:
        """
        Gets the team data from the MLB API.

        Args:
            team_id (int): The team ID.

        Returns:
            dict: The team data.
        """
        team_data = self._get_teams_data(team_ids=[team_id])
        if team_data is None: return None
        if len(team_data) == 0: return None
        return team_data[0]

    def _get_player_metadata(self) -> dict:
        """Get player data from the MLB API. 
        Ranks based on natural order from search API, unless team_abbreviation is provided.
        
        Returns:
            dict: The player data.
        """

        # EXTRACT TEAM ID TO PRIORITIZE
        team_id: int = None
        if self.team_abbreviation is not None:
            teams_data = self._get_teams_data(team_abbrevations=[self.team_abbreviation])
            if teams_data:
                team_id = teams_data[0].get('id', None)
                if team_id:
                    team_id = int(team_id)

        # FIND MLB API PLAYER ID
        params = {'names': self.name, 'limit': 5, 'active': 'true'}
        if team_id is not None:
            # ADD TEAM ID TO FILTER
            params['teamId'] = team_id
        data = self._get_mlb_stats_api_data(endpoint='people/search', params=params)

        # RETURN NONE IF NO PLAYER FOUND
        people_list = data.get('people', None)
        if not people_list: return None
        if len(people_list) == 0: return None

        # EXTRACT FIRST PLAYER
        return people_list[0]

    def _get_player_game_logs(self) -> list[dict]:
        """
        Gets the player's game logs from the MLB API.
        
        Returns:
            list[dict]: A list of game logs for the player. Each game log is a dictionary with the player's stats for that game.
        """
        if self.player_id is None:
            raise ValueError("Player ID must be provided.")
        
        params = {'stats': 'gameLog', 'group': self.player_type_group, 'season': self.stats_period.year_int}
        data = self._get_mlb_stats_api_data(endpoint=f'people/{self.player_id}/stats', params=params)
        
        # EXTRACT GAME LOGS
        total_stats: list[dict] = data.get('stats', None)
        if not total_stats: 
            return None

        # EXTRACT TODAY'S GAME(S)
        # DATA LOOKS LIKE:
        # {'exemptions': [],
        #  'group': {'displayName': 'pitching'},
        #  'splits': [{'date': '2025-03-28',
        #              'game': {'content': {'link': '/api/v1/game/778542/content'},
        #                       'dayNight': 'day',
        #                       'gameNumber': 1,
        #                       'gamePk': 778542,
        #                       'link': '/api/v1.1/game/778542/feed/live'},
        #                       'stat': {'airOuts': 4,
        #                                'atBats': 17,
        #                                'avg': '.235',
        #                                'balks': 0,
        #                                'baseOnBalls': 2,
        #                     ....
        for element in total_stats:
            
            # SKIP IF NOT PLAYER TYPE MATCH
            type_display_name = element.get('group', {}).get('displayName', '')
            if type_display_name != self.player_type_group:
                continue
            
            # EXTRACT GAME LOGS
            splits: list[dict] = element.get('splits', None)
            if not splits: continue
            all_game_data: list[dict] = []
            for split in splits:

                # EXTRACT DATE AND CHECK IF IT SHOULD BE INCLUDED
                game_date_str = split.get('date', None)
                if not game_date_str: 
                    continue

                # EXTRACT PLAYER STATS
                game_metadata: dict = split.get('game', {})
                game_pk = game_metadata.get('gamePk', None)
                game_number = game_metadata.get('gameNumber', None)
                game_player_stats_raw: dict = split.get('stat', {})
                game_player_summary_str = game_player_stats_raw.get('summary', None)
                game_player_stats_normalized = {self._map_mlb_api_stat_names_to_bref[key]: float(value) if self._mlb_api_stats_datatype_dict.get(key, 'str') == 'float' else value
                                                for key, value in game_player_stats_raw.items()
                                                if key in self._map_mlb_api_stat_names_to_bref.keys() }
                
                # ADD IP_GS FOR PITCHERS
                games_started = game_player_stats_normalized.get('GS', 0)
                innings_pitched = game_player_stats_normalized.get('IP', 0)
                if games_started > 0 and innings_pitched > 0:
                    # ADD IP AS IP_GS
                    game_player_stats_normalized['IP_GS'] = innings_pitched
                
                # ADD GAME PK AND NUMBER
                game_player_stats_normalized['date'] = game_date_str
                game_player_stats_normalized['game_pk'] = game_pk
                game_player_stats_normalized['game_number'] = game_number
                game_player_stats_normalized['game_player_summary'] = game_player_summary_str
                game_player_stats_normalized['player_id'] = self.player_id

                all_game_data.append(game_player_stats_normalized)

            if len(all_game_data) > 0:
                return all_game_data
        
        return total_stats
