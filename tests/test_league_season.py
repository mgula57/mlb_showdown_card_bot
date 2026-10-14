"""Offline checks for league season building blocks: the round-robin schedule and the bracket.

No database, no network. Run as `python tests/test_league_season.py`. The season runner itself
(chunked play against saved state) needs real cards and the league tables, so it's exercised
against the database instead.
"""

import os
import sys
from collections import Counter
from pathlib import Path
from random import Random

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from pydantic import ValidationError

from mlb_showdown_bot.core.league import BracketConfig, LeagueBracket, LeagueSchedule

failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  PASS  {label}")
    else:
        failures.append(f"{label}{f' -- {detail}' if detail else ''}")
        print(f"  FAIL  {label}{f' -- {detail}' if detail else ''}")


# ----------------------------------------------------------
print("SCHEDULE")
for teams, games_per_team in ((2, 10), (4, 20), (5, 30), (7, 162), (8, 162), (12, 162)):
    keys = [f"T{i}" for i in range(teams)]
    games = LeagueSchedule(keys, games_per_team).games()
    played, home, by_day = Counter(), Counter(), {}
    for game in games:
        played[game.home_key] += 1
        played[game.away_key] += 1
        home[game.home_key] += 1
        by_day.setdefault(game.day, []).extend([game.home_key, game.away_key])
    label = f"{teams} teams x {games_per_team}"
    check(f"{label}: every team plays exactly {games_per_team}", set(played.values()) == {games_per_team}, dict(played))
    check(f"{label}: nobody plays twice in a day", all(len(day) == len(set(day)) for day in by_day.values()))
    check(f"{label}: no empty days on the calendar", sorted(by_day) == list(range(1, len(by_day) + 1)))
    check(f"{label}: home games within 6 of even", max(home.values()) - min(home.values()) <= 6, dict(home))
    check(f"{label}: game indexes run 1..N in order", [g.game_index for g in games] == list(range(1, len(games) + 1)))

# ----------------------------------------------------------
print("\nBRACKET CONFIG")
for teams, lengths, ok in ((4, [5, 7], True), (6, [3, 5, 7], True), (8, [1, 5, 7], True), (0, [], True),
                           (4, [5], False), (4, [4, 7], False), (5, [5, 7], False)):
    try:
        BracketConfig(teams=teams, series_lengths=lengths)
        valid = True
    except ValidationError:
        valid = False
    check(f"{teams} teams {lengths} {'accepted' if ok else 'rejected'}", valid == ok)
check("round labels end with CS and WS", [r.value for r in BracketConfig.round_labels(3)] == ['DIV', 'CS', 'WS'])


def play_out(bracket: LeagueBracket, seed: int = 1) -> LeagueBracket:
    """Play every game, saving and reloading the bracket between days. Returns the final bracket."""
    rng, index, days = Random(seed), 0, 0
    while not bracket.is_complete:
        days += 1
        for series, home, away, _ in bracket.todays_games():
            index += 1
            bracket.record_game(series.series_id, home if rng.random() < 0.55 else away, index)
        bracket = LeagueBracket.from_state(bracket.to_state())  # SAVED AND RELOADED BETWEEN EVERY DAY
    return bracket


print("\nBRACKET PLAY")
seeds = [f"S{i}" for i in range(1, 9)]
six = LeagueBracket.create(BracketConfig(teams=6, series_lengths=[3, 5, 7]), seeds)
first_round = [(six.seeds[s.high_seed], six.seeds[s.low_seed]) for s in six.series if s.round_index == 0 and not s.is_bye]
check("6 teams: 3v6 and 4v5 play the first round", sorted(first_round) == [('S3', 'S6'), ('S4', 'S5')], first_round)
round_two = [(s.high_seed, s.low_seed) for s in six.series if s.round_index == 1]
check("6 teams: seeds 1 and 2 wait in round 2", sorted(r[0] for r in round_two) == [1, 2] and all(r[1] is None for r in round_two), round_two)
check("6 teams: only the first round plays day 1", {s.round_index for s, *_ in six.todays_games()} == {0})

for teams, lengths in ((2, [7]), (4, [5, 7]), (6, [3, 5, 7]), (8, [1, 5, 7])):
    bracket = play_out(LeagueBracket.create(BracketConfig(teams=teams, series_lengths=lengths), seeds))
    check(f"{teams} teams: reaches a champion", bracket.is_complete and bracket.champion_key in seeds[:teams], bracket.champion_key)
    result = bracket.as_result({}, {})
    check(f"{teams} teams: result rounds match the bracket", list(result.rounds) == [r.value for r in BracketConfig.round_labels(len(lengths))], list(result.rounds))
    for round_value, series_list in result.rounds.items():
        for s in series_list:
            needed = lengths[[r.value for r in BracketConfig.round_labels(len(lengths))].index(round_value)] // 2 + 1
            if max(s.home_team_wins, s.away_team_wins) != needed or s.winner is None:
                check(f"{teams} teams: every series decided at {needed} wins", False, s)
    for s in [s for s in result.rounds['WS']]:
        check(f"{teams} teams: better seed hosts the final", s.home_team_seed < s.away_team_seed, (s.home_team_seed, s.away_team_seed))

# ----------------------------------------------------------

if failures:
    print(f"\n{len(failures)} CHECK(S) FAILED:")
    for line in failures:
        print(f"  - {line}")
    sys.exit(1)
print("\nAll checks passed.")
