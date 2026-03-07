
from enum import Enum

class GameType(str, Enum):
    """Enumeration for MLB game types."""
    SPRING_TRAINING = "S"
    REGULAR_SEASON = "R"
    WILD_CARD = "F"
    DIVISION_SERIES = "D"
    LEAGUE_CHAMPIONSHIP_SERIES = "L"
    WORLD_SERIES = "W"
    CHAMPIONSHIP = "C"
    NINETEENTH_CENTURY_SERIES = "N"
    PLAYOFFS = "P"
    ALL_STAR_GAME = "A"
    INTRASQUAD = "I"
    EXHIBITION = "E"
