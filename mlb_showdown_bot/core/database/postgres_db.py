import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import AsIs
from psycopg2 import sql
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

# INTERNAL
from ..card.stats.stats_period import StatsPeriodType
from ..card.images import Edition
from ..card.sets import Era
from ..card.utils.shared_functions import convert_year_string_to_list

class PlayerArchive(BaseModel):
    id: str
    year: int
    bref_id: str
    historical_date: Optional[str]
    name: str
    player_type: str
    player_type_override: Optional[str]
    is_two_way: bool = False
    primary_positions: list[str]
    secondary_positions: list[str]
    g: int
    gs: int
    pa: Optional[int]
    ip: Optional[float]
    lg_id: str
    team_id: str
    team_id_list: list[str]
    team_games_played_dict: dict
    team_override: Optional[str]
    created_date: datetime
    modified_date: datetime
    stats: dict

    @property
    def player_subtype(self) -> str:
        if self.player_type == 'HITTER':
            return 'POSITION_PLAYER'

        games_started_vs_total = round(self.gs / self.g, 4) if self.g > 0 else 0
        if games_started_vs_total >= 0.5:
            return 'STARTING_PITCHER'
        else:
            return 'RELIEF_PITCHER'

class PostgresDB:

# ------------------------------------------------------------------------
# INITS AND CONNECTION
# ------------------------------------------------------------------------

    def __init__(self, skip_connection:bool = False, is_archive:bool = False) -> None:
        self.connection = None
        self.env_var_name = 'DATABASE_URL_ARCHIVE' if is_archive else 'DATABASE_URL'
        if not skip_connection:
            self.connect()
        
    def connect(self) -> None:
        """Connect to a postgres database. Connection is stored to the class as 'connection'.
        If no environment variable for DATABASE_URL exists, None is stored.
        
        """
        DATABASE_URL = os.getenv(self.env_var_name)

        try:
            self.connection = psycopg2.connect(DATABASE_URL, sslmode='require')
            self.connection.autocommit = True
        except Exception as e:
            self.connection = None

    def close_connection(self) -> None:
        """Close the connection if it exists"""
        if self.connection:
            self.connection.close()

