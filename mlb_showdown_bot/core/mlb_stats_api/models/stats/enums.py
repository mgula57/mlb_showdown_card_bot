from enum import Enum

class StatTypeEnum(str, Enum):
    YEAR_BY_YEAR = "yearByYear"
    CAREER = "career"
    SEASON = "season"
    SABERMETRICS = "sabermetrics"

class StatGroupEnum(str, Enum):
    HITTING = "hitting"
    PITCHING = "pitching"
    FIELDING = "fielding"

class GameTypeEnum(str, Enum):
    REGULAR_SEASON = "R"
    PLAYOFFS = "P"
    DIVISION_SERIES = "D"
    LEAGUE_CHAMPIONSHIP_SERIES = "L"
    WORLD_SERIES = "W"
    
