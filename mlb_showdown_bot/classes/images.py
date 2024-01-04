from enum import Enum
from pydantic import BaseModel, validator
from typing import Optional

# ---------------------------------------
# EDITION
# ---------------------------------------

class Edition(str, Enum):
    NONE = "NONE"
    COOPERSTOWN_COLLECTION = "CC"
    ALL_STAR_GAME = "ASG"
    SUPER_SEASON = "SS"
    ROOKIE_SEASON = "RS"
    HOLIDAY = "HOL"
    NATIONALITY = "NAT"
    POSTSEASON = "POST"

    @classmethod
    def _missing_(cls, _):
        return cls.NONE

    @property
    def ignore_historical_team_logo(self) -> bool:
        return self in [Edition.ALL_STAR_GAME, Edition.COOPERSTOWN_COLLECTION]
    
    @property
    def template_color_0405(self) -> str:
        match self:
            case Edition.COOPERSTOWN_COLLECTION:
                return "BROWN"
            case Edition.SUPER_SEASON:
                return "RED"
            case Edition.POSTSEASON:
                return "DARK_BLUE"
            case _: return None
    
    @property
    def use_edition_logo_as_team_logo(self) -> bool:
        return self in [Edition.COOPERSTOWN_COLLECTION, Edition.ALL_STAR_GAME]
    
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
        return self in [Edition.COOPERSTOWN_COLLECTION, Edition.ALL_STAR_GAME, Edition.SUPER_SEASON, Edition.ROOKIE_SEASON, Edition.POSTSEASON]

# ---------------------------------------
# EXPANSION
# ---------------------------------------

class Expansion(str, Enum):

    BS = 'BS'
    TD = 'TD'
    PR = 'PR'
    PM = 'PM'
    ASG = "ASG"

    def __repr__(self) -> str:
        return self.value
    
    @property
    def has_image(self) -> bool:
        return self.value not in ['BS', 'PM']

# ---------------------------------------
# PLAYER IMAGE COMPONENT
# ---------------------------------------

