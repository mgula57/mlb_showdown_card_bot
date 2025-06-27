import math
from statistics import mode
from typing import Any
from datetime import datetime, date

def total_innings_pitched(ip_list: list[float]) -> float:
    """
    Calculate the total innings pitched from a list of IPs.

    Args:
        ip_list (list[float]): List of innings pitched (e.g. [7.0, 6.1, 6.2, 5.0])

    Returns:
        float: Total innings pitched (e.g. 25.2)
    """
    # CONVERT THE STATS LIST DECIMAL VALUES FROM .1, .2 to .33, .66
    converted_stats = []
    for stat in ip_list:
        decimal_part = stat % 1.0
        new_decimal = 0.0
        match round(decimal_part, 1):
            case 0.1: new_decimal = 1.0 / 3.0
            case 0.2: new_decimal = 2.0 / 3.0
        converted_stats.append(math.floor(stat) + new_decimal)
    
    # GET TOTAL AND CONVERT BACK TO "BASEBALL" DECIMAL
    total_real_decimal = sum(converted_stats)
    total_decimal_part = total_real_decimal % 1.0
    new_total_decimal_part = 0.0
    match round(total_decimal_part, 1):
        case 0.3: new_total_decimal_part = 0.1
        case 0.7: new_total_decimal_part = 0.2
        case 1.0: new_total_decimal_part = 1.0
    
    return math.floor(total_real_decimal) + new_total_decimal_part

def aggregate_stats(category:list, stats:list, aggregation_method: str) -> Any:
    """
    Aggregate from a list of stats
    
    Args:
        stats (list): List of stats
        mode (str): Mode to aggregate by (e.g. 'sum', 'mean')

    Returns:
        dict: Aggregated stats
    """
    # CHECK FOR AT LEAST 1 VALUE
    if len(stats) == 0:
        return None
    
    first_value_type = type(stats[0])
    if first_value_type == str:
        match aggregation_method:
            case 'mode': return mode(stats)
            case 'last': return stats[-1]
    elif category == 'IP':
        return total_innings_pitched(stats)
    else:
        stats = [s for s in stats if len(str(s)) != 0]
        return sum(stats)
    
def convert_to_numeric(string_value:str) -> (int | float | str):
    """Will convert a string to either int or float if able, otherwise return as string

    Args:
        string_value: String for attribute

    Returns:
        Converted attribute
    """
    # CONVERT TYPE IF INT OR FLOAT

    if string_value is None:
        return 0

    is_leading_negative_symbol = string_value.startswith('-')
    string_value_first_decimal = string_value.replace('.','',1)
    if string_value.replace('-','').isdigit() if is_leading_negative_symbol else string_value.isdigit():
        return int(string_value)
    elif ( string_value_first_decimal.replace('-','').isdigit() if is_leading_negative_symbol else string_value_first_decimal.isdigit() ) and string_value.count('.') < 2:
        return float(string_value)
    else:
        # RETURN ORIGINAL STRING
        return string_value
    
def convert_to_date(game_log_date_str: str, year: int = None) -> date:
    """Helper function for converting different formats of bref date strings to a consistent format.
    
    Args:
        date_string: Date string from bref tables
        year: Year of the game log
        
    Returns:
        Date object
    """
    game_log_date_str_cleaned = game_log_date_str \
                                    .split('(')[0] \
                                    .strip() \
                                    .replace('\xa0susp', '') \
                                    .replace(' susp', '') 
    is_new_format = game_log_date_str.count('-') >= 2
    if is_new_format:
        # IN UPGRADED TABLES, DATES ARE IN THIS FORMAT "YYYY-MM-DD)"
        return datetime.strptime(game_log_date_str_cleaned, "%Y-%m-%d").date()
    else:
        # IN OLD TABLES, DATES ARE IN THIS FORMAT "MMM DD"
        game_log_date_str_full = f"{game_log_date_str_cleaned} {year}"
        return datetime.strptime(game_log_date_str_full, "%b %d %Y").date()

def convert_year_input_to_int(year_input: any) -> int:
    """Convert year input to an integer if possible.
    Will return None if the input cannot be converted (ex: `['2004', '2006']`, `'2020-2022'`)
    
    Args:
        year_input: Year input, can be int or str
    
    Returns:
        int: Year as an integer
    """
    if isinstance(year_input, int):
        return year_input
    elif isinstance(year_input, str):
        if year_input.isdigit():
            return int(year_input)
        else:
            return None
    else:
        try:
            return int(year_input)
        except ValueError:
            return None

