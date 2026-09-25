from collections import defaultdict
from typing import Optional

from ..mlb_stats_api import MLBStatsAPI
from ..mlb_stats_api.models.games.enums import GameType
from .models import PostseasonRound
from .schedule import normalized_team_abbr

_GAME_TYPE_TO_ROUND = {
    GameType.WILD_CARD: PostseasonRound.WILDCARD,
    GameType.DIVISION_SERIES: PostseasonRound.DIVISIONAL,
    GameType.LEAGUE_CHAMPIONSHIP_SERIES: PostseasonRound.CHAMPIONSHIP,
    GameType.WORLD_SERIES: PostseasonRound.WORLD_SERIES,
}


class RealPostseasonBracket:
    """Real postseason games played so far this year, indexed by round + matchup.

    Backs a `resume_from_real_postseason` run: rather than simulate the whole postseason from
    scratch, a series already underway (or finished) in real life is seeded with its actual win
    count via `record_for`, and only the games beyond that get simulated - see
    `PostseasonSeries.generate_games_list` / `Postseason.simulate`. A round that hasn't started in
    real life yet simply has no record for any matchup drawn from it, and plays out normally.

    Deliberately doesn't try to reconstruct per-game box scores for the real games themselves -
    those were never played through this engine's card-based rosters, so there is nothing
    meaningful to replay. A win/loss count is the same seeding strategy `resume_from_real_season`
    already uses for the regular season.
    """

    def __init__(self, year: int, mlb_stats_api: Optional[MLBStatsAPI] = None) -> None:
        self.year = year
        self._wins: dict[tuple[PostseasonRound, frozenset], dict[str, int]] = defaultdict(lambda: defaultdict(int))

        client = mlb_stats_api or MLBStatsAPI()
        schedule = client.games.get_season_schedule(
            season=year,
            game_types=[gt.value for gt in _GAME_TYPE_TO_ROUND],
        )

        for game in (schedule.games or []):
            round = _GAME_TYPE_TO_ROUND.get(game.game_type)
            if round is None or not game.teams or not game.teams.home or not game.teams.away:
                continue
            if not game.status or game.status.abstract_game_state != 'Final':
                continue

            home_line, away_line = game.teams.home, game.teams.away
            if home_line.is_winner is None and away_line.is_winner is None:
                continue

            home_abbr = normalized_team_abbr(home_line.team.abbreviation if home_line.team else None, year)
            away_abbr = normalized_team_abbr(away_line.team.abbreviation if away_line.team else None, year)
            if home_abbr is None or away_abbr is None:
                continue

            key = (round, frozenset({home_abbr, away_abbr}))
            if home_line.is_winner:
                self._wins[key][home_abbr] += 1
            elif away_line.is_winner:
                self._wins[key][away_abbr] += 1

    @property
    def has_any_results(self) -> bool:
        return len(self._wins) > 0

    def record_for(self, round: PostseasonRound, home_abbr: str, away_abbr: str) -> tuple[int, int]:
        """(home_wins, away_wins) already played in real life for this round + matchup.

        (0, 0) means no real games were found for it - either the round hasn't started yet in
        real life, or this exact matchup never happened (a round still fully in this sim's own
        hands). Either way the series plays out from scratch.
        """
        wins = self._wins.get((round, frozenset({home_abbr, away_abbr})), {})
        return wins.get(home_abbr, 0), wins.get(away_abbr, 0)
