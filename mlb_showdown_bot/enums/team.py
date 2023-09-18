from enum import Enum

class Team(Enum):

    AB2 = 'AB2'
    AB3 = 'AB3'
    ABC = 'ABC'
    AG = 'AG'
    ALT = 'ALT'
    ANA = 'ANA'
    ARI = 'ARI'
    ATH = 'ATH'
    ATL = 'ATL'
    BAL = 'BAL'
    BBB = 'BBB'
    BBS = 'BBS'
    BCA = 'BCA'
    BE = 'BE'
    BEG = 'BEG'
    BLA = 'BLA'
    BLU = 'BLU'
    BLN = 'BLN'
    BOS = 'BOS'
    BRA = 'BRA'
    BRO = 'BRO'
    BRG = 'BRG'
    BSN = 'BSN'
    BTT = 'BTT'
    BUF = 'BUF'
    BWW = 'BWW'
    CAL = 'CAL'
    CAG = 'CAG'
    CBB = 'CBB'
    CBE = 'CBE'
    CBN = 'CBN'
    CC = 'CC'
    CCB = 'CCB'
    CCC = 'CCC'
    CCU = 'CCU'
    CEG = 'CEG'
    CEL = 'CEL'
    CEN = 'CEN'
    CHC = 'CHC'
    CHI = 'CHI'
    CHT = 'CHT'
    CHW = 'CHW'
    CIN = 'CIN'
    CLE = 'CLE'
    CKK = 'CKK'
    CLV = 'CLV'
    COL = 'COL'
    COR = 'COR'
    CRS = 'CRS'
    CSE = 'CSE'
    CS = 'CS'
    CSW = 'CSW'
    CT = 'CT'
    CTG = 'CTG'
    DET = 'DET'
    DS = 'DS'
    DTS = 'DTS'
    DW = 'DW'
    FLA = 'FLA'
    HAR = 'HAR'
    HBG = 'HBG'
    HG = 'HG'
    HIL = 'HIL'
    HOU = 'HOU'
    IAB = 'IAB'
    IA = 'IA'
    IC = 'IC'
    ID = 'ID'
    JRC = 'JRC'
    KCA = 'KCA'
    KCC = 'KCC'
    KCM = 'KCM'
    KCN = 'KCN'
    KCR = 'KCR'
    LAA = 'LAA'
    LAD = 'LAD'
    LOU = 'LOU'
    LOW = 'LOW'
    LRG = 'LRG'
    LVB = 'LVB'
    MB = 'MB'
    MGS = 'MGS'
    MIA = 'MIA'
    MIL = 'MIL'
    MIN = 'MIN'
    MLA = 'MLA'
    MON = 'MON'
    MRS = 'MRS'
    NE = 'NE'
    NBY = 'NBY'
    NEG = 'NEG'
    NLG = 'NLG'
    NYC = 'NYC'
    NYG = 'NYG'
    NYM = 'NYM'
    NYU = 'NYU'
    NYY = 'NYY'
    OAK = 'OAK'
    OLY = 'OLY'
    PBG = 'PBG'
    PBS = 'PBS'
    PC = 'PC'
    PHA = 'PHA'
    PHI = 'PHI'
    PK = 'PK'
    PIT = 'PIT'
    PRO = 'PRO'
    PS = 'PS'
    PTG = 'PTG'
    RES = 'RES'
    RIC = 'RIC'
    ROC = 'ROC'
    ROK = 'ROK'
    SDP = 'SDP'
    SEA = 'SEA'
    SEP = 'SEP'
    SFG = 'SFG'
    SLB = 'SLB'
    SLG = 'SLG'
    SLM = 'SLM'
    SLR = 'SLR'
    SL2 = 'SL2'
    SL3 = 'SL3'
    SLS = 'SLS'
    SNS = 'SNS'
    STL = 'STL'
    STP = 'STP'
    TC = 'TC'
    TC2 = 'TC2'
    TBD = 'TBD'
    TBR = 'TBR'
    TEX = 'TEX'
    TOL = 'TOL'
    TOR = 'TOR'
    TT = 'TT'
    WAP = 'WAP'
    WAS = 'WAS'
    WEG = 'WEG'
    WHS = 'WHS'
    WIL = 'WIL'
    WMP = 'WMP'
    WOR = 'WOR'
    WP = 'WP'
    WSA = 'WSA'
    WSH = 'WSH'
    WSN = 'WSN'
    MLB = "MLB"

