from typing import ClassVar, Dict, List, Optional

from psycopg2 import sql
from pydantic import BaseModel

from ..database.postgres_db import PostgresDB
from .selection import PositionTarget, SlotPosition


class WotcSetProfile(BaseModel):
    """Composition of an original WOTC base set (expansion `BS`): how many cards it had at each
    position and what they averaged in points. Used as set-builder blueprints."""

    showdown_set: str
    set_size: int
    team_count: int
    position_targets: List[PositionTarget]

    # WOTC sets never change, so profiles are cached for the life of the process
    _cache: ClassVar[Optional[Dict[str, 'WotcSetProfile']]] = None

    @classmethod
    def load_all(cls) -> Dict[str, 'WotcSetProfile']:
        """Profiles for every WOTC base set, keyed by showdown set"""
        if cls._cache is None:
            db = PostgresDB()
            rows = db.execute_query(sql.SQL("""
                SELECT showdown_set, positions_list[1] AS position, team_id, points
                FROM card_wotc
                WHERE expansion = 'BS' AND positions_list[1] IS NOT NULL
            """))
            db.close_connection()
            profiles = cls._from_rows(rows)
            if profiles:
                cls._cache = profiles
            return profiles
        return cls._cache

    @classmethod
    def load(cls, showdown_set: str) -> 'WotcSetProfile':
        profile = cls.load_all().get(str(showdown_set))
        if profile is None:
            raise ValueError(f"No WOTC base set profile for '{showdown_set}'")
        return profile

    @classmethod
    def _from_rows(cls, rows: List[dict]) -> Dict[str, 'WotcSetProfile']:
        rows_by_set: Dict[str, List[dict]] = {}
        for row in rows:
            rows_by_set.setdefault(str(row['showdown_set']), []).append(row)

        profiles: Dict[str, WotcSetProfile] = {}
        for showdown_set, set_rows in sorted(rows_by_set.items()):
            points_by_slot: Dict[str, List[int]] = {}
            for row in set_rows:
                slot = SlotPosition.normalize(row['position'])
                points_by_slot.setdefault(slot, []).append(row['points'] or 0)
            set_size = len(set_rows)
            profiles[showdown_set] = cls(
                showdown_set=showdown_set,
                set_size=set_size,
                team_count=len({row['team_id'] for row in set_rows if row['team_id']}),
                position_targets=[
                    PositionTarget(
                        position=slot,
                        percentage=len(points_by_slot[slot]) / set_size,
                        avg_points=round(sum(points_by_slot[slot]) / len(points_by_slot[slot])),
                    )
                    for slot in SlotPosition.ALL if slot in points_by_slot
                ],
            )
        return profiles
