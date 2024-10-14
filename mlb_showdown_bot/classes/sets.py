from enum import Enum
import numpy as np
try:
    from .metadata import SpeedMetric
    from .player_position import PlayerType, PlayerSubType, Position
    from .metrics import Stat, PointsMetric
    from .value_range import ValueRange
    from .images import PlayerImageComponent, TemplateImageComponent, ImageParallel, Expansion, SpecialEdition
    from .chart import Chart, ChartCategory
except ImportError:
    from metadata import SpeedMetric
    from player_position import PlayerType, PlayerSubType, Position
    from metrics import Stat, PointsMetric
    from value_range import ValueRange
    from images import PlayerImageComponent, TemplateImageComponent, ImageParallel, Expansion, SpecialEdition
    from chart import Chart, ChartCategory


class Era(Enum):
    """ Class that stores metadata about each Showdown Bot "Era".

    Each era represents a statistical period in baseball history. The purpose of eras is to adjust cards to the way the game was played in that period. Similar to how metrics like WAR, OPS+, ERA+ change based on the season.
    """

    PRE_1900 = "PRE 1900 ERA"
    DEAD_BALL = "DEAD BALL ERA"
    LIVE_BALL = "LIVE BALL ERA"
    INTEGRATION = "INTEGRATION ERA"
    EXPANSION = "EXPANSION ERA"
    FREE_AGENCY = "FREE AGENCY ERA"
    STEROID = "STEROID ERA"
    POST_STEROID = "POST STEROID ERA"
    STATCAST = "STATCAST ERA"
    PITCH_CLOCK = "PITCH CLOCK ERA"

    @property
    def year_range(self) -> list[int]:
        match self.name:
            case 'PRE_1900': return list(range(1884, 1900))
            case 'DEAD_BALL': return list(range(1900, 1920))
            case 'LIVE_BALL': return list(range(1920, 1942))
            case 'INTEGRATION': return list(range(1942, 1961))
            case 'EXPANSION': return list(range(1961, 1977))
            case 'FREE_AGENCY': return list(range(1977, 1994))
            case 'STEROID': return list(range(1994, 2010))
            case 'POST_STEROID': return list(range(2010, 2015))
            case 'STATCAST': return list(range(2015, 2023))
            case 'PITCH_CLOCK': return list(range(2023, 2025))

    @property
    def speed_multiplier(self) -> float:
        match self.name:
            case 'PRE_1900': return 0.80
            case 'DEAD_BALL': return 0.80
            case 'PITCH_CLOCK': return 0.99
            case _: return 1.0

    @property
    def value_no_era_suffix(self) -> str:
        return self.value.replace(' ERA', '')




# ------------------------------------------------------------------------------
# SET
# ------------------------------------------------------------------------------

