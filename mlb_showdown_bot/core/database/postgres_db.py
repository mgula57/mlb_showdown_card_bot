import os
import psycopg2
import traceback
from unidecode import unidecode
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2 import extensions, extras
from psycopg2.extensions import AsIs
from psycopg2 import sql
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Any

# INTERNAL
from ..card.showdown_player_card import ShowdownPlayerCard, Team, PlayerType, Era, Edition, Position, StatsPeriodType, __version__
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
    war: Optional[float] = None
    lg_id: str
    team_id: str
    team_id_list: list[str]
    team_games_played_dict: dict
    team_override: Optional[str]
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    stats: dict
    stats_modified_date: Optional[datetime] = None

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

            # THIS WILL ENABLE NATURAL PASSING OF DICTS AS JSONB
            extensions.register_adapter(dict, extras.Json)

        except Exception as e:
            self.connection = None

    def close_connection(self) -> None:
        """Close the connection if it exists"""
        if self.connection:
            self.connection.close()

# ------------------------------------------------------------------------
# QUERIES
# ------------------------------------------------------------------------


    def execute_query(self, query:sql.SQL, filter_values:tuple=None) -> list[dict]:
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
        try:
            db_cursor.execute(query, filter_values)
            # print(db_cursor.mogrify(query, filter_values).decode())
        except:
            print(db_cursor.mogrify(query, filter_values).decode())
            return []
        output = [dict(row) for row in db_cursor.fetchall()]

        return output
    
    def fetch_player_stats_from_archive(self, year:str, bref_id:str, team_override:Team = None, type_override:PlayerType = None, historical_date:str = None, stats_period_type:StatsPeriodType = StatsPeriodType.REGULAR_SEASON) -> tuple[PlayerArchive, float]:
        """Query the stats_archive table for a particular player's data from a single year
        
        Args:
          year: Year input by the user. Showdown archive does not support multi-year.
          bref_id: Unique ID for the player defined by bref.
          team_override: User override for filtering to a specific team. (ex: Max Scherzer (TEX))
          type_override: User override for specifing player type (ex: Shohei Ohtani (Pitcher))
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
            team_override = f"({team_override.value})"
        if type_override:
            type_override = f"({type_override.value})"
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

    def fetch_all_player_year_stats_from_archive(self, bref_id:str, type_override:PlayerType = None) -> list[PlayerArchive]:
        """Query the stats_archive table for all player data for a given player
        
        Args:
            bref_id: Unique ID for the player defined by bref.
            type_override: User override for specifing player type (ex: Shohei Ohtani (Pitcher))

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

    def fetch_all_stats_from_archive(self, year_list: list[int], filters:list[tuple] = [], limit: int = None, order_by: str = None, exclude_records_with_stats: bool = True, historical_date: datetime = None, modified_start_date:str=None, modified_end_date:str=None) -> list[PlayerArchive]:
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
            conditions.append(sql.SQL(' >= ').join([sql.Identifier("stats_modified_date"), sql.Placeholder()]))
            values_to_filter.append(modified_start_date)

        if modified_end_date:
            conditions.append(sql.SQL(' <= ').join([sql.Identifier("stats_modified_date"), sql.Placeholder()]))
            values_to_filter.append(modified_end_date)

        for filter_tuple in filters:
            if len(filter_tuple) != 2:
                continue
            column_name, value = filter_tuple
            if value is None:
                continue
                
            # Handle list values with IN operator, single values with = operator
            if isinstance(value, list):
                if len(value) > 0:  # Only add condition if list is not empty
                    conditions.append(sql.SQL(' IN ').join([sql.Identifier(column_name), sql.Placeholder()]))
                    values_to_filter.append(tuple(value))  # Convert list to tuple for psycopg2
            else:
                conditions.append(sql.SQL(' = ').join([sql.Identifier(column_name), sql.Placeholder()]))
                values_to_filter.append(value)
            
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

    def fetch_current_season_player_data(self) -> list[dict]:
        """Fetch current season player data from the database."""

        if not self.connection:
            return None

        query = sql.SQL("""
            SELECT *
            FROM current_season_players
        """)

        result_list = self.execute_query(query=query)
        return result_list

