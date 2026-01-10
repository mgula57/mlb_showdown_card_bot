import json
import os
import psycopg2
import traceback
from unidecode import unidecode
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2 import extensions, extras
from psycopg2.extensions import AsIs
from psycopg2 import sql
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from enum import Enum

# INTERNAL
from ..card.showdown_player_card import ShowdownPlayerCard, Team, PlayerType, Era, Edition, Set, StatsPeriodType, __version__
from ..card.utils.shared_functions import convert_year_string_to_list
from ..shared.google_drive import fetch_image_metadata


# ----------------------------------------------------------------
# MARK: - DATA MODELS
# ----------------------------------------------------------------

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


class ImageMatchType(str, Enum):
    """Types of image matches available"""
    EXACT = "exact"
    TEAM_MATCH = "team match"
    YEAR_MATCH = "year match"
    NO_MATCH = "no match"

class ExploreDataRecord(BaseModel):
    """Pydantic model for records from the explore_data materialized view"""
    
    # Base identifiers
    id: str
    year: int
    bref_id: str
    name: str
    
    # Player type information
    player_type: str
    player_type_override: Optional[str] = None
    is_two_way: bool = False
    
    # Position information
    primary_positions: List[str]
    secondary_positions: List[str]
    positions_list: List[str]
    
    # Basic stats
    g: int = Field(description="Games played")
    gs: int = Field(description="Games started")
    pa: Optional[int] = Field(None, description="Plate appearances")
    real_ip: Optional[float] = Field(None, description="Innings pitched")
    
    # League and team information
    lg_id: str = Field(description="League ID")
    team_id: str = Field(description="Team ID")
    team_id_list: List[str] = Field(description="List of teams if multi-team player")
    team_games_played_dict: Dict[str, Any] = Field(description="Games played by team")
    team_override: Optional[str] = None
    
    # Card data
    card_data: ShowdownPlayerCard = Field(description="Raw card data as stored")
    showdown_set: str = Field(description="Showdown set (e.g., '2001', 'CLASSIC')")
    showdown_bot_version: Optional[str] = Field(None, description="Version of showdown bot used")
    
    # Parsed card attributes
    points: Optional[int] = Field(None, description="Card point value")
    nationality: Optional[str] = None
    organization: Optional[str] = Field(None, description="MLB, NGL, etc.")
    league: Optional[str] = Field(None, description="AL, NL, etc.")
    team: Optional[str] = Field(None, description="Team from team hierarchy")
    
    # Metadata
    positions_and_defense: Optional[Dict[str, Any]] = Field(None, description="Position and defense ratings")
    positions_and_defense_string: Optional[str] = Field(None, description="Formatted positions string")
    ip: Optional[int] = Field(None, description="Innings pitched (card value)")
    speed: Optional[int] = Field(None, description="Speed rating")
    hand: Optional[str] = Field(None, description="Handedness (L/R/S)")
    speed_letter: Optional[str] = Field(None, description="Speed letter grade")
    speed_full: Optional[str] = Field(None, description="Full speed designation (e.g., 'A(19)')")
    speed_or_ip: Optional[int] = Field(None, description="Speed for hitters, IP for pitchers")
    icons_list: List[str] = Field(default_factory=list, description="List of card icons")
    
    # Awards and stats
    awards_list: List[str] = Field(default_factory=list, description="List of awards/achievements")
    
    # Chart information
    command: Optional[int] = Field(None, description="Command rating")
    outs: Optional[int] = Field(None, description="Number of outs on chart")
    is_chart_outlier: Optional[bool] = Field(None, description="Whether chart has command/outs anomaly")
    
    # Image information
    image_match_type: ImageMatchType = Field(ImageMatchType.NO_MATCH, description="Type of image match")
    image_ids: Optional[Dict[str, str]] = Field(None, description="Available image IDs (BG/CUT)")
    
    # Metadata
    updated_at: datetime = Field(description="When record was last updated")
        
    @property
    def player_subtype(self) -> str:
        """Derive player subtype based on games started ratio"""
        if self.player_type == 'HITTER':
            return 'POSITION_PLAYER'
        
        games_started_vs_total = round(self.gs / self.g, 4) if self.g > 0 else 0
        if games_started_vs_total >= 0.5:
            return 'STARTING_PITCHER'
        else:
            return 'RELIEF_PITCHER'
    
    @property
    def is_multi_team(self) -> bool:
        """Whether player played for multiple teams"""
        return len(self.team_id_list) > 1
    
    @property
    def has_awards(self) -> bool:
        """Whether player has any awards"""
        return len(self.awards_list) > 0
    
    @property
    def has_image_match(self) -> bool:
        """Whether player has any image match"""
        return self.image_match_type != ImageMatchType.NO_MATCH
    
    @property
    def chart_efficiency(self) -> Optional[float]:
        """Calculate chart efficiency (command per out)"""
        if self.command is not None and self.outs is not None and self.outs > 0:
            return round(self.command / self.outs, 2)
        return None
    
    @property
    def war(self) -> Optional[float]:
        """Get WAR from card data stats"""
        if not self.card_data or not self.card_data.stats:
            return None
        
        try:
            war_value = self.card_data.stats.get('bWAR', None)
            if war_value is not None:
                return float(war_value)
            return None
        except (ValueError, TypeError):
            return None
    
    def get_position_defense_rating(self, position: str) -> Optional[int]:
        """Get defense rating for a specific position"""
        if not self.positions_and_defense or position not in self.positions_and_defense:
            return None
        
        try:
            return int(self.positions_and_defense[position])
        except (ValueError, TypeError):
            return None
    
    def get_real_stat(self, stat_name: str) -> Optional[Any]:
        """Get a real stat value from card data"""
        if not self.card_data or 'stats' not in self.card_data:
            return None
        
        stats = self.card_data['stats']
        return stats.get(stat_name)
    
    def get_chart_value(self, outcome: str) -> Optional[float]:
        """Get a specific chart outcome value"""
        if not self.card_data or 'chart' not in self.card_data:
            return None
        
        chart = self.card_data['chart']
        if 'values' not in chart:
            return None
            
        try:
            return float(chart['values'].get(outcome, 0))
        except (ValueError, TypeError):
            return None
    
    def has_icon(self, icon: str) -> bool:
        """Check if player has a specific icon"""
        return icon in self.icons_list
    
    def has_award(self, award: str) -> bool:
        """Check if player has a specific award"""
        return award in self.awards_list
    
    def has_award_prefix(self, award_prefix: str) -> bool:
        """Check if player has any award starting with prefix (e.g., 'MVP-' for any MVP ranking)"""
        return any(award.startswith(award_prefix) for award in self.awards_list)



