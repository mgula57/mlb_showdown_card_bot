from pydantic import BaseModel

from ...shared.player_position import PlayerType

class Position(BaseModel):
    """Model representing a player's position in MLB Stats API"""

    code: str
    name: str
    type: str
    abbreviation: str

    @property
    def player_type(self) -> PlayerType:
        """Determine if the position is a 'Pitcher' or 'Hitter'"""
        if self.code == '1':
            return PlayerType.PITCHER
        return PlayerType.HITTER