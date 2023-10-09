from enum import Enum

class Team(Enum):

    AB2 = 'AB2'
    AB3 = 'AB3'
    ABC = 'ABC'
    AC = 'AC'
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
    CG = 'CG'
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
    DM = 'DM'
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
    MLN = 'MLN'
    MON = 'MON'
    MRS = 'MRS'
    MRM = 'MRM'
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
            case 'CG': return (249, 106, 0, 255)
            case 'CHC': return (14, 51, 134, 255)
            case 'CHI': return (1, 31, 105, 255)
            case 'CHT': return (14, 0, 119, 255)
            case 'CHW': return (39, 37, 31, 255)
            case 'CIN': return (198, 1, 31, 255)
            case 'CLE': return (229, 0, 34, 255)
            case 'CKK': return (209, 9, 47, 255)
            case 'CLV': return (14, 0, 119, 255)
            case 'COL': return (51, 51, 102, 255)
            case 'COR': return (198,1,31,255)
            case 'CRS': return (14, 0, 119, 255)
            case 'CSE': return (10, 34, 64, 255)
            case 'CS': return (10, 34, 64, 255)
            case 'CSW': return (10, 34, 64, 255)
            case 'CT': return (198,1,31,255)
            case 'CTG': return (198,1,31,255)
            case 'DET': return (12, 35, 64, 255)
            case 'DM': return (252, 209, 22, 255)
            case 'DS': return (193, 44, 56, 255)
            case 'DTS': return (193, 44, 56, 255)
            case 'DW': return (189, 47, 45, 255)
            case 'FLA': return (0, 156, 166, 255)
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
            case 'MLN': return (0, 33, 68, 255)
            case 'MON': return (0, 48, 135, 255)
            case 'MRM': return (189, 47, 45, 255)
            case 'MRS': return (181, 0, 51, 255)
            case 'NE': return (12, 35, 64, 255)
            case 'NBY': return (25, 37, 62, 255)
            case 'NEG': return (0, 4, 42, 255)
            case 'NLG': return (17, 36, 55, 255)
            case 'NYC': return (162, 0, 45, 255)
            case 'NYG': return (227, 82, 5, 255)
            case 'NYM': return (0, 45, 114, 255)
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
            case 'SDP': return (47, 36, 29, 255)
            case 'SEA': return (12, 44, 86, 255)
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
            case 'TBD': return (0, 43, 115, 255)
            case 'TBR': return (9, 44, 92, 255)
            case 'TEX': return (192, 17, 31, 255)
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
    def primary_color_historical(self) -> tuple[int,int,int,int]:
        match self.value:
            case 'ANA': return {
                '1': (186,0,33,255),
            }
            case 'ARI': return {
                '1': (95, 37, 159, 255),
            }
            case 'ATL': return {
                '1': (24, 48, 135, 255),
                '2': (213, 0, 50, 255),
                '3': (213, 0, 50, 255),
            }
            case 'BAL': return {
                '1': (21, 10, 106, 255),
                '2': (243, 105, 22, 255),
                '3': (220, 72, 20, 255),
                '4': (252, 76, 2, 255),
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
                '1': (176,36,54,255),
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
                '6': (226,29,56,255),
            }
            case 'DET': return {
                '1': (0,33,68,255),
                '2': (0,33,68,255),
                '3': (0,33,68,255),
            }
            case 'HOU': return {
                '1': (250, 70, 22, 255),
                '2': (4, 30, 66, 255),
                '3': (12, 35, 64, 255),
                '4': (154, 51, 36, 255),
            }
            case 'KCR': return {
                '1': (0, 70, 135, 255),
                '2': (0, 70, 135, 255),
                '3': (0, 70, 135, 255),
            }
            case 'LAA': return {
                '1': (191, 13, 62, 255),
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
                '2': (186, 12, 47, 255),
            }
            case 'NYM': return {
                '1': self.primary_color,
                '2': self.primary_color,
                '3': self.primary_color,
            }
            case 'NYY': return {
                '1': (12, 35, 64, 255),
            }
            case 'OAK': return {
                '1': (17, 87, 64, 255),
                '2': (17, 87, 64, 255),
            }
            case 'PHI': return {
                '1': (232, 24, 40, 255),
                '2': (232, 24, 40, 255),
                '3': (111, 38, 61, 255),
                '4': (232, 24, 40, 255),
            }
            case 'PIT': return {
                '1': (255, 199, 44, 255),
                '2': (255, 199, 44, 255),
                '3': (255, 199, 44, 255),
            }
            case 'SDP': return {
                '1': (105, 63, 34, 255),
                '2': (70, 36, 37, 255),
                '3': (4, 30, 66, 255),
                '4': (0, 45, 98, 255),
                '5': (0, 45, 98, 255),
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
                '1': (32, 54, 168, 255),
                '2': (32, 54, 168, 255),
                '3': (186, 12, 47, 255),
            }
            case 'TOR': return {
                '1': (0, 107, 166, 255),
                '2': (0, 47, 108, 255),
                '3': (0, 75, 135, 255),
            }
            case 'WSN': return {
                '1': (171,0,3,255),
            }
            case _: return {}

    @property
    def secondary_color(self) -> tuple[int,int,int,int]:
        match self.value:
            case 'ANA': return (92, 136, 218, 255)
            case 'ARI': return (227, 212, 173, 255)
            case 'ATL': return (19, 39, 79, 255)
            case 'BAL': return (39, 37, 31, 255)
            case 'BOS': return (12, 35, 64, 255)
            case 'BRO': return (191, 192, 191, 255)
            case 'CAL': return (4, 28, 44, 255)
            case 'CCC': return (13, 30, 66, 255)
            case 'CHC': return (204, 52, 51, 255)
            case 'CHW': return (196, 206, 212, 255)
            case 'CIN': return (25, 25, 25, 255)
            case 'CLE': return (0, 56, 93, 255)
            case 'COL': return (196, 206, 212, 255)
            case 'DET': return (250, 70, 22, 255)
            case 'FLA': return (250, 70, 22, 255)
            case 'HOU': return (0, 45, 98, 255)
            case 'KCA': return (255, 204, 0, 255)
            case 'KCR': return (189, 155, 96, 255)
            case 'LAA': return (0, 50, 99, 255)
            case 'LAD': return (239, 62, 66, 255)
            case 'MIA': return (0, 0, 0, 255)
            case 'MIL': return (255, 197, 47, 255)
            case 'MIN': return (0, 43, 92, 255)
            case 'MLN': return (204, 9, 47, 255)
            case 'MON': return (228, 0, 43, 255)
            case 'NYG': return (45, 45, 45, 255)
            case 'NYM': return (252, 89, 16, 255)
            case 'NYY': return (196, 206, 211, 255)
            case 'OAK': return (239, 178, 30, 255)
            case 'PHI': return (0, 45, 114, 255)
            case 'PIT': return (39, 37, 31, 255)
            case 'SDP': return (255, 196, 37, 255)
            case 'SEA': return (0, 92, 92, 255)
            case 'SFG': return (39, 37, 31, 255)
            case 'STL': return (12, 35, 64, 255)
            case 'TBD': return (0, 70, 55, 255)
            case 'TBR': return (143, 188, 230, 255)
            case 'TEX': return (0, 50, 120, 255)
            case 'TOR': return (232, 41, 28, 255)
            case 'WSN': return (20, 34, 90, 255)

            # OLD TEAMS
            case 'BBB': return (251, 221, 0, 255)
            case 'BEG' | 'CEG' | 'NEG' | 'WEG': return (176, 0, 0, 255)
            case 'BRG': return (0, 21, 123, 255)
            case 'BSN': return (255, 204, 0, 255)
            case 'CBE' | 'CCB': return (0, 45, 114, 255)
            case 'CEN': return (10, 34, 63, 255)
            case 'DM': return (45, 68, 146, 255)
            case 'HG': return (45, 45, 45, 255)
            case 'KCM': return (16, 0, 55, 255)
            case 'MGS': return (125, 181, 231, 255)
            case 'MRS': return (3, 139, 184, 255)
            case 'NE': return (255, 253, 207, 255)
            case 'NYC': return (0, 21, 60, 255)
            case 'SEP': return (255, 212, 81, 255)
            case 'SL2' | 'SL3': return (15, 52, 167, 255)
            case 'SLB': return (92, 43, 46, 255)
            case 'WAP': return (20, 20, 20, 255)
            case 'WMP' | 'WP': return (10, 33, 63, 255)
            case 'WSH': return (204, 9, 47, 255)

            case _: return self.primary_color
    
    @property
    def secondary_color_historical(self) -> tuple[int,int,int,int]:
        match self.value:
            case 'ANA': return {
                '1': (0,50,99,255),
            }
            case 'ARI': return {
                '1': (0,95,97,255),
            }
            case 'ATL': return {
                '1': (186,22,46,255),
                '2': (0,51,160,255),
                '3': (0,51,160,255),
            }
            case 'CHC': return {
                '1': (12,35,64,255),
            }
            case 'CHW': return {
                '2': (204,9,47,255),
                '3': (204,9,47,255),
                '4': (204,9,47,255),
            }
            case 'CLE': return {
                '6': (26, 46, 90, 255),
            }
            case 'DET': return {
                '1': (240,240,240,255),
                '2': (250,70,22,255),
                '3': (250,70,22,255),
            }
            case 'HOU': return {
                '1': (4, 30, 66, 255),
                '2': (250, 70, 22, 255),
                '3': (137, 115, 75, 255),
                '4': (211, 188, 141, 255),
            }
            case 'KCR': return {
                '1': (192, 154, 91, 255),
                '2': (192, 154, 91, 255),
                '3': (192, 154, 91, 255),
            }
            case 'LAA': return {
                '1': (4, 28, 44, 255),
            }
            case 'MIA': return {
                '1': (0, 119, 200, 255),
            }
            case 'MIL': return {
                '1': (255, 212, 81, 255),
                '2': (255, 212, 81, 255),
                '3': (10, 105, 78, 255),
                '4': (182, 146, 46, 255),
            }
            case 'MIN': return {
                '1': (12, 35, 64, 255),
                '2': (34, 68, 179, 255),
            }
            case 'OAK': return {
                '1': (255, 205, 0, 255),
                '2': (255, 205, 0, 255),
            }
            case 'PHI': return {
                '2': (40, 72, 152, 255),
                '3': (107, 172, 228, 255),
                '4': (40, 72, 152, 255),
            }
            case 'PIT': return {
                '1': (39, 37, 31, 255),
                '2': (39, 37, 31, 255),
                '3': (39, 37, 31, 255),
            }
            case 'SDP': return {
                '1': (255, 205, 5, 255),
                '2': (227, 86, 37, 255),
                '3': (227, 82, 5, 255),
                '4': (162, 170, 173, 255),
                '5': (162, 170, 173, 255),
            }
            case 'SEA': return {
                '1': (255, 204, 0, 255),
                '2': (255, 204, 0, 255),
                '3': (255, 204, 0, 255),
            }
            case 'SFG': return {
                '1': (39, 37, 31, 255),
                '2': (39, 37, 31, 255),
                '3': (39, 37, 31, 255),
            }
            case 'STL': return {
                '1': (12, 35, 64, 255),
                '2': (12, 35, 64, 255),
                '3': (12, 35, 64, 255),
            }
            case 'TBD': return {
                '1': (35, 21, 80, 255),
            }
            case 'TEX': return {
                '1': (235, 31, 43, 255),
                '2': (235, 31, 43, 255),
                '3': (0, 45, 114, 255),
            }
            case 'TOR': return {
                '1': (218, 41, 28, 255),
                '2': (0, 107, 166, 255),
                '3': (24, 75, 135, 255),
            }
            case _: return {}
            
    def color(self, year:int, is_secondary:bool=False) -> tuple[int,int,int,int]:        
        logo_historical_index = self.logo_historical_index(year)
        default_color = self.secondary_color if is_secondary else self.primary_color
        historical_color_map = self.secondary_color_historical if is_secondary else self.primary_color_historical
        color_historical = historical_color_map.get(logo_historical_index, default_color)
        return color_historical

    def use_dark_text(self, year:int, is_secondary:bool) -> bool:
        red, green, blue, _ = self.color(year=year, is_secondary=is_secondary)
        return (red*0.299 + green*0.587 + blue*0.114) > 186
        

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
                '1': list(range(1962,1965)),
                '2': list(range(1965,1994)),
                '3': list(range(1994,2000)),
                '4': list(range(2000,2013)),
            }
            case 'KCR': return {
                '1': list(range(1969,1986)),
                '2': list(range(1986,1993)),
                '3': list(range(1993,2002)),
            }
            case 'LAD': return {
                '1': list(range(1999,2007)),
            }
            case 'LAA': return {
                '1': list(range(1961,1965)),
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
                '3': list(range(1970,1997)),
                '4': list(range(1997,2014)),
            }
            case 'SDP': return {
                '1': list(range(1969,1985)),
                '2': list(range(1985,1992)),
                '3': list(range(1992,2004)),
                '4': list(range(2004,2012)),
                '5': list(range(2012,2020)),
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

    def is_logo_wide(self, year:int, is_alternate:bool=False) -> bool:
        logo_name = self.logo_name(year=year, is_alternate=is_alternate)
        return logo_name in [
            'ANA','ANA-A','ATL','BAL-5','BAL-A-7','BOS-2','BOS-A-2','BRO','CHC-1','CHC-A-1','CHW-2','CHW-A-2',
            'CIN-1','CIN-3','CIN-4','CIN-A-1','CIN-A-3','CIN-A-4','CIN-A','CIN','CRS-A','CRS','IA-A','IA',
            'IC-A','IC','LOU-A','LOU','MIL-4','MLA-A','MLA','MLB','SDP-2','SDP-A-2','SEP-A','SEP',
            'SFG-2','SFG-3','SFG','STL-2','TBD-1','TBD','TBD-A-1','TBD-A','TOR-3','TOR-A-3'
        ]
    
    def logo_size_multiplier(self, year:int, is_alternate:bool=False) -> float:
        is_wide = self.is_logo_wide(year=year, is_alternate=is_alternate)
        if is_wide:
            return 1.25
        
        return 1.0


# ------------------------------------------------------------------------
# TEAM BACKGROUND (00/01)
# ------------------------------------------------------------------------

    def use_alternate_for_background(self, set:str) -> bool:
        match set:
            case '2000':
                return self.value in [
                    'ATL', 'LAD',
                ]
            case '2001':
                return self.value in [
                    'LAD', 'MIA'
                ]
            case _: return False

    def background_logo_opacity(self, set:str) -> float:
        return 0.30 if set == '2001' else 0.19
    
    def background_logo_rotation(self, set:str) -> int:
        return 18 if set == '2001' else 0
    
    def background_logo_size(self, year:int, set:str, is_alternate:bool=False) -> tuple[int,int]:
        logo_name = self.logo_name(year=year, is_alternate=is_alternate)
        match set:
            case '2000': 
                match logo_name:
                    case 'ATL-A' | 'ATL-1' | 'BOS-2': return (1950, 1950)
                    case 'ARI-1': return (2300, 2300)
                    case 'BRO': return (1800, 1800)
                    case 'FLA': return (2300, 2300)
                    case 'MIN-2': return (2400, 2400)
                    case 'NYG': return (1800, 1800)
                    case 'PHI-2': return (1800, 1800)
                    case 'SFG-1': return (1800, 1800)
                    case 'TBD' | 'TBD-1': return (1950, 1950)

                    # OLD TEAMS
                    case 'CRS' | 'IA' | 'LOU' | 'MLA': return (1800, 1800)
                    case 'MLN': return (1900, 1900)

                    case _: return (2600, 2600) if self.is_logo_wide(year=year,is_alternate=is_alternate) else (2200, 2200)
            case '2001': 
                match logo_name:
                    case 'ANA': return (1000, 1000)
                    case 'ANA-1': return (775, 775)
                    case 'ATL': return (1000, 1000)
                    case 'ARI-1': return (1000, 1000)
                    case 'BAL-5' | 'BAL-6' | 'BAL-7': return (775, 775)
                    case 'BOS-2': return (1000, 1000)
                    case 'BRO': return (950, 950)
                    case 'CHC-1': return (850, 850)
                    case 'CHW': return (775, 775)
                    case 'CHW-2': return (950, 950)
                    case 'CIN' | 'CIN-1' | 'CIN-3' | 'CIN-4': return (900, 900)
                    case 'CIN-2': return (775, 775)
                    case 'CLE': return (850, 850)
                    case 'CLE-3' | 'CLE-5': return (900, 900)
                    case 'COL': return (900, 900)
                    case 'DET-3': return (825, 825)
                    case 'FLA' : return (850, 850)
                    case 'HOU-1' : return (1000, 1000)
                    case 'HOU-4' : return (950, 950)
                    case 'KCA' : return (800, 800)
                    case 'KCR' | 'KCR-1' | 'KCR-2' | 'KCR-3' : return (850, 850)
                    case 'LAA': return (775, 775)
                    case 'LAD-A' | 'LAD-A-1': return (800, 800)
                    case 'MIL-3': return (800, 800)
                    case 'MIL-4': return (950, 950)
                    case 'MIN-2': return (875, 875)
                    case 'NYG': return (850, 850)
                    case 'PHI-2': return (950, 950)
                    case 'PHI' | 'PHI-4': return (800, 800)
                    case 'PIT-1': return (775, 775)
                    case 'PIT-4': return (875, 875)
                    case 'PIT' | 'PIT-2' | 'PIT-3': return (775, 775)
                    case 'SDP-1': return (950, 950)
                    case 'SDP-2' | 'SDP-3' | 'SDP-4': return (850, 850)
                    case 'SEA-2': return (850, 850)
                    case 'SFG-1': return (850, 850)
                    case 'SFG-2': return (850, 850)
                    case 'SFG' | 'SFG-3': return (950, 950)
                    case 'STL' | 'STL-2': return (850, 850)
                    case 'TBD' | 'TBD-1': return (1000, 1000)
                    case 'TBR': return (800, 800)
                    case 'TEX-1': return (900, 900)
                    case 'TEX-2' | 'TEX-3': return (800, 800)
                    case 'TOR-3': return (1000, 1000)
                    case 'WSN-1': return (825, 825)

                    # OLD TEAMS
                    case 'CC' | 'CCU' | 'COR' | 'IC' | 'PS': return (900, 900)
                    case 'CRS': return (1000, 1000)
                    case 'DW' | 'MRM' | 'TT': return (825, 825) # GENERIC NEGRO LEAGUES
                    case 'IA': return (1000, 1000)
                    case 'LOU': return (1000, 1000)
                    case 'MLA': return (1000, 1000)
                    case 'MLB': return (950, 950)
                    case 'MLN': return (900, 900)
                    case 'SEP': return (1000, 1000)
                    case 'TC' | 'TC2': return (900, 900)
                    case 'WAP': return (900, 900)

                    case _: return (735, 735)
            case _: return (750, 750)

    def background_image_paste_adjustment(self, year:int, set:str, is_alternate:bool=False) -> tuple[int,int]:
        logo_name = self.logo_name(year=year, is_alternate=is_alternate)
        match set:
            case '2000': 
                match logo_name:
                    case 'ANA': return (-100, 0)
                    case 'ARI': return (-100, 0)
                    case 'ARI-1': return (-50, 0)
                    case 'ATL-A' | 'ATL-1': return (-100,0)
                    case 'CHC-1': return (-50, 0)
                    case 'CHW-2': return (250, 0)
                    case 'CLE-3' | 'CLE-5': return (0, -75)
                    case 'COL': return (0, -50)
                    case 'FLA': return (0, 150)
                    case 'KCR' | 'KCR-1' | 'KCR-2' | 'KCR-3' : return (50, 0)
                    case 'MIA-1': return (0, -100)
                    case 'PIT-4': return (0, -60)
                    case 'TBD' | 'TBD-1': return (-150, 0)

                    # OLD TEAMS
                    case 'MLN': return (-175, 0)

                    case _: return (0,0)
            case '2001': 
                match logo_name:
                    case 'ANA': return (-175,-170)
                    case 'ANA-1': return (-60, -50)
                    case 'ARI': return (-75, 0)
                    case 'ARI-1': return (-180, -130)
                    case 'ATL': return (-90,-250)
                    case 'ATL-1': return (-100,0)
                    case 'ATL-3': return (-75,0)
                    case 'BAL-5' | 'BAL-6' | 'BAL-7': return (-60, -50)
                    case 'BOS-2': return (-90,-250)
                    case 'BOS-3': return (-20, 0)
                    case 'BRO': return (-90,-220)
                    case 'CHC-1': return (-60,-125)
                    case 'CHW': return (-60, -50)
                    case 'CHW-1': return (-60,-50)
                    case 'CHW-2': return (-90,-220)
                    case 'CHW-4': return (-25,0)
                    case 'CIN' | 'CIN-1' | 'CIN-3' | 'CIN-4': return (-120,-170)
                    case 'CIN-2': return (-60, -50)
                    case 'CLE': return (-125, -100)
                    case 'CLE-3' | 'CLE-5': return (-175, -220)
                    case 'CLE-6': return (-40, 0)
                    case 'COL': return (-100, -175)
                    case 'DET-3': return (-120, -100)
                    case 'DET' : return (-80, -60)
                    case 'FLA' : return (-60, -30)
                    case 'HOU-1' : return (-90, -230)
                    case 'HOU-3' : return (-60, -15)
                    case 'HOU-4' : return (-130, -160)
                    case 'KCA' : return (-30, -90)
                    case 'KCR' | 'KCR-1' | 'KCR-2' | 'KCR-3' : return (-100, -100)
                    case 'LAA' | 'LAA-1': return (-60, -50)
                    case 'LAD-A' | 'LAD-A-1': return (-40, -60)
                    case 'MIA-A': return (-40, -75)
                    case 'MIA-A-1': return (-40, -100)
                    case 'MIL': return (-20, 0)
                    case 'MIL-3': return (-50, -40)
                    case 'MIL-4': return (-100, -240)
                    case 'MIN-1': return (-40, -40)
                    case 'MIN-2': return (-85, -85)
                    case 'NYG': return (-85, -50)
                    case 'PHI-2': return (-125, -180)
                    case 'PHI-3': return (-40, 0)
                    case 'PHI' | 'PHI-4': return (-40, -50)
                    case 'PIT-1': return (-40, -40)
                    case 'PIT-4': return (-60, -75)
                    case 'PIT' | 'PIT-2' | 'PIT-3': return (-30, -30)
                    case 'SDP-1': return (-40, -190)
                    case 'SDP-2' | 'SDP-3' | 'SDP-4': return (-50, -90)
                    case 'SEA-2': return (-80, -125)
                    case 'SFG-1': return (-85, -50)
                    case 'SFG-2': return (-40, -80)
                    case 'SFG' | 'SFG-3': return (-65, -190)
                    case 'STL' | 'STL-2': return (-95, -120)
                    case 'TBD' | 'TBD-1': return (-160, -190)
                    case 'TBR': return (-50, -60)
                    case 'TEX-2' | 'TEX-3': return (-50, -60)
                    case 'TEX-1': return (-80, -120)
                    case 'TOR-2': return (-30, -50)
                    case 'TOR-3': return (-130, -200)
                    case 'WSN-1': return (-30, -80)

                    # OLD TEAMS
                    case 'BLU' | 'DS' | 'DTS': return (-20, -50)
                    case 'CC' | 'CCU' | 'COR' | 'IC' | 'PS': return (-120, -170)
                    case 'CRS': return (-90, -250)
                    case 'DW' | 'MRM' | 'TT': return (-100, -75) # GENERIC NEGRO LEAGUES
                    case 'HIL': return (-50, 0)
                    case 'IA': return (-90, -250)
                    case 'KCC' | 'KCM' | 'KCN': return (0, -90)
                    case 'LOU': return (-90, -250)
                    case 'LOW' | 'LVB': return (-165, 0)
                    case 'MLA': return (-90, -250)
                    case 'MLB': return (-70, -200)
                    case 'MLN': return (-160, -100)
                    case 'PBG': return (0, -50)
                    case 'PBS': return (-60, -50)
                    case 'PHA': return (-60, -50)
                    case 'PRO': return (-60, 0)
                    case 'SEP': return (-120, -220)
                    case 'SL2' | 'SL3': return (-30, -60)
                    case 'SLB': return (-20, -50)
                    case 'TC' | 'TC2': return (-120, -170)
                    case 'WAP': return (-120, -170)

                    case _: return (0,0)
            case _: return (0, 0) 

    def background_logo_paste_location(self, year:int, is_alternate:bool, set:str, image_size:tuple[int,int]) -> tuple[int,int]:
        image_width, image_height = image_size
        logo_width, logo_height = self.background_logo_size(year=year, set=set, is_alternate=is_alternate)
        x_adjustment, y_adjustment = self.background_image_paste_adjustment(year=year, set=set, is_alternate=is_alternate)
        x_standard, y_standard = (-40, -70) if set == '2001' else ( int( (image_width - logo_width) / 2 ), int( (image_height - logo_height) / 2 ) )
        return (x_standard + x_adjustment, y_standard + y_adjustment)