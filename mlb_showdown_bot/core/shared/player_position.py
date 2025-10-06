from enum import Enum

# INTERNAL
from ..card.stats.stat_highlights import StatHighlightsCategory, StatHighlightsType
     
class PlayerSubType(Enum):

    POSITION_PLAYER = 'position_player'
    STARTING_PITCHER = 'starting_pitcher'
    RELIEF_PITCHER = 'relief_pitcher'

    @property
    def parent_type(self) -> 'PlayerType':
        return PlayerType.HITTER if self == self.POSITION_PLAYER else PlayerType.PITCHER

    @property
    def is_pitcher(self) -> bool:
        return self.name in ['STARTING_PITCHER', 'RELIEF_PITCHER']
    
    @property
    def is_hitter(self) -> bool:
        return self.name == 'POSITION_PLAYER'

    @property
    def ip_under_5_negative_multiplier(self) -> float:
        return 1.5 if self.name == 'STARTING_PITCHER' else 1.0
    
    @property
    def nationality_chart_gradient_img_width(self) -> int:
        return 475 if self.value == 'position_player' else 680
        
    # ---------------------------------------
    # STATS
    # ---------------------------------------

    def stat_highlight_categories(self, type: StatHighlightsType) -> list[StatHighlightsCategory]:
        match self:
            case PlayerSubType.STARTING_PITCHER | self.RELIEF_PITCHER:
                categories = [
                    StatHighlightsCategory.G if self == self.RELIEF_PITCHER else StatHighlightsCategory.GS,
                ]
                match type:
                    case StatHighlightsType.CLASSIC: categories += [
                        StatHighlightsCategory.W if self == self.STARTING_PITCHER else StatHighlightsCategory.SV,
                        StatHighlightsCategory.ERA,
                        StatHighlightsCategory.WHIP,
                        StatHighlightsCategory.IP,
                        StatHighlightsCategory._2B,
                    ]
                    case StatHighlightsType.MODERN: categories += [
                        StatHighlightsCategory.ERA,
                        StatHighlightsCategory.FIP,
                        StatHighlightsCategory.bWAR,
                        StatHighlightsCategory.K_9,
                    ]
                    case StatHighlightsType.ALL: categories += [
                        StatHighlightsCategory.ERA,
                        StatHighlightsCategory.WHIP,
                        StatHighlightsCategory.IP,
                        StatHighlightsCategory.SV,
                        StatHighlightsCategory.K_9,
                        StatHighlightsCategory.bWAR,
                        StatHighlightsCategory.W,
                        StatHighlightsCategory.FIP,
                    ]
                return categories
            case self.POSITION_PLAYER:
                match type:
                    case StatHighlightsType.CLASSIC: return [
                        StatHighlightsCategory.G,
                        StatHighlightsCategory.SLASHLINE,
                        StatHighlightsCategory.HR,
                        StatHighlightsCategory.SB,
                        StatHighlightsCategory.RBI,
                        StatHighlightsCategory._2B,
                        StatHighlightsCategory.H,
                        StatHighlightsCategory._3B,
                    ]
                    case StatHighlightsType.MODERN: return [
                        StatHighlightsCategory.G,
                        StatHighlightsCategory.bWAR,
                        StatHighlightsCategory.OPS_PLUS,
                        StatHighlightsCategory.DEFENSE,
                        StatHighlightsCategory.dWAR,
                        StatHighlightsCategory.HR,
                        StatHighlightsCategory.SLASHLINE,
                        StatHighlightsCategory.SB,
                        StatHighlightsCategory._2B,
                        StatHighlightsCategory._3B,
                        StatHighlightsCategory.H,
                    ]
                    case StatHighlightsType.ALL: return [
                        StatHighlightsCategory.G,
                        StatHighlightsCategory.SLASHLINE,
                        StatHighlightsCategory.OPS_PLUS,
                        StatHighlightsCategory.DEFENSE,
                        StatHighlightsCategory.bWAR,
                        StatHighlightsCategory.dWAR,
                        StatHighlightsCategory.HR,
                        StatHighlightsCategory.SB,
                        StatHighlightsCategory.RBI,
                        StatHighlightsCategory._2B,
                        StatHighlightsCategory._3B,
                        StatHighlightsCategory.H,
                    ]
                    case _: return []

    # ---------------------------------------
    # OPPONENT CHART
    # ---------------------------------------

    def opponent_command_boost(self, set: str) -> float:
        match self:
            case self.RELIEF_PITCHER:
                match set:
                    case '2002': return 0.50
                    case _: return 0.0
            case _: return 0.0

