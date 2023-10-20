import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import AsIs
from psycopg2 import sql
from datetime import datetime

class PostgresDB:

# ------------------------------------------------------------------------
# INITS AND CONNECTION
# ------------------------------------------------------------------------

    def __init__(self, skip_connection:bool = False) -> None:
        self.connection = None
        if not skip_connection:
            self.connect()
        
    def connect(self) -> None:
        """Connect to a postgres database. Connection is stored to the class as 'connection'.
        If no environment variable for DATABASE_URL exists, None is stored.
        
        """
        DATABASE_URL = os.getenv('DATABASE_URL')

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
        try:
            db_cursor.execute(query, filter_values)
        except:
            return []
        output = [dict(row) for row in db_cursor.fetchall()]

        return output
    
    def fetch_player_stats_from_archive(self, year:str, bref_id:str, team_override:str = None, type_override:str = None, historical_date:str = None) -> tuple[dict, float]:
        """Query the stats_archive table for a particular player's data from a single year
        
        Args:
          year: Year input by the user. Showdown archive does not support multi-year.
          bref_id: Unique ID for the player defined by bref.
          team_override: User override for filtering to a specific team. (ex: Max Scherzer (TEX))
          type_override: User override for specifing player type (ex: Shoehi Ohtani (Pitcher))

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
            year_int = default_return_tuple
        
        if year_int is None or self.connection is None:
            return default_return_tuple
        
        if team_override:
            team_override = f"({team_override})"
        id_components = [str(year), bref_id, team_override, type_override, historical_date]
        concat_str_list = [component for component in id_components if component is not None]
        player_stats_id: str = "-".join(concat_str_list).lower()

        query = sql.SQL("SELECT stats FROM {table} WHERE {column} = %s ORDER BY modified_date DESC;") \
                    .format(
                        table=sql.Identifier("stats_archive"),
                        column=sql.Identifier("id")
                    )
        query_results_list = self.execute_query(query=query, filter_values=(player_stats_id, ))
        
        if len(query_results_list) == 0:
            return default_return_tuple
        
        # IF EMPTY DICT, RETURN NONE INSTEAD
        first_result_dict = query_results_list[0].get('stats', {})
        if len(first_result_dict) == 0:
            return default_return_tuple
        
        end_time = datetime.now()
        load_time = round((end_time - start_time).total_seconds(),2)
        
        return (first_result_dict, load_time)

    def fetch_all_stats_from_archive(self, year_list:list[int], exclude_records_with_stats:bool = True, historical_date:str = None) -> list[dict]:
        """Query the stats_archive table for all player data for a list of years. 
        Optionally filter the list for only rows where the stats column is empty.
        
        Args:
          year_list: List of years as integers. Convert to tuple before the query executes.
          exclude_records_with_stats: Optionally filter the list for only rows where the stats column is empty. True by default.
          historical_date: Optional additional filter for snapshot date

        Returns:
          List of stats archive data.
        """

        column_names_to_filter = ["year", "historical_date"]
        values_to_filter = [tuple([str(yr) for yr in year_list]), historical_date]
        conditions = [sql.SQL(' IS ' if col == "historical_date" and historical_date is None else " = ").join([sql.Identifier(col), sql.Placeholder()]) for col in column_names_to_filter]
        if exclude_records_with_stats:
            query = sql.SQL("SELECT * FROM {table} WHERE jsonb_extract_path(stats, 'bref_id') IS NULL AND {where_clause}") \
                        .format(
                            table=sql.Identifier("stats_archive"),
                            where_clause=sql.SQL(' AND ').join(conditions)
                        )
        else:
            query = sql.SQL("SELECT * FROM {table} WHERE {where_clause}") \
                        .format(
                            table=sql.Identifier("stats_archive"),
                            where_clause=sql.SQL(' AND ').join(conditions)
                        )
        filters = tuple(values_to_filter)
        return self.execute_query(query=query, filter_values=filters)

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
        