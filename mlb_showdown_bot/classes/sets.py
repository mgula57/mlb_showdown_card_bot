from enum import Enum

try:
    from .metadata import SpeedMetric
    from .player_position import PlayerType, PlayerSubType, Position
    from .metrics import Stat, PointsMetric
    from .value_range import ValueRange
    from .images import PlayerImageComponent, TemplateImageComponent, ImageParallel
    from .chart import Chart
except ImportError:
    from metadata import SpeedMetric
    from player_position import PlayerType, PlayerSubType, Position
    from metrics import Stat, PointsMetric
    from value_range import ValueRange
    from images import PlayerImageComponent, TemplateImageComponent, ImageParallel
    from chart import Chart


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

    @property
    def hr_rounding_cutoff(self) -> float:
        match self.name:
            case 'STEROID': return 0.85
            case 'STATCAST' | 'PITCH_CLOCK': return 0.70
            case _: return 0.75







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
    def min_onbase_single_plus(self) -> int:
        return 4 if self.has_classic_chart else 7
    
    @property
    def max_onbase_single_plus(self) -> int:
        return 12 if self.has_classic_chart else 16
    
    def speed_metric_multiplier(self, metric: SpeedMetric, use_variable_speed_multiplier:bool) -> float:
        if use_variable_speed_multiplier:
            return self.variable_speed_multiplier
        
        if metric == SpeedMetric.STOLEN_BASES:
            match self.value:
                case '2000': return 1.21
                case '2001': return 1.22
                case '2002': return 1.2
                case '2003': return 0.95
                case '2004': return 0.98
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
            case Position.CA: return 11 if self.value == '2001' else 12
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
                starting_x = 1050 if is_04_05 else 440
                starting_y = 1695 if is_04_05 else 2005
                distance_between_icons = 75 if is_04_05 else 80
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
                (16,0),(16,3),(16,4),(16,5),(16,6),
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
                (16,0),(16,3),(16,4),(16,5),(16,6),
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
                (16,0),(16,3),(16,4),(16,5),(16,6),
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
            ]
            case 'EXPANDED': return [
                (7,7),(7,8),(7,9),
                (8,5),(8,6),(8,7),(8,8),(8,9),(8,10),(8,11),
                (9,5),(9,6),(9,7),(9,8),(9,9),(9,10),(9,11),
                (10,5),(10,6),(10,7),(10,8),
                (11,5),(11,6),(11,7),(11,8),
                (12,5),(12,6),(12,7),
                (13,5),(13,6),(13,7),
                (14,5),(14,6),(14,7),
                (15,6),(15,7),(15,8),
                (16,0),(16,3),(16,4),(16,5),(16,6),
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
                (6,15),(6,16),(6,17),(6,18),(6,20),
            ]
            case '2001': return [
                (0,17),(0,18),
                (1,17),(1,18),
                (2,16),(2,17),(2,18),
                (3,14),(3,15),(3,16),(3,17),(3,18),
                (4,14),(4,15),(4,16),(4,17),(4,18),
                (5,14),(5,15),(5,16),(5,17),(5,18),(5,19),
                (6,14),(6,15),(6,16),(6,17),(6,18),(6,20),
            ]
            case '2002': return [
                (1,15),(1,16),(1,17),(1,18),
                (2,15),(2,16),(2,17),(2,18),(2,19),
                (3,15),(3,16),(3,17),(3,18),(3,19),
                (4,14),(4,15),(4,16),(4,17),(4,18),(4,19),
                (5,15),(5,16),(5,17),(5,18),
                (6,16),(6,17),(6,18),(6,20),
            ]
            case '2003': return [
                (1,15),(1,16),(1,18),
                (2,14),(2,15),(2,16),(2,18),
                (3,14),(3,15),(3,16),(3,17),(3,18),
                (4,14),(4,15),(4,16),(4,17),(4,18),
                (5,15),(5,16),(5,17),(5,18),
                (6,16),(6,17),(6,18),(6,20),
            ]
            case '2004' | '2005': return [
                (1,13),(1,14),(1,15),(1,16),(1,18),(1,19),
                (2,14),(2,15),(2,16),(2,18),(2,19),
                (3,15),(3,16),(3,17),(3,18),(3,19),
                (4,14),(4,15),(4,16),(4,17),(4,18),
                (5,12),(5,14),(5,15),(5,16),(5,17),(5,18),(5,19),
                (6,15),(6,16),(6,17),(6,18),(6,20),
            ]
            case 'CLASSIC': return [
                (0,17),(0,18),
                (1,17),(1,18),
                (1,16),(2,16),(2,17),(2,18),
                (3,14),(3,15),(3,16),(3,17),(3,18),(3,19),
                (4,14),(4,15),(4,16),(4,17),(4,18),
                (5,14),(5,15),(5,16),(5,17),(5,18),(5,19),
                (6,14),(6,15),(6,16),(6,17),(6,18),(6,20),
            ]
            case 'EXPANDED': return [
                (1,14),(1,15),(1,16),(1,17),(1,18),(1,19),
                (2,15),(2,16),(2,17),(2,18),(2,19),
                (3,15),(3,16),(3,17),(3,18),(3,19),
                (4,15),(4,16),(4,17),(4,18),(4,19),
                (5,14),(5,15),(5,16),(5,17),(5,18),(5,19),
                (6,14),(6,15),(6,16),(6,17),(6,18),(6,20),
            ]

    def command_out_combinations(self, player_type:PlayerType) -> list[tuple[int,int]]:
        return self.control_out_combinations if player_type.is_pitcher else self.onbase_out_combinations

    def command_out_accuracy_weighting(self, command:int, outs:int) -> float:
        command_out_str = f"{command}-{outs}"
        match self.value:
            case '2000':
                match command_out_str:
                    case '7-2' | '8-2' | '9-2': return 0.999
                    case '2-18': return 0.97
            case '2001':
                match command_out_str:
                    case '7-2' | '8-2' | '9-2': return 0.999
                    case '1-18': return 0.975
                    case '2-18': return 0.97
                    case '3-18' | '4-18': return 0.98
            case '2003':
                match command_out_str: 
                    case '1-18': return 0.99
                    case '2-18': return 0.98
                    case '3-17': return 0.99
                    case '3-18': return 0.99
                    case '4-18': return 0.98
            case '2004':
                match command_out_str: 
                    case '1-18': return 0.98
                    case '1-19': return 0.97
                    case '2-18': return 0.985
                    case '2-19': return 0.975
                    case '3-17': return 0.99
                    case '3-18': return 0.99
                    case '3-19': return 0.965
                    case '4-15': return 0.99
                    case '4-18': return 0.98

                    case '10-8': return 0.99
                    case '11-8': return 0.99
                    case '9-5': return 0.995
            case '2005':
                match command_out_str: 
                    case '1-18': return 0.99
                    case '1-19': return 0.97
                    case '2-18': return 0.985
                    case '2-19': return 0.975
                    case '3-17': return 0.99
                    case '3-18': return 0.99
                    case '3-19': return 0.965
                    case '4-15': return 0.99
                    case '4-18': return 0.98

                    case '10-8': return 0.99
                    case '11-8': return 0.99
                    case '9-5': return 0.995
            case 'CLASSIC':
                match command_out_str:
                    case '3-19' | '2-18' | '1-18': return 0.99
            case 'EXPANDED':
                match command_out_str:
                    case '3-19': return 0.98
                    case '3-18': return 0.99
                    case '2-18': return 0.993
                    case '1-18': return 0.99
                    case '2-19': return 0.98
                    case '1-19': return 0.99

        # DEFAULT TO 1.0
        return 1.00
    
    def chart_accuracy_slashline_weights(self, player_sub_type:PlayerSubType) -> dict[str, float]:
        match self.value:
            case '2000' | '2001':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return {
                        Stat.OBP.value: 3.0,
                        Stat.SLG.value: 1.0,
                    }
                    case PlayerSubType.STARTING_PITCHER | PlayerSubType.RELIEF_PITCHER: return {
                        Stat.OBP.value: 2.0,
                        Stat.SLG.value: 1.0,
                    }
            case '2002':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return {
                        Stat.OBP.value: 1.0,
                    }
                    case PlayerSubType.STARTING_PITCHER | PlayerSubType.RELIEF_PITCHER: return {
                        Stat.OBP.value: 2.0,
                        Stat.SLG.value: 1.0,
                    }
            case '2003':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return {
                        Stat.OBP.value: 1.0,
                    }
                    case PlayerSubType.STARTING_PITCHER | PlayerSubType.RELIEF_PITCHER: return {
                        Stat.OBP.value: 3.0,
                        Stat.SLG.value: 1.0,
                    }
            case '2004':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return {
                        Stat.OBP.value: 4.0,
                        Stat.SLG.value: 1.0,
                    }
                    case PlayerSubType.STARTING_PITCHER | PlayerSubType.RELIEF_PITCHER: return {
                        Stat.OBP.value: 3.0,
                        Stat.SLG.value: 1.0,
                    }
            case '2005':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return {
                        Stat.OBP.value: 2.5,
                        Stat.SLG.value: 1.0,
                    }
                    case PlayerSubType.STARTING_PITCHER | PlayerSubType.RELIEF_PITCHER: return {
                        Stat.OBP.value: 3.0,
                        Stat.SLG.value: 1.0,
                    }
            case 'CLASSIC' | 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return {
                        Stat.OBP.value: 1.5,
                        Stat.SLG.value: 1.0,
                    }
                    case PlayerSubType.STARTING_PITCHER | PlayerSubType.RELIEF_PITCHER: return {
                        Stat.OBP.value: 2.0,
                        Stat.SLG.value: 1.0,
                    }

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
    def pu_multiplier(self) -> float:
        match self.value:
            case '2000': return 2.25
            case '2001': return 2.5
            case '2002': return 2.8
            case '2003': return 2.2
            case '2004': return 2.05
            case '2005': return 2.4
            case 'CLASSIC': return 2.5
            case 'EXPANDED': return 2.4
    
    def gb_multiplier(self, player_type: PlayerType, era: Era) -> float:
        match player_type:
            case PlayerType.HITTER:
                match self.value:
                    case '2000':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL | Era.LIVE_BALL: return 1.10
                            case Era.INTEGRATION | Era.EXPANSION | Era.FREE_AGENCY: return 1.05
                            case Era.STEROID | Era.POST_STEROID: return 1.00
                            case Era.STATCAST | Era.PITCH_CLOCK: return 0.95
                    case '2001' | '2002' | '2003' | '2004' | '2005':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL | Era.LIVE_BALL: return 1.20
                            case Era.INTEGRATION | Era.EXPANSION | Era.FREE_AGENCY: return 1.15
                            case Era.STEROID | Era.POST_STEROID: return 1.10
                            case Era.STATCAST | Era.PITCH_CLOCK: return 1.00
                    case 'CLASSIC' | 'EXPANDED':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL | Era.LIVE_BALL: return 1.10
                            case Era.INTEGRATION | Era.EXPANSION | Era.FREE_AGENCY: return 1.05
                            case Era.STEROID | Era.POST_STEROID: return 1.00
                            case Era.STATCAST | Era.PITCH_CLOCK: return 0.90
            case PlayerType.PITCHER:
                match self.value:
                    case '2000':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL | Era.LIVE_BALL: return 1.05
                            case Era.INTEGRATION | Era.EXPANSION | Era.FREE_AGENCY: return 1.00
                            case Era.STEROID | Era.POST_STEROID: return 0.85
                            case Era.STATCAST | Era.PITCH_CLOCK: return 0.82
                    case '2001':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL | Era.LIVE_BALL: return 1.05
                            case Era.INTEGRATION | Era.EXPANSION | Era.FREE_AGENCY: return 1.00
                            case Era.STEROID: return 0.93
                            case Era.POST_STEROID: return 0.90
                            case Era.STATCAST | Era.PITCH_CLOCK: return 0.85
                    case '2002':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL | Era.LIVE_BALL: return 1.05
                            case Era.INTEGRATION | Era.EXPANSION | Era.FREE_AGENCY: return 1.00
                            case Era.STEROID: return 0.91
                            case Era.POST_STEROID: return 0.90
                            case Era.STATCAST | Era.PITCH_CLOCK: return 0.85
                    case '2003' | '2004' | '2005':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL | Era.LIVE_BALL: return 1.15
                            case Era.INTEGRATION | Era.EXPANSION | Era.FREE_AGENCY: return 1.10
                            case Era.STEROID: return 1.05
                            case Era.POST_STEROID: return 1.00
                            case Era.STATCAST | Era.PITCH_CLOCK: return 0.95
                    case 'CLASSIC' | 'EXPANDED':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL | Era.LIVE_BALL: return 1.10
                            case Era.INTEGRATION | Era.EXPANSION | Era.FREE_AGENCY: return 1.05
                            case Era.STEROID: return 1.00
                            case Era.POST_STEROID: return 0.95
                            case Era.STATCAST | Era.PITCH_CLOCK: return 0.90

    @property
    def hitter_so_results_soft_cap(self) -> int:
        match self.value:
            case '2002': return 4
            case _: return 3

    @property
    def hitter_so_results_hard_cap(self) -> int:
        match self.value:
            case '2000': return 5
            case '2002': return 7
            case _: return 6

    @property
    def hitter_single_plus_denominator_minimum(self) -> float:
        match self.value:
            case '2000' | '2001' | 'CLASSIC': return 3.2
            case '2002': return 7.0
            case '2003': return 6.0
            case '2004' | '2005' | 'EXPANDED': return 5.5
    
    @property
    def hitter_single_plus_denominator_maximum(self) -> float:
        match self.value:
            case '2000' | '2001' | 'CLASSIC': return 9.6
            case '2002': return 11.0
            case '2003' | '2004': return 10.5
            case '2005' | 'EXPANDED': return 9.75

    # ---------------------------------------
    # POINTS
    # ---------------------------------------

    @property
    def pts_normalizer_upper_limit(self) -> int:
        return 800
    
    def pts_metric_weight(self, player_sub_type:PlayerSubType, metric:PointsMetric) -> dict[PointsMetric, int]:
        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 75
                            case PointsMetric.SPEED: return 75
                            case PointsMetric.ONBASE: return 200
                            case PointsMetric.AVERAGE: return 40
                            case PointsMetric.SLUGGING: return 165
                            case PointsMetric.HOME_RUNS: return 35
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 105
                            case PointsMetric.ONBASE: return 485
                            case PointsMetric.AVERAGE: return 55
                            case PointsMetric.SLUGGING: return 210
                            case PointsMetric.OUT_DISTRIBUTION: return 30
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 110
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 90
                            case PointsMetric.OUT_DISTRIBUTION: return 20
            case '2001':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 65
                            case PointsMetric.SPEED: return 60
                            case PointsMetric.ONBASE: return 190
                            case PointsMetric.AVERAGE: return 50
                            case PointsMetric.SLUGGING: return 165
                            case PointsMetric.HOME_RUNS: return 45
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 115
                            case PointsMetric.ONBASE: return 470
                            case PointsMetric.AVERAGE: return 35
                            case PointsMetric.SLUGGING: return 255
                            case PointsMetric.OUT_DISTRIBUTION: return 30
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 174
                            case PointsMetric.AVERAGE: return 25
                            case PointsMetric.SLUGGING: return 112
                            case PointsMetric.OUT_DISTRIBUTION: return 20
            case '2002':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 70
                            case PointsMetric.SPEED: return 65
                            case PointsMetric.ONBASE: return 170
                            case PointsMetric.AVERAGE: return 40
                            case PointsMetric.SLUGGING: return 160
                            case PointsMetric.HOME_RUNS: return 40
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 100
                            case PointsMetric.ONBASE: return 330
                            case PointsMetric.AVERAGE: return 45
                            case PointsMetric.SLUGGING: return 280
                            case PointsMetric.OUT_DISTRIBUTION: return 20
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHER
                            case PointsMetric.ONBASE: return 100
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 85
                            case PointsMetric.OUT_DISTRIBUTION: return 10
            case '2003': 
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 60
                            case PointsMetric.SPEED: return 55
                            case PointsMetric.ONBASE: return 160
                            case PointsMetric.AVERAGE: return 50
                            case PointsMetric.SLUGGING: return 160
                            case PointsMetric.HOME_RUNS: return 60
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 70
                            case PointsMetric.ONBASE: return 280
                            case PointsMetric.AVERAGE: return 60
                            case PointsMetric.SLUGGING: return 270
                            case PointsMetric.OUT_DISTRIBUTION: return 20
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 135
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 110
                            case PointsMetric.OUT_DISTRIBUTION: return 10
            case '2004':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 65
                            case PointsMetric.SPEED: return 60
                            case PointsMetric.ONBASE: return 155
                            case PointsMetric.AVERAGE: return 60
                            case PointsMetric.SLUGGING: return 150
                            case PointsMetric.HOME_RUNS: return 45
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 70
                            case PointsMetric.ONBASE: return 295
                            case PointsMetric.AVERAGE: return 50
                            case PointsMetric.SLUGGING: return 150
                            case PointsMetric.OUT_DISTRIBUTION: return 30
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 115
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 105
                            case PointsMetric.OUT_DISTRIBUTION: return 20
            case '2005':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 65
                            case PointsMetric.SPEED: return 60
                            case PointsMetric.ONBASE: return 140
                            case PointsMetric.AVERAGE: return 70
                            case PointsMetric.SLUGGING: return 140
                            case PointsMetric.HOME_RUNS: return 50
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 75
                            case PointsMetric.ONBASE: return 305
                            case PointsMetric.AVERAGE: return 60
                            case PointsMetric.SLUGGING: return 190
                            case PointsMetric.OUT_DISTRIBUTION: return 30
                    case PlayerSubType.RELIEF_PITCHER:
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 115
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 107
                            case PointsMetric.OUT_DISTRIBUTION: return 20
            case 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 65
                            case PointsMetric.SPEED: return 75
                            case PointsMetric.ONBASE: return 220
                            case PointsMetric.AVERAGE: return 70
                            case PointsMetric.SLUGGING: return 180
                            case PointsMetric.HOME_RUNS: return 50
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 110
                            case PointsMetric.ONBASE: return 425
                            case PointsMetric.AVERAGE: return 35
                            case PointsMetric.SLUGGING: return 230
                            case PointsMetric.OUT_DISTRIBUTION: return 30
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 150
                            case PointsMetric.AVERAGE: return 25
                            case PointsMetric.SLUGGING: return 100
                            case PointsMetric.OUT_DISTRIBUTION: return 20
            case 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: 
                        match metric:
                            case PointsMetric.DEFENSE: return 65
                            case PointsMetric.SPEED: return 60
                            case PointsMetric.ONBASE: return 150
                            case PointsMetric.AVERAGE: return 70
                            case PointsMetric.SLUGGING: return 150
                            case PointsMetric.HOME_RUNS: return 50
                    case PlayerSubType.STARTING_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 75
                            case PointsMetric.ONBASE: return 305
                            case PointsMetric.AVERAGE: return 60
                            case PointsMetric.SLUGGING: return 180
                            case PointsMetric.OUT_DISTRIBUTION: return 20
                    case PlayerSubType.RELIEF_PITCHER: 
                        match metric:
                            case PointsMetric.IP: return 0 # IP IS ADJUSTED ELSEWHERE
                            case PointsMetric.ONBASE: return 105
                            case PointsMetric.AVERAGE: return 20
                            case PointsMetric.SLUGGING: return 105
                            case PointsMetric.OUT_DISTRIBUTION: return 10

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
                    case Position.CA: return 1.0
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
                    case Position._2B: return 1.0
                    case Position._3B: return 1.0
                    case Position.SS: return 1.25
                    case Position.CF: return 1.0
                    case Position.OF: return 1.0
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
                    case Position.LFRF: return 1.0
                    case Position.IF: return 1.0
        return 1.0

    def pts_command_out_multiplier(self, command:int, outs:int) -> float:
        command_out_str = f"{command}-{outs}"
        match self.value:
            case '2000':
                match command_out_str:
                    case '10-5': return 1.15
                    case '10-4': return 1.08
                    case '10-2': return 0.95
                    case '9-5': return 1.08
                    case '8-5': return 1.06
                    case '8-3': return 0.90
                    case '7-3': return 0.90

                    case '5-17': return 0.97
                    case '4-14': return  1.1
                    case '4-15': return 1.06
                    case '4-16': return 0.98
                    case '4-17': return 0.925
                    case '3-18': return 0.90
                    case '3-17': return 0.97
                    case '3-16': return 0.97
                    case '3-15': return 1.1
                    case '2-18': return 0.92
            case '2001':
                match command_out_str:
                    case '10-4': return 1.05
                    case '10-2': return 0.96
                    case '9-5': return 1.05
                    case '9-3': return 0.925
                    case '8-4': return 0.925
                    case '8-3': return 0.90
                    case '7-4': return 0.90
                    case '7-3': return 0.90

                    case '1-18': return 0.90
                    case '2-17': return 0.92
                    case '2-18': return 0.92
                    case '3-17': return 0.85
                    case '3-18': return 0.92
                    case '4-14': return 1.15
                    case '4-15': return 1.15
                    case '4-18': return 0.95
                    case '5-14': return 1.25
                    case '6-14': return 1.05
                    case '6-15': return 1.05
                    case '5-17': return 0.99
            case '2002':
                match command_out_str:
                    case '10-7': return 0.85
                    case '3-16': return 1.25
            case '2003':
                match command_out_str:
                    case '10-5': return 1.12
                    case '4-16': return 0.94
                    case '3-15': return 1.3
                    case '2-16': return 1.25
            case '2004':
                match command_out_str:
                    case '9-6': return 0.85
                    case '9-7': return 0.85

                    case '6-16': return 1.15
                    case '3-17': return 0.90
                    case '4-17': return 0.95
                    case '2-18': return 0.80
                    case '3-18': return 0.90
                    case '1-19': return 0.90
                    case '2-19': return 0.90
                    case '3-19': return 0.90
            case '2005':
                match command_out_str:
                    case '9-5': return 1.15
                    case '9-6': return 1.1
                    case '9-7': return 0.95

                    case '2-18': return 0.85
                    case '3-15': return 1.25
                    case '3-16': return 1.05
                    case '3-17': return 0.8
                    case '3-18': return 0.9
                    case '4-17': return 0.8
                    case '5-17': return 0.95
                    case '6-16': return 1.10
                    case '6-17': return 1.03
                    case '1-19': return 0.90
                    case '2-19': return 0.90
                    case '3-19': return 0.90
            case 'CLASSIC':
                match command_out_str:
                    case '10-4': return 1.05
                    case '10-2': return 0.96
                    case '9-5': return 1.05
                    case '9-3': return 0.925
                    case '8-4': return 0.925
                    case '8-3': return 0.90
                    case '7-4': return 0.90
                    case '7-3': return 0.90

                    case '1-18': return 0.90
                    case '2-17': return 0.92
                    case '2-18': return 0.95
                    case '3-17': return 0.85
                    case '3-18': return 0.95
                    case '4-14': return 1.15
                    case '4-15': return 1.15
                    case '5-14': return 1.15
                    case '6-14': return 1.05
                    case '6-15': return 1.05
            case 'EXPANDED':
                match command_out_str:
                    case '9-5': return 1.15
                    case '9-6': return 1.1
                    case '9-7': return 0.95

                    case '1-18': return 0.90
                    case '2-18': return 0.90
                    case '3-17': return 0.90
                    case '3-18': return 0.90
                    case '4-17': return 0.90
                    case '1-19': return 0.90
                    case '2-19': return 0.90
                    case '3-19': return 0.90

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
                    case PlayerSubType.STARTING_PITCHER: return False
                    case PlayerSubType.RELIEF_PITCHER: return False
            case '2002':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return False
                    case PlayerSubType.STARTING_PITCHER: return False
                    case PlayerSubType.RELIEF_PITCHER: return True
            case '2003' | '2004' | '2005' | 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return True
                    case PlayerSubType.STARTING_PITCHER: return True
                    case PlayerSubType.RELIEF_PITCHER: return True
    
    def pts_normalize_towards_median(self, player_sub_type:PlayerSubType) -> bool:
        match self.value:
            case '2002':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return False
                    case PlayerSubType.STARTING_PITCHER: return True
                    case PlayerSubType.RELIEF_PITCHER: return False
            case _:
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return False
                    case PlayerSubType.STARTING_PITCHER: return True
                    case PlayerSubType.RELIEF_PITCHER: return True

    def pts_normalizer_lower_threshold(self, player_sub_type:PlayerSubType) -> float:
        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.70
                    case PlayerSubType.STARTING_PITCHER: return 0.75
                    case PlayerSubType.RELIEF_PITCHER: return 0.55
            case '2001':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.65
                    case PlayerSubType.STARTING_PITCHER: return 0.70
                    case PlayerSubType.RELIEF_PITCHER: return 0.72
            case '2002':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.85
                    case PlayerSubType.STARTING_PITCHER: return 0.85
                    case PlayerSubType.RELIEF_PITCHER: return 0.85
            case '2003':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.85
                    case PlayerSubType.STARTING_PITCHER: return 0.72
                    case PlayerSubType.RELIEF_PITCHER: return 0.70
            case '2004':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.65
                    case PlayerSubType.STARTING_PITCHER: return 0.80
                    case PlayerSubType.RELIEF_PITCHER: return 0.675
            case '2005':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.65
                    case PlayerSubType.STARTING_PITCHER: return 0.78
                    case PlayerSubType.RELIEF_PITCHER: return 0.74
            case 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.65
                    case PlayerSubType.STARTING_PITCHER: return 0.70
                    case PlayerSubType.RELIEF_PITCHER: return 0.72
            case 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.POSITION_PLAYER: return 0.65
                    case PlayerSubType.STARTING_PITCHER: return 0.80
                    case PlayerSubType.RELIEF_PITCHER: return 0.77

    def pts_normalizer_weighting(self, player_sub_type:PlayerSubType) -> float:
        if player_sub_type == PlayerSubType.RELIEF_PITCHER:
            match self.value:
                case '2001' | 'CLASSIC': return 1.5
                case _: return 2.0

        return 1.0

    @property
    def pts_gb_min_max_dict(self) -> ValueRange:
        return ValueRange(min = 0.3, max = 0.5)
    
    def pts_reliever_ip_multiplier(self, ip:int) -> float:
        match self.value:
            case '2000':
                match ip:
                    case 2: return 1.90
                    case 3: return 2.55
            case '2001':
                match ip:
                    case 2: return 1.60
                    case 3: return 2.10
            case '2002':
                match ip:
                    case 2: return 1.20
                    case 3: return 1.80
            case '2003':
                match ip:
                    case 2: return 1.10
                    case 3: return 1.65
            case '2004':
                match ip:
                    case 2: return 1.34
                    case 3: return 2.01
            case '2005':
                match ip:
                    case 2: return 1.34
                    case 3: return 2.01
            case 'CLASSIC': 
                match ip:
                    case 2: return 1.60
                    case 3: return 2.10
            case 'EXPANDED': 
                match ip:
                    case 2: return 1.40
                    case 3: return 2.01
        return 1.0

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

    def pts_obp_percentile_range(self, player_sub_type:PlayerSubType) -> ValueRange:
        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.250, max = 0.390)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.240, max = 0.400)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.270, max = 0.430)
            case '2001':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.240, max = 0.400)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.240, max = 0.360)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.290, max = 0.450)
            case '2002':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.250, max = 0.360)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.250, max = 0.360)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.260, max = 0.450)
            case '2003':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.250, max = 0.390)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.240, max = 0.400)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.270, max = 0.425)
            case '2004':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.250, max = 0.370)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.240, max = 0.400)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.300, max = 0.415)
            case '2005':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.223, max = 0.370)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.240, max = 0.390)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.310, max = 0.410)
            case 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.240, max = 0.400)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.240, max = 0.360)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.290, max = 0.450)
            case 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.223, max = 0.370)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.240, max = 0.390)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.310, max = 0.410)

    def pts_ba_percentile_range(self, player_sub_type:PlayerSubType) -> ValueRange:
        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.225, max = 0.330)
            case '2001':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.225, max = 0.330)
            case '2002':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.290)
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
            case '2005':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.280)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.280)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.245, max = 0.330)
            case 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.300)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.225, max = 0.330)
            case 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.210, max = 0.280)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.210, max = 0.280)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.245, max = 0.330)

    def pts_slg_percentile_range(self, player_sub_type:PlayerSubType) -> ValueRange:
        match self.value:
            case '2000':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.350, max = 0.500)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.330, max = 0.530)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.350, max = 0.550)
            case '2001':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.340, max = 0.500)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.345, max = 0.500)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.350, max = 0.545)
            case '2002':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.340, max = 0.490)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.330, max = 0.445)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.360, max = 0.550)
            case '2003':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.350, max = 0.470)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.330, max = 0.500)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.360, max = 0.550)
            case '2004':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.340, max = 0.470)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.330, max = 0.475)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.380, max = 0.545)
            case '2005':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.335, max = 0.475)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.330, max = 0.480)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.380, max = 0.545)
            case 'CLASSIC':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.340, max = 0.500)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.345, max = 0.500)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.350, max = 0.545)
            case 'EXPANDED':
                match player_sub_type:
                    case PlayerSubType.STARTING_PITCHER: return ValueRange(min = 0.335, max = 0.475)
                    case PlayerSubType.RELIEF_PITCHER: return ValueRange(min = 0.330, max = 0.480)
                    case PlayerSubType.POSITION_PLAYER: return ValueRange(min = 0.375, max = 0.545)

    def pts_speed_or_ip_percentile_range(self, player_sub_type:PlayerSubType) -> ValueRange:
        match player_sub_type:
            case PlayerSubType.POSITION_PLAYER:
                return ValueRange(min = 10, max = 20) # SPEED
            case PlayerSubType.RELIEF_PITCHER:
                return ValueRange(min = 1, max = 2) # IP
            case PlayerSubType.STARTING_PITCHER:
                return ValueRange(min = 5, max = 8) # IP

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

    def super_season_text_length_cutoff(self, index:int) -> int:
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
        return 18 if self.value == '2000' else 19
    
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
    def is_split_image_long(self) -> bool:
        return not self.is_showdown_bot

    # ---------------------------------------
    # PLAYER IMAGE
    # ---------------------------------------

    @property
    def player_image_gdrive_folder_id(self) -> str:
        return '1htwN6r-9QNHJzg6Jq56dGXuJxD2QNaGv' # UNIVERSAL
    
    @property
    def player_image_crop_size(self) -> tuple[int,int]:
        match self.value:
            case '2001': return (1200,1680)
            case '2002' | '2003': return (1305,1827)
            case '2000' | '2004' | '2005': return (1500,2100)
            case 'CLASSIC' | 'EXPANDED': return (1200,1680)

    @property
    def player_image_crop_adjustment(self) -> tuple[int,int]:
        match self.value:
            case '2000': return (-25,-300)
            case '2001': return (-35,-460)
            case '2002': return (75,-250)
            case '2003': return (75,-150)
            case 'CLASSIC' | 'EXPANDED': return (0,int((self.player_image_crop_size[1] - 2100) / 2))
            case _: return (0,0)

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

    def player_image_component_crop_adjustment(self, component: PlayerImageComponent) -> tuple[int,int]:
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
        

    # ---------------------------------------
    # TEMPLATE IMAGE
    # ---------------------------------------

    def template_component_paste_coordinates(self, component:TemplateImageComponent, player_type:PlayerType=None) -> tuple[int,int]:
        match component:
            case TemplateImageComponent.TEAM_LOGO:
                match self.value:
                    case '2000': return (1200,1086)
                    case '2001': return (78,1584)
                    case '2002': return (80,1380)
                    case '2003': return (1179,1074)
                    case '2004' | '2005': return (1161,1425)
                    case 'CLASSIC' | 'EXPANDED': return (1161,1365)
            case TemplateImageComponent.PLAYER_NAME:
                match self.value:
                    case '2000': return (150,-1225)
                    case '2001': return (105,0)
                    case '2002': return (1275,0)
                    case '2003': return (1365,0)
                    case '2004' | '2005': return (276,1605)
                    case 'CLASSIC' | 'EXPANDED': return (325,1575)
            case TemplateImageComponent.PLAYER_NAME_SMALL:
                match self.value:
                    case '2000': return (165,-1225)
                    case '2001': return (105,0)
                    case '2002': return (1285,0)
                    case '2003': return (1375,0)
                    case '2004' | '2005': return (276,1610)
                    case 'CLASSIC' | 'EXPANDED': return (300,1575)
            case TemplateImageComponent.CHART:
                match self.value:
                    case '2000' | '2001': return (981,1335) if player_type.is_pitcher else (981,1317)
                    case '2002': return (948,1593)
                    case '2003': return (981,1518)
                    case '2004' | '2005': return (0,1779)
                    case 'CLASSIC' | 'EXPANDED': return (40,1885)
            case TemplateImageComponent.METADATA:
                match self.value:
                    case '2000' | '2001': return (0,0)
                    case '2002': return (810,1605)
                    case '2003': return (825,1530)
                    case '2004' | '2005': return (282,1710)
                    case 'CLASSIC' | 'EXPANDED': return (330,1670)
            case TemplateImageComponent.SET:
                match self.value:
                    case '2000' | '2001': return (129,2016)
                    case '2002': return (60,1860)
                    case '2003': return (93,1785)
                    case '2004' | '2005': return (1344,1911)
                    case 'CLASSIC' | 'EXPANDED': return (1200,2020)
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
                    case 'CLASSIC' | 'EXPANDED': return (1000,2020)
            case TemplateImageComponent.SUPER_SEASON:
                match self.value:
                    case '2000': return (1200,900)
                    case '2001': return (78,1584)
                    case '2002': return (45,1113)
                    case '2003': return (1041,786)
                    case '2004': return (1071,1164)
                    case '2005': return (1071,1164)
                    case 'CLASSIC' | 'EXPANDED': return (1071,1275)
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
                    case '2002': return (652,1770)
                    case '2003': return (275,1782)
                    case '2004' | '2005': return (1060,1910)
                    case 'CLASSIC' | 'EXPANDED': return (880,2010)
            case TemplateImageComponent.COMMAND:
                match self.value:
                    case 'CLASSIC' | 'EXPANDED': return (80,1540)
                    case _: return (0,0)
            case TemplateImageComponent.STYLE:
                match self.value:
                    case 'CLASSIC' | 'EXPANDED': return (60,1992)
            case TemplateImageComponent.STYLE_LOGO_BG:
                match self.value:
                    case 'CLASSIC' | 'EXPANDED': return (255,5)
            case TemplateImageComponent.STYLE_LOGO:
                match self.value:
                    case 'CLASSIC': return (285,18)
                    case 'EXPANDED': return (295,20)
            case TemplateImageComponent.STYLE_TEXT:
                match self.value:
                    case 'CLASSIC': return (38,27)
                    case 'EXPANDED': return (15,27)
            case TemplateImageComponent.BOT_LOGO:
                match self.value:
                    case '2000' | '2001': return (1250,1945)
                    case '2002': return (62,1900)
                    case '2003': return (655,1705)
                    case '2004' | '2005': return (1268,1965)
                    case 'CLASSIC' | 'EXPANDED': return (1345,2000)
            case TemplateImageComponent.SPLIT:
                match self.value:
                    case '2000': return (330, 1860)
                    case '2001': return (330, 1860)
                    case '2002': return (290, 1850)
                    case '2003': return (380, 1775)
                    case '2004' | '2005': return (80, 1912)
                    case 'CLASSIC' | 'EXPANDED': return (850,2000)

    def template_component_size(self, component:TemplateImageComponent) -> tuple[int,int]:
        match component:
            case TemplateImageComponent.TEAM_LOGO: 
                match self.value:
                    case '2000': return (225,225)
                    case '2001': return (255,255)
                    case '2002': return (450,450)
                    case '2003': return (270,270)
                    case '2004' | '2005': return (255,255)
                    case 'CLASSIC' | 'EXPANDED': return (275,275)
            case TemplateImageComponent.PLAYER_NAME: 
                match self.value:
                    case '2000': return (2100,300)
                    case '2001': return (1545,300)
                    case '2002': return (1395,300)
                    case '2003': return (3300,300)
                    case '2004' | '2005' | 'CLASSIC' | 'EXPANDED': return (900, 300)
            case TemplateImageComponent.SUPER_SEASON: 
                match self.value:
                    case '2000' | '2001': return (312,480)
                    case '2002': return (468,720)
                    case '2003': return (390,600)
                    case '2004' | '2005': return (339,522)
                    case 'CLASSIC' | 'EXPANDED': return (380,380)
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

    def baseline_chart(self, player_type:PlayerType, era:Era) -> Chart:
        match player_type:
            case PlayerType.PITCHER:
                match self.value:
                    case '2000':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.0,
                                    outs=15.85,
                                    values={
                                        'SO': 2.50,
                                        'BB': 1.40,
                                        '1B': 2.15,
                                        '2B': 0.60,
                                        '3B': 0.00,
                                        'HR': 0.00,
                                    }
                                )
                            case Era.LIVE_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.10,
                                    outs=15.75,
                                    values={
                                        'SO': 4.70,
                                        'BB': 1.46,
                                        '1B': 2.07,
                                        '2B': 0.67,
                                        '3B': 0.00,
                                        'HR': 0.05,
                                    }
                                )
                            case Era.INTEGRATION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.00,
                                    outs=15.90,
                                    values={
                                        'SO': 3.80,
                                        'BB': 1.40,
                                        '1B': 2.20,
                                        '2B': 0.45,
                                        '3B': 0.00,
                                        'HR': 0.05,
                                    }
                                )
                            case Era.EXPANSION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.10,
                                    outs=16.00,
                                    values={
                                        'SO': 4.00,
                                        'BB': 1.35,
                                        '1B': 2.15,
                                        '2B': 0.45,
                                        '3B': 0.00,
                                        'HR': 0.05,
                                    }
                                )
                            case Era.FREE_AGENCY:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.00,
                                    outs=16.00,
                                    values={
                                        'SO': 4.75,
                                        'BB': 1.40,
                                        '1B': 1.85,
                                        '2B': 0.67,
                                        '3B': 0.01,
                                        'HR': 0.07,
                                    }
                                )
                            case Era.STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.0,
                                    outs=15.75,
                                    values={
                                        'SO': 4.5,
                                        'BB': 1.35,
                                        '1B': 1.95,
                                        '2B': 0.67,
                                        '3B': 0.00,
                                        'HR': 0.08
                                    }
                                )
                            case Era.POST_STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.00,
                                    outs=16.10,
                                    values={
                                        'SO': 6.00,
                                        'BB': 1.40,
                                        '1B': 1.74,
                                        '2B': 0.65,
                                        '3B': 0.01,
                                        'HR': 0.10,
                                    }
                                )
                            case Era.STATCAST:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.25,
                                    outs=16.00,
                                    values={
                                        'SO': 6.00,
                                        'BB': 1.35,
                                        '1B': 1.92,
                                        '2B': 0.65,
                                        '3B': 0.00,
                                        'HR': 0.08,
                                    }
                                )
                            case Era.PITCH_CLOCK:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.24,
                                    outs=16.00,
                                    values={
                                        'SO': 6.00,
                                        'BB': 1.35,
                                        '1B': 1.92,
                                        '2B': 0.65,
                                        '3B': 0.00,
                                        'HR': 0.08,
                                    }
                                )
                    case '2001':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.0,
                                    outs=15.90,
                                    values={
                                        'SO': 2.50,
                                        'BB': 1.30,
                                        '1B': 2.17,
                                        '2B': 0.60,
                                        '3B': 0.00,
                                        'HR': 0.03,
                                    }
                                )
                            case Era.LIVE_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.05,
                                    outs=15.80,
                                    values={
                                        'SO': 3.55,
                                        'BB': 1.41,
                                        '1B': 2.11,
                                        '2B': 0.62,
                                        '3B': 0.00,
                                        'HR': 0.06,
                                    }
                                )
                            case Era.INTEGRATION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.00,
                                    outs=15.80,
                                    values={
                                        'SO': 3.40,
                                        'BB': 1.45,
                                        '1B': 2.11,
                                        '2B': 0.55,
                                        '3B': 0.01,
                                        'HR': 0.08,
                                    }
                                )
                            case Era.EXPANSION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.1,
                                    outs=16.1,
                                    values={
                                        'SO': 3.90,
                                        'BB': 1.40,
                                        '1B': 1.92,
                                        '2B': 0.50,
                                        '3B': 0.00,
                                        'HR': 0.08,
                                    }
                                )
                            case Era.FREE_AGENCY:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.00,
                                    outs=16.05,
                                    values={
                                        'SO': 4.40,
                                        'BB': 1.33,
                                        '1B': 1.91,
                                        '2B': 0.65,
                                        '3B': 0.00,
                                        'HR': 0.06,
                                    }
                                )
                            case Era.STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.0,
                                    outs=16.0,
                                    values={
                                        'SO': 4.1,
                                        'BB': 1.35,
                                        '1B': 2.0,
                                        '2B': 0.62,
                                        '3B': 0.00,
                                        'HR': 0.11,
                                    }
                                )
                            case Era.POST_STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.00,
                                    outs=16.1,
                                    values={
                                        'SO': 6.00,
                                        'BB': 1.35,
                                        '1B': 1.79,
                                        '2B': 0.65,
                                        '3B': 0.00,
                                        'HR': 0.11,
                                    }
                                )
                            case Era.STATCAST:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.3,
                                    outs=16.1,
                                    values={
                                        'SO': 6.00,
                                        'BB': 1.37,
                                        '1B': 1.83,
                                        '2B': 0.62,
                                        '3B': 0.00,
                                        'HR': 0.08,
                                    }
                                )
                            case Era.PITCH_CLOCK:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.3,
                                    outs=16.0,
                                    values={
                                        'SO': 6.00,
                                        'BB': 1.39,
                                        '1B': 1.89,
                                        '2B': 0.64,
                                        '3B': 0.00,
                                        'HR': 0.08,
                                    }
                                )
                    case '2002':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.5,
                                    outs=16.2,
                                    values={
                                        'SO': 2.00,
                                        'BB': 1.50,
                                        '1B': 1.78,
                                        '2B': 0.50,
                                        '3B': 0.00,
                                        'HR': 0.02,
                                    }
                                )
                            case Era.LIVE_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.00,
                                    outs=16.30,
                                    values={
                                        'SO': 3.70,
                                        'BB': 1.54,
                                        '1B': 1.70,
                                        '2B': 0.40,
                                        '3B': 0.01,
                                        'HR': 0.05,
                                    }
                                )
                            case Era.INTEGRATION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.10,
                                    outs=16.60,
                                    values={
                                        'SO': 3.70,
                                        'BB': 1.41,
                                        '1B': 1.52,
                                        '2B': 0.39,
                                        '3B': 0.00,
                                        'HR': 0.08,
                                    }
                                )
                            case Era.EXPANSION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.20,
                                    outs=16.80,
                                    values={
                                        'SO': 4.00,
                                        'BB': 1.35,
                                        '1B': 1.40,
                                        '2B': 0.35,
                                        '3B': 0.00,
                                        'HR': 0.10,
                                    }
                                )
                            case Era.FREE_AGENCY:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.35,
                                    outs=16.65,
                                    values={
                                        'SO': 3.90,
                                        'BB': 1.15,
                                        '1B': 1.61,
                                        '2B': 0.50,
                                        '3B': 0.00,
                                        'HR': 0.09,
                                    }
                                )
                            case Era.STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.3,
                                    outs=16.7,
                                    values={
                                        'SO': 4.20,
                                        'BB': 1.05,
                                        '1B': 1.40,
                                        '2B': 0.51,
                                        '3B': 0.01,
                                        'HR': 0.13,
                                    }
                                )
                            case Era.POST_STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.3,
                                    outs=16.80,
                                    values={
                                        'SO': 5.75,
                                        'BB': 1.10,
                                        '1B': 1.37,
                                        '2B': 0.60,
                                        '3B': 0.00,
                                        'HR': 0.13,
                                    }
                                )
                            case Era.STATCAST:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.45,
                                    outs=16.90,
                                    values={
                                        'SO': 5.75,
                                        'BB': 1.10,
                                        '1B': 1.35,
                                        '2B': 0.52,
                                        '3B': 0.00,
                                        'HR': 0.13,
                                    }
                                )
                            case Era.PITCH_CLOCK:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.45,
                                    outs=16.80,
                                    values={
                                        'SO': 5.75,
                                        'BB': 1.14,
                                        '1B': 1.40,
                                        '2B': 0.53,
                                        '3B': 0.00,
                                        'HR': 0.13,
                                    }
                                )
                    case '2003':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.7,
                                    outs=16.0,
                                    values={
                                        'SO': 2.00,
                                        'BB': 1.50,
                                        '1B': 1.88,
                                        '2B': 0.60,
                                        '3B': 0.00,
                                        'HR': 0.02,
                                    }
                                )
                            case Era.LIVE_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.70,
                                    outs=15.70,
                                    values={
                                        'SO': 2.70,
                                        'BB': 1.60,
                                        '1B': 2.15,
                                        '2B': 0.50,
                                        '3B': 0.00,
                                        'HR': 0.05,
                                    }
                                )
                            case Era.INTEGRATION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.90,
                                    outs=15.90,
                                    values={
                                        'SO': 3.00,
                                        'BB': 1.50,
                                        '1B': 2.04,
                                        '2B': 0.47,
                                        '3B': 0.01,
                                        'HR': 0.08,
                                    }
                                )
                            case Era.EXPANSION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.00,
                                    outs=16.00,
                                    values={
                                        'SO': 3.00,
                                        'BB': 1.45,
                                        '1B': 2.00,
                                        '2B': 0.45,
                                        '3B': 0.00,
                                        'HR': 0.10,
                                    }
                                )
                            case Era.FREE_AGENCY: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.95,
                                    outs=16.00,
                                    values={
                                        'SO': 3.30,
                                        'BB': 1.32,
                                        '1B': 1.90,
                                        '2B': 0.65,
                                        '3B': 0.00,
                                        'HR': 0.13,
                                    }
                                )
                            case Era.STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.9,
                                    outs=16.3,
                                    values={
                                        'SO': 3.65,
                                        'BB': 1.2,
                                        '1B': 1.93,
                                        '2B': 0.54,
                                        '3B': 0.13,
                                        'HR': 0.28,
                                    }
                                )
                            case Era.POST_STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.15,
                                    outs=15.95,
                                    values={
                                        'SO': 5.00,
                                        'BB': 1.25,
                                        '1B': 1.90,
                                        '2B': 0.70,
                                        '3B': 0.00,
                                        'HR': 0.20,
                                    }
                                )
                            case Era.STATCAST: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.25,
                                    outs=16.00,
                                    values={
                                        'SO': 5.00,
                                        'BB': 1.25,
                                        '1B': 1.90,
                                        '2B': 0.65,
                                        '3B': 0.00,
                                        'HR': 0.20,
                                    }
                                )
                            case Era.PITCH_CLOCK: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.23,
                                    outs=16.00,
                                    values={
                                        'SO': 5.00,
                                        'BB': 1.25,
                                        '1B': 1.90,
                                        '2B': 0.65,
                                        '3B': 0.00,
                                        'HR': 0.20,
                                    }
                                )
                    case '2004':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.60,
                                    outs=16.00,
                                    values={
                                        'SO': 2.10,
                                        'BB': 1.65,
                                        '1B': 1.84,
                                        '2B': 0.48,
                                        '3B': 0.00,
                                        'HR': 0.03,
                                    }
                                )
                            case Era.LIVE_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.50,
                                    outs=15.70,
                                    values={
                                        'SO': 2.40,
                                        'BB': 1.42,
                                        '1B': 2.15,
                                        '2B': 0.67,
                                        '3B': 0.01,
                                        'HR': 0.05,
                                    }
                                )
                            case Era.INTEGRATION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.80,
                                    outs=15.80,
                                    values={
                                        'SO': 2.60,
                                        'BB': 1.35,
                                        '1B': 2.10,
                                        '2B': 0.64,
                                        '3B': 0.01,
                                        'HR': 0.10,
                                    }
                                )
                            case Era.EXPANSION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.00,
                                    outs=15.95,
                                    values={
                                        'SO': 3.00,
                                        'BB': 1.25,
                                        '1B': 2.10,
                                        '2B': 0.60,
                                        '3B': 0.00,
                                        'HR': 0.10,
                                    }
                                )
                            case Era.FREE_AGENCY:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.70,
                                    outs=15.90,
                                    values={
                                        'SO': 3.50,
                                        'BB': 1.25,
                                        '1B': 2.00,
                                        '2B': 0.75,
                                        '3B': 0.00,
                                        'HR': 0.10,
                                    }
                                )
                            case Era.STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.85,
                                    outs=16.35,
                                    values={
                                        'SO': 4.0,
                                        'BB': 1.1,
                                        '1B': 2.1,
                                        '2B': 0.48,
                                        '3B': 0.09,
                                        'HR': 0.3,
                                    }
                                )
                            case Era.POST_STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.90,
                                    outs=16.00,
                                    values={
                                        'SO': 4.90,
                                        'BB': 1.20,
                                        '1B': 1.95,
                                        '2B': 0.70,
                                        '3B': 0.00,
                                        'HR': 0.15,
                                    }
                                )
                            case Era.STATCAST:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.00,
                                    outs=16.00,
                                    values={
                                        'SO': 5.50,
                                        'BB': 1.20,
                                        '1B': 2.00,
                                        '2B': 0.60,
                                        '3B': 0.00,
                                        'HR': 0.20,
                                    }
                                )
                            case Era.PITCH_CLOCK:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.00,
                                    outs=15.95,
                                    values={
                                        'SO': 5.50,
                                        'BB': 1.20,
                                        '1B': 2.03,
                                        '2B': 0.62,
                                        '3B': 0.00,
                                        'HR': 0.20,
                                    }
                                )
                    case '2005':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.60,
                                    outs=16.10,
                                    values={
                                        'SO': 2.10,
                                        'BB': 1.60,
                                        '1B': 1.78,
                                        '2B': 0.50,
                                        '3B': 0.00,
                                        'HR': 0.02,
                                    }
                                )
                            case Era.LIVE_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.50,
                                    outs=15.70,
                                    values={
                                        'SO': 2.40,
                                        'BB': 1.42,
                                        '1B': 2.10,
                                        '2B': 0.72,
                                        '3B': 0.01,
                                        'HR': 0.05,
                                    }
                                )
                            case Era.INTEGRATION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.80,
                                    outs=15.85,
                                    values={
                                        'SO': 4.00,
                                        'BB': 1.50,
                                        '1B': 2.05,
                                        '2B': 0.50,
                                        '3B': 0.00,
                                        'HR': 0.10,
                                    }
                                )
                            case Era.EXPANSION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.00,
                                    outs=15.85,
                                    values={
                                        'SO': 4.00,
                                        'BB': 1.40,
                                        '1B': 2.20,
                                        '2B': 0.45,
                                        '3B': 0.00,
                                        'HR': 0.10,
                                    }
                                )
                            case Era.FREE_AGENCY:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.75,
                                    outs=15.90,
                                    values={
                                        'SO': 3.35,
                                        'BB': 1.20,
                                        '1B': 2.10,
                                        '2B': 0.70,
                                        '3B': 0.00,
                                        'HR': 0.10,
                                    }
                                )
                            case Era.STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.9,
                                    outs=16.2,
                                    values={
                                        'SO': 3.87,
                                        'BB': 1.25,
                                        '1B': 2.05,
                                        '2B': 0.50,
                                        '3B': 0.09,
                                        'HR': 0.33,
                                    }
                                )
                            case Era.POST_STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.00,
                                    outs=15.90,
                                    values={
                                        'SO': 4.80,
                                        'BB': 1.20,
                                        '1B': 2.05,
                                        '2B': 0.70,
                                        '3B': 0.00,
                                        'HR': 0.15,
                                    }
                                )
                            case Era.STATCAST:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.15,
                                    outs=15.90,
                                    values={
                                        'SO': 5.10,
                                        'BB': 1.20,
                                        '1B': 2.05,
                                        '2B': 0.65,
                                        '3B': 0.00,
                                        'HR': 0.20,
                                    }
                                )
                            case Era.PITCH_CLOCK:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.10,
                                    outs=15.90,
                                    values={
                                        'SO': 5.10,
                                        'BB': 1.16,
                                        '1B': 2.06,
                                        '2B': 0.68,
                                        '3B': 0.00,
                                        'HR': 0.20,
                                    }
                                )
                    case 'CLASSIC':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.20,
                                    outs=16.0,
                                    values={
                                        'SO': 3.00,
                                        'BB': 1.35,
                                        '1B': 2.00,
                                        '2B': 0.62,
                                        '3B': 0.00,
                                        'HR': 0.03,
                                    }
                                )
                            case Era.LIVE_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=2.99,
                                    outs=15.70,
                                    values={
                                        'SO': 3.55,
                                        'BB': 1.43,
                                        '1B': 2.20,
                                        '2B': 0.62,
                                        '3B': 0.00,
                                        'HR': 0.05,
                                    }
                                )
                            case Era.INTEGRATION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=2.95,
                                    outs=15.90,
                                    values={
                                        'SO': 3.30,
                                        'BB': 1.43,
                                        '1B': 2.03,
                                        '2B': 0.52,
                                        '3B': 0.02,
                                        'HR': 0.10,
                                    }
                                )
                            case Era.EXPANSION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.05,
                                    outs=16.1,
                                    values={
                                        'SO': 3.80,
                                        'BB': 1.40,
                                        '1B': 1.97,
                                        '2B': 0.42,
                                        '3B': 0.00,
                                        'HR': 0.11,
                                    }
                                )
                            case Era.FREE_AGENCY:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.05,
                                    outs=16.1,
                                    values={
                                        'SO': 3.55,
                                        'BB': 1.24,
                                        '1B': 1.89,
                                        '2B': 0.65,
                                        '3B': 0.00,
                                        'HR': 0.12,
                                    }
                                )
                            case Era.STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.3,
                                    outs=16.0,
                                    values={
                                        'SO': 4.10,
                                        'BB': 1.35,
                                        '1B': 2.0,
                                        '2B': 0.62,
                                        '3B': 0.00,
                                        'HR': 0.11,
                                    }
                                )
                            case Era.POST_STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.00,
                                    outs=16.1,
                                    values={
                                        'SO': 4.95,
                                        'BB': 1.24,
                                        '1B': 1.90,
                                        '2B': 0.65,
                                        '3B': 0.00,
                                        'HR': 0.11,
                                    }
                                )
                            case Era.STATCAST:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.3,
                                    outs=16.1,
                                    values={
                                        'SO': 5.25,
                                        'BB': 1.32,
                                        '1B': 1.85,
                                        '2B': 0.62,
                                        '3B': 0.00,
                                        'HR': 0.11,
                                    }
                                )
                            case Era.PITCH_CLOCK:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.25,
                                    outs=16.1,
                                    values={
                                        'SO': 5.25,
                                        'BB': 1.33,
                                        '1B': 1.84,
                                        '2B': 0.62,
                                        '3B': 0.00,
                                        'HR': 0.11,
                                    }
                                )
                    case 'EXPANDED':
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.0,
                                    outs=15.8,
                                    values={
                                        'SO': 2.30,
                                        'BB': 1.70,
                                        '1B': 1.82,
                                        '2B': 0.60,
                                        '3B': 0.03,
                                        'HR': 0.05,
                                    }
                                )
                            case Era.LIVE_BALL:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.60,
                                    outs=15.65,
                                    values={
                                        'SO': 2.95,
                                        'BB': 1.56,
                                        '1B': 2.12,
                                        '2B': 0.58,
                                        '3B': 0.01,
                                        'HR': 0.08,
                                    }
                                )
                            case Era.INTEGRATION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.90,
                                    outs=15.80,
                                    values={
                                        'SO': 3.95,
                                        'BB': 1.50,
                                        '1B': 2.02,
                                        '2B': 0.49,
                                        '3B': 0.03,
                                        'HR': 0.16,
                                    }
                                )
                            case Era.EXPANSION:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.00,
                                    outs=15.90,
                                    values={
                                        'SO': 3.95,
                                        'BB': 1.42,
                                        '1B': 2.05,
                                        '2B': 0.52,
                                        '3B': 0.00,
                                        'HR': 0.11,
                                    }
                                )
                            case Era.FREE_AGENCY:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=3.80,
                                    outs=16.05,
                                    values={
                                        'SO': 4.00,
                                        'BB': 1.22,
                                        '1B': 1.90,
                                        '2B': 0.68,
                                        '3B': 0.00,
                                        'HR': 0.15,
                                    }
                                )
                            case Era.STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.2,
                                    outs=16.2,
                                    values={
                                        'SO': 4.00,
                                        'BB': 1.25,
                                        '1B': 2.05,
                                        '2B': 0.50,
                                        '3B': 0.09,
                                        'HR': 0.33,
                                    }
                                )
                            case Era.POST_STEROID:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.0,
                                    outs=16.0,
                                    values={
                                        'SO': 5.20,
                                        'BB': 1.20,
                                        '1B': 1.95,
                                        '2B': 0.67,
                                        '3B': 0.01,
                                        'HR': 0.17,
                                    }
                                )
                            case Era.STATCAST:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.2,
                                    outs=16.1,
                                    values={
                                        'SO': 5.5,
                                        'BB': 1.15,
                                        '1B': 1.90,
                                        '2B': 0.64,
                                        '3B': 0.01,
                                        'HR': 0.20,
                                    }
                                )
                            case Era.PITCH_CLOCK:
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=4.15,
                                    outs=16.1,
                                    values={
                                        'SO': 5.5,
                                        'BB': 1.15,
                                        '1B': 1.90,
                                        '2B': 0.64,
                                        '3B': 0.01,
                                        'HR': 0.20,
                                    }
                                )
            case PlayerType.HITTER:
                match self.value:
                    case '2000': 
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.6,
                                    outs=4.0,
                                    values={
                                        'SO': 0.2,
                                        'BB': 3.00,
                                        '1B': 8.50,
                                        '1B+': 1.50,
                                        '2B': 1.50,
                                        '3B': 1.00,
                                        'HR': 0.50,
                                    }
                                )
                            case Era.LIVE_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.77,
                                    outs=4.0,
                                    values={
                                        'SO': 1.0,
                                        'BB': 4.3,
                                        '1B': 6.95,
                                        '1B+': 0.53,
                                        '2B': 1.94,
                                        '3B': 0.30,
                                        'HR': 1.98,
                                    }
                                )
                            case Era.INTEGRATION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.45,
                                    outs=3.60,
                                    values={
                                        'SO': 1.6,
                                        'BB': 4.45,
                                        '1B': 7.10,
                                        '1B+': 0.75,
                                        '2B': 1.90,
                                        '3B': 0.30,
                                        'HR': 1.90,
                                    }
                                )
                            case Era.EXPANSION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.35,
                                    outs=3.85,
                                    values={
                                        'SO': 2.0,
                                        'BB': 4.4,
                                        '1B': 6.95,
                                        '1B+': 0.75,
                                        '2B': 1.85,
                                        '3B': 0.30,
                                        'HR': 1.90,
                                    }
                                )
                            case Era.FREE_AGENCY: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.40,
                                    outs=4.10,
                                    values={
                                        'SO': 1.00,
                                        'BB': 4.20,
                                        '1B': 6.85,
                                        '1B+': 0.70,
                                        '2B': 2.00,
                                        '3B': 0.40,
                                        'HR': 1.75,
                                    }
                                )
                            case Era.STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.7,
                                    outs=3.7,
                                    values={
                                        'SO': 0.2,
                                        'BB': 4.4,
                                        '1B': 6.65,
                                        '1B+': 0.41,
                                        '2B': 1.94,
                                        '3B': 0.30,
                                        'HR': 1.98,
                                    }
                                )
                            case Era.POST_STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.25,
                                    outs=3.90,
                                    values={
                                        'SO': 1.80,
                                        'BB': 4.4,
                                        '1B': 6.80,
                                        '1B+': 0.60,
                                        '2B': 2.00,
                                        '3B': 0.40,
                                        'HR': 1.90,
                                    }
                                )
                            case Era.STATCAST: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.2,
                                    outs=3.90,
                                    values={
                                        'SO': 2.0,
                                        'BB': 4.4,
                                        '1B': 6.80,
                                        '1B+': 0.50,
                                        '2B': 2.00,
                                        '3B': 0.30,
                                        'HR': 2.10,
                                    }
                                )
                            case Era.PITCH_CLOCK: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.35,
                                    outs=3.90,
                                    values={
                                        'SO': 2.0,
                                        'BB': 4.4,
                                        '1B': 6.60,
                                        '1B+': 0.60,
                                        '2B': 2.05,
                                        '3B': 0.30,
                                        'HR': 2.15,
                                    }
                                )
                    case '2001': 
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.6,
                                    outs=4.0,
                                    values={
                                        'SO': 0.50,
                                        'BB': 3.10,
                                        '1B': 8.40,
                                        '1B+': 1.50,
                                        '2B': 1.50,
                                        '3B': 1.00,
                                        'HR': 0.50,
                                    }
                                )
                            case Era.LIVE_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.75,
                                    outs=3.8,
                                    values={
                                        'SO': 1.00,
                                        'BB': 4.55,
                                        '1B': 6.90,
                                        '1B+': 0.70,
                                        '2B': 1.95,
                                        '3B': 0.2,
                                        'HR': 1.9,
                                    }
                                )
                            case Era.INTEGRATION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.45,
                                    outs=3.90,
                                    values={
                                        'SO': 1.90,
                                        'BB': 4.50,
                                        '1B': 7.20,
                                        '1B+': 0.70,
                                        '2B': 1.65,
                                        '3B': 0.2,
                                        'HR': 1.85, 
                                    }  
                                )
                            case Era.EXPANSION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.41,
                                    outs=4.15,
                                    values={
                                        'SO': 2.00,
                                        'BB': 4.45,
                                        '1B': 6.95,
                                        '1B+': 0.70,
                                        '2B': 1.65,
                                        '3B': 0.2,
                                        'HR': 1.9,  
                                    } 
                                )
                            case Era.FREE_AGENCY: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.55,
                                    outs=4.00,
                                    values={
                                        'SO': 0.90,
                                        'BB': 4.35,
                                        '1B': 6.70,
                                        '1B+': 0.85,
                                        '2B': 1.95,
                                        '3B': 0.2,
                                        'HR': 1.95, 
                                    } 
                                )
                            case Era.STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.8,
                                    outs=3.9,
                                    values={
                                        'SO': 1.31,
                                        'BB': 4.45,
                                        '1B': 6.7,
                                        '1B+': 0.63,
                                        '2B': 1.95,
                                        '3B': 0.2,
                                        'HR': 2.0,
                                    }
                                )
                            case Era.POST_STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.4,
                                    outs=4.1,
                                    values={
                                        'SO': 1.90,
                                        'BB': 4.35,
                                        '1B': 6.70,
                                        '1B+': 0.75,
                                        '2B': 1.95,
                                        '3B': 0.2,
                                        'HR': 1.95, 
                                    } 
                                )
                            case Era.STATCAST: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.3,
                                    outs=4.0,
                                    values={
                                        'SO': 2.00,
                                        'BB': 4.45,
                                        '1B': 6.70,
                                        '1B+': 0.70,
                                        '2B': 1.95,
                                        '3B': 0.2,
                                        'HR': 2.0,  
                                    }          
                                )
                            case Era.PITCH_CLOCK: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.4,
                                    outs=4.0,
                                    values={
                                        'SO': 2.00,
                                        'BB': 4.45,
                                        '1B': 6.40,
                                        '1B+': 0.75,
                                        '2B': 2.1,
                                        '3B': 0.2,
                                        'HR': 2.1,  
                                    }          
                                )
                    case '2002': 
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.25,
                                    outs=6.0,
                                    values={
                                        'SO': 0.75,
                                        'BB': 3.25,
                                        '1B': 6.90,
                                        '1B+': 1.00,
                                        '2B': 1.35,
                                        '3B': 0.75,
                                        'HR': 0.75,
                                    }
                                )
                            case Era.LIVE_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.7,
                                    outs=6.0,
                                    values={
                                        'SO': 1.00,
                                        'BB': 3.40,
                                        '1B': 6.20,
                                        '1B+': 0.70,
                                        '2B': 1.94,
                                        '3B': 0.26,
                                        'HR': 1.50,
                                    }
                                )
                            case Era.INTEGRATION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.45,
                                    outs=6.00,
                                    values={
                                        'SO': 1.00,
                                        'BB': 3.45,
                                        '1B': 6.52,
                                        '1B+': 0.65,
                                        '2B': 1.64,
                                        '3B': 0.24,
                                        'HR': 1.50,
                                    }
                                )
                            case Era.EXPANSION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.30,
                                    outs=6.10,
                                    values={
                                        'SO': 1.00,
                                        'BB': 3.40,
                                        '1B': 6.52,
                                        '1B+': 0.60,
                                        '2B': 1.64,
                                        '3B': 0.24,
                                        'HR': 1.50,
                                    }
                                )
                            case Era.FREE_AGENCY: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.4,
                                    outs=6.00,
                                    values={
                                        'SO': 1.00,
                                        'BB': 3.30,
                                        '1B': 6.60,
                                        '1B+': 0.55,
                                        '2B': 2.00,
                                        '3B': 0.20,
                                        'HR': 1.35,
                                    }
                                )
                            case Era.STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.4,
                                    outs=6.0,
                                    values={
                                        'SO': 2.09,
                                        'BB': 3.35,
                                        '1B': 6.0,
                                        '1B+': 0.2,
                                        '2B': 1.94,
                                        '3B': 0.24,
                                        'HR': 1.52,
                                    }
                                )
                            case Era.POST_STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.2,
                                    outs=6.10,
                                    values={
                                        'SO': 2.30,
                                        'BB': 3.35,
                                        '1B': 6.41,
                                        '1B+': 0.40,
                                        '2B': 2.00,
                                        '3B': 0.24,
                                        'HR': 1.50,
                                    }
                                )
                            case Era.STATCAST: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.10,
                                    outs=6.00,
                                    values={
                                        'SO': 2.50,
                                        'BB': 3.40,
                                        '1B': 6.52,
                                        '1B+': 0.30,
                                        '2B': 1.94,
                                        '3B': 0.24,
                                        'HR': 1.60,
                                    }
                                )
                            case Era.PITCH_CLOCK: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.20,
                                    outs=6.00,
                                    values={
                                        'SO': 2.50,
                                        'BB': 3.40,
                                        '1B': 6.36,
                                        '1B+': 0.40,
                                        '2B': 2.00,
                                        '3B': 0.24,
                                        'HR': 1.60,
                                    }
                                )
                    case '2003': 
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.0,
                                    outs=6.0,
                                    values={
                                        'SO': 0.50,
                                        'BB': 3.50,
                                        '1B': 6.60,
                                        '1B+': 1.00,
                                        '2B': 1.35,
                                        '3B': 0.80,
                                        'HR': 0.75,
                                    }
                                )
                            case Era.LIVE_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.65,
                                    outs=6.05,
                                    values={
                                        'SO': 1.10,
                                        'BB': 3.35,
                                        '1B': 6.40,
                                        '1B+': 0.70,
                                        '2B': 1.65,
                                        '3B': 0.35,
                                        'HR': 1.50,
                                    }
                                )
                            case Era.INTEGRATION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.20,
                                    outs=6.00,
                                    values={
                                        'SO': 1.90,
                                        'BB': 3.35,
                                        '1B': 6.40,
                                        '1B+': 0.70,
                                        '2B': 1.65,
                                        '3B': 0.35,
                                        'HR': 1.55,
                                    }
                                )
                            case Era.EXPANSION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=8.95,
                                    outs=6.20,
                                    values={
                                        'SO': 3.10,
                                        'BB': 3.20,
                                        '1B': 6.35,
                                        '1B+': 0.70,
                                        '2B': 1.55,
                                        '3B': 0.35,
                                        'HR': 1.65,
                                    }
                                )
                            case Era.FREE_AGENCY: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.10,
                                    outs=6.15,
                                    values={
                                        'SO': 1.00,
                                        'BB': 2.90,
                                        '1B': 6.60,
                                        '1B+': 0.65,
                                        '2B': 1.60,
                                        '3B': 0.35,
                                        'HR': 1.75,
                                    }
                                )
                            case Era.STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=8.6,
                                    outs=7.2,
                                    values={
                                        'SO': 2.1,
                                        'BB': 3.0,
                                        '1B': 6.57,
                                        '1B+': 0.28,
                                        '2B': 1.55,
                                        '3B': 0.32,
                                        'HR': 1.75,
                                    }
                                )
                            case Era.POST_STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=8.90,
                                    outs=6.40,
                                    values={
                                        'SO': 3.00,
                                        'BB': 3.00,
                                        '1B': 6.20,
                                        '1B+': 0.50,
                                        '2B': 1.60,
                                        '3B': 0.30,
                                        'HR': 2.00,
                                    }
                                )
                            case Era.STATCAST: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=8.75,
                                    outs=6.30,
                                    values={
                                        'SO': 3.30,
                                        'BB': 3.00,
                                        '1B': 6.30,
                                        '1B+': 0.55,
                                        '2B': 1.55,
                                        '3B': 0.30,
                                        'HR': 2.00,
                                    }
                                )
                            case Era.PITCH_CLOCK: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=8.85,
                                    outs=6.30,
                                    values={
                                        'SO': 3.30,
                                        'BB': 3.00,
                                        '1B': 6.20,
                                        '1B+': 0.60,
                                        '2B': 1.60,
                                        '3B': 0.30,
                                        'HR': 2.00,
                                    }
                                )
                    case '2004': 
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.30,
                                    outs=7.00,
                                    values={
                                        'SO': 0.50,
                                        'BB': 3.50,
                                        '1B': 5.70,
                                        '1B+': 0.85,
                                        '2B': 1.60,
                                        '3B': 0.75,
                                        'HR': 0.60,
                                    }
                                )
                            case Era.LIVE_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.70,
                                    outs=6.50,
                                    values={
                                        'SO': 1.70,
                                        'BB': 3.50,
                                        '1B': 6.30,
                                        '1B+': 0.75,
                                        '2B': 1.40,
                                        '3B': 0.15,
                                        'HR': 1.40,
                                    }
                                )
                            case Era.INTEGRATION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.50,
                                    outs=6.80,
                                    values={
                                        'SO': 2.00,
                                        'BB': 3.35,
                                        '1B': 6.20,
                                        '1B+': 0.70,
                                        '2B': 1.35,
                                        '3B': 0.15,
                                        'HR': 1.45,
                                    }
                                )
                            case Era.EXPANSION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.35,
                                    outs=7.0,
                                    values={
                                        'SO': 3.00,
                                        'BB': 3.30,
                                        '1B': 6.15,
                                        '1B+': 0.60,
                                        '2B': 1.30,
                                        '3B': 0.15,
                                        'HR': 1.50,
                                    }
                                )
                            case Era.FREE_AGENCY: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.35,
                                    outs=7.35,
                                    values={
                                        'SO': 1.90,
                                        'BB': 3.25,
                                        '1B': 5.82,
                                        '1B+': 0.50,
                                        '2B': 1.45,
                                        '3B': 0.18,
                                        'HR': 1.45,
                                    }
                                )
                            case Era.STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.05,
                                    outs=7.5,
                                    values={
                                        'SO': 2.3,
                                        'BB': 2.95,
                                        '1B': 6.59,
                                        '1B+': 0.12,
                                        '2B': 1.25,
                                        '3B': 0.17,
                                        'HR': 1.6,
                                    }
                                )
                            case Era.POST_STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.20,
                                    outs=7.2,
                                    values={
                                        'SO': 2.40,
                                        'BB': 3.15,
                                        '1B': 5.90,
                                        '1B+': 0.45,
                                        '2B': 1.55,
                                        '3B': 0.15,
                                        'HR': 1.60,
                                    }
                                )
                            case Era.STATCAST: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.00,
                                    outs=7.2,
                                    values={
                                        'SO': 3.00,
                                        'BB': 3.15,
                                        '1B': 6.00,
                                        '1B+': 0.40,
                                        '2B': 1.30,
                                        '3B': 0.15,
                                        'HR': 1.80,
                                    }
                                )
                            case Era.PITCH_CLOCK: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.15,
                                    outs=7.1,
                                    values={
                                        'SO': 3.00,
                                        'BB': 3.20,
                                        '1B': 5.90,
                                        '1B+': 0.45,
                                        '2B': 1.40,
                                        '3B': 0.15,
                                        'HR': 1.80,
                                    }
                                )
                    case '2005': 
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.35,
                                    outs=7.1,
                                    values={
                                        'SO': 0.50,
                                        'BB': 3.55,
                                        '1B': 5.40,
                                        '1B+': 0.80,
                                        '2B': 1.65,
                                        '3B': 0.80,
                                        'HR': 0.70,
                                    }
                                )
                            case Era.LIVE_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.70,
                                    outs=6.55,
                                    values={
                                        'SO': 1.00,
                                        'BB': 3.50,
                                        '1B': 6.20,
                                        '1B+': 0.75,
                                        '2B': 1.40,
                                        '3B': 0.15,
                                        'HR': 1.45,
                                    }
                                )
                            case Era.INTEGRATION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.45,
                                    outs=6.75,
                                    values={
                                        'SO': 1.00,
                                        'BB': 3.50,
                                        '1B': 6.05,
                                        '1B+': 0.55,
                                        '2B': 1.45,
                                        '3B': 0.15,
                                        'HR': 1.55,
                                    }
                                )
                            case Era.EXPANSION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.35,
                                    outs=7.1,
                                    values={
                                        'SO': 1.10,
                                        'BB': 3.35,
                                        '1B': 6.00,
                                        '1B+': 0.40,
                                        '2B': 1.35,
                                        '3B': 0.15,
                                        'HR': 1.65,
                                    }
                                )
                            case Era.FREE_AGENCY: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.40,
                                    outs=7.15,
                                    values={
                                        'SO': 1.10,
                                        'BB': 3.35,
                                        '1B': 5.90,
                                        '1B+': 0.50,
                                        '2B': 1.45,
                                        '3B': 0.15,
                                        'HR': 1.50,
                                    }
                                )
                            case Era.STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.0,
                                    outs=7.3,
                                    values={
                                        'SO': 2.4,
                                        'BB': 3.3,
                                        '1B': 6.0,
                                        '1B+': 0.12,
                                        '2B': 1.3,
                                        '3B': 0.19,
                                        'HR': 1.4,
                                    }
                                )
                            case Era.POST_STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.25,
                                    outs=7.00,
                                    values={
                                        'SO': 2.50,
                                        'BB': 3.35,
                                        '1B': 5.90,
                                        '1B+': 0.50,
                                        '2B': 1.45,
                                        '3B': 0.15,
                                        'HR': 1.65,
                                    }
                                )
                            case Era.STATCAST: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.0,
                                    outs=7.0,
                                    values={
                                        'SO': 3.05,
                                        'BB': 3.35,
                                        '1B': 6.00,
                                        '1B+': 0.40,
                                        '2B': 1.35,
                                        '3B': 0.15,
                                        'HR': 1.75,
                                    }
                                )
                            case Era.PITCH_CLOCK: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.1,
                                    outs=7.0,
                                    values={
                                        'SO': 3.05,
                                        'BB': 3.35,
                                        '1B': 5.85,
                                        '1B+': 0.45,
                                        '2B': 1.45,
                                        '3B': 0.15,
                                        'HR': 1.75,
                                    }
                                )
                    case 'CLASSIC': 
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.80,
                                    outs=4.05,
                                    values={
                                        'SO': 0.65,
                                        'BB': 3.10,
                                        '1B': 8.55,
                                        '1B+': 1.40,
                                        '2B': 1.50,
                                        '3B': 1.00,
                                        'HR': 0.40,
                                    }
                                )
                            case Era.LIVE_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.75,
                                    outs=3.8,
                                    values={
                                        'SO': 1.00,
                                        'BB': 4.55,
                                        '1B': 6.90,
                                        '1B+': 0.80,
                                        '2B': 1.95,
                                        '3B': 0.2,
                                        'HR': 1.80,
                                    }
                                )
                            case Era.INTEGRATION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.50,
                                    outs=3.95,
                                    values={
                                        'SO': 2.00,
                                        'BB': 4.50,
                                        '1B': 7.10,
                                        '1B+': 0.85,
                                        '2B': 1.65,
                                        '3B': 0.20,
                                        'HR': 1.75,
                                    }
                                )
                            case Era.EXPANSION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.42,
                                    outs=4.10,
                                    values={
                                        'SO': 2.00,
                                        'BB': 4.45,
                                        '1B': 6.85,
                                        '1B+': 0.80,
                                        '2B': 1.75,
                                        '3B': 0.20,
                                        'HR': 1.85,
                                    }
                                )
                            case Era.FREE_AGENCY: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.60,
                                    outs=4.1,
                                    values={
                                        'SO': 0.80,
                                        'BB': 4.45,
                                        '1B': 6.63,
                                        '1B+': 0.82,
                                        '2B': 2.00,
                                        '3B': 0.25,
                                        'HR': 1.75,
                                    }
                                )
                            case Era.STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.5,
                                    outs=4.0,
                                    values={
                                        'SO': 2.0,
                                        'BB': 4.45,
                                        '1B': 6.7,
                                        '1B+': 0.63,
                                        '2B': 1.95,
                                        '3B': 0.2,
                                        'HR': 2.0,
                                    }
                                )
                            case Era.POST_STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.45,
                                    outs=4.1,
                                    values={
                                        'SO': 1.60,
                                        'BB': 4.40,
                                        '1B': 6.60,
                                        '1B+': 0.70,
                                        '2B': 2.00,
                                        '3B': 0.2,
                                        'HR': 2.0,
                                    }
                                )
                            case Era.STATCAST: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.3,
                                    outs=4.0,
                                    values={
                                        'SO': 2.00,
                                        'BB': 4.45,
                                        '1B': 6.70,
                                        '1B+': 0.70,
                                        '2B': 1.95,
                                        '3B': 0.2,
                                        'HR': 2.0,
                                    }
                                )
                            case Era.PITCH_CLOCK: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=7.45,
                                    outs=4.0,
                                    values={
                                        'SO': 2.00,
                                        'BB': 4.45,
                                        '1B': 6.55,
                                        '1B+': 0.75,
                                        '2B': 2.05,
                                        '3B': 0.2,
                                        'HR': 2.0,
                                    }
                                )
                    case 'EXPANDED': 
                        match era:
                            case Era.PRE_1900 | Era.DEAD_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.7,
                                    outs=7.0,
                                    values={
                                        'SO': 0.50,
                                        'BB': 3.50,
                                        '1B': 5.75,
                                        '1B+': 0.80,
                                        '2B': 1.60,
                                        '3B': 0.75,
                                        'HR': 0.60,
                                    }
                                )
                            case Era.LIVE_BALL: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.85,
                                    outs=6.50,
                                    values={
                                        'SO': 1.00,
                                        'BB': 3.50,
                                        '1B': 6.20,
                                        '1B+': 0.75,
                                        '2B': 1.50,
                                        '3B': 0.10,
                                        'HR': 1.45,
                                    }
                                )
                            case Era.INTEGRATION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.5,
                                    outs=6.65,
                                    values={
                                        'SO': 1.00,
                                        'BB': 3.45,
                                        '1B': 6.10,
                                        '1B+': 0.70,
                                        '2B': 1.45,
                                        '3B': 0.10,
                                        'HR': 1.55,
                                    }
                                )
                            case Era.EXPANSION: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.5,
                                    outs=6.9,
                                    values={
                                        'SO': 1.30,
                                        'BB': 3.45,
                                        '1B': 6.05,
                                        '1B+': 0.70,
                                        '2B': 1.30,
                                        '3B': 0.10,
                                        'HR': 1.50,
                                    }
                                )
                            case Era.FREE_AGENCY: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.50,
                                    outs=7.15,
                                    values={
                                        'SO': 2.50,
                                        'BB': 3.30,
                                        '1B': 5.98,
                                        '1B+': 0.50,
                                        '2B': 1.35,
                                        '3B': 0.12,
                                        'HR': 1.60,
                                    }
                                )
                            case Era.STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.5,
                                    outs=7.4,
                                    values={
                                        'SO': 3.0,
                                        'BB': 3.3,
                                        '1B': 6.0,
                                        '1B+': 0.12,
                                        '2B': 1.3,
                                        '3B': 0.19,
                                        'HR': 1.4,
                                    }
                                )
                            case Era.POST_STEROID: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.35,
                                    outs=7.0,
                                    values={
                                        'SO': 2.50,
                                        'BB': 3.35,
                                        '1B': 6.10,
                                        '1B+': 0.40,
                                        '2B': 1.38,
                                        '3B': 0.12,
                                        'HR': 1.65,
                                    }
                                )
                            case Era.STATCAST: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.2,
                                    outs=7.1,
                                    values={
                                        'SO': 3.0,
                                        'BB': 3.35,
                                        '1B': 6.05,
                                        '1B+': 0.40,
                                        '2B': 1.30,
                                        '3B': 0.15,
                                        'HR': 1.65,
                                    }
                            )
                            case Era.PITCH_CLOCK: 
                                return Chart(
                                    is_pitcher=player_type.is_pitcher,
                                    set=self.value,
                                    is_expanded=self.has_expanded_chart,
                                    command=9.35,
                                    outs=7.0,
                                    values={
                                        'SO': 3.0,
                                        'BB': 3.30,
                                        '1B': 6.05,
                                        '1B+': 0.43,
                                        '2B': 1.42,
                                        '3B': 0.15,
                                        'HR': 1.65,
                                    }
                            )
