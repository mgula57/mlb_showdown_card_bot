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
        self._standings_leagues_loaded = 0
        self.is_complete = False  # SET WHEN `clubs` LOADS - FALSE MEANS DON'T CACHE THE LIST

    @property
    def clubs(self) -> list[TakeoverClub]:
        """Every club in the season, sorted worst record first.

        Standings are the source of records, but they can come back empty (before Opening Day) or
        partial (one league failing, or the API listing only some clubs early on). The season's
        team list fills any club the standings missed, at 0-0.
        """
        if self._clubs is not None:
            return self._clubs

        standings_clubs = self._standings_clubs()
        listed_clubs = self._team_list_clubs()
        standing_abbrs = {club.abbreviation for club in standings_clubs}
        missing = [club for club in listed_clubs if club.abbreviation not in standing_abbrs]
        # COMPLETE WHEN THE TEAM LIST CONFIRMED EVERY CLUB, OR (IT FAILED) BOTH LEAGUES' STANDINGS CAME BACK
        self.is_complete = bool(listed_clubs) or self._standings_leagues_loaded == len(LEAGUE_IDS)

        if any(club.wins + club.losses > 0 for club in standings_clubs):
            # SEASON UNDERWAY: RANK BY RECORD. FILLED-IN 0-0 CLUBS GO LAST SO NONE BECOMES THE "WORST" DEFAULT
            self._clubs = sorted(standings_clubs, key=lambda club: (club.win_pct, club.wins)) + missing
        else:
            # NO GAMES YET (E.G. AN UPCOMING SEASON SIMMED IN THE OFFSEASON): RANK BY LAST SEASON'S
            # RECORD SO THE DEFAULT TAKEOVER IS STILL THE CLUB COMING OFF THE WORST YEAR
            prior = TakeoverOptions(year=self.year - 1, mlb_stats_api=self.mlb_stats_api)._standings_clubs()
            prior_rank = {club.abbreviation: rank for rank, club in enumerate(sorted(prior, key=lambda club: (club.win_pct, club.wins)))}
            self._clubs = sorted(standings_clubs + missing, key=lambda club: (prior_rank.get(club.abbreviation, len(prior_rank)), club.name))
        return self._clubs

    def _standings_clubs(self) -> list[TakeoverClub]:
        """Clubs with their records from the season's division standings (unsorted)."""
        clubs: list[TakeoverClub] = []
        self._standings_leagues_loaded = 0
        for league_id in LEAGUE_IDS:
            try:
                standings = self.mlb_stats_api.leagues.get_standings(
                    season=str(self.year), league_id=league_id, standings_type=StandingsType.BY_DIVISION,
                )
            except Exception:
                continue
            if standings:
                self._standings_leagues_loaded += 1
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
        return clubs

    def _team_list_clubs(self) -> list[TakeoverClub]:
        """Every club on the season's MLB team list, at 0-0. Empty if the lookup fails."""
        try:
            api_teams = self.mlb_stats_api.teams.get_teams(sport_id=1, season=self.year)
        except Exception:
            return []

        clubs: list[TakeoverClub] = []
        for api_team in api_teams:
            abbreviation = normalized_team_abbr(api_team.abbreviation, self.year)
            if abbreviation is None:
                continue
            league_abbr = league_abbreviation(api_team.league)
            division = api_team.division.name if api_team.division else None
            region = division.split(' ')[-1].upper() if division else ''
            clubs.append(TakeoverClub(
                abbreviation=abbreviation,
                name=api_team.name or abbreviation,
                league=league_abbr,
                division=f"{league_abbr} {region}" if league_abbr and region else None,
            ))
        return clubs

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