class Set(str, Enum):
    """ Card logic and style metadata. Includes Showdown Bot produced sets and the original WOTC sets. 
    
        WOTC:
          - 2000
          - 2001
          - 2002
          - 2003
          - 2004
          - 2005

        Showdown Bot
          - CLASSIC
          - EXPANDED
    """

    _2000 = "2000"
    _2001 = "2001"
    _2002 = "2002"
    _2003 = "2003"
    _2004 = "2004"
    _2005 = "2005"
    CLASSIC = "CLASSIC"
    EXPANDED = "EXPANDED"

    def __repr__(self) -> str:
        return self.value

    # ---------------------------------------
    # SET ORIGINATION
    # ---------------------------------------

    @property
    def is_wotc(self) -> bool:
        return self.value not in ['CLASSIC', 'EXPANDED']
    
    @property
    def is_showdown_bot(self) -> bool:
        return not self.is_wotc
    
    @property
    def year(self) -> str:
        return self.value if self.is_wotc else '2022'
    
    @property
    def is_00_01(self) -> bool:
        return self.value in ['2000','2001']
    
    @property
    def is_04_05(self) -> bool:
        return self.value in ['2004','2005']
    
    @property
    def is_after_03(self) -> bool:
        return self.value in ['2004','2005','CLASSIC','EXPANDED',]
    
    
    # ---------------------------------------
    # ELIGIBILITY
    # ---------------------------------------

    @property
    def is_eligibile_for_year_container(self) -> bool:
        return self.value in ['2000', '2001', '2002', '2003', '2004', '2005', 'CLASSIC', 'EXPANDED', ] # NOW ENABLED FOR ALL SETS
    
    @property
    def is_year_container_text(self) -> bool:
        """ Applies to 04+ sets, uses text next to logo instead of container for displaying the year"""
        return self.value in ['2004','2005','CLASSIC','EXPANDED',]

    @property
    def is_eligibile_for_year_plus_one(self) -> bool:
        return self.is_04_05 or self.value == '2003'
    
    # ---------------------------------------
    # DEFAULTS
    # ---------------------------------------
    
    def default_set_number(self, year_str: str) -> str:
        return '—' if self.value in ['2003', '2004', '2005', 'CLASSIC', 'EXPANDED'] else year_str

    # ---------------------------------------
    # METRICS
    # ---------------------------------------

    @property
    def shOPS_command_adjustment_factor_weight(self) -> float:
        return 0.15

    # ---------------------------------------
    # SPEED
    # ---------------------------------------

    @property
    def max_in_game_spd(self) -> int:
        return 28
    
    @property
    def min_in_game_spd(self) -> int:
        return 8
    
    @property
    def speed_c_cutoff(self) -> int:
        match self.value:
            case '2002': return 13
            case _: return 12

    @property
    def speed_cutoff_for_sub_percentile_sb(self) -> int:
        match self:
            case Set._2002: return 22
            case Set._2004 | Set._2005 | Set.EXPANDED: return 21
            case _: return 20

    def speed_metric_multiplier(self, metric: SpeedMetric, use_variable_speed_multiplier:bool) -> float:
        if use_variable_speed_multiplier:
            return self.variable_speed_multiplier
        
        if metric == SpeedMetric.STOLEN_BASES:
            match self.value:
                case '2000': return 1.21
                case '2001': return 1.22
                case '2002': return 1.12
                case '2003': return 0.962
                case '2004': return 1.00
                case '2005': return 1.00
                case _: return 1.0
        
        return 1.0
    
    @property
    def variable_speed_multiplier(self) -> float:
        return 1.05 if self.is_00_01 else 1.00

    # ---------------------------------------
    # POSITIONS/DEFENSE
    # ---------------------------------------

    @property
    def catcher_position_name(self) -> str:
        return 'C' if self.is_00_01 else 'CA'

    def position_defense_max(self, position:Position) -> float:
        match position:
            case Position.CA: return 11 if self == Set._2001 else 12
            case Position._1B: return 1
            case Position._2B: return 5
            case Position._3B: return 4.5 if self.is_showdown_bot else 4
            case Position.SS: return 6 if self.is_showdown_bot else 5
            case Position.CF: return 3.5 if self.is_showdown_bot else 3
            case Position.LFRF | Position.OF | Position.RF | Position.LF: return 2
            case Position.IF: return 1
            case _: return 0

    @property
    def min_number_of_games_defense(self) -> int:
        return 7 

    def min_pct_of_games_defense(self, is_multi_year:bool) -> float:
        return 0.25 if is_multi_year else 0.15

    @property
    def starting_pitcher_pct_games_started(self) -> float:
        return 0.40

    @property
    def closer_min_saves_required(self) -> int:
        return 10
    
    @property
    def num_position_slots(self) -> int:
        return 3 if self.is_showdown_bot else 2
    
    @property
    def defense_floor(self) -> int:
        return -2 if self.is_showdown_bot else 0
    
    @property
    def infield_plus_one_requirement(self) -> int:
        return 6
    
    @property
    def is_outfield_split(self) -> bool:
        return self.value in ['2000','2001','2002']

    @property
    def dh_string(self) -> str:
        return 'DH' if self.value == '2000' else '–'
    
    @property
    def is_cf_eligible_for_lfrf(self) -> bool:
        return self in [Set._2000, Set._2001, Set.CLASSIC, Set.EXPANDED,]

    # ---------------------------------------
    # ICONS
    # ---------------------------------------

    @property
    def has_icons(self) -> bool:
        return self.value in ['2003','2004','2005','CLASSIC','EXPANDED',]
    
    @property
    def has_icon_pts(self) -> bool:
        return self.has_icons and self.value != 'CLASSIC'
    
    def icon_paste_coordinates(self, index:int) -> tuple[int,int]:
        match self.value:
            case '2003':
                y_position = 1905 if (index % 2) == 1 else 1830
                starting_x = 1005
                x_offset = int(-75 * (round(index * 1.001 / 2.0) - 1))
                return (starting_x + x_offset, y_position)

            case '2004' | '2005' | 'CLASSIC' | 'EXPANDED':
                is_04_05 = self.value in ['2004','2005']
                starting_x = 1050 if is_04_05 else 0
                starting_y = 1695 if is_04_05 else -4
                distance_between_icons = 75 if is_04_05 else 69
                return (int(starting_x + ( (index - 1) * distance_between_icons )), starting_y)


    # ---------------------------------------
    # CHART
    # ---------------------------------------    

    @property
    def onbase_out_combinations(self) -> list[tuple[int,int]]:
        match self.value:
            case '2000': return [
                (4,5),
                (5,2),(5,3),(5,4),(5,5),
                (6,2),(6,3),(6,4),(6,5),
                (7,2),(7,3),(7,4),(7,5),
                (8,2),(8,3),(8,4),(8,5),
                (9,2),(9,3),(9,4),(9,5),
                (10,2),(10,3),(10,4),(10,5),
                (11,2),(11,3),
                (12,0),(12,2),(12,3),
                (13,0),(13,1),
            ]
            case '2001': return [
                (4,5),(4,6),
                (5,2),(5,3),(5,4),(5,5),(5,6),
                (6,2),(6,3),(6,4),(6,5),(6,6),
                (7,2),(7,3),(7,4),(7,5),(7,6),
                (8,2),(8,3),(8,4),(8,5),
                (9,2),(9,3),(9,4),(9,5),
                (10,2),(10,3),(10,4),
                (11,2),(11,3),
                (12,0),(12,2),(12,3),
                (13,0),(13,1),
            ]
            case '2002': return [
                (7,5),(7,6),(7,7),(7,8),(7,9),(7,10),
                (8,5),(8,6),(8,7),(8,8),
                (9,5),(9,6),(9,7),
                (10,5),(10,6),(10,7),
                (11,5),(11,6),(11,7),
                (12,5),(12,6),(12,7),
                (13,5),(13,6),(13,7),
                (14,5),(14,6),(14,7),
                (15,6),(15,7),
                (16,0),(16,2),(16,3),(16,4),(16,5),(16,6),
            ]
            case '2003': return [
                (7,8),(7,9),(7,10),
                (8,5),(8,6),(8,7),(8,8),(8,9),
                (9,5),(9,6),(9,7),(9,8),
                (10,5),(10,6),(10,7),
                (11,5),(11,6),(11,7),
                (12,5),(12,6),(12,7),
                (13,5),(13,6),(13,7),
                (14,0),(14,2),(14,3),(14,5),(14,6),(14,7),
                (15,6),(15,7),
                (16,0),(16,2),(16,3),(16,4),(16,5),(16,6),
            ]
            case '2004' | '2005': return [
                (7,8),(7,9),(7,10),(7,11),
                (8,7),(8,8),(8,9),(8,10),(8,11),
                (9,5),(9,6),(9,7),(9,8),(9,9),(9,10),(9,11),
                (10,5),(10,6),(10,7),(10,8),
                (11,5),(11,6),(11,7),(11,8),
                (12,5),(12,6),(12,7),
                (13,5),(13,6),(13,7),
                (14,5),(14,6),(14,7),
                (15,6),(15,7),
                (16,0),(16,2),(16,3),(16,4),(16,5),(16,6),
            ]
            case 'CLASSIC': return [
                (4,5),(4,6),
                (5,2),(5,3),(5,4),(5,5),(5,6),
                (6,2),(6,3),(6,4),(6,5),(6,6),
                (7,3),(7,4),(7,5),(7,6),
                (8,3),(8,4),(8,5),(8,6),
                (9,3),(9,4),(9,5),(9,6),
                (10,2),(10,3),(10,4),(10,5),
                (11,2),(11,3),(11,4),(11,5),
                (12,0),(12,2),(12,3),(12,4),
                (13,0),(13,1),
            ]
            case 'EXPANDED': return [
                (7,7),(7,8),(7,9),(7,10),(7,11),(7,12),
                (8,5),(8,6),(8,7),(8,8),(8,9),(8,10),(8,11),
                (9,5),(9,6),(9,7),(9,8),(9,9),(9,10),(9,11),
                (10,5),(10,6),(10,7),(10,8),
                (11,5),(11,6),(11,7),(11,8),
                (12,5),(12,6),(12,7),
                (13,5),(13,6),(13,7),
                (14,5),(14,6),(14,7),
                (15,6),(15,7),(15,8),
                (16,0),(16,2),(16,3),(16,4),(16,5),(16,6),
            ]

    @property
    def control_out_combinations(self) -> list[tuple[int,int]]:
        match self.value:
            case '2000': return [
                (0,16),(0,17),(0,18),
                (2,15),(2,16),(2,18),
                (3,15),(3,16),(3,17),(3,18),
                (4,14),(4,15),(4,16),(4,17),(4,18),
                (5,15),(5,16),(5,17),(5,18),(5,19),
                (6,15),(6,16),(6,17),(6,18),(6,19),(6,20),
            ]
            case '2001': return [
                (0,17),(0,18),
                (1,17),(1,18),
                (2,16),(2,17),(2,18),
                (3,14),(3,15),(3,16),(3,17),(3,18),
                (4,14),(4,15),(4,16),(4,17),(4,18),
                (5,14),(5,15),(5,16),(5,17),(5,18),(5,19),
                (6,14),(6,15),(6,16),(6,17),(6,18),(6,19),(6,20),
            ]
            case '2002': return [
                (1,15),(1,16),(1,17),(1,18),(1,19),
                (2,15),(2,16),(2,17),(2,18),(2,19),
                (3,15),(3,16),(3,17),(3,18),(3,19),
                (4,14),(4,15),(4,16),(4,17),(4,18),(4,19),
                (5,15),(5,16),(5,17),(5,18),
                (6,16),(6,17),(6,18),(6,19),(6,20),
            ]
            case '2003': return [
                (1,15),(1,16),(1,18),
                (2,14),(2,15),(2,16),(2,18),
                (3,14),(3,15),(3,16),(3,17),(3,18),
                (4,14),(4,15),(4,16),(4,17),(4,18),
                (5,15),(5,16),(5,17),(5,18),
                (6,16),(6,17),(6,18),(6,19),(6,20),
            ]
            case '2004' | '2005': return [
                (1,13),(1,14),(1,15),(1,16),(1,18),(1,19),
                (2,14),(2,15),(2,16),(2,18),(2,19),
                (3,15),(3,16),(3,17),(3,18),(3,19),
                (4,14),(4,15),(4,16),(4,17),(4,18),
                (5,12),(5,14),(5,15),(5,16),(5,17),(5,18),(5,19),
                (6,15),(6,16),(6,17),(6,18),(6,19),(6,20),
            ]
            case 'CLASSIC': return [
                (0,17),(0,18),
                (1,17),(1,18),
                (1,16),(2,16),(2,17),(2,18),
                (3,14),(3,15),(3,16),(3,17),(3,18),(3,19),
                (4,14),(4,15),(4,16),(4,17),(4,18),
                (5,14),(5,15),(5,16),(5,17),(5,18),(5,19),
                (6,14),(6,15),(6,16),(6,17),(6,18),(6,19),(6,20),
            ]
            case 'EXPANDED': return [
                (1,14),(1,15),(1,16),(1,17),(1,18),(1,19),
                (2,15),(2,16),(2,17),(2,18),(2,19),
                (3,15),(3,16),(3,17),(3,18),(3,19),
                (4,15),(4,16),(4,17),(4,18),(4,19),
                (5,14),(5,15),(5,16),(5,17),(5,18),(5,19),
                (6,14),(6,15),(6,16),(6,17),(6,18),(6,19),(6,20),
            ]

    def command_out_combinations(self, player_type:PlayerType) -> list[tuple[int,int]]:
        return self.control_out_combinations if player_type.is_pitcher else self.onbase_out_combinations
    
    def command_accuracy_weighting(self, command:int, player_sub_type:PlayerSubType) -> float:
        """List of commands are corresponding accuracy weighting
        
        Args:
          command: Control/Onbase rating for player.
          player_sub_type: Player subtype attribute (POSITION_PLAYER, STARTING_PITCHER, RELIEF_PITCHER)

        Returns:
          Multiplier for the accuracy of the chart for the given command + set.
        """

        match self:
            case Set._2000:
                match command:
                    case 1: return 0.925
                    case 2: return 0.925
            case Set._2001:
                match command:
                    case 0: return 0.995
                    case 1: return 0.990
                    case 2: return 0.990

        return 1.0

    def test_command_out_combinations(self, is_pitcher:bool) -> list[tuple[int,int]]:
        hitter_command_range = np.arange(8, 11, 0.1).tolist() if self.has_expanded_chart else np.arange(6, 9, 0.1).tolist()
        hitter_out_range = np.arange(5, 8, 0.1).tolist() if self.has_expanded_chart else np.arange(2, 5, 0.1).tolist()
        command_range = np.arange(1, 5, 0.1).tolist() if is_pitcher else hitter_command_range
        outs_range = np.arange(15, 18, 0.1).tolist() if is_pitcher else hitter_out_range
        all_combos = [(c, o) for c in command_range for o in outs_range]
        return all_combos

    @property
    def has_expanded_chart(self) -> bool:
        return self.value in ['2002','2003','2004','2005','EXPANDED',]
    
    @property
    def has_classic_chart(self) -> bool:
        return not self.has_expanded_chart
    
    @property
    def is_chart_horizontal(self) -> bool:
        return self.is_after_03
    
    @property
    def pu_normalizer_1988(self) -> float:
        return 0.5
     
    @property
    def is_batting_avg_command_out_multiplier(self) -> bool:
        """Returns True if the set has a batting average multiplier"""
        return self in [Set._2003, Set._2004, Set._2005, Set.EXPANDED]

    # ---------------------------------------
    # POINTS
    # ---------------------------------------    

    def pts_metric_weight(self, player_sub_type:PlayerSubType, metric:PointsMetric) -> int:
        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 60
                            case PointsMetric.SPEED: return 80
                            case PointsMetric.ONBASE: return 120
                            case PointsMetric.AVERAGE: return 60
                            case PointsMetric.SLUGGING: return 60
                            case PointsMetric.HOME_RUNS: return 110
                            case PointsMetric.COMMAND: return 150
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 105
                            case PointsMetric.ONBASE: return 400
                            case PointsMetric.AVERAGE: return 55
                            case PointsMetric.SLUGGING: return 220
                            case PointsMetric.OUT_DISTRIBUTION: return 30
                            case PointsMetric.COMMAND: return 100
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 165
                            case PointsMetric.AVERAGE: return 10
                            case PointsMetric.SLUGGING: return 105
                            case PointsMetric.OUT_DISTRIBUTION: return 10
            case '2001' | 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 60
                            case PointsMetric.SPEED: return 65
                            case PointsMetric.ONBASE: return 242
                            case PointsMetric.AVERAGE: return 45
                            case PointsMetric.SLUGGING: return 120
                            case PointsMetric.HOME_RUNS: return 45
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 105
                            case PointsMetric.ONBASE: return 410
                            case PointsMetric.AVERAGE: return 35
                            case PointsMetric.SLUGGING: return 190
                            case PointsMetric.OUT_DISTRIBUTION: return 30
                            case PointsMetric.COMMAND: return 50
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 185
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 75
                            case PointsMetric.OUT_DISTRIBUTION: return 20
                            case PointsMetric.COMMAND: return 25
            case '2002':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 65
                            case PointsMetric.SPEED: return 75
                            case PointsMetric.ONBASE: return 110
                            case PointsMetric.COMMAND: return 40
                            case PointsMetric.AVERAGE: return 30
                            case PointsMetric.SLUGGING: return 130
                            case PointsMetric.HOME_RUNS: return 70
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 85
                            case PointsMetric.ONBASE: return 360
                            case PointsMetric.AVERAGE: return 25
                            case PointsMetric.SLUGGING: return 160
                            case PointsMetric.OUT_DISTRIBUTION: return 45
                            case PointsMetric.COMMAND: return 70
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHER
                            case PointsMetric.ONBASE: return 150
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 60
                            case PointsMetric.OUT_DISTRIBUTION: return 10
                            case PointsMetric.COMMAND: return 35
            case '2003': 
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 65
                            case PointsMetric.SPEED: return 65
                            case PointsMetric.ONBASE: return 150
                            case PointsMetric.AVERAGE: return 70
                            case PointsMetric.SLUGGING: return 170
                            case PointsMetric.HOME_RUNS: return 50
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 70
                            case PointsMetric.ONBASE: return 290
                            case PointsMetric.AVERAGE: return 60
                            case PointsMetric.SLUGGING: return 150
                            case PointsMetric.OUT_DISTRIBUTION: return 40
                            case PointsMetric.COMMAND: return 100
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 170
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 60
                            case PointsMetric.OUT_DISTRIBUTION: return 20
                            case PointsMetric.COMMAND: return 50
            case '2004':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 70
                            case PointsMetric.SPEED: return 60
                            case PointsMetric.ONBASE: return 140
                            case PointsMetric.AVERAGE: return 60
                            case PointsMetric.SLUGGING: return 180
                            case PointsMetric.HOME_RUNS: return 45
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 85
                            case PointsMetric.ONBASE: return 300
                            case PointsMetric.AVERAGE: return 50
                            case PointsMetric.SLUGGING: return 160
                            case PointsMetric.OUT_DISTRIBUTION: return 30
                            case PointsMetric.COMMAND: return 220
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 170
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 50
                            case PointsMetric.OUT_DISTRIBUTION: return 20
                            case PointsMetric.COMMAND: return 120
            case '2005' | 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 65
                            case PointsMetric.SPEED: return 45
                            case PointsMetric.ONBASE: return 135
                            case PointsMetric.AVERAGE: return 40
                            case PointsMetric.SLUGGING: return 250
                            case PointsMetric.HOME_RUNS: return 45
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 75
                            case PointsMetric.ONBASE: return 320
                            case PointsMetric.AVERAGE: return 50
                            case PointsMetric.SLUGGING: return 140
                            case PointsMetric.OUT_DISTRIBUTION: return 30
                            case PointsMetric.COMMAND: return 230
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 190
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 70
                            case PointsMetric.OUT_DISTRIBUTION: return 20
                            case PointsMetric.COMMAND: return 130

        return 0
    
    def pts_positional_defense_weight(self, position:Position) -> float:
        match self.value:
            case '2000':
                match position:
                    case Position.CA: return 1.0
                    case Position._1B: return 0.25
                    case Position._2B: return 1.0
                    case Position._3B: return 1.0
                    case Position.SS: return 0.80 # SURPRISING, BUT ACCORDING TO WOTC TESTS ITS RIGHT
                    case Position.CF: return 1.0
                    case Position.OF: return 0.89
                    case Position.LFRF: return 0.75
                    case Position.IF: return 1.0
            case '2001':
                match position:
                    case Position.CA: return 1.3
                    case Position._1B: return 0.5
                    case Position._2B: return 1.3
                    case Position._3B: return 1.0
                    case Position.SS: return 1.3
                    case Position.CF: return 1.1
                    case Position.OF: return 1.0
                    case Position.LFRF: return 0.65
                    case Position.IF: return 1.0
            case '2002':
                match position:
                    case Position.CA: return 1.25
                    case Position._1B: return 0.5
                    case Position._2B: return 1.0
                    case Position._3B: return 1.0
                    case Position.SS: return 1.1
                    case Position.CF: return 1.0
                    case Position.OF: return 1.0
                    case Position.LFRF: return 0.75
                    case Position.IF: return 1.0
            case '2003':
                match position:
                    case Position.CA: return 1.0
                    case Position._1B: return 0.5
                    case Position._2B: return 1.15
                    case Position._3B: return 1.10
                    case Position.SS: return 1.20
                    case Position.CF: return 1.0
                    case Position.OF: return 0.95
                    case Position.LFRF: return 0.75
                    case Position.IF: return 1.0
            case '2004' | '2005':
                match position:
                    case Position.CA: return 1.0
                    case Position._1B: return 0.5
                    case Position._2B: return 1.0
                    case Position._3B: return 1.0
                    case Position.SS: return 1.0
                    case Position.CF: return 1.0
                    case Position.OF: return 1.0
                    case Position.LFRF: return 1.0
                    case Position.IF: return 1.0
            case 'CLASSIC' | 'EXPANDED':
                match position:
                    case Position.CA: return 1.4
                    case Position._1B: return 0.5
                    case Position._2B: return 1.0
                    case Position._3B: return 1.0
                    case Position.SS: return 1.0
                    case Position.CF: return 1.0
                    case Position.OF: return 1.0
                    case Position.LFRF: return 0.75
                    case Position.IF: return 1.0
        return 1.0

    def pts_position_defense_value_range(self, position:Position) -> ValueRange:
        """Returns the min and max values for the defensive points for a given position and set."""

        # DEFINE MINIMUM/MAXIMUM
        min = 0
        max = self.position_defense_max(position=position)

        # MAKE ANY ADJUSTMENTS PER SET
        match self:
            case Set._2002:
                match position:
                    case Position.CA: 
                        min = 3
                        max = 9
        return ValueRange(min = min, max = max)

    def pts_command_out_multiplier(self, command:int, outs:int, subtype: PlayerSubType) -> float:
        return 1.0
        
    def pts_allow_negatives(self, player_sub_type:PlayerSubType) -> bool:
        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return False
                    case PlayerSubType.STARTING_PITCHER: return False
                    case PlayerSubType.RELIEF_PITCHER: return False
            case '2001' | 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return True
                    case PlayerSubType.STARTING_PITCHER: return True
                    case PlayerSubType.RELIEF_PITCHER: return True
            case '2002':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return True
                    case PlayerSubType.STARTING_PITCHER: return True
                    case PlayerSubType.RELIEF_PITCHER: return True
            case '2003':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return False
                    case PlayerSubType.STARTING_PITCHER: return True
                    case PlayerSubType.RELIEF_PITCHER: return True
            case '2004' | '2005' | 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return True
                    case PlayerSubType.STARTING_PITCHER: return True
                    case PlayerSubType.RELIEF_PITCHER: return True

    def pts_decay_rate_and_start(self, player_sub_type:PlayerSubType) -> float:
        """Returns the decay rate and starting point value for the normalization process.
        Depends on player subtype

        Args:
            player_sub_type (PlayerSubType): The player subtype (position player, starting pitcher, relief pitcher)

        Returns:
            float: The decay rate
            float: The starting point value
        """

        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.75, 500
                    case PlayerSubType.STARTING_PITCHER: return 0.525, 400
                    case PlayerSubType.RELIEF_PITCHER: return 0.55, 100
            case '2001' | 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.75, 500
                    case PlayerSubType.STARTING_PITCHER: return 0.55, 425
                    case PlayerSubType.RELIEF_PITCHER: return 0.85, 200
            case '2002':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.99, 500
                    case PlayerSubType.STARTING_PITCHER: return 0.85, 300
                    case PlayerSubType.RELIEF_PITCHER: return 0.90, 100
            case '2003':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.70, 500
                    case PlayerSubType.STARTING_PITCHER: return 0.75, 300
                    case PlayerSubType.RELIEF_PITCHER: return 0.70, 110
            case '2004':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.65, 400
                    case PlayerSubType.STARTING_PITCHER: return 0.60, 400
                    case PlayerSubType.RELIEF_PITCHER: return 0.52, 140
            case '2005' | 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.65, 400
                    case PlayerSubType.STARTING_PITCHER: return 0.52, 400
                    case PlayerSubType.RELIEF_PITCHER: return 0.55, 150
        
        # DEFAULT IS NONE
        return None

    @property
    def pts_gb_min_max_dict(self) -> ValueRange:
        return ValueRange(min = 0.3, max = 0.5)
    
    def pts_ip_multiplier(self, player_sub_type:PlayerSubType, ip:int) -> float:
        """Apply a multiplier to the negative IP points for a player subtype and IP value."""

        match player_sub_type:
            case PlayerSubType.RELIEF_PITCHER:
                match self.value:
                    case '2000':
                        match ip:
                            case 2: return 2.10
                            case 3: return 2.40
                    case '2001' | 'CLASSIC':
                        match ip:
                            case 2: return 1.55
                            case 3: return 2.00
                    case '2002':
                        match ip:
                            case 2: return 1.15
                            case 3: return 1.65
                    case '2003':
                        match ip:
                            case 2: return 1.10
                            case 3: return 1.60
                    case '2004':
                        match ip:
                            case 2: return 1.35
                            case 3: return 1.85
                    case '2005' | 'EXPANDED':
                        match ip:
                            case 2: return 1.20
                            case 3: return 1.70
            case PlayerSubType.STARTING_PITCHER:
                match self.value:
                    case '2000':
                        match ip:
                            case 4: return 0.70
                            case 5: return 0.85
                            case 9: return 1.02
                    case '2001' | 'CLASSIC':
                        match ip:
                            case 4: return 0.75
                            case 5: return 0.925
                            case 9: return 1.04
                    case '2002' | '2003':
                        match ip:
                            case 4: return 0.80
                            case 5: return 0.97
                            case 7: return 1.01
                            case 8: return 1.03
                            case 9: return 1.04
                    case '2004':
                        match ip:
                            case 4: return 0.80
                            case 5: return 0.97
                            case 8: return 1.00
                            case 9: return 1.04
                    case '2005' | 'EXPANDED':
                        match ip:
                            case 4: return 0.80
                            case 5: return 0.97
                            case 8: return 1.00
                            case 9: return 1.04

        return 1.0

    @property
    def pts_use_max_for_defense(self) -> bool:
        """Some sets use a max defensive PT value for multi-position players, others do not."""
        return self.value in ['2000', '2001']

    def pts_position_adjustment(self, positions: list[Position]) -> int:
        """Apply adjustment to the positional points for a given position and set.
        
        For multi-position players, the adjustment is taken as an avg.
        """

        pts_adjustments: list[int] = []
        for position in positions:
            match self:
                case Set._2000:
                    match position:
                        case Position.CL: pts_adjustments.append(25)
                case Set._2002: 
                    match position:
                        case Position.DH: pts_adjustments.append(-35)
                        case Position.CL: pts_adjustments.append(15)
        
        return sum(pts_adjustments) if len(pts_adjustments) > 0 else 0

    # ---------------------------------------
    # POINTS RANGES FOR PERCENTILES
    # ---------------------------------------

    def pts_range_for_metric(self, metric:PointsMetric, player_sub_type:PlayerSubType) -> ValueRange:
        match metric:
            case PointsMetric.ONBASE:
                return self.pts_obp_percentile_range(player_sub_type=player_sub_type)
            case PointsMetric.AVERAGE:
                return self.pts_ba_percentile_range(player_sub_type=player_sub_type)
            case PointsMetric.SLUGGING:
                return self.pts_slg_percentile_range(player_sub_type=player_sub_type)
            case PointsMetric.SPEED | PointsMetric.IP:
                return self.pts_speed_or_ip_percentile_range(player_sub_type=player_sub_type)
            case PointsMetric.HOME_RUNS:
                return self.pts_hr_percentile_range
            case PointsMetric.COMMAND:
                return self.pts_command_percentile_range(player_sub_type=player_sub_type)

    def pts_obp_percentile_range(self, player_sub_type:PlayerSubType) -> ValueRange:
        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.245, max = 0.385)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.190, max = 0.43)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.285, max = 0.450)
            case '2001' | 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.240, max = 0.400)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.240, max = 0.385)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.295, max = 0.450)
            case '2002':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.250, max = 0.380)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.250, max = 0.355)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.295, max = 0.440)
            case '2003':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.250, max = 0.390)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.240, max = 0.400)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.285, max = 0.430)
            case '2004':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.220, max = 0.350)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.375)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.300, max = 0.415)
            case '2005' | 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.220, max = 0.390)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.200, max = 0.390)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.300, max = 0.415)

    def pts_ba_percentile_range(self, player_sub_type:PlayerSubType) -> ValueRange:
        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.230, max = 0.330)
            case '2001' | 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.225, max = 0.330)
            case '2002':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.290)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.225, max = 0.330)
            case '2003':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.290)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.290)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.245, max = 0.320)
            case '2004':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.280)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.280)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.245, max = 0.315)
            case '2005' | 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.280)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.280)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.245, max = 0.330)

    def pts_slg_percentile_range(self, player_sub_type:PlayerSubType) -> ValueRange:
        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.350, max = 0.500)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.300, max = 0.600)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.350, max = 0.550)
            case '2001' | 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.340, max = 0.500)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.345, max = 0.500)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.355, max = 0.545)
            case '2002':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.350, max = 0.480)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.330, max = 0.445)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.370, max = 0.550)
            case '2003':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.350, max = 0.470)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.330, max = 0.500)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.360, max = 0.550)
            case '2004':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.320, max = 0.450)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.320, max = 0.450)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.380, max = 0.545)
            case '2005' | 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.320, max = 0.450)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.320, max = 0.450)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.380, max = 0.545)

    def pts_speed_or_ip_percentile_range(self, player_sub_type:PlayerSubType) -> ValueRange:
        match player_sub_type:
            case PlayerSubType.POSITION_PLAYER:
                match self:
                    case Set._2000: return ValueRange(min = 12, max = 20)
                    case Set._2002: return ValueRange(min = 12, max = 19)
                    case _: return ValueRange(min = 10, max = 20)
            case PlayerSubType.RELIEF_PITCHER:
                return ValueRange(min = 1, max = 2) # IP
            case PlayerSubType.STARTING_PITCHER:
                return ValueRange(min = 5, max = 8) # IP

    def pts_command_percentile_range(self, player_sub_type:PlayerSubType) -> ValueRange:
        match player_sub_type:
            case PlayerSubType.POSITION_PLAYER:
                onbase_min = 9 if self.has_expanded_chart else 6
                onbase_max = 13 if self.has_expanded_chart else 11
                return ValueRange(min = onbase_min, max = onbase_max)
            case PlayerSubType.RELIEF_PITCHER | PlayerSubType.STARTING_PITCHER:
                return ValueRange(min = 2, max = 6)
            
    @property
    def pts_hr_percentile_range(self) -> ValueRange:
        return ValueRange(min = 10, max = 35)

    # ---------------------------------------
    # CARD SIZING
    # ---------------------------------------

    @property
    def card_size(self) -> tuple[int,int]:
        return (1500,2100)

    @property
    def card_size_final(self) -> tuple[int,int]:
        return (1488,2079)

    @property
    def card_border_padding(self) -> tuple[int,int]:
        return 72

    @property
    def card_size_bordered(self) -> tuple[int,int]:
        default_width, default_height = self.card_size
        return (default_width + int(self.card_border_padding*2), default_height + int(self.card_border_padding*2))

    @property
    def card_size_bordered_final(self) -> tuple[int,int]:
        default_width, default_height = self.card_size_final
        return (default_width + int(self.card_border_padding*2), default_height + int(self.card_border_padding*2))

    # ---------------------------------------
    # IMAGES
    # ---------------------------------------

    @property
    def template_year(self) -> str:
        match self.value:
            case '2005': return '2004'
            case _: return self.year

    def template_custom_extension(self, parallel: ImageParallel) -> str:
        """Add extension to the template image path for a custom parallel. """

        match parallel:
            case ImageParallel.GOLD_FRAME:
                match self.value:
                    case '2002': return '-NO-NAME'
    
        return ''

    @property
    def has_dark_mode_template(self) -> bool:
        return self.value not in ['2004','2005',]

    @property
    def use_alternate_team_logo(self) -> bool:
        return self.is_after_03

    @property
    def super_season_year_text_color(self) -> str:
        return "#ffffff" if self.is_showdown_bot else "#982319"

    def super_season_year_paste_coordinates(self, is_multi_year:bool) -> tuple[int,int]:
        if is_multi_year:
            match self.value:
                case 'CLASSIC' | 'EXPANDED': return (122,265)
                case '2004' | '2005': return (126,110)
                case _: return (26,290)
        else:
            match self.value:
                case '2000' | '2001' | '2002' | '2003': return (24,282)
                case '2004' | '2005': return (135,90)
                case 'CLASSIC' | 'EXPANDED': return (133,252)

    @property
    def show_super_season_accolades(self) -> bool:
        return self.is_wotc
    
    @property
    def super_season_image_index(self) -> str:
        match self.value:
            case '2004' | '2005': return '2'
            case 'CLASSIC' | 'EXPANDED': return '3'
            case _: return '1'

    def super_season_text_length_cutoff(self, index:int = 1) -> int:
        if self.is_showdown_bot:
            return 14
        
        match index:
            case 1: return 16 if self.is_after_03 else 19
            case 2: return 15 if self.is_after_03 else 19
            case 3: return 11 if self.is_after_03 else 19

    @property
    def convert_final_image_to_rgb(self) -> bool:
        return self.value in ['2002','2004','2005','CLASSIC','EXPANDED',]
    
    @property
    def is_metadata_text_uppercased(self) -> bool:
        return self.value in ['2002','2004','2005']

    @property
    def small_name_text_length_cutoff(self) -> int:
        match self:
            case Set._2000: return 19
            case Set._2002: return 18
            case Set._2004 | Set._2005: return 18
            case Set.CLASSIC | Set.EXPANDED: return 18
            case _: return 20
    
    @property
    def has_unified_set_and_year_strings(self) -> bool:
        return self.value in ['2000', '2001', '2002']
    
    @property
    def enable_cooperstown_special_edition(self) -> bool:
        return self.value in ['2002','2003','2004','2005',]

    @property
    def has_split_first_and_last_names(self) -> bool:
        return self.value == '2001'
    
    @property
    def is_team_logo_drop_shadow(self) -> bool:
        return self.value in ['CLASSIC','EXPANDED']
    
    @property
    def is_space_between_position_and_defense(self) -> bool:
        return self not in [Set.CLASSIC, Set.EXPANDED]

    def is_special_edition_name_styling(self, special_edition:SpecialEdition) -> bool:
        # SPECIAL EDITIONS
        match special_edition:
            case SpecialEdition.ASG_2024:
                return self.value in ['2000','2001']
        
        return False

    # ---------------------------------------
    # PLAYER IMAGE
    # ---------------------------------------

    @property
    def player_image_gdrive_folder_id(self) -> str:
        return '1htwN6r-9QNHJzg6Jq56dGXuJxD2QNaGv' # UNIVERSAL
    
    def player_image_crop_size(self, special_edition:SpecialEdition = SpecialEdition.NONE) -> tuple[int,int]:
        match self.value:
            case '2000':
                if special_edition == SpecialEdition.ASG_2024: return (1200,1680) # MATCH 01 IF ASG
                else: return (1500,2100)
            case '2001': return (1200,1680)
            case '2002' | '2003': return (1305,1827)
            case '2004' | '2005': 
                if special_edition == SpecialEdition.ASG_2024: return (1350,1890)
                else: return (1500,2100)
            case 'CLASSIC' | 'EXPANDED': return (1200,1680)

    def player_image_crop_adjustment(self, special_edition:SpecialEdition = SpecialEdition.NONE) -> tuple[int,int]:
        match self.value:
            case '2000':
                if special_edition == SpecialEdition.ASG_2024: return (-35,-460) # MATCH 01 IF ASG
                else: return (-25,-300)
            case '2001': return (-35,-460)
            case '2002': return (75,-250)
            case '2003': return (75,-150)
            case '2004' | '2005': 
                if special_edition == SpecialEdition.ASG_2024: return (0,int((self.player_image_crop_size(special_edition)[1] - 2100) / 2))
                else: return (0,0)
            case 'CLASSIC' | 'EXPANDED': return (0,int((self.player_image_crop_size(special_edition)[1] - 2100) / 2))
            
    def player_image_components_list(self, is_special:bool=False) -> list[PlayerImageComponent]:
        if is_special:
            match self.value:
                case '2000': return [PlayerImageComponent.NAME_CONTAINER_2000, PlayerImageComponent.GLOW]
                case '2001': return [PlayerImageComponent.GLOW]
                case '2002' | '2003' | '2004' | '2005': return [PlayerImageComponent.BACKGROUND, PlayerImageComponent.GLOW]
                case 'CLASSIC' | 'EXPANDED': return [PlayerImageComponent.BACKGROUND, PlayerImageComponent.SHADOW]
        else:
            match self.value:
                case '2000': return [PlayerImageComponent.NAME_CONTAINER_2000, PlayerImageComponent.GLOW]
                case '2001': return [PlayerImageComponent.GLOW]
                case '2002' | '2003' | '2004' | '2005': return [PlayerImageComponent.BACKGROUND]
                case 'CLASSIC' | 'EXPANDED': return [PlayerImageComponent.BACKGROUND, PlayerImageComponent.SHADOW]

    def player_image_component_crop_adjustment(self, component: PlayerImageComponent, special_edition: SpecialEdition) -> tuple[int,int]:
        """Return crop adjustment for player image component and special edition.
        
        Args:
            component: PlayerImageComponent
            special_edition: SpecialEdition

        Returns:
            tuple[int,int]: (x,y) crop adjustment coordinates
        """

        # COMPONENTS
        match component:
            case PlayerImageComponent.GOLD_FRAME:
                match self.value:
                    case '2000': return (-20, 0)
        
        return None
    
    def player_image_component_size_adjustment(self, component: PlayerImageComponent) -> float:
        match component:
            case PlayerImageComponent.GOLD_FRAME:
                match self.value:
                    case '2001': return 1.025
                    case '2002': return 1.01
                    case 'EXPANDED' | 'CLASSIC': return 1.025
        
        return None
        
    def player_image_component_sort_index_adjustment(self, component: PlayerImageComponent, special_edition: SpecialEdition) -> int:
        """Returns customized sort order for certain image components for this special edition image.
        
        Args:
            component: PlayerImageComponent
            special_edition: SpecialEdition

        Returns:
            int: sort index adjustment
        """
        
        match special_edition:
            case SpecialEdition.ASG_2024:
                match self:
                    case _:
                        if 'CUSTOM_FOREGROUND' in component.name:
                            return PlayerImageComponent.CUSTOM_BACKGROUND.layering_index
        
        return None

    # ---------------------------------------
    # STAT HIGHLIGHTS
    # ---------------------------------------

    @property
    def stat_highlights_metric_limit(self) -> int:
        match self.value:
            case '2003': return 3
            case '2004' | '2005': return 6
            case 'CLASSIC' | 'EXPANDED': return 5
            case _: return 4

    def stat_highlight_container_size(self, stats_limit:int, is_year_and_stats_period_boxes:bool=False, is_expansion:bool=False, is_set_number:bool=False, is_period_box:bool=False, is_multi_year:bool=False, is_full_career:bool=False) -> str:
        """ Return size class for stat highlight container (ex: LARGE, MEDIUM, SMALL) """
        match self.value:
            case 'CLASSIC' | 'EXPANDED':
                # NOTE: PERIOD BOX IS COUNTED TWICE
                num_extra_spaces = len([b for b in [is_set_number, is_expansion, is_period_box, is_period_box, is_multi_year or is_full_career] if b])
                match num_extra_spaces:
                    case 4: return 'SMALL'
                    case 3: return 'SMALL+'
                    case 2: return 'MEDIUM'
                    case 0 | 1: return 'LARGE'
                    case _: return 'SMALL'
            case '2003': return 'MEDIUM' if is_year_and_stats_period_boxes else 'LARGE'
            case _: return 'LARGE' if stats_limit >= self.stat_highlights_metric_limit else 'MEDIUM'

    # ---------------------------------------
    # TEMPLATE IMAGE
    # ---------------------------------------

    def template_component_paste_coordinates(self, component:TemplateImageComponent, player_type:PlayerType=None, is_multi_year:bool=False, is_full_career:bool=False, expansion:Expansion = Expansion.BS, is_regular_season:bool = True, special_edition:SpecialEdition = SpecialEdition.NONE) -> tuple[int,int]:
        match component:
            case TemplateImageComponent.TEAM_LOGO:
                match self.value:
                    case '2000': return (1200,1086)
                    case '2001': return (78,1584)
                    case '2002': return (80,1380)
                    case '2003': return (1179,1074)
                    case '2004' | '2005': return (1180,1460)
                    case 'CLASSIC' | 'EXPANDED': return (1160,1345)
            case TemplateImageComponent.COOPERSTOWN:
                match self.value:
                    case '2004' | '2005': return (981,1335)
            case TemplateImageComponent.PLAYER_NAME:
                if special_edition == SpecialEdition.ASG_2024 and self in [Set._2000, Set._2001]:
                    return (360, 1565)
                match self.value:
                    case '2000': return (150,-1225)
                    case '2001': return (105,0)
                    case '2002': return (1275,0)
                    case '2003': return (1365,0)
                    case '2004' | '2005': return (276,1605)
                    case 'CLASSIC' | 'EXPANDED': return (290,1570)
            case TemplateImageComponent.PLAYER_NAME_SMALL:
                if special_edition == SpecialEdition.ASG_2024 and self in [Set._2000, Set._2001]:
                    return (360, 1565)
                match self.value:
                    case '2000': return (165,-1225)
                    case '2001': return (105,0)
                    case '2002': return (1285,0)
                    case '2003': return (1375,0)
                    case '2004' | '2005': return (276,1610)
                    case 'CLASSIC' | 'EXPANDED': return (290,1585)
            case TemplateImageComponent.CHART:
                match self.value:
                    case '2000' | '2001': return (981,1335) if player_type.is_pitcher else (981,1317)
                    case '2002': return (948,1593)
                    case '2003': return (981,1518)
                    case '2004' | '2005': return (0,1779)
                    case 'CLASSIC' | 'EXPANDED': return (40,1903)
            case TemplateImageComponent.METADATA:
                match self.value:
                    case '2000' | '2001': return (0,0)
                    case '2002': return (810,1605)
                    case '2003': return (825,1530)
                    case '2004' | '2005': return (282,1710)
                    case 'CLASSIC' | 'EXPANDED': return (320,1680)
            case TemplateImageComponent.SET:
                match self.value:
                    case '2000' | '2001': return (129,2016)
                    case '2002': return (60,1860)
                    case '2003': return (93,1785)
                    case '2004' | '2005': return (1344,1911)
                    case 'CLASSIC' | 'EXPANDED': return (1070,1995)
            case TemplateImageComponent.YEAR_CONTAINER:
                match self.value:
                    case '2000' | '2001': return (1250,1865)
                    case '2002': return (60,2038)
                    case '2003': return (482,1775)
                    case '2004' | '2005': return (1100,1450)
            case TemplateImageComponent.NUMBER:
                match self.value:
                    case '2002': return (120,1785)
                    case '2003': return (116,1785)
                    case '2004' | '2005': return (1191,1911)
                    case 'CLASSIC' | 'EXPANDED':
                        xadjust, yadjust = (-12, 0) if expansion == Expansion.TD else (0,0)
                        return ( (465 if expansion.has_image else 355) + xadjust, 2000 + yadjust )
            case TemplateImageComponent.SUPER_SEASON:
                match self.value:
                    case '2000': return (1200,900)
                    case '2001': return (78,1584)
                    case '2002': return (45,1113)
                    case '2003': return (1041,786)
                    case '2004': return (1071,1164)
                    case '2005': return (1071,1164)
                    case 'CLASSIC' | 'EXPANDED': return (1071,1150)
            case TemplateImageComponent.ROOKIE_SEASON:
                match self.value:
                    case '2000': return (1200,1086)
                    case '2001': return (1108,1040)
                    case '2002': return (80,1360)
                    case '2003': return (1085,1025)
                    case '2004' | '2005': return (1100,1400)
                    case 'CLASSIC' | 'EXPANDED': return (1075,1340)
            case TemplateImageComponent.ROOKIE_SEASON_YEAR_TEXT:
                return (40, 145)
            case TemplateImageComponent.POSTSEASON:
                match self.value:
                    case '2000': return (1200,1045)
                    case '2001': return (1108,1015)
                    case '2002': return (80,1275)
                    case '2003': return (1085,1010)
                    case '2004' | '2005': return (1100,1370)
                    case 'CLASSIC' | 'EXPANDED': return (1075,1305)
            case TemplateImageComponent.POSTSEASON_YEAR_TEXT_BOX:
                return (288, 745)
            case TemplateImageComponent.POSTSEASON_YEAR_TEXT:
                return (288, 755)
            case TemplateImageComponent.EXPANSION:
                match self.value:
                    case '2000' | '2001': return (1287,1855)
                    case '2002': 
                        xadjust, yadjust = (20, -17) if expansion == Expansion.TD else (0,0)
                        return (652 + xadjust, 1770 + yadjust) 
                    case '2003': return (275,1782)
                    case '2004' | '2005': return (1060,1910)
                    case 'CLASSIC' | 'EXPANDED': 
                        xadjust, yadjust = (0, -12) if expansion == Expansion.TD else (0,0)
                        return (350 + xadjust, 1990 + yadjust)
            case TemplateImageComponent.COMMAND:
                match self.value:
                    case 'CLASSIC' | 'EXPANDED': return (75,1565)
                    case _: return (0,0)
            case TemplateImageComponent.STYLE:
                match self.value:
                    case 'CLASSIC' | 'EXPANDED': return (72,1980)
            case TemplateImageComponent.STYLE_LOGO_BG:
                match self.value:
                    case 'CLASSIC' | 'EXPANDED': return (180,4)
            case TemplateImageComponent.STYLE_LOGO:
                match self.value:
                    case 'CLASSIC': return (203,13)
                    case 'EXPANDED': return (210,14)
            case TemplateImageComponent.STYLE_TEXT:
                match self.value:
                    case 'CLASSIC': return (35,20)
                    case 'EXPANDED': return (15,20)
            case TemplateImageComponent.BOT_LOGO:
                match self.value:
                    case '2000' | '2001': return (1250,1945)
                    case '2002': return (62,1900)
                    case '2003': return (655,1705)
                    case '2004' | '2005': return (1268,1965)
                    case 'CLASSIC' | 'EXPANDED': return (1320,1975)
            case TemplateImageComponent.SPLIT:
                match self.value:
                    case '2000': return (330, 1860)
                    case '2001': return (330, 1860)
                    case '2002': return (290, 1850)
                    case '2003': return (380, 1775)
                    case '2004' | '2005': return (80, 1912)
                    case 'CLASSIC' | 'EXPANDED': 
                        if is_full_career: return (865,1990)
                        if is_multi_year: return (800,1990)
                        return (925,1990)
            case TemplateImageComponent.STAT_HIGHLIGHTS:
                match self.value:
                    case '2000' | '2001': return (330 if is_regular_season else 612, 1862)
                    case '2002': return (290 if is_regular_season else 572, 1850)
                    case '2003': return (77, 1712)
                    case '2004' | '2005': return (80, 1912) if is_regular_season else (362, 1912)
                    case 'CLASSIC' | 'EXPANDED': return (349, 1990)

    def template_component_size(self, component:TemplateImageComponent) -> tuple[int,int]:
        match component:
            case TemplateImageComponent.TEAM_LOGO: 
                match self.value:
                    case '2000': return (225,225)
                    case '2001': return (255,255)
                    case '2002': return (450,450)
                    case '2003': return (270,270)
                    case '2004' | '2005': return (200,200)
                    case 'CLASSIC' | 'EXPANDED': return (275,275)
            case TemplateImageComponent.PLAYER_NAME: 
                match self.value:
                    case '2000': return (2100,300)
                    case '2001': return (1545,300)
                    case '2002': return (1395,300)
                    case '2003': return (3300,300)
                    case '2004' | '2005': return (900, 300)
                    case 'CLASSIC' | 'EXPANDED': return (1150, 300)
            case TemplateImageComponent.SUPER_SEASON: 
                match self.value:
                    case '2000' | '2001': return (312,480)
                    case '2002': return (468,720)
                    case '2003': return (390,600)
                    case '2004' | '2005': return (339,522)
                    case 'CLASSIC' | 'EXPANDED': return (400,480)
            case TemplateImageComponent.ROOKIE_SEASON: 
                match self.value:
                    case '2000': return (273,273)
                    case '2001': return (300,300)
                    case '2002': return (575,575)
                    case '2003': return (375,375)
                    case '2004' | '2005': return (339,339)
                    case 'CLASSIC' | 'EXPANDED': return (380,380)
            case TemplateImageComponent.POSTSEASON: 
                match self.value:
                    case '2000': return (273,273)
                    case '2001': return (300,300)
                    case '2002': return (575,575)
                    case '2003': return (375,375)
                    case '2004' | '2005': return (339,339)
                    case 'CLASSIC' | 'EXPANDED': return (380,380)
            case TemplateImageComponent.POSTSEASON_YEAR_TEXT_BOX: 
                return (415, 140)
            case TemplateImageComponent.BOT_LOGO: 
                match self.value:
                    case '2000' | '2001': return (150,150)
                    case '2002': return (145,145)
                    case '2003': return (150,150)
                    case '2004' | '2005': return (130,130)
                    case 'CLASSIC' | 'EXPANDED': return (100,100)

    def template_component_font_size(self, component: TemplateImageComponent) -> int:
        match component:
            case TemplateImageComponent.CHART:
                match self.value:
                    case '2000' | '2001': return 148
                    case '2002': return 117
                    case '2003': return 145
                    case '2004' | '2005': return 144
                    case 'CLASSIC' | 'EXPANDED': return 158
    
    def template_component_font_spacing(self, component: TemplateImageComponent) -> int:
        match component:
            case TemplateImageComponent.CHART:
                match self.value:
                    case '2000' | '2001': return 31
                    case '2002': return 25
                    case '2003': return 26
                    case '2004' | '2005' | 'CLASSIC' | 'EXPANDED': return 75

    def template_component_font_color(self, component: TemplateImageComponent, is_dark_mode:bool=False) -> str:

        # REUSED COLORS
        black = "#000000"
        white = "#FFFFFF"
        dark_gray = "#767676"
        mid_gray = "#888686"
        mid_light_gray = "#929191"
        light_gray = "#B5B4B5"

        match component:
            case TemplateImageComponent.STYLE_TEXT:
                match self:
                    case Set.CLASSIC | Set.EXPANDED: return light_gray if is_dark_mode else dark_gray
                    case _: return white
            case TemplateImageComponent.SET: # YEAR
                match self:
                    case Set.CLASSIC | Set.EXPANDED: return mid_light_gray if is_dark_mode else mid_gray
                    case _: return white
            case TemplateImageComponent.NUMBER:
                match self:
                    case Set._2003: return black
                    case Set.CLASSIC | Set.EXPANDED: return mid_light_gray if is_dark_mode else mid_gray
                    case _: return white
            case TemplateImageComponent.SPLIT | TemplateImageComponent.STAT_HIGHLIGHTS:
                match self:
                    case Set.CLASSIC | Set.EXPANDED: return mid_light_gray if is_dark_mode else dark_gray
                    case _: return white

    def template_component_color(self, component: TemplateImageComponent, parallel: ImageParallel) -> str:
        """Return color string for a template image component """

        match component:
            case TemplateImageComponent.PLAYER_NAME:
                match self.value:
                    case '2000' | '2001': return "#D2D2D2"
                    case '2002': return "#b5b4b5"
                    case _: return "#FFFFFF"

        return None

    # ---------------------------------------
    # BASELINE PLAYERS
    # ---------------------------------------

    def opponent_chart(self, player_sub_type:PlayerSubType, era:Era, year_list: list[int]) -> Chart:
        chart = self.wotc_baseline_chart(player_type=player_sub_type.parent_type.opponent_type, my_type=player_sub_type)
        chart.adjust_for_era(era.value, year_list=year_list)
        return chart

    def wotc_baseline_chart(self, player_type: PlayerType, my_type: PlayerSubType) -> Chart:
        is_rp = my_type == PlayerSubType.RELIEF_PITCHER
        match player_type:
            case PlayerType.PITCHER:
                match self:
                    case Set._2000:
                        return Chart(
                            is_baseline = True,
                            is_pitcher=player_type.is_pitcher,
                            set=self.value,
                            era=Era.STEROID,
                            is_expanded=self.has_expanded_chart,
                            command=2.75,
                            values={
                                'PU': 1.00,
                                'SO': 4.27,
                                'GB': 6.00,
                                'FB': 4.73,
                                'BB': 1.35,
                                '1B': 1.88,
                                '2B': 0.68,
                                '3B': 0.00,
                                'HR': 0.09,
                            }
                        )
                    case Set._2001 | Set.CLASSIC:
                        return Chart(
                            is_baseline = True,
                            is_pitcher=player_type.is_pitcher,
                            set=self.value,
                            era=Era.STEROID,
                            is_expanded=self.has_expanded_chart,
                            command=3.00,
                            values={
                                'PU': 1.00,
                                'SO': 3.75,
                                'GB': 5.74,
                                'FB': 5.51,
                                'BB': 1.30,
                                '1B': 1.83,
                                '2B': 0.69,
                                '3B': 0.01,
                                'HR': 0.17,
                            }
                        )
                    case Set._2002:
                        return Chart(
                            is_baseline = True,
                            is_pitcher=player_type.is_pitcher,
                            set=self.value,
                            era=Era.STEROID,
                            is_expanded=self.has_expanded_chart,
                            command=3.25,
                            values={
                                'PU': 1.30,
                                'SO': 4.10,
                                'GB': 5.70,
                                'FB': 5.75,
                                'BB': 1.08,
                                '1B': 1.24,
                                '2B': 0.58,
                                '3B': 0.01,
                                'HR': 0.24,
                            }
                        )
                    case Set._2003:
                        return Chart(
                            is_baseline = True,
                            is_pitcher=player_type.is_pitcher,
                            set=self.value,
                            era=Era.STEROID,
                            is_expanded=self.has_expanded_chart,
                            command=3.80,
                            values={
                                'PU': 0.66,
                                'SO': 4.05,
                                'GB': 6.45,
                                'FB': 5.40,
                                'BB': 1.08,
                                '1B': 1.59,
                                '2B': 0.52,
                                '3B': 0.10,
                                'HR': 0.15,
                            }
                        )
                    case Set._2004 | Set._2005 | Set.EXPANDED:
                        return Chart(
                            is_baseline = True,
                            is_pitcher=player_type.is_pitcher,
                            set=self.value,
                            era=Era.STEROID,
                            is_expanded=self.has_expanded_chart,
                            command=3.80 + (0.00 if self == Set._2004 else -0.03),
                            values={
                                'PU': 0.65,
                                'SO': 4.00,
                                'GB': 6.45,
                                'FB': 5.45,
                                'BB': 1.20,
                                '1B': 1.49,
                                '2B': 0.53,
                                '3B': 0.07,
                                'HR': 0.16,
                            }
                        )
            case PlayerType.HITTER:
                match self:
                    case Set._2000:
                        return Chart(
                            is_baseline = True,
                            is_pitcher=player_type.is_pitcher,
                            set=self.value,
                            era=Era.STEROID,
                            is_expanded=self.has_expanded_chart,
                            command=7.40 + (0.2 if is_rp else 0),
                            values={
                                'PU': 0.00,
                                'SO': 0.75,
                                'GB': 1.52,
                                'FB': 1.05,
                                'BB': 4.92,
                                '1B': 8.01,
                                '2B': 1.60 + (-0.25 if is_rp else 0),
                                '3B': 0.30,
                                'HR': 1.85 + (0.25 if is_rp else 0),
                            }
                        )
                    case Set._2001 | Set.CLASSIC:
                        return Chart(
                            is_baseline = True,
                            is_pitcher=player_type.is_pitcher,
                            set=self.value,
                            era=Era.STEROID,
                            is_expanded=self.has_expanded_chart,
                            command=7.10 + (0.42 if is_rp else 0),
                            values={
                                'PU': 0.00,
                                'SO': 0.85,
                                'GB': 1.12 + (0.10 if is_rp else 0),
                                'FB': 1.15,
                                'BB': 5.10 + (0.65 if is_rp else 0),
                                '1B': 7.83 + (-0.90 if is_rp else 0),
                                '2B': 1.60 + (-0.15 if is_rp else 0),
                                '3B': 0.25,
                                'HR': 2.10 + (0.30 if is_rp else 0),
                            }
                        )
                    case Set._2002:
                        return Chart(
                            is_baseline = True,
                            is_pitcher=player_type.is_pitcher,
                            set=self.value,
                            era=Era.STEROID,
                            is_expanded=self.has_expanded_chart,
                            command=9.00 + (0.35 if is_rp else 0),
                            values={                                
                                'PU': 0.00,
                                'SO': 2.05 - (0.15 if is_rp else 0),
                                'GB': 3.25 - (0.10 if is_rp else 0),
                                'FB': 1.00,
                                'BB': 3.80 - (0.00 if is_rp else 0),
                                '1B': 6.80 - (0.00 if is_rp else 0),
                                '2B': 1.65 + (0.20 if is_rp else 0),
                                '3B': 0.15,
                                'HR': 1.30 + (0.05 if is_rp else 0),
                            }
                        )
                    case Set._2003:
                        return Chart(
                            is_baseline = True,
                            is_pitcher=player_type.is_pitcher,
                            set=self.value,
                            era=Era.STEROID,
                            is_expanded=self.has_expanded_chart,
                            command=8.35,
                            values={
                                'PU': 0.00,
                                'SO': 2.25,
                                'GB': 1.46 + (-0.70 if is_rp else 0),
                                'FB': 4.00 + (0.70 if is_rp else 0),
                                'BB': 3.50 + (-0.80 if is_rp else 0),
                                '1B': 5.85 + (1.30 if is_rp else 0),
                                '2B': 0.84 + (-0.50 if is_rp else 0),
                                '3B': 0.45,
                                'HR': 1.65,
                            }
                        )
                    case Set._2004 | Set._2005 | Set.EXPANDED:
                        is_04 = self == Set._2004
                        return Chart(
                            is_baseline = True,
                            is_pitcher=player_type.is_pitcher,
                            set=self.value,
                            era=Era.STEROID,
                            is_expanded=self.has_expanded_chart,
                            command=8.20,
                            values={                                
                                'PU': 0.00,
                                'SO': 2.40 + (-0.20 if is_04 else 0),
                                'GB': 0.90 + (0.10 if is_04 else 0),
                                'FB': 4.95 + (0.10 if is_04 else 0),
                                'BB': 4.00 + (-0.05 if is_04 else 0),
                                '1B': 6.20 + (0.05 if is_04 else 0),
                                '2B': 0.05,
                                '3B': 0.10,
                                'HR': 1.40,
                            }
                        )
