from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator

from .lineup import LineupBuilder, LineupCandidate


class CardSource(str, Enum):
    BOT    = "BOT"     # card_bot archive (official Showdown Bot cards)
    WOTC   = "WOTC"    # card_wotc table (WOTC cards)
    WBC    = "WBC"     # card_wbc table (World Baseball Classic cards)
    CUSTOM = "CUSTOM"  # internal.log_custom_card (user's own generated cards)


class PickSource(str, Enum):
    MANUAL    = "MANUAL"    # user picked the card themselves
    AUTOFILL  = "AUTOFILL"  # filled by the autofill algorithm
    IMPORTED  = "IMPORTED"  # copied from another team (future)


class TeamSource(str, Enum):
    USER     = "user"
    OFFICIAL = "official"
    ASG      = "asg"
    MLB      = "mlb"  # synthesized on-the-fly from a real MLB/WBC roster + card archive, never persisted


class TeamRosterSlot(BaseModel):
    card_id: str
    card_source: CardSource
    roster_position: str  # "C","1B","2B","3B","SS","LF","CF","RF","SP","RP","DH","BE"
    draft_order: Optional[int] = None
    pick_source: PickSource = PickSource.MANUAL


class LineupSlot(BaseModel):
    card_id: str
    card_source: CardSource
    field_position: str  # "C","1B","2B","3B","SS","LF","CF","RF","SP","DH" — derived from
                         # the roster on read, never stored on the lineup itself
    batting_order: int   # 1–9


class Lineup(BaseModel):
    name: str = "Default"
    index: int = 0
    slots: list[LineupSlot] = []


class PitcherAssignment(BaseModel):
    card_id: str
    card_source: CardSource
    role: str  # "SP1"–"SP5", "RP", "CL"


# Roster positions map 1:1 onto lineup field positions and rotation roles, so a team's
# defensive alignment and rotation are derived from the roster rather than stored.
# Lineups (batting order only) are the one piece that is stored, and only when the user
# creates one — the "Default" lineup below is always recomputed.
FIELD_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH']
ROTATION_ROLES  = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5']
BULLPEN_ROLES   = ['RP', 'CL']
PITCHER_ROLES   = ROTATION_ROLES + BULLPEN_ROLES
DEFAULT_LINEUP_NAME = 'Default'


def _lineup_candidates(roster: list[dict]) -> tuple[list[LineupCandidate], Optional[LineupCandidate]]:
    """Split the roster into batting-order candidates plus the pitcher who bats when
    there is no DH. Stats come from the widened card LATERALs in _TEAM_BASE_SELECT and
    are absent for WBC/CUSTOM cards."""
    def candidate(slot: dict, field_position: str) -> LineupCandidate:
        return LineupCandidate(
            card_id=slot['card_id'],
            card_source=slot['card_source'],
            field_position=field_position,
            command=slot.get('command'),
            outs=slot.get('outs'),
            speed=slot.get('speed'),
            points=slot.get('points'),
            onbase_perc=slot.get('onbase_perc'),
            slugging_perc=slot.get('slugging_perc'),
        )

    hitters = [candidate(s, s['roster_position']) for s in roster if s.get('roster_position') in FIELD_POSITIONS]

    # A pitcher only takes an at-bat when the DH slot is empty.
    pitcher = None
    if not any(h.field_position == 'DH' for h in hitters):
        ace = next((s for s in roster if s.get('roster_position') == 'SP1'), None)
        if ace:
            pitcher = candidate(ace, 'SP')

    return hitters, pitcher


def derive_lineups_rotation(roster: list[dict], stored_lineups: Optional[list[dict]] = None) -> tuple[list[dict], list[dict]]:
    """Rebuild the lineups and rotation for a team.

    Lineups: the computed 'Default' batting order always sits at index 0, followed by any
    user-created lineups. Stored lineups carry only (card_id, batting_order), so each slot's
    `field_position` is resolved here from the roster.

    Rotation: starters ordered by role (SP1..SP5), then the bullpen in roster order — which
    is `sort_order`, since the roster arrives ORDER BY sort_order.
    """
    default_slots = LineupBuilder(*_lineup_candidates(roster)).build()
    lineups: list[dict] = [{'name': DEFAULT_LINEUP_NAME, 'index': 0, 'slots': default_slots}]

    position_by_card = {s['card_id']: s.get('roster_position') for s in roster}
    for i, lineup in enumerate(stored_lineups or [], start=1):
        slots = [
            {
                'card_id': slot['card_id'],
                'card_source': slot['card_source'],
                'field_position': position_by_card.get(slot['card_id']) or 'DH',
                'batting_order': slot['batting_order'],
            }
            for slot in sorted(lineup.get('slots') or [], key=lambda s: s['batting_order'])
            # A player dropped from the roster since this lineup was saved is skipped.
            if slot['card_id'] in position_by_card
        ]
        lineups.append({'name': lineup['name'], 'index': i, 'slots': slots})

    starters = [s for s in roster if s.get('roster_position') in ROTATION_ROLES]
    starters.sort(key=lambda s: ROTATION_ROLES.index(s['roster_position']))
    bullpen = [s for s in roster if s.get('roster_position') in BULLPEN_ROLES]
    rotation = [
        {'card_id': s['card_id'], 'card_source': s['card_source'], 'role': s['roster_position']}
        for s in starters + bullpen
    ]

    return lineups, rotation


