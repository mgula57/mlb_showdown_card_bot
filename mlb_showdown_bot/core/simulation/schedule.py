from datetime import date, datetime, timedelta
from itertools import combinations
from typing import Optional

from ..mlb_stats_api import MLBStatsAPI
from ..shared.team import Team as ShowdownTeam
from .game import Game


def league_abbreviation(league) -> Optional[str]:
    """Abbreviation for an MLB API League model ("American League" -> "AL"). The API often omits `abbreviation`."""
    if league is None:
        return None
    if league.abbreviation:
        return league.abbreviation
    if league.name:
        return ''.join(word[0] for word in league.name.split()).upper()
    return None


def normalized_team_abbr(api_abbreviation: Optional[str], year: int) -> Optional[str]:
    """The card archive's abbreviation for an MLB API team in a given season.

    The API reports a franchise's modern code for every season it played, so it is resolved
    back to the era-correct one - otherwise a historical season's schedule and divisions never
    join to its cards. Every lookup keyed on team abbreviation must go through here.
    """
    if api_abbreviation is None:
        return None
    showdown_team = ShowdownTeam.map_from_mlb_api_team(api_abbreviation)
    if showdown_team is None or showdown_team == ShowdownTeam.MLB:
        return api_abbreviation
    return showdown_team.for_year(year).value