def fill_empty_stat_categories(stats_data:dict, is_pitcher:bool, is_game_logs:bool=False) -> dict:
    """Ensure all required fields are populated for player stats.
    
    Args:
        stats_data: Current dict for stats.
        is_pitcher: True if pitcher, False if batter
        is_game_logs: True if game logs, False if season long stats

    Returns:
        Update stats dict
    """

    def percentile(minValue:float, maxValue:float, value:float) -> float:
        percentile_raw = (value-minValue) / (maxValue-minValue)

        return min(percentile_raw,1.0) if percentile_raw > 0 else 0

    # CHECK FOR PA
    current_categories = stats_data.keys()
    if 'PA' not in current_categories:
        stats_data['is_stats_estimate'] = True

        # CHECK FOR BATTERS FACED
        bf = stats_data.get('batters_faced',0)
        is_bf_above_than_hits_and_bb = bf > ( stats_data.get('H', 0) + stats_data.get('BB', 0) ) # ACCOUNTS FOR BLANK BF ON PARTIAL SEASONS
        if bf > 0 and is_bf_above_than_hits_and_bb:
            stats_data['PA'] = bf
        # ESTIMATE PA AGAINST
        else:
            stats_data['PA'] = stats_data.get('IP', 0) * 4.25 # NEED TO ESTIMATE PA BASED ON AVG PA PER INNING

    # PITCHER GAME LOGS DO NOT HAVE SH, SO DERIVE FROM PA
    if is_game_logs and is_pitcher and 'SH' not in current_categories:
        stats_data['SH'] = stats_data.get('PA', 0) - stats_data.get('AB', 0) - stats_data.get('BB', 0) - stats_data.get('HBP', 0) - stats_data.get('SF', 0)
        current_categories = stats_data.keys() # RESET CURRENT CATEGORIES
    
    keys_to_fill = ['SH','HBP','IBB','SF','SO']
    for key in keys_to_fill:
        if key not in current_categories:
            stats_data[key] = 0

    if 'ER' in current_categories and 'IP' in current_categories and 'earned_run_avg' not in current_categories and is_pitcher:
        stats_data['earned_run_avg'] = round(9 * stats_data['ER'] / stats_data['IP'], 3)

    if '2B' not in current_categories:
        if is_pitcher:
            maxDoubles = 0.25
            eraPercentile = percentile(minValue=1.0, maxValue=5.0, value=stats_data.get('earned_run_avg', 0))
            stats_data['2B'] = int(stats_data['H'] * eraPercentile * maxDoubles)
        else:
            stats_data['2B'] = 0

    if '3B' not in current_categories:
        if is_pitcher:
            maxTriples = 0.025
            eraPercentile = percentile(minValue=1.0, maxValue=5.0, value=stats_data.get('earned_run_avg', 0))
            stats_data['3B'] = int(stats_data['H'] * eraPercentile * maxTriples)
        else:
            stats_data['3B'] = 0
    
    if 'slugging_perc' not in current_categories:
        ab = stats_data.get('AB') if stats_data.get('AB', None) else stats_data.get('PA', 0) - stats_data.get('BB', 0) - stats_data.get('HBP', 0)
        doubles = stats_data.get('2B', 0)
        triples = stats_data.get('3B', 0)
        hr = stats_data.get('HR', 0)
        singles = stats_data.get('H', 0) - doubles - triples - hr
        total_bases = (singles + (2 * doubles) + (3 * triples) + (4 * hr))
        stats_data['AB'] = ab
        stats_data['TB'] = total_bases
        stats_data['slugging_perc'] = round(total_bases / ab, 5) if ab > 0 else 0.0

    if 'onbase_perc' not in current_categories:
        sf = 0 if len(str(stats_data.get('SF', ''))) == 0 else stats_data.get('SF', 0)
        obp_denominator = ( stats_data.get('AB', 0) + stats_data.get('BB', 0) + stats_data.get('HBP', 0) + sf ) if 'AB' in stats_data.keys() else stats_data['PA']
        stats_data['onbase_perc'] = round((stats_data.get('H', 0) + stats_data.get('BB', 0) + stats_data.get('HBP', 0)) / obp_denominator, 5)
    
    if 'batting_avg' not in current_categories:
        stats_data['batting_avg'] = round(stats_data.get('H', 0) / stats_data['AB'], 5) if stats_data.get('AB', 0) > 0 else 0.0
    
    if 'SB' not in current_categories:
        stats_data['SB'] = 0

    if '1B' not in current_categories:
        stats_data['1B'] = int(stats_data.get('H', 0)) - int(stats_data.get('HR', 0)) - int(stats_data.get('3B', 0)) - int(stats_data.get('2B', 0))

    if 'onbase_plus_slugging' not in current_categories:
        stats_data["onbase_plus_slugging"] = round(stats_data["onbase_perc"] + stats_data["slugging_perc"],4)

    # PITCHER CATEGORIES
    if 'IP_GS' in current_categories and 'GS' in current_categories and 'IP/GS' not in current_categories:
        stats_data['IP/GS'] = round(stats_data['IP_GS'] / stats_data['GS'], 4)

    if 'ER' in current_categories and 'IP' in current_categories and 'earned_run_avg' not in current_categories:
        stats_data['earned_run_avg'] = round(9 * stats_data['ER'] / stats_data['IP'], 3)

    if 'BB' in current_categories and 'H' in current_categories and 'IP' in current_categories and 'whip' not in current_categories:
        stats_data['whip'] = round(( stats_data.get('BB', 0) + stats_data.get('H', 0) ) / stats_data.get('IP', 0), 3)

    return stats_data

def convert_year_string_to_list(year_input:str, all_years_played:list[str] = []) -> list[int]:
    """Take year input/string and convert to a list of year ints
    Ex: 
      - '2000' -> [2000]
      - '2000-2004' -> [2000,2001,2002,2003,2004]
    """
    if year_input.upper() == 'CAREER':
        return [int(year) for year in all_years_played]
    elif '-' in year_input:
        # RANGE OF YEARS
        years = year_input.split('-')
        year_start = int(years[0].strip())
        year_end = int(years[1].strip())
        return list(range(year_start,year_end+1))
    elif '+' in year_input:
        years = year_input.split('+')
        return [int(x.strip()) for x in years]
    else:
        return [int(year_input)]