# ------------------------------------------------------------------------
# EXPLORE
# ------------------------------------------------------------------------

    def fetch_card_data(self, filters: dict = {}) -> list[dict]:
        """Fetch all card data from the database with support for lists and min/max filtering."""

        if not self.connection:
            return None
        
        try:

            query = sql.SQL("""
                SELECT *
                FROM explore_data
                WHERE TRUE
            """)

            filter_values = []

            # Pop out sorting filters
            sort_by = str(filters.pop('sort_by', 'points')).lower()
            sort_direction = str(filters.pop('sort_direction', 'desc')).lower()

            # Pop out pagination and limit
            page = int(filters.pop('page', 1))
            limit = int(filters.pop('limit', 50))

            # Apply filters if any
            if filters and len(filters) > 0:
                filter_clauses = []
                
                for key, value in filters.items():
                    if value is None:
                        continue
                        
                    # Handle min/max filtering
                    if key.startswith('min_'):
                        field_name = key[4:]  # Remove 'min_' prefix
                        filter_clauses.append(sql.SQL("coalesce({field} >= %s, true)").format(
                            field=sql.Identifier(field_name)
                        ))
                        filter_values.append(value)
                        
                    elif key.startswith('max_'):
                        field_name = key[4:]  # Remove 'max_' prefix
                        filter_clauses.append(sql.SQL("{field} <= %s").format(
                            field=sql.Identifier(field_name)
                        ))
                        filter_values.append(value)

                    elif key == 'search':
                        # Handle search text filtering (ILIKE %value%)
                        filter_clauses.append(sql.SQL("{field} ILIKE %s").format(
                            field=sql.Identifier("name")
                        ))
                        filter_values.append(f"%{value}%")

                    elif key == 'is_multi_team':
                        # Handle multi-team filtering based on cardinality of team_id_list
                        if isinstance(value, list) and len(value) > 0:
                            multi_team_conditions = []
                            
                            for multi_team_value in value:
                                if multi_team_value.lower() == 'true':
                                    # Players with multiple teams (cardinality > 1)
                                    multi_team_conditions.append(sql.SQL("cardinality(team_id_list) > 1"))
                                elif multi_team_value.lower() == 'false':
                                    # Players with single team (cardinality = 1 or NULL/empty array)
                                    multi_team_conditions.append(sql.SQL("(cardinality(team_id_list) <= 1 OR team_id_list IS NULL)"))
                            
                            if multi_team_conditions:
                                # Use OR to combine conditions (show records matching any of the selected values)
                                filter_clauses.append(sql.SQL("({})").format(
                                    sql.SQL(" OR ").join(multi_team_conditions)
                                ))
                            
                    # Handle list filtering (IN clause)
                    elif isinstance(value, list) and len(value) > 0:
                        # For JSONB array fields, use @> operator to check if array contains any of the values
                        match key:
                            case 'positions':
                                # Check if any of the provided positions are in the player's positions
                                filter_clauses.append(sql.SQL("positions_list && %s"))
                                filter_values.append(value)
                            case 'icons':
                                # Check if any of the provided icons are in the player's icons
                                filter_clauses.append(sql.SQL("icons_list && %s"))
                                filter_values.append(value)
                            case 'include_small_sample_size':
                                # Only filter if array is ["false"]
                                if value == ["false"]:
                                    filter_clauses.append(sql.SQL("(case" \
                                        " when positions_list && ARRAY['STARTER'] then real_ip >= 75" \
                                        " when positions_list && ARRAY['RELIEVER', 'CLOSER'] then real_ip >= 30" \
                                        " else pa >= 250" \
                                    "end)"))
                            case _:
                                # Regular IN clause for non-array fields
                                placeholders = sql.SQL(", ").join([sql.Placeholder()] * len(value))
                                filter_clauses.append(sql.SQL("{field}::text IN ({placeholders})").format(
                                    field=sql.Identifier(key),
                                    placeholders=placeholders
                                ))
                                filter_values.extend(value)
                            
                    # Handle regular equality filtering
                    else:
                        filter_clauses.append(sql.SQL("{field} = %s").format(
                            field=sql.Identifier(key)
                        ))
                        filter_values.append(value)

                if filter_clauses:
                    query += sql.SQL(" AND ") + sql.SQL(" AND ").join(filter_clauses)

            # ADD SORTING
            if sort_direction not in ['asc', 'desc']:
                sort_direction = 'desc'

            # CHECK FOR JSONB USE CASES
            is_defensive_sort = 'positions_and_defense' in sort_by
            if is_defensive_sort:
                sort_by = sort_by.replace('positions_and_defense_', '').upper()
                # For 1B, 2B, 3B, SS we need to check both the position and the 'IF' key
                # For CF, LF/RF we need to check both the position and the 'OF' key
                check_if_key = sort_by in ['1B', '2B', '3B', 'SS']
                check_of_key = sort_by in ['CF', 'LF/RF']
                if check_if_key or check_of_key:
                    additional_key = 'IF' if check_if_key else 'OF'
                    final_sort = sql.SQL("""CASE 
                                                WHEN positions_and_defense ? %s THEN (positions_and_defense->>%s)::numeric 
                                                WHEN positions_and_defense ? %s THEN (positions_and_defense->>%s)::numeric 
                                                ELSE null 
                                            END {direction} NULLS LAST""").format(
                        direction=sql.SQL(sort_direction)
                    )
                    filter_values += [sort_by, sort_by, additional_key, additional_key]
                else:
                    final_sort = sql.SQL("""CASE WHEN positions_and_defense ? %s THEN (positions_and_defense->>%s)::numeric ELSE null END {direction} NULLS LAST""").format(
                        direction=sql.SQL(sort_direction)
                    )
                    filter_values += [sort_by, sort_by]

            else:
                final_sort = sql.SQL("{field} {direction} NULLS LAST").format(
                    field=sql.Identifier(sort_by),
                    direction=sql.SQL(sort_direction)
                )

            query += sql.SQL(" ORDER BY {}, points DESC, bref_id, year").format(final_sort)

            # ADD LIMIT AND PAGINATION
            if not isinstance(page, int) or page < 1:
                page = 1
            if not isinstance(limit, int) or limit < 1 or limit > 1000:
                limit = 50

            query += sql.SQL(" LIMIT %s OFFSET %s")
            filter_values.extend([limit, (page - 1) * limit])

            result_list = self.execute_query(query=query, filter_values=tuple(filter_values))
            return result_list
        except Exception as e:
            print("Error fetching card data:", e)
            traceback.print_exc()
            return []

    def fetch_team_data(self) -> list[dict]:
        """Fetch team data hierarchyfrom the database"""

        if not self.connection:
            return None
        
        query = sql.SQL("""
            SELECT  
                organization,
                league,
                team,
                min_year,
                max_year,
                cards
            FROM team_hierarchy
            ORDER BY team
        """)
        
        data = self.execute_query(query)
        return data