class Schedule:
    """A season's worth of games plus team/league metadata.

    Sources:
      - MLB Stats API season schedule (any year the API covers)
      - Generated round robin for tournaments/custom leagues
    """

    def __init__(
        self, year: int, tournament: str = None, pct_limit: float = None, game_limit: int = None,
        team_names: list[str] = None, mlb_stats_api: Optional[MLBStatsAPI] = None, start_date: Optional[date] = None,
        allow_empty: bool = False,
    ) -> None:
        self.year = year
        self.tournament = tournament

        if tournament:
            self.generate_schedule(teams=team_names, games=game_limit)
            return

        self.load_schedule_from_mlb_api(
            year=year, game_limit=game_limit, pct_limit=pct_limit, mlb_stats_api=mlb_stats_api,
            start_date=start_date, allow_empty=allow_empty,
        )

    def _finalize_games_list(
        self, scheduled_games: list[dict], game_limit: int, pct_limit: float,
        original_games_per_team: int = None, start_date: Optional[date] = None, allow_empty: bool = False,
    ) -> None:
        """Shared tail end of schedule loading: apply limits and build Game objects.

        Each dict in scheduled_games needs: date, home_team, away_team, home_game_number, away_game_number, home_league, away_league.

        Args:
          original_games_per_team: Max games any team plays in the pre-limit schedule. Used to
            calibrate per-team roster/injury math against the *unlimited* schedule length even
            when `game_limit`/`pct_limit` shorten the simulated run.
          start_date: A rest-of-season projection's cutoff - only games on or after this date are
            kept, i.e. `start_date` itself is assumed not yet played (the common case is "today,"
            where that's true for at least part of the slate). Applied before `game_limit`/
            `pct_limit`, so the two combine ("the next 20 games from here") rather than one
            overriding the other.
          allow_empty: A `resume_from_real_postseason` run wants exactly this - every regular-
            season game already in the past, zero left to simulate. Team/league metadata is still
            derived from the full, unfiltered schedule below regardless of this flag, so the
            postseason has every real club to draw its bracket from even though none of them has
            a game here.
        """

        self.original_schedule_length = len(scheduled_games)

        # TEAM/LEAGUE METADATA COMES FROM THE FULL, UNFILTERED SCHEDULE - A CLUB'S LEAGUE DOESN'T
        # DEPEND ON WHETHER IT HAS A GAME LEFT TO PLAY.
        self.team_leagues: dict[str, str] = {}
        for scheduled_game in scheduled_games:
            self.team_leagues[scheduled_game['home_team']] = scheduled_game['home_league']
            self.team_leagues[scheduled_game['away_team']] = scheduled_game['away_league']
        self.unique_team_names = list(self.team_leagues.keys())

        playable_games = scheduled_games
        if start_date:
            playable_games = [g for g in playable_games if g['date'] >= start_date]
            if len(playable_games) == 0 and not allow_empty:
                raise ValueError(f"No games remain to simulate in {self.year} on or after {start_date}.")
        if game_limit:
            playable_games = playable_games[:game_limit]
        elif pct_limit:
            playable_games = playable_games[:int(len(playable_games) * pct_limit)]
        self.schedule_length = len(playable_games)

        self.games: list[Game] = []
        games_per_team_count: dict[str, int] = {}
        for index, scheduled_game in enumerate(playable_games):
            self.games.append(
                Game(
                    index=index,
                    date=scheduled_game['date'],
                    home_team_name=scheduled_game['home_team'],
                    away_team_name=scheduled_game['away_team'],
                    home_team_game_number=scheduled_game['home_game_number'],
                    away_team_game_number=scheduled_game['away_game_number'],
                )
            )
            games_per_team_count[scheduled_game['home_team']] = games_per_team_count.get(scheduled_game['home_team'], 0) + 1
            games_per_team_count[scheduled_game['away_team']] = games_per_team_count.get(scheduled_game['away_team'], 0) + 1

        # PER-TEAM GAME COUNTS + SCHEDULE DENSITY, USED TO CALIBRATE INJURY HAZARD RATES.
        self.games_per_team = max(games_per_team_count.values()) if games_per_team_count else 0
        self.original_games_per_team = original_games_per_team if original_games_per_team is not None else self.games_per_team
        if self.games:
            dates = [g.date for g in self.games]
            self.season_span_days = (max(dates) - min(dates)).days + 1
        else:
            self.season_span_days = 0

    @property
    def games_per_day(self) -> float:
        """Average games a team plays per calendar day of the season (schedule density)."""
        return self.games_per_team / max(self.season_span_days, 1)

    def load_schedule_from_mlb_api(
        self, year: int, game_limit: int, pct_limit: float, mlb_stats_api: Optional[MLBStatsAPI] = None,
        start_date: Optional[date] = None, allow_empty: bool = False,
    ) -> None:

        client = mlb_stats_api or MLBStatsAPI()
        season_schedule = client.games.get_season_schedule(season=year)

        def normalized_abbr(team) -> Optional[str]:
            return normalized_team_abbr(team.abbreviation if team else None, year)

        scheduled_games: list[dict] = []
        games_played_count: dict[str, int] = {}
        for game in (season_schedule.games or []):
            if not game.teams or not game.teams.home or not game.teams.away:
                continue
            home_team = game.teams.home.team
            away_team = game.teams.away.team
            home_abbr = normalized_abbr(home_team)
            away_abbr = normalized_abbr(away_team)
            if home_abbr is None or away_abbr is None or game.official_date is None:
                continue

            games_played_count[home_abbr] = games_played_count.get(home_abbr, 0) + 1
            games_played_count[away_abbr] = games_played_count.get(away_abbr, 0) + 1

            scheduled_games.append({
                'date': datetime.strptime(game.official_date, '%Y-%m-%d').date(),
                'home_team': home_abbr,
                'away_team': away_abbr,
                'home_game_number': games_played_count[home_abbr],
                'away_game_number': games_played_count[away_abbr],
                'home_league': league_abbreviation(home_team.league) or 'MLB',
                'away_league': league_abbreviation(away_team.league) or 'MLB',
            })

        if len(scheduled_games) == 0:
            raise ValueError(f"MLB Stats API returned no schedule data for {year}")

        original_games_per_team = max(games_played_count.values()) if games_played_count else 0
        self._finalize_games_list(
            scheduled_games=scheduled_games, game_limit=game_limit, pct_limit=pct_limit,
            original_games_per_team=original_games_per_team, start_date=start_date, allow_empty=allow_empty,
        )

    def generate_schedule(self, teams: list[str], games: int) -> None:

        self.original_schedule_length = games
        self.schedule_length = games
        self.unique_team_names = teams
        self.team_leagues = {tm: self.tournament for tm in teams }

        # ROUND ROBIN
        combos = list(combinations(teams, 2))
        num_combos = len(combos)
        self.games = []
        while len(self.games) < games:
            for matchup in combos:
                if len(self.games) >= games:
                    break
                index = len(self.games) + 1
                game_date = (datetime.now() + timedelta(int(index / num_combos))).date()
                home_team = matchup[0]
                away_team = matchup[1]

                self.games.append(
                    Game(
                        index=index,
                        date=game_date,
                        home_team_name=home_team,
                        away_team_name=away_team,
                        home_team_game_number=len([g for g in self.games if g.home_team_name == home_team or g.away_team_name == home_team]) + 1,
                        away_team_game_number=len([g for g in self.games if g.home_team_name == away_team or g.away_team_name == away_team]) + 1,
                    )
                )

        # PER-TEAM GAME COUNTS + SCHEDULE DENSITY (TOURNAMENTS DON'T USE INJURIES, BUT KEEP THE FIELDS POPULATED).
        games_per_team_count: dict[str, int] = {}
        for game in self.games:
            games_per_team_count[game.home_team_name] = games_per_team_count.get(game.home_team_name, 0) + 1
            games_per_team_count[game.away_team_name] = games_per_team_count.get(game.away_team_name, 0) + 1
        self.games_per_team = max(games_per_team_count.values()) if games_per_team_count else 0
        self.original_games_per_team = self.games_per_team
        if self.games:
            dates = [g.date for g in self.games]
            self.season_span_days = (max(dates) - min(dates)).days + 1
        else:
            self.season_span_days = 0
