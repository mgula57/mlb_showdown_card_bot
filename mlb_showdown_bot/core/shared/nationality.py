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
            case _: return 'BLUE'

    @property
    def logo_size_multiplier(self) -> float:
        return 1.25
    
    @property
    def three_letter_mlb_api_code(self) -> str:
        match self:
            case Nationality.US: return 'USA'
            case Nationality.DO: return 'DOM'
            case Nationality.VE: return 'VEN'
            case Nationality.CU: return 'CUB'
            case Nationality.CA: return 'CAN'
            case Nationality.MX: return 'MEX'
            case Nationality.PR: return 'PUR'
            case Nationality.PA: return 'PAN'
            case Nationality.JP: return 'JPN'
            case Nationality.GB: return 'GBR'
            case Nationality.DE: return 'DEU'
            case Nationality.AU: return 'AUS'
            case Nationality.CO: return 'COL'
            case Nationality.KR: return 'KOR'
            case Nationality.CW: return 'CUW'
            case Nationality.TW: return 'TPE'
            case Nationality.NI: return 'NCA'
            case Nationality.NL: return 'NED'
            case Nationality.IT: return 'ITA'
            case Nationality.CN: return 'CHN'
            case Nationality.CZ: return 'CZE'
            case Nationality.IS: return 'ISR'
            case Nationality.BR: return 'BRA'
            case _: return 'UNK'
            