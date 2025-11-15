from pydantic import BaseModel, Field, field_serializer
from typing import Any, Dict, Optional, List, Set
from enum import Enum

from ...mlb_stats_api.models.person import Position, Player as MLBStatsApi_Player, StatGroupEnum, StatTypeEnum, StatSplit
from ...shared.player_position import PlayerType
from ...card.stats.stats_period import StatsPeriod

# -------------------------------
# MARK: - Primary Datasources 
# -------------------------------
class PrimaryDatasource(str, Enum):
    MLB_API = "mlb_api"
    BREF = "bref"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            match value.lower():
                case 'mlb_api' | 'mlb' | 'mlbstatsapi':
                    return cls.MLB_API
                case 'bref' | 'baseball_reference' | 'baseballreference':
                    return cls.BREF
        return cls.BREF # Default to BREF if unrecognized

# -------------------------------
# MARK: - Normalized Player Stats Model
# -------------------------------
class NormalizedPlayerStats(BaseModel):
    """Creates a shared structure for player stats across different sources"""

    # Identity & Metadata
    primary_datasource: PrimaryDatasource
    bref_id: Optional[str] = None
    mlb_id: Optional[int] = None
    bref_url: Optional[str] = None
    mlb_url: Optional[str] = None
    name: str
    nationality: Optional[str] = None

    # Season Context
    year_id: int | str = Field(..., alias='year_ID')  # e.g., 2023 or "Career"
    age: Optional[int] = None
    team_id: Optional[str] = Field(None, alias='team_ID')
    lg_ID: Optional[str] = None
    
    # Player Type & Physical
    type: str  # "Hitter" or "Pitcher"
    hand: Optional[str] = None  # "Left", "Right", "Both"
    hand_throw: Optional[str] = None  # "Left", "Right"
    
    # Career Context
    years_played: Optional[List[str]] = None
    rookie_status_year: Optional[int] = None
    is_rookie: bool = False
    is_hof: bool = False
    
    # Core Hitting Stats
    G: int = 0
    PA: int = 0
    AB: int = 0
    R: int = 0
    H: int = 0
    singles: int = Field(0, alias='1B')  # Handle "1B" field name
    doubles: int = Field(0, alias='2B')  # Handle "2B" field name
    triples: int = Field(0, alias='3B')  # Handle "3B" field name
    HR: int = 0
    RBI: int = 0
    SB: int = 0
    CS: int = 0
    BB: int = 0
    SO: int = 0
    
    # Additional Hitting Stats
    TB: int = 0
    GIDP: int = 0
    HBP: int = 0
    SH: int = 0
    SF: int = 0
    IBB: int = 0
    
    # Calculated Stats
    batting_avg: float = 0.0
    onbase_perc: float = 0.0
    slugging_perc: float = 0.0
    onbase_plus_slugging: float = 0.0
    onbase_plus_slugging_plus: Optional[int] = None  # OPS+
    
    # Advanced Ratios
    go_ao_ratio: Optional[float] = Field(None, alias='GO/AO')
    if_fb_ratio: Optional[float] = Field(None, alias='IF/FB')
    
    # Leadership Flags
    is_hr_leader: bool = False
    is_sb_leader: bool = False
    is_so_leader: bool = False
    is_above_hr_threshold: bool = False
    is_above_so_threshold: bool = False
    is_above_sb_threshold: bool = False
    is_above_w_threshold: bool = False
    
    # Position & Defense
    pos_season: Optional[str] = None  # e.g., "*6/DH"
    positions: Optional[Dict[str, 'PositionStats']] = None
    dWAR: Optional[float] = None
    bWAR: Optional[float] = None
    
    # Statcast Metrics
    sprint_speed: Optional[float] = None
    outs_above_avg: Optional[Dict[str, float]] = None
    
    # Awards & Recognition
    award_summary: Optional[str] = None
    accolades: Optional[Dict[str, List[str]]] = None
    
    # Game Logs
    game_logs: Optional[List['GameLog']] = None
    postseason_game_logs: Optional[List['PostseasonGameLog']] = None

    # Warnings
    warnings: Optional[List[str]] = None

    @field_serializer('primary_datasource')
    def serialize_primary_datasource(self, value: PrimaryDatasource) -> str:
        """Serialize enum to its string value"""
        return value.value if value else None

    @classmethod
    def expected_fields(cls) -> List[str]:
        """Returns a list of expected fields in the NormalizedPlayerStats model"""
        return list(cls.__annotations__.keys())
    
    @classmethod
    def field_aliases(cls) -> Dict[str, str]:
        """Returns a mapping of field aliases to their actual field names"""
        aliases = {}
        for field_name, field_info in cls.model_fields.items():
            if field_info.alias:
                aliases[field_info.alias] = field_name
        return aliases
    
    @classmethod
    def all_valid_field_names(cls) -> Set[str]:
        """Returns all valid field names including both actual names and aliases"""
        valid_names = set(cls.__annotations__.keys())
        
        # Add aliases
        for field_info in cls.model_fields.values():
            if field_info.alias:
                valid_names.add(field_info.alias)
        
        return valid_names

