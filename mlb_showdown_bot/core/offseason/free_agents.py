import threading
from datetime import datetime, timedelta
from typing import ClassVar, Optional

from pydantic import BaseModel

from ..database.postgres_db import PostgresDB
from ..mlb_stats_api import MLBStatsAPI
from .upcoming_rosters import UpcomingSeasonRosters


class UnsignedFreeAgent(BaseModel):
    """A free agent from last season's class who hasn't signed anywhere yet."""

    mlb_id: int
    name: str
    position: Optional[str] = None  # MLB abbreviation ('SP', 'C', 'OF', ...)
    original_team_id: Optional[int] = None
    original_team_abbreviation: Optional[str] = None  # MLB API abbreviation, not yet era-normalized
    # FROM THE PLAYER'S CARD IN THE REQUESTED SET - SET BY `with_cards`.
    points: Optional[int] = None
    card_positions: list[str] = []
    is_pitcher: bool = False
    pa: Optional[int] = None
    ip: Optional[float] = None


class UnsignedFreeAgents:
    """The players a pre-Opening Day sim leaves out because they're on no club yet.

    Comes from the MLB API's free agent list for the card season (the 2026 class for a 2027 sim),
    minus anyone who has signed. Anyone already on a 40-man is also dropped, in case the free agent
    list lags behind the roster.
    """

    CACHE_TTL: ClassVar[timedelta] = timedelta(minutes=30)
    _cache: ClassVar[dict[int, tuple[list[UnsignedFreeAgent], datetime]]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, mlb_stats_api: MLBStatsAPI):
        self.api = mlb_stats_api

    def for_season(self, season: int) -> list[UnsignedFreeAgent]:
        """Unsigned free agents heading into `season`."""
        with self._lock:
            cached = self._cache.get(season)
            if cached and datetime.now() - cached[1] < self.CACHE_TTL:
                return cached[0]

        rostered = {mlb_id for ids in UpcomingSeasonRosters(mlb_stats_api=self.api).mlb_ids_by_team(season).values() for mlb_id in ids}
        free_agents = [
            UnsignedFreeAgent(
                mlb_id=fa.player.id,
                name=fa.player.full_name or str(fa.player.id),
                position=fa.position.abbreviation if fa.position else None,
                original_team_id=fa.original_team.id if fa.original_team else None,
                original_team_abbreviation=fa.original_team.abbreviation if fa.original_team else None,
            )
            for fa in self.api.people.get_free_agents(season=UpcomingSeasonRosters.card_year(season))
            if fa.new_team is None and fa.date_signed is None and fa.player.id not in rostered
        ]
        with self._lock:
            self._cache[season] = (free_agents, datetime.now())
        return free_agents

    def with_cards(self, season: int, showdown_set: str, db: PostgresDB) -> list[UnsignedFreeAgent]:
        """Only the free agents with a card in `showdown_set`, best card first. A two-way player's
        higher-point card stands for him."""
        free_agents = self.for_season(season)
        records = db.fetch_card_bot_records_for_mlb_ids(
            mlb_ids=[fa.mlb_id for fa in free_agents],
            card_year=UpcomingSeasonRosters.card_year(season),
            showdown_set=showdown_set,
        )
        best_by_mlb_id = {}
        for record in records:
            current = best_by_mlb_id.get(record.mlb_id)
            if current is None or (record.points or 0) > (current.points or 0):
                best_by_mlb_id[record.mlb_id] = record
        carded = [
            fa.model_copy(update={
                'points': record.points, 'card_positions': list(record.primary_positions),
                'is_pitcher': record.player_type == 'PITCHER', 'pa': record.pa, 'ip': record.real_ip,
            })
            for fa in free_agents if (record := best_by_mlb_id.get(fa.mlb_id)) is not None
        ]
        return sorted(carded, key=lambda fa: -(fa.points or 0))
