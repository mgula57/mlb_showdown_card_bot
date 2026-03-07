from enum import Enum

class Hand(str, Enum):

    RIGHT = "R"
    LEFT = "L"
    SWITCH = "S"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
            if value.upper() in ["R", "RIGHT"]:
                return cls.RIGHT
            elif value.upper() in ["L", "LEFT"]:
                return cls.LEFT
            elif value.upper() in ["S", "SWITCH", "B", "BOTH"]:
                return cls.SWITCH
        return cls.RIGHT  # Default to RIGHT if no match found

    def visual(self, is_pitcher:bool) -> str:
        return f'{self.value}HP' if is_pitcher else f'Bats {self.value}'
    
    def silhouette_name(self, is_pitcher:bool) -> str:
        letter = 'L' if self.name == 'SWITCH' else self.value
        suffix = 'P' if is_pitcher else 'H'
        return f'{letter}H{suffix}'