class PlayerImageComponent(str, Enum):

    BACKGROUND = "BG"
    CUSTOM_BACKGROUND = "CUSTOM BG"
    CUSTOM_FOREGROUND = "CUSTOM FG"
    SHADOW = "SHADOW"
    GLOW = "GLOW"
    CUT = "CUT"
    GRADIENT = "GRADIENT"
    DARKENER = "DARKENER"
    COOPERSTOWN = "COOPERSTOWN"
    POSTSEASON = "POSTSEASON"
    ELLIPSE_LARGE = "ELLIPSE-LARGE"
    ELLIPSE_MEDIUM = "ELLIPSE-MEDIUM"
    ELLIPSE_SMALL = "ELLIPSE-SMALL"
    SUPER_SEASON = "SUPER SEASON"
    RAINBOW_FOIL = "RAINBOW FOIL"
    SILHOUETTE = "SILHOUETTE"
    SAPPHIRE = "SAPPHIRE"
    RADIAL = "RADIAL"
    COMIC_BOOK_LINES = "COMIC-BOOK-HERO"
    GOLD_RUSH = "GOLD-BEAMS"
    GOLD = "GOLD"
    GOLD_FRAME = "GOLD_FRAME"
    MOONLIGHT = "MOONLIGHT"
    WHITE_SMOKE = "WHITE_SMOKE"
    FLAMES = "FLAMES"
    WHITE_CIRCLE = "WHITE_CIRCLE"
    BLACK_CIRCLE = "BLACK_CIRCLE"
    TEAM_COLOR = "TEAM_COLOR"
    TEAM_LOGO = "TEAM_LOGO"
    NAME_CONTAINER_2000 = "NAME_CONTAINER_2000"

    @property
    def load_source(self) -> str:
        match self.name:
            case "BACKGROUND" | "SHADOW" | "GLOW" | "CUT": return "DOWNLOAD"
            case "TEAM_COLOR": return "COLOR"
            case "TEAM_LOGO": return "TEAM_LOGOS"
            case "NAME_CONTAINER_2000": return "NAME_CONTAINER"
            case "SILHOUETTE": return "SILHOUETTE"
            case _: return "CARD_ART"

    @property
    def is_loaded_via_download(self) -> bool:
        return self.load_source == "DOWNLOAD"
    
    @property
    def adjust_paste_coordinates_for_bordered(self) -> bool:
        return self.name in ["NAME_CONTAINER_2000", "SILHOUETTE"]
    
    @property
    def ignores_custom_crop(self) -> bool:
        return self.name in [
            "SUPER_SEASON",
            "CUSTOM_BACKGROUND",
            "CUSTOM_FOREGROUND",
            "GRADIENT",
            "RAINBOW_FOIL",
            "SAPPHIRE",
            "RADIAL",
            "COOPERSTOWN",
            "COMIC_BOOK_LINES",
            "GOLD_RUSH",
            "GOLD",
            "WHITE_SMOKE",
            "FLAMES",
            "WHITE_CIRCLE",
            "BLACK_CIRCLE",
            "TEAM_COLOR",
            "TEAM_LOGO",
            "SILHOUETTE",
            "NAME_CONTAINER_2000",
            "DARKENER",
            "GOLD_FRAME",
        ]
    
    @property
    def crop_adjustment_02_03(self) -> tuple[int, int]:
        match self.name:
            case "WHITE_CIRCLE" | "BLACK_CIRCLE" | "TEAM_COLOR" | "TEAM_LOGO": return (75,0)
            case _: return None

    @property
    def opacity(self) -> float:
        match self.name:
            case "RAINBOW_FOIL" | "SAPPHIRE": return 0.65
            case "TEAM_COLOR": return 0.75
            case _: return 1.0

    @property
    def is_ellipse(self) -> bool:
        return self.name in ['ELLIPSE_LARGE','ELLIPSE_MEDIUM','ELLIPSE_SMALL',]
    
    @property
    def layering_index(self) -> int:
        ordered_list = [
            'BACKGROUND',
            'CUSTOM_BACKGROUND',
            'COOPERSTOWN',
            'SUPER_SEASON',
            "POSTSEASON",
            'DARKENER',
            'GRADIENT',
            'RAINBOW_FOIL',
            'SAPPHIRE',
            'RADIAL',
            'COMIC_BOOK_LINES',
            'GOLD_RUSH',
            'GOLD',
            'GOLD_FRAME',
            'WHITE_SMOKE',
            'MOONLIGHT',
            'FLAMES',
            'TEAM_LOGO',
            'TEAM_COLOR',
            'WHITE_CIRCLE',
            'BLACK_CIRCLE',
            'NAME_CONTAINER_2000',
            'SHADOW',
            'GLOW',
            'CUT',
            'CUSTOM_FOREGROUND',
            'SILHOUETTE',
        ]
        return ordered_list.index(self.name) if self.name in ordered_list else None

# ---------------------------------------
# SPECIAL EDITION
# ---------------------------------------

class SpecialEdition(str, Enum):
    
    ASG_2023 = "ASG 2023"
    COOPERSTOWN_COLLECTION = "CC"
    SUPER_SEASON = "SS"
    TEAM_COLOR_BLAST_DARK = "TCBD"
    NATIONALITY = "NATIONALITY"
    POSTSEASON = "POSTSEASON"
    NONE = "NONE"

    def color(self, league:str=None) -> tuple[int,int,int,int]:
        match self.name:
            case "ASG_2023": 
                if league is None:
                    return None
                colors_dict = {
                    'NL': (12, 44, 85, 255), # BLUE
                    'AL': (2, 112, 113, 255), # GREEN
                }
                return colors_dict.get(league, None)
            
    @property
    def image_component_saturation_adjustments_dict(self) -> dict[PlayerImageComponent, float]:
        match self:
            case SpecialEdition.COOPERSTOWN_COLLECTION | SpecialEdition.POSTSEASON: return {
                PlayerImageComponent.BACKGROUND: 0.33,
            }
            case SpecialEdition.SUPER_SEASON: return {
                PlayerImageComponent.BACKGROUND: 0.75,
            }
        return {}

# ---------------------------------------
# IMAGE PARALLELS
# ---------------------------------------


