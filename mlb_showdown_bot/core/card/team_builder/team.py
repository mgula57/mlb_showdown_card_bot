from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class CardSource(str, Enum):
    BOT    = "BOT"     # card_bot archive (official Showdown Bot cards)
    WOTC   = "WOTC"    # card_wotc table (WOTC + WBC cards)
    CUSTOM = "CUSTOM"  # internal.log_custom_card (user's own generated cards)


class TeamSource(str, Enum):
    USER     = "user"
    OFFICIAL = "official"
    ASG      = "asg"


class TeamRosterSlot(BaseModel):
    card_id: str
    card_source: CardSource
    roster_position: str  # "C","1B","2B","3B","SS","LF","CF","RF","SP","RP","DH","BENCH","BULLPEN"
    draft_order: Optional[int] = None


class LineupSlot(BaseModel):
    card_id: str
    card_source: CardSource
    field_position: str       # "C","1B","2B","3B","SS","LF","CF","RF","SP","DH"
    batting_order: Optional[int] = None  # 1–9, None for pitchers/DH


class Lineup(BaseModel):
    name: str = "Default"
    slots: list[LineupSlot] = []


class PitcherAssignment(BaseModel):
    card_id: str
    card_source: CardSource
    role: str  # "SP1"–"SP5", "CP", "SU", "MR", "LONG"


class Team(BaseModel):
    team_id: Optional[str] = None    # UUID assigned by DB on create
    user_id: Optional[str] = None    # None for official/admin teams
    name: str
    abbreviation: str                # stored uppercase, max 5 chars
    primary_color: str = "rgb(0,0,0)"
    secondary_color: str = "rgb(255,255,255)"
    showdown_set: str = "EXPANDED"
    is_public: bool = False
    source: TeamSource = TeamSource.USER
    # Roster constraint settings (flat columns in DB)
    pts_limit: Optional[int] = None
    roster_size: int = 25
    min_bench: int = 4
    min_bullpen: int = 5
    bench_pts_multiplier: float = 1.0
    # JSONB columns
    roster: list[TeamRosterSlot] = []
    lineups: list[Lineup] = []
    rotation: list[PitcherAssignment] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator('abbreviation')
    @classmethod
    def normalize_abbreviation(cls, v: str) -> str:
        return v.strip()[:5].upper()

    @property
    def starters(self) -> list[TeamRosterSlot]:
        bench_positions = {"BENCH", "BULLPEN"}
        return [s for s in self.roster if s.roster_position.upper() not in bench_positions]

    @property
    def bench(self) -> list[TeamRosterSlot]:
        return [s for s in self.roster if s.roster_position.upper() == "BENCH"]

    @property
    def bullpen(self) -> list[TeamRosterSlot]:
        return [s for s in self.roster if s.roster_position.upper() == "BULLPEN"]

    def to_db_dict(self) -> dict:
        """Serialize to a flat dict suitable for DB insertion/update."""
        return {
            'name': self.name,
            'abbreviation': self.abbreviation,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'showdown_set': self.showdown_set,
            'is_public': self.is_public,
            'source': self.source.value,
            'pts_limit': self.pts_limit,
            'roster_size': self.roster_size,
            'min_bench': self.min_bench,
            'min_bullpen': self.min_bullpen,
            'bench_pts_multiplier': self.bench_pts_multiplier,
            'roster': [s.model_dump() for s in self.roster],
            'lineups': [
                {'name': ln.name, 'slots': [sl.model_dump() for sl in ln.slots]}
                for ln in self.lineups
            ],
            'rotation': [p.model_dump() for p in self.rotation],
        }

    @classmethod
    def from_db_row(cls, row: dict) -> 'Team':
        """Deserialize from a DB row dict (as returned by RealDictCursor)."""
        return cls(
            team_id=str(row['team_id']),
            user_id=row.get('user_id'),
            name=row['name'],
            abbreviation=row['abbreviation'],
            primary_color=row.get('primary_color', 'rgb(0,0,0)'),
            secondary_color=row.get('secondary_color', 'rgb(255,255,255)'),
            showdown_set=row.get('showdown_set', 'EXPANDED'),
            is_public=row.get('is_public', False),
            source=row.get('source', TeamSource.USER),
            pts_limit=row.get('pts_limit'),
            roster_size=row.get('roster_size', 25),
            min_bench=row.get('min_bench', 4),
            min_bullpen=row.get('min_bullpen', 5),
            bench_pts_multiplier=row.get('bench_pts_multiplier', 1.0),
            roster=[TeamRosterSlot(**s) for s in (row.get('roster') or [])],
            lineups=[
                Lineup(name=ln['name'], slots=[LineupSlot(**sl) for sl in ln.get('slots', [])])
                for ln in (row.get('lineups') or [])
            ],
            rotation=[PitcherAssignment(**p) for p in (row.get('rotation') or [])],
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )
