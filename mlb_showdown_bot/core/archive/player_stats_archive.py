import urllib
import cloudscraper
import traceback
from bs4 import BeautifulSoup
from pprint import pprint
from time import sleep
from datetime import date, datetime
from requests import exceptions as req_exc

from ..database.postgres_db import PostgresDB, PlayerArchive
from .player_stats import PlayerStats, PlayerType
from ..card.utils.shared_functions import convert_to_numeric
from ..card.showdown_player_card import ShowdownPlayerCard, StatsPeriod, StatsPeriodType, ShowdownImage, StatHighlightsType, PlayerType, Set as ShowdownSet


class PlayerStatsArchive:

# ------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------

    def __init__(self, years:list[int], is_snapshot:bool = False, player_ids: list[str] = None) -> None:
        """"""
        self.years = years
        self.is_snapshot = is_snapshot
        self.historical_date = date.today().strftime('%Y-%m-%d') if is_snapshot else None # FORMAT WILL BE YYYY-MM-DD (EX: "2023-09-01")
        self.two_way_bref_ids = ['ohtansh01','sudhowi01','mercewi01','dunnja01','howelha01','hickmch01',]
        self.player_list: list[PlayerStats] = []
        self.player_ids = player_ids

# ------------------------------------------------------------------------
# PLAYER LIST GENERATION
# ------------------------------------------------------------------------

    def generate_player_list(self, delay_between_years:float = 2.5, publish_to_postgres:bool=False, env: str = "dev") -> None:
        """Query baseball reference to get player list for each year requested.
        Stores final output to player_list class attribute as list of dictionaries.

        Args:
          None

        Returns:
          None
        """

        if publish_to_postgres:
            # CREATE DATABASE TABLE
            is_prod = env.lower() == 'prod'
            db = PostgresDB(is_archive=is_prod)
            db.create_player_season_stats_table()
            db_cursor = db.connection.cursor()

        final_player_data_list = []
        num_years = len(self.years)
        for year in self.years:
            print(f" -- STARTING {year} --")
            year_player_stats_list = []
            for type in PlayerType:
                
                # PULL ALL PLAYERS IN SEASON FOR TYPE
                all_players_url = f'https://www.baseball-reference.com/leagues/majors/{year}-standard-{type.bref_standard_page_name}.shtml'
                all_players_soup = self.__soup_for_url(url=all_players_url, is_baseball_ref_page=True)
                standard_table = all_players_soup.find('table', attrs={'id':f'players_standard_{type.bref_standard_page_name}'})
                all_player_rows = standard_table.find_all('tr')

                if len(all_player_rows) == 0:
                    print(f"WARNING: NO PLAYERS FOUND FOR {year} {type.value}")
                    continue

                # PARSE PLAYER DATA
                player_stats_list: list[PlayerStats] = []
                player_team_lists_dict: dict[str, dict[str: int]] = {}
                players_with_mlb_total_row: list[str] = []
                bref_ids_hitters = [player_data.bref_id for player_data in year_player_stats_list]
                for player_data_soup in all_player_rows:

                    player_stats = self.__convert_player_statline_soup_to_stats_object(player_soup_row=player_data_soup, player_type=type, year=year)
                    
                    if player_stats is None:
                        continue

                    if player_stats.name is None:
                        continue

                    # SETUP COMBINATION OF MULTI-TEAM RECORDS FOR SAME PLAYER
                    if player_stats.is_single_team_id:
                        current_player_team_dict = player_team_lists_dict.get(player_stats.bref_id, {})
                        current_player_team_dict[player_stats.team_id] = player_stats.g
                        player_team_lists_dict[player_stats.bref_id] = current_player_team_dict

                    # SKIP OUT OF POSITION PLAYERS
                    if player_stats.is_out_of_position_for_type(type=type, hitter_bref_ids=bref_ids_hitters):
                        continue

                    # FLAG IF RECORD IS PLAYER TOTAL FOR MLB LEAGUE.
                    # HELPS REMOVE NL/AL ONLY ROWS DOWNSTREAM
                    if not player_stats.is_single_team_id and player_stats.is_multi_league_id:
                        players_with_mlb_total_row.append(player_stats.bref_id)

                    player_stats_list.append(player_stats)

                # ERROR IF NO TEAM LISTS WERE PRODUCED ABOVE
                if len(player_team_lists_dict) == 0:
                    raise ValueError(f"ERROR - NO PLAYER TEAM LISTS WERE FORMED FOR {year} {type.value}")

                # UPDATE TEAM FOR PLAYER'S TRADED MID SEASON
                updated_player_stats_list = []
                skipped_player_list: list[PlayerStats] = []
                for player_stats in player_stats_list:

                    # LOAD TEAM LIST
                    player_teams_played_for_dict = player_team_lists_dict.get(player_stats.bref_id, None)
                    if player_teams_played_for_dict is None:
                        raise ValueError(f"ERROR - PLAYER {player_stats.name} DOES NOT HAVE ANY TEAMS")
                    is_player_multi_team = len(player_teams_played_for_dict) > 1
                    player_stats.team_games_played_dict = player_teams_played_for_dict
                    
                    # SKIP PARTIAL PLAYER SEASONS
                    is_single_team_in_multi_team_season = (player_stats.is_single_team_id and is_player_multi_team)
                    is_non_mlb_total = not player_stats.is_single_team_id and (not player_stats.is_multi_league_id if player_stats.bref_id in players_with_mlb_total_row else False)
                    if is_single_team_in_multi_team_season or is_non_mlb_total:
                        skipped_player_list.append(player_stats)
                        continue
                    
                    # SKIP PLAYER IF THEY DON'T MEET PA/IP REQUIREMENT
                    if not player_stats.meets_minimum_pa_or_ip_requirements:
                        skipped_player_list.append(player_stats)
                        continue

                    # ASSIGN PLAYER THE LAST TEAM THEY PLAYED FOR
                    player_team_list = list(player_teams_played_for_dict.keys())
                    player_stats.team_id = player_team_list[-1]
                    player_stats.team_id_list = player_team_list
                    
                    updated_player_stats_list.append(player_stats)
                    if publish_to_postgres:
                        print(f" UPLOADING {player_stats.name:<30}", end="\r")
                        db.upsert_player_season_stats_row(
                            cursor=db_cursor, 
                            data=player_stats.as_dict(convert_stats_to_json=True), 
                            conflict_strategy="update_all_exclude_stats"
                        )
                        player_stats.modified_date = datetime.now()

                if len(updated_player_stats_list) == 0:
                    print(f"WARNING: NO PLAYERS ELIGIBLE FOR {year} {type.value}")

                year_player_stats_list += updated_player_stats_list
                print(f"ADDED {len(updated_player_stats_list)} PLAYERS FOR {year} {type.value}")
                print(f"SKIPPED {len(skipped_player_list)} PLAYERS FOR {year} {type.value}")

            final_player_data_list += year_player_stats_list
            if num_years > 1:
                sleep(delay_between_years)
        
        self.player_list: list[PlayerStats] = final_player_data_list
        self.player_list.sort(key=lambda x: (x.war or 0, x.g or 0), reverse=True) # WILL PRIORITIZE PLAYERS WITH MOST WINS ABOVE REPLACEMENT

        if publish_to_postgres:
            # CLOSE CONNECTION
            db.close_connection()

    def __convert_player_statline_soup_to_stats_object(self, player_soup_row:BeautifulSoup, player_type: PlayerType, year:int) -> PlayerStats:
        """Convert Beautiful Soup for player to stats class

        Args:
          player_soup_row: BeautifulSoup table object a player's overall statline.
          player_type: HITTER or PITCHER represented as an Enum.
          year: Season of player data.

        Returns:
          Player Stats object
        """
        
        # PARSE ALL COLUMNS IN PLAYER'S DATA ROW
        initial_player_dict = {}
        columns = player_soup_row.find_all('td')
        for column_data in columns:
            stat_category: str = column_data['data-stat']

            # IN BATTERS PAGE ALL STATS ARE PREFIXED WITH 'b_', FOR PITCHERS IT'S 'p_'
            prefix = 'b_' if player_type == PlayerType.HITTER else 'p_'
            stat_category = stat_category.replace(prefix,'') if stat_category.startswith(prefix) else stat_category
            match stat_category:
                case 'games': stat_category = 'g'
                case 'team_name_abbr': stat_category = 'team_ID'
                case 'comp_name_abbr': stat_category = 'lg_ID'
                case 'doubles': stat_category = '2b'
                case 'triples': stat_category = '3b'
                case 'p_war' | 'b_war': stat_category = 'war'

            # PARSE BREF ID AND NAME 
            if stat_category in ['player', 'name_display']:
                # BREF ID
                bref_id = column_data.get('data-append-csv', None)
                if bref_id is None:
                    return None
                initial_player_dict['bref_id'] = bref_id
                # NAME
                player_name_hyperlink = column_data.find('a')
                player_name = player_name_hyperlink.get_text().replace(u'\xa0', u' ')
                player_name = player_name.encode('latin1').decode('utf-8')
                initial_player_dict['name'] = player_name

            # CONVERT TO NUMERIC IF NECESSARY
            stat = column_data.get_text().replace(u'\xa0', u' ')
            stat = convert_to_numeric(stat)
            if stat_category == 'IBB' and stat == '':
                stat = 0
            initial_player_dict[stat_category.lower()]= stat

        # CREATE PLAYER STATS OBJECT
        player_stats = PlayerStats(year=year, type=player_type, data=initial_player_dict, two_way_players_list=self.two_way_bref_ids, historical_date=self.historical_date)

        return player_stats