class Team(BaseModel):
    team_id: Optional[str] = None    # UUID assigned by DB on create
    user_id: Optional[str] = None    # None for official/admin teams
    name: str
    abbreviation: str                # stored uppercase, max 5 chars
    primary_color: str = "rgb(0,0,0)"
    secondary_color: str = "rgb(255,255,255)"
    is_public: bool = False
    source: TeamSource = TeamSource.USER
    # Roster constraint settings (flat columns in DB)
    pts_limit: Optional[int] = None
    roster_size: int = 25
    min_bench: int = 4
    min_bullpen: int = 5
    num_starters: int = 5
    bench_pts_multiplier: float = 1.0
    # Set / source restrictions
    allowed_sets: list[str] = []
    allowed_card_sources: list[str] = []
    # JSONB columns
    player_filters: dict = {}
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
        bench_positions = {"BE", "RP"}
        return [s for s in self.roster if s.roster_position.upper() not in bench_positions]

    @property
    def bench(self) -> list[TeamRosterSlot]:
        return [s for s in self.roster if s.roster_position.upper() == "BE"]

    @property
    def bullpen(self) -> list[TeamRosterSlot]:
        return [s for s in self.roster if s.roster_position.upper() == "RP"]

    def to_db_dict(self) -> dict:
        """Serialize to a flat dict suitable for DB insertion/update."""
        return {
            'name': self.name,
            'abbreviation': self.abbreviation,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'is_public': self.is_public,
            'source': self.source.value,
            'pts_limit': self.pts_limit,
            'roster_size': self.roster_size,
            'min_bench': self.min_bench,
            'min_bullpen': self.min_bullpen,
            'num_starters': self.num_starters,
            'bench_pts_multiplier': self.bench_pts_multiplier,
            'allowed_sets': self.allowed_sets,
            'allowed_card_sources': self.allowed_card_sources,
            'player_filters': self.player_filters,
            'roster': [s.model_dump() for s in self.roster],
            'lineups': [ln.model_dump() for ln in self.stored_lineups],
        }

    @property
    def stored_lineups(self) -> list['Lineup']:
        """User-created lineups only — the computed 'Default' is never persisted."""
        return [ln for ln in self.lineups if ln.name != DEFAULT_LINEUP_NAME]

    @classmethod
    def from_db_row(cls, row: dict) -> 'Team':
        """Deserialize from a DB row dict (as returned by RealDictCursor).

        The rotation and the 'Default' lineup are derived from the roster; only
        user-created lineups come off the row.
        """
        roster_rows = row.get('roster') or []
        derived_lineups, derived_rotation = derive_lineups_rotation(roster_rows, row.get('lineups'))
        return cls(
            team_id=str(row['team_id']),
            user_id=row.get('user_id'),
            name=row['name'],
            abbreviation=row['abbreviation'],
            primary_color=row.get('primary_color', 'rgb(0,0,0)'),
            secondary_color=row.get('secondary_color', 'rgb(255,255,255)'),
            is_public=row.get('is_public', False),
            source=row.get('source', TeamSource.USER),
            pts_limit=row.get('pts_limit'),
            roster_size=row.get('roster_size', 25),
            min_bench=row.get('min_bench', 4),
            min_bullpen=row.get('min_bullpen', 5),
            num_starters=row.get('num_starters', 5),
            bench_pts_multiplier=row.get('bench_pts_multiplier', 1.0),
            allowed_sets=row.get('allowed_sets') or [],
            allowed_card_sources=row.get('allowed_card_sources') or [],
            player_filters=row.get('player_filters') or {},
            roster=[TeamRosterSlot(**s) for s in roster_rows],
            lineups=[
                Lineup(
                    name=ln['name'],
                    index=ln['index'],
                    slots=[LineupSlot(**sl) for sl in ln.get('slots', [])],
                )
                for ln in derived_lineups
            ],
            rotation=[PitcherAssignment(**p) for p in derived_rotation],
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )
