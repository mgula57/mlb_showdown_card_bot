from enum import Enum
from pydantic import BaseModel, validator
from datetime import date, datetime
from typing import Optional, Any
from statistics import mode

try:
    from .shared_functions import aggregate_stats, convert_to_numeric, fill_empty_stat_categories
except ImportError:
    from shared_functions import aggregate_stats, convert_to_numeric, fill_empty_stat_categories

class StatsPeriodType(str, Enum):

    REGULAR_SEASON = "REGULAR"
    DATE_RANGE = "DATES"
    POSTSEASON = "POST"
    SPLIT = "SPLIT"

    @property
    def uses_game_logs(self) -> bool:
        return self in [StatsPeriodType.DATE_RANGE, StatsPeriodType.POSTSEASON]

    @property
    def enable_date_range(self) -> bool:
        return self.name in ['DATE_RANGE']
    
    @property
    def enable_split(self) -> bool:
        return self.name in ['SPLIT']
    
    @property
    def player_image_search_term(self) -> str:
        match self:
            case StatsPeriodType.POSTSEASON: return "(POST)"
            case _: return None

    @property
    def show_text_on_card_image(self) -> bool:
        return self not in [StatsPeriodType.REGULAR_SEASON]
    
    @property
    def is_regular_season_games_stat_needed(self) -> bool:
        return self not in [StatsPeriodType.REGULAR_SEASON]
    
    @property
    def stats_dict_key(self) -> str:
        match self:
            case StatsPeriodType.DATE_RANGE: return "game_logs"
            case StatsPeriodType.POSTSEASON: return "postseason_game_logs"
            case _: return None
    

