from enum import Enum

class Nationality(Enum):

    US = 'US'
    DO = 'DO'
    VE = 'VE'
    CU = 'CU'
    CA = 'CA'
    MX = 'MX'
    PR = 'PR'
    PA = 'PA'
    JP = 'JP'
    GB = 'GB'
    DE = 'DE'
    AU = 'AU'
    CO = 'CO'
    KR = 'KR'
    CW = 'CW'
    TW = 'TW'
    NI = 'NI'
    NL = 'NL'
    IT = 'IT'
    CN = 'CN'
    CZ = 'CZ'
    IS = 'IS'
    BR = 'BR'
    ES = 'ES'
    ZA = 'ZA'
    NONE = 'NONE'

    @classmethod
    def _missing_(cls, value):
        return cls.NONE

    @property
    def is_unknown(self) -> bool:
        return self.value == 'NONE'
    
    @property
    def is_populated(self) -> bool:
        return not self.is_unknown
    
    @property
    def primary_color(self) -> tuple[int,int,int,int]:
        if len(self.colors) == 0:
            return (0,0,0,0)
        
        return self.colors[0]
    
    @property
    def secondary_color(self) -> tuple[int,int,int,int]:
        num_colors = len(self.colors)

        match num_colors:
            case 0: return (0,0,0,0)
            case 1: return self.primary_color
            case _: return self.colors[1]
        
    @property
    def colors(self) -> list[tuple[int,int,int,int]]:
        match self.value:
            case 'US': return [
                (178, 34, 52, 255), # RED
                (60, 59, 110, 255), # BLUE
            ]
            case 'DO': return [
                (206, 17, 38, 255), # RED
                (0, 45, 98, 255), # BLUE
            ]
            case 'VE': return [
                (223, 179, 2, 255), # YELLOW
                (0, 36, 125, 255), # BLUE
                (207, 20, 43, 255), # RED
            ]
            case 'CU': return [
                (0, 42, 143, 255), # BLUE
                (203, 21, 21, 255), # RED        
            ]
            case 'CA': return [
                (234, 6, 25, 255), # RED        
            ]
            case 'MX': return [
                (0, 103, 71, 255), # GREEN
                (205, 17, 39, 255), # RED
            ]
            case 'PR': return [
                (60, 93, 170, 255), # BLUE
                (223, 28, 35, 255), # RED
            ]
            case 'PA': return [
                (7, 35, 87, 255), # BLUE
                (218, 18, 26, 255), # RED
            ]
            case 'JP': return [
                (188, 0, 45, 255), # RED
                (14, 25, 47, 255), # NAVY
            ]
            case 'GB': return [
                (207, 20, 43, 255), # RED
                (0, 36, 125, 255), # NAVY
            ]
            case 'DE': return [
                (0, 0, 0, 255), # BLACK
                (221, 0, 0, 255), # RED
                (255, 206, 0, 255), # YELLOW
            ]
            case 'AU': return [
                (0, 0, 102, 255), # BLUE
                (205, 0, 1, 255), # RED
            ]
            case 'CO': return [
                (202, 166, 17, 255), # YELLOW
                (1, 56, 147, 255), # BLUE
                (205, 17, 39, 255), # RED
            ]
            case 'KR': return [
                (1, 67, 122, 255), # BLUE
                (219, 26, 50, 255), # RED
            ]
            case 'CW': return [
                (1, 42, 126, 255), # BLUE
                (250, 232, 19, 255), # YELLOW
            ]
            case 'TW': return [
                (237, 29, 36, 255), # RED
                (42, 48, 135, 255), # BLUE
            ]
            case 'NI': return [
                (0, 101, 204, 255), # BLUE
            ]
            case 'NL': return [
                (33, 70, 139, 255), # BLUE
                (174, 28, 40, 255), # RED
            ]
            case 'IT': return [
                (0, 146, 71, 255), # GREEN
                (206, 43, 54, 255), # RED
            ]
            case 'CN': return [
                (223, 40, 15, 255), # RED
                (255, 223, 0, 255), # YELLOW
            ]
            case 'CZ': return [
                (215, 20, 26, 255), # RED
                (17, 69, 126, 255), # BLUE
            ]
            case 'IS': return [
                (1, 55, 183, 255), # BLUE
            ]
            case 'BR': return [
                (0, 148, 64, 255), # GREEN
                (255, 203, 0, 255), # YELLOW
            ]
            case 'ES': return [
                (173, 21, 25, 255), # RED
                (250, 189, 0, 255), # YELLOW
            ]
            case 'ZA': return [
                (224, 60, 49, 255), # RED
                (0, 119, 73, 255), # GREEN
                (0, 20, 137, 255), # BLUE
            ]
            case _: return [
                (0, 0, 0, 0), # BLACK
            ]

    @property
    def template_color(self) -> str:
        match self.value:
            case 'US': return 'RED'
            case 'DO': return 'RED'
            case 'VE': return 'YELLOW'
            case 'CU': return 'BLUE'
            case 'CA': return 'RED'
            case 'MX': return 'GREEN'
            case 'PR': return 'BLUE'
            case 'PA': return 'BLUE'
            case 'JP': return 'RED'
            case 'GB': return 'RED'
            case 'DE': return 'RED'
            case 'AU': return 'BLUE'
            case 'CO': return 'YELLOW'
            case 'KR': return 'BLUE'
            case 'CW': return 'BLUE'
            case 'TW': return 'RED'
            case 'NI': return 'BLUE'
            case 'NL': return 'BLUE'
            case 'IT': return 'GREEN'
            case 'CN': return 'RED'
            case 'CZ': return 'RED'
            case 'IS': return 'BLUE'
            case 'BR': return 'YELLOW'
            case 'ES': return 'RED'
            case 'ZA': return 'BLUE'
            case _: return 'BLUE'

    @property
    def logo_size_multiplier(self) -> float:
        return 1.25
    
            