# ------------------------------------------------------------------------
# RUNNING BASEBALL REFERENCE / SAVANT SCRAPER
# ------------------------------------------------------------------------
    
    @property
    def is_player_list_empty(self) -> bool:
        return len(self.player_list) == 0

    def scrape_stats_for_player_list(self, delay:float = 10.0, publish_to_postgres:bool=True, env: str = "dev", limit:int=None, exclude_records_with_stats:bool=True, modified_start_date:str = None, modified_end_date:str = None, player_id_list:list[str] = None) -> None:
        """Using the class player_list array, iterrate through players and scrape bref data.

        Args:
            delay: Delay between each player's scrape.
            publish_to_postgres: Flag to publish data to postgres.
            env: Environment to run in (dev, prod).
            limit: Limit for how many players can be run.
            exclude_records_with_stats: Flag to exclude records with stats.
            modified_start_date: Limit to only records modified after this date.
            modified_end_date: Limit to only records modified before this date.

        Returns:
          None
        """

        if publish_to_postgres:
            # CREATE DATABASE TABLE
            is_prod = env.lower() == 'prod'
            db = PostgresDB(is_archive=is_prod)
            db.create_player_season_stats_table()
            db_cursor = db.connection.cursor()

            # POPULATE PLAYER STATS LIST FROM THE DATABASE IF IT'S EMPTY
            if self.is_player_list_empty:
                self.fill_player_stats_from_archive(db=db, exclude_records_with_stats=exclude_records_with_stats, modified_start_date=modified_start_date, modified_end_date=modified_end_date, player_id_list=player_id_list)
            else:
                self.player_list = [
                    player for player in self.player_list 
                    if not (
                        (exclude_records_with_stats and player.stats and len(player.stats) > 0)
                        or (modified_start_date and player.modified_date and player.modified_date < datetime.fromisoformat(modified_start_date))
                        or (modified_end_date and player.modified_date and player.modified_date > datetime.fromisoformat(modified_end_date))
                        or (player_id_list and player.bref_id not in player_id_list)
                    )
                ]

        # SORT BY bWAR DESC
        self.player_list.sort(key=lambda x: (x.war or 0, x.g or 0), reverse=True) # WILL PRIORITIZE PLAYERS WITH MOST WINS ABOVE REPLACEMENT

        # SCRAPE STATS AND INSERT/UPDATE DB RECORDS
        total_players = min(len(self.player_list), limit) if limit else len(self.player_list)
        for index, player in enumerate(self.player_list, start=1):

            try:

                # SETUP TIME ESTIMATE
                est_time_remaining_seconds = (total_players - index) * (delay + 2.0) # 2.0 IS FOR SLEEP MECHANISMS WITHIN BREF CLASS
                est_time_remaining_mins = round(est_time_remaining_seconds / 60.0, 2)
                est_time_remaining_hours = round(est_time_remaining_mins / 60.0, 2)
                time_unit = "HOURS" if est_time_remaining_mins > 120 else "MINS"
                time_value = est_time_remaining_hours if time_unit == 'HOURS' else est_time_remaining_mins

                print(f"  {index}/{total_players}: {player.name: <20} ({time_value} {time_unit} LEFT)")
                player.scrape_stats_data()
                if publish_to_postgres:
                    db.upsert_player_season_stats_row(cursor=db_cursor, data=player.as_dict(convert_stats_to_json=True), conflict_strategy="update_stats_only")
                if limit:
                    if index >= limit:
                        break
                
                sleep(delay)

            except Exception as e:
                print(f"ERROR PROCESSING PLAYER {player.name} {player.year} - {e}")
                sleep(delay)

        if publish_to_postgres:
            # CLOSE CONNECTION
            db.close_connection()

    def fill_player_stats_from_archive(self, db: PostgresDB, exclude_records_with_stats:bool=False, modified_start_date: str = None, modified_end_date: str = None, player_id_list: list[str] = None, ignore_minimums: bool = False) -> None:
        """Fill player stats list from archive database.
        
        Args:
            db: PostgresDB object.
            exclude_records_with_stats: Flag to exclude records with stats.
            modified_start_date: Limit to only records modified after this date.
            modified_end_date: Limit to only records modified before this date.
            player_id_list: Limit to only records for these player IDs.
            ignore_minimums: Flag to ignore minimum PA/IP when filling player stats.
        Returns:
            None
        """

        filters: list[tuple[str, list]] = []
        if not ignore_minimums:
            filters.append(('(pa >= 35 or ip >= 15)', []))

        if player_id_list:
            filters.append(('bref_id', player_id_list))

        player_archive_list: list[PlayerArchive] = db.fetch_all_stats_from_archive(
            year_list=self.years, 
            exclude_records_with_stats=exclude_records_with_stats, 
            historical_date=self.historical_date, 
            modified_start_date=modified_start_date, 
            modified_end_date=modified_end_date,
            filters=filters
        )
        for player_archive in player_archive_list:
            player_archive_data = player_archive.__dict__
            player_stats = PlayerStats(year=player_archive.year, type=PlayerType(player_archive.player_type), data=player_archive_data, two_way_players_list=[], historical_date=self.historical_date)
            for key, value in player_archive_data.items():
                if key == 'player_type':
                    continue
                setattr(player_stats, key, value)
            self.player_list.append(player_stats)


