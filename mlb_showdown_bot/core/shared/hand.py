from enum import Enum

class Hand(str, Enum):

    RIGHT = "R"
    LEFT = "L"
    SWITCH = "S"

    def visual(self, is_pitcher:bool) -> str:
        return f'{self.value}HP' if is_pitcher else f'Bats {self.value}'
    
    def silhouette_name(self, is_pitcher:bool) -> str:
        letter = 'L' if self.name == 'SWITCH' else self.value
        suffix = 'P' if is_pitcher else 'H'
        return f'{letter}H{suffix}'