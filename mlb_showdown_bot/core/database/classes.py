from pydantic import BaseModel
from typing import Optional

from unidecode import unidecode

from ..card.sets import Set
from ..card.showdown_player_card import ShowdownPlayerCard, PlayerType, WBCTeam
from ..fangraphs.models import LeaderboardStats

class WbcShowdownCardRecord(BaseModel):
    """Data model representing a WBC roster entry along with its corresponding Showdown card data (if available)"""
    
    # From WBC roster data
    wbc_season: int
    wbc_team: WBCTeam
    wbc_team_id: Optional[int] = None
    position: str # This is the position the player played in the WBC, which may differ from their MLB position
    name: str
    mlb_id: int

    # From MLB <> Bref Map
    bref_id: Optional[str] = None

    # Showdown Card Data
    showdown_set: Set
    card_id: Optional[str] = None
    card_data: Optional[ShowdownPlayerCard] = None  # This will hold the Showdown card data if a match is found

    # Additional Context
    stat_source: Optional[str] = None  # E.g. "MLB", "Minor League", "KBO", "NGB"

    @property
    def name_safe_for_matching(self) -> str:
        """Return a version of the player's name that is normalized for matching purposes (e.g. removing accents, converting to lowercase)"""
        return unidecode(self.name).lower()
    
    @property
    def player_type_for_matching(self) -> PlayerType:
        """Return the player type for matching purposes based on the position played in the WBC roster, which may differ from their MLB position. This is important because some players may have different positions listed in different data sources, and we want to try to match them as accurately as possible."""
        return PlayerType.PITCHER if self.position in ["P", "SP", "RP"] else PlayerType.HITTER

# -------------------------------
# FANGRAPHS DATA MODELS
# -------------------------------

class FangraphsLeaderboardRecord(BaseModel):
    """Data model representing a single record from a Fangraphs leaderboard query"""
    
    id: str
    fangraphs_minor_id: Optional[str] = None
    player_name: str
    team: Optional[str] = None
    team_id: Optional[int] = None
    position: Optional[str] = None
    season: Optional[int] = None

    stats: Optional[LeaderboardStats] = None

    stat_type: str
    league: str

    @property
    def is_pitcher_stat_type(self) -> bool:
        """Determine if the stat type is a pitching stat type based on the stat_type field, which can help inform how we use this data for matching and filling in card stats"""
        pitching_stat_types = ["pit"]
        return self.stat_type.lower() in pitching_stat_types

    @property
    def name_safe_for_matching(self) -> str:
        """Return a version of the player's name that is normalized for matching purposes (e.g. removing accents, converting to lowercase)"""
        return unidecode(self.player_name).lower()
    
    @property
    def player_type_for_matching(self) -> PlayerType:
        """Return the player type for matching purposes based on the position listed in the Fangraphs data, which may differ from their MLB position. This is important because some players may have different positions listed in different data sources, and we want to try to match them as accurately as possible."""
        return PlayerType.PITCHER if self.position and self.position in ["P", "SP", "RP"] else PlayerType.HITTER