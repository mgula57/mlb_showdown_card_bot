import ipaddress
import os
import re
import socket
import requests
from enum import Enum
from io import BytesIO
from urllib.parse import urljoin, urlparse
from pydantic import BaseModel, PrivateAttr, ValidationInfo, field_validator
from typing import ClassVar, Optional, Union

from ...core.shared.nationality import WBCTeam

# INTERNAL
from .stats.stat_highlights import StatHighlightsType, StatHighlightsCategory

# ---------------------------------------
# MARK: EDITION
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
    PROMO = "PM"
    WBC = "WBC"

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
        return self not in [Edition.COOPERSTOWN_COLLECTION, Edition.NATIONALITY, Edition.ALL_STAR_GAME]
    
    @property
    def ignore_showdown_library(self) -> bool:
        return self in [Edition.NATIONALITY] # TODO: NATIONALITY DATA CURRENTLY NOT IN SL, REMOVE AFTER ADDING

    @property
    def has_additional_logo_00_01(self) -> bool:
        return self in [Edition.COOPERSTOWN_COLLECTION, Edition.ALL_STAR_GAME, Edition.SUPER_SEASON, Edition.ROOKIE_SEASON, Edition.POSTSEASON, Edition.WBC]

# ---------------------------------------
# MARK: EXPANSION
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
# MARK: PLAYER IMAGE COMPONENT
# ---------------------------------------

