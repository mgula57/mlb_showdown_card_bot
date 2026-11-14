"""Read-only teams the Team Builder builds rather than stores: a historical MLB club for one season,
and an Era Roster (a current club's best players across a decade or all time).

Both prefer pre-processed rosters (the `showdown_bot teams` imports) and compose one on the fly
for any club the import hasn't covered. The `/seasons/.../showdown_team` routes serve them to the
Team Builder, and a live game resolves either kind into a club through the same builder, so the two
can never field different rosters for the same team.
"""

from datetime import datetime, timedelta
from typing import Optional

from ...database.postgres_db import PostgresDB
from ..sets import Set as ShowdownSet
from .era_roster_drafter import EraRosterDrafter
from .roster_era import LEAGUE_WIDE_ABBR, LEAGUE_WIDE_NAME, LEAGUE_WIDE_TEAM_ID, RosterEraRegistry
from .roster_to_team_converter import RosterToTeamConverter
from .stored_roster_to_team_converter import StoredRosterToTeamConverter
from .team import Team


class SyntheticTeamError(ValueError):
    """A request for a team that doesn't exist or can't be built. Safe to show the user."""


class SyntheticTeams:
    """Builds historical and era teams in the `/user/teams` API shape, cached per worker."""

    CACHE_TTL = timedelta(hours=1)
    _cache: dict[str, tuple[dict, datetime]] = {}

    @classmethod
    def _cached(cls, key: str) -> Optional[dict]:
        hit = cls._cache.get(key)
        return hit[0] if hit and datetime.now() - hit[1] < cls.CACHE_TTL else None

    @classmethod
    def _store(cls, key: str, data: dict) -> dict:
        cls._cache[key] = (data, datetime.now())
        return data

    @staticmethod
    def parse_set(showdown_set: str) -> ShowdownSet:
        try:
            return ShowdownSet(showdown_set)
        except ValueError:
            raise SyntheticTeamError(f'Invalid showdown_set: {showdown_set}. Valid options are: {[s.value for s in ShowdownSet]}')

    @classmethod
    def historical(cls, season: int, team_id: int, sport_id: int = 1, showdown_set: str = ShowdownSet._2000.value,
                   team_abbr: Optional[str] = None, team_name: Optional[str] = None) -> dict:
        """A historical MLB club's roster for one season, as an API team dict."""
        set_value = cls.parse_set(showdown_set).value
        key = f"{season}:{team_id}:{sport_id}:{set_value}"
        if (cached := cls._cached(key)) is not None:
            return cached

        synthetic_team_id = f"mlb-{sport_id}-{team_id}-{season}-{set_value}"
        with PostgresDB() as db:
            stored_cards, stored_slots = db.fetch_historical_team_card_pool(
                season=season, showdown_set=set_value, team_id=team_id, sport_id=sport_id,
            )
            if stored_slots:
                # Pre-processed: identity is stored too, so a cold link needs no client-side resolution.
                identity = db.fetch_historical_team(season=season, team_id=team_id, sport_id=sport_id) or {}
                builder = StoredRosterToTeamConverter(
                    cards=stored_cards,
                    meta_rows=stored_slots,
                    team_id=synthetic_team_id,
                    name=identity.get('name') or team_name or team_abbr or f"Team {team_id}",
                    abbreviation=identity.get('abbreviation') or team_abbr or str(team_id),
                    primary_color=identity.get('primary_color'),
                    secondary_color=identity.get('secondary_color'),
                )
            else:
                cards = db.fetch_team_season_card_pool(
                    season=season, showdown_set=set_value, team_id=team_id, team_abbr=team_abbr, sport_id=sport_id,
                )
                builder = RosterToTeamConverter(
                    cards=cards,
                    team_id=synthetic_team_id,
                    name=team_name or team_abbr or f"Team {team_id}",
                    abbreviation=team_abbr or str(team_id),
                    season=season,
                )
        return cls._store(key, builder.build_api_dict())

    @classmethod
    def era(cls, team_id: int, era_key: str = RosterEraRegistry.ALL_TIME_KEY, sport_id: int = 1,
            showdown_set: str = ShowdownSet._2000.value, team_abbr: Optional[str] = None, team_name: Optional[str] = None) -> dict:
        """A current club's Era Roster, as an API team dict.

        Prefers the pre-processed slots in internal.dim_era_roster (a lookup), and falls back to
        composing the roster on the fly via EraRosterDrafter for any team/era the CLI backfill
        hasn't covered.
        """
        era = RosterEraRegistry.from_key(era_key)
        if era is None:
            raise SyntheticTeamError(f'Invalid era: {era_key}. Valid options are: {[e.key for e in RosterEraRegistry.all()]}')
        set_value = cls.parse_set(showdown_set).value
        key = f"era:{era.key}:{team_id}:{sport_id}:{set_value}"
        if (cached := cls._cached(key)) is not None:
            return cached

        synthetic_team_id = f"era-{era.key}-{sport_id}-{team_id}-{set_value}"
        with PostgresDB() as db:
            stored_cards, stored_slots = db.fetch_era_team_card_pool(
                team_id=team_id, era=era.key, showdown_set=set_value, sport_id=sport_id,
            )
            if stored_slots:
                identity = db.fetch_era_team(team_id=team_id, era=era.key, showdown_set=set_value, sport_id=sport_id) or {}
                raw_name = identity.get('name') or team_name or team_abbr or f"Team {team_id}"
                resolved_abbr = identity.get('abbreviation') or team_abbr
                builder = StoredRosterToTeamConverter(
                    cards=stored_cards,
                    meta_rows=stored_slots,
                    team_id=synthetic_team_id,
                    name=era.team_name(raw_name, abbreviation=resolved_abbr),
                    abbreviation=resolved_abbr or str(team_id),
                    primary_color=identity.get('primary_color'),
                    secondary_color=identity.get('secondary_color'),
                )
            elif team_id == LEAGUE_WIDE_TEAM_ID:
                # Cross-team "All-MLB" roster — no team filter at all, pooled from every team.
                candidates = db.fetch_era_candidate_pool(
                    team_abbr=None, showdown_set=set_value, start_year=era.start_year, end_year=era.end_year,
                )
                builder = EraRosterDrafter(
                    cards=candidates,
                    team_id=synthetic_team_id,
                    name=era.team_name(team_name or LEAGUE_WIDE_NAME),
                    abbreviation=team_abbr or LEAGUE_WIDE_ABBR,
                )
            else:
                candidates = db.fetch_era_candidate_pool(
                    team_abbr=team_abbr or str(team_id), showdown_set=set_value, start_year=era.start_year, end_year=era.end_year,
                )
                builder = EraRosterDrafter(
                    cards=candidates,
                    team_id=synthetic_team_id,
                    name=era.team_name(team_name or team_abbr or f"Team {team_id}", abbreviation=team_abbr),
                    abbreviation=team_abbr or str(team_id),
                )
        return cls._store(key, builder.build_api_dict())

    @staticmethod
    def as_team(data: dict) -> Team:
        """An API team dict back as a `Team`, e.g. to field it in a game."""
        return Team(**{key: value for key, value in data.items() if key in Team.model_fields})
