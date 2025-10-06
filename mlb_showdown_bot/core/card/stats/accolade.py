from enum import Enum

class Accolade(Enum):

    # COUNTING STATS
    HITS = 'H'
    DOUBLES = '2B'
    TRIPLES = '3B'
    HR = 'HR'
    WALKS = 'BB'
    RUNS = 'R'
    RBI = 'RBI'
    SB = 'SB'
    SO = 'SO_p'
    WINS = 'W'
    SHUTOUTS = 'SHO'
    IP = 'IP'
    CG = 'CG'
    SAVES = 'SV'
    TOTAL_BASES = 'TB'

    # RATE STATS
    BA = 'batting_avg'
    OBP = 'onbase_perc'
    SLG = 'slugging_perc'
    OPS = 'onbase_plus_slugging'
    WHIP = 'whip'
    WIN_LOSS_PERC = 'win_loss_perc'
    SO9 = 'strikeouts_per_nine'
    ERA = 'earned_run_avg'

    # ADVANCED STATS
    OPS_PLUS = 'onbase_plus_slugging_plus'
    WAR = 'WAR'
    FIP = 'fip'
    ERA_PLUS = 'earned_run_avg_plus'

    # AWARDS
    ALL_STAR = 'allstar'
    AWARDS = 'awards'
    SILVER_SLUGGER = 'silver_sluggers'
    GOLD_GLOVE = 'gold_gloves'
    MVP = 'mvp'
    CY_YOUNG = 'cyyoung'

    @property 
    def value_type(self) -> str:
        match self.name:
            case "MVP" | "CY_YOUNG": return "AWARD (PLACEMENT, PCT)"
            case "SILVER_SLUGGER" | "ALL_STAR" | "GOLD_GLOVE" : return "AWARD (NO VOTING)"
            case "AWARDS": return "AWARDS (LIST)"
            case _: return "ORDINAL"

    @property
    def awards_to_keep(self) -> list[str]:
        """Defines which award substrings to keep when looking at the AWARDS element"""
        return ["CY YOUNG", "NL MVP", "AL MVP", "ROOKIE OF THE YEAR", ]
    
    @property
    def title(self) -> str:
        """Cleaned up name for use in super season accolades"""
        match self.name:
            case "DOUBLES" | "TRIPLES": return self.value
            case "SO9": return "SO/9"
            case "WIN_LOSS_PERC": return "W/L%"
            case _: return self.name.replace('_PLUS','+').replace('_',' ')
    
    @property
    def rank_list(self) -> list[str]:
        return [
           "AWARDS","GOLD_GLOVE","SILVER_SLUGGER","CY_YOUNG","MVP",
           "HR","BA","OBP","SLG","OPS","DOUBLES","TRIPLES","RBI","SB","WALKS","HITS","RUNS","TOTAL_BASES",
           "ERA","SAVES","SO","WHIP","WINS","IP","OPS_PLUS","ERA_PLUS","WAR",
           "SHUTOUTS","CG","WIN_LOSS_PERC","SO9","FIP",
           "ALL_STAR",
        ]
    
    @property
    def priority_multiplier(self) -> float:
        match self.name:
            case "OPS_PLUS" | "FIP" | "ERA_PLUS": return 3.0
            case "MVP" | "CY_YOUNG": return 0.5
            case _: return 1.0
    
    @property
    def is_pitcher_exclusive(self) -> bool:
        return self.name in ["CY_YOUNG","ERA","SAVES","SO","WHIP","WINS","IP","ERA_PLUS","SHUTOUTS","CG","WIN_LOSS_PERC","SO9","FIP",]
    
    @property
    def is_hitter_exclusive(self) -> bool:
        return self.name in ["SILVER_SLUGGER","GOLD_GLOVE","HR","BA","OBP","SLG","OPS","DOUBLES","TRIPLES","RBI","SB","WALKS","HITS","RUNS","TOTAL_BASES","OPS_PLUS",]

    @property 
    def rank(self) -> int:
        return self.rank_list.index(self.name) + 1
