
import pandas as pd
import cloudscraper
import re
import os
from pathlib import Path
import json
import string
import math
import statistics
import operator
from bs4 import BeautifulSoup
from pprint import pprint
from datetime import datetime
import unidecode
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from .classes.team import Team
    from .classes.accolade import Accolade
except ImportError:
    # USE LOCAL IMPORT
    from classes.team import Team
    from classes.accolade import Accolade

class BaseballReferenceScraper:

# ------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------

    def __init__(self, name:str, year:str, ignore_cache:bool=False, disable_cleaning_cache:bool=False) -> None:

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
        self.source = None
        self.ignore_cache = ignore_cache
        self.disable_cleaning_cache = disable_cleaning_cache
        self.load_time = None
        
        # PARSE MULTI YEARS
        if isinstance(year, list):
            is_multi_value_list = len(year) > 1
            self.is_multi_year = is_multi_value_list
            self.years = year
        else:
            self.is_multi_year = False
            self.years = [year]

        # CHECK FOR TEAM OVERRIDE
        self.team_override = None
        for team_id in [team.value for team in Team]:
            team_match = f'({team_id})' in self.name.upper()
            if team_match and not self.is_multi_year and not is_full_career:
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
            default_bref_id = self.__check_for_default_bref_id(name)
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

    def __check_for_default_bref_id(self, name:str) -> str:
        """Check for player name string in default csv with names and bref ids

        Purpose is to see if bot can avoid needing to scrape Google.

        Args:
          name: Full name of Player

        Returns:
          BrefId (If found), otherwise None
        """ 
        name_cleaned = name.replace("'", "").replace(".", "").lower().strip()
        player_id_filepath = os.path.join(Path(os.path.dirname(__file__)),'player_ids.csv')
        player_ids_pd = pd.read_csv(player_id_filepath)
        player_ids_pd_filtered = player_ids_pd.loc[player_ids_pd['name'] == name_cleaned]
        results_count = len(player_ids_pd_filtered)

        if results_count == 1:
            bref_id = player_ids_pd_filtered['brefid'].max()
            return bref_id if len(bref_id) > 0 else None
        else:
            return None

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
          self.error = "429 - TOO MANY REQUESTS TO BASEBALL REFERENCE. PLEASE TRY AGAIN IN A FEW MINUTES."
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
        years_as_str = '-'.join([str(y) for y in self.years])
        override_type = f"{f'-{self.pitcher_override}' if self.pitcher_override else ''}{f'-{self.hitter_override}' if self.hitter_override else ''}"
        override_team = f'-{self.team_override}' if self.team_override else ""
        cached_filename = f"{years_as_str}-{self.baseball_ref_id}{override_type}{override_team}.json"
        cached_data = self.load_cached_data(cached_filename)
        if cached_data:
            self.source = 'Local Cache'
            end_time = datetime.now()
            self.load_time = round((end_time - start_time).total_seconds(),2)
            return cached_data
        
        # STANDARD STATS PAGE HAS MOST RELEVANT STATS NEEDED
        url_for_homepage_stats = f'https://www.baseball-reference.com/players/{self.first_initial}/{self.baseball_ref_id}.shtml'
        soup_for_homepage_stats = self.__soup_for_url(url_for_homepage_stats, is_baseball_ref_page=True)

        master_stats_dict = {}
        is_full_career = self.years == ['CAREER']
        is_data_from_statcast = False
        for year in self.years:
            # DEFENSE
            stats_dict = {'bref_id': self.baseball_ref_id, 'bref_url': url_for_homepage_stats}
            positional_fielding = self.positions_and_defense(soup_for_homepage_stats=soup_for_homepage_stats,year=year)
            stats_dict.update(positional_fielding)

            # HAND / TYPE
            type = self.type(positions_dict=stats_dict['positions'],year=year)

            # NATIONALITY
            nationality = self.nationality(soup_for_homepage_stats=soup_for_homepage_stats)

            # ROOKIE STATUS YEAR
            rookie_status_year = self.rookie_status_year(soup_for_homepage_stats=soup_for_homepage_stats)

            # IF HALL OF FAME?
            is_hof = self.is_hof(soup_for_homepage_stats=soup_for_homepage_stats)

            # WAR
            stats_dict.update({'bWAR': self.__bWar(soup_for_homepage_stats, year, type)})

            # COVER THE CASE OF NOT HAVING DATA FOR A PARTICULAR YEAR (EX: JOHN SMOLTZ 2000)
            if not type:
                continue

            name = self.player_name(soup_for_homepage_stats)
            years_played = self.__years_played_list(type=type, homepage_soup=soup_for_homepage_stats)
            stats_dict['type'] = type
            stats_dict['hand'] = self.hand(soup_for_homepage_stats, type)
            stats_dict['hand_throw'] = self.hand(soup_for_homepage_stats, type='Pitcher') # ALWAYS PASS PITCHER TO STORE THROWING HAND
            stats_dict['name'] = name
            stats_dict['years_played'] = years_played
            stats_dict['nationality'] = nationality
            stats_dict['rookie_status_year'] = rookie_status_year
            stats_dict['is_hof'] = is_hof
            stats_dict['is_rookie'] = False if is_full_career or self.is_multi_year or rookie_status_year is None else ( int(year) <= rookie_status_year )
            
            # HITTING / HITTING AGAINST
            advanced_stats = self.advanced_stats(type,year=year)
            stats_dict.update(advanced_stats)

            # ICON THRESHOLDS
            icon_threshold_bools = self.__add_icon_threshold_bools(type=type, year=year, stats_dict=stats_dict, homepage_soup=soup_for_homepage_stats)
            stats_dict.update(icon_threshold_bools)
            
            # FILL BLANKS IF NEEDED
            keys_to_fill = ['SH','GIDP','IBB','HBP','SF']
            for key in keys_to_fill:
                if key in stats_dict.keys():
                    raw_value = stats_dict[key]
                    if len(str(raw_value)) == 0:
                        stats_dict[key] = 0

            if self.__is_pitcher_from_1901_to_1918(year=year,type=type):
                team_id = self.__team_w_most_games_played(type, soup_for_homepage_stats, years_filter_list=[int(year)])
                if team_id == 'TOT':
                    team_id = self.__parse_team_after_trade(soup_for_homepage_stats=soup_for_homepage_stats,year=year,type=type)
                stats_dict['team_ID'] = team_id

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
            if 'outs_above_avg' not in stats_dict.keys() and is_hitter: # ONLY NEEDS TO RUN ONCE FOR MULTI-YEAR
                years_list = years_played if is_full_career else self.years
                years_as_ints = [int(y) for y in years_list]
                oaa_dict = self.statcast_outs_above_average_dict(name=name, years=years_as_ints)
                stats_dict['outs_above_avg'] = oaa_dict
                is_data_from_statcast = len(stats_dict['outs_above_avg']) > 0 if stats_dict['outs_above_avg'] else False
                current_positions = stats_dict.get('positions', {})
                for position, oaa in oaa_dict.items():
                    dict_for_position = current_positions.get(position, None)
                    if dict_for_position:
                        dict_for_position['oaa'] = oaa
                        current_positions[position] = dict_for_position
                stats_dict['positions'] = current_positions
            
            # DERIVE 1B 
            triples = 0 if '3B' not in stats_dict.keys() else int(stats_dict['3B'])
            doubles = 0 if '2B' not in stats_dict.keys() else int(stats_dict['2B'])
            stats_dict['1B'] = int(stats_dict['H']) - int(stats_dict['HR']) - triples - doubles
            master_stats_dict[year] = stats_dict
        
        if self.is_multi_year:
            # COMBINE INDIVIDUAL YEAR DATA
            stats_dict.update(self.__combine_multi_year_dict(master_stats_dict))
            stats_dict['team_ID'] = self.__team_w_most_games_played(type, soup_for_homepage_stats, years_filter_list=self.years)
        
        # PARSE ACCOLADES IN TOTAL
        stats_dict['accolades'] = self.__accolades_dict(soup_for_homepage_stats=soup_for_homepage_stats, years_included=self.years)

        # SAVE DATA        
        self.source = f"Baseball Reference{'/Baseball Savant' if is_data_from_statcast else ''}"
        self.__cache_data_locally(data=stats_dict, filename=cached_filename)
        
        # CALC LOAD TIME
        end_time = datetime.now()
        self.load_time = round((end_time - start_time).total_seconds(),2)
        
        return stats_dict
    
    def positions_and_defense(self, soup_for_homepage_stats:BeautifulSoup, year:int) -> dict[str, dict]:
        """Parse standard positions and fielding metrics into a dictionary.

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats on homepage.
          year: Year for Player stats

        Returns:
          Dict for each position with details.
        """

        is_full_career = year == 'CAREER'
        if is_full_career:
            fielding_table = soup_for_homepage_stats.find('div', attrs = {'id': 'div_standard_fielding'})
            fielding_table_footer = fielding_table.find('tfoot')
            fielding_metrics_by_position = fielding_table_footer.find_all('tr')
        else:
            fielding_metrics_by_position = soup_for_homepage_stats.find_all('tr', attrs = {'id': '{}:standard_fielding'.format(year)})

        positions_dict = {}
        for position_data in fielding_metrics_by_position:
            is_position_found = position_data.find('td', attrs={'data-stat':'pos'})
            if is_position_found:
                position_name = position_data.find('td', attrs={'data-stat':'pos'}).get_text()
                games_played = position_data.find('td',attrs={'class':'right','data-stat':'G'}).get_text()

                if position_name != 'TOT':
                    # DRS (2003+)
                    drs_object = position_data.find('td',attrs={'class':'right','data-stat':'bis_runs_total'})
                    drs_rating = drs_object.get_text() if drs_object else None
                    drs_rating = None if (drs_rating or '') == '' else float(drs_rating)
                    
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
                        drs_object = position_data.find('td',attrs={'class':'right','data-stat':'bis_runs_total_per_season'})
                        drs_rating = drs_object.get_text() if drs_object != None else 0
                        drs_rating = 0 if drs_rating == '' else int(drs_rating)

                    # TOTAL ZONE (1953-2003)
                    suffix = '_per_season' if use_stat_per_yr else ''
                    total_zone_object = position_data.find('td',attrs={'class':'right','data-stat':f'tz_runs_total{suffix}'})
                    total_zone_rating = total_zone_object.get_text() if total_zone_object else None
                    total_zone_rating = None if (total_zone_rating or '') == '' else float(total_zone_rating)

                    # UPDATE POSITION DICTIONARY
                    positions_dict[position_name] = {
                        'g': int(games_played) if games_played != '' else 0,
                        'tzr': total_zone_rating,
                        'drs': drs_rating,
                    }
        
        # GET DEFENSIVE WAR IN CASE OF LACK OF TZR AVAILABILITY FOR SEASONS < 1952
        # UPDATE: SCRAPE TOTAL WAR AS WELL
        try:
            if is_full_career:
                summarized_header = self.__get_career_totals_row(div_id='div_batting_value',soup_object=soup_for_homepage_stats)
                num_seasons = float(summarized_header.find('th').get_text().split(" ")[0])
                dwar_object = summarized_header.find('td',attrs={'data-stat':'WAR_def'})
                dwar_rating = float(dwar_object.get_text()) if dwar_object != None else 0
                # USE AVG FOR CAREER
                dwar_rating = round(dwar_rating / num_seasons,2)
            else:
                player_value = soup_for_homepage_stats.find('tr', attrs = {'id': 'batting_value.{}'.format(year)})
                dwar_object = player_value.find('td',attrs={'class':'right','data-stat':'WAR_def'})
                dwar_rating = dwar_object.get_text() if dwar_object != None else 0

        except:
            dwar_rating = 0
        
        # CHECK FOR PINCH HITTER
        # PINCH HITTERS WILL NOT HAVE A RECORD IN THE FIELDING TABLE
        is_positions_empty = len(positions_dict) == 0
        metadata = soup_for_homepage_stats.find('div', attrs = {'id': 'meta'})
        if is_positions_empty and metadata:
            # FIND THE HAND TAG IN THE METADATA LIST
            for strong_tag in metadata.find_all('strong'):
                positions_tag = 'Positions:'
                if strong_tag.text == positions_tag:
                    positions_str = strong_tag.next_sibling.replace('•','').rstrip()
                    if 'Pinch Hitter' in positions_str:
                        positions_dict['DH'] = {
                            'g': 0,
                            'tzr': None,
                            'drs': None
                        }
        return {
            'positions': positions_dict,
            'dWAR': dwar_rating,
        }

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
            return war_rating
        except:
            return 0.0

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

    def advanced_stats(self, type:str, year:int) -> dict:
        """Parse advanced stats page from baseball reference.

        Standard and ratio stats. For Pitchers, uses batting against table.

        Args:
          type: Player is Pitcher or Hitter.
          year: Year for Player stats

        Returns:
          Dict with standard and ratio statistics.
        """

        is_full_career = year == 'CAREER'

        # SCRAPE ADVANCED STATS PAGE
        page_suffix = '-bat' if type == 'Hitter' else '-pitch'
        url_advanced_stats = 'https://www.baseball-reference.com/players/{}/{}{}.shtml'.format(self.first_initial, self.baseball_ref_id, page_suffix)
        soup_for_advanced_stats = self.__soup_for_url(url_advanced_stats, is_baseball_ref_page=True)

        table_prefix = 'batting' if type == 'Hitter' else 'pitching'

        if is_full_career:
            standard_row = self.__get_career_totals_row(div_id=f'all_{table_prefix}_standard',soup_object=soup_for_advanced_stats)
            
        else:
            standard_row_key = f'{table_prefix}_standard.{year}'
            standard_row = soup_for_advanced_stats.find('tr',attrs={'class':'full','id': standard_row_key})

        advanced_stats = {}

        # BATTING AGAINST (PITCHERS ONLY)
        if type == 'Pitcher':
            if is_full_career:
                try:
                    batting_against_table = self.__get_career_totals_row(div_id='div_pitching_batting',soup_object=soup_for_advanced_stats)
                    advanced_stats.update(self.__parse_generic_bref_row(batting_against_table))
                except:
                    advanced_stats.update(self.__parse_splits_stats(year=year))
            else:
                # LOOK AT "SPLITS" PAGE FOR PRE-1916 PITCHERS
                if self.__is_pitcher_from_1901_to_1918(year=year,type=type):
                    advanced_stats.update(self.__parse_splits_stats(year=year))
                else:
                    batting_against_soup = soup_for_advanced_stats.find('table', attrs={'id': 'pitching_batting'})
                    partial_stats = self.__find_partial_team_stats_row(soup_object=batting_against_soup, team=self.team_override, year=year)
                    if self.team_override and partial_stats:
                        advanced_stats.update(partial_stats)
                    else:
                        batting_against_row = soup_for_advanced_stats.find('tr',attrs={'class':'full','id': f'pitching_batting.{year}'})
                        advanced_stats.update(self.__parse_generic_bref_row(batting_against_row))
        
        # STANDARD STATS
        standard_table_soup = soup_for_advanced_stats.find('div', attrs={'class': 'table_container', 'id': f'div_{table_prefix}_standard'})
        partial_stats_soup = self.__find_partial_team_stats_row(soup_object=standard_table_soup, team=self.team_override, year=year, return_soup_object=True)
        if self.team_override and partial_stats_soup:
            advanced_stats.update(self.__parse_standard_stats(type, partial_stats_soup, included_g_for_pitcher=is_full_career))
        else:
            standard_stats_dict = self.__parse_standard_stats(type, standard_row, included_g_for_pitcher=is_full_career)
            advanced_stats.update(standard_stats_dict)

        # PARSE AWARDS IF FULL CAREER
        if is_full_career or self.team_override:
            year_filter = '' if is_full_career else str(year)
            all_year_standard_stats = soup_for_advanced_stats.find_all('tr',attrs={'class':'full','id': re.compile(f"{table_prefix}_standard.{year_filter}")})
            awards_total = ""
            for year_stats in all_year_standard_stats:
                stats_dict = self.__parse_standard_stats(type, year_stats)
                if 'is_sv_leader' in stats_dict:
                    advanced_stats['is_sv_leader'] = stats_dict['is_sv_leader']
                year_award_summary = stats_dict['award_summary']
                if len(year_award_summary) > 0:
                    awards_total = f'{awards_total},{year_award_summary}'
            advanced_stats['award_summary'] = awards_total

        # IF A PLAYER PLAYED FOR MULTIPLE TEAMS IN ONE SEASON, SELECT THE LAST TEAM THEY PLAYED FOR.
        team_id_key = 'team_ID'
        if team_id_key in advanced_stats.keys():
            if advanced_stats[team_id_key] == 'TOT':
                advanced_stats[team_id_key] = self.__parse_team_after_trade(soup_for_homepage_stats=soup_for_advanced_stats,year=year,type=type)

        # FILL IN EMPTY STATS
        current_categories = advanced_stats.keys()
        if 'PA' not in current_categories:
            advanced_stats['is_stats_estimate'] = True
            # CHECK FOR BATTERS FACED
            if advanced_stats['batters_faced'] > 0:
                advanced_stats['PA'] = advanced_stats['batters_faced']
            # ESTIMATE PA AGAINST
            else:
                advanced_stats['PA'] = advanced_stats['IP'] * 4.25 # NEED TO ESTIMATE PA BASED ON AVG PA PER INNING
        
        keys_to_fill = ['SH','HBP','IBB','SF']
        for key in keys_to_fill:
            if key not in current_categories:
                advanced_stats[key] = 0

        if '2B' not in current_categories:
            maxDoubles = 0.25
            eraPercentile = self.__percentile(minValue=1.0, maxValue=5.0, value=advanced_stats['earned_run_avg'])
            advanced_stats['2B'] = int(advanced_stats['H'] * eraPercentile * maxDoubles)

        if '3B' not in current_categories:
            maxTriples = 0.025
            eraPercentile = self.__percentile(minValue=1.0, maxValue=5.0, value=advanced_stats['earned_run_avg'])
            advanced_stats['3B'] = int(advanced_stats['H'] * eraPercentile * maxTriples)
        
        if 'slugging_perc' not in current_categories:
            ab = advanced_stats['PA'] - advanced_stats['BB'] - advanced_stats['HBP']
            singles = advanced_stats['H'] - advanced_stats['2B'] - advanced_stats['3B'] - advanced_stats['HR']
            total_bases = (singles + (2 * advanced_stats['2B']) + (3 * advanced_stats['3B']) + (4 * advanced_stats['HR']))
            advanced_stats['AB'] = ab
            advanced_stats['TB'] = total_bases
            advanced_stats['slugging_perc'] = total_bases / ab

        if 'onbase_perc' not in current_categories:
            advanced_stats['onbase_perc'] = (advanced_stats['H'] + advanced_stats['BB']) / advanced_stats['PA']
        
        if 'batting_avg' not in current_categories:
            advanced_stats['batting_avg'] = advanced_stats['H'] / advanced_stats['AB']
        
        if 'SB' not in current_categories:
            advanced_stats['SB'] = 0

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
        if type == 'Pitcher':
            ip_per_gs = 0.0
            starter_stats_soup = soup_for_advanced_stats.find('div', attrs={'id': 'div_pitching_starter'})
            if starter_stats_soup:
                partial_stats_soup = self.__find_partial_team_stats_row(soup_object=starter_stats_soup, team=self.team_override, year=year, return_soup_object=True)
                row_accounting_for_team_override = partial_stats_soup if self.team_override and partial_stats_soup else starter_stats_soup.find('tr', attrs={'id': f'pitching_starter.{year}'})
                if row_accounting_for_team_override:
                    ip_per_start_object = row_accounting_for_team_override.find('td', attrs={'data-stat': 'innings_per_start'})
                    if ip_per_start_object:
                        ip_per_start_text = ip_per_start_object.get_text()
                        ip_per_gs = self.__convert_to_numeric(ip_per_start_text)
            advanced_stats['IP/GS'] = ip_per_gs
        
        return advanced_stats

    def __parse_standard_stats(self, type:str, soup_row:BeautifulSoup, included_g_for_pitcher:bool=False) -> dict:
        """Parse standard batting table.

        Args:
          type: Player is Pitcher or Hitter.
          soup_row: BeautifulSoup row object with season stats.
          included_g_for_pitcher: Boolean for whether to parse 'G' for pitchers.

        Returns:
          Dict with standard hitting statistics.
        """

        standard_stats_dict = {}

        for category in soup_row:
            stat_category = category['data-stat']
            # LEAGUE LEADER?
            is_league_leader = '<strong>' in str(category) or '<em>' in str(category) # LEAGUE LEADERS ON BASEBALL REF ARE DENOTED BY BOLD OR ITALIC TEXT

            if stat_category in ('SV','HR','SB','SO'):
                # SAVE THIS INFO FOR RP, HR, OR SB ICONS
                standard_stats_dict[f'is_{stat_category.lower()}_leader'] = is_league_leader
             
            stat = category.get_text()
            if stat_category in ['SF','IBB','CS'] and stat == '':
                stat = '0'
            stat = self.__convert_to_numeric(stat)

            if type == 'Pitcher':
                pitching_categories = ['earned_run_avg','team_ID','G','GS','W','SV','IP','H','2B','3B','HR','BB','SO','HBP','whip','batters_faced','award_summary']
                fill_zeros = ['GS','W','SV','H','2B','3B','HR','BB','SO','HBP','batters_faced']
                if included_g_for_pitcher:
                    pitching_categories.append('G')
                if stat_category in pitching_categories:
                    if len(str(stat)) == 0 and stat_category in fill_zeros:
                        stat = 0
                    standard_stats_dict[stat_category] = stat
            else:
                if stat_category == 'SO' and len(str(stat)) == 0:
                    standard_stats_dict[stat_category] = 0
                else:
                    standard_stats_dict[stat_category] = stat

        return standard_stats_dict

    def __parse_splits_stats(self,year:int) -> dict:
        """Parse standard statline from the "splits" page on Baseball Reference

        Args:
          year: Year for data stats (ex: 2021, CAREER)

        Returns:
          Dict with standard statistics.
        """
        url_splits = f'https://www.baseball-reference.com/players/split.fcgi?id={self.baseball_ref_id}&year={year}&t=p'
        soup_for_split = self.__soup_for_url(url_splits, is_baseball_ref_page=True)
        tables_w_incomplete_split = [a for a in soup_for_split.select('th[data-stat="incomplete_split"]')]
        stats = tables_w_incomplete_split[1]
        header_values = [self.__convert_to_numeric(sib['data-stat']) for sib in stats.next_siblings]
        stats_values = [self.__convert_to_numeric(sib.string) for sib in stats.next_siblings]
        batting_against_dict = dict(zip(header_values, stats_values))
        return batting_against_dict

    def __parse_generic_bref_row(self, row:BeautifulSoup) -> dict:
        """Parse hitting stats a pitcher allowed.

        Args:
          row: BeautifulSoup tr row object with stats

        Returns:
          Dict with statistics
        """

        final_stats_dict = {}
        if row is not None:
            for category in row:
                stat_category = category['data-stat']
                stat = category.get_text()
                stat = self.__convert_to_numeric(stat)
                if stat_category in ['IBB'] and stat == '':
                    stat = 0
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

    def __parse_team_after_trade(self, soup_for_homepage_stats:BeautifulSoup, year:int, type:str) -> str:
        """Parse the last team a player playe dfor in the given season.

        Args:
          soup_for_homepage_stats: BeautifulSoup object for advanced stats table.
          year: Year for Player stats
          type: Player is Pitcher or Hitter.

        Returns:
          Team Id for last team the player played on in year
        """

        header_prefix = 'batting' if type == 'Hitter' else 'pitching'
        standard_table = soup_for_homepage_stats.find('table',attrs={'id':f'{header_prefix}_standard'})
        if standard_table is None:
            return 'TOT'
        partial_objects_list = standard_table.find_all('tr',attrs={'class':'partial_table'})
        teams_list = []
        # ITERATE THROUGH PARTIAL SEASONS
        try:
            for partial_object in partial_objects_list:
                # SAVE TEAMS ONLY FOR year SEASON
                object_for_this_season = partial_object.find('th',attrs={'data-stat':'year_ID', 'csk': re.compile(str(year))})
                if object_for_this_season:
                    # PARSE TEAM ID
                    team_object = partial_object.find('td', attrs={'data-stat':'team_ID'})
                    if team_object is None:
                        continue
                    team_id = team_object.get_text()
                    if team_id != '' and team_id != 'TOT':
                        # ADD TO TEAMS LIST
                        teams_list.append(team_id)
            last_team = teams_list[-1]
            return last_team
        except:
            return 'TOT'

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
                list_of_values_for_stat = self.__get_stat_list_from_standard_table(type, homepage_soup, stat_key=stat)
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

    def __combine_multi_year_dict(self, yearly_stats_dict):
        """Combine multiple years into one master final dataset

        Args:
          yearly_stats_dict: Dict of dicts per year.

        Returns:
          Flattened dictionary with combined stats
        """
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
        }

        # FLATTEN MULTI YEAR STATS
        yearPd = pd.DataFrame.from_dict(yearly_stats_dict, orient='index')
        columns_to_remove = list(set(column_aggs.keys()) - set(yearPd.columns))
        if max(self.years) < 2015:
            columns_to_remove.append('sprint_speed')
        [column_aggs.pop(key) for key in columns_to_remove if key in column_aggs.keys()]
        avg_year = yearPd.groupby(by='name',as_index=False).agg(column_aggs)
        # CALCULATE RATES
        avg_year["batting_avg"] = round(avg_year['H'] / float(avg_year['AB']),3)
        avg_year["onbase_perc"] = round((avg_year['H'] + avg_year['BB'] + avg_year['HBP']) / float(avg_year['AB'] + avg_year['BB'] + avg_year['HBP'] + avg_year['SF']),3)
        avg_year["slugging_perc"] = round(avg_year['TB'] / avg_year['AB'],3)
        avg_year["onbase_plus_slugging"] = round(avg_year["onbase_perc"] + avg_year["slugging_perc"],3)
        avg_year['IF/FB'] = None if math.isnan(avg_year['IF/FB']) else avg_year['IF/FB']
        avg_year['GO/AO'] = None if math.isnan(avg_year['GO/AO']) else avg_year['GO/AO']

        avg_year_dict = avg_year.iloc[0].to_dict()

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
        aggregated_dWar = statistics.median(dWar_list)

        return {
            'positions': aggregated_positions,
            'dWar': aggregated_dWar
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
        row = footer.find_all('tr')[0]
        return row

    def __years_played_list(self, type:str, homepage_soup:BeautifulSoup) -> list[str]:
        """Parse the standard batting/pitching table to get a list of the years
           a player played in.

        Args:
          homepage_soup: Beautiful Soup object for the player's homepage on bRef

        Returns:
          List of years as strings
        """
        table_prefix = 'batting' if type == 'Hitter' else 'pitching'
        standard_table = homepage_soup.find('div', attrs = {'id': f'all_{table_prefix}_standard'})
        year_soup_objects_list = standard_table.find_all('tr', attrs = {'id': re.compile(f'{table_prefix}_standard.')})
        years_parsed = [year['id'].split('.')[-1] for year in year_soup_objects_list]
        return years_parsed

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
        standard_table = homepage_soup.find('div', attrs = {'id': f'all_{table_prefix}_standard'})
        year_soup_objects_list = standard_table.find_all('tr', attrs = {'id': re.compile(f'{table_prefix}_standard.')})
        teams_and_games_played = {}
        for year_object in year_soup_objects_list:
            year = int(year_object.find('th',attrs={'data-stat': 'year_ID'}).get_text())
            if len(years_filter_list) < 1 or (year in years_filter_list):
                team = year_object.find('td',attrs={'data-stat': 'team_ID'}).get_text()
                games = int(year_object.find('td',attrs={'data-stat': 'G'}).get_text())
                if team != 'TOT':
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
        standard_table = homepage_soup.find('div', attrs = {'id': f'all_{table_prefix}_standard'})
        year_soup_objects_list = standard_table.find_all('tr', attrs = {'id': re.compile(f'{table_prefix}_standard.')})
        stat_list = []
        for year_object in year_soup_objects_list:
            stat_object = year_object.find('td',attrs={'data-stat': stat_key})
            if stat_object:
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
        if not team:
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
            
# ------------------------------------------------------------------------
# HELPER METHODS
# ------------------------------------------------------------------------

    def load_cached_data(self, filename:str) -> dict:
        """Check if data file exists in local storage, load and return JSON converted to a dict
        
        Args:
          data: Dictionary of transformed player data.
          filename: Name of the JSON file.

        Returns:
          Dictionary of locally cached player data.
        """

        folder_path = os.path.join(Path(os.path.dirname(__file__)), 'cache_data')
        full_path = os.path.join(folder_path, filename)

        # RETURN NONE IF FILE DOES NOT EXIST
        if not os.path.isfile(full_path) or self.ignore_cache:
            return None
        
        # RETURN NONE IF FILE IS OVER 10 MINS OLD
        mins_since_modification = self.__file_mins_since_modification(path=full_path)
        if mins_since_modification > 10.0 and not self.disable_cleaning_cache:
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
        folder_path = os.path.join(Path(os.path.dirname(__file__)), 'cache_data')
        full_path = os.path.join(folder_path, filename)
        with open(full_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

        # REMOVE STALE FILES
        self.__remove_old_files(folder_path=folder_path)
    
    def __remove_old_files(self, folder_path:str, mins_cutoff:float = 10.0) -> None:

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

        if string_value.isdigit():
            return int(string_value)
        elif string_value.replace('.','',1).isdigit() and string_value.count('.') < 2:
            return float(string_value)
        else:
            # RETURN ORIGINAL STRING
            return string_value