# ------------------------------------------------------------------------
# CONVERTING TO SHOWDOWN CARDS
# ------------------------------------------------------------------------

    def generate_showdown_player_cards(self, publish_to_postgres:bool=True, env: str = "dev", refresh_explore: bool=True, sets: list[ShowdownSet] = None, ignore_minimums: bool = False, player_id_list: list[str] = None) -> None:
        """Using the class player_list
        
        Args:
            publish_to_postgres: Flag to publish data to postgres.
            refresh_explore: Flag to refresh explore views after upload.
            sets: List of Showdown Sets to generate cards for. If None, generates for all sets.
            ignore_minimums: Flag to ignore minimum PA/IP when generating cards.
            player_id_list: List of player IDs to generate cards for. If None, generates for all players.
        Returns:
            None
        """

        # DEFAULT SETS TO ALL IF NONE PROVIDED
        if sets is None:
            sets = [s for s in ShowdownSet]

        # FETCH PLAYER DATA FROM ARCHIVE
        if publish_to_postgres:
            # CREATE DATABASE TABLE
            is_prod = env.lower() == 'prod'
            db = PostgresDB(is_archive=is_prod)

            # POPULATE PLAYER STATS LIST FROM THE DATABASE IF IT'S EMPTY
            if self.is_player_list_empty:
                self.fill_player_stats_from_archive(db=db, ignore_minimums=ignore_minimums, player_id_list=player_id_list)

        print("CONVERTING TO SHOWDOWN CARDS...")
        showdown_cards: list[ShowdownPlayerCard] = []
        for set in sets:
            print(f'\nSET: {set}')
            total_players = len(self.player_list)
            for index, player in enumerate(self.player_list, 1):
                type_override_raw = player.player_type_override
                type_override = PlayerType.PITCHER if type_override_raw else None
                name = player.name
                year = str(player.year)
                stats = player.stats
                set = set

                stats_period = StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=year)
                image = ShowdownImage(stat_highlights_type=StatHighlightsType.ALL)

                if player.bref_id in ['howelha01', 'dunnja01','sudhowi01','mercewi01'] and type_override_raw == '(pitcher)':
                    continue
                
                # SKIP PLAYERS WITH 0 PA
                if stats.get('PA', 0) == 0:
                    continue

                print(f"  {index}/{total_players}: {name: <30}", end="\r")
                try:
                    showdown = ShowdownPlayerCard(
                        name=name, year=year, stats=stats, stats_period=stats_period,
                        set=set, player_type_override=type_override, print_to_cli=False,
                        image=image
                    )
                except Exception as e:
                    print(f"\nERROR CREATING SHOWDOWN CARD FOR {name} ({year}) - {e}")
                    continue
                
                showdown_cards.append(showdown)
            
        if len(showdown_cards) == 0:
            print("NO SHOWDOWN CARDS GENERATED.")
            return
        
        db.upload_to_card_data(showdown_cards=showdown_cards, batch_size=1000)

        if refresh_explore:
            db.refresh_explore_views()


# ------------------------------------------------------------------------
# PARSE DATA
# ------------------------------------------------------------------------

    def __soup_for_url(self, url:str, is_baseball_ref_page:bool=False) -> BeautifulSoup:
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
            AttributeError: Cannot find Baseball Ref Page for name/year combo.

        Returns:
          HTML string for URL request.
        """

        scraper = cloudscraper.create_scraper()
        
        # TIMEOUTS
        CONNECT_TO = 8
        READ_TO = 22

        try:
            html = scraper.get(url, timeout=(CONNECT_TO, READ_TO))
            html.raise_for_status()
        except req_exc.Timeout:
            # Bubble up a clear timeout error
            raise TimeoutError(f"Request timed out (> {CONNECT_TO + READ_TO}s): {url}")
        except req_exc.RequestException as e:
            # Other network errors
            raise RuntimeError(f"HTTP error for {url}: {e}") from e
        

        if html.status_code == 502:
            raise urllib.URLError('502 Bad Gateway')
        if html.status_code == 429:
            print("429 - TOO MANY REQUESTS")

        return html.text
    