# ----------------------------------------------------------------
# MARK: - POSTGRES DB CLASS
# ----------------------------------------------------------------

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
    
    def fetch_player_search_from_archive(self, players_stats_ids: list[str]) -> list[dict]:
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

    def fetch_explore_data(self, filters: dict = {}) -> list[ExploreDataRecord]:
        """Fetch all explore data from the database with support for lists and min/max filtering."""

        raw_data = self.fetch_card_data(filters=filters)
        if raw_data is None:
            return []

        return [ExploreDataRecord(**row) for row in raw_data]

    def fetch_card_data(self, filters: dict = {}) -> list[dict]:
        """Fetch all card data from the database with support for lists and min/max filtering."""

        if not self.connection:
            return None
        
        try:

            # Pop Out Source
            source = str(filters.pop('source', 'BOT')).lower()

            match source:
                case 'bot':
                    query = sql.SQL("""
                        SELECT *
                        FROM explore_data
                        WHERE TRUE
                    """)
                case 'wotc':
                    query = sql.SQL("""
                        SELECT *
                        FROM wotc_card_data
                        WHERE TRUE
                    """)

            filter_values = []

            # Pop out sorting filters
            sort_by = str(filters.pop('sort_by', 'points'))
            sort_direction = str(filters.pop('sort_direction', 'desc')).lower()

            # Pop out pagination and limit
            page = int(filters.pop('page', 1))
            limit = int(filters.pop('limit', 50))

            # Apply filters if any
            if filters and len(filters) > 0:
                filter_clauses = []

                # SOURCE SPECIFIC FILTERS
                match source:
                    case 'bot':
                        filters['showdown_bot_version'] = __version__
                    case 'wotc':
                        sets = filters.get('showdown_set', [])
                        # FILTER TO SPECIFIC SETS IF USER HAS `CLASSIC` OR `EXPANDED` SELECTED - THEY DIDNT EXIST IN WOTC
                        if isinstance(sets, str):
                            if sets == 'CLASSIC':
                                filters['showdown_set'] = ['2000', '2001']
                            elif sets == 'EXPANDED':
                                filters['showdown_set'] = ['2002', '2003', '2004', '2005']

                
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
                            case 'awards':
                                # Check if any of the provided awards are in the player's awards
                                # Handle partial matching for values ending with '-'
                                award_conditions = []
                                for award in value:
                                    if award.endswith('-*'):
                                        # Partial match: check if any element in the array starts with the prefix
                                        award_prefix = award[:-2]  # Remove the trailing '-*'
                                        award_conditions.append(sql.SQL("EXISTS (SELECT 1 FROM unnest(awards_list) AS award WHERE award LIKE %s)"))
                                        filter_values.append(f"{award_prefix}-%")
                                    else:
                                        # Exact match: check if the exact value exists in the array
                                        award_conditions.append(sql.SQL("%s = ANY(awards_list)"))
                                        filter_values.append(award)
                                
                                if award_conditions:
                                    filter_clauses.append(sql.SQL("({})").format(
                                        sql.SQL(" OR ").join(award_conditions)
                                    ))
                            case 'include_small_sample_size':
                                # Only filter if array is ["false"]
                                if value == ["false"]:
                                    filter_clauses.append(sql.SQL("(case" \
                                        " when positions_list && ARRAY['STARTER'] then real_ip >= 75" \
                                        " when positions_list && ARRAY['RELIEVER', 'CLOSER'] then real_ip >= 30" \
                                        " else pa >= 250" \
                                    " end)"))
                            case 'is_hof':
                                # Filter based on Hall of Fame status
                                if value == ['true']:
                                    filter_clauses.append(sql.SQL("jsonb_extract_path(card_data, 'stats', 'is_hof')::BOOLEAN IS TRUE"))
                                elif value == ['false']:
                                    filter_clauses.append(sql.SQL("jsonb_extract_path(card_data, 'stats', 'is_hof')::BOOLEAN IS NOT TRUE"))
                                
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
            if 'positions_and_defense' in sort_by:
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

            elif 'chart_values' in sort_by:
                chart_key = sort_by.replace('chart_values_', '').upper()
                final_sort = sql.SQL("""(card_data->'chart'->'values'->>%s)::float {direction} NULLS LAST""").format(
                    direction=sql.SQL(sort_direction)
                )
                filter_values += [chart_key]

            elif 'real_stats' in sort_by:
                real_stats_key = sort_by.replace('real_stats_', '')
                final_sort = sql.SQL("""case when length((card_data->'stats'->>%s)) = 0 then null else (card_data->'stats'->>%s)::float end {direction} NULLS LAST""").format(
                    direction=sql.SQL(sort_direction)
                )
                filter_values += [real_stats_key, real_stats_key]

            else:
                final_sort = sql.SQL("{field} {direction} NULLS LAST").format(
                    field=sql.Identifier(sort_by),
                    direction=sql.SQL(sort_direction)
                )

            query += sql.SQL(" ORDER BY {}, points DESC, bref_id, year").format(final_sort)

            # ADD LIMIT AND PAGINATION
            if not isinstance(page, int) or page < 1:
                page = 1
            if not isinstance(limit, int) or limit < 1 or limit > 5000:
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

    def refresh_explore_views(self, drop_existing:bool=False) -> None:
        """Refreshes all explore related materialized views.

        Views:
            - player_search: List of players and seasons with a bWAR and award summary. Source for advanced search on the customs page;
            - team_year_league_list: List of teams by year and league. Source for league/team hierarchy filters on the explore page;
            - explore_data: Main explore data view that powers the explore page.
            
        Args:
            drop_existing: If True, drop existing views before recreating them.
            
        Returns:
            None
        """

        if self.connection is None:
            print("No database connection available for refreshing explore views.")
            return

        # BUILD EXTENSIONS
        self._build_extensions()

        # REFRESH MATERIALIZED VIEWS
        if not self.build_player_search_view(drop_existing=drop_existing): return
        if not self.build_team_year_league_list_view(drop_existing=drop_existing): return
        if not self.build_explore_data_view(drop_existing=drop_existing): return
        if not self.build_team_hierarchy_view(drop_existing=drop_existing): return

        self.connection.close()