# ------------------------------------------------------------------------
# COLOR
# ------------------------------------------------------------------------

    @property
    def primary_color(self) -> tuple[int,int,int,int]:
        match self.value:
            case 'AB2': return (172, 0, 0, 255)
            case 'AB3': return (172, 0, 0, 255)
            case 'ABC': return (172, 0, 0, 255)
            case 'AG': return (2, 2, 2, 255)
            case 'ALT': return (104, 5, 49, 255)
            case 'ANA': return (19, 41, 75, 255)
            case 'ARI': return (167, 25, 48, 255)
            case 'ATH': return (0, 51, 160, 255)
            case 'ATL': return (206, 17, 65, 255)
            case 'BAL': return (223, 70, 1, 255)
            case 'BBB': return (184, 0, 0, 255)
            case 'BBS': return (135, 72, 42, 255)
            case 'BCA': return (10, 53, 132, 255)
            case 'BE': return (12, 35, 64, 255)
            case 'BEG': return (0, 4, 42, 255)
            case 'BLA': return (236, 165, 73, 255)
            case 'BLU': return (243, 105, 22, 255)
            case 'BLN': return (21, 10, 106, 255)
            case 'BOS': return (189, 48, 57, 255)
            case 'BRA': return (55, 55, 55, 255)
            case 'BRO': return (8, 41, 132, 255)
            case 'BRG': return (248, 41, 31, 255)
            case 'BSN': return (213, 0, 50, 255)
            case 'BTT': return (1, 55, 129, 255)
            case 'BUF': return (36, 32, 33, 255)
            case 'BWW': return (8, 41, 132, 255)
            case 'CAL': return (191, 13, 62, 255)
            case 'CAG': return (18, 44, 73, 255)
            case 'CBB': return (25, 73, 158, 255)
            case 'CBE': return (200, 16, 46, 255)
            case 'CBN': return (37, 76, 139, 255)
            case 'CC': return (228, 0, 23, 255)
            case 'CCB': return (200, 16, 46, 255)
            case 'CCC': return (160, 135, 69, 255)
            case 'CCU': return (192, 0, 49, 255)
            case 'CEG': return (0, 4, 42, 255)
            case 'CEL': return (37, 76, 139, 255)
            case 'CEN': return (192, 0, 49, 255)
            case 'CHC': return (14, 51, 134, 255)
            case 'CHI': return (1, 31, 105, 255)
            case 'CHT': return (14, 0, 119, 255)
            case 'CHW': return (39, 37, 31, 255)
            case 'CIN': return (198,1,31,255)
            case 'CLE': return (227,25,55,255)
            case 'CKK': return (209, 9, 47, 255)
            case 'CLV': return (14, 0, 119, 255)
            case 'COL': return (51,0,111,255)
            case 'COR': return (198,1,31,255)
            case 'CRS': return (14, 0, 119, 255)
            case 'CSE': return (10, 34, 64, 255)
            case 'CS': return (10, 34, 64, 255)
            case 'CSW': return (10, 34, 64, 255)
            case 'CT': return (198,1,31,255)
            case 'CTG': return (198,1,31,255)
            case 'DET': return (12, 35, 64, 255)
            case 'DS': return (193, 44, 56, 255)
            case 'DTS': return (193, 44, 56, 255)
            case 'DW': return (189, 47, 45, 255)
            case 'FLA': return (2, 159, 171, 255)
            case 'HAR': return (5, 0, 51, 255)
            case 'HBG': return (5, 0, 51, 255)
            case 'HG': return (2, 2, 2, 255)
            case 'HIL': return (203, 17, 66, 255)
            case 'HOU': return (235, 110, 31, 255)
            case 'IAB': return (172, 0, 0, 255)
            case 'IA': return (160, 39, 60, 255)
            case 'IC': return (228, 0, 23, 255)
            case 'ID': return (172, 0, 0, 255)
            case 'JRC': return (219, 35, 77, 255)
            case 'KCA': return (2, 133, 68, 255)
            case 'KCC': return (34, 39, 63, 255)
            case 'KCM': return (243, 0, 0, 255)
            case 'KCN': return (34, 39, 63, 255)
            case 'KCR': return (0, 70, 135, 255)
            case 'LAA': return (186, 0, 33, 255)
            case 'LAD': return (0, 90, 156, 255)
            case 'LOU': return (185, 32, 39, 255)
            case 'LOW': return (234, 26, 43, 255)
            case 'LRG': return (18, 26, 65, 255)
            case 'LVB': return (234, 26, 43, 255)
            case 'MB': return (45, 45, 45, 255)
            case 'MGS': return (19, 16, 45, 255)
            case 'MIA': return (0, 163, 224, 255)
            case 'MIL': return (18, 40, 75, 255)
            case 'MIN': return (211,17,69,255)
            case 'MLA': return (0, 33, 68, 255)
            case 'MON': return (228, 0, 43, 255)
            case 'MRS': return (181, 0, 51, 255)
            case 'NE': return (12, 35, 64, 255)
            case 'NBY': return (25, 37, 62, 255)
            case 'NEG': return (0, 4, 42, 255)
            case 'NLG': return (17, 36, 55, 255)
            case 'NYC': return (162, 0, 45, 255)
            case 'NYG': return (227, 82, 5, 255)
            case 'NYM': return (252, 89, 16, 255)
            case 'NYU': return (7, 91, 72, 255)
            case 'NYY': return (12, 35, 64, 255)
            case 'OAK': return (0, 56, 49, 255)
            case 'OLY': return (2, 17, 103, 255)
            case 'PBG': return (0, 0, 0, 255)
            case 'PBS': return (15, 135, 1, 255)
            case 'PC': return (123, 46, 42, 255)
            case 'PHA': return (0, 51, 160, 255)
            case 'PHI': return (232, 24, 40, 255)
            case 'PK': return (255, 196, 12, 255)
            case 'PIT': return (253, 184, 39, 255)
            case 'PRO': return (35, 31, 32, 255)
            case 'PS': return (192, 62, 51, 255)
            case 'PTG': return (203, 17, 66, 255)
            case 'RES': return (0, 4, 91, 255)
            case 'RIC': return (250, 138, 49, 255)
            case 'ROC': return (101, 55, 19, 255)
            case 'ROK': return (17, 111, 59, 255)
            case 'SDP': return (249, 182, 1, 255)
            case 'SEA': return (0, 92, 92, 255)
            case 'SEP': return (0, 79, 157, 255)
            case 'SFG': return (253, 90, 30, 255)
            case 'SLB': return (227, 73, 18, 255)
            case 'SLG': return (10, 34, 64, 255)
            case 'SLM': return (5, 14, 55, 255)
            case 'SLR': return (200, 16, 46, 255)
            case 'SL2': return (214, 0, 36, 255)
            case 'SL3': return (214, 0, 36, 255)
            case 'SLS': return (214, 0, 36, 255)
            case 'SNS': return (214, 0, 36, 255)
            case 'STL': return (196, 30, 58, 255)
            case 'STP': return (20, 52, 141, 255)
            case 'TC': return (158, 25, 23, 255)
            case 'TC2': return (158, 25, 23, 255)
            case 'TBD': return (0, 70, 55, 255)
            case 'TBR': return (70, 188, 230, 255)
            case 'TEX': return (192,17,31, 255)
            case 'TOL': return (64, 62, 98, 255)
            case 'TOR': return (19, 74, 142, 255)
            case 'TT': return (189, 47, 45, 255)
            case 'WAP': return (103, 172, 221, 255)
            case 'WAS': return (0, 33, 68, 255)
            case 'WEG': return (0, 4, 42, 255)
            case 'WHS': return (0, 33, 68, 255)
            case 'WIL': return (99, 61, 146, 255)
            case 'WMP': return (228, 0, 23, 255)
            case 'WOR': return (224, 17, 95, 255)
            case 'WP': return (228, 0, 23, 255)
            case 'WSA': return (0, 33, 68, 255)
            case 'WSH': return (0, 33, 68, 255)
            case 'WSN': return (171, 0, 3, 255)
            case _: return (55, 55, 55, 255)

    @property
    def primary_logo_historical(self) -> tuple[int,int,int,int]:
        match self.value:
            case 'ANA': return {
                '1': (186,0,33,255),
            }
            case 'ARI': return {
                '1': (0,96,86,255),
            }
            case 'ATL': return {
                '1': (1, 51, 172, 255),
                '2': (213, 0, 50, 255),
                '3': (213, 0, 50, 255),
            }
            case 'BAL': return {
                '1': (21, 10, 106, 255),
                '2': (243, 105, 22, 255),
                '3': (220, 72, 20, 255),
                '4': (220, 72, 20, 255),
                '5': (220, 72, 20, 255),
                '6': (220, 72, 20, 255),
                '7': (220, 72, 20, 255),
            }
            case 'BOS': return {
                '1': (189, 48, 57, 255),
                '2': (189, 48, 57, 255),
                '3': (189, 48, 57, 255),
                '4': (189, 48, 57, 255),
            }
            case 'CHC': return {
                '1': (12, 35, 64, 255),
                '2': (14, 51, 134, 255),
                '3': (14, 51, 134, 255),
                '4': (14, 51, 134, 255),
                '5': (14, 51, 134, 255),
            }
            case 'CHW': return {
                '1': (0, 38, 99, 255),
                '2': (0, 38, 99, 255),
                '3': (0, 38, 99, 255),
                '4': (0, 38, 99, 255),
            }
            case 'CIN': return {
                '1': (198,1,31,255),
                '2': (198,1,31,255),
                '3': (198,1,31,255),
                '4': (198,1,31,255),
            }
            case 'CLE': return {
                '1': (0,33,68,255),
                '2': (215,0,44,255),
                '3': (215,0,44,255),
                '4': (215,0,44,255),
                '5': (215,0,44,255),
                '6': (237,23,79,255),
            }
            case 'DET': return {
                '1': (0,33,68,255),
                '2': (0,33,68,255),
                '3': (0,33,68,255),
            }
            case 'HOU': return {
                '1': (255, 72, 25, 255),
                '2': (114, 116, 74, 255),
                '3': (157, 48, 34, 255),
            }
            case 'KCR': return {
                '1': (0, 70, 135, 255),
                '2': (0, 70, 135, 255),
                '3': (0, 70, 135, 255),
            }
            case 'MIA': return {
                '1': (255, 102, 0, 255),
            }
            case 'MIL': return {
                '1': (18, 40, 75, 255),
                '2': (0, 70, 174, 255),
                '3': (141, 116, 74, 255),
                '4': (18, 40, 75, 255),
            }
            case 'MIN': return {
                '1': (190, 15, 52, 255),
                '2': (190, 15, 52, 255),
            }
            case 'NYM': return {
                '1': (252, 89, 16, 255),
                '2': (252, 89, 16, 255),
                '3': (252, 89, 16, 255),
            }
            case 'NYY': return {
                '1': (12, 35, 64, 255),
            }
            case 'OAK': return {
                '1': (0, 56, 49, 255),
                '2': (0, 56, 49, 255),
            }
            case 'PHI': return {
                '1': (232, 24, 40, 255),
                '2': (232, 24, 40, 255),
                '3': (232, 24, 40, 255),
                '4': (232, 24, 40, 255),
            }
            case 'PIT': return {
                '1': (253, 184, 39, 255),
                '2': (253, 184, 39, 255),
                '3': (253, 184, 39, 255),
            }
            case 'SDP': return {
                '1': (97, 55, 30, 255),
                '2': (70, 36, 37, 255),
                '3': (10, 35, 67, 255),
                '4': (183, 166, 109, 255),
            }
            case 'SEA': return {
                '1': (0, 40, 120, 255),
                '2': (0, 40, 120, 255),
                '3': (0, 40, 120, 255),
            }
            case 'SFG': return {
                '1': (253, 90, 30, 255),
                '2': (253, 90, 30, 255),
                '3': (253, 90, 30, 255),
            }
            case 'STL': return {
                '1': (196, 30, 58, 255),
                '2': (196, 30, 58, 255),
                '3': (196, 30, 58, 255),
            }
            case 'TBD': return {
                '1': (17, 141, 196, 255),
            }
            case 'TEX': return {
                '1': (235, 0, 44, 255),
                '2': (235, 0, 44, 255),
                '3': (192, 17, 31, 255),
            }
            case 'TOR': return {
                '1': (0, 107, 166, 255),
                '2': (0, 107, 166, 255),
                '3': (0, 75, 135, 255),
            }
            case 'WSN': return {
                '1': (171,0,3,255),
            }
            case _: return {}

    def primary_color_for_year(self, year:int) -> tuple[int,int,int,int]:
        logo_historical_index = self.logo_historical_index(year)
        primary_color_historical = self.primary_logo_historical.get(logo_historical_index, None)
        return primary_color_historical if primary_color_historical else self.primary_color


