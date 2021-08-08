
import pandas as pd
import requests
import re
import ast
import os
from pathlib import Path
import json
import string
import statistics
import operator
from bs4 import BeautifulSoup
from pprint import pprint
from datetime import datetime
import unidecode

class BaseballReferenceScraper:

# ------------------------------------------------------------------------
# INIT

    def __init__(self, name, year):
        if year.upper() == 'CAREER':
            year = 'CAREER'
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
        if isinstance(year, list):
            is_multi_value_list = len(year) > 1
            self.is_multi_year = is_multi_value_list
            self.years = year
        else:
            self.is_multi_year = False
            self.years = [year]
        # CHECK FOR BASEBALL REFERENCE ID
        self.is_name_a_bref_id = any(char.isdigit() for char in name)
        if self.is_name_a_bref_id:
            self.baseball_ref_id = name.lower()
        else:
            # CHECK DEFAULT CSV
            default_bref_id = self.__check_for_default_bref_id(name)
            if default_bref_id:
                self.baseball_ref_id = default_bref_id
            else:
                # SEARCH GOOGLE
                self.baseball_ref_id = self.search_google_for_b_ref_id(name, year)

        self.first_initial = self.baseball_ref_id[:1]

# ------------------------------------------------------------------------
# SCRAPE WEBSITES

    def __check_for_default_bref_id(self, name):
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

    def search_google_for_b_ref_id(self, name, year):
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
            raise RuntimeError('Google has an overload of requests coming from your IP Address. Wait a few minutes and try again.')

        # NO BASEBALL REFERENCE RESULTS FOR THAT NAME AND YEAR
        if search_results == []:
            raise AttributeError('Cannot Find BRef Page for {} in {}'.format(name,year))
          

        top_result_url = search_results[0]["href"]
        player_b_ref_id = top_result_url.split('.shtml')[0].split('/')[-1]
        return player_b_ref_id

    def __soup_for_url(self, url, is_baseball_ref_page=False):
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

    def html_for_url(self, url):
        """Make request for URL to get HTML

        Args:
          url: URL for the request.

        Raises:
            AttributeError: Cannot find Baseball Ref Page for name/year combo.

        Returns:
          HTML string for URL request.
        """

        html = requests.get(url)

        return html.text