class ImageParallel(str, Enum):
    
    RAINBOW_FOIL = "RF"
    SAPPHIRE = "SPH"
    BLACK_AND_WHITE = "B&W"
    RADIAL = "RAD"
    COMIC_BOOK_HERO = "CB"
    GOLD_RUSH = "GOLDRUSH"
    GOLD = "GOLD"
    GOLD_FRAME = "GF"
    WHITE_SMOKE = "WS"
    FLAMES = "FLAMES"
    TEAM_COLOR_BLAST = "TCB"
    MYSTERY = "MYSTERY"
    MOONLIGHT = "MOONLIGHT"
    NONE = "NONE"

    @classmethod
    def _missing_(cls, value):
        return cls.NONE

    @property
    def has_special_components(self) -> bool:
        return self.name not in ['NONE', 'BLACK_AND_WHITE']

    def special_component_additions(self, set: str) -> dict[str,str]:
        match self.name:
            case "RAINBOW_FOIL": return { PlayerImageComponent.RAINBOW_FOIL: "RAINBOW-FOIL" }
            case "SAPPHIRE": return { PlayerImageComponent.SAPPHIRE: "SAPPHIRE" }
            case "RADIAL": return { PlayerImageComponent.RADIAL: "RADIAL" }
            case "COMIC_BOOK_HERO": return { PlayerImageComponent.COMIC_BOOK_LINES: PlayerImageComponent.COMIC_BOOK_LINES.name }
            case "GOLD_RUSH": return { PlayerImageComponent.GOLD_RUSH: PlayerImageComponent.GOLD_RUSH.name }
            case "GOLD": return { PlayerImageComponent.GOLD: PlayerImageComponent.GOLD.name }
            case "GOLD_FRAME": return { PlayerImageComponent.GOLD_FRAME: PlayerImageComponent.GOLD_FRAME.name, PlayerImageComponent.BACKGROUND: None }
            case "WHITE_SMOKE": return { PlayerImageComponent.WHITE_SMOKE: PlayerImageComponent.WHITE_SMOKE.name, PlayerImageComponent.BACKGROUND: None }
            case "FLAMES": return { PlayerImageComponent.FLAMES: PlayerImageComponent.FLAMES.name }
            case "TEAM_COLOR_BLAST": return { PlayerImageComponent.WHITE_CIRCLE: PlayerImageComponent.WHITE_CIRCLE.name, PlayerImageComponent.TEAM_LOGO: None, PlayerImageComponent.TEAM_COLOR: None, PlayerImageComponent.BACKGROUND: None }
            case "MOONLIGHT":
                comps_dict = { PlayerImageComponent.MOONLIGHT: PlayerImageComponent.MOONLIGHT.name, PlayerImageComponent.BACKGROUND: None }
                if set == '2001':
                    comps_dict[PlayerImageComponent.TEAM_LOGO] = None
                return comps_dict
            case _: return {}

    @property
    def special_components_replacements(self) -> dict[str,str]:
        match self.name:
            case "SAPPHIRE" | "WHITE_SMOKE" | "FLAMES" | "TEAM_COLOR_BLAST" | "GOLD_RUSH" | "GOLD" | "GOLD_FRAME" | "MOONLIGHT": return { PlayerImageComponent.GLOW: PlayerImageComponent.SHADOW }
            case _: return {}
    
    @property
    def image_type_saturations_dict(self) -> dict[str,float]:
        match self.name:
            case "COMIC_BOOK_HERO" | "WHITE_SMOKE": return { PlayerImageComponent.BACKGROUND: 0.05 }
            case "GOLD_RUSH" | "GOLD" | "GOLD_FRAME": return { PlayerImageComponent.BACKGROUND: 0.40 }
            case "MOONLIGHT": return { PlayerImageComponent.BACKGROUND: 0.60 }
            case "TEAM_COLOR_BLAST": return { PlayerImageComponent.TEAM_LOGO: 0.10 }
            case _: return {}

    @property
    def is_team_background_black_and_white(self) -> bool:
        return self.name in ['COMIC_BOOK_HERO', 'GOLD_RUSH', 'GOLD', 'WHITE_SMOKE']
    
    @property
    def color_override_04_05_chart(self) -> str:
        match self.name:
            case 'GOLD' | 'GOLD_RUSH' | 'GOLD_FRAME': return 'GOLD'
            case 'FLAMES': return 'RED'
            case _: return None
    
    @property
    def name_container_suffix_2000(self) -> str:
        match self.name:
            case 'GOLD' | 'GOLD_RUSH' | 'GOLD_FRAME': return '-GOLD'
            case _: return ''

    @property
    def template_color_04_05(self) -> str:
        match self:
            case ImageParallel.MOONLIGHT: return "BLACK"
            case _: return None


# ---------------------------------------
# TEMPLATE IMAGE COMPONENT
# ---------------------------------------