# ------------------------------------------------------------------------
# LOGO
# ------------------------------------------------------------------------

    @property
    def logo_historical_year_range_dict(self) -> dict[str, list[int]]:
        match self.value:
            case 'ANA': return {
                '1': list(range(2002, 2005)),
            }
            case 'ARI': return {
                '1': list(range(1998,2007))
            }
            case 'ATL': return {
                '1': list(range(1966,1972)),
                '2': list(range(1972,1981)),
                '3': list(range(1981,1987)),
            }
            case 'BAL': return {
                '1': list(range(1872,1900)),
                '2': list(range(1914,1916)),
                '3': list(range(1954,1966)),
                '4': list(range(1966,1992)),
                '5': list(range(1992,1995)),
                '6': list(range(1995,2009)),
                '7': list(range(2009,2019)),
            }
            case 'BOS': return {
                '1': list(range(1871,1901)),
                '2': list(range(1901,1924)),
                '3': list(range(1924,1961)),
                '4': list(range(1961,1976)),
            }
            case 'CHC': return {
                '1': list(range(1876,1919)),
                '2': list(range(1919,1946)),
                '3': list(range(1946,1957)),
                '4': list(range(1957,1979)),
                '5': list(range(1979,1997)),
            }
            case 'CHW': return {
                '1': list(range(1901,1939)),
                '2': list(range(1939,1960)),
                '3': list(range(1960,1976)),
                '4': list(range(1976,1991)),
            }
            case 'CIN': return {
                '1': list(range(1876,1953)),
                '2': list(range(1953,1968)),
                '3': list(range(1968,1993)),
                '4': list(range(1993,1999)),
            }
            case 'CLE': return {
                '1': list(range(1871,1921)),
                '2': list(range(1921,1946)),
                '3': list(range(1946,1973)),
                '4': list(range(1973,1979)),
                '5': list(range(1979,2013)),
                '6': list(range(2013,2022)),
            }
            case 'DET': return {
                '1': list(range(1901,1957)),
                '2': list(range(1957,1994)),
                '3': list(range(1994,2005)),
            }
            case 'HOU': return {
                '1': list(range(1965,1994)),
                '2': list(range(1994,2000)),
                '3': list(range(2000,2013)),
            }
            case 'KCR': return {
                '1': list(range(1969,1986)),
                '2': list(range(1986,1993)),
                '3': list(range(1993,2002)),
            }
            case 'MIA': return {
                '1': list(range(2012,2019)),
            }
            case 'MIL': return {
                '1': list(range(1970,1978)),
                '2': list(range(1978,1994)),
                '3': list(range(1994,2000)),
                '4': list(range(2000,2018)),
            }
            case 'MIN': return {
                '1': list(range(1961,1987)),
                '2': list(range(1987,2009)),
            }
            case 'NYM': return {
                '1': list(range(1962,1993)),
                '2': list(range(1993,1998)),
                '3': list(range(1998,2011)),
            }
            case 'NYY': return {
                '1': list(range(1900,1950)),
            }
            case 'OAK': return {
                '1': list(range(1968,1982)),
                '2': list(range(1982,1993)),
            }
            case 'PHI': return {
                '1': list(range(1900,1950)),
                '2': list(range(1950,1970)),
                '3': list(range(1970,1992)),
                '4': list(range(1992,2019)),
            }
            case 'PIT': return {
                '1': list(range(1900,1948)),
                '2': list(range(1948,1970)),
                '3': list(range(1970,2009)),
            }
            case 'SDP': return {
                '1': list(range(1969,1985)),
                '2': list(range(1985,1992)),
                '3': list(range(1992,2004)),
                '4': list(range(2004,2012)),
            }
            case 'SEA': return {
                '1': list(range(1977,1981)),
                '2': list(range(1981,1987)),
                '3': list(range(1987,1993)),
            }
            case 'SFG': return {
                '1': list(range(1968,1983)),
                '2': list(range(1983,1994)),
                '3': list(range(1994,2000)),
            }
            case 'STL': return {
                '1': list(range(1875,1927)),
                '2': list(range(1927,1965)),
                '3': list(range(1965,1998)),
            }
            case 'TBD': return {
                '1': list(range(1998,2001)),
            }
            case 'TEX': return {
                '1': list(range(1972,1982)),
                '2': list(range(1982,1994)),
                '3': list(range(1994,2003)),
            }
            case 'TOR': return {
                '1': list(range(1977,1997)),
                '2': list(range(1997,2003)),
                '3': list(range(2003,2012)),
            }
            case 'WSN': return {
                '1': list(range(2005,2011)),
            }
            case _: return {}

    def logo_historical_index(self, year:int, include_dash:bool = False) -> str:

        for index, year_range in self.logo_historical_year_range_dict.items():
            if year in year_range:
                prefix = '-' if include_dash else ''
                return f"{prefix}{index}"
        
        return ''
    
    def logo_name(self, year:int, is_alternate:bool=False) -> str:
        alt_ext = '-A' if is_alternate else ''
        return f"{self.value}{alt_ext}{self.logo_historical_index(year=year, include_dash=True)}"