# ------------------------------------------------------------------------
# CHECK FOR STATS IN ARCHIVE
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
# QUERIES
# ------------------------------------------------------------------------

    def execute_query(self, query:sql.SQL, filter_values:tuple) -> list[dict]:
        """Execute a query and transform data to list of dictionaries.
        Keys represent field names, values are the rows from the database.
        
        Args:
          query: psycopg2 SQL object
          filter_value: Tuple of value(s) to filter by
        
        Returns:
          List of column: row_value dictionaries. If no results or no connection, empty dict will be returned.
        """

        # RETURN EMPTY LIST IF NO CONNECTION
        if self.connection is None:
            return []
        
        db_cursor = self.connection.cursor(cursor_factory=RealDictCursor)

        # PRINT QUERY AND FILTER VALUES FOR DEBUGGING
        # print(db_cursor.mogrify(query, filter_values).decode())

        try:
            db_cursor.execute(query, filter_values)
        except:
            return []
        output = [dict(row) for row in db_cursor.fetchall()]

        return output
    
    def fetch_player_stats_from_archive(self, year:str, bref_id:str, team_override:str = None, type_override:str = None, historical_date:str = None, stats_period_type:StatsPeriodType = StatsPeriodType.REGULAR_SEASON) -> tuple[PlayerArchive, float]:
        """Query the stats_archive table for a particular player's data from a single year
        
        Args:
          year: Year input by the user. Showdown archive does not support multi-year.
          bref_id: Unique ID for the player defined by bref.
          team_override: User override for filtering to a specific team. (ex: Max Scherzer (TEX))
          type_override: User override for specifing player type (ex: Shoehi Ohtani (Pitcher))
          split: Split name (if applicable)

        Returns:
          Tuple:
            Dict of player's real stats
            Execution time
        """

        start_time = datetime.now()
        default_return_tuple = (None, 0)

        # SUPPORTS SINGLE YEAR ONLY
        # ONLY VALID INTEGER YEARS
        try:
            year_int = int(year)
        except Exception as e:
            year_int = None
        
        if year_int is None or self.connection is None or stats_period_type == StatsPeriodType.SPLIT:
            return default_return_tuple
        
        if team_override:
            team_override = f"({team_override})"
        id_components = [str(year), bref_id, team_override, type_override, historical_date]
        concat_str_list = [component for component in id_components if component is not None]
        player_stats_id: str = "-".join(concat_str_list).lower()

        query = sql.SQL("SELECT * FROM {table} WHERE {column} = %s ORDER BY modified_date DESC;") \
                    .format(
                        table=sql.Identifier("stats_archive"),
                        column=sql.Identifier("id")
                    )
        query_results_list = self.execute_query(query=query, filter_values=(player_stats_id, ))
        
        if len(query_results_list) == 0:
            return default_return_tuple
        
        # IF EMPTY STATS, RETURN NONE INSTEAD
        first_result_dict = query_results_list[0]
        first_player_archive = PlayerArchive(**first_result_dict)
        if len(first_player_archive.stats) == 0:
            return default_return_tuple
        
        end_time = datetime.now()
        load_time = round((end_time - start_time).total_seconds(),2)
        
        return (first_player_archive, load_time)

    def fetch_all_player_year_stats_from_archive(self, bref_id:str, type_override:str = None) -> list[PlayerArchive]:
        """Query the stats_archive table for all player data for a given player
        
        Args:
            bref_id: Unique ID for the player defined by bref.
            type_override: User override for specifing player type (ex: Shoehi Ohtani (Pitcher))

        Returns:
            List of stats archive data where each element is a year.
        """

        # RETURN EMPTY LIST IF NO CONNECTION
        if self.connection is None:
            return []
        
        query = sql.SQL("SELECT * FROM {table} WHERE {column} = %s ORDER BY year;") \
                    .format(
                        table=sql.Identifier("stats_archive"),
                        column=sql.Identifier("bref_id")
                    )
        query_results_list = self.execute_query(query=query, filter_values=(bref_id, ))
        
        if len(query_results_list) == 0:
            return []
        
        return [PlayerArchive(**row) for row in query_results_list]

    def fetch_all_stats_from_archive(self, year_list: list[int], limit: int = None, order_by: str = None, exclude_records_with_stats: bool = True, historical_date: datetime = None, modified_start_date:str=None, modified_end_date:str=None) -> list[PlayerArchive]:
        """
        Fetch stats archive data for a list of years.

        Args:
          year_list: List of years as integers. Convert to tuple before the query executes.
          limit: Maximum number of rows to fetch. If None, fetch all rows.
          exclude_records_with_stats: Optionally filter the list for only rows where the stats column is empty. True by default.
          historical_date: Optional additional filter for snapshot date
          modified_start_date: Optional filter for modified_date start. Would include only records modified after this date.
          modified_end_date: Optional filter for modified_date end. Would include only records modified before this date.

        Returns:
          List of stats archive data.
        """

        column_names_to_filter = ["year", "historical_date"]
        values_to_filter = [tuple(year_list), historical_date]
        where_clause_values_equals_str = "=" if len(year_list) == 0 else "IN"
        conditions = [sql.SQL(' IS ' if col == "historical_date" and historical_date is None else f" {where_clause_values_equals_str} ").join([sql.Identifier(col), sql.Placeholder()]) for col in column_names_to_filter]

        if modified_start_date:
            conditions.append(sql.SQL(' >= ').join([sql.Identifier("modified_date"), sql.Placeholder()]))
            values_to_filter.append(modified_start_date)

        if modified_end_date:
            conditions.append(sql.SQL(' <= ').join([sql.Identifier("modified_date"), sql.Placeholder()]))
            values_to_filter.append(modified_end_date)
            
        where_clause = sql.SQL(' AND ').join(conditions)

        additional_conditions: list[sql.SQL] = []
        # ADD ORDER BY
        if order_by is not None:
            order_by_clause = sql.SQL('ORDER BY {} DESC').format(sql.SQL(order_by))
            additional_conditions.append(order_by_clause)

        # ADD LIMIT
        if limit is not None:
            limit_clause = sql.SQL('LIMIT %s')
            additional_conditions.append(limit_clause)
            values_to_filter.append(limit)
        
        if exclude_records_with_stats:
            query = sql.SQL("SELECT * FROM {table} WHERE jsonb_extract_path(stats, 'bref_id') IS NULL AND {where_clause} {order_by_filter}") \
                        .format(
                            table=sql.Identifier("stats_archive"),
                            where_clause=where_clause,
                            order_by_filter=sql.SQL(' ').join(additional_conditions)
                        )
        else:
            query = sql.SQL("SELECT * FROM {table} WHERE {where_clause} {order_by_filter}") \
                        .format(
                            table=sql.Identifier("stats_archive"),
                            where_clause=where_clause,
                            order_by_filter=sql.SQL(' ').join(additional_conditions)
                        )
        filters = tuple(values_to_filter)
        results = self.execute_query(query=query, filter_values=filters)

        return [PlayerArchive(**row) for row in results]
    
    def fetch_player_year_list_from_archive(self, players_stats_ids: list[str]) -> list[dict]:
        """Query the stats_archive table for all player data for given a list of player_stats_ids ('{bref_id}-{year}')
        
        Args:
          players_stats_ids: List of concatinated strings for bref_id and year

        Returns:
          List of stats archive data.
        """

        conditions = [sql.SQL(' IN ').join([sql.Identifier('id'), sql.Placeholder()])]
        query = sql.SQL("SELECT * FROM {table} WHERE {where_clause}") \
                    .format(
                        table=sql.Identifier("stats_archive"),
                        where_clause=sql.SQL(' AND ').join(conditions)
                    )
        filters = (tuple(players_stats_ids), )
        return self.execute_query(query=query, filter_values=filters)

    def fetch_random_player_stats_from_archive(self, year_input:str = None, era:str = None, edition:str = None) -> PlayerArchive:
        """Fetch a random player's stats from the database given certain parameters
        
        Args:
            year_input: Year(s) input by user. Will be used first over era if inputted by user.
            era: Era to filter by. Will be used if years is not inputted.
            edition: Edition to filter by. Each edition has a different filter applied:
                      - Cooperstown Collection: Only players in the Hall of Fame
                      - Super Season: Must either be an all star or meet bWAR requirement.
                      - All Star Game: Must be an all star.
                      - Rookie Season: Must be a rookie.

        Returns:
            PlayerArchive object with player stats.
        """

        # FILTER TO > 50 GAMES FOR HITTER, > 45 IP FOR PITCHER
        conditions:list[sql.SQL] = []
        values_to_filter:list = []

        year_list: list[int] = []
        if year_input:
            
            # CREATE RANGE FROM YEAR STRING
            year_list = convert_year_string_to_list(year_input) or []

        # YEAR LIST IS EMPTY, USE ERA TO SAMPLE YEARS
        if len(year_list) == 0 and era is not None:
            try:
                era_object = Era(era)
                year_list = era_object.year_range
            except:
                year_list = []
            
        if len(year_list) > 0:
            conditions.append(sql.SQL(" IN ").join([sql.Identifier("year"), sql.Placeholder()]))
            values_to_filter.append(tuple(year_list))
            
        where_clause = sql.SQL(' AND ').join(conditions) if len(conditions) > 0 else sql.SQL("TRUE")

        # DEFINE MINIMUMS
        hitter_games_minimum_statement =  sql.SQL(" and ").join([
            sql.SQL(" = ").join([sql.Identifier("player_type"), sql.Placeholder()]), # HITTER
            sql.SQL(" > ").join([sql.Identifier("g"), sql.Placeholder()]),           # AND GAMES > 50
        ])
        pitcher_ip_minimum_statement = sql.SQL(" and ").join([
            sql.SQL(" = ").join([sql.Identifier("player_type"), sql.Placeholder()]), # PITCHER
            sql.SQL(" > ").join([sql.Identifier("ip"), sql.Placeholder()]),           # AND IP > 45
        ])
        min_multiplier = 0.55 if 2020 in year_list else 1
        hitter_minimum_games = int(80 * min_multiplier)
        pitcher_minimum_ip = int(45 * min_multiplier)
        values_to_filter += ["HITTER", hitter_minimum_games, "PITCHER", pitcher_minimum_ip]

        # HANDLE SPECIAL CASES FOR EDITIONS
        match Edition(edition):
            case Edition.COOPERSTOWN_COLLECTION:
                # ONLY HALL OF FAME PLAYERS
                # HANDLED BY CHECKING FOR "is_hof" key = true inside of "stats" JSONB field
                edition_where_clause = sql.SQL("jsonb_extract_path(stats, 'is_hof')::BOOLEAN IS TRUE")
            case Edition.ALL_STAR_GAME:
                # MUST BE AN ALL STAR
                edition_where_clause = sql.SQL("jsonb_extract_path(stats, 'award_summary')::text like '%%AS%%'")
            case Edition.ROOKIE_SEASON:
                # MUST BE A ROOKIE
                edition_where_clause = sql.SQL("jsonb_extract_path(stats, 'is_rookie')::BOOLEAN IS TRUE")
            case Edition.SUPER_SEASON:
                # EITHER WAS AN ALL STAR OR MET bWAR REQUIREMENT
                bwar_min = int(5.0 * min_multiplier)
                edition_where_clause = sql.SQL(
                    "(case when length((stats->>'bWAR')) = 0 then 0.0 else (stats->>'bWAR')::float end) >= {} OR jsonb_extract_path(stats, 'award_summary')::text like '%%AS%%'"
                ).format(sql.Placeholder())
                values_to_filter.append(bwar_min)
            case _:
                edition_where_clause = sql.SQL("TRUE")
        
        query = sql.SQL("""
                        SELECT *
                        FROM {table} 
                        WHERE TRUE
                            AND ({where_clause})
                            AND ( ({hitter_games_minimum}) or ({pitcher_ip_minimum}) ) 
                            AND ({edition_where_clause}) 
                        ORDER BY RANDOM() LIMIT 1"""
                    ).format(
                        table=sql.Identifier("stats_archive"),
                        where_clause=where_clause,
                        hitter_games_minimum=hitter_games_minimum_statement,
                        pitcher_ip_minimum=pitcher_ip_minimum_statement,
                        edition_where_clause=edition_where_clause
                    )
        
        filters = tuple(values_to_filter)
        result_list = self.execute_query(query=query, filter_values=filters)

        if len(result_list) == 0: return None

        return PlayerArchive(**result_list[0])
    