# ------------------------------------------------------------------------
# WOTC
# ------------------------------------------------------------------------

    def upload_wotc_card_data(self, wotc_card_data: list[ShowdownPlayerCard], drop_existing:bool=False) -> bool:
        """Upload WOTC card data to the database.
        
        Args:
            wotc_card_data: List of WOTCCardData objects to upload.
            drop_existing: If True, drop existing table before uploading new data.
        
        Returns:
            True if upload was successful, False otherwise.
        """

        if self.connection is None:
            print("No database connection available for uploading WOTC card data.")
            return False
        
        try:
            cursor = self.connection.cursor()

            # DROP EXISTING TABLE IF REQUESTED
            if drop_existing:
                cursor.execute("DROP TABLE IF EXISTS wotc_card_data;")
                print("  → Dropped existing wotc_card_data table.")

            # CREATE TABLE IF NOT EXISTS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wotc_card_data (
                    id character varying(100) NOT NULL,
                    player_id character varying(64),
                    showdown_set character varying(20) NOT NULL,
                    expansion character varying(20),
                    edition character varying(20),
                    card_data jsonb,
                    year character varying(15),
                    bref_id character varying(10),
                    name character varying(100),
                    player_type character varying(50),
                    player_type_override character varying(50),
                    primary_positions text[],
                    secondary_positions text[],
                    g integer,
                    gs integer,
                    pa integer,
                    real_ip integer,
                    lg_id character varying(10),
                    team_id character varying(10),
                    team_id_list text[],
                    showdown_bot_version character varying(10),
                    points integer,
                    points_estimated integer,
                    points_diff_estimated_vs_actual integer,
                    nationality character varying(50),
                    organization character varying(50),
                    league character varying(50),
                    team character varying(50),
                    positions_and_defense jsonb,
                    positions_and_defense_string character varying(100),
                    positions_list text[],
                    ip integer,
                    speed integer,
                    hand character varying(10),
                    speed_letter character varying(5),
                    speed_full character varying(20),
                    speed_or_ip integer,
                    icons_list text[],
                    awards_list text[],
                    command integer,
                    outs integer,
                    is_chart_outlier boolean,
                    is_errata boolean DEFAULT FALSE,
                    notes text,
                    created_date timestamp without time zone DEFAULT now(),
                    modified_date timestamp without time zone DEFAULT now()
                );
                """
            )
            print("  → Ensured wotc_card_data table exists.")

            # CLEAR EXISTING DATA
            cursor.execute("DELETE FROM wotc_card_data;")
            print("  → Cleared existing WOTC card data.")

            # PREPARE BATCH DATA
            batch_data = []
            for card in wotc_card_data:
                player_id = "-".join([str(card.year), card.bref_id]) if card.bref_id else None
                if card.stats_period.type != StatsPeriodType.REGULAR_SEASON:
                    player_id += f"-{card.stats_period.id}"

                stat_source = card.stats_for_card or {}
                
                batch_data.append((
                    card.id,
                    player_id,
                    card.set.value,
                    card.image.expansion.value if card.image.expansion else None,
                    card.image.edition.value if card.image.edition else None,
                    json.dumps(card.as_json()),
                    card.year,
                    card.bref_id,
                    card.name,
                    card.player_type.value.upper() if card.player_type else None,
                    card.player_type_override.value.upper() if card.player_type_override else None,
                    [p.value for p in card.positions_and_games_played.keys()],
                    [],
                    stat_source.get("G", None),
                    stat_source.get("GS", None),
                    stat_source.get("PA", None),
                    stat_source.get("IP", None),
                    card.league,
                    card.team,
                    [card.team],
                    __version__,
                    card.points,
                    card.points_estimated,
                    card.points_diff_estimated_vs_actual,
                    card.nationality.value if card.nationality else None,
                    "MLB",
                    card.league,
                    card.team,
                    json.dumps(card.positions_and_defense_for_visuals),
                    card.positions_and_defense_string,
                    [p.value for p in card.positions_list],
                    card.ip if card.ip else 0,
                    card.speed.speed if card.speed.speed else 0,
                    card.hand.value if card.hand else None,
                    card.speed.letter if card.speed.speed else None,
                    card.speed.full_string if card.speed.speed else None,
                    card.ip or card.speed.speed,
                    [i.value for i in card.icons],
                    [a for a in stat_source.get("awards", "").split(",") if a],
                    card.chart.command,
                    card.chart.outs_full,
                    card.chart.is_command_out_anomaly,
                    card.is_errata,
                    card.notes,
                    datetime.now(),
                ))

            # BATCH INSERT NEW DATA
            insert_query = """
                INSERT INTO wotc_card_data (
                    id,
                    player_id,
                    showdown_set,
                    expansion,
                    edition,
                    card_data,
                    year,
                    bref_id,
                    name,
                    player_type,
                    player_type_override,
                    primary_positions,
                    secondary_positions,
                    g,
                    gs,
                    pa,
                    real_ip,
                    lg_id,
                    team_id,
                    team_id_list,
                    showdown_bot_version,
                    points,
                    points_estimated,
                    points_diff_estimated_vs_actual,
                    nationality,
                    organization,
                    league,
                    team,
                    positions_and_defense,
                    positions_and_defense_string,
                    positions_list,
                    ip,
                    speed,
                    hand,
                    speed_letter,
                    speed_full,
                    speed_or_ip,
                    icons_list,
                    awards_list,
                    command,
                    outs,
                    is_chart_outlier,
                    is_errata,
                    notes,
                    modified_date
                )
                VALUES %s
            """

            execute_values(
                cursor, 
                insert_query, 
                batch_data,
                template=None,
                page_size=1000  # Process in chunks of 1000
            )
            
            print(f"  → Uploaded {len(wotc_card_data)} WOTC card data records.")
            return True

        except Exception as e:
            traceback.print_exc()
            print(f"Error uploading WOTC card data: {e}")
            self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

# -------------------------------------------------------------------------
# IDS
# ------------------------------------------------------------------------

    def update_player_id_table(self, data: List[dict]) -> None:
        """Update the player_id_master table with new data. Load is always rip and replace.
        
        Args:
            data: List of dictionaries containing player ID master data.
        
        Returns:
            None
        """

        if self.connection is None:
            print("No database connection available for updating player ID mapping.")
            return

        try:
            cursor = self.connection.cursor()

            # CREATE TABLE IF NOT EXISTS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_id_master (
                    bref_id character varying(10) PRIMARY KEY,
                    mlb_id integer,
                    fangraphs_id integer,
                    name_first character varying(50),
                    name_last character varying(50),
                    mlb_first_year integer,
                    mlb_last_year integer,
                    created_date timestamp without time zone DEFAULT now(),
                    modified_date timestamp without time zone DEFAULT now()
                );
                """
            )
            print("  → Ensured player_id_mapping table exists.")

            # ADD INDEXES/UNIQUES ON bref_id AND mlb_id
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_player_id_master_mlb_id
                ON player_id_master (mlb_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_player_id_master_bref_id
                ON player_id_master (bref_id);
            """)
            print("  → Ensured indexes on player_id_master table exist.")


            # PREPARE BATCH DATA
            batch_data = []
            for record in data:
                batch_data.append((
                    record.get('bref_id'),
                    record.get('mlb_id'),
                    record.get('fangraphs_id'),
                    record.get('name_first'),
                    record.get('name_last'),
                    record.get('mlb_first_year'),
                    record.get('mlb_last_year'),
                    datetime.now(),
                ))

            # UPSERT DATA
            upsert_query = """
                INSERT INTO player_id_master (
                    bref_id,
                    mlb_id,
                    fangraphs_id,
                    name_first,
                    name_last,
                    mlb_first_year,
                    mlb_last_year,
                    modified_date
                )
                VALUES %s
                ON CONFLICT (bref_id) DO UPDATE SET
                    mlb_id = EXCLUDED.mlb_id,
                    fangraphs_id = EXCLUDED.fangraphs_id,
                    name_first = EXCLUDED.name_first,
                    name_last = EXCLUDED.name_last,
                    mlb_first_year = EXCLUDED.mlb_first_year,
                    mlb_last_year = EXCLUDED.mlb_last_year,
                    modified_date = EXCLUDED.modified_date;
            """

            execute_values(
                cursor, 
                upsert_query, 
                batch_data,
                template=None,
                page_size=1000  # Process in chunks of 1000
            )
            
            print(f"  → Updated {len(data)} player ID master records.")

        except Exception as e:
            traceback.print_exc()
            print(f"Error updating player ID master: {e}")
            self.connection.rollback()
        finally:
            if cursor:
                cursor.close()


# ------------------------------------------------------------------------
# MATERIALIZED VIEWS
# ------------------------------------------------------------------------

    def _build_materialized_view(self, view_name:str, sql_logic: str, schema:str = 'public', indexes: list[str] = None, drop_existing:bool=False) -> bool:
        """Create or replace a materialized view in the database.
        
        Args:
            name: Name of the materialized view.
            sql_logic: SQL logic to define the view. Does not include CREATE MATERIALIZED VIEW statement.
            schema: Schema where the view will be created.
            indexes: List of index creation SQL statements to execute after creating the view.
            drop_existing: If True, drop the existing view before creating a new one.

        Returns:
            True if the view was rebuilt successfully, False otherwise.
        """

        # RETURN IF NO CONNECTION
        if self.connection is None:
            print("No database connection available for building materialized view.")
            return
        
        try:
            cursor = self.connection.cursor()

            # DROP EXISTING VIEW IF REQUESTED
            if drop_existing:
                cursor.execute(sql.SQL("""
                    DROP MATERIALIZED VIEW IF EXISTS {schema}.{view_name} CASCADE;
                """).format(
                    schema=sql.Identifier(schema),
                    view_name=sql.Identifier(view_name)
                ))
                print(f"  → Dropped existing materialized view '{view_name}'.")
            
            # CHECK IF VIEW EXISTS
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_matviews 
                    WHERE matviewname = %s AND schemaname = %s
                )
            """, (view_name.lower(), schema.lower()))
            view_exists = cursor.fetchone()[0]
            
            # VIEW EXISTS, REFRESH IT
            if view_exists:
                # DO IT CONCURRENTLY IF INDEXES EXIST
                if indexes:
                    cursor.execute(sql.SQL("""
                        REFRESH MATERIALIZED VIEW CONCURRENTLY {schema}.{view_name};
                    """).format(
                        schema=sql.Identifier(schema),
                        view_name=sql.Identifier(view_name)
                    ))
                else:
                    cursor.execute(sql.SQL("""
                        REFRESH MATERIALIZED VIEW {schema}.{view_name};
                    """).format(
                        schema=sql.Identifier(schema),
                        view_name=sql.Identifier(view_name)
                    ))
                print(f"  → Refreshed existing materialized view '{view_name}'.")
                return True

            # VIEW DOES NOT EXIST, CREATE IT
            cursor.execute(sql.SQL("""
                CREATE MATERIALIZED VIEW {schema}.{view_name} AS (
                    {sql_logic}
                );
            """).format(
                schema=sql.Identifier(schema),
                view_name=sql.Identifier(view_name),
                sql_logic=sql.SQL(sql_logic)
            ))
            print(f"  → Created materialized view '{view_name}'.")
            if indexes:
                for index in indexes:
                    cursor.execute(index)
                    print(f"  → Created index for materialized view '{view_name}': {index}")
            return True

        # EXCEPT BLOCK
        except Exception as e:
            print(f"Error creating {view_name} view: {e}")
            self.connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def build_player_search_view(self, drop_existing:bool = False) -> None:
        """Build or refresh the player_search materialized view.
        
        Args:
            drop_existing: If True, drop the existing view before creating a new one.
        
        """

        sql_logic = '''
            with
            
            archive_data as (
            
                select
                unaccent(replace(lower(name), '.', '')) as name,
                year,
                bref_id,
                team_id as team,
                player_type_override,
                jsonb_extract_path(stats, 'is_hof')::boolean as is_hof,
                case when length(stats->>'award_summary') = 0 then null else stats->>'award_summary'::text end as award_summary,
                case when length((stats->>'bWAR')) = 0 then 0.0 else (stats->>'bWAR')::float end as bwar
                from stats_archive
                
            ),
            
            current_season_data as (
            
                select
                unaccent(replace(lower(name), '.', '')) as name,
                date_part('year', modified_date) as year,
                bref_id,
                team_id as team,
                null::text as player_type_override,
                false as is_hof,
                award_summary,
                bwar
                from current_season_players
                where date_part('year', modified_date) > (select max(year) from stats_archive)
                
            ),
            
            combined as (
            
                select *
                from archive_data
                union all
                select *
                from current_season_data
            
            )
            
            select *
            from combined
        '''
        indexes = [
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_player_search_bref_id ON player_search (bref_id, year, player_type_override);"
        ]
        return self._build_materialized_view(
            view_name='player_search',
            sql_logic=sql_logic,
            indexes=indexes,
            drop_existing=drop_existing
        )

    def build_team_year_league_list_view(self, drop_existing:bool = False) -> None:
        """Build or refresh the team_year_league_list materialized view.
        
        Args:
            drop_existing: If True, drop the existing view before creating a new one.
        
        """

        sql_logic = '''
            with 
            
            years_and_teams as (
            
                select 
                distinct
                    case
                    when year = 1939 and team_id = 'TC2' then 'NGL'
                    when lg_id in ('NN2', 'NNL', 'NAL', 'ECL', 'NSL', 'ANL', 'EWL') then 'NGL'
                    when lg_id in ('PL', 'AA', 'FL', 'UA') then 'NON-MLB'
                    when lg_id in ('2LG', 'NL', 'AL')  then 'MLB'
                    else lg_id
                    end as organization,
                    
                    case
                    when year = 1939 and team_id = 'TC2' then 'NNL'
                    else lg_id
                    end as league,
                    team_id as team,
                    year
                
                from stats_archive
                where true
                and (
                    lg_id not in ('2LG', 'MLB')
                    or (year = 1939 and team_id = 'TC2')
                )
            
            ), 
            
            --  explore_mismatches as (
            --  
            --    select distinct name, explore_data.year, explore_data.team_id
            --    from explore_data
            --    left join years_and_teams 
            --      on explore_data.team_id = years_and_teams.team_id
            --      and explore_data.year = years_and_teams.year
            --    where explore_data.showdown_set = '2005'
            --      and years_and_teams.team_id is null
            --      
            --  ),
            
            dupes as (
            
                select 
                team,
                year,
                count(*) as rc
                from years_and_teams
                group by 1,2
                having count(*) > 1
                
            )
            
            select *
            from years_and_teams
        '''
        indexes = [
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_team_year_league_list ON team_year_league_list (team, year);"
        ]
        return self._build_materialized_view(
            view_name='team_year_league_list',
            sql_logic=sql_logic,
            indexes=indexes,
            drop_existing=drop_existing
        )

    def build_explore_data_view(self, drop_existing:bool = False) -> None:
        """Build or refresh the explore_data materialized view.
        
        Args:
            drop_existing: If True, drop the existing view before creating a new one.
        
        """

        sql_logic = '''
            select 
                stats_archive.id,
                stats_archive.year,
                stats_archive.bref_id,
                unaccent(stats_archive.name) as name,
                stats_archive.player_type,
                stats_archive.player_type_override,
                stats_archive.is_two_way,
                stats_archive.primary_positions,
                stats_archive.secondary_positions,
                stats_archive.g,
                stats_archive.gs,
                stats_archive.pa,
                stats_archive.ip as real_ip,
                stats_archive.lg_id,
                stats_archive.team_id,
                stats_archive.team_id_list,
                stats_archive.team_games_played_dict,
                stats_archive.team_override,
                
                card_data.card_data,
                card_data.showdown_set,
                card_data->>'version' as showdown_bot_version,
                
                
                -- PARSED CARD ATTRIBUTES 
                cast(card_data->>'points' as int) as points,
                card_data->>'nationality' as nationality,
                team_year_league_list.organization,
                team_year_league_list.league,
                team_year_league_list.team,
                
                -- METADATA
                card_data->'positions_and_defense' as positions_and_defense,
                card_data->>'positions_and_defense_string' as positions_and_defense_string,
                ARRAY(
                    SELECT jsonb_array_elements_text(card_data->'positions_list')
                ) as positions_list,
                cast(card_data->>'ip' as int) as ip,
                cast(card_data->'speed'->>'speed' as int) as speed,
                card_data->>'hand' as hand,
                card_data->'speed'->>'letter' as speed_letter,
                (card_data->'speed'->>'letter') || '(' || (card_data->'speed'->>'speed') || ')' as speed_full,
                case
                    when stats_archive.player_type = 'HITTER' then cast(card_data->'speed'->>'speed' as int)
                    else cast(card_data->>'ip' as int)
                end as speed_or_ip,
                ARRAY(
                    SELECT jsonb_array_elements_text(card_data->'icons')
                ) as icons_list,

                -- STATS
                CASE
                    WHEN stats->>'award_summary' = '' OR stats->>'award_summary' IS NULL 
                    THEN ARRAY[]::text[]
                    ELSE string_to_array(stats->>'award_summary', ',')
                END as awards_list,
                
                -- CHART
                cast(card_data->'chart'->>'command' as int) as command,
                cast(card_data->'chart'->>'outs_full' as int) as outs,
                cast(card_data->'chart'->>'is_command_out_anomaly' as boolean) as is_chart_outlier,
                
                -- AUTO IMAGES
                case
                    when exists (
                        select 1 from auto_images i
                        where i.player_id = stats_archive.bref_id
                        and i.year = stats_archive.year::text
                        and i.team_id = stats_archive.team_id
                        and coalesce(i.player_type_override, 'n/a') = coalesce(stats_archive.player_type_override, 'n/a')
                    ) then 'exact'
                    when exists (
                        select 1 from auto_images i
                        where i.player_id = stats_archive.bref_id
                        and i.team_id = stats_archive.team_id
                        and coalesce(i.player_type_override, 'n/a') = coalesce(stats_archive.player_type_override, 'n/a')
                    ) then 'team match'
                    when exists (
                        select 1 from auto_images i
                        where i.player_id = stats_archive.bref_id
                        and i.year = stats_archive.year::text
                        and coalesce(i.player_type_override, 'n/a') = coalesce(stats_archive.player_type_override, 'n/a')
                    ) then 'year match'
                    else 'no match'
                end as image_match_type,
                
                exact_img_match.image_ids as image_ids,
                
                NOW() as updated_at
                
            from stats_archive
            join card_data 
                on stats_archive.id = card_data.player_id
            left join team_year_league_list
                on team_year_league_list.year = stats_archive.year 
                and team_year_league_list.team = stats_archive.team_id
            left join auto_images as exact_img_match
                on stats_archive.year::text = exact_img_match.year
                and stats_archive.bref_id = exact_img_match.player_id
                and coalesce(stats_archive.player_type_override, 'n/a') = coalesce(exact_img_match.player_type_override, 'n/a')
                and stats_archive.team_id = exact_img_match.team_id
                and exact_img_match.is_postseason = FALSE
        '''
        indexes = [
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_explore_data_card_set_version ON explore_data (id, showdown_set, showdown_bot_version);"
        ]
        # SHOOT MESSAGE TO USER WHILE THE VIEW IS REBUILDING (IF DROPPED)
        if drop_existing:
            self.update_feature_status(
                feature_name='explore',
                message='The Explore data is being upgraded, this may take several minutes. Please check back soon!',
                is_disabled=True
            )

        status = self._build_materialized_view(
            view_name='explore_data',
            sql_logic=sql_logic,
            indexes=indexes,
            drop_existing=drop_existing
        )

        # REMOVE STATUS MESSAGE IF SUCCESSFUL
        if drop_existing:
            self.update_feature_status(
                feature_name='explore',
                message=None,
                is_disabled=False
            )

        return status

    def build_team_hierarchy_view(self, drop_existing:bool = False) -> None:
        """Build or refresh the team_hierarchy materialized view. Used in the explore for filtering
        
        Args:
            drop_existing: If True, drop the existing view before creating a new one.
        """

        sql_logic = '''
            with teams as (
  
                select 
                organization, 
                league, 
                team, 
                min(year) as min_year, 
                max(year) as max_year, 
                count(*) as cards
                
                from explore_data
                where true
                and league != 'MLB'
                group by 1,2,3
            
            )
            
            select *
            from teams
            order by team
        '''
        return self._build_materialized_view(
            view_name='team_hierarchy',
            sql_logic=sql_logic,
            indexes=[],
            drop_existing=True # Always drop to capture new teams
        )

