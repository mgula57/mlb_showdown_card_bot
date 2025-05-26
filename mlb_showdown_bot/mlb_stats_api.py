
import requests
from pprint import pprint
from datetime import datetime, date, timedelta

# MY PACKAGES
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from .classes.stats_period import StatsPeriod, StatsPeriodType, convert_to_date
    from .classes.team import Team
except ImportError:
    # USE LOCAL IMPORT 
    from classes.stats_period import StatsPeriod, StatsPeriodType, convert_to_date
    from classes.team import Team

stat_map_mlb_api_to_bref: dict[str,str] = {
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
stats_converted_to_float_list = [
    'avg', 'obp', 'ops', 'slg', 
    'era', 'whip', 'inningsPitched',
]

def get_player_realtime_game_logs(player_name:str, player_team:str, year:int, is_pitcher:bool, existing_statline:dict[str: any], user_input_date_max:date = None, user_input_date_min:date = None) -> list[dict]:
    """
    Hits the MLB API to get the player's game logs for the current season.
    Filters out any games that are already in the existing statline or outside the user input date range.

    Args:
        player_name (str): The name of the player. Will be used to search for the player in the MLB API.
        player_team (str): The team of the player. Will be used if multiple player matches (ex: Will Smith)
        year (int): The year of the season.
        is_pitcher (bool): True if the player is a pitcher, False if a hitter.
        existing_statline (dict): The existing statline for the player.
        user_input_date_max (date, optional): The maximum date for filtering game logs.
    
    Returns:
        list[dict]: A list of game logs for the player. Each game log is a dictionary with the player's stats for that game.
    """
    # IDENTIFY THE LAST DATE STORED IN BREF
    game_logs = existing_statline.get(StatsPeriodType.DATE_RANGE.stats_dict_key, [])
    all_game_dates = [convert_to_date(game_log_date_str = game_log.get('date', game_log.get('date_game', None)), year=int(year)) 
                        for game_log in game_logs]
    latest_date_in_bref_stats = max(all_game_dates) if len(all_game_dates) > 0 else None

    # FIND MLB API PLAYER ID
    player_data = get_player_data(player_name=player_name, team_abbreviation=player_team)
    player_id = player_data['id']

    # QUERY REALTIME GAME LOGS
    group = 'pitching' if is_pitcher else 'hitting'
    stats_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=gameLog&group={group}&season={year}"
    stats_response = requests.get(stats_url)
    stats_data = stats_response.json()
    total_stats: dict = stats_data['stats']
    if not total_stats: return None

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
    group_for_type = 'pitching' if is_pitcher else 'hitting'
    for element in total_stats:
        
        # SKIP IF NOT PITCHING OR HITTING
        type_display_name = element.get('group', {}).get('displayName', '')
        if type_display_name != group_for_type:
            continue
        
        # EXTRACT GAME LOGS
        splits = element.get('splits', None)
        if not splits: continue
        all_game_data: list[dict] = []
        for split in splits:

            # EXTRACT DATE AND CHECK IF IT SHOULD BE INCLUDED
            game_date_str = split.get('date', None)
            if not game_date_str: 
                continue

            game_date = convert_to_date(game_date_str, year)
            is_game_already_included = False if latest_date_in_bref_stats is None else game_date <= latest_date_in_bref_stats
            is_game_outside_user_bounds = (False if user_input_date_max is None else game_date > user_input_date_max) \
                                            or (False if user_input_date_min is None else game_date < user_input_date_min)
            if is_game_already_included or is_game_outside_user_bounds:
                continue

            # EXTRACT PLAYER STATS
            game_metadata = split.get('game', {})
            game_pk = game_metadata.get('gamePk', None)
            game_number = game_metadata.get('gameNumber', None)
            game_player_stats_raw: dict = split.get('stat', {})
            game_player_summary_str = game_player_stats_raw.get('summary', None)
            game_player_stats_normalized = {stat_map_mlb_api_to_bref[key]: float(value) if key in stats_converted_to_float_list else value
                                            for key, value in game_player_stats_raw.items() 
                                            if key in stat_map_mlb_api_to_bref.keys() }
            
            # ADD GAME PK AND NUMBER
            game_player_stats_normalized['date'] = game_date_str
            game_player_stats_normalized['game_pk'] = game_pk
            game_player_stats_normalized['game_number'] = game_number
            game_player_stats_normalized['game_player_summary'] = game_player_summary_str
            game_player_stats_normalized['player_id'] = player_id

            all_game_data.append(game_player_stats_normalized)

        if len(all_game_data) > 0:
            return all_game_data
        
    return None

def get_game_status_data(game_pk:str, game_date:str, additional_details:dict) -> dict:
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
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/linescore"
    response = requests.get(url)
    game_data = response.json()
    if response.status_code == 404:
        return
    
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
    team_data_home = get_team_data(team_id_home)
    team_data_away = get_team_data(team_id_away)
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
   
def get_teams_data(team_ids:list[int] = None, team_abbrevations:list[str] = None) -> dict:
    """
    Gets the teams data from the MLB API.

    Args:
        team_ids (list, optional): List of team IDs to filter by. Defaults to None.
        team_abbrevations (list, optional): List of team abbreviations to filter by. Defaults to None.

    Returns:
        dict: The teams data.
    """
    url = f"https://statsapi.mlb.com/api/v1/teams?season=2025&sportId=1&activeStatus=Y"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 404:
        return
    
    # EXTRACT TEAM INFO
    team_data_list = data.get('teams', None)
    if not team_data_list: return None
    
    # FILTER TEAM DATA
    if team_ids is not None:
        team_data = [team for team in team_data_list if team['id'] in team_ids]
    elif team_abbrevations is not None:
        team_data = [team for team in team_data_list if team['abbreviation'] in team_abbrevations]
    else:
        team_data = team_data_list
    
    if len(team_data) == 0:
        return None
    
    return team_data

def get_team_data(team_id:int) -> dict:
    """
    Gets the team data from the MLB API.

    Args:
        team_id (int): The team ID.

    Returns:
        dict: The team data.
    """
    team_data = get_teams_data(team_ids=[team_id])
    if team_data is None: return None
    if len(team_data) == 0: return None
    return team_data[0]

def get_player_data(player_name:str, team_abbreviation:str = None) -> dict:
    """Get player data from the MLB API. 
    Ranks based on natural order from search API, unless team_abbreviation is provided.
    
    Args:
        player_name (str): The name of the player.
        team_abbreviation (str, optional): The team abbreviation to prioritize. Defaults to None.

    Returns:
        dict: The player data.
    """

    # EXTRACT TEAM ID TO PRIORITIZE
    team_id = None
    if team_abbreviation is not None:
        teams_data = get_teams_data(team_abbrevations=[team_abbreviation])
        if teams_data:
            team_id = teams_data[0].get('id', None)
            if team_id:
                team_id = int(team_id)

    # FIND MLB API PLAYER ID
    team_filter = f"&teamId={team_id}" if team_id is not None else ""
    url = f"https://statsapi.mlb.com/api/v1/people/search?names={player_name}&limit=5&active=true{team_filter}"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 404:
        return

    # RETURN NONE IF NO PLAYER FOUND
    people_list = data.get('people', None)
    if not people_list: return None
    if len(people_list) == 0: return None

    # EXTRACT PLAYER ID
    return people_list[0]

def get_player_realtime_game_stats_and_game_boxscore(year:str, bref_stats:dict, stats_period:StatsPeriod, is_disabled:bool=False) -> tuple[list[dict], dict]:
    """
    Gets the player's latest game stats and that game's boxscore data from the MLB API.
    
    Args:
        year (str): The year of the season.
        bref_stats (dict): The player's stats from baseball reference. Used to filter dates.
        stats_period (StatsPeriod): The stats period object.
        is_disabled (bool): Whether the player is disabled or not.

    Returns:
        tuple[list[dict], dict]: A tuple containing the player's game logs and the game's boxscore data as well as boolean with whether the game is additional or already in the stats.
    """

    # SKIP IF DISABLED
    current_date = datetime.now().date()
    current_year = current_date.year
    is_current_year = str(year) == str(current_year)
    if is_disabled or \
            bref_stats is None or \
            not is_current_year or \
            not stats_period.type.check_for_realtime_stats or \
            stats_period.end_date < datetime.now().date():
        return None, None, None
    
    player_name = bref_stats.get('name', '')
    player_team = bref_stats.get('team_ID', '')
    is_pitcher = bref_stats.get('type', '') == 'Pitcher'
    realtime_game_logs = get_player_realtime_game_logs(
        player_name=player_name, 
        player_team=player_team,
        year=year, 
        is_pitcher=is_pitcher,
        existing_statline=bref_stats,
        user_input_date_max = stats_period.end_date
    )

    # SEARCH FOR OLDER GAME IF NO NEW GAME IS RETURNED ABOVE
    # NOTE THE CHANGE IN STATLINE AND DATE MAX INPUT
    is_game_already_in_statline = False
    if realtime_game_logs is None:
        is_game_already_in_statline = True
        realtime_game_logs = get_player_realtime_game_logs(
            player_name=player_name, 
            player_team=player_team,
            year=year, 
            is_pitcher=is_pitcher,
            existing_statline={},
            user_input_date_max=None,
            user_input_date_min=current_date - timedelta(days=1)
        )

    if realtime_game_logs is None:
        return None, None, None
    
    # GET BOX SCORE OF LATEST GAME
    latest_player_game_stats = realtime_game_logs[-1]
    latest_player_game_stats.update({
        'name': player_name,
    })
    game_pk = latest_player_game_stats.get('game_pk', None)
    latest_player_game_boxscore_data = get_game_status_data(
        game_pk=game_pk, 
        game_date=latest_player_game_stats.get('date', None), 
        additional_details={'game_player_summary': latest_player_game_stats}
    )

    return realtime_game_logs, latest_player_game_boxscore_data, is_game_already_in_statline