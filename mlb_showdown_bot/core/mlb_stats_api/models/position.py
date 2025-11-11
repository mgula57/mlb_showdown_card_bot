from pydantic import BaseModel

class PrimaryPosition(BaseModel):
    """Model representing a player's primary position in MLB Stats API"""
    
    code: str
    name: str
    type: str
    abbreviation: str