# ------------------------------------------------------------------------
# EXTENSIONS
# ------------------------------------------------------------------------

    def _build_extensions(self) -> None:
        """Create necessary extensions in the database."""

        # RETURN IF NO CONNECTION
        if self.connection is None:
            print("No database connection available for creating extensions.")
            return
        
        create_extension_statements = [
            "CREATE EXTENSION IF NOT EXISTS unaccent;"
        ]
        db_cursor = self.connection.cursor()
        try:
            for statement in create_extension_statements:
                db_cursor.execute(statement)
        except:
            return
        finally:
            db_cursor.close()

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

    def build_auto_images_table(self, refresh_explore: bool=False, drop_existing:bool = False) -> None:
        """Creates and replaces the auto_images table in the database."""
 
        # RETURN IF NO CONNECTION
        if self.connection is None:
            print("No database connection available for fetching auto-generated image metadata.")
            return

        # FETCH IMAGE METADATA FROM GOOGLE DRIVE
        print("Fetching auto-generated image metadata from Google Drive...")
        image_metadata = fetch_image_metadata(
            folder_id=Set._2000.player_image_gdrive_folder_id, 
            retries=3
        )
        print(f"Fetched metadata for {len(image_metadata)} files from Google Drive.")
        
        # TRANSFORM INTO DICT WITH {image_name: {BG: id, 'CUT': id }}
        aggregated_images: dict[str, dict[str, str]] = {}
        for item in image_metadata:
            image_name: str = item['name']
            if '-' not in image_name: continue
            image_id: str = item['id']
            image_name_without_type = image_name.split('-', 1)[-1]  # Remove prefix before first '-'
            updated_dict = aggregated_images.get(image_name_without_type, {})
            if 'BG' in image_name:
                updated_dict['BG'] = image_id
            elif 'CUT' in image_name:
                updated_dict['CUT'] = image_id
            aggregated_images[image_name_without_type] = updated_dict

        # PARSE NAMES AND STORE AS CLASSES
        auto_image_entries: list[dict] = []
        for image_name, image_ids in aggregated_images.items():

            # PARSE NAME INTO COMPONENTS
            # EX: 2025-Raleigh-(raleica01)-(SEA).png
            #   - year: 2025
            #   - team_id: SEA
            #   - player_id: raleica01
            #   - player_name: Raleigh
            final_attributes: dict[str, any] = {'image_ids': image_ids}
            name_parts = image_name.rsplit('.', 1)[0].split('-')
            has_reached_first_parenthesis = False
            player_name = "" # ADDED TO IN MULTIPLE PARTS
            for index, text in enumerate(name_parts):
                has_parenthesis = text.startswith('(') and text.endswith(')')
                
                # YEAR
                if index == 0:
                    final_attributes['year'] = int(text)
                    continue
                
                # PLAYER NAME
                if not has_reached_first_parenthesis and not has_parenthesis:
                    if player_name == "":
                        player_name = text
                    else:
                        player_name += f" {text}"
                    continue
                
                # PLAYER ID
                if has_parenthesis and not has_reached_first_parenthesis:
                    final_attributes['player_name'] = player_name # STORE PLAYER NAME
                    final_attributes['player_id'] = text.split('(')[1].split(')')[0]
                    has_reached_first_parenthesis = True

                # TEAM ID
                if has_parenthesis and len(text) <= 5:
                    final_attributes['team_id'] = text.split('(')[1].split(')')[0]

                if text == '(POST)':
                    final_attributes['is_postseason'] = True

                if has_parenthesis and ('Hitter' in text or 'Pitcher' in text):
                    final_attributes['player_type_override'] = text.lower() # KEEP PARENTHESIS AND LOWERCASE TO MATCH STATS ARCHIVE (e.g., (hitter), (pitcher))

            auto_image_entries.append(final_attributes)

        # DATABASE OPERATIONS
        db_cursor = self.connection.cursor()

        # CHECK IF TABLE EXISTS
        table_exists_query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'auto_images'
            );
        """
        db_cursor.execute(table_exists_query)
        table_exists = db_cursor.fetchone()[0]
        if table_exists:
            print("auto_images table exists. It will be replaced with new data.")
        
            # TRUNCATE THE EXISTING TABLE
            if drop_existing:
                truncate_or_drop_table_statement = '''
                    DROP TABLE IF EXISTS auto_images;
                '''
            else:
                truncate_or_drop_table_statement = '''
                    TRUNCATE TABLE auto_images;
                '''
        else:
            truncate_or_drop_table_statement = '''
                -- Table does not exist, will be created.
            '''
        create_table_statement = f'''
            CREATE TABLE IF NOT EXISTS auto_images(
                year VARCHAR(20) NOT NULL,
                player_id VARCHAR(10) NOT NULL,
                player_name VARCHAR(48) NOT NULL,
                team_id VARCHAR(10),
                player_type_override VARCHAR(10),
                is_postseason BOOLEAN DEFAULT FALSE,
                image_ids JSONB,
                created_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
            );'''
        index_statement = '''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_auto_images_player_year_type
            ON auto_images (year, player_id, player_type_override, team_id, is_postseason);
        '''
        try:
            db_cursor.execute(truncate_or_drop_table_statement)
            db_cursor.execute(create_table_statement)
            db_cursor.execute(index_statement)
        except Exception as e:
            print(f"Error occurred while setting up database tables: {e}")
            return
        
        # INSERT OR UPDATE ROWS
        insert_statement = """
            INSERT INTO auto_images (year, player_id, player_name, team_id, player_type_override, image_ids, is_postseason) 
            VALUES %s
        """
        insert_values = []

        for entry in auto_image_entries:
            player_id = entry.get('player_id')
            year = entry.get('year')
            player_type_override = entry.get('player_type_override', None)
            team_id = entry.get('team_id', None)
            image_ids = entry.get('image_ids', {})
            is_postseason = entry.get('is_postseason', False)
            if not player_id or not year:
                continue
            insert_values.append((
                year,
                player_id,
                entry.get('player_name'),
                team_id,
                player_type_override,
                image_ids,
                is_postseason
            ))
        try:
            execute_values(db_cursor, insert_statement, insert_values)
            print(f"Inserted/Updated {len(insert_values)} rows into auto_images table.")
        except Exception as e:
            print(f"Error inserting/updating auto_images data: {e}")
            self.connection.rollback()
            return
        finally:
            db_cursor.close()

        
        # REFRESH EXPLORE (DOWNSTREAM DEPENDENCY)
        if refresh_explore:
            self.refresh_explore_views()

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
        try:
            cursor.execute(insert_statement, (AsIs(','.join(columns)), tuple(values)))
        except Exception as e:
            print(f"ERROR upserting stats archive row for id {data.get('id')}: {e}")
            pass
        
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

                    batch_data.append((card_data['player_id'], showdown.set.value, showdown.version, card_data))

                # Insert batch
                insert_query = """
                    INSERT INTO card_data (player_id, showdown_set, version, card_data) 
                    VALUES %s
                    ON CONFLICT (player_id, showdown_set, version) 
                    DO UPDATE SET 
                        card_data = EXCLUDED.card_data,
                        modified_date = NOW()
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