class StatsPeriod(BaseModel):

    # ATTRIBUTES
    type: StatsPeriodType = StatsPeriodType.REGULAR_SEASON
    year: str = None

    # DATE RANGE
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # SPLIT
    split: Optional[str] = None

    # STATS
    # FILLED IN SHOWDOWN BOT CLASS
    stats: Optional[dict[str, Any]] = None

    def __init__(self, **data) -> None:

        # CHANGE TO DATE RANGE IF MID-SEASON
        type = StatsPeriodType(data.get('type', StatsPeriodType.REGULAR_SEASON.value))
        try:
            year = int(data.get('year', None))
        except:
            year = None
        today = date.today()
        if type == StatsPeriodType.REGULAR_SEASON and today.month < 10 and year == today.year:
            data['type'] = StatsPeriodType.DATE_RANGE.value
            data['start_date'] = f'{year}-03-01'
            data['end_date'] = f'{year}-10-15'

        super().__init__(**data)

        # VALIDATE ATTRIBUTES
        if not self.type.enable_date_range:
            self.start_date = None
            self.end_date = None

        if not self.type.enable_split:
            self.split = None

        if self.split:
            self.split = self.split.strip()
            if len(self.split) == 0:
                self.split = None
        

    @property
    def id(self) -> str:
        values = [self.type.value, self.start_date, self.end_date, self.split]
        return "-".join([str(v).replace('/','-') for v in values if v is not None])
    
    @property
    def is_date_range(self) -> bool:
        return self.start_date and self.end_date
    
    @property
    def string(self) -> str:
        match self.type:
            case StatsPeriodType.REGULAR_SEASON: return "REGULAR SEASON"
            case StatsPeriodType.DATE_RANGE:
                dates_formatted_list = [datetime.combine(dt, datetime.min.time()).strftime("%b %d") for dt in [self.start_date, self.end_date]]
                dates_split = " to ".join(dates_formatted_list)
                if len(dates_formatted_list) == 2:
                    if dates_formatted_list[0] == dates_formatted_list[1]:
                        return f"{dates_formatted_list[0]}"
                return f"{dates_split}"
            case StatsPeriodType.POSTSEASON: return f"POSTSEASON"
            case StatsPeriodType.SPLIT: return f"SPLIT ({self.split or 'N/A'})"
    
    @property
    def empty_message(self) -> str:
        match self.type:
            case StatsPeriodType.REGULAR_SEASON: return "No regular season data available"
            case StatsPeriodType.DATE_RANGE: return f"No data found from {self.string.replace('(', '').replace(')','')}"
            case StatsPeriodType.POSTSEASON: return f"No postseason data available"
            case StatsPeriodType.SPLIT: return f"Split '{self.split or 'N/A'}' not found"

    def reset(self) -> None:
        self.type = StatsPeriodType.REGULAR_SEASON
        self.start_date = None
        self.end_date = None
        self.split = None

    def add_stats_from_logs(self, game_logs:list[dict[str, Any]], year_list: list[int], is_pitcher:bool) -> None:
        """
        Add stats from game logs to the stats dictionary
        
        Args:
            game_logs (list[dict[str, Any]]): List of game logs. Can be regular season or postseason
            year_list (list[int]): List of years to filter by
            is_pitcher (bool): If the player is a pitcher
            team_override (str): Optionally filter out records that don't match the team ID

        Returns:
            None
        """

        # RETURN IF NO GAME LOGS
        if len(game_logs) == 0: return
        
        # ADD STATS TO DICTIONARY
        stats_as_lists: dict[str, list] = {}
        first_year = year_list[0]
        for game_log_data in game_logs:

            # ------------------------
            # CLEAN UP GAME LOG DATA
            # ------------------------

            # REMOVE BAD UNICODE CHARACTERS
            date_game = game_log_data.get('date_game', game_log_data.get('date', None))
            if date_game:
                game_log_data['date_game'] = date_game.replace(u'\xa0', u' ')
                
            # CHECK FOR DATE/YEAR FILTER
            year_from_game_log = convert_to_numeric(str(game_log_data.get('year_game', first_year)))
            year_check = year_from_game_log in year_list
            date_check = True
            game_log_date_str: str = game_log_data.get('date_game', None)
            if self.is_date_range and game_log_date_str:
                game_log_date_str_cleaned = game_log_date_str.split('(')[0].strip().replace('\xa0susp', '')
                is_new_format = game_log_date_str.count('-') >= 2
                if is_new_format:
                    # IN UPGRADED TABLES, DATES ARE IN THIS FORMAT "YYYY-MM-DD)"
                    game_log_date = datetime.strptime(game_log_date_str_cleaned, "%Y-%m-%d").date()
                else:
                    # IN OLD TABLES, DATES ARE IN THIS FORMAT "MMM DD"
                    game_log_date_str_full = f"{game_log_date_str_cleaned} {first_year}"
                    game_log_date = datetime.strptime(game_log_date_str_full, "%b %d %Y").date()
                
                # CHECK IF DATE IS WITHIN RANGE
                date_check = self.start_date <= game_log_date <= self.end_date

                # UPDATE 'date_game' WITH FORMATTED DATE
                game_log_data['date_game'] = game_log_date.strftime("%b %-d")
            
            # TODO: SKIP IF TEAM OVERRIDE IS PRESENT AND TEAM DOESN'T MATCH

            # SKIP ROW IF IT FAILS THE DATE OR YEAR CHECKS
            if not date_check or not year_check:
                continue 

            # ADD TO GAMES PLAYED
            game_log_data['G'] = 1
            innings_text = game_log_data.get('player_game_span', None)
            if innings_text:
                is_start = 'GS' in str(innings_text) or 'SHO' in str(innings_text) or 'CG' in str(innings_text)
                game_log_data['GS'] = int(is_start)
                if is_start:
                    game_log_data['IP_GS'] = game_log_data.get('IP', 0)

            # DECISION
            decision_text = game_log_data.get('player_game_result', None)
            if decision_text and is_pitcher:
                is_win_decision = 'W' in str(decision_text)
                game_log_data['W'] = int(is_win_decision)

            # ------------------------
            # ADD TO AGGREGATED LISTS
            # ------------------------
            for key, value in game_log_data.items():
                if key in stats_as_lists:
                    stats_as_lists[key].append(value)
                else:
                    stats_as_lists[key] = [value]


        stats_agg_type = {'team_ID': 'last',}
        aggregated_data = { 
            k.replace('batters_faced', 'PA'): aggregate_stats(category=k, stats=v, aggregation_method=stats_agg_type.get(k, 'mode')) 
            for k,v in stats_as_lists.items() 
            if k != 'earned_run_avg'
        }

        # CHECK FOR NO-DATA
        if len(aggregated_data) == 0:
            return

        # ADD FIRST AND LAST GAME DATES
        game_dates = stats_as_lists.get('date_game', None)
        if game_dates:
            first_game_date_str: str = str(game_dates[0]).upper().split(' (', 1)[0]
            last_game_date_str: str = str(game_dates[-1]).upper().split(' (', 1)[0]
            aggregated_data['first_game_date'] = first_game_date_str
            aggregated_data['last_game_date'] = last_game_date_str

            # UPDATE STATS PERIOD OBJECT WITH EXACT GAME DATES
            try:
                self.start_date = datetime.strptime(f'{first_game_date_str} {first_year}', "%b %d %Y").date()
                self.end_date = datetime.strptime(f'{last_game_date_str} {first_year}', "%b %d %Y").date()
            except:
                pass

        # FILL IN EMPTY CATEGORIES
        aggregated_data = fill_empty_stat_categories(aggregated_data, is_pitcher)
        
        self.stats = aggregated_data