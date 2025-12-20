from pydantic import BaseModel, Field, field_serializer
from typing import Any, Dict, Optional, List, Set
from enum import Enum
from pprint import pprint

from ...mlb_stats_api.models.person import Position, Player as MLBStatsApi_Player, StatGroupEnum, StatTypeEnum, StatSplit
from ...fangraphs.models import FieldingStats
from ...shared.player_position import PlayerType
from ..utils.shared_functions import fill_empty_stat_categories, convert_number_to_ordinal
from ...card.stats.stats_period import StatsPeriod, StatsPeriodYearType

# -------------------------------
# MARK: - Primary Datasources 
# -------------------------------
class Datasource(str, Enum):
    MLB_API = "mlb_api"
    BREF = "bref"
    FANGRAPHS = "fangraphs"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            match value.lower():
                case 'mlb_api' | 'mlb' | 'mlbstatsapi':
                    return cls.MLB_API
                case 'bref' | 'baseball_reference' | 'baseballreference':
                    return cls.BREF
                case 'fangraphs' | 'fg':
                    return cls.FANGRAPHS
        return cls.BREF # Default to BREF if unrecognized

# -------------------------------
# MARK: - Normalized Player Stats Model
# -------------------------------
class NormalizedPlayerStats(BaseModel):
    """Creates a shared structure for player stats across different sources"""

    # Identity & Metadata
    primary_datasource: Datasource
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

    # Pitching Stats
    W: int = 0
    L: int = 0
    GS: int = 0
    IP: float = 0.0
    ER: int = 0
    earned_run_avg: Optional[float] = None
    whip: Optional[float] = None
    SV: int = 0
    batters_faced: Optional[int] = None
    outs: Optional[int] = None
    
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
    defense_datasource: Optional[Datasource] = None
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
    is_stats_estimated: bool = False

    @field_serializer('primary_datasource')
    def serialize_primary_datasource(self, value: Datasource) -> str:
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
    
    def inject_defensive_stats_list(self, position_stats_list: List['PositionStats'], source: Datasource) -> None:
        """Injects defensive stats from a list of PositionStats into the positions field. Updates defense datasource as well."""
        if not position_stats_list or len(position_stats_list) == 0:
            return
        
        # RESET ALL POSITIONS EXCEPT PITCHER AND DH
        self.positions = {k: v for k, v in (self.positions or {}).items() if k in ['P', 'DH']}
        
        for pos_stats in position_stats_list:
            self.positions[pos_stats.position] = pos_stats

        self.defense_datasource = source

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
        player_type = PlayerStatsNormalizer._mlb_api_determine_player_type(player.primary_position)
        normalized_data = {
            # Identity
            'primary_datasource': Datasource.MLB_API,
            'mlb_id': player.id,

            'name': player.full_name,
            'year_ID': stats_period.year,
            'team_ID': PlayerStatsNormalizer.extract_team_id(player, stats_period),
            'lg_ID': PlayerStatsNormalizer._extract_league_id(player, stats_period),
            'type': player_type,
            'hand': Hand(player.bat_side.description).value,
            'hand_throw': Hand(player.pitch_hand.description).value,
            
            # Standard stats
            **PlayerStatsNormalizer._extract_standard_stats(player, stats_period),
            
            # Defensive stats
            'positions': PlayerStatsNormalizer._extract_position_stats(player, stats_period),

            # Missing
            'outs_above_avg': {}, # TODO: Extract from Statcast data
            'sprint_speed': None, # Extracted later from statcase
            'accolades': PlayerStatsNormalizer._convert_mlb_stats_awards_and_ranks_to_accolades_dict(player, stats_period),
            
            # # Advanced metrics
            # 'sprint_speed': getattr(mlb_player, 'sprint_speed', None),
            # 'onbase_plus_slugging_plus': self._extract_ops_plus(hitting_stats),
        }

        # FILL IN EMPTY VALUES
        normalized_data = fill_empty_stat_categories(
            stats_data=normalized_data,
            is_pitcher=player_type == PlayerType.PITCHER.value,
            is_game_logs=False
        )

        normalized_player_stats = NormalizedPlayerStats(**normalized_data)
        return normalized_player_stats
    
    @staticmethod
    def from_bref_data(bref_data: Dict[str, Any]) -> NormalizedPlayerStats:
        """Normalizes stats from Baseball Reference data"""
        # Implementation would extract and map fields from bref_data to NormalizedPlayerStats
        # This is a placeholder for the actual normalization logic
        normalized_stats = NormalizedPlayerStats(primary_datasource=Datasource.BREF, **bref_data)
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

        stats_type = StatTypeEnum.CAREER if stats_period.is_full_career else StatTypeEnum.STATS_SINGLE_SEASON

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

        stats_type = PlayerStatsNormalizer._primary_stats_type(stats_period.year_type)
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

                # NORMALIZE STAT NAME AND TYPE
                stat_key_normalized = stat_name_mapping.get(key, key)
                is_non_counting_metric = stat_key_normalized in [
                    'batting_avg', 'onbase_perc', 'slugging_perc', 
                    'onbase_plus_slugging', 'earned_run_avg', 'whip', 'IP', 'GO/AO'
                ]

                # PASS ON STATS IF NOT A KEY IN NORMALIZEDPLAYERSTATS
                if stat_key_normalized not in NormalizedPlayerStats.all_valid_field_names():
                    # print(f"Skipping unrecognized stat key: {stat_key_normalized}")
                    continue

                # PASS IF MULTIPLE SPLITS AND THIS IS A NON-COUNTING METRIC
                # ONCE SPLITS ARE COMBINED, THESE METRICS WILL BE RECALCULATED
                if is_non_counting_metric and len(standard_stat_splits) > 1:
                    # print(f"Skipping non-counting metric for multiple splits: {stat_key_normalized}")
                    continue

                try:
                    stat_value_converted = stat_type_mapping.get(stat_key_normalized, int)(value)
                    # LIMIT TO 4 DECIMAL PLACES FOR FLOATS
                    if isinstance(stat_value_converted, float):
                        stat_value_converted = round(stat_value_converted, 4)
                except Exception as e:
                    print(f"Error converting stat '{stat_key_normalized}': {e}")
                    stat_value_converted = str(value)
                
                if stat_key_normalized not in standard_stats:
                    # STAT IS NOT YET IN DICT
                    standard_stats[stat_key_normalized] = stat_value_converted
                else:
                    # Sum numeric stats
                    if isinstance(stat_value_converted, (int, float)):
                        standard_stats[stat_key_normalized] += stat_value_converted
                    # For non-numeric stats, you might want to handle differently
                    # e.g., take the latest value, average, etc. Here we skip.

        return standard_stats

    @staticmethod
    def extract_team_id(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> Optional[str]:
        """Extracts the team ID for the player in the given stats period"""
        stats_type = PlayerStatsNormalizer._primary_stats_type(stats_period.year_type)
        group_type = StatGroupEnum.HITTING if mlb_player.primary_position and mlb_player.primary_position.player_type == PlayerType.HITTER else StatGroupEnum.PITCHING
        standard_stat_splits = mlb_player.get_stat_splits(
            group_type=group_type,
            type=stats_type,
            seasons=stats_period.year_list
        )

        if not standard_stat_splits or len(standard_stat_splits) == 0:
            print("No standard stats available.")
            return None  # No stats available
        
        # Get team with most games played
        team_games_played: Dict[str, int] = {}
        for split in standard_stat_splits:
            team = split.team
            if team and team.abbreviation:
                games_played = split.stat.get('gamesPlayed', 0)
                team_games_played[team.abbreviation] = team_games_played.get(team.abbreviation, 0) + games_played

        if not team_games_played:
            print("No team games played data available.")
            return None

        # Return the team with the most games played
        return max(team_games_played, key=team_games_played.get)

    @staticmethod
    def _extract_league_id(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> Optional[str]:
        """Get corresponding league ID for the player in the given stats period"""

        primary_team_id = PlayerStatsNormalizer.extract_team_id(mlb_player, stats_period)
        if not primary_team_id:
            return None
        
        # GET STAT SPLITS
        # FIND THE TEAM MATCHING THE PRIMARY TEAM ID
        # RETURN THE FIRST (WILL BE LATEST YEAR'S) LEAGUE ABBREVIATION
        stats_type = PlayerStatsNormalizer._primary_stats_type(stats_period.year_type)
        group_type = StatGroupEnum.HITTING if mlb_player.primary_position and mlb_player.primary_position.player_type == PlayerType.HITTER else StatGroupEnum.PITCHING
        standard_stat_splits = mlb_player.get_stat_splits(
            group_type=group_type,
            type=stats_type,
            seasons=stats_period.year_list
        )
        for split in standard_stat_splits:
            team = split.team
            if team and team.abbreviation == primary_team_id:
                if team.league and team.league.abbreviation:
                    return team.league.abbreviation
                
        return None

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
            'losses': 'L',
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
            'wins': 'W',
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

    @staticmethod
    def _primary_stats_type(stats_period_type: StatsPeriodYearType) -> StatTypeEnum:
        """Returns a string representation of the stats period year type"""
        match stats_period_type:
            case StatsPeriodYearType.SINGLE_YEAR:
                return StatTypeEnum.STATS_SINGLE_SEASON
            case StatsPeriodYearType.FULL_CAREER:
                return StatTypeEnum.CAREER
            case StatsPeriodYearType.MULTI_YEAR:
                return StatTypeEnum.STATS_SINGLE_SEASON
            case _:
                return StatTypeEnum.STATS_SINGLE_SEASON

    @staticmethod
    def _convert_mlb_stats_awards_and_ranks_to_accolades_dict(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> Dict[str, List[str]]:
        """Converts MLB Stats API awards and ranks into accolades dictionary"""
        
        # FINAL DICT
        accolades: Dict[str, List[str]] = {}

        # MLB STATS RANKINGS ARE STORED AS STAT SPLITS
        stats_type = StatTypeEnum.RANKINGS_BY_YEAR
        group_type = StatGroupEnum.HITTING if mlb_player.primary_position and mlb_player.primary_position.player_type == PlayerType.HITTER else StatGroupEnum.PITCHING
        rankings_by_year = mlb_player.get_stat_splits(
            group_type=group_type,
            type=stats_type,
            seasons=stats_period.year_list
        )

        # MLB STATS API WILL RETURN 2 SPLITS FOR YEARS
        # FILTER TO ONE PER YEAR
        deduped_rankings_by_year: List[StatSplit] = []
        for split in rankings_by_year:
            if any(existing_split.season == split.season for existing_split in deduped_rankings_by_year):
                continue
            deduped_rankings_by_year.append(split)

        # CONVERT TO ACCOLADES DICT
        map_stat_names = PlayerStatsNormalizer._map_mlb_api_stats_to_bref()
        for split in deduped_rankings_by_year:
            
            stats = split.stat
            if not stats:
                continue
            
            for key, value in stats.items():

                try: rank_value = int(value)
                except: continue

                stat_key_normalized = map_stat_names.get(key, key)
                existing_accolades_for_stat = accolades.get(stat_key_normalized, [])
                                
                ordinal_rank = convert_number_to_ordinal(rank_value).upper()

                # CONVERT TO STRING
                # EX: "2025 AL (7TH)"
                league_abbr = split.team.league.abbreviation if split.team and split.team.league else "N/A"
                accolade_str = f"{split.season} {league_abbr} ({ordinal_rank})"
                existing_accolades_for_stat.append(accolade_str)
                accolades[stat_key_normalized] = existing_accolades_for_stat

        return accolades


# -------------------------------
# MARK: - Supporting Models
# -------------------------------

class PositionStats(BaseModel):
    """Defensive stats for a specific position"""
    
    g: int = 0  # Games played at position
    innings: Optional[float] = None  # Innings played at position
    position: Optional[str] = None  # Position abbreviation. Sometimes wont be included if part of dictionary with key (ex: {"SS": {...}})

    # METRICS
    tzr: Optional[float] = None  # Total Zone Rating
    drs: Optional[float] = None  # Defensive Runs Saved
    oaa: Optional[float] = None  # Outs Above Average
    uzr: Optional[float] = None  # Ultimate Zone Rating

    @staticmethod
    def from_fangraphs_fielding_stats(fangraphs_stats: FieldingStats) -> 'PositionStats':
        """Creates PositionStats from Fangraphs FieldingStats model"""
        return PositionStats(
            g=int(fangraphs_stats.games) if fangraphs_stats.games is not None else 0,
            innings=float(fangraphs_stats.innings) if fangraphs_stats.innings is not None else None,
            position=fangraphs_stats.position,
            tzr=float(fangraphs_stats.tz) if fangraphs_stats.tz is not None else None,
            drs=float(fangraphs_stats.drs) if fangraphs_stats.drs is not None else None,
            oaa=float(fangraphs_stats.oaa) if fangraphs_stats.oaa is not None else None,
            uzr=float(fangraphs_stats.uzr) if fangraphs_stats.uzr is not None else None,
        )
    
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