from enum import Enum

class Edition(Enum):
    NONE = "NONE"
    COOPERSTOWN_COLLECTION = "CC"
    ALL_STAR_GAME = "ASG"
    SUPER_SEASON = "SS"
    ROOKIE_SEASON = "RS"
    HOLIDAY = "HOL"
    NATIONALITY = "NAT"

    @property
    def ignore_historical_team_logo(self) -> bool:
        return self in [Edition.ALL_STAR_GAME, Edition.COOPERSTOWN_COLLECTION]
    
    @property
    def template_color_0405(self) -> str:
        if self == Edition.COOPERSTOWN_COLLECTION:
            return "BROWN"
        elif self == Edition.SUPER_SEASON:
            return "RED"
        else:
            return None
    
    @property
    def use_edition_logo_as_team_logo(self) -> bool:
        return self in [Edition.COOPERSTOWN_COLLECTION]
    
    @property
    def template_extension(self) -> str:
        return f'-{self.value}' if self in [Edition.ALL_STAR_GAME, Edition.COOPERSTOWN_COLLECTION] else ''
    
    @property
    def is_not_empty(self) -> bool:
        return self != Edition.NONE

    @property
    def rotate_team_logo_2002(self) -> bool:
        return self not in [Edition.COOPERSTOWN_COLLECTION, Edition.NATIONALITY]
    
    @property
    def ignore_showdown_library(self) -> bool:
        return self in [Edition.NATIONALITY] # TODO: NATIONALITY DATA CURRENTLY NOT IN SL, REMOVE AFTER ADDING

    @property
    def has_additional_logo_00_01(self) -> bool:
        return self.name in ['COOPERSTOWN_COLLECTION', 'ALL_STAR_GAME', 'SUPER_SEASON', 'ROOKIE_SEASON']