class PlayerType(Enum):

    PITCHER = 'Pitcher'
    HITTER = 'Hitter'

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return None

    @property
    def is_pitcher(self) -> bool:
        return self == self.PITCHER
    
    @property
    def is_hitter(self) -> bool:
        return self == self.HITTER
    
    @property
    def opponent_type(self) -> 'PlayerType':
        return self.HITTER if self == self.PITCHER else self.PITCHER
    
    # ---------------------------------------
    # IMAGES
    # ---------------------------------------

    @property
    def template_color_04_05(self) -> str:
        return 'BLUE' if self.is_pitcher else 'GREEN'
    
    @property
    def override_user_input_substrings(self) -> list[str]:
        """List of allowable strings for the user to input to designate a type override."""
        match self.name:
            case "PITCHER": return ['PITCHER', 'PITCHING',]
            case "HITTER": return ['HITTER', 'HITTING',]
    
    @property
    def override_string(self) -> str:
        """Add parenthesis to the type"""
        return f"({self.name})"
    
    @property
    def sub_types(self) -> list[PlayerSubType]:
        return [PlayerSubType.POSITION_PLAYER] if self.is_hitter else [PlayerSubType.STARTING_PITCHER, PlayerSubType.RELIEF_PITCHER]

    # ---------------------------------------
    # BREF
    # ---------------------------------------
    
    @property
    def bref_standard_page_name(self) -> str:
        """Name used in the baseball reference page for standard stats"""
        return "batting" if self.name == "HITTER" else "pitching"


class Position(Enum):

    CA = 'C'
    _1B = '1B'
    _2B = '2B'
    _3B = '3B'
    SS = 'SS'
    CF = 'CF'
    OF = 'OF'
    IF = 'IF'
    LFRF = 'LF/RF'
    DH = "DH"

    SP = "STARTER"
    RP = "RELIEVER"
    CL = "CLOSER"

    LF = "LF"
    RF = "RF"

    @classmethod
    def _missing_(cls, value):
        """Handle alternative values for multi-value enums"""
        
        if value in ['CA', 'C']: # HANDLE CA ALTERNATIVES
            return cls.CA

        if value in ['LF/RF', 'LFRF']: # HANDLE LF/RF ALTERNATIVES
            return cls.LFRF
        
        return None
    
    @property
    def all_values(self) -> list[str]:
        """Return all possible string values for this enum member"""
        match self:
            case Position.CA:
                return ['C', 'CA']
            case Position.LFRF:
                return ['LF/RF', 'LFRF']
            case _:
                return [self.value]

    def value_visual(self, ca_position_name:str) -> str:
        match self.name:
            case 'CA': return ca_position_name
            case _: return self.value

    def extract_games_played_used_for_sort(self, games_played_dict: dict[str: int]) -> int:
        """Use games played dictionary to identify number to use for sorting purposes.
        Bot sorts how positions are shown based on games played.
        
        If positions are combined sort by TOTAL games across positions

        Args:
          - Dictionary mapping position name to number of games played

        Returns:
          Integer with games played value to use during sort
        """
        match self:
            case Position.CA:
                # SAFELY INCLUDE BOTH 'C' AND 'CA' JUST IN CASE THE NAME CHANGES ACROSS SETS
                ca_games = [g for pos, g in games_played_dict.items() if pos in ['C', 'CA',]]
                return sum(ca_games) if len(ca_games) > 0 else 0
            case Position.IF:
                infield_games = [g for pos, g in games_played_dict.items() if pos in ['1B', '2B', '3B', 'SS']]
                return sum(infield_games) if len(infield_games) > 0 else 0
            case Position.LFRF:
                lf_rf_games = sum([g for pos, g in games_played_dict.items() if pos in ['LF', 'RF',]])
                return lf_rf_games
            case _:
                return games_played_dict.get(self.value, 0)

    @property
    def ordering_index(self) -> int:
        match self.name:
            case 'CA': return 11
            case '_1B': return 9
            case '_2B': return 8
            case '_3B': return 7
            case 'SS': return 6
            case 'LFRF': return 5
            case 'CF': return 4
            case 'OF': return 3
            case 'IF': return 2
            case 'DH': return
            case 'SP': return 1
            case 'RP': return 1
            case 'CL': return 1
            case _: return 0

    @property
    def allowed_combinations(self) -> list[str]:
        match self.name:
            case '_2B': return ['SS','3B',]
            case '_3B': return ['SS','2B',]
            case 'SS': return ['2B','3B',]
            case _: return []

    @property
    def is_infield(self) -> bool:
        return self in [Position._1B, Position._2B, Position._3B, Position.SS, Position.IF]

    @property
    def is_middle_infield(self) -> bool:
        return self in [Position.IF, Position._2B, Position.SS]
    
    @property
    def is_outfield(self) -> bool:
        return self in [Position.LF, Position.CF, Position.RF, Position.OF, Position.LFRF,]
    
    @property
    def is_pitcher(self) -> bool:
        return self.name in ['SP','RP','CL']
    
    @property
    def is_hitter(self) -> bool:
        return not self.is_pitcher
    
    @property
    def is_valid_in_game(self) -> bool:
        return self.name not in ['LF', 'RF']
    
    def __repr__(self):
        return self.value
    
    # ---------------------------------------
    # SIMULATION
    # ---------------------------------------

    @property
    def rest_multiplier(self) -> float:
        match self:
            case Position.CA: return 0.5
            case _: return 1.0