# ------------------------------------------------------------------------
# STATUSES
# ------------------------------------------------------------------------

    def update_feature_status(self, feature_name:str, is_disabled:bool, message:str=None) -> bool:
        """Update the status of a feature in the feature_status table.
        
        Args:
            feature_name: Name of the feature to update.
            is_disabled: New status of the feature (True for disabled, False for enabled).
            message: Optional message associated with the status update.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if self.connection is None:
            print("ERROR: NO CONNECTION TO DB")
            return False

        cursor = self.connection.cursor()

        # CHECK IF TABLE EXISTS
        table_check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'feature_status'
            );
        """
        cursor.execute(table_check_query)
        table_exists = cursor.fetchone()[0]
        if not table_exists:
            create_table_query = """
                CREATE TABLE feature_status (
                    feature_name VARCHAR(100) PRIMARY KEY,
                    is_disabled BOOLEAN NOT NULL,
                    message TEXT,
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
            """
            cursor.execute(create_table_query)
            self.connection.commit()

        try:
            update_query = """
                INSERT INTO feature_status (feature_name, is_disabled, message, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (feature_name) DO UPDATE SET
                    is_disabled = EXCLUDED.is_disabled,
                    message = EXCLUDED.message,
                    updated_at = NOW()
            """
            cursor.execute(update_query, (feature_name, is_disabled, message))
            self.connection.commit()
            return cursor.rowcount > 0

        except Exception as e:
            print(f"ERROR updating feature status: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def get_feature_statuses(self) -> dict[str, dict[str, any]]:
        """Check the status of features in the feature_status table.
        Used to show users if certain features are disabled.
        
        Returns:
            dict: A dictionary with feature names as keys and their status info as values.
        """
        if self.connection is None:
            print("ERROR: NO CONNECTION TO DB")
            return {}

        cursor = self.connection.cursor()

        try:
            query = """
                SELECT feature_name, is_disabled, message, updated_at AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York' as updated_at
                FROM feature_status
                WHERE is_disabled
            """
            cursor.execute(query)
            results = cursor.fetchall()

            # Map results to a dictionary
            feature_statuses = {
                row[0]: {
                    'name': row[0],
                    'is_disabled': row[1],
                    'message': row[2],
                    'updated_at': row[3]
                }
                for row in results
            }
            return feature_statuses

        except Exception as e:
            print(f"ERROR checking feature statuses: {e}")
            return {}
        finally:
            cursor.close()