
import pandas as pd
import requests
import re
import ast
import json
import string
from bs4 import BeautifulSoup
from pprint import pprint

class BaseballReferenceScraper:

# ------------------------------------------------------------------------
# INIT

    def __init__(self, name, year):

        self.name = name
        self.year = year
        self.baseball_ref_id = self.search_google_for_b_ref_id(name, year)
        self.first_initial = self.baseball_ref_id[:1]

# ------------------------------------------------------------------------
# SCRAPE WEBSITES

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
            raise AttributeError('Cannot Find BRef Page for {} in {}'.format(self.name,self.year))
          

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

        if html.status_code == 502:
        	raise URLError('502 Bad Gateway')

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

        stats_dict = {}
        # DEFENSE
        positional_fielding = self.positional_fielding(soup_for_homepage_stats)
        stats_dict.update(positional_fielding)

        # HAND / TYPE
        type = self.type(positional_fielding)
        stats_dict['type'] = type
        stats_dict['hand'] = self.hand(soup_for_homepage_stats, type)
        # HITTING / HITTING AGAINST
        advanced_stats = self.advanced_stats(type)
        stats_dict.update(advanced_stats)
        # SPEED
        stats_dict['sprint_speed'] = self.sprint_speed(self.name, self.year)
        # DERIVE 1B 
        stats_dict['1B'] = int(stats_dict['H']) - int(stats_dict['HR']) - int(stats_dict['3B']) - int(stats_dict['2B'])

        return stats_dict

    def positional_fielding(self, soup_for_homepage_stats):
        """Parse standard fielding metrics (tzr, games_played).

        Args:
          soup_for_homepage_stats: BeautifulSoup object with all stats on homepage.

        Returns:
          Dict with name, tzr, and games played per position.
        """

        fielding_metrics_by_position = soup_for_homepage_stats.find_all('tr', attrs = {'id': '{}:standard_fielding'.format(self.year)})

        all_positions = {}
        for index, position_info in enumerate(fielding_metrics_by_position, 1):
            # PARSE POSITION ATTRIBUTES
            position_name = position_info.find('td', attrs={'class':'left','data-stat':'pos'}).get_text()
            games_played = position_info.find('td',attrs={'class':'right','data-stat':'G'}).get_text()
            total_zone_object = position_info.find('td',attrs={'class':'right','data-stat':'tz_runs_total'})
            total_zone_rating = total_zone_object.get_text() if total_zone_object != None else 0
            # UPDATE POSITION DICTIONARY
            position_dict = {
                'Position{}'.format(index): position_name,
                'gPosition{}'.format(index): games_played if games_played != '' else 0,
                'tzPosition{}'.format(index): total_zone_rating
            }
            all_positions.update(position_dict)

        return all_positions

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

    def type(self, positional_fielding):
        """Guess Player Type (Pitcher or Hitter) based on games played at each position.

        Args:
          positional_fielding: Dict with positions, games_played, and tzr

        Raises:
          AttributeError: This Player Played 0 Games. Check Player Name and Year.

        Returns:
          Either 'Hitter' or 'Pitcher' string.
        """

        games_as_pitcher = 0
        games_as_hitter = 0
        positions = int(len(positional_fielding) / 3)
        # SPLIT GAMES BETWEEN TYPES
        for position_index in range(1, positions + 1):
            games = int(positional_fielding['gPosition{}'.format(position_index)])
            position = positional_fielding['Position{}'.format(position_index)]
            if position == 'P':
                games_as_pitcher += games
            else:
                games_as_hitter += games
        # COMPARE GAMES PLAYED IN BOTH TYPES
        if games_as_hitter + games_as_pitcher == 0:
            raise AttributeError('This Player Played 0 Games in {}. Check Player Name and Year'.format(self.year))
        elif games_as_pitcher < games_as_hitter:
            return "Hitter"
        else:
            return "Pitcher"

    def sprint_speed(self, name, year):
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
            is_player_match = self.name.split(' ')[0] in player_dict['name_display_last_first'] \
                              and self.name.split(' ')[1] in player_dict['name_display_last_first']
            if is_player_match:
                speed = float(player_dict['r_sprint_speed_top50percent_pretty'])
                return speed
        # IF NOT FOUND, RETURN LEAGUE AVG
        return 27

    def advanced_stats(self, type):
        """Parse advanced stats page from baseball reference.

        Standard and ratio stats. For Pitchers, uses batting against table.

        Args:
          type: Player is Pitcher or Hitter.

        Returns:
          Dict with standard and ratio statistics.
        """

        # SCRAPE ADVANCED STATS PAGE
        page_suffix = '-bat' if type == 'Hitter' else '-pitch'
        url_advanced_stats = 'https://www.baseball-reference.com/players/{}/{}{}.shtml'.format(self.first_initial, self.baseball_ref_id, page_suffix)
        soup_for_advanced_stats = self.__soup_for_url(url_advanced_stats, is_baseball_ref_page=True)

        table_prefix = 'batting' if type == 'Hitter' else 'pitching'

        standard_table_key = '{}_standard.{}'.format(table_prefix, self.year)
        standard_table = soup_for_advanced_stats.find('tr',attrs={'class':'full','id': standard_table_key})

        advanced_stats = {}
        # BATTING AGAINST (PITCHERS ONLY)
        if type == 'Pitcher':
            batting_against_table = soup_for_advanced_stats.find('tr',attrs={'class':'full','id': 'pitching_batting.{}'.format(self.year)})
            advanced_stats.update(self.__parse_batting_against(batting_against_table))

        # STANDARD STATS
        advanced_stats.update(self.__parse_standard_stats(type, standard_table))

        # RATIO STATS
        ratio_table_key = '{}_ratio.{}'.format(table_prefix,self.year)
        ratio_table = soup_for_advanced_stats.find('tr', attrs = {'class':'full','id': ratio_table_key})
        advanced_stats.update(self.__parse_ratio_stats(ratio_table))

        return advanced_stats

    def __parse_standard_stats(self, type, standard_table):
        """Parse standard batting table.

        Args:
          type: Player is Pitcher or Hitter.
          standard_table: BeautifulSoup table object with season hitting stats.

        Returns:
          Dict with standard hitting statistics.
        """

        standard_stats_dict = {}

        for category in standard_table:
            stat_category = category['data-stat']
            stat = category.get_text()
            if type == 'Pitcher':
                pitching_categories = ['earned_run_avg','GS','W','SV','IP','award_summary']
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
            batting_against_dict[stat_category]= stat

        return batting_against_dict

    def __parse_ratio_stats(self, ratio_table):
        """Parse out ratios (GB/AO, PU)

        Args:
          ratio_table: BeautifulSoup table object with ratios.

        Returns:
          Dict with ratio statistics.
        """

        if ratio_table is None:
            # DEFAULT TO 50 / 50 SPLIT
            gb_ao_ratio = 1.0
            pu_ratio = 0.5
        else:
            gb_ao_ratio = ratio_table.find('td',attrs={'class':'right','data-stat': 'go_ao_ratio'}).get_text()
            if int(self.year) > 1988:
                # PU RATIO DATA AVAILABLE AFTER 1988
                pu_ratio_raw = ratio_table.find('td',attrs={'class':'right','data-stat': 'infield_fb_perc'}).get_text()
                pu_ratio = int(pu_ratio_raw.replace('%','')) / 100.0
            else:
                pu_ratio = 0.5

        return {
            'GO/AO': gb_ao_ratio,
            'IF/FB': pu_ratio
        }

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