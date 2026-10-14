from dataclasses import dataclass


@dataclass(frozen=True)
class ScheduledGame:
    game_index: int   # 1-BASED, IN PLAY ORDER
    day: int          # 1-BASED
    home_key: str
    away_key: str


class LeagueSchedule:
    """A balanced round robin played as series.

    Built with the circle method: every "round" pairs each team with one opponent (a team sits
    out when the count is odd), and each pairing plays a `series_length`-game series on
    consecutive days, so on any day a team plays at most once. Rounds repeat until every team has
    `games_per_team` games or no pairing can be added without passing it. Each series is hosted
    by whichever of its two teams has had fewer home games so far, which keeps home games level.
    """

    def __init__(self, team_keys: list[str], games_per_team: int, series_length: int = 3) -> None:
        if len(team_keys) < 2:
            raise ValueError("A schedule needs at least 2 teams")
        self.team_keys = list(team_keys)
        self.games_per_team = games_per_team
        self.series_length = series_length

    def _rounds(self) -> list[list[tuple[str, str]]]:
        """One cycle of circle-method rounds: each a list of team pairings (the order only breaks
        hosting ties - see `games`)."""
        keys = self.team_keys + ([None] if len(self.team_keys) % 2 else [])
        n = len(keys)
        rounds = []
        for r in range(n - 1):
            pairings = []
            for i in range(n // 2):
                a, b = keys[i], keys[n - 1 - i]
                if a is None or b is None:
                    continue
                pairings.append((a, b) if (r + i) % 2 == 0 else (b, a))
            rounds.append(pairings)
            keys = [keys[0], keys[-1]] + keys[1:-1]  # ROTATE EVERYONE BUT THE FIRST
        return rounds

    def games(self) -> list[ScheduledGame]:
        played = {key: 0 for key in self.team_keys}
        home_games = {key: 0 for key in self.team_keys}
        games: list[ScheduledGame] = []
        day = 0
        cycle = 0
        rounds = self._rounds()
        while min(played.values()) < self.games_per_team:
            added_this_cycle = 0
            for pairings in rounds:
                # PICK EACH SERIES' HOST ONCE, BEFORE ITS FIRST GAME
                series = [
                    (a, b) if home_games[a] < home_games[b] or (home_games[a] == home_games[b] and cycle % 2 == 0) else (b, a)
                    for a, b in pairings
                ]
                for game_number in range(self.series_length):
                    day += 1
                    added_today = 0
                    for home, away in series:
                        if played[home] >= self.games_per_team or played[away] >= self.games_per_team:
                            continue
                        games.append(ScheduledGame(game_index=len(games) + 1, day=day, home_key=home, away_key=away))
                        played[home] += 1
                        played[away] += 1
                        home_games[home] += 1
                        added_today += 1
                    if added_today == 0:
                        day -= 1  # NOBODY PLAYED - DON'T LEAVE AN EMPTY DAY ON THE CALENDAR
                    added_this_cycle += added_today
            if added_this_cycle == 0:
                break  # EVERY REMAINING PAIRING WOULD PUSH SOMEONE PAST THE TARGET
            cycle += 1
        return games
