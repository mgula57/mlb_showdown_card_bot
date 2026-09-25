from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ...shared.team import Team


@dataclass(frozen=True)
class RosterEra:
    """A year range an Era Roster (all-time or all-decade) is built from."""
    key: str
    label: str
    start_year: int
    end_year: int

    def team_name(self, base_name: str, abbreviation: Optional[str] = None) -> str:
        """Display name for one team's roster within this era, e.g. "1990s Yankees" or
        "All-Time Braves" -- nickname only, no city, since a franchise-spanning roster (the
        Braves alone have played as the Boston/Milwaukee/Atlanta Braves) has no single city
        that's correct for every year in the range. Resolved from `abbreviation` when it maps to
        a current franchise (see Team.nickname); `base_name` is just the fallback for the
        League-wide "All-MLB" sentinel or an abbreviation Team.nickname doesn't cover.

        Applied at read time (see api/seasons.py) rather than stored, so dim_era_team.name stays
        the plain franchise/league name and any future naming-format change doesn't need every
        era rebuilt."""
        nickname = Team.map_from_mlb_api_team(abbreviation).nickname if abbreviation else None
        return f"{self.label} {nickname or base_name}"


# A cross-team "All-MLB" Era Roster (e.g. "the best 1990s players, any team") is stored and
# addressed exactly like a real franchise's Era Roster -- same dim_era_team/dim_era_roster rows,
# same API routes, same URL shape -- just under this one reserved sentinel team_id instead of a
# real MLB Stats API team id (which are all positive). PostgresDB.fetch_era_candidate_pool skips
# its team_id crosswalk entirely when given no team_abbr, pooling every team's cards for the era.
LEAGUE_WIDE_TEAM_ID = 0
LEAGUE_WIDE_ABBR = "MLB"
LEAGUE_WIDE_NAME = "All-MLB"


class RosterEraRegistry:
    """The fixed set of eras Era Rosters can be built for: ALL_TIME (a franchise's full
    history) plus each full decade from 1900 through the current one.

    Deliberately a known, enumerable list rather than a freeform (start_year, end_year) the CLI
    could be given -- that keeps the Browse UI (a dropdown of short codes), the stored roster's
    primary key, and caching all simple. A user wanting an arbitrary custom range (e.g. a
    "1996-2001 dynasty" team) still has the regular team builder for that.
    """

    ALL_TIME_KEY = "ALL_TIME"
    ALL_TIME_START_YEAR = 1901
    _DECADE_START_FLOOR = 1900

    @classmethod
    def all_time(cls) -> RosterEra:
        return RosterEra(key=cls.ALL_TIME_KEY, label="All-Time", start_year=cls.ALL_TIME_START_YEAR, end_year=datetime.now().year)

    @classmethod
    def decade(cls, decade_start_year: int) -> RosterEra:
        return RosterEra(key=f"{decade_start_year}s", label=f"{decade_start_year}s",
                          start_year=decade_start_year, end_year=decade_start_year + 9)

    @classmethod
    def decades(cls, through_year: Optional[int] = None) -> list[RosterEra]:
        through_year = through_year or datetime.now().year
        return [cls.decade(y) for y in range(cls._DECADE_START_FLOOR, through_year + 1, 10)]

    @classmethod
    def all(cls) -> list[RosterEra]:
        """Every known era, ALL_TIME first, decades newest first."""
        return [cls.all_time()] + list(reversed(cls.decades()))

    @classmethod
    def from_key(cls, key: str) -> Optional[RosterEra]:
        if key == cls.ALL_TIME_KEY:
            return cls.all_time()
        if key and key.endswith('s') and key[:-1].isdigit() and int(key[:-1]) % 10 == 0:
            return cls.decade(int(key[:-1]))
        return None