# ------------------------------------------------------------------------
# TABLES
# ------------------------------------------------------------------------
#   
    def create_stats_archive_table(self, table_suffix:str='') -> None:
        """"""

        # RETURN IF NO CONNECTION
        if self.connection is None:
            return
        
        create_table_statement = f'''
            CREATE TABLE IF NOT EXISTS stats_archive{table_suffix}(
                id varchar(100) PRIMARY KEY,
                year int NOT NULL,
                bref_id VARCHAR(10) NOT NULL,
                historical_date TEXT,
                name VARCHAR(48) NOT NULL,
                player_type VARCHAR(10),
                player_type_override VARCHAR(10),
                is_two_way BOOLEAN,
                primary_positions TEXT [],
                secondary_positions TEXT [],
                g INT,
                gs INT,
                pa INT,
                ip FLOAT,
                lg_id VARCHAR(10),
                team_id VARCHAR(10),
                team_id_list TEXT [],
                team_games_played_dict JSONB,
                team_override VARCHAR(8),
                created_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                modified_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                stats JSONB
            );'''
        db_cursor = self.connection.cursor()
        try:
            db_cursor.execute(create_table_statement)
        except:
            return
		
    def upsert_stats_archive_row(self, cursor, data:dict, skip_upsert:bool = False) -> None:
        """Upsert record into stats archive. 
        Insert record if it does not exist, otherwise update the row's `stats` and `modified_date` values

        Args:
          cursor: psycopg Cursor object.
          data: data to store.
        
        """
        columns = data.keys()
        values = data.values()
        if skip_upsert:
            insert_statement = '''
                INSERT INTO STATS_ARCHIVE (%s) VALUES %s
                ON CONFLICT (id) DO NOTHING
            '''
        else:
            insert_statement = '''
                INSERT INTO STATS_ARCHIVE (%s) VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                (modified_date, stats) = (NOW(), EXCLUDED.stats)
            '''
        cursor.execute(insert_statement, (AsIs(','.join(columns)), tuple(values)))
        