
import requests
from pprint import pprint
from datetime import datetime, date

# MY PACKAGES
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from .classes.stats_period import StatsPeriodType, convert_to_date
except ImportError:
    # USE LOCAL IMPORT 
    from classes.stats_period import StatsPeriodType, convert_to_date

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

def get_player_realtime_game_logs(player_name:str, player_team:str, year:int, is_pitcher:bool, existing_statline:dict[str: any], user_input_date_max:date = None) -> list[dict]:
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
    url = f"https://statsapi.mlb.com/api/v1/people/search?names={player_name}&limit=5&active=true"
    response = requests.get(url)
    data = response.json()

    # RETURN NONE IF NO PLAYER FOUND
    people_list = data['people']
    if not people_list: return None
    if len(people_list) == 0: return None

    # EXTRACT PLAYER ID
    player_data = data['people'][0]
    player_id = player_data['id']

    # QUERY REALTIME GAME LOGS
    stats_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=gameLog&season={year}"
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
            is_game_outside_user_bounds = False if user_input_date_max is None else game_date > user_input_date_max
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

            all_game_data.append(game_player_stats_normalized)

        if len(all_game_data) > 0:
            return all_game_data
        
    return None
