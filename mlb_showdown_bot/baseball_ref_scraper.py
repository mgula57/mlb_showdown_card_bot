
import pandas as pd
import numpy as np
import cloudscraper
import re
import os
from pathlib import Path
import json
import string
import math
import statistics
from statistics import mode
import operator
from bs4 import BeautifulSoup
from pprint import pprint
from datetime import datetime
from difflib import SequenceMatcher
import unidecode
from thefuzz import fuzz
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from .classes.team import Team
    from .classes.accolade import Accolade
    from .classes.stats_period import StatsPeriod, StatsPeriodType
except ImportError:
    # USE LOCAL IMPORT
    from classes.team import Team
    from classes.accolade import Accolade
    from classes.stats_period import StatsPeriod, StatsPeriodType

class BaseballReferenceScraper:

# ------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------

    def __init__(self, name:str, year:str, stats_period:StatsPeriod = StatsPeriod(), ignore_cache:bool=False, disable_cleaning_cache:bool=False, cache_folder_path:str=None, disable_stats_period_range_updates:bool=False) -> None:

        self.year_input = year.upper()
        is_full_career = year.upper() == 'CAREER'
        if is_full_career:
            year = 'CAREER'
        elif '(' in year:
            year = int(year[:4])
        elif '-' in year:
            # RANGE OF YEARS
            years = year.split('-')
            year_start = int(years[0].strip())
            year_end = int(years[1].strip())
            year = list(range(year_start,year_end+1))
        elif '+' in year:
            years = year.split('+')
            year = [int(x.strip()) for x in years]

        self.name = name
        self.error = None
        self.warnings: list[str] = []
        self.source = None
        self.cache_folder_path = cache_folder_path or os.path.join(Path(os.path.dirname(__file__)),'cache_data')
        self.ignore_cache = ignore_cache
        self.disable_cleaning_cache = disable_cleaning_cache
        self.disable_stats_period_range_updates = disable_stats_period_range_updates
        self.load_time = None
        self.stats_period = stats_period
        
        # PARSE MULTI YEARS
        if isinstance(year, list):
            is_multi_value_list = len(year) > 1
            self.is_multi_year = is_multi_value_list
            self.years = year
        else:
            self.is_multi_year = False
            self.years = [year]
        self.is_full_career = self.years == ['CAREER']

        # CHECK FOR TEAM OVERRIDE
        self.team_override = None
        for team_id in [team.value for team in Team]:
            team_match = f'({team_id})' in self.name.upper()
            if team_match and not self.is_multi_year and not is_full_career and stats_period.split is None:
                self.team_override = team_id

        # CHECK FOR TYPE OVERRIDE
        self.pitcher_override = '(PITCHER)' if ( '(PITCHER)' in self.name.upper() or '(PITCHING)' in self.name.upper() ) else None
        self.hitter_override = '(HITTER)' if ( '(HITTER)' in self.name.upper() or '(HITTING)' in self.name.upper() ) and self.pitcher_override is None else None
        self.player_type_override = None if (self.pitcher_override is None and self.hitter_override is None) else f"{self.hitter_override if self.hitter_override else ''}{self.pitcher_override if self.pitcher_override else ''}"

        # CHECK FOR BASEBALL REFERENCE ID
        self.is_name_a_bref_id = any(char.isdigit() for char in name)
        if self.is_name_a_bref_id:
            self.baseball_ref_id = name.split(' ')[0].lower()
        else:
            # CHECK DEFAULT CSV
            default_bref_id = self.__check_for_default_bref_id(name=name, years=self.years)
            if default_bref_id:
                self.baseball_ref_id = default_bref_id
            else:
                # SEARCH GOOGLE
                self.baseball_ref_id = self.search_google_for_b_ref_id(name, year)

        self.first_initial = self.baseball_ref_id[:1]

        # STORE BASEBALL REFERENCE ID USED FOR TRENDS DATA QUERY
        if "ohtansh01" in self.baseball_ref_id:
            self.baseball_ref_id_used_for_trends = f"ohtansh01 {'(Pitcher)' if self.pitcher_override else '(Hitter)'}"
        else:
            self.baseball_ref_id_used_for_trends = self.baseball_ref_id

# ------------------------------------------------------------------------
# SCRAPE WEBSITES

    def __check_for_default_bref_id(self, name:str, years: list[str]) -> str:
        """Check for player name string in default csv with names and bref ids

        Purpose is to see if bot can avoid needing to scrape Google.

        Args:
          name: Full name of Player
          years: List of years for Player stats

        Returns:
          BrefId (If found), otherwise None
        """ 
        
        # LOAD CSV
        player_id_filepath = os.path.join(Path(os.path.dirname(__file__)),'player_ids.csv')
        player_ids_pd = pd.read_csv(player_id_filepath)
        max_year = player_ids_pd['year_end'].max()

        # CLEAN NAME AND YEAR RANGE FOR CARD
        name_cleaned = unidecode.unidecode(name.replace("'", "").replace(".", "").lower().strip().split('(')[0].strip())
        try:
            year_ints = [int(y) for y in years]
            year_start = min( min(year_ints), max_year)
            year_end = min( max(year_ints), max_year)
        except:
            year_start = None
            year_end = None

        # FILTER PLAYERS FOR YEAR(S)
        if year_start and year_end:
            player_ids_pd = player_ids_pd.loc[(player_ids_pd['year_start'] <= year_end) & (player_ids_pd['year_end'] >= year_start)]
        
        # DEFINE SIMILARITY SCORE
        player_ids_pd['name'] = player_ids_pd['name'].apply(lambda x: unidecode.unidecode(x))
        player_ids_pd['similarity_score'] = player_ids_pd['name'].apply(lambda x: fuzz.ratio(name_cleaned, x))

        # FILTER BY SIMILARITY SCORE
        player_ids_pd_filtered = player_ids_pd.loc[player_ids_pd['similarity_score'] > 86].sort_values(by=['similarity_score', 'bwar', 'pa', 'ip'], ascending=[False, False, False, False])
        results_count = len(player_ids_pd_filtered)

        if results_count == 0:
            return None
        else:
            # RETURN FIRST RESULT OF player_ids_pd_filtered
            bref_id = player_ids_pd_filtered.head(1)['brefid'].values[0]
            return bref_id if len(bref_id) > 0 else None

    def search_google_for_b_ref_id(self, name:str, year:str) -> str:
        """Convert name to a baseball reference Player ID.

        Goes by rank on google search for search: 'baseball reference "name" "year"'.
        This is needed to find the player_id used to scrape baseball reference.

        Args:
          name: Full name of Player
          year: Year for Player stats

        Raises:
          AttributeError: Cannot find Baseball Ref Page for name/year combo.

        Returns:
          Baseball Reference Id String (ex: 'Mike Piazza' -> 'piazzmi01').
        """

        name_for_url = name.replace(' ','+')

        # SET RESULT LIMIT TO INCREASE SPEED AND MINIMIZE ERRORS
        result_limit = 4
        url_search_name_and_year = 'https://www.google.com/search?q=baseball+reference+{}+{}+stats&num={}'.format(name_for_url, year, result_limit)
        soup_search_name_and_year = self.__soup_for_url(url_search_name_and_year)

        last_initial = self.__name_last_initial(name)
        search_results = soup_search_name_and_year.find_all("a", href=re.compile("https://www.baseball-reference.com/players/{}/".format(last_initial)))
        
        # GOOGLE WILL BLOCK REQUESTS IF IT DETECTS THE BOT.
        if len(soup_search_name_and_year.find_all(text="Why did this happen?")) > 0:
            self.error = 'Google has an overload of requests coming from your IP Address. Wait a few minutes and try again.'
            raise RuntimeError(self.error)

        # NO BASEBALL REFERENCE RESULTS FOR THAT NAME AND YEAR
        if search_results == []:
            self.error = f'Cannot Find BRef Page for {name} in {year}'
            raise AttributeError(self.error)
        
        top_result_url = search_results[0]["href"]
        player_b_ref_id = top_result_url.split('.shtml')[0].split('/')[-1]
        return player_b_ref_id

    def __soup_for_url(self, url:str, is_baseball_ref_page=False) -> BeautifulSoup:
        """Converts html to BeautifulSoup object.

        Args:
          url: URL for the request.
          is_baseball_ref_page: Bool to denote if the URL is a link to baseball-reference.com.

        Returns:
          BeautifulSoup object with website data.
        """

        html = self.html_for_url(url)

        if is_baseball_ref_page:
            # A LOT OF BREF STATS ARE LOADED THROUGH JAVASCRIPT, BUT CAN BE FOUND IN COMMENTED HTML
            html = html.replace("<!--","")

        soup = BeautifulSoup(html, "lxml")

        return soup

    def html_for_url(self, url:str) -> str:
        """Make request for URL to get HTML

        Args:
          url: URL for the request.

        Raises:
          TimeoutError: 502 - BAD GATEWAY
          TimeoutError: 429 - TOO MANY REQUESTS TO BASEBALL REFERENCE

        Returns:
          HTML string for URL request.
        """

        scraper = cloudscraper.create_scraper()
        html = scraper.get(url)

        if html.status_code == 502:
          self.error = "502 - BAD GATEWAY"
          raise TimeoutError(self.error)
        if html.status_code == 429:
          website = url.split('//')[1].split('/')[0]
          self.error = f"429 - TOO MANY REQUESTS TO {website}. PLEASE TRY AGAIN IN A FEW MINUTES."
          raise TimeoutError(self.error)

        return html.text