class PlayerImageComponent(str, Enum):

    BACKGROUND = "BG"
    CUSTOM_BACKGROUND = "CUSTOM BG"
    CUSTOM_FOREGROUND = "CUSTOM FG"
    CUSTOM_FOREGROUND_1 = "CUSTOM FG 1"
    CUSTOM_FOREGROUND_2 = "CUSTOM FG 2"
    CUSTOM_FOREGROUND_3 = "CUSTOM FG 3"
    CUSTOM_FOREGROUND_4 = "CUSTOM FG 4"
    CUSTOM_FOREGROUND_5 = "CUSTOM FG 5"
    SHADOW = "SHADOW"
    GLOW = "GLOW"
    CUT = "CUT"
    GRADIENT = "GRADIENT"
    DARKENER = "DARKENER"
    COOPERSTOWN = "COOPERSTOWN"
    POSTSEASON = "POSTSEASON"
    ELLIPSE_EXTRALARGE = "ELLIPSE-EXTRALARGE"
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
    GALAXY = "GALAXY"
    WHITE_SMOKE = "WHITE_SMOKE"
    FLAMES = "FLAMES"
    WHITE_CIRCLE = "WHITE_CIRCLE"
    BLACK_CIRCLE = "BLACK_CIRCLE"
    TEAM_COLOR = "TEAM_COLOR"
    TEAM_LOGO = "TEAM_LOGO"
    NAME_CONTAINER_2000 = "NAME_CONTAINER_2000"

    # STARS
    STARS = "STARS"

    @property
    def load_source(self) -> str:
        match self.name:
            case "BACKGROUND" | "SHADOW" | "GLOW" | "CUT": return "DOWNLOAD"
            case "TEAM_COLOR": return "COLOR"
            case "TEAM_LOGO": return "TEAM_LOGOS"
            case "NAME_CONTAINER_2000": return "NAME_CONTAINER"
            case "SILHOUETTE": return "SILHOUETTE"
            case "ELLIPSE_LARGE" | "ELLIPSE_MEDIUM" | "ELLIPSE_SMALL": return "CIRCLE"
            case "STARS": return "STARS"
            case _: return "CARD_ART"

    @property
    def source_name(self) -> str:
        """
        Component name as it appears in the it's source (ex: GOOGLE_DRIVE, LOCAL_DRIVE, etc.).
        Ex: GLOW and SHADOW images now use CUT as the source.
        """
        match self.name:
            case "GLOW" | "SHADOW": return "CUT"
            case _: return self.value

    @property
    def is_loaded_via_download(self) -> bool:
        return self.load_source == "DOWNLOAD"
    
    @property
    def adjust_paste_coordinates_for_bordered(self) -> bool:
        return self.name in ["NAME_CONTAINER_2000"]
    
    @property
    def ignores_custom_crop(self) -> bool:
        return self.name in [
            "SUPER_SEASON",
            "CUSTOM_BACKGROUND",
            "CUSTOM_FOREGROUND",
            "CUSTOM_FOREGROUND_1",
            "CUSTOM_FOREGROUND_2",
            "CUSTOM_FOREGROUND_3",
            "CUSTOM_FOREGROUND_4",
            "CUSTOM_FOREGROUND_5",
            "GRADIENT",
            "RAINBOW_FOIL",
            "SAPPHIRE",
            "RADIAL",
            "COOPERSTOWN",
            "COMIC_BOOK_LINES",
            "GOLD_RUSH",
            "GOLD",
            "WHITE_SMOKE",
            "GALAXY",
            "FLAMES",
            "WHITE_CIRCLE",
            "BLACK_CIRCLE",
            "TEAM_COLOR",
            "TEAM_LOGO",
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
        return self.name in ['ELLIPSE_LARGE','ELLIPSE_MEDIUM','ELLIPSE_SMALL','ELLIPSE_EXTRALARGE']
    
    @property
    def layering_index(self) -> int:
        ordered_list = [
            'BACKGROUND',
            'CUSTOM_BACKGROUND',
            'COOPERSTOWN',
            'SUPER_SEASON',
            'POSTSEASON',
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
            "GALAXY",
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
            "CUSTOM_FOREGROUND_1",
            "CUSTOM_FOREGROUND_2",
            "CUSTOM_FOREGROUND_3",
            "CUSTOM_FOREGROUND_4",
            "CUSTOM_FOREGROUND_5",
            'SILHOUETTE',
        ]
        return ordered_list.index(self.name) if self.name in ordered_list else None

    @property
    def frame_size(self) -> int:
        """Returns the size of the frame for the image component. Only applies to images that are built via Python."""
        match self.name:
            case "ELLIPSE_EXTRALARGE": return 500
            case "ELLIPSE_LARGE": return 375
            case "ELLIPSE_MEDIUM": return 275
            case "ELLIPSE_SMALL": return 200
            case _: return None


# ---------------------------------------
# MARK: SPECIAL EDITION
# ---------------------------------------

class SpecialEdition(str, Enum):
    
    ASG_2023 = "ASG 2023"
    ASG_2024 = "ASG 2024"
    ASG_2025 = "ASG 2025"
    ASG_2026 = "ASG 2026"
    ASG_LINES = "ASG LINES"
    COOPERSTOWN_COLLECTION = "CC"
    SUPER_SEASON = "SS"
    TEAM_COLOR_BLAST_DARK = "TCBD"
    NATIONALITY = "NATIONALITY"
    WBC = "WBC"
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
    def hide_2000_player_name(self) -> bool:
        return self in [SpecialEdition.ASG_2024, SpecialEdition.ASG_2025, SpecialEdition.ASG_2026, SpecialEdition.WBC]

    @property
    def ignore_edition_based_team_logo(self) -> bool:
        return self in [SpecialEdition.ASG_LINES]

    @property
    def has_full_bleed_background(self) -> bool:
        return self in [SpecialEdition.ASG_2024, SpecialEdition.ASG_2025, SpecialEdition.ASG_2026]

    @property
    def image_component_saturation_adjustments_dict(self) -> dict[PlayerImageComponent, float]:
        """Adjusts the saturation of the image components for the special edition image."""
        match self:
            case SpecialEdition.COOPERSTOWN_COLLECTION | SpecialEdition.POSTSEASON: return {
                PlayerImageComponent.BACKGROUND: 0.33,
            }
            case SpecialEdition.SUPER_SEASON: return {
                PlayerImageComponent.BACKGROUND: 0.75,
            }
            case SpecialEdition.ASG_LINES: return {
                PlayerImageComponent.BACKGROUND: 0.30,
            }
        return {}
    
    def image_component_color_overlay_dict(self, primary_color:tuple[int,int,int,int], secondary_color:tuple[int,int,int,int]) -> dict[PlayerImageComponent, tuple[int,int,int,int]]:
        """Returns dict of image components that need to be colored for this special edition image.
        
        Args:
            primary_color (tuple[int,int,int,int]): The primary color to use for the overlay.
            secondary_color (tuple[int,int,int,int]): The secondary color to use for the overlay.

        Returns:
            dict[PlayerImageComponent, float]: Dict of image components that need to be colored for this special edition image.
        """
        match self:
            case SpecialEdition.ASG_2024: return {
                PlayerImageComponent.CUSTOM_FOREGROUND: primary_color,
                PlayerImageComponent.CUSTOM_FOREGROUND_2: primary_color,
                PlayerImageComponent.CUSTOM_FOREGROUND_3: secondary_color,
            }
            case SpecialEdition.ASG_2026: return {
                PlayerImageComponent.CUSTOM_FOREGROUND_1: secondary_color,
            }
        return {}

# ---------------------------------------
# MARK: IMAGE PARALLELS
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
    BREAKOUT = "BREAKOUT"
    MYSTERY = "MYSTERY"
    MOONLIGHT = "MOONLIGHT"
    GALAXY = "GALAXY"
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
            case "BREAKOUT": return { PlayerImageComponent.BACKGROUND: None }
            case "TEAM_COLOR_BLAST": return { PlayerImageComponent.WHITE_CIRCLE: PlayerImageComponent.WHITE_CIRCLE.name, PlayerImageComponent.TEAM_LOGO: None, PlayerImageComponent.TEAM_COLOR: None, PlayerImageComponent.BACKGROUND: None }
            case "MOONLIGHT":
                comps_dict = { PlayerImageComponent.MOONLIGHT: PlayerImageComponent.MOONLIGHT.name, PlayerImageComponent.BACKGROUND: None }
                if set == '2001':
                    comps_dict[PlayerImageComponent.TEAM_LOGO] = None
                return comps_dict
            case "GALAXY": return { PlayerImageComponent.GALAXY: PlayerImageComponent.GALAXY.name, PlayerImageComponent.BACKGROUND: None }
            case _: return {}

    @property
    def special_components_replacements(self) -> dict[str,str]:
        match self.name:
            case "SAPPHIRE" | "WHITE_SMOKE" | "FLAMES" | "TEAM_COLOR_BLAST" | "GOLD_RUSH" | "GOLD" | "GOLD_FRAME" | "MOONLIGHT" | "GALAXY" | "BREAKOUT": return { PlayerImageComponent.GLOW: PlayerImageComponent.SHADOW }
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
    def hides_name_container_2000(self) -> bool:
        return self.name in ['BREAKOUT']

    @property
    def name_container_suffix_2000(self) -> str:
        match self.name:
            case 'GOLD' | 'GOLD_RUSH' | 'GOLD_FRAME': return '-GOLD'
            case _: return ''

    @property
    def has_team_color_template_04_05(self) -> bool:
        return self.name in ['TEAM_COLOR_BLAST', 'BREAKOUT']

    @property
    def template_color_04_05(self) -> str:
        match self:
            case ImageParallel.MOONLIGHT: return "BLACK"
            case _: return None

    @property
    def name_cleaned(self) -> str:
        """Cleaned version of the name, uppercased"""
        return self.name.replace('_', ' ').upper()

# ---------------------------------------
# MARK: TEMPLATE IMAGE COMPONENT
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
    COOPERSTOWN = "cooperstown"
    ROOKIE_SEASON = "rookie_season"
    ROOKIE_SEASON_YEAR_TEXT = "rookie_season_year_text"
    POSTSEASON = "postseason"
    POSTSEASON_YEAR_TEXT = "postseason_year_text"
    POSTSEASON_YEAR_TEXT_BOX = "postseason_year_text_box"
    WBC = "wbc"
    EXPANSION = "expansion"
    COMMAND = "command"
    STYLE = "style"
    STYLE_LOGO = "style_logo"
    STYLE_LOGO_BG = "style_logo_bg"
    STYLE_TEXT = "style_text"
    BOT_LOGO = "bot_logo"
    SPLIT = "split"
    STAT_HIGHLIGHTS = "stat_highlights"

# ---------------------------------------
# MARK: IMAGE SOURCE
# ---------------------------------------

class ImageSourceType(str, Enum):
    UPLOAD = "Upload"
    LINK = 'Link'
    LOCAL_CACHE = 'Local Cache'
    GOOGLE_DRIVE = 'Google Drive'
    USER_DRIVE = 'User Drive'
    LOCAL_DRIVE = 'Local Drive'
    EMPTY = 'EMPTY'

    def __repr__(self) -> str:
        return self.value

    @property
    def is_user_generated(self) -> bool:
        return self.name in ['UPLOAD', 'LINK']

    @property
    def is_automated(self) -> bool:
        return self.name in ['LOCAL_CACHE', 'GOOGLE_DRIVE', 'USER_DRIVE', 'LOCAL_DRIVE']

    @property
    def is_empty(self) -> bool:
        return self.name == 'EMPTY'


class ImageLibrary(BaseModel):
    """A folder of auto images searched for player image matches.

    The Showdown Bot library is built in. Others are Google Drive folders users shared (Viewer)
    with the user-drive service account, searched in the order the user picked in Account settings.
    """

    SHOWDOWN_BOT_ID: ClassVar[str] = 'SHOWDOWN_BOT'
    # ex: BG-1994-Bonds-(bondsba01)-(SFG).png
    FILE_NAME_PATTERN: ClassVar[re.Pattern] = re.compile(r'^(BG|CUT)-[^-]+-.*\([^)]+\)')

    id: str
    name: str
    folder_id: Optional[str] = None

    @classmethod
    def showdown_bot(cls) -> 'ImageLibrary':
        return cls(id=cls.SHOWDOWN_BOT_ID, name='Showdown Bot')

    @property
    def is_showdown_bot(self) -> bool:
        return self.id == self.SHOWDOWN_BOT_ID

    @classmethod
    def ordered(cls, libraries: list['ImageLibrary'], order: Optional[list[str]]) -> list['ImageLibrary']:
        """Libraries sorted by the user's saved order. Unordered user libraries go first, since
        connecting one implies wanting it searched; the Showdown Bot library is always included."""
        by_id = {lib.id: lib for lib in [*libraries, cls.showdown_bot()]}
        ordered_ids = [lib_id for lib_id in (order or []) if lib_id in by_id]
        unordered_ids = [lib.id for lib in libraries if lib.id not in ordered_ids]
        ids = unordered_ids + ordered_ids
        if cls.SHOWDOWN_BOT_ID not in ids:
            ids.append(cls.SHOWDOWN_BOT_ID)
        return [by_id[lib_id] for lib_id in ids]

    @classmethod
    def is_recognized_file_name(cls, file_name: str) -> bool:
        """True if the file follows the {BG|CUT}-{YEAR}-{NAME}-({PLAYER ID})... naming the matcher needs."""
        return bool(cls.FILE_NAME_PATTERN.match(file_name or ''))


class ImageMatchType(str, Enum):
    """How well a library's auto images fit a card, best first"""
    EXACT = "exact"
    TEAM_MATCH = "team match"
    YEAR_MATCH = "year match"
    NO_MATCH = "no match"

    @property
    def rank(self) -> int:
        return list(ImageMatchType).index(self)


class AutoImageFile(BaseModel):
    """Attributes parsed from an auto image file name.

    ex: BG-2025-Raleigh-(raleica01)-(SEA).png
      - component: BG
      - year: 2025
      - player_name: Raleigh
      - player_id: raleica01
      - team_id: SEA
    """

    component: Optional[str] = None
    year: str
    player_name: str = ''
    player_id: str
    team_id: Optional[str] = None
    player_type_override: Optional[str] = None
    is_postseason: bool = False
    is_wbc: bool = False

    @classmethod
    def from_file_name(cls, file_name: str) -> Optional['AutoImageFile']:
        """Parse a {COMPONENT}-{YEAR}-{NAME}-({PLAYER ID})-(...) file name. None if it has no player id."""
        component, _, name = (file_name or '').partition('-')
        if not name:
            return None
        return cls.from_name_without_component(name, component=component.upper())

    @classmethod
    def from_name_without_component(cls, name: str, component: Optional[str] = None) -> Optional['AutoImageFile']:
        """Parse a {YEAR}-{NAME}-({PLAYER ID})-(...) name (component prefix already removed)."""
        attributes: dict = {'component': component, 'is_wbc': '(WBC_' in name}
        name_parts = name.rsplit('.', 1)[0].split('-')
        player_name_parts: list[str] = []
        for index, text in enumerate(name_parts):
            has_parenthesis = text.startswith('(') and text.endswith(')')
            value = text[1:-1] if has_parenthesis else text

            if index == 0:
                attributes['year'] = text
                continue

            if 'player_id' not in attributes:
                if has_parenthesis:
                    attributes['player_id'] = value
                else:
                    player_name_parts.append(text)
                # PLAYER ID CAN ALSO BE SHORT ENOUGH TO LOOK LIKE A TEAM, SO DON'T FALL THROUGH
                continue

            if has_parenthesis and len(text) <= 5:
                attributes['team_id'] = value
            if text == '(POST)':
                attributes['is_postseason'] = True
            if has_parenthesis and ('Hitter' in text or 'Pitcher' in text):
                # KEEP PARENTHESIS AND LOWERCASE TO MATCH STATS ARCHIVE (e.g., (hitter), (pitcher))
                attributes['player_type_override'] = text.lower()

        if not attributes.get('player_id') or not attributes.get('year'):
            return None
        return cls(player_name=' '.join(player_name_parts), **attributes)

    def match_type(self, year: str, team_id: Optional[str], player_type_override: Optional[str]) -> ImageMatchType:
        """How well this image fits a card. Postseason/WBC images never count, matching the card_bot classification."""
        if self.is_postseason or self.is_wbc or (self.player_type_override or None) != (player_type_override or None):
            return ImageMatchType.NO_MATCH
        is_year_match = self.year == str(year)
        is_team_match = team_id is not None and self.team_id == team_id
        if is_year_match and is_team_match:
            return ImageMatchType.EXACT
        if is_team_match:
            return ImageMatchType.TEAM_MATCH
        if is_year_match:
            return ImageMatchType.YEAR_MATCH
        return ImageMatchType.NO_MATCH


class ImageSource(BaseModel):

    type: ImageSourceType = ImageSourceType.EMPTY
    url: Optional[str] = None
    path: Optional[str] = None
    library_name: Optional[str] = None
    # SERVER-RESOLVED FROM THE USER'S ACCOUNT. PRIVATE SO IT'S NEVER PARSED FROM REQUEST/CARD JSON
    # (NO SEARCHING FOLDERS THE USER DOESN'T OWN) OR SERIALIZED (KEEPS FOLDER IDS OUT OF CARD JSON/LOGS)
    _libraries: list[ImageLibrary] = PrivateAttr(default_factory=list)

    @property
    def libraries(self) -> list[ImageLibrary]:
        return self._libraries

    def set_libraries(self, libraries: Optional[list[ImageLibrary]]) -> None:
        self._libraries = list(libraries or [])

    # SET BY THE WEB APP AT STARTUP SO REQUEST/CARD JSON CAN'T POINT `path` AT ARBITRARY SERVER FILES.
    # NONE = UNRESTRICTED (CLI, WHERE `path` IS A FILE ON THE USER'S OWN MACHINE)
    _allowed_path_root: ClassVar[Optional[str]] = None

    # DECODERS PILLOW MAY USE FOR USER IMAGES. PILLOW SNIFFS FORMAT FROM CONTENT, NOT THE EXTENSION,
    # SO WITHOUT THIS A ".png" UPLOAD COULD REACH THE BMP/TIFF/JPEG2000/ETC DECODERS
    ALLOWED_FORMATS: ClassVar[tuple[str, ...]] = ('PNG', 'JPEG', 'GIF', 'WEBP')
    MAX_DOWNLOAD_BYTES: ClassVar[int] = 16 * 1024 * 1024
    MAX_REDIRECTS: ClassVar[int] = 3
    DOWNLOAD_TIMEOUT_SECONDS: ClassVar[int] = 10

    def model_post_init(self, __context):
        """Post init to update the source type if empty"""
        if self.type == ImageSourceType.EMPTY:
            if self.path:
                self.type = ImageSourceType.UPLOAD
            elif self.url:
                self.type = ImageSourceType.LINK

    @property
    def is_automated(self) -> bool:
        return self.type.is_automated

    @classmethod
    def restrict_paths_to(cls, root: str) -> None:
        """Only allow `path` to reference files inside `root` (the web server's temp upload folder)."""
        cls._allowed_path_root = os.path.realpath(root)

    def open_source(self) -> Union[str, BytesIO]:
        """Resolve the user's image to something PIL can open: the local path, or the downloaded url bytes.

        Raises:
          ValueError: If the path is outside the allowed root, or the url is not a public http(s) address.
        """
        if self.path:
            root = self._allowed_path_root
            if root and os.path.commonpath([root, os.path.realpath(self.path)]) != root:
                raise ValueError("Image path is not allowed")
            return self.path
        return self._download_url(self.url)

    def _download_url(self, url: str) -> BytesIO:
        """Download a user image url, refusing non-public hosts (SSRF) and capping time and size.

        Redirects are followed manually so each hop's host is checked too.
        """
        for _ in range(self.MAX_REDIRECTS + 1):
            self._validate_public_url(url)
            with requests.get(url, timeout=self.DOWNLOAD_TIMEOUT_SECONDS, stream=True, allow_redirects=False) as response:
                if response.is_redirect:
                    url = urljoin(url, response.headers['Location'])
                    continue
                response.raise_for_status()
                content = BytesIO()
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    content.write(chunk)
                    if content.tell() > self.MAX_DOWNLOAD_BYTES:
                        raise ValueError("Image is too large")
                content.seek(0)
                return content
        raise ValueError("Image url redirected too many times")

    @staticmethod
    def _validate_public_url(url: str) -> None:
        """Raise unless the url is http(s) and its host resolves only to public internet addresses."""
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            raise ValueError("Image url must be http or https")
        try:
            addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80))
        except socket.gaierror:
            raise ValueError("Image url host could not be resolved")
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            ip = getattr(ip, 'ipv4_mapped', None) or ip
            if not ip.is_global:
                raise ValueError("Image url must point to a public address")
    
