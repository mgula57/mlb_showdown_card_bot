from enum import Enum
from pydantic import BaseModel, ValidationInfo, field_validator, model_validator
from datetime import date, datetime, timedelta
from typing import Optional, Any
from statistics import mode
import calendar

# INTERNAL
from ..utils.shared_functions import aggregate_stats, convert_to_numeric, fill_empty_stat_categories, convert_to_date, convert_year_string_to_list
from ...shared.team import Team

class StatsPeriodType(str, Enum):

    REGULAR_SEASON = "REGULAR"
    DATE_RANGE = "DATES"
    POSTSEASON = "POST"
    SPLIT = "SPLIT"

    PROJECTED = "PROJECTED"
    REPLACEMENT = "REPLACEMENT"

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

    @property
    def check_for_realtime_stats(self) -> bool:
        return self in [StatsPeriodType.REGULAR_SEASON, StatsPeriodType.DATE_RANGE]

class StatsPeriodDateAggregation(str, Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"

    def date_ranges(self, year:str, start_date:date = None, stop_date:date = None) -> list[tuple[date, date]]:

        # ONLY WORKS ON SINGLE YEAR
        try: 
            year = int(year)
        except: 
            return []
        
        start_date = start_date or datetime.strptime(f"{year}-03-15", "%Y-%m-%d").date()
        stop_date = stop_date or datetime.strptime(f"{year}-10-10", "%Y-%m-%d").date()
        date_ranges: list[tuple[date, date]] = []
        match self:
            case StatsPeriodDateAggregation.DAY:
                # CREATE RUNNING RANGE OF DATES, STARTING FROM MARCH 15 UNTIL OCT 10
                end_date = start_date
                while end_date < stop_date:
                    date_ranges.append((start_date, end_date))
                    end_date = end_date + timedelta(days=1)

                return date_ranges
            
            case StatsPeriodDateAggregation.WEEK:
                # END DATE SHOULD BE SUNDAY OF EACH WEEK
                end_date = start_date
                while end_date < stop_date:
                    days_to_sunday = 6 - end_date.weekday() if end_date.weekday() != 6 else 7
                    end_date = min(end_date + timedelta(days=days_to_sunday), stop_date)
                    date_ranges.append((start_date, end_date))

                return date_ranges
            
            case StatsPeriodDateAggregation.MONTH:
                # CHECK IF START DATE IS AFTER 18TH OF THE MONTH
                # IF SO COMBINE WITH NEXT MONTH, ENDING AT NEXT MONTH'S END
                # EX: MARCH 19 - APRIL 30
                end_date = start_date
                if start_date.day > 18:
                    # MOVE END DATE TO END OF MONTH OR STOP DATE
                    next_month = start_date.month + 1
                    # GET THE LAST DAY OF THE NEXT MONTH
                    last_day = calendar.monthrange(start_date.year, next_month)[1]
                    end_date = min(date(start_date.year, next_month, last_day), stop_date)
                    date_ranges.append((start_date, end_date))
                
                while end_date < stop_date:
                    
                    # GET THE LAST DAY OF THE NEXT MONTH
                    next_month = end_date.month + 1
                    last_day = calendar.monthrange(start_date.year, next_month)[1]
                    end_date = min(date(start_date.year, next_month, last_day), stop_date)
                    date_ranges.append((start_date, end_date))
                
                return date_ranges

    def get_first_date_of_aggregation(self, end_date:date) -> date:
        match self:
            case StatsPeriodDateAggregation.DAY:
                return end_date
            case StatsPeriodDateAggregation.WEEK:
                return end_date - timedelta(days=6)
            case StatsPeriodDateAggregation.MONTH:
                return date(end_date.year, end_date.month, 1)

class StatsPeriodYearType(str, Enum):
    SINGLE_YEAR = "SINGLE_YEAR"
    MULTI_YEAR = "MULTI_YEAR"
    FULL_CAREER = "FULL_CAREER"


class StatsPeriod(BaseModel):

    # ATTRIBUTES
    year: str
    type: StatsPeriodType = StatsPeriodType.REGULAR_SEASON

    # MULTI-YEAR
    year_list: list[int] = []
    year_type: StatsPeriodYearType = StatsPeriodYearType.SINGLE_YEAR
    is_full_career: bool = False
    is_multi_year: bool = False

    # DATE RANGE
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # SPLIT
    split: Optional[str] = None

    # SOURCE
    source: str = 'Unknown'

    # STATS
    # FILLED IN SHOWDOWN BOT CLASS
    stats: Optional[dict[str, Any]] = None

    # ADDITIONAL INFO
    display_text: Optional[str] = None
    disable_display_text_on_card: Optional[bool] = None

    def model_post_init(self, __context):

        # ADJUSTMENTS
        self._check_and_apply_current_season_adjustment()

        # FLAG MULTI-YEAR
        if self.year.upper() == 'CAREER':
            self.is_full_career = True
            self.is_multi_year = True
            self.year_type = StatsPeriodYearType.FULL_CAREER
        elif self.year_list and len(self.year_list) > 1:
            self.is_multi_year = True
            self.year_type = StatsPeriodYearType.MULTI_YEAR
        else:
            self.is_multi_year = False
            self.year_type = StatsPeriodYearType.SINGLE_YEAR

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

        self.display_text = self._display_text()
        

    # ---------------------------------
    # VALIDATORS
    # ---------------------------------

    @model_validator(mode="before")
    def ensure_required_inputs(cls, values: dict) -> dict:

        if not isinstance(values, dict):
            # IF VALUES IS NOT A DICT, RETURN AS-IS (OR RAISE AN ERROR)
            return values

        # FORCE THESE ATTRIBUTES TO RUN
        required_attributes = [
            'year_list', 'is_multi_year', 'is_full_career', 
        ]
        for attr in required_attributes:
            if attr not in values.keys():
                values[attr] = None

        return values

    @field_validator('year', mode='before')
    def clean_year(cls, year:str) -> str:
        return str(year).upper()

    @field_validator('year_list', mode='before')
    def parse_year_list(cls, year_list:list[int], info:ValidationInfo) -> list[int]:

        if year_list is not None:
            if len(year_list) > 0:
                return year_list
        values = info.data
        year:str = values.get('year', '')
        stats:dict = values.get('stats', {})
        all_years_played:list[str] = stats.get('years_played', [])
        return convert_year_string_to_list(year_input=year, all_years_played=all_years_played)

    @field_validator('is_full_career', mode='before')
    def parse_is_full_career(cls, is_full_career:bool, info:ValidationInfo) -> bool:
        if is_full_career:
            return is_full_career
        
        year:str = info.data.get('year', '')
        return year.upper() == 'CAREER'
    
    @field_validator('is_multi_year', mode='before')
    def parse_is_multi_year(cls, is_multi_year:bool, info:ValidationInfo) -> bool:
        if is_multi_year:
            return is_multi_year
        
        year_list:list[int] = info.data.get('year_list', [])
        return len(year_list) > 1
    
    # ---------------------------------
    # PROPERTIES
    # ---------------------------------

    @property
    def id(self) -> str:
        values = [self.type.value, self.split]
        return "-".join([str(v).replace('/','-') for v in values if v is not None])
    
    @property
    def is_date_range(self) -> bool:
        return self.start_date and self.end_date
    
    @property
    def year_int(self) -> int:
        """
        Returns the year as an integer if it is a single year, otherwise returns None.
        """
        if len(self.year_list) == 1:
            return self.year_list[0]
        return None
    
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

    @property
    def check_for_realtime_stats(self) -> bool:
        """
        Returns True if the stats period type is REGULAR_SEASON or DATE_RANGE and the user inputted date range includes the current date.
        This is used to determine if realtime stats should be fetched from the MLB API.
        """
        is_today_included = False if self.end_date is None else self.end_date >= date.today()
        return self.type.check_for_realtime_stats and is_today_included
    
    @property
    def is_this_year(self) -> bool:
        """
        Returns True if the stats period is for the current year.
        """
        current_year = date.today().year
        return self.year_int == current_year if self.year_int else False

    @property
    def is_during_current_season(self) -> bool:
        """
        Returns True if the stats period is during the current season.
        """

        try: year = int(self.year)
        except: year = None
        if year is None: return False

        today = date.today()
        if (today.month < 10 and year == today.year):
            return True
        
        return False

    @property
    def first_year(self) -> Optional[int]:
        """
        Returns the first year in the stats period.
        """
        if len(self.year_list) > 0:
            return self.year_list[0]
        return None
    
    @property
    def last_year(self) -> Optional[int]:
        """
        Returns the last year in the stats period.
        """
        if len(self.year_list) > 0:
            return max(self.year_list)
        return None

    @property
    def is_during_statcast_era(self) -> bool:
        """
        Returns True if the stats period is during the Statcast era (2015 and later).
        """

        if self.last_year is None:
            return False
        
        return self.last_year >= 2015

    @property
    def year_list_as_strs(self) -> str:
        """Returns the year list as a list of strings. Orders in ascending order."""
        return [str(year) for year in sorted(self.year_list)]

    # ---------------------------------
    # METHODS
    # ---------------------------------

    def _check_and_apply_current_season_adjustment(self) -> None:
        """
        If the card is during the current season, we want to change it to a date range.
        This is so that the card shows the date range on the image.
        """

        # CHECK IF SINGLE YEAR
        try: year = int(self.year)
        except: year = None
        if year is None: return

        # CHECK TYPE
        if self.type != StatsPeriodType.REGULAR_SEASON:
            return
        
        # CHECK IF BEFORE OCT 1 OF THIS YEAR
        if not self.is_during_current_season:
            return

        self.type = StatsPeriodType.DATE_RANGE
        self.start_date = date(year=year, month=3, day=1)
        self.end_date = date(year=year, month=10, day=15)

    def reset(self) -> None:
        self.type = StatsPeriodType.REGULAR_SEASON
        self.start_date = None
        self.end_date = None
        self.split = None

        self._check_and_apply_current_season_adjustment()
        self.display_text = self._display_text()

    def add_stats_from_game_logs(self, game_logs:list[dict[str, Any]], is_pitcher:bool, team_override:Team = None) -> None:
        """
        Add stats from game logs to the stats dictionary
        
        Args:
            game_logs (list[dict[str, Any]]): List of game logs. Can be regular season or postseason
            is_pitcher (bool): If the player is a pitcher
            team_override (Team, optional): Team override for filtering game logs

        Returns:
            None
        """

        # RETURN IF NO GAME LOGS
        if len(game_logs) == 0: return
        
        # ADD STATS TO DICTIONARY
        stats_as_lists: dict[str, list] = {}
        first_year = self.year_list[0]
        last_year = self.year_list[-1]
        is_multi_year = first_year != last_year
        for game_log_data in game_logs:

            # ------------------------
            # CLEAN UP GAME LOG DATA
            # ------------------------

            # REMOVE BAD UNICODE CHARACTERS
            date_game = game_log_data.get('date_game', game_log_data.get('date', None))
            if date_game:
                game_log_data['date_game'] = date_game.replace(u'\xa0', u' ')
                
            # CHECK FOR DATE/YEAR FILTER
            
            # IF DATE RANGE BASED, CHECK DATES
            date_check = True
            game_log_date_str: str = game_log_data.get('date_game', None)
            is_new_format = game_log_date_str.count('-') >= 2 if game_log_date_str else False

            # OLDER FORMAT HAD DEDICATED YEAR COLUMN
            doesnt_have_dedicated_year_column = self.type == StatsPeriodType.POSTSEASON and is_new_format and game_log_date_str
            default_year = game_log_date_str.split('-', 1)[0] if doesnt_have_dedicated_year_column else first_year
            year_from_game_log = convert_to_numeric(str(game_log_data.get('year_game', default_year)))
            year_check = year_from_game_log in self.year_list

            if self.is_date_range and game_log_date_str:
                game_log_date = convert_to_date(game_log_date_str, default_year)
                
                # CHECK IF DATE IS WITHIN RANGE
                date_check = self.start_date <= game_log_date <= self.end_date

                # UPDATE 'date_game' WITH FORMATTED DATE
                game_log_data['date_game'] = game_log_date.strftime("%b %-d")
            
            # SKIP IF TEAM OVERRIDE IS PRESENT AND TEAM DOESN'T MATCH
            if team_override and game_log_data.get('team_ID', 'n/a') != team_override.value:
                continue

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

            # UPDATE STATS PERIOD OBJECT WITH EXACT GAME DATES
            try:
                self.start_date = datetime.strptime(f'{first_game_date_str} {first_year}', "%b %d %Y").date()
                self.end_date = datetime.strptime(f'{last_game_date_str} {last_year}', "%b %d %Y").date()

                # FORMAT MULTI-YEAR DATE RANGES DIFFERENTLY
                # EX: 6/3/00
                if is_multi_year:
                    first_game_date_str = self.start_date.strftime("%-m/%-d/%y")
                    last_game_date_str = self.end_date.strftime("%-m/%-d/%y")

            except:
                import traceback
                
                pass

            aggregated_data['first_game_date'] = first_game_date_str
            aggregated_data['last_game_date'] = last_game_date_str

        # FILL IN EMPTY CATEGORIES
        aggregated_data = fill_empty_stat_categories(stats_data=aggregated_data, is_pitcher=is_pitcher, is_game_logs=True)
        
        self.stats = aggregated_data
        self.display_text = self._display_text()

    def _display_text(self) -> str:
        """
        Generate summary text for the stats period. Displayed on the card image.
        
        Returns:
            str: Summary text
        """
        text:str = None
        match self.type:
            case StatsPeriodType.POSTSEASON:
                text = 'POSTSEASON'
            case StatsPeriodType.DATE_RANGE:
                if self.stats is None:
                    return None
                text_list = [self.stats.get('first_game_date', None), self.stats.get('last_game_date', None)]
                text_list = [t for t in text_list if t]
                game_1_comp = self.stats.get('first_game_date', 'g1').strip()
                game_2_comp = self.stats.get('last_game_date', 'g2').strip()
                is_single_game = game_1_comp == game_2_comp            
                text = game_1_comp if is_single_game else ' - '.join(text_list)
            case StatsPeriodType.SPLIT:
                text = self.split.upper()
            case StatsPeriodType.REGULAR_SEASON:
                text = self.year
            case StatsPeriodType.PROJECTED:
                text = f"PROJECTED"
            case StatsPeriodType.REPLACEMENT:
                text = f"REPLACEMENT"
        return text