# -------------------------------
# MARK: - Normalizer Class
# -------------------------------

class PlayerStatsNormalizer:
    """Normalizes player stats from various sources into NormalizedPlayerStats"""
    
    @staticmethod
    def from_mlb_api(player: MLBStatsApi_Player, stats_period: StatsPeriod) -> NormalizedPlayerStats:
        """Normalizes stats from MLB Stats API Player model for a given season"""
        # Implementation would extract and map fields from Player to NormalizedPlayerStats
        # This is a placeholder for the actual normalization logic
        
        # Build normalized player
        normalized_data = {
            # Identity
            'primary_datasource': PrimaryDatasource.MLB_API,
            'mlb_id': player.id,

            'name': player.full_name,
            'year_ID': stats_period.year,
            'team_ID': player.current_team.abbreviation if player.current_team else None,
            'type': PlayerStatsNormalizer._mlb_api_determine_player_type(player.primary_position),
            'hand': Hand(player.bat_side.description).value,
            'hand_throw': Hand(player.pitch_hand.description).value,
            
            # Standard stats
            **PlayerStatsNormalizer._extract_standard_stats(player, stats_period),
            
            # Defensive stats
            'positions': PlayerStatsNormalizer._extract_position_stats(player, stats_period),

            # Missing
            'outs_above_avg': {}, # TODO: Extract from Statcast data
            'sprint_speed': None, # TODO: Extract from Statcast data
            'accolades': {}, # TODO: Find a source for accolades
            
            # # Advanced metrics
            # 'sprint_speed': getattr(mlb_player, 'sprint_speed', None),
            # 'onbase_plus_slugging_plus': self._extract_ops_plus(hitting_stats),
        }
        return NormalizedPlayerStats(**normalized_data)
    
    @staticmethod
    def from_bref_data(bref_data: Dict[str, Any]) -> NormalizedPlayerStats:
        """Normalizes stats from Baseball Reference data"""
        # Implementation would extract and map fields from bref_data to NormalizedPlayerStats
        # This is a placeholder for the actual normalization logic
        normalized_stats = NormalizedPlayerStats(primary_datasource=PrimaryDatasource.BREF, **bref_data)
        return normalized_stats

    # Helper methods for normalization

    @staticmethod
    def _extract_year_id_from_seasons(seasons: list[int | str]) -> str | int:
        """Extracts the year ID from the seasons list"""
        if not seasons or len(seasons) == 0:
            raise ValueError("Seasons list is empty.")
        
        if len(seasons) == 1:
            season = seasons[0]
            if isinstance(season, str) and season.isdigit():
                return int(season)
            else:
                return season
        else:
            return ",".join(str(s) for s in seasons)

    @staticmethod
    def _mlb_api_determine_player_type(primary_position: Position) -> Optional[str]:
        """Determines if player is a Hitter or Pitcher based on stats"""
        if primary_position is None:
            return None
        if primary_position and primary_position.code == '1':
            return PlayerType.PITCHER.value
        return PlayerType.HITTER.value

    @staticmethod
    def _extract_position_stats(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> Optional[Dict[str, Dict[str, Any]]]:
        """Extracts position stats from MLB Stats API Player model.
        
        Final structure:
        {'SS': {'g': 120, 'tzr': 5.3, 'drs': 10, 'oaa': 8, 'uzr': 12.4}, ...}

        Args:
            mlb_player (MLBStatsApi_Player): The MLB Stats API Player model

        Returns:
            Dict[str, Dict[str, Any]]: Mapping of position abbr to their defensive stats
        """

        stats_type = StatTypeEnum.CAREER if stats_period.is_full_career else StatTypeEnum.YEAR_BY_YEAR

        # Get fielding data for season(s)
        fielding_stat_splits = mlb_player.get_stat_splits(
            group_type=StatGroupEnum.FIELDING,
            type=stats_type,
            seasons=stats_period.year_list
        )

        if not fielding_stat_splits or len(fielding_stat_splits) == 0:
            print("No fielding stats available.")
            return None  # No stats available

        converted_stats: Dict[str, Dict[str, Any]] = {}
        for split in fielding_stat_splits:

            # Check for position data
            stats = split.stat
            position = stats.get('position', None) if stats else None
            if not position:
                print("No position found in fielding stats split.")
                continue
            try:
                position = Position(**position)
            except Exception as e:
                print(f"Error creating Position object: {e}")
                continue
            
            # Get required stats
            games_played = stats.get('gamesPlayed', 0)

            if position.abbreviation not in converted_stats:
                converted_stats[position.abbreviation] = {
                    'g': games_played,
                    # 'tzr': 0.0, TODO: ADD FROM ANOTHER SOURCE
                    # 'drs': 0.0,
                    # 'oaa': 0.0,
                    # 'uzr': 0.0,
                }
                continue
            current_stats = converted_stats[position.abbreviation]
            current_stats['g'] += games_played
            converted_stats[position.abbreviation] = current_stats

        return converted_stats

    @staticmethod
    def _extract_standard_stats(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> Dict[str, Any]:
        """Extracts standard stats from a MLBStatsPlayer stat splits"""

        stats_type = StatTypeEnum.CAREER if stats_period.is_full_career else StatTypeEnum.YEAR_BY_YEAR
        group_type = StatGroupEnum.HITTING if mlb_player.primary_position and mlb_player.primary_position.player_type == PlayerType.HITTER else StatGroupEnum.PITCHING
        standard_stat_splits = mlb_player.get_stat_splits(
            group_type=group_type,
            type=stats_type,
            seasons=stats_period.year_list
        )

        # Combine stats from all splits
        standard_stats: Dict[str, Any] = {}
        if not standard_stat_splits or len(standard_stat_splits) == 0:
            print("No standard stats available.")
            return standard_stats  # No stats available
        
        stat_name_mapping = PlayerStatsNormalizer._map_mlb_api_stats_to_bref()
        stat_type_mapping = PlayerStatsNormalizer._stat_datatype_dict()
        for split in standard_stat_splits:
            stats = split.stat
            if not stats:
                continue
            for key, value in stats.items():

                # Normalize stat name and type
                stat_key_normalized = stat_name_mapping.get(key, key)

                # Pass on stats if not a key in NormalizedPlayerStats
                if stat_key_normalized not in NormalizedPlayerStats.all_valid_field_names():
                    print(f"Skipping unrecognized stat key: {stat_key_normalized}")
                    continue

                try:
                    stat_value_converted = stat_type_mapping.get(stat_key_normalized, int)(value)
                    # Limit to 4 decimal places for floats
                    if isinstance(stat_value_converted, float):
                        stat_value_converted = round(stat_value_converted, 4)
                except Exception as e:
                    print(f"Error converting stat '{stat_key_normalized}': {e}")
                    stat_value_converted = str(value)
                
                if stat_key_normalized not in standard_stats:
                    standard_stats[stat_key_normalized] = stat_value_converted
                else:
                    # Sum numeric stats
                    if isinstance(stat_value_converted, (int, float)):
                        standard_stats[stat_key_normalized] += stat_value_converted
                    # For non-numeric stats, you might want to handle differently
                    # e.g., take the latest value, average, etc. Here we skip.

        return standard_stats
    
    @staticmethod
    def _map_mlb_api_stats_to_bref() -> Dict[str, str]:
        """Maps MLB Stats API stat keys to Baseball Reference stat keys"""
        return {
            'atBats': 'AB',
            'baseOnBalls': 'BB',
            'battersFaced': 'batters_faced',
            'caughtStealing': 'CS',
            'doubles': '2B',
            'earnedRuns': 'ER',
            'era': 'earned_run_avg',
            'gamesPlayed': 'G',
            'gamesStarted': 'GS',
            'groundIntoDoublePlay': 'GIDP',
            'groundOutsToAirouts': 'GO/AO',
            'hitByPitch': 'HBP',
            'hits': 'H',
            'homeRuns': 'HR',
            'inningsPitched': 'IP',
            'intentionalWalks': 'IBB',
            'plateAppearances': 'PA',
            'rbi': 'RBI',
            'runs': "R",
            'sacBunts': 'SH',
            'sacFlies': 'SF',
            'saves': 'SV',
            'stolenBases': 'SB',
            'strikeOuts': 'SO',
            'totalBases': 'TB',
            'triples': '3B',
            'whip': 'whip',

            # Slashline
            'avg': 'batting_avg',
            'slg': 'slugging_perc',
            'obp': 'onbase_perc',
            'ops': 'onbase_plus_slugging',
        }
    
    @staticmethod
    def _stat_datatype_dict() -> dict[str, str]:
        """
        Maps the normalized stat keys to their data types
        """
        return {
            'batting_avg': float,
            'onbase_perc': float,
            'onbase_plus_slugging': float,
            'slugging_perc': float,
            'earned_run_avg': float,
            'whip': float,
            'IP': float,
            'GO/AO': float,
            'date': str,  # Date is stored as a string in the format YYYY-MM-DD
        }

# -------------------------------
# MARK: - Supporting Models
# -------------------------------

class PositionStats(BaseModel):
    """Defensive stats for a specific position"""
    
    g: int = 0  # Games played at position
    tzr: Optional[float] = None  # Total Zone Rating
    drs: Optional[float] = None  # Defensive Runs Saved
    oaa: Optional[float] = None  # Outs Above Average
    uzr: Optional[float] = None  # Ultimate Zone Rating
    
class BaseGameLog(BaseModel):
    """Base game log model"""
    
    date: str  # Keep as string to match your format
    team_ID: str
    player_game_span: str  # e.g., "CG", "GS-8", "CG(10)"
    
    # Game stats
    PA: int = 0
    AB: int = 0
    R: int = 0
    H: int = 0
    doubles: int = Field(0, alias='2B')
    triples: int = Field(0, alias='3B')
    HR: int = 0
    RBI: int = 0
    SB: int = 0
    CS: int = 0
    BB: int = 0
    SO: int = 0
    HBP: int = 0
    SF: int = 0
    SH: int = 0
    GIDP: int = 0
    IBB: int = 0

class GameLog(BaseGameLog):
    """Regular season game log"""
    pass

class PostseasonGameLog(BaseGameLog):
    """Postseason game log"""
    pass

class Hand(str, Enum):

    RIGHT = "Right"
    LEFT = "Left"
    SWITCH = "Both"

    # Handle conditional logic for other formats if needed
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            match value.upper():
                case 'SWITCH' | 'BOTH' | 'S':
                    return cls.SWITCH
        return None