# ---------------------------------------
# MARK: IMAGE COLORING
# ---------------------------------------

class ImageColoring(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    MULTI = "MULTI"

# ---------------------------------------
# MARK: IMAGE FILE FORMAT
# ---------------------------------------

class ImageFileFormat(str, Enum):
    """File format the final card image is saved as."""

    PNG = "PNG"
    JPEG = "JPEG"

    @classmethod
    def _missing_(cls, value):
        # Accept CLI-style input like "jpg" or "png"
        if isinstance(value, str):
            normalized = value.strip().upper()
            return cls.JPEG if normalized == 'JPG' else cls.__members__.get(normalized)
        return None

    @property
    def extension(self) -> str:
        return 'jpg' if self == ImageFileFormat.JPEG else 'png'

    @property
    def save_kwargs(self) -> dict:
        """PIL save options. JPEG keeps full-resolution color (4:4:4 subsampling): PIL's default
        4:2:0 visibly smears saturated edges like team colors and red text. At quality 95 the
        average color difference vs PNG is below what's perceptible, at ~1/3 the file size."""
        if self == ImageFileFormat.JPEG:
            return {'format': 'JPEG', 'quality': 95, 'subsampling': 0, 'optimize': True}
        return {'format': 'PNG'}

# Format new card images are rendered in. `ShowdownImage.file_format` itself stays PNG by default,
# since it describes an already-rendered image and cards stored before JPEG (archive rows, cloud
# uploads) were PNG; every rendering entry point sets this explicitly instead.
DEFAULT_RENDER_FILE_FORMAT = ImageFileFormat.JPEG

# ---------------------------------------
# MARK: SHOWDOWN IMAGE
# ---------------------------------------

class ShowdownImage(BaseModel):

    edition: Edition = Edition.NONE
    expansion: Expansion = Expansion.BS
    source: ImageSource = ImageSource()
    parallel: ImageParallel = ImageParallel.NONE
    special_edition: SpecialEdition = SpecialEdition.NONE
    output_folder_path: Optional[str] = None
    output_file_name: Optional[str] = None
    file_format: ImageFileFormat = ImageFileFormat.PNG
    set_name: Optional[str] = None
    set_year: Optional[int] = None
    set_number: Optional[str] = None
    add_one_to_set_year: bool = False
    show_year_text: bool = False
    is_bordered: bool = False
    
    hide_team_logo: bool = False
    
    error: Optional[str] = None
    nickname_index: Optional[int] = None
    glow_multiplier: float = 1.0

    # COLORS
    is_dark_mode: bool = False
    color_primary: str = "#000000"
    color_secondary: str = "#ffffff"
    coloring: ImageColoring = ImageColoring.PRIMARY

    # STATS
    stat_highlights_type: StatHighlightsType = StatHighlightsType.NONE
    stat_highlights_list: list[str] = []
    disable_showing_stat_highlights: bool = False

    # AWARDS
    award_summary_list: Optional[list[str]] = None

    # ONLINE STORAGE
    upload_to_supabase: Optional[bool] = None
    storage_path: Optional[str] = None
    thumbnail_storage_path: Optional[str] = None

    def update_special_edition(self, has_nationality: bool = False, has_wbc_info: bool = False, enable_cooperstown_special_edition: bool = False, year:str = None, is_04_05: bool = False) -> None:
        if self.special_edition == SpecialEdition.NONE:

            if self.edition == Edition.ALL_STAR_GAME and year == '2023':
                self.special_edition = SpecialEdition.ASG_2023
                return 
            
            if self.edition == Edition.ALL_STAR_GAME and year == '2024':
                self.special_edition = SpecialEdition.ASG_2024
                return 
            
            if self.edition == Edition.ALL_STAR_GAME and year == '2025':
                self.special_edition = SpecialEdition.ASG_2025
                return
            
            if self.edition == Edition.ALL_STAR_GAME and year == '2026':
                self.special_edition = SpecialEdition.ASG_2026
                return
            
            if self.edition == Edition.ALL_STAR_GAME and is_04_05:
                try:
                    year_int = int(year)
                    if year_int >= 1980: # ASG LOGOS AVAILABLE FOR 1980 AND LATER
                        self.special_edition = SpecialEdition.ASG_LINES
                    return
                except:
                    pass
            
            if self.edition == Edition.SUPER_SEASON and is_04_05:
                self.special_edition = SpecialEdition.SUPER_SEASON
                return 
            
            if self.edition == Edition.COOPERSTOWN_COLLECTION and enable_cooperstown_special_edition:
                self.special_edition = SpecialEdition.COOPERSTOWN_COLLECTION
                return 
            
            if self.edition == Edition.NATIONALITY and has_nationality:
                self.special_edition = SpecialEdition.NATIONALITY
                return 
        
            if self.edition == Edition.WBC and has_wbc_info:
                self.special_edition = SpecialEdition.WBC
                return

            if self.parallel == ImageParallel.TEAM_COLOR_BLAST and self.is_dark_mode:
                self.special_edition = SpecialEdition.TEAM_COLOR_BLAST_DARK
                return 

    def apply_wbc_team_theming(self, wbc_team: WBCTeam, wbc_year: int) -> None:
        """Apply WBC team theming to the image based on the WBC team and year."""
        if type(wbc_team) == str:
            wbc_team = WBCTeam(wbc_team)

        if wbc_team and wbc_year:
            self.edition = Edition.WBC
            self.special_edition = SpecialEdition.WBC
            primary_color_tuple = wbc_team.primary_color
            self.color_primary = f"rgb({primary_color_tuple[0]}, {primary_color_tuple[1]}, {primary_color_tuple[2]})"
            secondary_color_tuple = wbc_team.secondary_color
            self.color_secondary = f"rgb({secondary_color_tuple[0]}, {secondary_color_tuple[1]}, {secondary_color_tuple[2]})"

    @field_validator('nickname_index', mode='before')
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


    # BACKWARDS COMPATIBILITY
    @property
    def use_secondary_color(self) -> bool:
        """Check if the image is secondary-colored."""
        return self.coloring == ImageColoring.SECONDARY

    @property
    def is_multi_colored(self) -> bool:
        """Check if the image is multi-colored."""
        return self.coloring == ImageColoring.MULTI