class PositionSlotParent(Enum):
    
    CATCHER_AND_DH = "CATCHER AND DH"
    INFIELD = "INFIELD"
    OUTFIELD = "OUTFIELD"
    ROTATION = "ROTATION"
    BULLPEN = "BULLPEN"
    BENCH = "BENCH"
    NONE = "NONE"


class PositionSlot(Enum):
    CA = "CA"
    _1B = "1B"
    _2B = "2B"
    _3B = "3B"
    SS = "SS"
    LF = "LF"
    CF = "CF"
    RF = "RF"
    DH = "DH"
    SP = "SP"
    BP = "RP"
    BE = "BE"

    NONE = "NA"

    @property
    def valid_positions(self) -> list[Position]:
        all_position_player_positions = [Position.CA, Position._1B, Position._2B, Position._3B, Position.SS, Position.LFRF, Position.CF, Position.OF, Position.IF, Position.DH]
        match self:
            case PositionSlot._1B | PositionSlot._2B | PositionSlot._3B | PositionSlot.SS: return [Position(self.value), Position.IF]
            case PositionSlot.LF | PositionSlot.RF: return [Position.LFRF, Position.OF]
            case PositionSlot.CF: return [Position.CF, Position.OF]
            case PositionSlot.DH | PositionSlot.BE: return all_position_player_positions
            case PositionSlot.SP: return [Position.SP]
            case PositionSlot.BP: return [Position.RP, Position.CL]
            case PositionSlot.NONE: return []
            case _: return [Position(self.value)]

    @property
    def is_position_player(self) -> bool:
        return self not in [PositionSlot.SP, PositionSlot.BP, PositionSlot.NONE]

    @property
    def is_pitcher(self) -> bool:
        return self in [PositionSlot.SP,PositionSlot.BP]
    
    @property
    def parent(self) -> PositionSlotParent:
        match self:
            case PositionSlot.CA | PositionSlot.DH: return PositionSlotParent.CATCHER_AND_DH
            case PositionSlot._1B | PositionSlot._2B | PositionSlot._3B | PositionSlot.SS: return PositionSlotParent.INFIELD
            case PositionSlot.LF | PositionSlot.CF | PositionSlot.RF: return PositionSlotParent.OUTFIELD
            case PositionSlot.SP: return PositionSlotParent.ROTATION
            case PositionSlot.BP: return PositionSlotParent.BULLPEN
            case PositionSlot.BE: return PositionSlotParent.BENCH
            case _: return PositionSlotParent.NONE

    @property
    def has_defense(self) -> bool:
        return self not in [PositionSlot.DH, PositionSlot.BE, PositionSlot.SP, PositionSlot.BP, PositionSlot.NONE]
    
    @property
    def is_outfield(self) -> bool:
        return self in [PositionSlot.LF, PositionSlot.CF, PositionSlot.RF]