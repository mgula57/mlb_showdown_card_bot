from pydantic import BaseModel, Field
from typing import Optional

from ..teams.team import Team

class Award(BaseModel):

    id: str
    name: str
    season: Optional[str] = None
    team: Optional[Team] = None

    @staticmethod
    def leagues_included() -> list[str]:
        return ["MLB", "AL", "NL"]

    @property
    def is_included_in_accolades(self) -> bool:
        """Determine if this award should be included in accolades"""
        included_award_suffixes = [
            'AS',    # ALL STAR
            'SS',    # SILVER SLUGGER
            'GG',    # GOLD GLOVE
            'MVP',   # MOST VALUABLE PLAYER
            'CY',    # CY YOUNG
            'ROY',  # ROOKIE OF THE YEAR
            'AFIRST' # FIRST TEAM MLB
        ]
        return self.short_name in included_award_suffixes

    @property
    def short_name(self) -> str:
        """Get a short name for the award based on its ID"""
        updated_str = self.id
        for removal_str in Award.leagues_included():
            updated_str = updated_str.replace(removal_str, "")
        return updated_str
    
    @property
    def long_name(self) -> str:
        """Get a long name for the award based on its full name"""
        mapping = {
            'AS': 'All Star',
            'SS': 'Silver Slugger',
            'GG': 'Gold Glove',
            'MVP': 'MVP',
            'CY': 'Cy Young',
            'ROY': 'Rookie of the Year',
            'AFIRST': 'MLB First Team'
        }
        return mapping.get(self.short_name, self.short_name)
    
    @property
    def normalized_accolade_list_key(self) -> str:
        """
        Get a normalized key for the accolade based on the award short name.
        Purpose is to match original bref accolade keys.
        """
        mapping = {
            'AS': 'allstar',
            'SS': 'silver_sluggers',
            'GG': 'gold_gloves',
            'MVP': 'mvp',
            'CY': 'cyyoung',
        }
        return mapping.get(self.short_name, None)
    
    @property
    def is_in_normalized_award_list(self) -> bool:
        """In bref accolades there was a specific list of general awards. 
        This is used for career long cards to see MVP/ROY/CY across years."""
        included_short_names = [
            'MVP',
            'CY',
            'ROY',
        ]
        return self.short_name in included_short_names
    
    @property
    def league(self) -> Optional[str]:
        """Extract league from award ID if applicable"""
        for league in Award.leagues_included():
            if self.id.startswith(league):
                return league
        return None

    @property
    def award_summary_abbr(self) -> Optional[str]:
        """Generate a summary abbreviation for the award"""
        included_short_names_and_abbr = {
            'MVP': 'MVP-1',
            'CY': 'CYA-1',
            'ROY': 'ROY-1',
            'SS': 'SS',
            'GG': 'GG',
            'AS': 'AS',
        }
        return included_short_names_and_abbr.get(self.short_name, None)