# ------------------------------------------------------------------------
# PARSING HTML
# ------------------------------------------------------------------------

    def player_statline(self) -> dict:
        """Scrape baseball-reference.com to get all relevant stats

        Args:
          None

        Returns:
          Dict with all categories and stats.
        """

        start_time = datetime.now()

        # CHECK IN LOCAL CACHE
        cached_data = self.load_cached_data(self.cache_filename)
        if cached_data:
            self.source = 'Local Cache'
            end_time = datetime.now()
            self.load_time = round((end_time - start_time).total_seconds(),2)
            return cached_data
        
        # STANDARD STATS PAGE HAS MOST RELEVANT STATS NEEDED
        url_for_homepage_stats = f'https://www.baseball-reference.com/players/{self.first_initial}/{self.baseball_ref_id}.shtml'
        soup_for_homepage_stats = self.__soup_for_url(url_for_homepage_stats, is_baseball_ref_page=True)

        # DEFINE YEARS TO LOOP THROUGH
        years_for_loop = self.years
        is_full_career = self.is_full_career
        is_multi_year = self.is_multi_year
        years_played = self.__years_played_list(homepage_soup=soup_for_homepage_stats)
        years_played_as_ints = [int(y) for y in years_played]

        # ACCOUNT FOR CAREER CARDS THAT DONT HAVE FULL STATS AVAILABLE
        # TREAT AS IF THE USER INPUTTED THE EXACT YEAR RANGE INSTEAD OF CAREER.
        #  - NEGRO LEAGUERS THAT EVENTUALLY PLAYED IN MLB
        #  - PRE 1914 PITCHERS
        all_leagues_played_in = self.__all_leagues_played(soup_for_homepage_stats)
        played_in_negro_leagues = any([lg in ['NAL','NAL','NN2','NSL'] for lg in all_leagues_played_in])
        has_reduced_stats = ( min(years_played_as_ints) < 1914 or played_in_negro_leagues ) and is_full_career
        if has_reduced_stats:
            years_for_loop = years_played_as_ints
            is_multi_year = True
            is_full_career = False

        # PARSE OVERALL TYPE(S) ACROSS YEAR(S)
        positions_and_games = self.positions_and_games_played(soup_for_homepage_stats=soup_for_homepage_stats, years=years_played)
        overall_type = self.type(positions_dict=positions_and_games, year=self.year_input)

        # ALSO QUERY ADVANCED STATS
        page_suffix = '-bat' if overall_type == 'Hitter' else '-pitch'
        url_advanced_stats = 'https://www.baseball-reference.com/players/{}/{}{}.shtml'.format(self.first_initial, self.baseball_ref_id, page_suffix)
        soup_for_advanced_stats = self.__soup_for_url(url_advanced_stats, is_baseball_ref_page=True)

        # ITERATE THROUGH YEARS
        master_stats_dict = {}
        is_data_from_statcast = False
        has_ran_oaa = False
        for year in years_for_loop:
            stats_dict = {'bref_id': self.baseball_ref_id, 'bref_url': url_for_homepage_stats}
            
            # DEFENSE
            # RETURNED AS DICT WITH POSITIONS AND dWAR
            # EX: {'positions': {'C': {'g': 100}, '1B': {'g': 50}}, 'dWAR': 2.0}
            positional_fielding = self.positions_and_defense(soup_for_homepage_stats=soup_for_homepage_stats,year=year,overall_positions_and_games=positions_and_games)

            # HANDLE SCENARIO WHERE NO FIELDING DATA EXISTS BECAUSE PLAYER IS DH
            positions_dict = positional_fielding.get('positions', {})
            is_positionless = False
            if len(positions_dict) == 0 and overall_type == 'Hitter':
                
                dh_appearances = self.__appearances_for_position(soup_for_homepage_stats=soup_for_homepage_stats, year=year, position='DH')
                is_positionless = dh_appearances is None
                positional_fielding['positions'] = { 'DH': {'g': dh_appearances } }
            
            stats_dict.update(positional_fielding)

            # HAND / TYPE
            type:str = None
            if not is_positionless:
                type = self.type(positions_dict=stats_dict['positions'],year=year)

            # COVER THE CASES:
            #   - NOT HAVING A TYPE DUE TO BEING A DH
            #   - NOT HAVING DATA FOR A PARTICULAR YEAR (EX: JOHN SMOLTZ 2000)
            #   - TYPE NOT MATCHING OVERALL TYPE (ACROSS MULTIPLE YEARS IF APPLICABLE)

            # IN NEWER BREF TABLES DH IS NOT LISTING IN FIELDING
            if type is None and (overall_type or '') == 'Hitter':
                type = 'Hitter'

            # CHECK IF `DID NOT PLAY` MESSAGE EXISTS FOR THE YEAR
            table_prefix = 'batting' if (type or '') == 'Hitter' else 'pitching'
            rows_for_year = soup_for_advanced_stats.find_all('tr',attrs={'id': f'players_standard_{table_prefix}.{year}'})
            for row in rows_for_year:
                if 'Did not play' in row.get_text():
                    type = None
                    break
            
            # CHECK IF SEASON IS SKIPPED (EX: JOSH GIBSON 1941)
            players_standard_batting = soup_for_advanced_stats.find('table', attrs={'id': f'players_standard_{table_prefix}'})
            if players_standard_batting:
                skipped_year_rows = players_standard_batting.find_all('tr',attrs={'class': 'spacer partial_table'})
                for row in skipped_year_rows:
                    header = row.find('th')
                    if header is None: continue
                    csk = header.get('csk', '').strip()
                    if str(year) == csk:
                        type = None
                        break

            mismatching_type = type != overall_type
            if type is None or mismatching_type:
                continue

            # NATIONALITY
            nationality = self.nationality(soup_for_homepage_stats=soup_for_homepage_stats)

            # ROOKIE STATUS YEAR
            rookie_status_year = self.rookie_status_year(soup_for_homepage_stats=soup_for_homepage_stats)

            # IF HALL OF FAME?
            is_hof = self.is_hof(soup_for_homepage_stats=soup_for_homepage_stats)

            # WAR
            stats_dict.update({'bWAR': self.__bWar(soup_for_homepage_stats, year, type)})

            name = self.player_name(soup_for_homepage_stats)
            stats_dict['type'] = type
            stats_dict['hand'] = self.hand(soup_for_homepage_stats, type)
            stats_dict['hand_throw'] = self.hand(soup_for_homepage_stats, type='Pitcher') # ALWAYS PASS PITCHER TO STORE THROWING HAND
            stats_dict['name'] = name
            stats_dict['years_played'] = years_played
            stats_dict['nationality'] = nationality
            stats_dict['rookie_status_year'] = rookie_status_year
            stats_dict['is_hof'] = is_hof
            stats_dict['is_rookie'] = False if is_full_career or is_multi_year or rookie_status_year is None else ( int(year) <= rookie_status_year )
            
            # ADVANCED STATS
            # STORES HITTING AND HITTING AGAINST STATS THAT ARE NEEDED FOR CARD CREATION
            advanced_stats = self.parse_advanced_stats(soup_for_advanced_stats=soup_for_advanced_stats, type=type, year=year, ignore_ip_per_gs=has_reduced_stats)
            stats_dict.update(advanced_stats)

            # ICON THRESHOLDS
            icon_threshold_bools = self.__add_icon_threshold_bools(type=type, year=year, stats_dict=stats_dict, homepage_soup=soup_for_homepage_stats)
            stats_dict.update(icon_threshold_bools)
            
            # FILL BLANKS IF NEEDED
            keys_to_fill = ['SH','GIDP','IBB','HBP','SF','SB','CS',]
            for key in keys_to_fill:
                if key in stats_dict.keys():
                    raw_value = stats_dict[key]
                    if len(str(raw_value)) == 0:
                        stats_dict[key] = 0

            if self.__is_pitcher_from_1901_to_1918(year=year,type=type):
                team_id = self.__team_w_most_games_played(type, soup_for_homepage_stats, years_filter_list=[int(year)])
                league_id = stats_dict.get('lg_ID', 'MLB')
                if self.__is_team_id_multiple(team_id):
                    team_id, league_id = self.__parse_team_after_trade(soup_for_homepage_stats=soup_for_homepage_stats,year=year,type=type)
                stats_dict['team_ID'] = team_id
                stats_dict['lg_ID'] = league_id

            # FULL CAREER
            is_hitter = type == 'Hitter'
            if is_full_career:
                stats_dict['team_ID'] = self.__team_w_most_games_played(type, soup_for_homepage_stats)
                sprint_speed_list = []
                if is_hitter:
                    for year in years_played:
                        sprint_speed = self.statcast_sprint_speed(name=name, year=year)
                        if sprint_speed:
                            sprint_speed_list.append(sprint_speed)
                if len(sprint_speed_list) > 0:
                    stats_dict['sprint_speed'] = sum(sprint_speed_list) / len(sprint_speed_list)
                else:
                    stats_dict['sprint_speed'] = None
            elif is_hitter:
                stats_dict['sprint_speed'] = self.statcast_sprint_speed(name=name, year=year)
            is_data_from_statcast = stats_dict.get('sprint_speed', None) is not None

            # OUTS ABOVE AVERAGE (2016+)
            if not has_ran_oaa and is_hitter: # ONLY NEEDS TO RUN ONCE FOR MULTI-YEAR
                years_list = years_played if self.is_full_career else self.years
                years_as_ints = [int(y) for y in years_list]
                oaa_dict = self.statcast_outs_above_average_dict(name=name, years=years_as_ints)
                stats_dict['outs_above_avg'] = oaa_dict
                is_data_from_statcast = len(stats_dict['outs_above_avg']) > 0 if stats_dict['outs_above_avg'] else False
                current_positions = stats_dict.get('positions', {})
                for position, oaa in oaa_dict.items():
                    dict_for_position = current_positions.get(position, None)
                    if dict_for_position:
                        dict_for_position['oaa'] = round(oaa, 5)
                        current_positions[position] = dict_for_position
                stats_dict['positions'] = current_positions
                has_ran_oaa = True
            
            # DERIVE 1B 
            triples = int(stats_dict.get('3B', 0))
            doubles = int(stats_dict.get('2B', 0))
            stats_dict['1B'] = int(stats_dict.get('H', 0)) - int(stats_dict.get('HR', 0)) - triples - doubles
            master_stats_dict[year] = stats_dict
        
        if is_multi_year:
            # COMBINE INDIVIDUAL YEAR DATA
            stats_dict.update(self.__combine_multi_year_dict(yearly_stats_dict=master_stats_dict, years=years_for_loop))
            stats_dict['team_ID'] = self.__team_w_most_games_played(type, soup_for_homepage_stats, years_filter_list=years_for_loop)
        
        # PARSE ACCOLADES IN TOTAL
        stats_dict['accolades'] = self.__accolades_dict(soup_for_homepage_stats=soup_for_homepage_stats, years_included=years_for_loop)

        # STATS WINDOW DATA
        if self.stats_period.type.uses_game_logs:
            # STORE REG SEASON GAMES FOR HITTERS. NEEDED FOR SPEED/DEFENSE CALCS
            if self.stats_period.type.is_regular_season_games_stat_needed and stats_dict.get('type', 'n/a') == 'Hitter':
                stats_dict['G_RS'] = stats_dict.get('G', 0)
            game_log_data = self.game_log_data(type=type, years=years_for_loop)
            if game_log_data:
                stats_dict.update(game_log_data)

        # FIX EMPTY STRING DATA
        empty_str_fields_for_test = ['batting_avg', 'onbase_perc', 'slugging_perc', 'onbase_plus_slugging']
        for field in empty_str_fields_for_test:
            if str(stats_dict.get(field, 0.00)) == '':
                stats_dict[field] = 0.00

        # SAVE DATA        
        self.source = f"Baseball Reference{'/Baseball Savant' if is_data_from_statcast else ''}"
        self.__cache_data_locally(data=stats_dict, filename=self.cache_filename)
        
        # CALC LOAD TIME
        end_time = datetime.now()
        self.load_time = round((end_time - start_time).total_seconds(),2)
        
        return stats_dict
    
    def __positions_table_records(self, soup_for_homepage_stats:BeautifulSoup, year:str) -> dict[str, dict]:
        """Parse standard positions and fielding metrics into a dictionary.

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats on homepage.
          year: Year for Player stats

        Returns:
          List of BeautifulSoup objects for each position and year.
        """

        is_full_career = year == 'CAREER'
        if is_full_career:
            fielding_table = soup_for_homepage_stats.find('div', attrs = {'id': re.compile('div_standard_fielding|div_players_standard_fielding')})
            fielding_table_footer = fielding_table.find('tfoot')
            all_footer_rows = fielding_table_footer.find_all('tr')
            
            # BREF NOW DOESN'T SHOW THE POSITION NAME WHEN IT'S A TOTAL ROW WITH ONLY 1 POSITION
            # LOOK AT THE LAST RECORD TO GET THE POSITION NAME
            if len(all_footer_rows) == 1:
                career_total_row: BeautifulSoup = all_footer_rows[0]
                position_name = self.__extract_text_for_element(object=career_total_row, tag='td', attr_key='data-stat', values=['pos', 'f_position'])
                if position_name.strip() == '':

                    # GET POSITION NAME FROM THE FIRST ROW
                    replacement_position_object = soup_for_homepage_stats.find('tr', attrs = {'id': re.compile(f':standard_fielding|players_standard_fielding\.')})
                    replacement_position = self.__extract_text_for_element(object=replacement_position_object, tag='td', attr_key='data-stat', values=['pos', 'f_position'])
                    career_total_row.insert(0, BeautifulSoup(f'<td data-stat="f_position">{replacement_position}</td>', 'html.parser'))
                    all_footer_rows = [career_total_row]
            
            return all_footer_rows
        else:
            return soup_for_homepage_stats.find_all('tr', attrs = {'id': re.compile(f'{year}:standard_fielding|players_standard_fielding\.{year}')})
        
    def positions_and_games_played(self, soup_for_homepage_stats:BeautifulSoup, years:list[str]) -> list[str]:
        """Parse standard positions and fielding metrics into a dictionary.

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats on homepage.
          year: Year for Player stats

        Returns:
          Dict with positions and games played over the period of years. Ex: { 'C': {'g': 100}, '1B': {'g': 50} }
        """
        
        positions_and_games_played: dict[str: dict[str,int]] = {}
        for year in years:
            fielding_metrics_by_position = self.__positions_table_records(soup_for_homepage_stats=soup_for_homepage_stats, year=year)
            for position_data in fielding_metrics_by_position:
                team_column = self.__extract_text_for_element(object=position_data, tag='td', attr_key='data-stat', values=['team_ID', 'team_name_abbr'])
                if team_column:
                    if team_column == 'TOT' or 'TM' in team_column: continue
                position_column = position_data.find('td', attrs={'data-stat': re.compile('pos|f_position')})
                if position_column:
                    position_name: str = position_column.get_text()
                    if position_name != 'TOT' and position_name.strip() != '':
                        existing_games_played = positions_and_games_played.get(position_name, {}).get('g', 0)
                        games_played_text = self.__extract_text_for_element(object=position_data, tag='td', attr_key='data-stat', values=['G', 'games', 'f_games'])
                        games_played = int(games_played_text) if games_played_text != '' else 0
                        existing_games_played += games_played
                        positions_and_games_played[position_name] = {'g': existing_games_played}
        
        # ADD DH APPEARANCES
        games_at_dh = self.__get_dh_appearances(soup_for_homepage_stats, years=[year])
        if games_at_dh:
            positions_and_games_played['DH'] = { 'g': games_at_dh, }

        return positions_and_games_played
    
    def positions_and_defense(self, soup_for_homepage_stats:BeautifulSoup, year:int|str, overall_positions_and_games:dict[str:int]) -> dict[str, dict]:
        """Parse standard positions and fielding metrics into a dictionary.

        Args:
            soup_for_homepage_stats: BeautifulSoup object with all stats on homepage.
            year: Year for Player stats
            overall_positions_and_games: Dict with positions and games played over the players career. Ex: { 'C': {'g': 100}, '1B': {'g': 50} }.

        Returns:
          Dict for each position with details.
        """

        is_full_career = year == 'CAREER'
        fielding_metrics_by_position = self.__positions_table_records(soup_for_homepage_stats=soup_for_homepage_stats, year=year)

        positions_dict = {}
        for position_data in fielding_metrics_by_position:

            # FILTER FOR PARTIAL OR FULL RECORDS
            #  - TOTAL ROW FOR FULL YEAR
            #  - PARTIAL ROW (TEAM SPECIFIC) FOR TEAM OVERRIDE
            is_partial_table_row = 'partial_table' in position_data.get('class', [])
            is_valid_row = (is_partial_table_row) if self.team_override else (not is_partial_table_row)
            if not is_valid_row: continue

            # IF TEAM OVERRIDE, CHECK FOR TEAM COLUMN
            if self.team_override:
                team_name = self.__extract_text_for_element(object=position_data, tag='td', attr_key='data-stat', values=['team_ID', 'team_name_abbr'])
                if team_name:
                    if team_name != self.team_override: continue

            position_name = self.__extract_text_for_element(object=position_data, tag='td', attr_key='data-stat', values=['pos', 'f_position'])
            
            # IN UPGRADED TABLES, POSITION CAN BE BLANK FOR PLAYERS WHO PLAYED ONE POSITION THEIR ENTIRE CAREER
            # IF THAT HAPPENS, USE THE POSITION NAME FROM OVERALL GAMES PLAYED
            if is_full_career and position_name == '' and len(overall_positions_and_games) == 1:
                position_name = list(overall_positions_and_games.keys())[0]

            if position_name:
                
                games_played_text = self.__extract_text_for_element(object=position_data, tag='td', attr_key='data-stat', values=['G', 'f_games'])
                games_played = int(games_played_text) if games_played_text else 0

                if position_name != 'TOT':
                    # DRS (2003+)
                    drs_rating_text = self.__extract_text_for_element(object=position_data, tag='td', attr_key='data-stat', values=['bis_runs_total', 'f_drs_total'])
                    drs_rating = None if (drs_rating_text or '') == '' else float(drs_rating_text)
                    
                    # ACCOUNT FOR SHORTENED OR ONGOING SEASONS
                    use_stat_per_yr = False
                    if is_full_career:
                        use_stat_per_yr = True
                    else:
                        today = datetime.today()
                        card_year_end_date = datetime(int(year), 10, 1)
                        is_year_end_date_before_today = today < card_year_end_date
                        drs_is_above_0 = int(drs_rating) > 0 if drs_rating else False
                        use_stat_per_yr = (str(year) == '2020' or is_year_end_date_before_today) and drs_is_above_0
                    
                    if use_stat_per_yr:
                        drs_rating_text = self.__extract_text_for_element(object=position_data, tag='td', attr_key='data-stat', values=['bis_runs_total_per_season', 'f_drs_total_per_year'])
                        drs_rating = None if (drs_rating_text or '') == '' else int(drs_rating_text)

                    # TOTAL ZONE (1953-2003)
                    suffix = '_per_year' if use_stat_per_yr else ''
                    total_zone_text = self.__extract_text_for_element(object=position_data, tag='td', attr_key='data-stat', values=[f'tz_runs_total{suffix}', f'f_tz_runs_total{suffix}'])
                    total_zone_rating = None if (total_zone_text or '') == '' else float(total_zone_text)

                    # UPDATE POSITION DICTIONARY
                    positions_dict[position_name] = {
                        'g': games_played,
                        'tzr': total_zone_rating,
                        'drs': drs_rating,
                    }
        
        # GET DEFENSIVE WAR IN CASE OF LACK OF TZR AVAILABILITY FOR SEASONS < 1952
        # UPDATE: SCRAPE TOTAL WAR AS WELL
        try:
            if is_full_career:
                summarized_header = self.__get_career_totals_row(div_id=re.compile('div_batting_value|div_players_value_batting'),soup_object=soup_for_homepage_stats)
                num_seasons = float(summarized_header.find('th').get_text().split(" ")[0])
                dwar_object = summarized_header.find('td',attrs={'data-stat':re.compile('WAR_def|b_war_def')})
                dwar_rating = float(dwar_object.get_text()) if dwar_object != None else 0
                # USE AVG FOR CAREER
                dwar_rating = round(dwar_rating / num_seasons,2)
            else:
                player_value = soup_for_homepage_stats.find('tr', attrs = {'id': re.compile(f'batting_value.{year}|players_value_batting.{year}')})
                dwar_object = player_value.find('td',attrs={'class':'right','data-stat': re.compile('WAR_def|b_war_def')})
                dwar_rating = dwar_object.get_text() if dwar_object != None else 0
                try:
                    dwar_rating = float(dwar_rating)
                except:
                    dwar_rating = dwar_rating

        except:
            dwar_rating = 0
        
        # CHECK FOR PINCH HITTER
        # PINCH HITTERS WILL NOT HAVE A RECORD IN THE FIELDING TABLE
        is_positions_empty = len(positions_dict) == 0
        metadata = soup_for_homepage_stats.find('div', attrs = {'id': 'meta'})
        if is_positions_empty and metadata:
            # FIND THE HAND TAG IN THE METADATA LIST
            for strong_tag in metadata.find_all('strong'):
                positions_tags = ['Positions:', 'Position:']
                if strong_tag.text in positions_tags:
                    positions_str = strong_tag.next_sibling.replace('•','').rstrip()
                    pinch_hitters_list = ['skinnbo01'] # MANUAL LIST
                    if 'Pinch Hitter' in positions_str or self.baseball_ref_id in pinch_hitters_list:
                        positions_dict['DH'] = {
                            'g': 0,
                            'tzr': None,
                            'drs': None
                        }

        # CHECK FOR DH
        # DH WILL NOT HAVE A RECORD IN THE FIELDING TABLE
        if not self.pitcher_override:
            games_at_dh = self.__get_dh_appearances(soup_for_homepage_stats, years=[year])
            if games_at_dh:
                positions_dict['DH'] = {
                    'g': games_at_dh,
                    'tzr': None,
                    'drs': None
                }

        return {
            'positions': positions_dict,
            'dWAR': dwar_rating,
        }

    def __appearances_for_position(self, soup_for_homepage_stats:BeautifulSoup, position:str, year:str) -> int:
        """Parse appearances for a given position.

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats on homepage.
          position: Position for Player stats
          year: Year for Player stats

        Returns:
          Int for appearances at position.
        """

        # GO TO THE APPEARANCES TABLE
        appearances_table = soup_for_homepage_stats.find('table', attrs = {'id': 'appearances'})
        is_full_career = year == 'CAREER'

        # PICK THE RIGHT SECTION
        appearances_table_section = appearances_table.find('tfoot') if is_full_career else appearances_table.find('tbody')
        if appearances_table_section is None:
            return None

        # LOOK AT THE FOOTER IF FULL CAREER
        record = None
        if is_full_career:
            footer = appearances_table.find('tfoot')
            record = footer.find('tr')
        else:
            # FIND tr WITH ID: appearances.{year} AND CLASS IS NOT PARTIAL TABLE
            records = appearances_table_section.find_all('tr', attrs = {'id': f'appearances.{year}'})
            for record in records:
                if 'partial_table' not in record.get('class', []):
                    break

        if record is None: return None
        
        # GET THE POSITION COLUMN
        number_of_games_cell = record.find('td', attrs = {'data-stat': f'games_at_{position.lower()}'})
        if number_of_games_cell:
            return int(number_of_games_cell.get_text())
                
        return None

    def __bWar(self, soup_for_homepage_stats:BeautifulSoup, year:int, type:str) -> float:
        """Parse bWAR (baseball reference WAR)

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats on homepage.
          year: Year for Player stats
          type: Pitcher or Hitter

        Returns:
          Float bWAR value
        """
        is_full_career = year == 'CAREER'
        is_pitcher = type == 'Pitcher'
        type_string = 'pitching' if is_pitcher else 'batting'
        war_type_suffix = '_pitch' if is_pitcher else ''
        try:
            if is_full_career:
                summarized_header = self.__get_career_totals_row(div_id=f"div_{type_string}_value",soup_object=soup_for_homepage_stats)
                # TOTAL WAR
                war_object = summarized_header.find('td',attrs={'data-stat':f"WAR{war_type_suffix}"})
                war_rating = float(war_object.get_text()) if war_object != None else 0
            else:
                player_value = soup_for_homepage_stats.find('tr', attrs = {'id': f"{type_string}_value.{year}"})
                # TOTAL WAR
                war_object = player_value.find('td',attrs={'class':'right','data-stat':f"WAR{war_type_suffix}"})
                war_rating = war_object.get_text() if war_object != None else 0
            return float(war_rating)
        except:
            return 0.0

    def __get_dh_appearances(self, soup_for_homepage_stats:BeautifulSoup, years:list[str]) -> int:
        """Parse DH appearances for a given year.
        
        Args:
            soup_for_homepage_stats: BeautifulSoup object with all stats on homepage.
            year: Year for Player stats

        Returns:
            Int for DH appearances.
        """

        # CHECK APPEARANCES TABLE
        appearances_table = soup_for_homepage_stats.find('table', attrs = {'id': 'appearances'})
        total_games_at_dh = 0
        if appearances_table:
            is_full_career = str(years[0]) == 'CAREER'
            if is_full_career:
                footer = appearances_table.find('tfoot')
                footer_row = footer.find('tr') # WILL BE THE FIRST ROW OF FOOTER
                if footer_row:
                    year_rows = [footer_row]
            else:
                # LOOP THROUGH ALL THE TR ROWS UNTIL THE YEAR IS FOUND
                year_rows: list[BeautifulSoup] = []
                for tr in appearances_table.find_all('tr'):
                    year_text = self.__extract_text_for_element(object=tr, tag='th', attr_key='data-stat', values=['year_ID', 'year_id']) or ''
                    if year_text in years:
                        year_rows.append(tr)
            for year_row in year_rows:
                dh_games = self.__extract_text_for_element(object=year_row, tag='td', attr_key='data-stat', values=['G_dh'])
                if dh_games:
                    total_games_at_dh += int(dh_games)
        
        return total_games_at_dh

    def hand(self, soup_for_homepage_stats:BeautifulSoup, type:str) -> str:
        """Parse hand of player.

        Batting Hand for hitter.
        Throwing Hand for pitcher.

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats from homepage.

        Raises:
          ValueError: No metadata found.

        Returns:
          'Right', 'Left', or 'Both' string.
        """

        metadata = soup_for_homepage_stats.find('div', attrs = {'id': 'meta'})

        if metadata is None:
            self.error = 'No player metadata found'
            raise ValueError(self.error)
        # FIND THE HAND TAG IN THE METADATA LIST
        for strong_tag in metadata.find_all('strong'):
            hand_tag = 'Bats: ' if type == 'Hitter' else 'Throws: '
            if strong_tag.text == hand_tag:
                hand = strong_tag.next_sibling.replace('•','').rstrip()
                hand = 'Both' if hand == 'Unknown' else hand
                return hand

    def player_name(self, soup_for_homepage_stats:BeautifulSoup) -> str:
        """Parse player name from baseball reference

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats from homepage.

        Raises:
          ValueError: No player name found.

        Returns:
          'Right', 'Left', or 'Both' string.
        """

        metadata = soup_for_homepage_stats.find('div', attrs = {'id': 'meta'})

        if metadata is None:
            self.error = 'No player name found'
            raise ValueError(self.error)
        # FIND THE ITEMPROP TAG
        name_object = metadata.find('h1', attrs = {'itemprop': 'name'})
        if name_object is None:
            name_string = metadata.find('span').get_text()
        else:
            name_string = name_object.find('span').get_text()

        # FIX POTENTIAL ENCODING ISSUES
        try:
            name_string = name_string.encode('iso-8859-1').decode('utf-8')
        except:
            self.error = 'Could not encode name string.'

        return name_string

    def nationality(self, soup_for_homepage_stats:BeautifulSoup) -> str:
        """Parse player's nationality

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats from homepage.

        Raises:
          ValueError: No player nationality found.

        Returns:
          'Right', 'Left', or 'Both' string.
        """

        # FIND METADATA DIV
        metadata = soup_for_homepage_stats.find('div', attrs = {'id': 'meta'})
        if metadata is None:
            self.error = "No player nationality found"
            raise ValueError(self.error)
        
        # FIND ALL CLASSES WITH THE KEYWORD "f-i" IN THE CLASS NAME.
        #   EX: <span class="f-i f-pr" style="">pr</span>
        # WHEN A PLAYER HAS 2 NATIONALITIES, CHOSE THE BIRTH COUNTRY
        for strong_tag in metadata.find_all('span', { "class": re.compile('.*f-i.*') }):
            country_abbr = strong_tag.text
            if country_abbr:
                return country_abbr.upper()

        # NO NATIONALITY WAS FOUND, RETURN NONE
        return None
    
    def rookie_status_year(self, soup_for_homepage_stats:BeautifulSoup) -> int:
        """Parse the player's rookie status end year. Used for the "R" icon.

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats from homepage.

        Returns:
          Int for the last year of rookie eligibility for the player.
        """

        # FIND METADATA DIV
        metadata = soup_for_homepage_stats.find('div', attrs = {'id': 'meta'})
        if metadata is None:
            return None

        # FIND THE HAND TAG IN THE METADATA LIST
        for strong_tag in metadata.find_all('strong'):
            if strong_tag.text == 'Rookie Status:':
                rookie_status_full_sentence = strong_tag.next_sibling.strip()
                rookie_status_only_ints = re.sub("[^0-9]", "", rookie_status_full_sentence)
                if len(rookie_status_only_ints) != 4:
                    continue
                try:
                    rookie_status_year = int(rookie_status_only_ints)
                    return rookie_status_year
                except:
                    continue

        # NO ROOKIE STATUS WAS FOUND, RETURN NONE
        return None

    def is_hof(self, soup_for_homepage_stats:BeautifulSoup) -> bool:
        """Parse the player's metadata and check if they are in the HOF

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats from homepage.

        Returns:
          Boolean for whether the are in the Hall of Fame or not.
        """

        # FIND METADATA DIV
        metadata = soup_for_homepage_stats.find('div', attrs = {'id': 'meta'})
        if metadata is None:
            return None

        # FIND THE HAND TAG IN THE METADATA LIST
        for strong_tag in metadata.find_all('strong'):
            if strong_tag.text == 'Hall of Fame:':
                return True

        # NO ROOKIE STATUS WAS FOUND, RETURN NONE
        return False
    
    def __accolades_dict(self, soup_for_homepage_stats:BeautifulSoup, years_included:list[str]) -> dict:
        """Parse the "Leaderboards, Awards, Honors" section of bref.

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats from homepage.
          years_included: List of years to filter for stats

        Returns:
          Boolean for whether the are in the Hall of Fame or not.
        """
        leaderboard_table_divs_list = soup_for_homepage_stats.find_all('div', attrs={'id': re.compile(f'leaderboard_')})

        # RETURN EMPTY DICT IF NO LEADERBOARDS
        if leaderboard_table_divs_list is None:
            return {}

        awards_and_accolades_dict = {}
        for leaderboard_div in leaderboard_table_divs_list:
            td_list_accolades = leaderboard_div.find_all('td')
            category = leaderboard_div['id'].replace('leaderboard_','')
            categories_included_list = [accolade.value for accolade in Accolade]
            if td_list_accolades is None or category not in categories_included_list:
                continue
            accolades_list_for_category = []
            for td_row in td_list_accolades:
                accolade_text = td_row.get_text().replace(u'\xa0', u' ').replace('  ', ' ').replace(u'\n','').replace(' *','').upper().strip()
                is_year_match = len([year for year in years_included if str(year).upper() in accolade_text or str(year) == 'CAREER']) > 0
                if is_year_match:
                    accolades_list_for_category.append(accolade_text)
            
            if len(accolades_list_for_category) > 0:
                awards_and_accolades_dict[category] = accolades_list_for_category

        return awards_and_accolades_dict

    def type(self, positions_dict:dict[str,dict], year:int) -> str:
        """Guess Player Type (Pitcher or Hitter) based on games played at each position.

        Args:
          positional_fielding: Dict with positions, games_played, and tzr
          year: Year for Player stats

        Raises:
          AttributeError: This Player Played 0 Games. Check Player Name and Year.

        Returns:
          Either 'Hitter' or 'Pitcher' string.
        """
        games_as_pitcher = sum([pos_data.get('g', 0) for pos, pos_data in positions_dict.items() if pos == 'P'])
        games_as_hitter = sum([pos_data.get('g', 0) for pos, pos_data in positions_dict.items() if pos != 'P'])

        # CHECK FOR TYPE OVERRIDE
        is_pitcher_override = self.pitcher_override and games_as_pitcher > 0
        is_hitter_override = self.hitter_override

        # COMPARE GAMES PLAYED IN BOTH TYPES
        total_games = games_as_hitter + games_as_pitcher
        if total_games == 0:
            if self.is_multi_year:
                return None
            elif 'DH' in positions_dict.keys():
                return "Hitter"
            else:
                if not (self.is_multi_year or self.is_full_career):
                    self.error = f'This Player Played 0 Games in {year}. Check Player Name and Year'
                    raise AttributeError(self.error)
        elif is_pitcher_override:
            return "Pitcher"
        elif is_hitter_override:
            return "Hitter"
        elif games_as_pitcher < games_as_hitter:
            return "Hitter"
        else:
            return "Pitcher"

    def __all_leagues_played(self, soup_for_homepage_stats:BeautifulSoup) -> list[str]:
        """Parse all leagues played by a player.

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats from homepage.

        Returns:
          List of leagues played by player.
        """

        league_cells: list[BeautifulSoup] = soup_for_homepage_stats.find_all('td', attrs = {'data-stat': re.compile('lg_ID|comp_name_abbr')})
        if len(league_cells) == 0:
            return []

        leagues_played = []
        for cell in league_cells:
            league_abbr = cell.get_text()
            if league_abbr not in leagues_played:
                leagues_played.append(league_abbr)

        return leagues_played

    def statcast_sprint_speed(self, name:str, year:int) -> float:
        """Sprint Speed for player from Baseball Savant (Only applicable to 2015+).

        Args:
          name: Full name of Player
          year: Year for Player stats

        Raises:
          AttributeError: This Player Played 0 Games. Check Player Name and Year.

        Returns:
          Average sprint speed for Player as Float.
        """

        # DATA ONLY AVAILABLE 2015+
        if int(year) < 2015:
            return None

        sprint_speed_url = 'https://baseballsavant.mlb.com/sprint_speed_leaderboard?year={}&position=&team=&min=0'.format(year)
        speed_data_html = self.html_for_url(sprint_speed_url)

        speed_data_extracted = re.search('var data = (.*);',speed_data_html).group(1)
        speed_list_all_players = json.loads(speed_data_extracted)

        for player_dict in speed_list_all_players:
            # FIND PLAYER IN LIST
            is_player_match = self.__is_statcast_name_match(bref_name=name, statcast_name=player_dict['name_display_last_first'])
            if is_player_match:
                speed = float(player_dict['r_sprint_speed_top50percent_pretty'])
                return speed
        # IF NOT FOUND, RETURN LEAGUE AVG
        default_speed = 26.25
        return default_speed

    def statcast_outs_above_average_dict(self, name:str, years:list[int]) -> dict[str, float]:
        """Outs above average metric for players from Baseball Savant (Only applicable to 2016+).

        Args:
          name: Full name of Player
          year: List of years to include.

        Returns:
          Dictionary with position and outs above avg value
        """
        # DEFINE YEAR RANGE
        min_year = min(years)
        max_year = max(years)

        year_start_for_query = max(min_year, 2016)
        year_end_for_query = max_year
        # DATA ONLY AVAILABLE 2016+
        if max_year < 2016:
            return {}

        url = f'https://baseballsavant.mlb.com/leaderboard/outs_above_average?type=Fielder&startYear={year_start_for_query}&endYear={year_end_for_query}&position=&team=&min=0'
        oaa_html = self.html_for_url(url)

        data_extracted = re.search('var data = (.*);',oaa_html).group(1)
        oaa_list_all_players = json.loads(data_extracted)

        for player_dict in oaa_list_all_players:
            # FIND PLAYER IN LIST
            
            is_player_match = self.__is_statcast_name_match(bref_name=name, statcast_name=player_dict['entity_name'])
            if is_player_match:
                # MAKE REQUEST FOR DETAILED PAGE WITH EXACT NUMBERS
                statcast_player_id = player_dict['entity_id']
                player_detail_url = f'https://baseballsavant.mlb.com/savant-player/{statcast_player_id}?stats=statcast-r-fielding-mlb'
                player_detail_html = self.html_for_url(url=player_detail_url)
                fielding_data_extracted = re.search('infieldDefense: (.*),',player_detail_html)
                if fielding_data_extracted:
                    fielding_data_grouped = fielding_data_extracted.group(1)
                    fielding_data_jsons = json.loads(fielding_data_grouped)
                    fielding_data = {}
                    for fielding_row in fielding_data_jsons:
                        team_abbr = fielding_row['fld_abbreviation']
                        is_year_match = int(fielding_row['year']) in years
                        is_team_row = self.team_override == team_abbr if self.team_override else team_abbr != 'NA'
                        if is_year_match and is_team_row:
                            position = fielding_row['pos_name_short']
                            ooa = fielding_row['outs_above_average']
                            if ooa:                              
                                ooa_rounded = round(ooa, 3)
                                if position in fielding_data.keys():
                                    # POSITION IS ALREADY IN JSON, ADD TO IT
                                    fielding_data[position] += ooa_rounded
                                else:
                                    fielding_data[position] = ooa_rounded
                                # IF OF POSITION, ADD TO TOTAL OF DEFENSE
                                if position in ['LF','CF','RF']:
                                    if 'OF' in fielding_data.keys():
                                        # POSITION IS ALREADY IN JSON, ADD TO IT
                                        fielding_data['OF'] += ooa_rounded
                                    else:
                                        fielding_data['OF'] = ooa_rounded
                    return fielding_data
                
        # IF NOT FOUND, RETURN NONE
        return {}

    def __is_statcast_name_match(self, bref_name:str, statcast_name:str) -> bool:
        """Compare first name and last name from bref vs statcast to match to a player.
        Returns true if both the first name and last name are a match.

        Args:
          bref_name: Full name of Player from baseball reference.
          statcast_name: String from a statcast leaderboard.

        Returns:
          True or False for whether the name matches.
        """

        # REMOVE SPECIAL CHARACTERS FROM THE NAME
        bref_name = unidecode.unidecode(bref_name.replace(".", ""))
        bref_name_split_list = bref_name.split(' ')
        first_name_cleaned = bref_name_split_list[0]
        last_name = bref_name_split_list[1]

        # PARSE BASEBALL SAVANT NAME
        savant_name_raw = unidecode.unidecode(statcast_name)
        savant_name_split_list = savant_name_raw.split(', ', 1)

        # REPLACE DECIMAL POINTS WITH EMPTY STRING
        try:
            full_name_baseball_savant = f"{savant_name_split_list[1]} {savant_name_split_list[0]}".replace(".","")
        except:
            return False
        
        is_first_and_last_matches = first_name_cleaned in full_name_baseball_savant and last_name in full_name_baseball_savant
        is_exact_name_match = bref_name.lower() == full_name_baseball_savant.lower()
        is_match = is_first_and_last_matches or is_exact_name_match
        
        return is_match

    def parse_advanced_stats(self, soup_for_advanced_stats:BeautifulSoup, type:str, year:str, ignore_ip_per_gs:bool=False) -> dict:
        """Parse advanced stats page from baseball reference.

        Standard and ratio stats. For Pitchers, uses batting against table.

        Args:
          soup_for_advanced_stats: BeautifulSoup object with all stats from advanced stats page.
          type: Player is Pitcher or Hitter.
          year: Year for Player stats
          ignore_ip_per_gs: Ignore IP/GS for pitchers. Flagged if reduced stats are available (ex: Negro Leagues, < 1914)

        Returns:
          Dict with standard and ratio statistics.
        """

        is_full_career = year == 'CAREER'
        table_prefix = 'batting' if type == 'Hitter' else 'pitching'
        if is_full_career:
            standard_row = self.__get_career_totals_row(div_id=re.compile(f'all_{table_prefix}_standard|all_players_standard_{table_prefix}'),soup_object=soup_for_advanced_stats)
        else:
            standard_row = None
            standard_rows = soup_for_advanced_stats.find_all('tr',attrs={'id': f'players_standard_{table_prefix}.{year}'}) \
                                or soup_for_advanced_stats.find_all('tr',attrs={'class':'full','id': f'{table_prefix}_standard.{year}'})
            for row in standard_rows:
                class_names = row.get('class', [])
                if 'partial_table' not in class_names:
                    standard_row = row
                    break

        advanced_stats = {}

        # BATTING AGAINST (PITCHERS ONLY)
        if type == 'Pitcher':
            if is_full_career:
                try:
                    batting_against_table = self.__get_career_totals_row(div_id='div_pitching_batting',soup_object=soup_for_advanced_stats)
                    advanced_stats.update(self.__parse_generic_bref_row(batting_against_table))
                except:
                    advanced_stats.update(self.__parse_incomplete_splits_stats(year=year))
            else:
                # LOOK AT "SPLITS" PAGE FOR PRE-1916 PITCHERS
                if self.__is_pitcher_from_1901_to_1918(year=year,type=type):
                    advanced_stats.update(self.__parse_incomplete_splits_stats(year=year))
                else:
                    batting_against_soup = soup_for_advanced_stats.find('table', attrs={'id': 'pitching_batting'})
                    partial_stats = self.__find_partial_team_stats_row(soup_object=batting_against_soup, team=self.team_override, year=year)
                    if self.team_override and partial_stats:
                        advanced_stats.update(partial_stats)
                    else:
                        batting_against_row = soup_for_advanced_stats.find('tr',attrs={'class':'full','id': f'pitching_batting.{year}'})
                        advanced_stats.update(self.__parse_generic_bref_row(batting_against_row))
        
        # STANDARD STATS
        standard_table_soup = soup_for_advanced_stats.find('div', attrs={'class': 'table_container', 'id': f'div_{table_prefix}_standard'}) \
                                or soup_for_advanced_stats.find('div', attrs={'class': 'table_container', 'id': f'div_players_standard_{table_prefix}'})
        partial_stats_soup = self.__find_partial_team_stats_row(soup_object=standard_table_soup, team=self.team_override, year=year, return_soup_object=True)
        
        # DEFINE COLUMNS THAT WILL BE INCLUDED FROM STANDARD PAGE
        # HITTERS INCLUDE ALL COLUMNS
        standard_columns_filter = [] if type == 'Hitter' else ['earned_run_avg','team_ID','G','GS','W','SV','IP','ER','H','2B','3B','HR','BB','SO','HBP','whip','batters_faced','award_summary']
        if type == 'Pitcher' and is_full_career:
            standard_columns_filter.append('G')
        
        # PARSE RECORD(S)
        row_source = partial_stats_soup if (self.team_override and partial_stats_soup) else standard_row
        standard_stats_dict = self.__parse_generic_bref_row(row=row_source, included_categories=standard_columns_filter, search_for_lg_leader=True)
        advanced_stats.update(standard_stats_dict)

        # CHECK IF DATA SHOULD BE OVERRIDDEN BY SPLITS
        splits_data = self.parse_splits_data(type=type, year=year)
        if splits_data:
            advanced_stats.update(splits_data)

        # PARSE AWARDS IF FULL CAREER
        if is_full_career or self.team_override:
            year_filter = '' if is_full_career else str(year)
            all_year_standard_stats = soup_for_advanced_stats.find_all('tr',attrs={'id': re.compile(f"{table_prefix}_standard\.{year_filter}|players_standard_{table_prefix}\.{year_filter}")})
            awards_total = ""
            for year_stats in all_year_standard_stats:
                stats_dict = self.__parse_generic_bref_row(row=year_stats, included_categories=standard_columns_filter, search_for_lg_leader=True)
                if 'is_sv_leader' in stats_dict:
                    advanced_stats['is_sv_leader'] = stats_dict['is_sv_leader']
                year_award_summary = stats_dict.get('award_summary', None) or stats_dict.get('awards', '')
                if len(year_award_summary) > 0:
                    awards_total = f'{awards_total},{year_award_summary}'
            advanced_stats['award_summary'] = awards_total

        # IF A PLAYER PLAYED FOR MULTIPLE TEAMS IN ONE SEASON, SELECT THE LAST TEAM THEY PLAYED FOR.
        team_id_key, league_id_key = 'team_ID', 'lg_ID'
        current_team_id = advanced_stats.get(team_id_key, None)
        if current_team_id:
            if self.__is_team_id_multiple(current_team_id):
                updated_team_id, updated_league_id = self.__parse_team_after_trade(soup_for_homepage_stats=soup_for_advanced_stats,year=year,type=type)
                advanced_stats[team_id_key] = updated_team_id
                advanced_stats[league_id_key] = updated_league_id

        # FILL IN EMPTY STATS
        advanced_stats = self.__fill_empty_required_stat_categories(advanced_stats)

        # RATIO STATS
        ratio_table_key = f'div_{table_prefix}_ratio'
        if is_full_career:
            ratio_row = self.__get_career_totals_row(div_id=ratio_table_key,soup_object=soup_for_advanced_stats)
        else:
            ratio_table = soup_for_advanced_stats.find('div', attrs = {'id': ratio_table_key})
            partial_stats_soup = self.__find_partial_team_stats_row(soup_object=ratio_table, team=self.team_override, year=year, return_soup_object=True)
            if self.team_override and partial_stats_soup:
                ratio_row = partial_stats_soup
            else:
                ratio_row_key = f'{table_prefix}_ratio.{year}'
                ratio_row = soup_for_advanced_stats.find('tr', attrs = {'class': 'full', 'id': ratio_row_key})
        advanced_stats.update(self.__parse_ratio_stats(ratio_row=ratio_row))

        # IP/GS (STARTING PITCHER)
        if type == 'Pitcher' and not ignore_ip_per_gs:
            ip_per_gs = 0.0
            starter_stats_soup = soup_for_advanced_stats.find('div', attrs={'id': 'div_pitching_starter'})
            if starter_stats_soup:
                partial_stats_soup = self.__find_partial_team_stats_row(soup_object=starter_stats_soup, team=self.team_override, year=year, return_soup_object=True)
                row_accounting_for_team_override = partial_stats_soup if self.team_override and partial_stats_soup else starter_stats_soup.find('tr', attrs={'id': f'pitching_starter.{year}'})
                if row_accounting_for_team_override:
                    ip_per_start_text = self.__extract_text_for_element(object=row_accounting_for_team_override, tag='td', attr_key='data-stat', values=['innings_per_start'])
                    if ip_per_start_text:
                        ip_per_gs = self.__convert_to_numeric(ip_per_start_text)
            advanced_stats['IP/GS'] = ip_per_gs
        
        return advanced_stats
    
    def __fill_empty_required_stat_categories(self, stats_data:dict) -> dict:
        """Ensure all required fields are populated for player stats.
        
        Args:
          data: Current dict for stats.

        Returns:
          Update stats dict
        """

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
        
        keys_to_fill = ['SH','HBP','IBB','SF','SO']
        for key in keys_to_fill:
            if key not in current_categories:
                stats_data[key] = 0

        if '2B' not in current_categories:
            maxDoubles = 0.25
            eraPercentile = self.__percentile(minValue=1.0, maxValue=5.0, value=stats_data['earned_run_avg'])
            stats_data['2B'] = int(stats_data['H'] * eraPercentile * maxDoubles)

        if '3B' not in current_categories:
            maxTriples = 0.025
            eraPercentile = self.__percentile(minValue=1.0, maxValue=5.0, value=stats_data['earned_run_avg'])
            stats_data['3B'] = int(stats_data['H'] * eraPercentile * maxTriples)
        
        if 'slugging_perc' not in current_categories:
            ab = stats_data.get('AB') if stats_data.get('AB', None) else stats_data['PA'] - stats_data['BB'] - stats_data['HBP']
            singles = stats_data['H'] - stats_data['2B'] - stats_data['3B'] - stats_data['HR']
            total_bases = (singles + (2 * stats_data['2B']) + (3 * stats_data['3B']) + (4 * stats_data['HR']))
            stats_data['AB'] = ab
            stats_data['TB'] = total_bases
            stats_data['slugging_perc'] = round(total_bases / ab, 5) if ab > 0 else 0.0

        if 'onbase_perc' not in current_categories:
            sf = 0 if len(str(stats_data.get('SF', ''))) == 0 else stats_data.get('SF', 0)
            obp_denominator = ( stats_data.get('AB', 0) + stats_data.get('BB', 0) + stats_data.get('HBP', 0) + sf ) if 'AB' in stats_data.keys() else stats_data['PA']
            stats_data['onbase_perc'] = round((stats_data['H'] + stats_data['BB'] + stats_data.get('HBP', 0)) / obp_denominator, 5)
        
        if 'batting_avg' not in current_categories:
            stats_data['batting_avg'] = round(stats_data['H'] / stats_data['AB'], 5) if stats_data.get('AB', 0) > 0 else 0.0
        
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

    def __parse_incomplete_splits_stats(self,year:int) -> dict:
        """Parse standard statline from the "splits" page on Baseball Reference for players with incomplete data.

        Args:
          year: Year for data stats (ex: 2021, CAREER)

        Returns:
          Dict with statistics.
        """

        url_splits = f'https://www.baseball-reference.com/players/split.fcgi?id={self.baseball_ref_id}&year={year}&t=p'
        soup_for_split = self.__soup_for_url(url_splits, is_baseball_ref_page=True)
        tables_w_incomplete_split = [a for a in soup_for_split.select('th[data-stat="incomplete_split"]')]
        stats = tables_w_incomplete_split[1]
        header_values = [self.__convert_to_numeric(sib['data-stat']) for sib in stats.next_siblings]
        stats_values = [self.__convert_to_numeric(sib.string) for sib in stats.next_siblings]
        batting_against_dict = dict(zip(header_values, stats_values))
        return batting_against_dict

    def parse_splits_data(self, type:str, year:int) -> dict:
        """Find and parse the row with matching split name.
        Return None if split does not exist.

        Args:
          type: Player is Pitcher or Hitter.
          year: Year for data stats (ex: 2021, CAREER)
          split_name: Name of the split.

        Returns:
          Dict with split statistics.
        """

        # RETURN NONE IF NO SPLIT
        if self.stats_period.type != StatsPeriodType.SPLIT or self.stats_period.split is None:
            return None
        
        type_ext = 'p' if type == 'Pitcher' else 'b'
        url_splits = f'https://www.baseball-reference.com/players/split.fcgi?id={self.baseball_ref_id}&year={year}&t={type_ext}'
        soup_for_split = self.__soup_for_url(url_splits, is_baseball_ref_page=True)

        for tag in ['th', 'td']:
            splits = soup_for_split.find_all(tag, string=re.compile(self.stats_period.split, flags=re.IGNORECASE))

            # FILTER TO BEST MATCH SPLIT
            if len(splits) > 1:
                best_string_match_ratio = max([SequenceMatcher(None, split.get_text(), self.stats_period.split).ratio() for split in splits])
                updated_splits = []
                for split in splits:
                    ratio = SequenceMatcher(None, split.get_text(), self.stats_period.split).ratio()
                    if round(ratio, 4) == round(best_string_match_ratio, 4):
                        updated_splits.append(split)
                splits = updated_splits
                
            # MATCH FOUND, BREAK LOOP
            if len(splits) > 0:
                break
        
        if len(splits) == 0:
            self.warnings.append(f'No Splits Available for {self.stats_period.split}')
            self.stats_period.reset()
            return None

        # ITERATE THROUGH ALL SPLIT ROWS THAT MATCH THE USER INPUTTED NAME
        # LOOP MAKES SURE ALL STATS ARE CAPTURED, ESPECIALLY IMPORTANT FOR PITCHERS 
        #   WHO WILL HAVE GAME LEVEL AND BATTING AGAINST RECORDS
        stats_dict: dict = {}
        for header_column in splits:
            header_values = [self.__convert_to_numeric(sib['data-stat']) for sib in header_column.next_siblings]
            stats_values = [self.__convert_to_numeric(sib.string) for sib in header_column.next_siblings]
            stats_dict.update(dict(zip(header_values, stats_values)))
        
        stats_dict = self.__fill_empty_required_stat_categories(stats_dict)

        return stats_dict

    def game_log_data(self, type:str, years:list[str]) -> dict:
        """Parse Game Log Data. Used in certain stat period types (Postseason, Date Range).

        Args:
          type: Player Type
          years: List of years as strings.

        Returns:
          Aggregated stats dict from game logs.
        """
        
        is_pitcher = type == 'Pitcher'
        type_ext = 'p' if is_pitcher else 'b'
        years = [int(y) if y != 'CAREER' else y for y in years]
        first_year = years[0]
        period_ext = "year=0&post=1" if self.stats_period.type == StatsPeriodType.POSTSEASON else f"year={first_year}"
        url = f"https://www.baseball-reference.com/players/gl.fcgi?id={self.baseball_ref_id}&t={type_ext}&{period_ext}"
        soup_game_log_page = self.__soup_for_url(url, is_baseball_ref_page=True)

        # CHECK FOR ROWS
        # NOTE: THIS HANDLES BOTH THE OLD AND "UPGRADED" TABLES
        # OLD: ID OF TABLE WAS 'batting_gamelogs' OR 'pitching_gamelogs'
        # UPGRADED: LOOK FOR A TABLE WITH id="players_standard_batting"/"players_standard_pitching" and data-soc-sum-scope-type="player_game"
        type_prefix = 'pitching' if is_pitcher else 'batting'
        game_log_records = soup_game_log_page.find_all('tr', attrs={'id': re.compile(f'{type_prefix}_gamelogs.')})
        is_no_records_old_table = len(game_log_records) == 0
        if is_no_records_old_table:
            # CHECK FOR NEW UPGRADED TABLE
            game_log_table = soup_game_log_page.find('table', attrs={'id': f'players_standard_{type_prefix}'})
            if game_log_table:
                game_log_records = game_log_table.find_all('tr', attrs={'id': re.compile(f'players_standard_{type_prefix}.')})
                # FILTER OUT RECORDS WITH "spacer" IN CLASS
                game_log_records = [row for row in game_log_records if 'spacer' not in row.get('class', 'N/A')]

        included_categories = ['year_game','ps_round','date_game','team_ID','player_game_span','IP','H','R','ER','BB','SO','HR','HBP','batters_faced','PA','SB','CS','AB','2B','3B','IBB','GIDP','SF','RBI','player_game_result',
                               'date','team_name_abbr',]
        game_logs_parsed: list[dict] = [self.__parse_generic_bref_row(row=game_log, included_categories=included_categories) for game_log in game_log_records]
        
        # AGGREGATE DATA
        aggregated_data_into_lists: dict[str, list] = {}
        for game_log_data in game_logs_parsed:

            # REMOVE BAD UNICODE CHARACTERS
            date_game = game_log_data.get('date_game', game_log_data.get('date', None))
            if date_game:
                game_log_data['date_game'] = date_game.replace(u'\xa0', u' ')
                
            # CHECK FOR DATE/YEAR FILTER
            year_from_game_log = self.__convert_to_numeric(str(game_log_data.get('year_game', first_year)))
            year_check = year_from_game_log in years or first_year == 'CAREER'
            date_check = True
            game_log_date_str: str = game_log_data.get('date_game', None)
            if self.stats_period.is_date_range and game_log_date_str:
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
                date_check = self.stats_period.start_date <= game_log_date <= self.stats_period.end_date

                # UPDATE 'date_game' WITH FORMATTED DATE
                game_log_data['date_game'] = game_log_date.strftime("%b %-d")
            
            # SKIP IF TEAM OVERRIDE IS PRESENT AND TEAM DOESN'T MATCH
            if self.team_override:
                team_id = game_log_data.get('team_ID', '')
                if team_id != self.team_override:
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

            for category, stat in game_log_data.items():
                # IF THE KEY IS NOT IN THE AGGREGATED_DATA DICTIONARY, ADD IT
                if category not in aggregated_data_into_lists:
                    aggregated_data_into_lists[category] = [stat]
                else:
                    # IF THE KEY IS ALREADY PRESENT, APPEND THE VALUE TO THE LIST
                    aggregated_data_into_lists[category].append(stat)
                    
        stats_agg_type = {
            'team_ID': 'last',
        }
        aggregated_data = { k.replace('batters_faced', 'PA'): self.__aggregate_stats_list(category=k, stats=v, str_agg_type=stats_agg_type.get(k, 'mode')) for k,v in aggregated_data_into_lists.items() if k != 'earned_run_avg'}

        # CHECK FOR NO-DATA
        if len(aggregated_data) == 0:
            self.warnings.append(self.stats_period.empty_message)
            self.stats_period.reset()
            return None

        aggregated_data = self.__fill_empty_required_stat_categories(aggregated_data)

        # ADD FIRST AND LAST GAME DATES
        game_dates = aggregated_data_into_lists.get('date_game', None)
        if game_dates:
            first_game_date_str: str = str(game_dates[0]).upper().split(' (', 1)[0]
            last_game_date_str: str = str(game_dates[-1]).upper().split(' (', 1)[0]
            aggregated_data['first_game_date'] = first_game_date_str
            aggregated_data['last_game_date'] = last_game_date_str

            # UPDATE STATS PERIOD OBJECT WITH EXACT GAME DATES
            if not self.disable_stats_period_range_updates:
                try:
                    self.stats_period.start_date = datetime.strptime(f'{first_game_date_str} {self.year_input}', "%b %d %Y").date()
                    self.stats_period.end_date = datetime.strptime(f'{last_game_date_str} {self.year_input}', "%b %d %Y").date()
                except:
                    pass
        
        return aggregated_data

    def __parse_generic_bref_row(self, row:BeautifulSoup, included_categories:list[str] = [], search_for_lg_leader:bool = False) -> dict:
        """Parse hitting stats a pitcher allowed.

        Args:
          row: BeautifulSoup tr row object with stats
          included_categories: List of categories to include. If empty include all.
          search_for_lg_leader: Boolean for whether to look for league leader bold/italic text.

        Returns:
          Dict with statistics
        """

        if row is None:
            return {}

        columns = row.find_all()

        final_stats_dict = {}        
        for category_object in columns:

            stat_category:str = category_object.get('data-stat', None)
            if stat_category is None: continue
            stat_category = self.__conform_stat_category_to_old_structure(stat_category)

            if stat_category not in included_categories and len(included_categories) > 0:
                continue

            if search_for_lg_leader:
                is_league_leader = '<strong>' in str(category_object) or '<em>' in str(category_object) # LEAGUE LEADERS ON BASEBALL REF ARE DENOTED BY BOLD OR ITALIC TEXT

                if stat_category in ('SV','HR','SB','SO'):
                    # SAVE THIS INFO FOR RP, HR, OR SB ICONS
                    final_stats_dict[f'is_{stat_category.lower()}_leader'] = is_league_leader

            stat = category_object.get_text()
            fill_blanks_w_zeros = ['GS','W','SV','H','2B','3B','HR','BB','SO','HBP','SF','IBB','CS','batters_faced']
            if stat_category in fill_blanks_w_zeros and len(stat) == 0:
                stat = '0'
            stat = self.__convert_to_numeric(stat)
            final_stats_dict[stat_category]= stat

        return final_stats_dict

    def __parse_ratio_stats(self, ratio_row:BeautifulSoup) -> dict[str,float]:
        """Parse out ratios (GB/AO, PU)

        Args:
          ratio_row: BeautifulSoup table row for ratios.

        Returns:
          Dict with ratio statistics.
        """

        gb_ao_ratio = None
        pu_ratio = None
        if ratio_row is not None:
            # GB/AO
            gb_ao_ratio_raw = ratio_row.find('td',attrs={'class':'right','data-stat': 'go_ao_ratio'}).get_text()
            try:
                gb_ao_ratio = float(gb_ao_ratio_raw)
            except:
                gb_ao_ratio = None
            # PU/FB
            pu_ratio_raw = ratio_row.find('td',attrs={'class':'right','data-stat': 'infield_fb_perc'})
            if pu_ratio_raw:
                # PU RATIO DATA AVAILABLE AFTER 1988
                pu_ratio_text = pu_ratio_raw.get_text()
                pu_ratio = None if pu_ratio_text == '' else round(int(pu_ratio_text.replace('%','')) / 100.0, 3)

        return {
            'GO/AO': gb_ao_ratio,
            'IF/FB': pu_ratio
        }

    def __parse_team_after_trade(self, soup_for_homepage_stats:BeautifulSoup, year:int, type:str) -> tuple[str, str]:
        """Parse the last team a player playe dfor in the given season.

        Args:
          soup_for_homepage_stats: BeautifulSoup object for advanced stats table.
          year: Year for Player stats
          type: Player is Pitcher or Hitter.

        Returns:
          Team Id for last team the player played on in year
          League Id for last team the player played on in year
        """

        default_return = 'TOT', 'TOT'
        header_prefix = 'batting' if type == 'Hitter' else 'pitching'
        standard_table = soup_for_homepage_stats.find('table', id=lambda x: x in [f'{header_prefix}_standard', f'players_standard_{header_prefix}'])
        if standard_table is None:
            return default_return
        partial_objects_list = standard_table.find_all('tr',attrs={'class':'partial_table'})
        
        # ITERATE THROUGH PARTIAL SEASONS
        teams_list = []
        team_league_dict: dict[str: str] = {}
        try:
            for partial_object in partial_objects_list:
                
                # CHECK IF YEAR FOR ROW MATCHES YEAR FROM PARAMETER
                year_text = self.__extract_text_for_element(object=partial_object, tag='th', attr_key='data-stat', values=['year_ID', 'year_id'])
                if year_text is None:
                    continue
                does_partial_object_match_year = year_text == str(year)

                # SKIP ROW IF NOT YEAR MATCH
                if not does_partial_object_match_year: 
                    continue

                # PARSE TEAM ID
                team_id = self.__extract_text_for_element(object=partial_object, tag='td', attr_key='data-stat', values=['team_ID', 'team_name_abbr'])
                if team_id is None:
                    continue
                if team_id != '' and not self.__is_team_id_multiple(team_id):
                    # ADD TO TEAMS LIST
                    teams_list.append(team_id)
                    league_id = self.__extract_text_for_element(object=partial_object, tag='td', attr_key='data-stat', values=['lg_ID', 'comp_name_abbr'])
                    if league_id is not None:
                        team_league_dict[team_id] = league_id
                        
            last_team = teams_list[-1]
            last_team_league = team_league_dict.get(last_team, 'TOT')
            return last_team, last_team_league
        except:
            return default_return

    def __add_icon_threshold_bools(self, type:str, year:int, stats_dict:dict, homepage_soup:BeautifulSoup) -> dict[str,bool]:
        """Add 4 boolean flags for whether the player qualifies for Icons for a given stat

        Args:
          type: Player is Pitcher or Hitter.
          year: String representation for year of stats
          stats_dict: Real life stats in a dict (ex: H, BB, HR, etc)
          homepage_soup: Beautiful Soup object for the player's homepage on bRef

        Returns:
          Dictionary for threshold booleans
        """

        # ICON STATS
        icon_threshold_bools = {
            'is_above_hr_threshold': False,
            'is_above_so_threshold': False,
            'is_above_sb_threshold': False,
            'is_above_w_threshold': False,
        }
        stat_icon_mapping = {
            'HR': 17 if year == '2020' else 40,
            'SO': 96 if year == '2020' else 215,
            'SB': 15 if year == '2020' else 40,
            'W': 20,
        }
        for stat, threshold in stat_icon_mapping.items():
            bool_key_name = f"is_above_{stat.lower()}_threshold"
            
            if year == 'CAREER':
                stat_to_search = 'p_w' if stat in ['W'] else stat
                list_of_values_for_stat = self.__get_stat_list_from_standard_table(type, homepage_soup, stat_key=stat_to_search)
                if list_of_values_for_stat:
                    list_cleaned = [0 if str(x) == '' else x for x in list_of_values_for_stat]
                    max_for_stat = max(list_cleaned)
                    is_qualified_for_icon = int(max_for_stat) >= threshold
                    icon_threshold_bools[bool_key_name] = is_qualified_for_icon
            else:
                if stat in stats_dict.keys():
                    if len(str(stats_dict[stat])) == 0:
                        icon_threshold_bools[bool_key_name] = False
                    else:
                        is_qualified_for_icon = int(stats_dict[stat]) >= threshold
                        icon_threshold_bools[bool_key_name] = is_qualified_for_icon
        
        return icon_threshold_bools

    def __combine_multi_year_dict(self, yearly_stats_dict:dict[int: dict], years: list[int]) -> dict:
        """Combine multiple years into one master final dataset

        Args:
          yearly_stats_dict: Dict of dicts per year.

        Returns:
          Flattened dictionary with combined stats
        """

        # ENSURE ALL YEARS HAVE THE SAME TYPE
        types = [stats.get('type', None) for stats in yearly_stats_dict.values() if stats.get('type', None)]
        # GET MOST COMMON ELEMENT IN LIST
        most_common_type = max(set(types), key=types.count)
        yearly_stats_dict = { year: stats for year, stats in yearly_stats_dict.items() if stats.get('type', 'n/a') == most_common_type }

        # FLATTEN MULTI YEAR STATS
        yearPd = pd.DataFrame.from_dict(yearly_stats_dict, orient='index')
        wa_games = lambda x: round(np.average(x, weights=yearPd.loc[x.index, "G"]))
        column_aggs = {
            '1B': 'sum',
            '2B': 'sum',
            '3B': 'sum',
            'AB': 'sum',
            'BB': 'sum',
            'CS': 'sum',
            'G': 'sum',
            'GIDP': 'sum',
            'H': 'sum',
            'HBP': 'sum',
            'HR': 'sum',
            'IBB': 'sum',
            'PA': 'sum',
            'R': 'sum',
            'RBI': 'sum',
            'SB': 'sum',
            'SF': 'sum',
            'SH': 'sum',
            'SO': 'sum',
            'TB': 'sum',
            'IP': 'sum',
            'SV': 'sum',
            'GS': 'sum',
            'W': 'sum',
            'ER': 'sum',
            'GO/AO': 'mean',
            'IF/FB': 'mean',
            'sprint_speed': 'mean',
            'is_above_hr_threshold': 'max',
            'is_above_so_threshold': 'max',
            'is_above_sb_threshold': 'max',
            'is_above_w_threshold': 'max',
            'is_sv_leader': 'max',
            'is_hr_leader': 'max',
            'is_sb_leader': 'max',
            'award_summary': ','.join,
            'bWAR': 'sum',
            'onbase_plus_slugging_plus': wa_games,
        }
        columns_to_remove = list(set(column_aggs.keys()) - set(yearPd.columns))
        if max(years) < 2015:
            columns_to_remove.append('sprint_speed')
        [column_aggs.pop(key) for key in columns_to_remove if key in column_aggs.keys()]
        avg_year = yearPd.groupby(by='name',as_index=False).agg(column_aggs)
        avg_year_dict = avg_year.iloc[0].to_dict()

        # CALCULATE RATES
        hits = float(avg_year_dict['H'])
        ab = float(avg_year_dict['AB'])
        bb = float(avg_year_dict['BB'])
        hbp = float(avg_year_dict['HBP'])
        sf = float(avg_year_dict['SF'])
        tb = float(avg_year_dict['TB'])
        if_fb = avg_year_dict['IF/FB']
        go_ao = avg_year_dict['GO/AO']
                   
        avg_year_dict["batting_avg"] = round(hits / ab, 3)
        avg_year_dict["onbase_perc"] = round((hits + bb + hbp) / (ab + bb + hbp + sf), 3)
        avg_year_dict["slugging_perc"] = round(tb / ab, 3)
        avg_year_dict["onbase_plus_slugging"] = round(avg_year_dict["onbase_perc"] + avg_year_dict["slugging_perc"],3)
        avg_year_dict['IF/FB'] = None if math.isnan(if_fb) else if_fb
        avg_year_dict['GO/AO'] = None if math.isnan(go_ao) else go_ao

        # MANUALLY AGGREGATE IP IF PITCHER
        # HANDLES CASES WHERE IP HAS DECIMALS
        if most_common_type == 'Pitcher':
            ip_list = [float(stats['IP']) for stats in yearly_stats_dict.values() if stats.get('IP', None)]
            total_ip = self.__sum_ip(ip_list)
            avg_year_dict['IP'] = total_ip

            avg_year_dict['earned_run_avg'] = round(9 * avg_year_dict.get('ER', 0) / avg_year_dict.get('IP', 1), 3)
            avg_year_dict['whip'] = round(( avg_year_dict.get('BB', 0) + avg_year_dict.get('H', 0) ) / avg_year_dict.get('IP', 0), 3)

        # AGGREGATE DEFENSIVE METRICS
        avg_year_dict.update(self.__combine_multi_year_positions(yearly_stats_dict))

        return avg_year_dict

    def __combine_multi_year_positions(self, yearly_stats_dict:dict) -> dict:
        """Combine multiple year defensive positions and metrics
        into one master final dataset.

        Args:
          yearly_stats_dict: Dict of dicts per year.

        Returns:
          Flattened dictionary with combined stats
        """

        # OBJECT TO UPDATE
        positions_and_metric_value_lists:dict[str: dict] = {}
        dWar_list = []

        # CREATE SUB-LISTS OF VALUES
        for stats in yearly_stats_dict.values():

            # DWAR
            dWar_list.append(float(stats['dWAR']))

            # POSITIONS AND DEFENSE
            positions_dict = stats.get('positions', {})
            for position, pos_data in positions_dict.items():
                updated_pos_aggregate = positions_and_metric_value_lists.get(position, {})
                for metric, value in pos_data.items():
                    updated_agg_list = updated_pos_aggregate.get(metric, [])
                    if value is not None:
                        updated_agg_list.append(value)
                    updated_pos_aggregate[metric] = updated_agg_list
                positions_and_metric_value_lists[position] = updated_pos_aggregate
            
        # AGGREGATE PER METRIC PER POSITION
        aggregated_positions = {}
        for position, pos_data in positions_and_metric_value_lists.items():
            updated_position_data = {}
            for metric, value_list in pos_data.items():
                is_median = metric in ['tzr', 'drs']
                aggregated_value = None
                if len(value_list) > 0:
                    aggregated_value = statistics.median(value_list) if is_median else sum(value_list)
                updated_position_data[metric] = aggregated_value
            aggregated_positions[position] = updated_position_data

        # SUM DWAR
        median_dWar = statistics.median(dWar_list)
        total_dWar = sum(dWar_list)

        return {
            'positions': aggregated_positions,
            'dWAR': median_dWar,
            'dWAR_total': total_dWar,
        }

    def __get_career_totals_row(self, div_id:str, soup_object:BeautifulSoup) -> BeautifulSoup:
        """Grab first row of career totals data from any table

        Args:
          div_id: ID attribute of the div object
          soup_object: Beautiful Soup object to extract from

        Returns:
          Beautiful Soup object for career totals
        """
        
        div = soup_object.find('div', attrs = {'id': div_id})
        footer = div.find('tfoot')
        rows = footer.find_all('tr')

        # RETURN FIRST ROW WITH NON BLANK HEADER
        for row in rows:
            header_object:BeautifulSoup = row.find('th')
            if header_object is None: continue
            if len(header_object.get_text()) > 0:
                return row
        
        return None

    def __years_played_list(self, homepage_soup:BeautifulSoup) -> list[str]:
        """Parse the standard batting/pitching table to get a list of the years
           a player played in.

        Args:
          homepage_soup: Beautiful Soup object for the player's homepage on bRef

        Returns:
          List of years as strings
        """
        
        # FIND ALL YEARS BATTING AND PITCHING
        years_parsed: list[str] = []
        for table_prefix in ['batting', 'pitching']:
            standard_table = homepage_soup.find('div', id=lambda x: x in [f'all_{table_prefix}_standard', f'all_players_standard_{table_prefix}'])
            if standard_table:
                year_soup_objects_list = standard_table.find_all('tr', attrs = {'id': re.compile(f'({table_prefix}_standard\.|players_standard_{table_prefix}\.)')})
                for year in year_soup_objects_list:
                    id = year.get('id', '')
                    if 'YR' in id.upper():
                        continue
                    years_parsed.append(id.split('.')[-1])
        
        # FILTER TO UNIQUE
        years_parsed = list(set(years_parsed))

        return list(sorted(years_parsed))

    def __team_w_most_games_played(self, type:str, homepage_soup:BeautifulSoup, years_filter_list:list[int]=[]):
        """Parse the standard batting/pitching table to get a list of the years
           a player played in.

        Args:
          type: Player is Pitcher or Hitter.
          homepage_soup: Beautiful Soup object for the player's homepage on bRef
          years_filter_list: Optional list of years to include

        Returns:
          List of years as strings
        """
        table_prefix = 'batting' if type == 'Hitter' else 'pitching'
        standard_table = homepage_soup.find('div', attrs = {'id': re.compile(f'all_{table_prefix}_standard|all_players_standard_{table_prefix}')})
        year_soup_objects_list = standard_table.find_all('tr', attrs = {'id': re.compile(f'{table_prefix}_standard\.|players_standard_{table_prefix}\.')})
        teams_and_games_played = {}
        for year_object in year_soup_objects_list:
            
            year_str = self.__extract_text_for_element(object=year_object, tag='th', attr_key='data-stat', values=['year_ID', 'year_id'])
            if year_str is None: 
                continue
            if 'YR' in year_str.upper():
                continue
            year = int(year_str)
            if len(years_filter_list) < 1 or (year in years_filter_list):
                team = self.__extract_text_for_element(object=year_object, tag='td', attr_key='data-stat', values=['team_ID', 'team_name_abbr'])
                games_str = self.__extract_text_for_element(object=year_object, tag='td', attr_key='data-stat', values=['G', 'games', 'b_games', 'p_g', 'p_games'])
                if team is None or games_str is None: 
                    continue 
                games = int(games_str)
                if not self.__is_team_id_multiple(team):
                    if team in teams_and_games_played.keys():
                        games += teams_and_games_played[team]
                    teams_and_games_played[team] = games
        if len(teams_and_games_played.keys()) > 0:
            team_w_most_games = sorted(teams_and_games_played.items(), key=operator.itemgetter(1), reverse=True)[0][0]
            return team_w_most_games
        else:
            return 'TOT'

    def __get_stat_list_from_standard_table(self, type:str, homepage_soup:BeautifulSoup, stat_key:str) -> list:
        """Parse the standard batting/pitching table to get a list of values for a given stat.

        Args:
          type: Player is Pitcher or Hitter.
          homepage_soup: Beautiful Soup object for the player's homepage on bRef
          years_filter_list: Optional list of years to include

        Returns:
          List of stats across years.
        """
        table_prefix = 'batting' if type == 'Hitter' else 'pitching'
        standard_table = homepage_soup.find('div', attrs = {'id': re.compile(f'all_{table_prefix}_standard|all_players_standard_{table_prefix}')})
        year_soup_objects_list = standard_table.find_all('tr', attrs = {'id': re.compile(f'{table_prefix}_standard\.|players_standard_{table_prefix}\.')})
        stat_list = []
        for year_object in year_soup_objects_list:
            is_total = ' Yr' in year_object.get('id', '')
            stat_object = year_object.find('td',attrs={'data-stat': stat_key})
            if stat_object and not is_total:
                stat = stat_object.get_text()
                stat = self.__convert_to_numeric(stat)
                stat_list.append(stat)
        
        if len(stat_list) < 1:
            return None

        return stat_list

    def __is_pitcher_from_1901_to_1918(self, year:int, type:str) -> bool:
        """Checks to see if the player is a pitcher and the year is between 1901-1917.
        
        Args:
          year: Year for player stats
          type: String to designate player type ('Pitcher','Hitter')
        
        Returns:
          TRUE or FALSE bool
        """
        try:
            return int(year) > 1900 and int(year) < 1918 and type == 'Pitcher'
        except:
            return False

    def __find_partial_team_stats_row(self, soup_object:BeautifulSoup, team:str, year:int, return_soup_object:bool=False) -> BeautifulSoup:
        """Iterates through each object to try to find specific team stats for a given year.
        
        Args:
          soup_object: Beautiful Soup object to search in
          team: Team ID to search for
          year: Year for player stats
          return_soup_object: Optionally return the soup object instead of the dictionary
        
        Returns:
          Soup object for the players statline for that specific team.
        """

        # TEAM OVERRIDE IS NONE, RETURN NONE
        if not team or soup_object is None:
            return None

        # FIND ALL OPPORTUNITIES
        partial_seasons = soup_object.find_all('tr',attrs={'class':'partial_table'})

        # FILTER TO ROW WHERE TEAM AND YEAR MATCH
        for season in partial_seasons:
            data = self.__parse_generic_bref_row(season)
            if 'team_ID' in data.keys() and 'year_ID' in data.keys():
                if data['team_ID'] == team and str(data['year_ID']) == year:
                    return season if return_soup_object else data

        # NO MATCHES, RETURN NONE    
        return None

    def __conform_stat_category_to_old_structure(self, stat_category:str) -> str:
        """Converts new stat categories to old stat categories for backwards compatibility.
        For example 'b_doubles' -> '2B'

        Args:
          category: New stat category

        Returns:
          Old stat category
        """

        # PARSE STAT CATEGORY
        # IN NEWER TABLES BREF ADDED "b_" PREFIX TO SOME STATS AND MADE THE TEXT
        if stat_category.startswith('b_') and stat_category not in ['b_war']:
            stat_category = stat_category.replace('b_','')
        
        if stat_category.startswith('p_') and stat_category not in ['p_war']:
            stat_category = stat_category.replace('p_','')

        # CONFORM UPGRADED BREF TABLES TO OLD FORMAT
        old_to_new_stat_mapping = {
            'doubles': '2B',
            'triples': '3B',
            'team_name_abbr': 'team_ID',
            'comp_name_abbr': 'lg_ID',
            'awards': 'award_summary',
            'pos': 'pos_season',
            'games': 'G',
            'b_war': 'bWAR',
            'p_war': 'bWAR',
            'dwar': 'dWAR',
            'b_war_def': 'dWAR',
            'roba': 'rOBA',
            'year_id': 'year_ID',
            'bfp': 'batters_faced',
        }
        stat_category = old_to_new_stat_mapping.get(stat_category, stat_category)

        categories_to_keep_default_case = [
            'age','bWAR','dWAR','team_ID','lg_ID','year_ID','pos_season',
            'batting_avg','onbase_perc','slugging_perc','onbase_plus_slugging',
            'onbase_plus_slugging_plus','award_summary','rbat_plus','rOBA',
            'whip','batters_faced','earned_run_avg','batting_avg_bip','year_game',
            'ps_round','date_game','player_game_span','player_game_result',
            'date','date_game','team_name_abbr',
        ]
        if stat_category not in categories_to_keep_default_case:
            stat_category = stat_category.upper()

        return stat_category

    def __is_team_id_multiple(self, team_id:str) -> bool:
        """Checks if team ID is a multiple team ID (ex: 'TOT', '3TM')

        Args:
          team_id: Team ID to check

        Returns:
          TRUE or FALSE bool
        """
        return team_id == 'TOT' or 'TM' in team_id

    def __extract_text_for_element(self, object:BeautifulSoup, tag:str, attr_key:str, values: list[str]) -> str:
        """Extract text from a tag for a given list of possible IDs

        Args:
          object: BeautifulSoup object to search in
          tag: Tag to extract text from
          ids: List of IDs to search for

        Returns:
          Text extracted from tag
        """
        for value in values:
            element = object.find(tag, attrs={attr_key: value})
            if element:
                return element.get_text()
        
        return None