class WBCTeam(Enum):
    AUS = "AUS"
    BRA = "BRA"
    CAN = "CAN"
    CHN = "CHN"
    COL = "COL"
    CUB = "CUB"
    CZE = "CZE"
    DOM = "DOM"
    ESP = "ESP"
    GBR = "GBR"
    ISR = "ISR"
    ITA = "ITA"
    JPN = "JPN"
    KOR = "KOR"
    MEX = "MEX"
    NCA = "NCA"
    NED = "NED"
    PAN = "PAN"
    PUR = "PUR"
    RSA = "RSA"
    TPE = "TPE"
    USA = "USA"
    VEN = "VEN"

    NONE = 'NONE'

    @classmethod
    def _missing_(cls, value):
        return cls.NONE

    @property
    def nationality(self) -> Nationality:
        match self:
            case WBCTeam.AUS: return Nationality.AU
            case WBCTeam.BRA: return Nationality.BR
            case WBCTeam.CAN: return Nationality.CA
            case WBCTeam.CHN: return Nationality.CN
            case WBCTeam.COL: return Nationality.CO
            case WBCTeam.CUB: return Nationality.CU
            case WBCTeam.CZE: return Nationality.CZ
            case WBCTeam.DOM: return Nationality.DO
            case WBCTeam.ESP: return Nationality.ES
            case WBCTeam.GBR: return Nationality.GB
            case WBCTeam.ISR: return Nationality.IS
            case WBCTeam.ITA: return Nationality.IT
            case WBCTeam.JPN: return Nationality.JP
            case WBCTeam.KOR: return Nationality.KR
            case WBCTeam.MEX: return Nationality.MX
            case WBCTeam.NCA: return Nationality.NI
            case WBCTeam.NED: return Nationality.NL
            case WBCTeam.PAN: return Nationality.PA
            case WBCTeam.PUR: return Nationality.PR
            case WBCTeam.RSA: return Nationality.ZA
            case WBCTeam.TPE: return Nationality.TW
            case WBCTeam.USA: return Nationality.US
            case WBCTeam.VEN: return Nationality.VE
            case _: return Nationality.NONE

    @property
    def logo_size_multiplier(self) -> float:
        return 1.00

    @property
    def colors(self) -> list[tuple[int,int,int,int]]:
        """Override colors for WBC teams that differ from their nationality's typical colors, to better match their WBC branding"""
        match self:
            case WBCTeam.AUS: return [
                (0, 72, 58, 255), # GREEN
                (255, 188, 44, 255), # YELLOW
            ]
            case WBCTeam.BRA: return [
                (255, 223, 1, 255), # YELLOW
                (1, 84, 158, 255), # BLUE
            ]
            case WBCTeam.ITA: return [
                (8, 94, 153, 255), # BLUE
                (239, 73, 66, 255), # RED
            ]
            case WBCTeam.NED: return [
                (244, 124, 49, 255), # ORANGE
                (0, 0, 0, 255), # BLACK
            ]
            case _: 
                return self.nationality.colors

    @property
    def primary_color(self) -> tuple[int,int,int,int]:
        if len(self.colors) == 0:
            return (0,0,0,0)
        
        return self.colors[0]
    
    @property
    def secondary_color(self) -> tuple[int,int,int,int]:
        num_colors = len(self.colors)

        match num_colors:
            case 0: return (0,0,0,0)
            case 1: return self.primary_color
            case _: return self.colors[1]

    def logo_extension(self, wbc_year: int) -> str:
        """Adds `-` and an index for the few teams that had multiple logos across different WBC years"""
        try:
            wbc_year = int(wbc_year)
        except:
            return ""
        
        match self:
            case WBCTeam.CHN:
                if wbc_year <= 2017:
                    return "-1"
            case WBCTeam.JPN:
                if wbc_year <= 2013:
                    return "-1"
            case WBCTeam.KOR:
                if wbc_year <= 2017:
                    return "-1"
        
        return ""
    