# ------------------------------------------------------------------------
# PARSING HTML

    def player_statline(self):
        """Scrape baseball-reference.com to get all relevant stats

        Args:
          None

        Returns:
          Dict with all categories and stats.
        """

        # STANDARD STATS PAGE HAS MOST RELEVANT STATS NEEDED
        url_for_homepage_stats = 'https://www.baseball-reference.com/players/{}/{}.shtml'.format(self.first_initial,self.baseball_ref_id)
        soup_for_homepage_stats = self.__soup_for_url(url_for_homepage_stats, is_baseball_ref_page=True)

        master_stats_dict = {}
        is_full_career = self.years == ['CAREER']
        for year in self.years:
            # DEFENSE
            stats_dict = {'bref_id': self.baseball_ref_id}
            positional_fielding = self.positional_fielding(soup_for_homepage_stats=soup_for_homepage_stats,year=year)
            stats_dict.update(positional_fielding)

            # HAND / TYPE
            type = self.type(positional_fielding,year=year)

            # WAR
            stats_dict.update({'bWAR': self.__bWar(soup_for_homepage_stats, year, type)})

            # COVER THE CASE OF NOT HAVING DATA FOR A PARTICULAR YEAR (EX: JOHN SMOLTZ 2000)
            if not type:
                continue

            name = self.player_name(soup_for_homepage_stats)
            years_played = self.__years_played_list(type=type, homepage_soup=soup_for_homepage_stats)
            stats_dict['type'] = type
            stats_dict['hand'] = self.hand(soup_for_homepage_stats, type)
            stats_dict['name'] = name
            stats_dict['years_played'] = years_played
            
            # HITTING / HITTING AGAINST
            advanced_stats = self.advanced_stats(type,year=year)
            stats_dict.update(advanced_stats)

            # ICON THRESHOLDS
            icon_threshold_bools = self.__add_icon_threshold_bools(type=type, year=year, stats_dict=stats_dict, homepage_soup=soup_for_homepage_stats)
            stats_dict.update(icon_threshold_bools)

            # FULL CAREER
            if is_full_career:
                stats_dict['team_ID'] = self.__team_multi_year(type, soup_for_homepage_stats)
                sprint_speed_list = []
                for year in years_played:
                    sprint_speed = self.sprint_speed(name=name, year=year, type=type)
                    if sprint_speed:
                        sprint_speed_list.append(sprint_speed)
                if len(sprint_speed_list) > 0:
                    stats_dict['sprint_speed'] = sum(sprint_speed_list) / len(sprint_speed_list)
                else:
                    stats_dict['sprint_speed'] = None
            else:
                stats_dict['sprint_speed'] = self.sprint_speed(name=name, year=year, type=type)
            
            # DERIVE 1B 
            stats_dict['1B'] = int(stats_dict['H']) - int(stats_dict['HR']) - int(stats_dict['3B']) - int(stats_dict['2B'])
            master_stats_dict[year] = stats_dict
        
        if self.is_multi_year:
            # COMBINE INDIVIDUAL YEAR DATA
            stats_dict.update(self.__combine_multi_year_dict(master_stats_dict))
            stats_dict['team_ID'] = self.__team_multi_year(type, soup_for_homepage_stats, years_filter_list=self.years)
            return stats_dict
        else:
            return stats_dict

    def positional_fielding(self, soup_for_homepage_stats, year):
        """Parse standard fielding metrics (tzr, games_played).

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats on homepage.
          year: Year for Player stats

        Returns:
          Dict with name, tzr, and games played per position.
        """
        is_full_career = year == 'CAREER'
        if is_full_career:
            fielding_table = soup_for_homepage_stats.find('div', attrs = {'id': 'div_standard_fielding'})
            fielding_table_footer = fielding_table.find('tfoot')
            fielding_metrics_by_position = fielding_table_footer.find_all('tr')
        else:
            fielding_metrics_by_position = soup_for_homepage_stats.find_all('tr', attrs = {'id': '{}:standard_fielding'.format(year)})

        # POSITIONAL TZR
        all_positions = {}
        for index, position_info in enumerate(fielding_metrics_by_position, 1):
            # PARSE POSITION ATTRIBUTES
            is_position_found = position_info.find('td', attrs={'data-stat':'pos'})
            if is_position_found:
                position_name = position_info.find('td', attrs={'data-stat':'pos'}).get_text()
                games_played = position_info.find('td',attrs={'class':'right','data-stat':'G'}).get_text()
                    
                if position_name != 'TOT':
                    # DRS (2003+)
                    drs_metric_name = 'bis_runs_total'
                    drs_object = position_info.find('td',attrs={'class':'right','data-stat':'bis_runs_total'})
                    drs_rating = drs_object.get_text() if drs_object != None else 0
                    drs_rating = 0 if drs_rating == '' else drs_rating
                    
                    # ACCOUNT FOR SHORTENED OR ONGOING SEASONS
                    if is_full_career:
                        use_stat_per_yr = True
                    else:
                        today = datetime.today()
                        card_year_end_date = datetime(int(year), 10, 15)
                        is_year_end_date_before_today = today < card_year_end_date
                        use_stat_per_yr = (str(year) == '2020' or is_year_end_date_before_today) and int(drs_rating) > 0
                    
                    if use_stat_per_yr:
                        drs_object = position_info.find('td',attrs={'class':'right','data-stat':'bis_runs_total_per_season'})
                        drs_rating = drs_object.get_text() if drs_object != None else 0
                        drs_rating = 0 if drs_rating == '' else int(drs_rating)

                    # TOTAL ZONE (1953-2003)
                    suffix = '_per_season' if use_stat_per_yr else ''
                    total_zone_object = position_info.find('td',attrs={'class':'right','data-stat':f'tz_runs_total{suffix}'})
                    total_zone_rating = total_zone_object.get_text() if total_zone_object != None else 0
                    total_zone_rating = 0 if total_zone_rating == '' else total_zone_rating

                    # UPDATE POSITION DICTIONARY
                    position_dict = {
                        'Position{}'.format(index): position_name,
                        'gPosition{}'.format(index): games_played if games_played != '' else 0,
                        'tzPosition{}'.format(index): total_zone_rating,
                        'drsPosition{}'.format(index): drs_rating
                    }
                    all_positions.update(position_dict)

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
            all_positions.update({'dWAR': dwar_rating})
        except:
            all_positions.update({'dWAR': 0})

        return all_positions

    def __bWar(self, soup_for_homepage_stats, year, type):
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

    def hand(self, soup_for_homepage_stats, type):
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
            raise ValueError('No metadata found')
        # FIND THE HAND TAG IN THE METADATA LIST
        for strong_tag in metadata.find_all('strong'):
            hand_tag = 'Bats: ' if type == 'Hitter' else 'Throws: '
            if strong_tag.text == hand_tag:
                hand = strong_tag.next_sibling.replace('•','').rstrip()
                return hand

    def player_name(self, soup_for_homepage_stats):
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
            raise ValueError('No player name found')
        # FIND THE ITEMPROP TAG
        name_object = metadata.find('h1', attrs = {'itemprop': 'name'})
        name_string = name_object.find('span').get_text()
        return name_string

    def type(self, positional_fielding, year):
        """Guess Player Type (Pitcher or Hitter) based on games played at each position.

        Args:
          positional_fielding: Dict with positions, games_played, and tzr
          year: Year for Player stats

        Raises:
          AttributeError: This Player Played 0 Games. Check Player Name and Year.

        Returns:
          Either 'Hitter' or 'Pitcher' string.
        """

        games_as_pitcher = 0
        games_as_hitter = 0
        positions = int((len(positional_fielding)-1) / 4)
        # SPLIT GAMES BETWEEN TYPES
        for position_index in range(1, positions + 1):
            games = int(positional_fielding['gPosition{}'.format(position_index)])
            position = positional_fielding['Position{}'.format(position_index)]
            if position == 'P':
                games_as_pitcher += games
            else:
                games_as_hitter += games

        # CHECK FOR TYPE OVERRIDE
        is_pitcher_override = '(PITCHER)' in self.name.upper() and games_as_pitcher > 0
        is_hitter_override = '(HITTER)' in self.name.upper()

        # COMPARE GAMES PLAYED IN BOTH TYPES
        total_games = games_as_hitter + games_as_pitcher
        if total_games == 0:
            if self.is_multi_year:
                return None
            else:
                raise AttributeError('This Player Played 0 Games in {}. Check Player Name and Year'.format(year))
        elif is_pitcher_override:
            return "Pitcher"
        elif is_hitter_override:
            return "Hitter"
        elif games_as_pitcher < games_as_hitter:
            return "Hitter"
        else:
            return "Pitcher"

    def sprint_speed(self, name, year, type):
        """Sprint Speed for player from Baseball Savant (Only applicable to 2015+).

        Args:
          name: Full name of Player
          year: Year for Player stats
          type: String for player type (Pitcher or Hitter)

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
            first_name_cleaned = unidecode.unidecode(name.split(' ')[0].replace(".", ""))
            last_name = unidecode.unidecode(name.split(' ')[1])
            full_name_baseball_savant = unidecode.unidecode(player_dict['name_display_last_first'])
            is_player_match = first_name_cleaned in full_name_baseball_savant \
                              and last_name in full_name_baseball_savant
            if is_player_match:
                speed = float(player_dict['r_sprint_speed_top50percent_pretty'])
                return speed
        # IF NOT FOUND, RETURN LEAGUE AVG
        default_speed = 26.25
        return default_speed

    def advanced_stats(self, type, year):
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
            standard_table = self.__get_career_totals_row(div_id=f'all_{table_prefix}_standard',soup_object=soup_for_advanced_stats)
            
        else:
            standard_table_key = '{}_standard.{}'.format(table_prefix, year)
            standard_table = soup_for_advanced_stats.find('tr',attrs={'class':'full','id': standard_table_key})

        advanced_stats = {}

        # BATTING AGAINST (PITCHERS ONLY)
        if type == 'Pitcher':
            if is_full_career:
                batting_against_table = self.__get_career_totals_row(div_id='div_pitching_batting',soup_object=soup_for_advanced_stats)
            else:
                batting_against_table = soup_for_advanced_stats.find('tr',attrs={'class':'full','id': 'pitching_batting.{}'.format(year)})
            advanced_stats.update(self.__parse_batting_against(batting_against_table))
        
        # STANDARD STATS
        standard_stats_dict = self.__parse_standard_stats(type, standard_table, included_g_for_pitcher=is_full_career)
        advanced_stats.update(standard_stats_dict)

        # PARSE AWARDS IF FULL CAREER
        if is_full_career:
            all_year_standard_stats = soup_for_advanced_stats.find_all('tr',attrs={'class':'full','id': re.compile(f"{table_prefix}_standard.")})
            awards_total = ""
            for year in all_year_standard_stats:
                stats_dict = self.__parse_standard_stats(type, year)
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
                advanced_stats[team_id_key] = self.__parse_team_after_trade(advanced_stats_soup=soup_for_advanced_stats,year=year)

        # RATIO STATS
        if is_full_career:
            ratio_table_key = f'div_{table_prefix}_ratio'
            ratio_table = self.__get_career_totals_row(div_id=ratio_table_key,soup_object=soup_for_advanced_stats)
        else:
            ratio_table_key = f'{table_prefix}_ratio.{year}'
            ratio_table = soup_for_advanced_stats.find('tr', attrs = {'class':'full','id': ratio_table_key})
        advanced_stats.update(self.__parse_ratio_stats(ratio_table,year=year))

        return advanced_stats

    def __parse_standard_stats(self, type, standard_table, included_g_for_pitcher=False):
        """Parse standard batting table.

        Args:
          type: Player is Pitcher or Hitter.
          standard_table: BeautifulSoup table object with season hitting stats.
          included_g_for_pitcher: Boolean for whether to parse 'G' for pitchers.

        Returns:
          Dict with standard hitting statistics.
        """

        standard_stats_dict = {}

        for category in standard_table:
            stat_category = category['data-stat']
            # SAVE THIS INFO FOR RP ICON
            if stat_category == 'SV':
                # LEAGUE LEADERS ON BASEBALL REF ARE DENOTED BY BOLD TEXT
                is_league_leader = '<strong>' in str(category)
                standard_stats_dict['is_sv_leader'] = is_league_leader
             
            stat = category.get_text()
            if stat_category in ['SF','IBB','CS'] and stat == '':
                stat = '0'
            stat = self.__convert_to_numeric(stat)

            if type == 'Pitcher':
                pitching_categories = ['earned_run_avg','GS','W','SV','IP','award_summary']
                if included_g_for_pitcher:
                    pitching_categories.append('G')
                if stat_category in pitching_categories:
                    standard_stats_dict[stat_category] = stat
            else:
                standard_stats_dict[stat_category] = stat

        return standard_stats_dict

    def __parse_batting_against(self, batting_against_table):
        """Parse hitting stats a pitcher allowed.

        Args:
          batting_against_table: BeautifulSoup table object with opponent hitting stats.

        Raises:
          ValueError: No Pitcher Data Before 1918 can be used to calculate Showdown Metrics needed for a card.

        Returns:
          Dict with opponent hitting statistics.
        """

        if batting_against_table is None:
            # NO HITTING AGAINST DATA AVAILABLE BEFORE 1918.
            raise ValueError('No Pitcher Data Before 1918 can be used to calculate Showdown Metrics needed for a card')

        batting_against_dict = {}
        for category in batting_against_table:
            stat_category = category['data-stat']
            stat = category.get_text()
            stat = self.__convert_to_numeric(stat)
            batting_against_dict[stat_category]= stat

        return batting_against_dict

    def __parse_ratio_stats(self, ratio_table, year):
        """Parse out ratios (GB/AO, PU)

        Args:
          ratio_table: BeautifulSoup table object with ratios.
          year: Year for Player stats

        Returns:
          Dict with ratio statistics.
        """

        if ratio_table is None:
            # DEFAULT TO 50 / 50 SPLIT
            gb_ao_ratio = 1.0
            pu_ratio = 0.5
        else:
            gb_ao_ratio_raw = ratio_table.find('td',attrs={'class':'right','data-stat': 'go_ao_ratio'}).get_text()
            try:
                gb_ao_ratio = float(gb_ao_ratio_raw)
            except:
                gb_ao_ratio = 1.0
            pu_ratio_raw = ratio_table.find('td',attrs={'class':'right','data-stat': 'infield_fb_perc'})
            if pu_ratio_raw:
                # PU RATIO DATA AVAILABLE AFTER 1988
                pu_ratio_text = pu_ratio_raw.get_text()
                pu_ratio_text_cleaned = '20' if pu_ratio_text == '' else pu_ratio_text
                pu_ratio = int(pu_ratio_text_cleaned.replace('%','')) / 100.0
            else:
                pu_ratio = 0.20

        return {
            'GO/AO': gb_ao_ratio,
            'IF/FB': pu_ratio
        }

    def __parse_team_after_trade(self, advanced_stats_soup, year):
        """Parse the last team a player playe dfor in the given season.

        Args:
          advanced_stats_soup: BeautifulSoup object for advanced stats table.
          year: Year for Player stats

        Returns:
          Team Id for last team the player played on in year
        """

        partial_objects_list = advanced_stats_soup.find_all('tr',attrs={'class':'partial_table'})
        teams_list = []
        # ITERATE THROUGH PARTIAL SEASONS
        try:
            for partial_object in partial_objects_list:
                # SAVE TEAMS ONLY FOR year SEASON
                object_for_this_season = partial_object.find('th',attrs={'data-stat':'year_ID', 'csk': re.compile(str(year))})
                if object_for_this_season:
                    # PARSE TEAM ID 
                    team_id = partial_object.find('td', attrs={'data-stat':'team_ID'}).get_text()
                    if team_id not in teams_list and team_id != '':
                        # ADD TO TEAMS LIST
                        teams_list.append(team_id)
            last_team = teams_list[-1]
            return last_team
        except:
            return 'TOT'

    def __add_icon_threshold_bools(self, type, year, stats_dict, homepage_soup):
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
                    is_qualified_for_icon = int(stats_dict[stat]) >= threshold
                    icon_threshold_bools[bool_key_name] = is_qualified_for_icon
        
        return icon_threshold_bools

    def __career_year_range(self, table_prefix, advanced_stats_soup):
        """Parse the player's first and last seasons in the MLB

        Args:
          table_prefix: String for whether player is batter or pitcher
          advanced_stats_soup: BeautifulSoup object for advanced stats table.

        Returns:
          Tuple of start and end years of career (ex: 2001, 2009)
        """
        try:
            full_element_prefix = '{}_standard.'.format(table_prefix)
            all_seasons_list = advanced_stats_soup.find_all('tr',attrs={'class':'full','id': re.compile(full_element_prefix)})
            first_season = all_seasons_list[0].find('th',attrs={'class':'left','data-stat': 'year_ID'} )
            last_season = all_seasons_list[-1].find('th',attrs={'class':'left','data-stat': 'year_ID'} )
            year_of_first_season = str(first_season["csk"])
            year_of_last_season = str(last_season["csk"])
            return year_of_first_season, year_of_last_season
        except:
            return 2300, 2300

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
            'award_summary': ','.join,
        }

        # FLATTEN MULTI YEAR STATS
        yearPd = pd.DataFrame.from_dict(yearly_stats_dict, orient='index')
        columns_to_remove = list(set(column_aggs.keys()) - set(yearPd.columns))
        if max(self.years) < 2015:
            columns_to_remove.append('sprint_speed')
        [column_aggs.pop(key) for key in columns_to_remove]
        avg_year = yearPd.groupby(by='name',as_index=False).agg(column_aggs)

        # CALCULATE RATES
        avg_year["batting_avg"] = round(avg_year['H'] / float(avg_year['AB']),3)
        avg_year["onbase_perc"] = round((avg_year['H'] + avg_year['BB'] + avg_year['HBP']) / float(avg_year['AB'] + avg_year['BB'] + avg_year['HBP'] + avg_year['SF']),3)
        avg_year["slugging_perc"] = round(avg_year['TB'] / avg_year['AB'],3)
        avg_year["onbase_plus_slugging"] = round(avg_year["onbase_perc"] + avg_year["slugging_perc"],3)

        avg_year_dict = avg_year.iloc[0].to_dict()

        # AGGREGATE DEFENSIVE METRICS
        avg_year_dict.update(self.__combine_multi_year_positions(yearly_stats_dict))

        return avg_year_dict

    def __combine_multi_year_positions(self, yearly_stats_dict):
        """Combine multiple year defensive positions and metrics
        into one master final dataset.

        Args:
          yearly_stats_dict: Dict of dicts per year.

        Returns:
          Flattened dictionary with combined stats
        """

        # OBJECT TO UPDATE
        defensive_fields_dict = {}
        positions_and_defense = {}
        positions_and_games_played = {}
        dWar_list = []

        # PARSE BY POSITION
        for year, stats in yearly_stats_dict.items():
            defensive_stats = {k:v for (k,v) in stats.items() if 'Position' in k or 'dWAR' in k}
            num_positions = int((len(defensive_stats.keys())-1) / 4)
            dWar_list.append(float(defensive_stats['dWAR']))
            for position_index in range(1, num_positions+1):
                position = defensive_stats['Position{}'.format(position_index)]
                # CHECK IF POSITION MATCHES PLAYER TYPE
                games_at_position = int(defensive_stats['gPosition{}'.format(position_index)])
                if position in positions_and_games_played.keys():
                    games_at_position += positions_and_games_played[position]
                positions_and_games_played[position] = games_at_position
                # IN-GAME RATING AT
                if position:
                    try:                                
                        year_defense_metrics = {
                            'drs': int(defensive_stats['drsPosition{}'.format(position_index)]),
                            'tzr': int(defensive_stats['tzPosition{}'.format(position_index)]),
                        }
                    except:
                        year_defense_metrics = {'drs': 0, 'tzr': 0}
                    if position in positions_and_defense.keys():
                        for key in ['drs', 'tzr']:
                            current_stat_list = positions_and_defense[position][key]
                            current_stat_list.append(year_defense_metrics[key])
                            positions_and_defense[position][key] = current_stat_list
                    else:
                        positions_and_defense[position] = { k:[v] for (k,v) in year_defense_metrics.items() }
        
        # RE-INDEX POSITIONAL STATS
        positions_and_games_played_sorted_tuple = sorted(positions_and_games_played.items(), key=operator.itemgetter(1), reverse=True)
        for index, (position, games_played) in enumerate(positions_and_games_played_sorted_tuple, 1):
            position_dict = {
                f"Position{index}": position,
                f"gPosition{index}": games_played,
                "dWar": statistics.median(dWar_list),
                f"drsPosition{index}": statistics.median(positions_and_defense[position]['drs']),
                f"tzPosition{index}": statistics.median(positions_and_defense[position]['tzr']),
            }
            defensive_fields_dict.update(position_dict)

        return defensive_fields_dict

    def __get_career_totals_row(self, div_id, soup_object):
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

    def __years_played_list(self, type, homepage_soup):
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

    def __team_multi_year(self, type, homepage_soup, years_filter_list=[]):
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
        team_w_most_games = sorted(teams_and_games_played.items(), key=operator.itemgetter(1), reverse=True)[0][0]
        return team_w_most_games

    def __get_stat_list_from_standard_table(self, type, homepage_soup, stat_key):
        """Parse the standard batting/pitching table to get a list of values for a given stat.

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

# ------------------------------------------------------------------------
# HELPER METHODS

    def __name_last_initial(self, name):
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

    def __convert_to_numeric(self, string_value):
        """Will convert a string to either int or float if able, otherwise return as string

        Args:
          string_value: String for attribute

        Returns:
          Converted attribute
        """
        # CONVERT TYPE IF INT OR FLOAT
        if string_value.isdigit():
            return int(string_value)
        elif string_value.replace('.','',1).isdigit() and string_value.count('.') < 2:
            return float(string_value)
        else:
            # RETURN ORIGINAL STRING
            return string_value