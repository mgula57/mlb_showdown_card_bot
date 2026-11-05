"""Offline checks for the Leagues list tile payload (`core/league/list_item.py`).

No database: rows are built by hand in the shape `PostgresDB.list_user_leagues` returns.
Run as `python tests/test_league_list_item.py`.
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from mlb_showdown_bot.core.league import LeagueListItem, SnakeOrder

failures: list[str] = []


def check(label: str, passed: bool) -> None:
    print(f"{'PASS' if passed else 'FAIL'}  {label}")
    if not passed:
        failures.append(label)


def team(abbreviation: str) -> dict:
    return {'team_id': f"id-{abbreviation}", 'user_id': None, 'name': abbreviation, 'abbreviation': abbreviation,
            'primary_color': None, 'secondary_color': None}


def record(abbreviation: str, wins: int, losses: int) -> dict:
    return {'name': abbreviation, 'identity': {'abbreviation': abbreviation}, 'wins': wins, 'losses': losses,
            'win_pct': wins / (wins + losses)}


def row(**overrides) -> dict:
    return {'league_id': 'L1', 'settings': {'team_count': 3, 'roster_size': 20}, 'current_season_status': None,
            'champion_team_id': None, 'picks_made': 0, 'standing_divisions': None, 'games_per_team': None,
            'teams': [], **overrides}


# BEFORE THE FIRST DRAFT
open_league = LeagueListItem(row()).payload()
check("an open league has no teams or draft", open_league['teams'] == [] and open_league['draft_pick'] is None)
check("raw standings stay off the payload", 'standing_divisions' not in open_league and 'picks_made' not in open_league)

# THE DRAFT'S SECOND ROUND SNAKES BACK: PICK 4 OF 3 TEAMS IS THE LAST SLOT
teams = [team('AAA'), team('BBB'), team('CCC')]
drafting = LeagueListItem(row(current_season_status='drafting', teams=teams, picks_made=3)).payload()
check("the snake puts the last slot on the clock for round 2",
      [t['abbreviation'] for t in drafting['teams'] if t['is_on_the_clock']] == ['CCC'])
check("draft teams stay in slot order", [t['abbreviation'] for t in drafting['teams']] == ['AAA', 'BBB', 'CCC'])
check("the pick count reads pick 4 of 60", (drafting['draft_pick'], drafting['draft_total_picks']) == (4, SnakeOrder(3, 20).total_picks))

done = LeagueListItem(row(current_season_status='drafting', teams=teams, picks_made=60)).payload()
check("a finished draft has no one on the clock", not any(t['is_on_the_clock'] for t in done['teams']) and done['draft_pick'] is None)

# STANDINGS ORDER AND RECORDS
divisions = {'LEAGUE': [record('BBB', 50, 30), record('AAA', 40, 40), record('CCC', 30, 50)]}
regular = LeagueListItem(row(current_season_status='regular', teams=teams, standing_divisions=divisions, games_per_team='162')).payload()
check("teams sort by record", [t['abbreviation'] for t in regular['teams']] == ['BBB', 'AAA', 'CCC'])
check("records attach by abbreviation", (regular['teams'][0]['wins'], regular['teams'][0]['losses']) == (50, 30))
check("games played and the schedule length", (regular['games_played'], regular['games_per_team']) == (80, 162))

# THE TITLE OUTRANKS THE BEST RECORD
complete = LeagueListItem(row(current_season_status='complete', teams=teams, standing_divisions=divisions, champion_team_id='id-CCC')).payload()
check("the champion leads, whatever its record", complete['teams'][0]['abbreviation'] == 'CCC' and complete['teams'][0]['is_champion'])
check("only the champion is marked", sum(t['is_champion'] for t in complete['teams']) == 1)

if failures:
    print(f"\n{len(failures)} CHECK(S) FAILED:")
    for line in failures:
        print(f"  - {line}")
    sys.exit(1)
print("\nAll checks passed.")
