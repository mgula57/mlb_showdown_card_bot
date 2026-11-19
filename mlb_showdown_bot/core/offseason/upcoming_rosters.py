import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from typing import ClassVar, Optional

from pydantic import BaseModel

from ..card.team_builder import RosterToTeamConverter
from ..database.postgres_db import PostgresDB, ExploreDataRecord
from ..mlb_stats_api import MLBStatsAPI, RosterTypeEnum
from ..mlb_stats_api.clients.teams_client import TeamsClient


class RosterEntry(BaseModel):
    """One player on a club's 40-man."""

    mlb_id: int
    name: str
    position: Optional[str] = None  # MLB abbreviation ('C', 'SS', 'CF', 'P', 'TWP', ...)

    @property
    def is_pitcher(self) -> bool:
        return self.position == 'P'


class UpcomingSeasonRosters:
    """Rosters for a season that hasn't reached Opening Day yet.

    Each club's roster is its current 40-man from the MLB Stats API, which already reflects
    offseason trades and signings, paired with every player's card from the season before. Free
    agents who haven't signed are on no roster. A player with no card that year (a rookie, or
    someone who missed it) has no card in the pools; `entries_by_team` still lists him, so the sim
    can give him a replacement-level card when his club needs the spot (see `RosterGapFiller`).
    """

    CACHE_TTL: ClassVar[timedelta] = timedelta(minutes=30)
    _MAX_WORKERS: ClassVar[int] = 8
    # (season, sport_id) -> (team_id -> 40-man, fetched at). Shared across instances so the
    # standings, team pages and sim all reuse one fetch of the 30 rosters.
    _cache: ClassVar[dict[tuple[int, int], tuple[dict[int, list[RosterEntry]], datetime]]] = {}
    # (season, sport_id, showdown_set) -> (team_id -> composed 26-man points, computed at)
    _points_cache: ClassVar[dict[tuple[int, int, str], tuple[dict[int, int], datetime]]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, mlb_stats_api: MLBStatsAPI, sport_id: int = 1):
        self.api = mlb_stats_api
        self.sport_id = sport_id

    # ------------------------------------------------------------------
    # SEASON STATE
    # ------------------------------------------------------------------

    def applies_to(self, season: int) -> bool:
        """True for a future season, or the current one before its regular season opens."""
        today = date.today()
        if season != today.year:
            return season > today.year
        calendar = self.api.seasons.get_season(season=season, sport_id=self.sport_id)
        if not calendar or not calendar.regular_season_start_date:
            return False
        return today < date.fromisoformat(calendar.regular_season_start_date)

    @staticmethod
    def card_year(season: int) -> int:
        """Cards come from the last completed season."""
        return season - 1

    # ------------------------------------------------------------------
    # ROSTERS
    # ------------------------------------------------------------------

    def entries_by_team(self, season: int) -> dict[int, list[RosterEntry]]:
        """Every club's 40-man, keyed by MLB team id."""
        key = (season, self.sport_id)
        with self._lock:
            cached = self._cache.get(key)
            if cached and datetime.now() - cached[1] < self.CACHE_TTL:
                return cached[0]

        teams = self.api.teams.get_teams(sport_id=self.sport_id, season=season)
        # A dedicated client: 30 rosters would churn the shared client's small response cache, and
        # this layer caches the result itself.
        roster_client = TeamsClient(use_cache=False, rate_limit_delay=0)

        def fetch(team_id: int) -> tuple[int, list[RosterEntry]]:
            try:
                roster = roster_client.get_team_roster(team_id=team_id, season=str(season), roster_type=RosterTypeEnum.MAN_40)
            except Exception:
                return team_id, []
            return team_id, [
                RosterEntry(
                    mlb_id=slot.person.id,
                    name=slot.person.full_name or str(slot.person.id),
                    position=slot.position.abbreviation if slot.position else None,
                )
                for slot in roster.roster
            ]

        with ThreadPoolExecutor(max_workers=self._MAX_WORKERS) as pool:
            rosters = dict(pool.map(fetch, [team.id for team in teams]))

        # A club whose fetch failed stays out of the cache so the next request retries it.
        if all(rosters.values()):
            with self._lock:
                self._cache[key] = (rosters, datetime.now())
        return rosters

    def mlb_ids_by_team(self, season: int) -> dict[int, list[int]]:
        """Every club's 40-man, as MLB player ids keyed by MLB team id."""
        return {team_id: [entry.mlb_id for entry in entries] for team_id, entries in self.entries_by_team(season).items()}

    def entries_by_abbreviation(self, season: int) -> dict[str, list[RosterEntry]]:
        """Every club's 40-man, keyed by the MLB API abbreviation (e.g. 'KC')."""
        abbreviations = {team.id: team.abbreviation for team in self.api.teams.get_teams(sport_id=self.sport_id, season=season) if team.abbreviation}
        return {
            abbreviations[team_id]: entries
            for team_id, entries in self.entries_by_team(season).items() if team_id in abbreviations
        }

    def card_pools(self, season: int, showdown_set: str, db: PostgresDB, team_ids: Optional[list[int]] = None) -> dict[int, list[ExploreDataRecord]]:
        """Each club's cards, in one query. Narrow to `team_ids` to skip the rest."""
        rosters = self.mlb_ids_by_team(season)
        if team_ids is not None:
            rosters = {team_id: ids for team_id, ids in rosters.items() if team_id in team_ids}
        team_by_mlb_id = {mlb_id: team_id for team_id, ids in rosters.items() for mlb_id in ids}
        records = db.fetch_card_bot_records_for_mlb_ids(
            mlb_ids=list(team_by_mlb_id),
            card_year=self.card_year(season),
            showdown_set=showdown_set,
        )
        pools: dict[int, list[ExploreDataRecord]] = {team_id: [] for team_id in rosters}
        for record in records:
            team_id = team_by_mlb_id.get(record.mlb_id)
            if team_id is not None:
                pools[team_id].append(record)
        return pools

    def team_points(self, season: int, showdown_set: str, db: PostgresDB) -> dict[int, int]:
        """Card points of each club's composed 26-man, the number the standings show."""
        key = (season, self.sport_id, showdown_set)
        with self._lock:
            cached = self._points_cache.get(key)
            if cached and datetime.now() - cached[1] < self.CACHE_TTL:
                return cached[0]
        points: dict[int, int] = {}
        for team_id, cards in self.card_pools(season=season, showdown_set=showdown_set, db=db).items():
            builder = RosterToTeamConverter(cards=cards, team_id=str(team_id), name=str(team_id), abbreviation=str(team_id), season=season,
                                            allow_adjacent_positions=True)
            points[team_id] = builder.rostered_points() if cards else 0
        with self._lock:
            self._points_cache[key] = (points, datetime.now())
        return points
