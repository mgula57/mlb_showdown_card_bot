from typing import Optional

from pydantic import BaseModel

from ..mlb_stats_api import MLBStatsAPI
from ..mlb_stats_api.models.leagues.standings import StandingsType
from .schedule import league_abbreviation, normalized_team_abbr

# THE TWO MLB LEAGUES. STANDINGS ARE FETCHED PER LEAGUE, SO BOTH ARE NEEDED FOR A FULL SEASON.
LEAGUE_IDS = (103, 104)  # AL, NL


class TakeoverClub(BaseModel):
    """A real club a builder team can replace, with the real record it posted that season."""

    abbreviation: str  # ERA-CORRECT - THIS IS THE SCHEDULE/CARD JOIN KEY, E.G. "TBD" FOR 1998
    name: str = ""
    league: Optional[str] = None
    division: Optional[str] = None
    wins: int = 0
    losses: int = 0

    @property
    def win_pct(self) -> float:
        games = self.wins + self.losses
        return self.wins / games if games else 0.0


class TakeoverOptions:
    """The clubs available to take over in a season, worst real record first.

    The default club is the season's worst - taking over a last-place team is the intended
    uphill version of the game - but any club can be chosen. Records come from the MLB Stats
    API rather than the archive because the archive stores cards, not team results.
    """

    def __init__(self, year: int, mlb_stats_api: Optional[MLBStatsAPI] = None) -> None:
        self.year = year
        self.mlb_stats_api = mlb_stats_api or MLBStatsAPI()
        self._clubs: Optional[list[TakeoverClub]] = None

    @property
    def clubs(self) -> list[TakeoverClub]:
        """Every club that played the season, sorted worst record first."""
        if self._clubs is not None:
            return self._clubs

        clubs: list[TakeoverClub] = []
        for league_id in LEAGUE_IDS:
            try:
                standings = self.mlb_stats_api.leagues.get_standings(
                    season=str(self.year), league_id=league_id, standings_type=StandingsType.BY_DIVISION,
                )
            except Exception:
                continue
            for standing in standings:
                league_abbr = league_abbreviation(standing.league)
                region = standing.division.name.split(' ')[-1].upper() if standing.division and standing.division.name else ''
                for record in (standing.team_records or []):
                    abbreviation = normalized_team_abbr(record.team.abbreviation, self.year)
                    if abbreviation is None:
                        continue
                    clubs.append(TakeoverClub(
                        abbreviation=abbreviation,
                        name=record.team.name or abbreviation,
                        league=league_abbr,
                        division=f"{league_abbr} {region}" if league_abbr and region else None,
                        wins=record.league_record.wins if record.league_record else 0,
                        losses=record.league_record.losses if record.league_record else 0,
                    ))

        self._clubs = sorted(clubs, key=lambda club: (club.win_pct, club.wins))
        return self._clubs

    @property
    def default_abbr(self) -> Optional[str]:
        """The season's worst club - the default to replace."""
        clubs = self.clubs
        return clubs[0].abbreviation if clubs else None

    def resolve(self, requested_abbr: Optional[str]) -> Optional[str]:
        """Validate a requested club, falling back to the worst-record default when unset.

        Returns None when the season has no standings at all, which lets the caller fail with
        the simulation's own team-list error rather than a vaguer one from here.
        """
        if not requested_abbr:
            return self.default_abbr
        requested = requested_abbr.upper()
        known = {club.abbreviation for club in self.clubs}
        if known and requested not in known:
            raise ValueError(f"'{requested}' did not play in {self.year}. Options: {sorted(known)}")
        return requested
