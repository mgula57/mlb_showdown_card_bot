from enum import Enum


# ---------------------------------------
# PLAYER IMAGE COMPONENT
# ---------------------------------------

class PlayerImageComponent(Enum):

    BACKGROUND = "BG"
    CUSTOM_BACKGROUND = "CUSTOM BG"
    CUSTOM_FOREGROUND = "CUSTOM FG"
    SHADOW = "SHADOW"
    GLOW = "GLOW"
    CUT = "CUT"
    GRADIENT = "GRADIENT"
    COOPERSTOWN = "COOPERSTOWN"
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
            'GRADIENT',
            'RAINBOW_FOIL',
            'SAPPHIRE',
            'RADIAL',
            'COMIC_BOOK_LINES',
            'GOLD_RUSH',
            'GOLD',
            'WHITE_SMOKE',
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

class SpecialEdition(Enum):
    
    ASG_2023 = "ASG 2023"
    COOPERSTOWN_COLLECTION = "CC"
    SUPER_SEASON = "SS"
    TEAM_COLOR_BLAST_DARK = "TCBD"
    NATIONALITY = "NATIONALITY"
    NONE = "NONE"

    @property
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
        match self.name:
            case "COOPERSTOWN_COLLECTION": return {
                PlayerImageComponent.BACKGROUND: 0.33,
            }
            case "SUPER_SEASON": return {
                PlayerImageComponent.BACKGROUND: 0.75,
            }
        return {}

# ---------------------------------------
# IMAGE PARALLELS
# ---------------------------------------


class ImageParallel(Enum):
    
    RAINBOW_FOIL = "RF"
    SAPPHIRE = "SPH"
    BLACK_AND_WHITE = "B&W"
    RADIAL = "RAD"
    COMIC_BOOK_HERO = "CB"
    GOLD_RUSH = "GOLDRUSH"
    GOLD = "GOLD"
    WHITE_SMOKE = "WS"
    FLAMES = "FLAMES"
    TEAM_COLOR_BLAST = "TCB"
    MYSTERY = "MYSTERY"
    NONE = "NONE"

    @property
    def has_special_components(self) -> bool:
        return self.name not in ['NONE', 'BLACK_AND_WHITE']

    @property
    def special_component_additions(self) -> dict[str,str]:
        match self.name:
            case "RAINBOW_FOIL": return { PlayerImageComponent.RAINBOW_FOIL: "RAINBOW-FOIL" }
            case "SAPPHIRE": return { PlayerImageComponent.SAPPHIRE: "SAPPHIRE" }
            case "RADIAL": return { PlayerImageComponent.RADIAL: "RADIAL" }
            case "COMIC_BOOK_HERO": return { PlayerImageComponent.COMIC_BOOK_LINES: PlayerImageComponent.COMIC_BOOK_LINES.name }
            case "GOLD_RUSH": return { PlayerImageComponent.GOLD_RUSH: PlayerImageComponent.GOLD_RUSH.name }
            case "GOLD": return { PlayerImageComponent.GOLD: PlayerImageComponent.GOLD.name }
            case "WHITE_SMOKE": return { PlayerImageComponent.WHITE_SMOKE: PlayerImageComponent.WHITE_SMOKE.name, PlayerImageComponent.BACKGROUND: None }
            case "FLAMES": return { PlayerImageComponent.FLAMES: PlayerImageComponent.FLAMES.name }
            case "TEAM_COLOR_BLAST": return { PlayerImageComponent.WHITE_CIRCLE: PlayerImageComponent.WHITE_CIRCLE.name, PlayerImageComponent.TEAM_LOGO: None, PlayerImageComponent.TEAM_COLOR: None, PlayerImageComponent.BACKGROUND: None }
            case _: return {}

    @property
    def special_components_replacements(self) -> dict[str,str]:
        match self.name:
            case "SAPPHIRE" | "WHITE_SMOKE" | "FLAMES" | "TEAM_COLOR_BLAST" | "GOLD_RUSH" | "GOLD": return { PlayerImageComponent.GLOW: PlayerImageComponent.SHADOW }
            case _: return {}
    
    @property
    def image_type_saturations_dict(self) -> dict[str,float]:
        match self.name:
            case "COMIC_BOOK_HERO" | "WHITE_SMOKE": return { PlayerImageComponent.BACKGROUND: 0.05 }
            case "GOLD_RUSH" | "GOLD": return { PlayerImageComponent.BACKGROUND: 0.40 }
            case "TEAM_COLOR_BLAST": return { PlayerImageComponent.TEAM_LOGO: 0.10 }
            case _: return {}

    @property
    def is_team_background_black_and_white(self) -> bool:
        return self.name in ['COMIC_BOOK_HERO', 'GOLD_RUSH', 'GOLD', 'WHITE_SMOKE']
    
    @property
    def color_override_04_05_chart(self) -> str:
        match self.name:
            case 'GOLD_RUSH': return 'YELLOW'
            case 'GOLD': return 'YELLOW'
            case 'FLAMES': return 'RED'
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
    EXPANSION = "expansion"
    COMMAND = "command"
    STYLE = "style"
    BOT_LOGO = "bot_logo"