# ------------------------------------------------------------------------
# HELPER METHODS
# ------------------------------------------------------------------------

    @property
    def cache_filename(self) -> str:
        """Name of cache file for player data. """
        years_as_str = '-'.join([str(y) for y in self.years])
        override_type = f"{f'-{self.pitcher_override}' if self.pitcher_override else ''}{f'-{self.hitter_override}' if self.hitter_override else ''}"
        override_team = f'-{self.team_override}' if self.team_override else ""
        override_period = f"-{self.stats_period.id}"
        return f"{years_as_str}-{self.baseball_ref_id}{override_type}{override_team}{override_period}.json"

    def load_cached_data(self, filename:str) -> dict:
        """Check if data file exists in local storage, load and return JSON converted to a dict
        
        Args:
          data: Dictionary of transformed player data.
          filename: Name of the JSON file.

        Returns:
          Dictionary of locally cached player data.
        """

        folder_path = self.cache_folder_path
        full_path = os.path.join(folder_path, filename)

        # RETURN NONE IF FILE DOES NOT EXIST
        if not os.path.isfile(full_path) or self.ignore_cache:
            return None
        
        # RETURN NONE IF FILE IS OVER 10 MINS OLD
        mins_since_modification = self.__file_mins_since_modification(path=full_path)
        if mins_since_modification > 30.0 and not self.disable_cleaning_cache:
            return None

        file = open(full_path, 'r')
        data = json.loads(file.read())

        # REMOVE STALE FILES
        self.__remove_old_files(folder_path=folder_path)
        
        return data

    def __cache_data_locally(self, data:dict, filename:str) -> None:
        """Store player data dictionary locally to cache as JSON.

        Args:
          data: Dictionary of transformed player data.
          filename: Name of the JSON file.

        Returns:
          None
        """
        folder_path = self.cache_folder_path
        full_path = os.path.join(folder_path, filename)
        with open(full_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

        # REMOVE STALE FILES
        self.__remove_old_files(folder_path=folder_path)
    
    def __remove_old_files(self, folder_path:str, mins_cutoff:float = 30.0) -> None:

        # DISABLE CLEANING
        if self.disable_cleaning_cache:
            return

        # CLEAR OUT OLD FILES
        for item in os.listdir(folder_path):
            if item != '.gitkeep':
                item_path = os.path.join(folder_path, item)
                is_file_stale = self.__file_mins_since_modification(item_path) >= mins_cutoff
                if is_file_stale:
                    os.remove(item_path)

    def __file_mins_since_modification(self, path:str) -> float:
        """Checks modified date of file.
           Used for cleaning and reading from cache.

        Args:
          path: String path to file in os.

        Returns:
            Float with time in mins since modification.
        """

        datetime_current = datetime.now()
        datetime_uploaded = datetime.fromtimestamp(os.path.getmtime(path))
        file_age_mins = (datetime_current - datetime_uploaded).total_seconds() / 60.0

        return file_age_mins
    
    def __name_last_initial(self, name:str) -> str:
        """Parse first initial of Player's last name.

        Need to account for >2 words and Suffixes (Jr, Sr, etc)

        Args:
          name: Full name of Player

        Returns:
          First Initial of Last Name (ex: 'Ken Griffey Jr' -> 'g')
        """

        remove_punctuation = str.maketrans('', '', string.punctuation)
        name_wo_punctuation = name.translate(remove_punctuation)

        name_no_suffix = name_wo_punctuation.lower()
        illegal_suffixes = [' jr', ' sr']
        for suffix in illegal_suffixes:
            if name_no_suffix.endswith(suffix):
                name_no_suffix = name_no_suffix.replace(suffix, '')

        last_initial = name_no_suffix.split(' ')[1][:1]
        return last_initial

    def __percentile(self, minValue:float, maxValue:float, value:float) -> float:
        """Get percentile of value given a range.

        Args:
          minValue: minimum of range
          maxValue: maximum of range
          value: value to compare

        Returns:
          float for percentile within range
        """

        percentile_raw = (value-minValue) / (maxValue-minValue)

        return min(percentile_raw,1.0) if percentile_raw > 0 else 0

    def __convert_to_numeric(self, string_value:str):
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
        
    def __aggregate_stats_list(self, category:str, stats:list[any], str_agg_type:str = 'mode') -> any:
        """Aggregate list of stats into one value.

        Args:
          category: What the stat represents.
          stats: List of stats. Can be any type, including str.
          str_agg_type: How to aggregate if type is string. Accepted values are 'mode' or 'last'

        Returns:
          Single value representing the aggregate of stats.
        """

        # CHECK FOR AT LEAST 1 VALUE
        if len(stats) == 0:
            return None
        
        first_value_type = type(stats[0])
        if first_value_type == str:
            match str_agg_type:
                case 'mode': return mode(stats)
                case 'last': return stats[-1]
        elif category == 'IP':

            # CONVERT THE STATS LIST DECIMAL VALUES FROM .1, .2 to .33, .66
            converted_stats = []
            for stat in stats:
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
        else:
            stats = [s for s in stats if len(str(s)) != 0]
            return sum(stats)

    def __sum_ip(self, ip_list: list[float]) -> float:
        """Sum IP list with special handling for partial innings.
        
        Args:
          ip_list: List of IP values as floats.

        Returns:
          Float with total IP.
        """

        if len(ip_list) == 0:
            return 0

        ip_decimal_multiplier = (3 + 1/3)
        whole_numbers = sum([math.floor(ip) for ip in ip_list])
        decimals_regular = sum([ (ip % 1) * ip_decimal_multiplier for ip in ip_list])
        
        decimal_baseball = math.floor(decimals_regular) + ( (decimals_regular % 1) / ip_decimal_multiplier )
        total_ip = round(whole_numbers + decimal_baseball, 1)

        return total_ip