# ------------------------------------------------------------------------
# TEAM BACKGROUND (00/01)
# ------------------------------------------------------------------------

    @property
    def use_alternate_for_2000_background(self) -> bool:
        return self.value in [
            'ATL'
        ]

    def is_background_logo_wide(self, year:int, is_alternate:bool=False) -> bool:
        logo_name = self.logo_name(year=year, is_alternate=is_alternate)
        return logo_name in [
            'ATL','BAL-5','BAL-A-7','BOS-2','BOS-A-2','BRO','CHC-1','CHC-A-1','CHW-2','CHW-A-2',
            'CIN-1','CIN-3','CIN-4','CIN-A-1','CIN-A-3','CIN-A-4','CIN-A','CIN','CRS-A','CRS','IA-A','IA',
            'IC-A','IC','LOU-A','LOU','MIL-4','MLA-A','MLA','MLB','SDP-2','SDP-A-2','SEP-A','SEP',
            'SFG-2','SFG-3','SFG','STL-2','TBD-1','TBD','TBD-A-1','TBD-A','TOR-3','TOR-A-3'
        ]

    def background_logo_opacity(self, set:str) -> float:
        return 0.20 if set == '2001' else 0.19
    
    def background_logo_rotation(self, set:str) -> int:
        return 18 if set == '2001' else 0
    
    def background_logo_size(self, year:int, set:str, is_alternate:bool=False) -> tuple[int,int]:
        logo_name = self.logo_name(year=year, is_alternate=is_alternate)
        match set:
            case '2000': 
                match logo_name:
                    case 'ATL-A': return (1950, 1950)
                    case _: return (2600, 2600) if self.is_background_logo_wide(year=year,is_alternate=is_alternate) else (2200, 2200)
            case '2001': 
                match logo_name:
                    case 'ATL': return (1000, 1000)
                    case _: return (735, 735)
            case _: return (750, 750)

    def background_image_paste_adjustment(self, year:int, set:str, is_alternate:bool=False) -> tuple[int,int]:
        logo_name = self.logo_name(year=year, is_alternate=is_alternate)
        match set:
            case '2000': 
                match logo_name:
                    case 'ATL-A': return (-100,0)
                    case _: return (0,0)
            case '2001': 
                match logo_name:
                    case 'ATL': return (-90,-250)
                    case _: return (0,0)
            case _: return (0, 0) 

    def background_logo_paste_location(self, year:int, is_alternate:bool, set:str, image_size:tuple[int,int]) -> tuple[int,int]:
        image_width, image_height = image_size
        logo_width, logo_height = self.background_logo_size(year=year, set=set, is_alternate=is_alternate)
        x_adjustment, y_adjustment = self.background_image_paste_adjustment(year=year, set=set, is_alternate=is_alternate)
        x_standard, y_standard = (50, 25) if set == '2001' else ( int( (image_width - logo_width) / 2 ), int( (image_height - logo_height) / 2 ) )
        return (x_standard + x_adjustment, y_standard + y_adjustment)