# ------------------------------------------------------------------------
# TABLES
# ------------------------------------------------------------------------

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
                stats JSONB,
                stats_modified_date timestamp without time zone DEFAULT now(),
                war double precision
            );'''
        db_cursor = self.connection.cursor()
        try:
            db_cursor.execute(create_table_statement)
        except:
            return


# ------------------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------------------

    def log_card_submission(self, card:ShowdownPlayerCard, user_inputs: dict[str: Any], additional_attributes: dict[str: Any]) -> str:
        """
        Store card submission data in the card_log table.

        Args:
            ShowdownPlayerCard: Card object to log.
            user_inputs: User inputs to log, including any additional attributes.
            additional_attributes: Additional attributes to log, if any.

        Returns:
            Error message if any, otherwise None.
        """

        if not self.connection:
            print("No database connection available for logging.")
            return 
        
        # Helper function to convert enum values to strings
        def convert_enum_values(obj):
            """Recursively convert enum values to their string representation"""
            if hasattr(obj, 'value'):  # It's an enum
                return obj.value
            elif isinstance(obj, dict):
                return {k: convert_enum_values(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enum_values(item) for item in obj]
            else:
                return obj
            
        user_inputs_converted = convert_enum_values(user_inputs)
            
        # BUILD CARD SUBMISSION OBJECT
        columns_not_on_card_object = [
            'error', 'error_for_user', 'scraper_load_time', 'historical_season_trends', 'in_season_trends'
        ]
        if card:
            # CARD IS POPULATED
            card_submission = {
                'name': card.name,
                'year': card.year, 
                'set': card.set.value, 
                'is_cooperstown': None,                                 # DEPRECATED
                'is_super_season': None,                                # DEPRECATED
                'img_url': card.image.source.url,
                'img_name': card.image.source.path, 
                'is_all_star_game': None,                               # DEPRECATED
                'expansion': card.image.expansion,
                'stats_offset': card.chart_version,
                'set_num': card.image.set_number,
                'is_holiday': None,                                     # DEPRECATED
                'is_dark_mode': card.image.is_dark_mode,
                'is_rookie_season': None,                               # DEPRECATED
                'is_variable_spd_00_01': card.is_variable_speed_00_01, 
                'is_random': None,                                      # DEPRECATED
                'is_automated_image': card.image.source.is_automated, 
                'is_foil': None,                                        # DEPRECATED
                'is_stats_loaded_from_library': False,                  # DEPRECATED
                'is_img_loaded_from_library': False,                    # DEPRECATED
                'add_year_container': card.image.show_year_text,
                'ignore_showdown_library': None,                        # DEPRECATED
                'set_year_plus_one': card.image.add_one_to_set_year,
                'edition': card.image.edition,
                'hide_team_logo': card.image.hide_team_logo,
                'date_override': card.date_override,
                'era': card.era.value if card.era else None, 
                'image_parallel': card.image.parallel.value if card.image.parallel else None, 
                'bref_id': card.bref_id, 
                'team': card.team.value, 
                'data_source': card.stats_period.source, 
                'image_source': card.image.source.type.value, 
                'card_load_time': card.load_time, 
                'is_secondary_color': card.image.use_secondary_color, 
                'nickname_index': card.image.nickname_index, 
                'period': card.stats_period.type.value if card.stats_period else None, 
                'period_start_date': card.stats_period.start_date if card.stats_period else None,
                'period_end_date': card.stats_period.end_date if card.stats_period else None,
                'period_split': card.stats_period.split if card.stats_period else None,
                'is_multi_colored': card.image.is_multi_colored if card.image else None,
                'stat_highlights_type': card.image.stat_highlights_type.value if card.image else None,
                'glow_multiplier': card.image.glow_multiplier if card.image else None,
            }
        else:
            # NO CARD GENERATED
            card_submission = {
                'name': user_inputs.get('name', None),
                'year': user_inputs.get('year', None),
                'set': user_inputs.get('set', None),
            }

        # ADD ADDITIONAL ATTRIBUTES
        for key, value in additional_attributes.items():
            if key in columns_not_on_card_object:
                card_submission[key] = value

        # ADD USER INPUTS AND VERSION
        card_submission['user_inputs'] = user_inputs_converted
        card_submission['version'] = __version__

        # INSERT INTO THE DATABASE
        column_list = list(card_submission.keys())
        columns = ', '.join(column_list)
        placeholders = ', '.join(['%s'] * len(column_list))
        values = list(card_submission.values())
        sql = f"INSERT INTO card_log ({columns}) VALUES ({placeholders})"
        try:
            with self.connection.cursor() as cur:
                cur.execute(sql, values)
                self.connection.commit()
        except Exception as error:
            traceback.print_exc()
            print(f"Error logging card submission to DB: {error}")
            self.connection.rollback()
            return None

    def upsert_stats_archive_row(self, cursor, data:dict, conflict_strategy:str = "do_nothing") -> None:
        """Upsert record into stats archive. 
        Insert record if it does not exist, otherwise update the row's `stats` and `modified_date` values

        Args:
          cursor: psycopg Cursor object.
          data: data to store.
          conflict_strategy: "do_nothing", "update_all_columns", "update_all_exclude_stats", "update_stats_only"
        
        Returns:
          None
        """
        columns = data.keys()
        values = data.values()
        match conflict_strategy:
            case "do_nothing":
                insert_statement = '''
                    INSERT INTO STATS_ARCHIVE (%s) VALUES %s
                    ON CONFLICT (id) DO NOTHING
                '''
            case "update_all_columns":
                insert_statement = '''
                    INSERT INTO STATS_ARCHIVE (%s) VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                    (
                        year, historical_date, name, 
                        player_type, player_type_override, is_two_way, 
                        primary_positions, secondary_positions, 
                        g, gs, pa, ip, war,
                        lg_id, team_id, team_id_list, team_games_played_dict, team_override, 
                        modified_date, stats, stats_modified_date
                    ) =
                    (
                        EXCLUDED.year, EXCLUDED.historical_date, EXCLUDED.name, 
                        EXCLUDED.player_type, EXCLUDED.player_type_override, EXCLUDED.is_two_way, 
                        EXCLUDED.primary_positions, EXCLUDED.secondary_positions, 
                        EXCLUDED.g, EXCLUDED.gs, EXCLUDED.pa, EXCLUDED.ip, EXCLUDED.war,
                        EXCLUDED.lg_id, EXCLUDED.team_id, EXCLUDED.team_id_list, EXCLUDED.team_games_played_dict, EXCLUDED.team_override, 
                        NOW(), EXCLUDED.stats, NOW()
                    )
                '''
            case "update_all_exclude_stats":
                insert_statement = '''
                    INSERT INTO STATS_ARCHIVE (%s) VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                    (
                        year, historical_date, name, 
                        player_type, player_type_override, is_two_way, 
                        primary_positions, secondary_positions, 
                        g, gs, pa, ip, war,
                        lg_id, team_id, team_id_list, team_games_played_dict, team_override, 
                        modified_date
                    ) =
                    (
                        EXCLUDED.year, EXCLUDED.historical_date, EXCLUDED.name, 
                        EXCLUDED.player_type, EXCLUDED.player_type_override, EXCLUDED.is_two_way, 
                        EXCLUDED.primary_positions, EXCLUDED.secondary_positions, 
                        EXCLUDED.g, EXCLUDED.gs, EXCLUDED.pa, EXCLUDED.ip, EXCLUDED.war,
                        EXCLUDED.lg_id, EXCLUDED.team_id, EXCLUDED.team_id_list, EXCLUDED.team_games_played_dict, EXCLUDED.team_override, 
                        NOW()
                    )
                '''
            case "update_stats_only":
                insert_statement = '''
                    INSERT INTO STATS_ARCHIVE (%s) VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                    (stats_modified_date, stats) = (NOW(), EXCLUDED.stats)
                '''

        cursor.execute(insert_statement, (AsIs(','.join(columns)), tuple(values)))
        
    def upload_to_card_data(self, showdown_cards: list[ShowdownPlayerCard], batch_size: int = 1000) -> None:
        """Upload showdown cards to PostgreSQL database
        
        Args:
            showdown_cards: List of ShowdownPlayerCard objects to upload.
            batch_size: Number of cards to upload in each batch.
        
        Returns:
            None
        """
        
        print("UPLOADING TO DATABASE...")
        if self.connection is None:
            print("ERROR: NO CONNECTION TO DB")
            return
        
        cursor = self.connection.cursor()
        
        try:
            
            # Process cards in batches
            total_cards = len(showdown_cards)
            for i in range(0, total_cards, batch_size):
                batch = showdown_cards[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_cards + batch_size - 1) // batch_size
                
                print(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} cards)...")
                
                # Prepare batch data
                batch_data = []
                for showdown in batch:
                    card_data = showdown.as_json()
                    
                    # Clean up the data for JSON storage
                    id_fields = [field for field in [showdown.year, showdown.bref_id, f'({showdown.player_type_override.value})' if showdown.player_type_override else None] if field is not None]
                    card_data['player_id'] = "-".join(id_fields).lower()
                    card_data['name'] = unidecode(card_data['name'])

                    batch_data.append((card_data['player_id'], showdown.set.value, card_data))

                # Insert batch
                insert_query = """
                    INSERT INTO card_data (player_id, showdown_set, card_data) 
                    VALUES %s
                """

                execute_values(
                    cursor, 
                    insert_query, 
                    batch_data,
                    template=None,
                    page_size=batch_size
                )
                
                self.connection.commit()
                print(f"  ✓ Uploaded {len(batch)} cards")
            
            print(f"✓ Successfully uploaded {total_cards} showdown cards to database")
            
        except Exception as e:
            print(f"ERROR uploading to database: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()