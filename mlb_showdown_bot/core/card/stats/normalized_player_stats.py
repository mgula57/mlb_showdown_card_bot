from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Any, Dict, Optional, List, Set
from enum import Enum
from pprint import pprint

from ...mlb_stats_api.models.person import Position, Player as MLBStatsApi_Player, StatGroupEnum, StatTypeEnum, StatSplit
from ...fangraphs.models import FieldingStats, LeaderboardStats
from ...shared.player_position import PlayerType
from ...shared.hand import Hand
from ..utils.shared_functions import fill_empty_stat_categories, convert_number_to_ordinal, total_innings_pitched, total_ip_for_calculations
from ...card.stats.stats_period import StatsPeriod, StatsPeriodType, StatsPeriodYearType, StatsPeriodLeague
from .datasource import Datasource

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
    team_override: Optional[str] = None  # Manually override team if needed
    lg_ID: Optional[str] = None
    
    # Player Type & Physical
    type: PlayerType  # "Hitter" or "Pitcher"
    player_type_override: Optional[PlayerType] = None  # Manually override player type if needed
    hand: Optional[Hand] = None  # "Left", "Right", "Both"
    hand_throw: Optional[Hand] = None  # "Left", "Right"
    
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
    IP_GS: Optional[float] = Field(None, alias='IP/GS')
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
    onbase_plus_slugging_plus: Optional[int | float] = None  # OPS+
    wrc_plus: Optional[float] = Field(None, alias='wRcPlus') 
    
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
    fWAR: Optional[float] = None
    
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

    def model_post_init(self, __context):
        
        # FILL IN MISSING ER FOR PITCHERS
        # DIDN'T START STORING THAT DATA UNTIL 2024
        # DERIVE FROM ERA AND IP IF MISSING
        try:
            if self.type == PlayerType.PITCHER and self.earned_run_avg is not None and self.IP and self.IP > 0:
                if self.ER is None or self.ER == 0:
                    self.ER = int(round((self.earned_run_avg * total_ip_for_calculations(self.IP)) / 9))
        except Exception as e:
            print(f"Error calculating ER from ERA and IP: {e}")
            pass

    @field_serializer('primary_datasource')
    def serialize_primary_datasource(self, value: Datasource) -> str:
        """Serialize enum to its string value"""
        return value.value if value else None

    @field_validator('pos_season', mode='before')
    def validate_pos_season(cls, value) -> str:
        """Ensures pos_season is always a string, defaults to empty string if None"""
        return str(value) if value is not None else None
    
    @field_validator('dWAR', 'bWAR', 'age', 'earned_run_avg', mode='before')
    def validate_empty_stats(cls, value) -> float:
        """Defaults dWAR, bWAR, and age to None if empty string"""
        return None if value is not None and (str(value) == '' or str(value) == '--' or str(value) == '-.--') else value

    @field_validator('PA', 'AB', mode='before')
    def validate_counting_ints(cls, value) -> int:
        """Defaults counting ints to None if empty string"""
        if value is None:
            return None
        
        if str(value) == '':
            return None
        
        return int(value)
    
    @field_validator('SB', 'RBI', mode='before')
    def validate_zeroed_out_stats(cls, value) -> int:
        """Sets stats that are zero to None to indicate missing data"""
        if value is None:
            return 0
        
        if str(value) == '' or str(value) == '--':
            return 0
        
        return int(value)

    @field_validator('go_ao_ratio', 'if_fb_ratio', mode='before')
    def validate_advanced_ratios(cls, value) -> float:
        """Defaults advanced ratios to None if empty string"""
        if value is None:
            return None
        
        if str(value) == '' or str(value) == '-.--':
            return None
        
        return float(value)

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

    def inject_statcast_oaa(self, oaa_stats: Dict[str, float]) -> None:
        """Injects statcast Outs Above Average (OAA) defensive stats into existing PositionStats. This is used to merge the two sources of defensive metrics since they often have different coverage."""
        if not oaa_stats or len(oaa_stats) == 0:
            return
        
        if not self.positions:
            return

        for pos, oaa in oaa_stats.items():
            if pos in self.positions:
                self.positions[pos].oaa = oaa

    def as_dict(self) -> Dict[str, Any]:
        """Returns a dictionary representation of the model, including aliases"""
        return self.model_dump(by_alias=True, exclude_none=True, exclude_unset=True)

    def add_bref_id(self, bref_id: Optional[str]) -> None:
        """Adds a Baseball Reference ID to the model"""
        if not bref_id:
            return
        self.bref_id = bref_id
        self.bref_url = f"https://www.baseball-reference.com/players/{bref_id[0]}/{bref_id}.shtml"

    @property
    def is_missing_stats(self) -> bool:
        """Determines if the player is missing core stats (e.g., G, PA, IP) which may indicate incomplete data"""
        if not self.type:
            return True
        match self.type:
            case PlayerType.HITTER:
                return not self.G and not self.PA
            case PlayerType.PITCHER:
                return not self.GS and not self.IP
            
        return False

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
        player_type = PlayerStatsNormalizer._mlb_api_determine_player_type(player.primary_position, stats_period)
        player_type_override = stats_period.player_type_override if stats_period else None
        normalized_data = {
            # Identity
            'primary_datasource': Datasource.MLB_API,
            'mlb_id': player.id,

            'name': player.full_name,
            'year_ID': stats_period.year,
            'team_ID': PlayerStatsNormalizer.extract_team_id(player, stats_period),
            'lg_ID': PlayerStatsNormalizer._extract_league_id(player, stats_period),
            'type': player_type,
            'player_type_override': player_type_override,
            'hand': Hand(player.bat_side.description).value,
            'hand_throw': Hand(player.pitch_hand.description).value,
            
            # Standard stats
            **PlayerStatsNormalizer._extract_standard_stats(player, stats_period),
            
            # Defensive stats
            'positions': PlayerStatsNormalizer._extract_position_stats(player, stats_period),

            # Missing
            'outs_above_avg': {}, # TODO: Extract from Statcast data
            'sprint_speed': None, # Extracted later from statcast
            'accolades': PlayerStatsNormalizer._convert_mlb_stats_awards_and_ranks_to_accolades_dict(player, stats_period),
            'is_rookie': PlayerStatsNormalizer._determine_rookie_status(player, stats_period),
            'award_summary': PlayerStatsNormalizer._build_award_summary_str(player, stats_period),
            'is_above_w_threshold': PlayerStatsNormalizer._determine_20_game_winner(player, stats_period),

            # # Advanced metrics
            # 'sprint_speed': getattr(mlb_player, 'sprint_speed', None),
            # 'onbase_plus_slugging_plus': self._extract_ops_plus(hitting_stats),
        }

        # TYPE BASED ADDITIONS
        if player_type == PlayerType.PITCHER.value:
            # LOOK WITHIN STAT SPLITS FOR IP/GS
            gs_ip = PlayerStatsNormalizer._extract_ip_per_gs(player, stats_period)
            if gs_ip:
                normalized_data['IP/GS'] = gs_ip

        # ADD GAME LOGS
        if stats_period.year_type == StatsPeriodYearType.SINGLE_YEAR:
            normalized_data['game_logs'] = PlayerStatsNormalizer._extract_game_logs(player, stats_period)

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

    @staticmethod
    def from_fangraphs_leaderboard_data(fg_data: LeaderboardStats, mlb_id: Optional[int] = None, hand: Optional[Hand] = None, hand_throw: Optional[Hand] = None) -> NormalizedPlayerStats:
        """Normalizes stats from a Fangraphs leaderboard record"""
        # Implementation would extract and map fields from record to NormalizedPlayerStats
        # This is a placeholder for the actual normalization logic
        player_type = PlayerType.PITCHER if fg_data.is_pitcher else PlayerType.HITTER
        normalized_data = {
            # Identity
            'primary_datasource': Datasource.FANGRAPHS,
            'mlb_id': mlb_id,
            'player_type': player_type,

            'name': fg_data.player_name,
            'year_ID': fg_data.season,
            'team_ID': 'MLB',  # Fangraphs doesn't always provide team info in leaderboard data, so default to MLB
            'lg_ID': fg_data.league,
            'type': player_type.value,
            'hand': hand.value if hand else Hand.RIGHT.value,  # Fangraphs doesn't provide handedness in leaderboard data, so default to Right
            'hand_throw': hand_throw.value if hand_throw else Hand.RIGHT.value,  # Fangraphs doesn't provide throwing hand in leaderboard data, so default to Right
            
            # Required stats
            **PlayerStatsNormalizer._extract_standard_stats_from_fangraphs_leaderboard(fg_data),
            
            # Defensive stats
            'positions': PlayerStatsNormalizer._create_generic_position_stats_from_list(positions=fg_data.positions, games=fg_data.g or 0),

            # Missing
            'outs_above_avg': {}, # Doesn't Exist in Fangraphs leaderboard data 
            'sprint_speed': None, # Doesn't Exist in Fangraphs leaderboard data
            'accolades': {},
            'is_rookie': False, # Doesn't Exist in Fangraphs leaderboard data
            'award_summary': '',
            'is_above_w_threshold': False, # Doesn't Exist in Fangraphs leaderboard data
        }
        # FILL IN EMPTY VALUES
        normalized_data = fill_empty_stat_categories(
            stats_data=normalized_data,
            is_pitcher=player_type.is_pitcher,
            is_game_logs=False
        )

        normalized_player_stats = NormalizedPlayerStats(**normalized_data)
        return normalized_player_stats

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
    def _mlb_api_determine_player_type(primary_position: Position, stats_period: StatsPeriod) -> Optional[str]:
        """Determines if player is a Hitter or Pitcher based on stats"""
        if stats_period and stats_period.player_type_for_mlb_api(primary_position.abbreviation):
            return stats_period.player_type_for_mlb_api(primary_position.abbreviation)
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
            types=[stats_type],
            seasons=stats_period.year_list
        )

        # For pitchers, use games pitched from the standard stats split to fill in positions if no fielding splits are available, since many pitchers won't have fielding stats but we can assume they played pitcher for any games they pitched in
        if mlb_player.is_pitcher and (not fielding_stat_splits or len(fielding_stat_splits) == 0):
            pitching_standard_stats = mlb_player.get_stat_splits(
                group_type=StatGroupEnum.PITCHING,
                types=[stats_type],
                seasons=stats_period.year_list
            )
            games_pitched = 0
            for split in (pitching_standard_stats or []):
                stats = split.stat
                if stats and 'gamesPitched' in stats:
                    games_pitched += stats['gamesPitched']
            if games_pitched > 0:
                return {
                    'P': {
                        'g': games_pitched,
                        # 'tzr': None,
                        'drs': 0,
                        # 'oaa': None,
                        # 'uzr': None,
                    }
                }

        if not mlb_player.is_pitcher and (not fielding_stat_splits or len(fielding_stat_splits) == 0):
            
            # FIELDING STATS FOR MINOR LEAGUERS PRE ~2007 DOES NOT EXIST. FILL WITH PRIMARY POSITION AND GAMES PLAYED IF AVAILABLE
            if not stats_period.is_mlb and mlb_player.primary_position and stats_period.last_year < 2007:
                primary_position = mlb_player.primary_position.abbreviation
                if primary_position and stats_period.year_type == StatsPeriodYearType.SINGLE_YEAR:
                    standard_stats = mlb_player.get_stat_splits(
                        group_type=StatGroupEnum.HITTING,
                        types=[stats_type],
                        seasons=stats_period.year_list
                    )
                    games_played = 0
                    for split in (standard_stats or []):
                        stats = split.stat
                        if stats and 'gamesPlayed' in stats:
                            games_played += stats['gamesPlayed']
                    if games_played > 0:
                        return PlayerStatsNormalizer._create_generic_position_stats_from_list(positions=[primary_position], games=games_played)

            return None  # No stats available

        converted_stats: Dict[str, Dict[str, Any]] = {}
        unique_sport_ids = list(set([split.sport.id for split in fielding_stat_splits if split.sport]))
        for split in (fielding_stat_splits or []):

            # Check for position data
            stats = split.stat

            # IF THERE ARE MULTIPLE SPLITS AND SOME HAVE TEAM AND ANOTHER IS OVERALL, TAKE THE OVERALL SPLIT
            if len(fielding_stat_splits) > 1 and split.team and any(s.team is None for s in fielding_stat_splits):
                continue

            # SKIP NON-TOTAL SPLITS WHEN A MINOR LEAGUE TOTAL ROW EXISTS
            minor_total_sport_id = 21
            if len(unique_sport_ids) > 1 and split.sport and minor_total_sport_id in unique_sport_ids and split.sport.id != minor_total_sport_id:
                continue

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

            # Add fielding percent if MILB
            fielding_pct = stats.get('fielding', None) if position.abbreviation != 'DH' else None
            if fielding_pct is not None:
                try: fielding_pct = float(fielding_pct)
                except: fielding_pct = None

            if position.abbreviation not in converted_stats:
                converted_stats[position.abbreviation] = {
                    'g': games_played,
                    'fld_pct': fielding_pct,
                    # 'tzr': 0.0, ADDED FROM FANGRAPHS LATER
                    # 'drs': 0.0,
                    # 'oaa': 0.0,
                    # 'uzr': 0.0,
                }
                continue
            current_stats = converted_stats[position.abbreviation]
            current_stats['g'] += games_played
            converted_stats[position.abbreviation] = current_stats

        # MAKE COMBINED `OF` POSITION IF PLAYER HAS CF AND LF OR RF, SINCE BREF USED TO COMBINE THEM INTO ONE POSITION
        # DO A WEIGHTED AVERAGE FOR FIELDING PCT IF AVAILABLE
        of_positions = [p for p in ('CF', 'LF', 'RF') if p in converted_stats]
        if len(of_positions) > 1:
            of_games = sum(converted_stats[p]['g'] for p in of_positions)
            pct_and_games = [(converted_stats[p]['fld_pct'], converted_stats[p]['g']) for p in of_positions if converted_stats[p].get('fld_pct') is not None]
            games_with_pct = sum(g for _, g in pct_and_games)
            of_fld_pct = round(sum(pct * g for pct, g in pct_and_games) / games_with_pct, 4) if games_with_pct > 0 else None
            converted_stats['OF'] = {'g': of_games, 'fld_pct': of_fld_pct}

        return converted_stats

    @staticmethod
    def _create_generic_position_stats_from_list(positions: List[str], games: int) -> Dict[str, Dict[str, Any]]:
        """Creates a generic position stats dict from a list of position abbreviations. Used when we don't have actual defensive metrics but want to populate the positions field."""
        position_stats = {}
        for pos in positions:
            position_stats[pos] = {
                'g': games,
                # 'tzr': None,
                'drs': 0,
                # 'oaa': None,
                # 'uzr': None,
            }
        return position_stats

    @staticmethod
    def _extract_standard_stats(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> Dict[str, Any]:
        """Extracts standard stats from a MLBStatsPlayer stat splits.
        
        Fetches each StatType separately and merges results to avoid double-counting stats
        that appear in multiple types (e.g. statsSingleSeason + statsSingleSeasonAdvanced).
        The primary stat type wins for any overlapping keys; subsequent types only contribute
        keys not already present. Counting stats are still summed across years/teams within
        each stat type.
        """

        is_pitcher = stats_period.player_type_for_mlb_api(mlb_player.primary_position.abbreviation) == PlayerType.PITCHER if stats_period else mlb_player.is_pitcher
        stats_types = [PlayerStatsNormalizer._primary_stats_type(stats_period.year_type)] \
                        + ([StatTypeEnum.STATS_SINGLE_SEASON_ADVANCED] if is_pitcher else []) \
                        + [StatTypeEnum.SABERMETRICS]
        group_type = StatGroupEnum.PITCHING if is_pitcher else StatGroupEnum.HITTING

        stat_name_mapping = PlayerStatsNormalizer._map_mlb_api_stats_to_bref()
        stat_type_mapping = PlayerStatsNormalizer._stat_datatype_dict()

        # PROCESS EACH STAT TYPE INDEPENDENTLY, THEN MERGE
        # This prevents double-counting fields shared across stat types (e.g. GS, SB, 2B)
        # while still summing correctly across teams/years within each type.
        combined_stats: Dict[str, Any] = {}

        for stats_type in stats_types:
            splits = mlb_player.get_stat_splits(
                group_type=group_type,
                types=[stats_type],
                seasons=stats_period.year_list
            )
            if not splits:
                continue

            unique_sport_ids = list(set([split.sport.id for split in splits if split.sport]))
            ip_splits: List[float] = []
            type_stats: Dict[str, Any] = {}

            # ACCUMULATE RAW BATTED BALL COUNTS FOR IF/FB (keys not in NormalizedPlayerStats)
            popup_total = flyball_total = linedrive_total = 0

            for split in splits:
                stats = split.stat
                if not stats:
                    continue

                # IF THERE ARE MULTIPLE SPLITS AND SOME HAVE TEAM AND ANOTHER IS OVERALL, TAKE THE OVERALL SPLIT
                if len(splits) > 1 and split.team and any(s.team is None for s in splits):
                    continue

                # SKIP NON-TOTAL SPLITS WHEN A MINOR LEAGUE TOTAL ROW EXISTS
                minor_total_sport_id = 21
                if len(unique_sport_ids) > 1 and split.sport and minor_total_sport_id in unique_sport_ids and split.sport.id != minor_total_sport_id:
                    continue

                # ACCUMULATE BATTED BALL COUNTS FOR IF/FB CALCULATION
                if is_pitcher:
                    popup_total += stats.get('popOuts', 0) + stats.get('popHits', 0)
                    flyball_total += stats.get('flyOuts', 0) + stats.get('flyHits', 0)
                    linedrive_total += stats.get('lineOuts', 0) + stats.get('lineHits', 0)

                for key, value in stats.items():

                    # NORMALIZE STAT NAME AND TYPE
                    stat_key_normalized = stat_name_mapping.get(key, key)
                    is_non_counting_metric = stat_key_normalized in [
                        'batting_avg', 'onbase_perc', 'slugging_perc',
                        'onbase_plus_slugging', 'earned_run_avg', 'whip',
                    ]

                    # SKIP STATS NOT IN NORMALIZEDPLAYERSTATS
                    if stat_key_normalized not in NormalizedPlayerStats.all_valid_field_names():
                        continue

                    # SKIP NON-COUNTING METRICS WHEN MULTIPLE SPLITS EXIST
                    # THEY WILL BE RECALCULATED AFTER SUMMING COUNTING STATS
                    if is_non_counting_metric and len(splits) > 1:
                        continue

                    try:
                        stat_value_converted = stat_type_mapping.get(stat_key_normalized, int)(value)
                        if isinstance(stat_value_converted, float):
                            stat_value_converted = round(stat_value_converted, 4)
                    except Exception as e:
                        if str(value) == '-.--':  # Handle special case for missing advanced ratios
                            stat_value_converted = None
                        else:
                            print(f"Error converting stat '{stat_key_normalized}': {e}")
                            stat_value_converted = str(value)

                    # IP NEEDS SPECIAL HANDLING TO COMBINE FRACTIONAL INNINGS
                    if stat_key_normalized == 'IP' and len(splits) > 1:
                        ip_splits.append(stat_value_converted)
                        continue

                    if stat_key_normalized not in type_stats:
                        type_stats[stat_key_normalized] = stat_value_converted
                    elif isinstance(stat_value_converted, (int, float)):
                        type_stats[stat_key_normalized] += stat_value_converted

            # COMBINE FRACTIONAL INNINGS PITCHED ACROSS SPLITS
            if ip_splits:
                type_stats['IP'] = total_innings_pitched(ip_splits)

            # COMPUTE IF/FB FROM ACCUMULATED BATTED BALL COUNTS
            if is_pitcher and 'IF/FB' not in combined_stats:
                total_airborne = popup_total + flyball_total + linedrive_total
                if total_airborne > 0:
                    type_stats['IF/FB'] = round(popup_total / total_airborne, 4)

            # MERGE INTO COMBINED: PRIMARY TYPE WINS FOR OVERLAPPING KEYS
            # SUBSEQUENT TYPES ONLY CONTRIBUTE KEYS NOT ALREADY PRESENT
            is_primary_type = (stats_type == stats_types[0])
            for key, value in type_stats.items():
                if is_primary_type or key not in combined_stats:
                    combined_stats[key] = value

        return combined_stats

    @staticmethod
    def _extract_standard_stats_from_fangraphs_leaderboard(fg_data: LeaderboardStats) -> Dict[str, Any]:
        """Extracts standard stats from a Fangraphs leaderboard record. This is separate from the MLB API extraction because the stat keys and structure can be different."""
        stat_name_mapping = PlayerStatsNormalizer._map_fangraphs_leaderboard_stats_to_bref()
        stat_type_mapping = PlayerStatsNormalizer._stat_datatype_dict()

        standard_stats: Dict[str, Any] = {}
        for key, value in fg_data.model_dump(by_alias=True).items():
            if value is None: # Skip None values
                continue
            stat_key_normalized = stat_name_mapping.get(key, key)

            if stat_key_normalized not in NormalizedPlayerStats.all_valid_field_names():
                continue

            try:
                stat_value_converted = stat_type_mapping.get(stat_key_normalized, int)(value)
                if isinstance(stat_value_converted, float):
                    stat_value_converted = round(stat_value_converted, 4)
            except Exception as e:
                print(f"Error converting stat '{stat_key_normalized}' from Fangraphs data: {e}")
                stat_value_converted = value

            standard_stats[stat_key_normalized] = stat_value_converted

        return standard_stats

    @staticmethod
    def extract_team_id(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> Optional[str]:
        """Extracts the team ID for the player in the given stats period"""

        if stats_period.league and stats_period.league == StatsPeriodLeague.MILB:
            # TODO: USE GENERIC MILB TEAM FOR NOW. EVENTUALLY WILL NEED TO MAP TO SPECIFIC TEAMS
            return 'MILB'

        stats_type = PlayerStatsNormalizer._primary_stats_type(stats_period.year_type)
        is_hitter = stats_period.player_type_for_mlb_api(mlb_player.primary_position.abbreviation) == PlayerType.HITTER if stats_period else not mlb_player.is_pitcher
        group_type = StatGroupEnum.HITTING if is_hitter else StatGroupEnum.PITCHING
        standard_stat_splits = mlb_player.get_stat_splits(
            group_type=group_type,
            types=[stats_type],
            seasons=stats_period.year_list
        )

        if not standard_stat_splits or len(standard_stat_splits) == 0:
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
        team_raw = max(team_games_played, key=team_games_played.get)

        return PlayerStatsNormalizer._convert_to_bref_team_id(team_raw)

    @staticmethod
    def _convert_to_bref_team_id(team_id: str) -> str:
        """Converts MLB API team ID to Baseball Reference team ID if needed"""
        conversion_map = {
            'AZ': 'ARI',
            'CWS': 'CHW',
            'KC': 'KCR',
            'SD': 'SDP',
            'SF': 'SFG',
            'TB': 'TBR',
            'WSH': 'WSN',
        }
        return conversion_map.get(team_id, team_id)

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
        is_hitter = stats_period.player_type_for_mlb_api(mlb_player.primary_position.abbreviation) == PlayerType.HITTER if stats_period else not mlb_player.is_pitcher
        group_type = StatGroupEnum.HITTING if is_hitter else StatGroupEnum.PITCHING
        standard_stat_splits = mlb_player.get_stat_splits(
            group_type=group_type,
            types=[stats_type],
            seasons=stats_period.year_list
        )
        for split in standard_stat_splits:
            team = split.team
            if team and team.abbreviation == primary_team_id:
                if team.league and team.league.abbreviation:
                    return team.league.abbreviation
                
        return None

    @staticmethod
    def _extract_game_logs(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> List['GameLog']:
        """Extracts game logs for the player. Stats are in a gameLogs split. Returns a list of GameLog objects."""
        stats_type = StatTypeEnum.GAME_LOG
        is_hitter = stats_period.player_type_for_mlb_api(mlb_player.primary_position.abbreviation) == PlayerType.HITTER if stats_period else not mlb_player.is_pitcher
        group_type = StatGroupEnum.HITTING if is_hitter else StatGroupEnum.PITCHING
        game_log_splits = mlb_player.get_stat_splits(
            group_type=group_type,
            types=[stats_type],
            seasons=stats_period.year_list
        )

        if not game_log_splits or len(game_log_splits) == 0:
            return []  # No stats available
        
        stat_name_mapping = PlayerStatsNormalizer._map_mlb_api_stats_to_bref()
        stat_type_mapping = PlayerStatsNormalizer._stat_datatype_dict()

        game_logs: List['GameLog'] = []
        for split in game_log_splits:
            stats = split.stat
            if not stats:
                continue
            
            game_date = split.date
            game_pk = split.game.get('gamePk', None) if split.game else None
            team_id = PlayerStatsNormalizer._convert_to_bref_team_id(split.team.abbreviation) if split.team and split.team.abbreviation else None
            stats_normalized = {}
            for key, value in stats.items():
                
                stat_key_normalized = stat_name_mapping.get(key, key)

                if stat_key_normalized not in NormalizedPlayerStats.all_valid_field_names():
                    continue

                try:
                    stat_value_converted = stat_type_mapping.get(stat_key_normalized, int)(value)
                    if isinstance(stat_value_converted, float):
                        stat_value_converted = round(stat_value_converted, 4)
                except Exception as e:
                    stat_value_converted = str(value)

                if (type(stat_value_converted) == float or type(stat_value_converted) == int) and stat_value_converted == 0:
                    continue # Skip zero values in game logs to reduce size
                stats_normalized[stat_key_normalized] = stat_value_converted

            game_log_entry = {
                'date': game_date,
                'team_ID': team_id,
                'game_pk': game_pk,
                **stats_normalized
            }
            game_logs.append(GameLog(**game_log_entry))

        return game_logs

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
            'hitBatsmen': 'HBP',
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

            # Value
            'war': 'fWAR',
        }
    
    @staticmethod
    def _map_fangraphs_leaderboard_stats_to_bref() -> Dict[str, str]:
        """Maps Fangraphs leaderboard stat keys to Baseball Reference stat keys"""
        return {
            'WHIP': 'whip',
            'ERA': 'earned_run_avg',
            'ER': 'ER',
            'TBF': 'batters_faced',

            # Slashline
            'AVG': 'batting_avg',
            'SLG': 'slugging_perc',
            'OBP': 'onbase_perc',
            'OPS': 'onbase_plus_slugging',

            'WAR': 'fWAR',
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
            'IF/FB': float,
            'fWAR': float,
            'dWAR': float,
            'bWAR': float,
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

        # ----- RANKS ----- #

        # MLB STATS RANKINGS ARE STORED AS STAT SPLITS
        stats_type = StatTypeEnum.RANKINGS_BY_YEAR
        group_type = StatGroupEnum.HITTING if mlb_player.primary_position and mlb_player.primary_position.player_type == PlayerType.HITTER else StatGroupEnum.PITCHING
        rankings_by_year = mlb_player.get_stat_splits(
            group_type=group_type,
            types=[stats_type],
            seasons=stats_period.year_list
        )

        if not rankings_by_year or len(rankings_by_year) == 0:
            return accolades  # No stats available

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
                if stat_key_normalized == 'SO' and mlb_player.primary_position and mlb_player.primary_position.player_type == PlayerType.PITCHER:
                    stat_key_normalized = 'SO_p' # Bref differentiates hitter and pitcher strikeouts
                existing_accolades_for_stat = accolades.get(stat_key_normalized, [])
                                
                ordinal_rank = convert_number_to_ordinal(rank_value).upper()

                # CONVERT TO STRING
                # EX: "2025 AL (7TH)"
                league_abbr = split.team.league.abbreviation if split.team and split.team.league else "N/A"
                accolade_str = f"{split.season} {league_abbr} ({ordinal_rank})"
                existing_accolades_for_stat.append(accolade_str)
                accolades[stat_key_normalized] = existing_accolades_for_stat

        # ----- AWARDS ----- #

        for award in (mlb_player.awards or []):

            # ONLY INCLUDE RELEVANT AWARDS
            if not award.is_included_in_accolades:
                continue

            if not award.normalized_accolade_list_key and not award.is_in_normalized_award_list:
                continue

            if not award.season:
                continue

            if not award.season in stats_period.year_list_as_strs:
                continue

            league_abbr = award.league if award.league else "N/A"
            accolade_str = f"{award.season} {league_abbr}"

            if award.normalized_accolade_list_key:
                existing_accolades_for_award = accolades.get(award.normalized_accolade_list_key, [])
                existing_accolades_for_award.append(accolade_str)
                accolades[award.normalized_accolade_list_key] = existing_accolades_for_award

            if award.is_in_normalized_award_list:
                existing_accolades_for_awards = accolades.get('awards', [])
                accolade_str_with_award_name = f"{accolade_str} {award.long_name.upper()}"
                existing_accolades_for_awards.append(accolade_str_with_award_name)
                accolades['awards'] = existing_accolades_for_awards

        return accolades

    @staticmethod
    def _determine_rookie_status(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> bool:
        """Determines if the player is a rookie in the given stats period"""

        if stats_period.league and stats_period.league == StatsPeriodLeague.MILB:
            return False  # We don't want to classify any minor league players as rookies since they won't have MLB rookie status
        
        if mlb_player.rookie_seasons is None or len(mlb_player.rookie_seasons) == 0:
            return False

        if stats_period.is_full_career:
            return False
        
        if stats_period.is_multi_year:
            return stats_period.year_list_as_strs == mlb_player.rookie_seasons

        if stats_period.year_type == StatsPeriodYearType.SINGLE_YEAR:
            return str(stats_period.year) in mlb_player.rookie_seasons

        return False
    
    @staticmethod
    def _build_award_summary_str(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> str:
        """Builds a summary string of awards for the player in the given stats period.
        Matches the format used by Baseball Reference.
        
        Example: "GG,SS,MVP-1"

        Args:
            mlb_player (MLBStatsApi_Player): The MLB Stats API Player model
        
        Returns:
            str: Comma-separated award summary string
        """

        if not mlb_player.awards or len(mlb_player.awards) == 0:
            return ""

        award_abbr_list: List[str] = []

        for award in mlb_player.awards:
            if not award.award_summary_abbr: continue
            if not award.season: continue
            if award.season not in stats_period.year_list_as_strs: continue

            award_abbr_list.append(award.award_summary_abbr)

        # MAKE LIST UNIQUE AND SORTED
        award_abbr_list = sorted(list(set(award_abbr_list)))
        return ",".join(award_abbr_list)

    @staticmethod
    def _determine_20_game_winner(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> bool:
        """Determines if the pitcher won 20 games in the given stats period"""
        
        stats_type = PlayerStatsNormalizer._primary_stats_type(stats_period.year_type)
        is_hitter = stats_period.player_type_for_mlb_api(mlb_player.primary_position.abbreviation) == PlayerType.HITTER if stats_period else not mlb_player.is_pitcher
        group_type = StatGroupEnum.HITTING if is_hitter else StatGroupEnum.PITCHING
        standard_stat_splits = mlb_player.get_stat_splits(
            group_type=group_type,
            types=[stats_type],
            seasons=stats_period.year_list
        )

        for split in (standard_stat_splits or []):
            if not split.stat: continue

            for key, value in split.stat.items():
                if key == 'wins':
                    try:
                        wins = int(value)
                        if wins >= 20:
                            return True
                    except:
                        continue

        return False

    @staticmethod
    def _extract_ip_per_gs(mlb_player: MLBStatsApi_Player, stats_period: StatsPeriod) -> Optional[float]:
        """Calculates GS/IP by looking inside stat splits for the split code 'sp' and dividing gamesStarted by inningsPitched. This is necessary because MLB Stats API doesn't provide a direct GS/IP stat and we want to be able to calculate it for all players, even those with minimal pitching stats who may not have this ratio calculated in the API."""
        group_type = StatGroupEnum.PITCHING
        pitching_stat_splits = mlb_player.get_stat_splits(
            group_type=group_type,
            types=[StatTypeEnum.STAT_SPLITS],
            seasons=stats_period.year_list
        )
        
        total_ip_list = []
        total_gs = 0
        for split in pitching_stat_splits:
            if split.split and split.split.code == 'sp' and split.stat:
                games_started = split.stat.get('gamesStarted', 0)
                innings_pitched_str = split.stat.get('inningsPitched', '0')
                try:
                    ip_float = float(innings_pitched_str)
                except:
                    ip_float = 0.0
                total_gs += games_started
                total_ip_list.append(ip_float)
        total_ip = total_innings_pitched(total_ip_list)
        if total_gs > 0:
            return round(total_ip / total_gs, 1) # Rounded to 1 to match bref
        
        return None
        

    # -------------------------------
    # Multi-Year Combining Methods
    # -------------------------------

    @staticmethod
    def combine_multi_year_stats(stats_list: List[NormalizedPlayerStats], stats_period: StatsPeriod) -> NormalizedPlayerStats:
        """Combines multiple years of NormalizedPlayerStats into a single NormalizedPlayerStats for multi-year periods"""
        
        if not stats_list or len(stats_list) == 0:
            raise ValueError("Cannot combine empty stats list")
        
        if len(stats_list) == 1:
            return stats_list[0]  # Nothing to combine
        
        # For 2-way players, filter out stats that don't match the primary type
        # Identify type based on game counts
        type_game_counts: Dict[str, int] = {}
        for stats in stats_list:
            player_type = stats.player_type_override if stats.player_type_override else stats.type
            type_game_counts[player_type] = type_game_counts.get(player_type, 0) + (stats.G or 0)

        if len(type_game_counts) > 1:
            primary_type = max(type_game_counts, key=type_game_counts.get)
            stats_list = [s for s in stats_list if (s.player_type_override if s.player_type_override else s.type) == primary_type]
        
        # Use the first entry as base template - USE ALIASES IN OUTPUT
        base_stats = stats_list[-1]  # Use the most recent year as base
        combined_data = base_stats.model_dump(by_alias=True, exclude_none=True, exclude_unset=True)
        
        # Update metadata for multi-year
        combined_data['year_ID'] = "CAREER" if stats_period.is_full_career else "-".join(str(s.year_id) for s in stats_list)
        combined_data['primary_datasource'] = base_stats.primary_datasource.value  # Serialize enum

        # USE TEAM WITH THE MOST GAMES PLAYED
        team_games_played: Dict[str, int] = {}
        for stats in stats_list:
            if stats.team_id and stats.G:
                team_games_played[stats.team_id] = team_games_played.get(stats.team_id, 0) + stats.G
        combined_data['team_ID'] = max(team_games_played, key=team_games_played.get) if team_games_played else None
        
        # Define aggregation strategies - USE ALIASES for fields that have them
        counting_stats = {
            'G', 'PA', 'AB', 'R', 'H', 'singles', 'doubles', 'triples', 'HR', 'RBI',
            'SB', 'CS', 'BB', 'SO', 'TB', 'GIDP', 'HBP', 'SH', 'SF', 'IBB',
            'W', 'L', 'GS', 'ER', 'SV', 'bWAR', 'dWAR', 'fWAR', 'batters_faced',  # Use aliases here too
        }
        
        averaging_stats = {
            'sprint_speed', 'go_ao_ratio', 'if_fb_ratio', 'onbase_plus_slugging_plus'  # Use aliases here too
        }
        
        max_stats = {
            'is_hr_leader', 'is_sb_leader', 'is_so_leader', 'is_above_hr_threshold',
            'is_above_so_threshold', 'is_above_sb_threshold', 'is_above_w_threshold'
        }
        
        concatenation_stats = {
            'award_summary'
        }

        list_concatenation_stats = {
            'game_logs', 'postseason_game_logs', 'warnings'
        }
        
        # Create field mapping for accessing attributes by alias
        field_attr_to_alias = {k: k for k in NormalizedPlayerStats.__annotations__.keys()}
        field_attr_to_alias.update({v: k for k, v in NormalizedPlayerStats.field_aliases().items()} )
        
        # Aggregate counting stats (sum)
        for stat in counting_stats:
            alias = field_attr_to_alias.get(stat, stat)
            if alias in combined_data:
                # Get the actual field name to use with getattr
                total = sum((getattr(stats, stat, 0) or 0) for stats in stats_list)
                if isinstance(combined_data[alias], float):
                    total = round(total, 4)
                combined_data[alias] = total
        
        # Handle IP separately (special decimal handling)
        ip_values = [stats.IP for stats in stats_list if stats.IP > 0]
        if ip_values:
            combined_data['IP'] = total_innings_pitched(ip_values)
        
        # Aggregate averaging stats (mean)
        for stat in averaging_stats:
            alias = field_attr_to_alias.get(stat, stat)
            if alias in combined_data:
                
                valid_values = [getattr(stats, stat) for stats in stats_list 
                            if getattr(stats, stat, None) is not None]
                if valid_values:
                    combined_data[alias] = round(sum(valid_values) / len(valid_values), 4)
                else:
                    combined_data[alias] = None
        
        # Aggregate max stats (any True = True)
        for stat in max_stats:
            alias = field_attr_to_alias.get(stat, stat)
            if alias in combined_data:
                combined_data[alias] = any(getattr(stats, stat, False) for stats in stats_list)
        
        # Handle concatenation stats
        for stat in concatenation_stats:
            alias = field_attr_to_alias.get(stat, stat)
            if alias in combined_data:
                values = [getattr(stats, stat) for stats in stats_list 
                        if getattr(stats, stat, None)]
                if values:
                    # Remove duplicates and join
                    unique_values = list(dict.fromkeys(values))  # Preserves order
                    combined_data[alias] = ','.join(unique_values)
                else:
                    combined_data[alias] = None
        

        # Combine game logs and warnings lists
        for stat in list_concatenation_stats:
            alias = field_attr_to_alias.get(stat, stat)
            combined_list = []
            for stats in stats_list:
                stat_list = getattr(stats, stat, [])
                if stat_list:
                    combined_list.extend(stat_list)
            combined_data[alias] = combined_list if combined_list else None
        
        # Rest of the combining logic...
        combined_positions = PlayerStatsNormalizer._combine_positions(stats_list)
        combined_data['positions'] = combined_positions
        
        combined_accolades = PlayerStatsNormalizer._combine_accolades(stats_list)
        combined_data['accolades'] = combined_accolades
        
        # Recalculate rate stats after combining counting stats
        combined_data.update(PlayerStatsNormalizer._recalculate_rate_stats(combined_data))

        # Remove rookie status 
        combined_data['is_rookie'] = False
        
        # Create and return new NormalizedPlayerStats
        return NormalizedPlayerStats(**combined_data)

    @staticmethod
    def _combine_positions(stats_list: List[NormalizedPlayerStats]) -> Optional[Dict[str, 'PositionStats']]:
        """Combine position stats from multiple years"""
        combined_positions: Dict[str, 'PositionStats'] = {}

        years_with_stat: Dict[str, list] = {}  # Track number of years with stats for deciding which to use
        metrics = ['tzr', 'drs', 'oaa', 'uzr',]

        for stats in stats_list:
            if not stats.positions:
                continue
                
            for pos, pos_stats in stats.positions.items():
                if pos not in combined_positions:
                    combined_positions[pos] = PositionStats(
                        g=pos_stats.g,
                        innings=pos_stats.innings,
                        position=pos,
                        tzr=pos_stats.tzr,
                        drs=pos_stats.drs,
                        oaa=pos_stats.oaa,
                        uzr=pos_stats.uzr
                    )
                    for metric in metrics:
                        if getattr(pos_stats, metric) is not None and stats.year_id not in years_with_stat.get(metric, []):
                            years_with_stat[metric] = years_with_stat.get(metric, []) + [stats.year_id]
                else:
                    # Sum games, average the metrics
                    existing = combined_positions[pos]
                    existing.g += pos_stats.g
                    
                    # ADD UP THE METRICS
                    for metric in metrics:
                        existing_val = getattr(existing, metric)
                        new_val = getattr(pos_stats, metric)
                        
                        if existing_val is not None and new_val is not None:
                            setattr(existing, metric, existing_val + new_val)
                        elif new_val is not None:
                            setattr(existing, metric, new_val)
                        
                        # TRACK NUMBER OF YEARS WITH METRIC AVAILABLE
                        if new_val is not None:
                            existing_year_list_for_metric = years_with_stat.get(metric, [])
                            if stats.year_id not in existing_year_list_for_metric:
                                existing_year_list_for_metric.append(stats.year_id)
                            years_with_stat[metric] = existing_year_list_for_metric


        if not combined_positions:
            return None
        
        # REMOVE METRICS THAT HAVE A SMALL PERCENTAGE OF YEARS WITH DATA
        total_years = len(stats_list)
        for pos, pos_stats in combined_positions.items():
            metrics = ['tzr', 'drs', 'oaa', 'uzr',]
            for metric in metrics:
                year_list_for_metric = years_with_stat.get(metric, [])
                if len(year_list_for_metric) / total_years < 0.80:
                    # LESS THAN 80% OF YEARS HAVE DATA, REMOVE METRIC
                    setattr(pos_stats, metric, None)

        return combined_positions if combined_positions else None

    @staticmethod
    def _combine_accolades(stats_list: List[NormalizedPlayerStats]) -> Optional[Dict[str, List[str]]]:
        """Combine accolades from multiple years"""
        combined_accolades = {}
        
        for stats in stats_list:
            if not stats.accolades:
                continue
                
            for key, values in stats.accolades.items():
                if key not in combined_accolades:
                    combined_accolades[key] = []
                combined_accolades[key].extend(values)
        
        # Remove duplicates while preserving order
        for key in combined_accolades:
            combined_accolades[key] = list(dict.fromkeys(combined_accolades[key]))
        
        return combined_accolades if combined_accolades else None

    @staticmethod
    def _recalculate_rate_stats(combined_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate rate stats after combining counting stats"""
        rate_updates = {}
        
        # Batting rates
        ab = combined_data.get('AB', 0)
        h = combined_data.get('H', 0)
        bb = combined_data.get('BB', 0)
        hbp = combined_data.get('HBP', 0)
        sf = combined_data.get('SF', 0)
        tb = combined_data.get('TB', 0)
        
        if ab > 0:
            rate_updates['batting_avg'] = round(h / ab, 4)
            rate_updates['slugging_perc'] = round(tb / ab, 4)
            
            obp_denominator = ab + bb + hbp + sf
            if obp_denominator > 0:
                rate_updates['onbase_perc'] = round((h + bb + hbp) / obp_denominator, 4)
                rate_updates['onbase_plus_slugging'] = round(
                    rate_updates.get('onbase_perc', 0) + rate_updates.get('slugging_perc', 0), 4
                )
        
        # Pitching rates
        ip = combined_data.get('IP', 0)
        er = combined_data.get('ER', 0)
        h_allowed = combined_data.get('H', 0)  # For pitchers, this would be hits allowed
        bb_allowed = combined_data.get('BB', 0)  # Walks allowed
        
        if ip > 0:
            rate_updates['earned_run_avg'] = round(9 * er / ip, 4)
            if h_allowed + bb_allowed > 0:
                rate_updates['whip'] = round((h_allowed + bb_allowed) / ip, 4)
        
        return rate_updates

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
    fld_pct: Optional[float] = None  # Fielding Percentage

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
    
    game_pk: Optional[int] = None  # Unique identifier for the game log entry, can be generated as needed
    date: Optional[str] = None # e.g., "2024-04-01"
    date_game: Optional[str] = None  # e.g., "Apr 1"
    team_ID: str
    player_game_span: Optional[str] = None  # e.g., "CG", "GS-8", "CG(10)"
    game_decision: Optional[str] = None  # e.g., "W", "L", "SV", "HLD", etc.
    
    # Game stats
    PA: int = 0
    AB: int = 0
    R: int = 0
    H: int = 0
    singles: int = Field(0, alias='1B')
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

    W: Optional[int] = 0
    ER: Optional[int] = 0
    IP: Optional[float] = 0.0
    SV: Optional[int] = 0
    GS: Optional[int] = 0
    batters_faced: Optional[int] = 0

    @field_validator('GIDP', 'AB', 'R', 'SB', 'ER', 'IP', 'RBI', 'PA', mode='before')
    def validate_gidp(cls, v):
        """Validates GIDP to ensure it's an integer"""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return 0
        return v
    
    @field_validator('date', mode='before')
    def validate_date(cls, v, info):
        """Validates date to ensure it's in YYYY-MM-DD format"""
        if v is None:
            print(f"Date is missing: {info.data.get('year_ID', {})}")
        return v

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