class TemplateImageComponent(Enum):

    TEAM_LOGO = "team_logo"
    PLAYER_NAME = "player_name"
    PLAYER_NAME_SMALL = "player_name_small"
    CHART = "chart"
    METADATA = "metadata"
    SET = "set"
    YEAR_CONTAINER = "year_container"
    NUMBER = "number"
    SUPER_SEASON = "super_season"
    ROOKIE_SEASON = "rookie_season"
    ROOKIE_SEASON_YEAR_TEXT = "rookie_season_year_text"
    POSTSEASON = "postseason"
    POSTSEASON_YEAR_TEXT = "postseason_year_text"
    POSTSEASON_YEAR_TEXT_BOX = "postseason_year_text_box"
    EXPANSION = "expansion"
    COMMAND = "command"
    STYLE = "style"
    STYLE_LOGO = "style_logo"
    STYLE_LOGO_BG = "style_logo_bg"
    STYLE_TEXT = "style_text"
    BOT_LOGO = "bot_logo"
    SPLIT = "split"

# ---------------------------------------
# IMAGE SOURCE
# ---------------------------------------

class ImageSourceType(str, Enum):
    UPLOAD = "Upload"
    LINK = 'Link'
    LOCAL_CACHE = 'Local Cache'
    GOOGLE_DRIVE = 'Google Drive'
    EMPTY = 'EMPTY'

    def __repr__(self) -> str:
        return self.value

    @property
    def is_user_generated(self) -> bool:
        return self.name in ['UPLOAD', 'LINK']
    
    @property
    def is_automated(self) -> bool:
        return self.name in ['LOCAL_CACHE', 'GOOGLE_DRIVE']
    
    @property
    def is_empty(self) -> bool:
        return self.name == 'EMPTY'


class ImageSource(BaseModel):

    type: ImageSourceType = ImageSourceType.EMPTY
    url: Optional[str] = None
    path: Optional[str] = None

    def __init__(self, **data) -> None:
        super().__init__(**data)
        if self.type == ImageSourceType.EMPTY:
            if self.path:
                self.type = ImageSourceType.UPLOAD
            elif self.url:
                self.type = ImageSourceType.LINK

    @property
    def is_automated(self) -> bool:
        return self.type.is_automated


class ShowdownImage(BaseModel):

    edition: Edition = Edition.NONE
    expansion: Expansion = Expansion.BS
    source: ImageSource = ImageSource()
    parallel: ImageParallel = ImageParallel.NONE
    special_edition: SpecialEdition = SpecialEdition.NONE
    output_folder_path: Optional[str] = None
    output_file_name: Optional[str] = None
    set_name: Optional[str] = None
    set_year: Optional[int] = None
    set_number: str = '—'
    add_one_to_set_year: bool = False
    show_year_text: bool = False
    is_bordered: bool = False
    is_dark_mode: bool = False
    hide_team_logo: bool = False
    use_secondary_color: bool = False
    error: Optional[str] = None
    nickname_index: Optional[int] = None

    def update_special_edition(self, has_nationality: bool = False, enable_cooperstown_special_edition: bool = False, year:str = None, is_04_05: bool = False) -> None:
        if self.special_edition == SpecialEdition.NONE:
            if self.edition == Edition.ALL_STAR_GAME and year == '2023':
                self.special_edition = SpecialEdition.ASG_2023
                return 
            
            if self.edition == Edition.SUPER_SEASON and is_04_05:
                self.special_edition = SpecialEdition.SUPER_SEASON
                return 
            
            if self.edition == Edition.COOPERSTOWN_COLLECTION and enable_cooperstown_special_edition:
                self.special_edition = SpecialEdition.COOPERSTOWN_COLLECTION
                return 
            
            if self.edition == Edition.NATIONALITY and has_nationality:
                self.special_edition = SpecialEdition.NATIONALITY
                return 

            if self.parallel == ImageParallel.TEAM_COLOR_BLAST and self.is_dark_mode:
                self.special_edition = SpecialEdition.TEAM_COLOR_BLAST_DARK
                return 
            
    @validator('nickname_index', always=True, pre=True)
    def clean_nickname_index(cls, nickname_index:int) -> int:

        if nickname_index is None:
            return None
        
        try:
            as_int = int(nickname_index)
            if as_int > 6:
                return None
            return as_int
        except:
            return None
