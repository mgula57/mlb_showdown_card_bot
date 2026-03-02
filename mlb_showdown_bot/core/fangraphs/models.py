from pydantic import BaseModel, Field, field_validator
from typing import Optional

class FieldingStats(BaseModel):
    """Fielding statistics from FanGraphs"""
    
    # Player attributes
    player_name: str = Field(alias="PlayerName")
    name: str = Field(alias="Name")  # Raw name with HTML tags
    team: str = Field(alias="Team")  # Raw team with HTML tags  
    position: str = Field(alias="Pos")
    player_id: int = Field(alias="playerid")
    mlb_stats_id: Optional[int] = Field(None, alias="xMLBAMID")
    season: int = Field(alias="Season")
    
    # Key game information
    games: float = Field(alias="G")
    games_started: float = Field(alias="GS") 
    innings: float = Field(alias="Inn")
    
    # Advanced defensive metrics (your key stats)
    drs: Optional[float] = Field(None, alias="DRS")  # Defensive Runs Saved
    oaa: Optional[float] = Field(None, alias="OAA")  # Outs Above Average
    uzr: Optional[float] = Field(None, alias="UZR")  # Ultimate Zone Rating
    uzr_150: Optional[float] = Field(None, alias="UZR/150")  # UZR per 150 games
    tz: Optional[float] = Field(None, alias="TZ")    # Total Zone (TZR equivalent)
    
    # Basic fielding stats
    fielding_percentage: Optional[float] = Field(None, alias="FP")
    errors: Optional[float] = Field(None, alias="E")
    

class LeaderboardStats(BaseModel):
    """General model for leaderboard stats from FanGraphs, which can be extended for specific stat types (e.g. hitting, pitching)"""
    # Player attributes
    player_name: str = Field(alias="PlayerName")
    name: Optional[str] = Field(None, alias="Name")
    team: str = Field(alias="Team")
    season: int = Field(alias="Season")
    age: Optional[int] = Field(None, alias="Age")
    playerids: str = Field(alias="playerids")
    minormasterid: Optional[str] = Field(None, alias="minormasterid")
    teamid: Optional[int] = Field(None, alias="teamid")
    j_name: Optional[str] = Field(None, alias="JName")
    k_name: Optional[str] = Field(None, alias="KName")

    # Shared counting stats
    g: Optional[int] = Field(None, alias="G")
    h: Optional[int] = Field(None, alias="H")
    r: Optional[int] = Field(None, alias="R")
    bb: Optional[int] = Field(None, alias="BB")
    hr: Optional[int] = Field(None, alias="HR")
    so: Optional[int] = Field(None, alias="SO")
    hbp: Optional[int] = Field(None, alias="HBP")
    ibb: Optional[int] = Field(None, alias="IBB")
    avg: Optional[float] = Field(None, alias="AVG")
    babip: Optional[float] = Field(None, alias="BABIP")
    bb_pct: Optional[float] = Field(None, alias="BB%")
    k_pct: Optional[float] = Field(None, alias="K%")

    # Hitting fields
    ab: Optional[int] = Field(None, alias="AB")
    pa: Optional[int] = Field(None, alias="PA")
    singles: Optional[int] = Field(None, alias="1B")
    doubles: Optional[int] = Field(None, alias="2B")
    triples: Optional[int] = Field(None, alias="3B")
    cs: Optional[int] = Field(None, alias="CS")
    sb: Optional[int] = Field(None, alias="SB")
    sf: Optional[int] = Field(None, alias="SF")
    sh: Optional[int] = Field(None, alias="SH")
    gdp: Optional[int] = Field(None, alias="GDP")
    rbi: Optional[int] = Field(None, alias="RBI")
    obp: Optional[float] = Field(None, alias="OBP")
    slg: Optional[float] = Field(None, alias="SLG")
    ops: Optional[float] = Field(None, alias="OPS")
    iso: Optional[float] = Field(None, alias="ISO")
    spd: Optional[float] = Field(None, alias="Spd")
    wrc: Optional[float] = Field(None, alias="wRC")
    wraa: Optional[float] = Field(None, alias="wRAA")
    woba: Optional[float] = Field(None, alias="wOBA")
    wrc_plus: Optional[float] = Field(None, alias="wRC+")
    wbsr: Optional[float] = Field(None, alias="wBsR")
    bb_per_k: Optional[float] = Field(None, alias="BB/K")

    # Pitching fields
    w: Optional[float] = Field(None, alias="W")
    l: Optional[float] = Field(None, alias="L")
    gs: Optional[float] = Field(None, alias="GS")
    ip: Optional[float] = Field(None, alias="IP")
    er: Optional[float] = Field(None, alias="ER")
    sv: Optional[float] = Field(None, alias="SV")
    bs: Optional[float] = Field(None, alias="BS")
    hld: Optional[float] = Field(None, alias="HLD")
    bk: Optional[float] = Field(None, alias="BK")
    cg: Optional[float] = Field(None, alias="CG")
    sho: Optional[float] = Field(None, alias="ShO")
    wp: Optional[float] = Field(None, alias="WP")
    tbf: Optional[float] = Field(None, alias="TBF")
    pitches: Optional[float] = Field(None, alias="Pitches")
    era: Optional[float] = Field(None, alias="ERA")
    fip: Optional[float] = Field(None, alias="FIP")
    ef: Optional[float] = Field(None, alias="E-F")
    whip: Optional[float] = Field(None, alias="WHIP")
    lob_pct: Optional[float] = Field(None, alias="LOB%")
    k_per_9: Optional[float] = Field(None, alias="K/9")
    bb_per_9: Optional[float] = Field(None, alias="BB/9")
    hr_per_9: Optional[float] = Field(None, alias="HR/9")
    k_per_bb: Optional[float] = Field(None, alias="K/BB")
    k_minus_bb_pct: Optional[float] = Field(None, alias="K-BB%")

    @property
    def is_pitcher(self) -> bool:
        """Determine if the player is a pitcher based on parsing "Name" field
        Ex: "<a href=\"statss.aspx?playerid=10337&position=P\">Edwin Escobar</a>" -> True
        """
        return 'position=P' in (self.name or '')
    
    @property
    def league(self) -> Optional[str]:
        """Extract league from the "Team" field if possible (e.g. "NYM (NL)" -> "NL")"""
        if self.team and '(' in self.team and ')' in self.team:
            return self.team.split('(')[-1].split(')')[0]
        return None
    
    @property
    def positions(self) -> list[str]:
        """Extract position(s) from the "Name" field if possible 
        Ex: "<a href=\"statss.aspx?playerid=10711&position=2B/OF\">Arismendy Alcántara</a>" -> ["2B", "OF"])
        """
        positions = []
        name_value = self.name or ''
        if 'position=' in name_value:
            pos_part = name_value.split('position=')[-1].split('"')[0]  # Get the part after "position=" and before the next quote
            positions = pos_part.split('/')  # Split by '/' to get multiple positions if applicable
        return positions

