"""Offline checks for Faceoffs - one builder team played against another.

No database, no network: cards are built from `build_replacement_level_stats_for_card`, the same
offline generator the other sim tests use, and the database is stubbed, so this runs as
`python tests/test_faceoff.py` anywhere. The privacy SQL needs a real Postgres and isn't covered.

Five things are under test:
  1. IDENTITY - two teams can share an abbreviation or every card without colliding in the engine.
  2. SETUP - the challenged team is home, a chosen starter starts, and a saved bullpen order and
     closer reach the engine.
  3. DETERMINISM - a seed fully determines a Faceoff.
  4. SERIES - a series stops at a majority of wins and follows the shared 2-3-2 home pattern.
  5. API - `POST /sim/faceoff` enforces who may play whom and how.
"""

import os
import sys
from datetime import date
from pathlib import Path

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from flask import Flask, g

import mlb_showdown_bot.api.sim as sim_api
from mlb_showdown_bot.core.card.sets import Set
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.core.card.stats.stats_period import StatsPeriod, StatsPeriodType
from mlb_showdown_bot.core.card.team_builder.team import CardSource, Team, TeamRosterSlot
from mlb_showdown_bot.core.data.replacement_season_averages import build_replacement_level_stats_for_card
from mlb_showdown_bot.core.database.postgres_db import PostgresDB
from mlb_showdown_bot.core.shared.player_position import Position
from mlb_showdown_bot.core.simulation.faceoff import FaceoffEntrant, FaceoffError, FaceoffSide, TeamMatchupSimulator
from mlb_showdown_bot.core.simulation.postseason import top_seed_is_home
from mlb_showdown_bot.core.simulation.stats import real_card_id
from mlb_showdown_bot.core.simulation.team import SimTeam

YEAR = 2023
LINEUP_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]
CHALLENGER_ID = "11111111-1111-1111-1111-111111111111"
OPPONENT_ID = "22222222-2222-2222-2222-222222222222"
ME = "user-me"
SOMEONE_ELSE = "user-else"

_card_cache: dict[tuple, ShowdownPlayerCard] = {}
failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  PASS  {label}")
    else:
        failures.append(f"{label}{f' -- {detail}' if detail else ''}")
        print(f"  FAIL  {label}{f' -- {detail}' if detail else ''}")


def stub_card(name: str, position: str) -> ShowdownPlayerCard:
    key = (name, position)
    if key not in _card_cache:
        is_pitcher = position in ("STARTER", "RELIEVER")
        stats = build_replacement_level_stats_for_card(
            year=YEAR, player_type="PITCHER" if is_pitcher else "HITTER", positions=[Position(position)],
        )
        stats["name"] = name
        stats["bref_id"] = f"{name.lower()}01"
        _card_cache[key] = ShowdownPlayerCard(
            name=name, year=str(YEAR), set=Set._2000, stats=stats,
            stats_period=StatsPeriod(year=str(YEAR), type=StatsPeriodType.REPLACEMENT),
        )
    return _card_cache[key].model_copy(deep=True)


def roster(prefix: str) -> list[dict]:
    """A full roster as stored rows. A shared `prefix` gives two teams identical cards."""
    slots = [(f"{prefix}{p}", p) for p in LINEUP_POSITIONS]
    slots += [(f"{prefix}SP{i}", f"SP{i}") for i in range(1, 6)]
    slots += [(f"{prefix}RP{i}", "RP") for i in range(1, 6)]
    return [{"card_id": card_id, "card_source": "BOT", "roster_position": pos} for card_id, pos in slots]


def stub_cards(rows: list[dict]) -> dict[str, ShowdownPlayerCard]:
    cards = {}
    for row in rows:
        position = row["roster_position"]
        kind = "STARTER" if position.startswith("SP") else "RELIEVER" if position in ("RP", "CL") else position
        cards[row["card_id"]] = stub_card(row["card_id"], kind)
    return cards


def team_row(team_id: str, abbreviation: str, prefix: str, **overrides) -> dict:
    return {
        "team_id": team_id, "user_id": ME, "name": f"Team {abbreviation}", "abbreviation": abbreviation,
        "roster": roster(prefix), "source": "user", "is_public": True, "is_archived": False, "total_points": 5000,
        **overrides,
    }


def entrant(row: dict, **overrides) -> FaceoffEntrant:
    return FaceoffEntrant(team=Team.from_db_row(row), total_points=row["total_points"], **overrides)


class OfflineSimulator(TeamMatchupSimulator):
    """Serves stub cards instead of reading a roster from the database."""

    def _load_cards(self, team):
        return stub_cards([slot.model_dump() for slot in team.roster])


CHALLENGER = team_row(CHALLENGER_ID, "AAA", "a")
OPPONENT = team_row(OPPONENT_ID, "BBB", "b")


def play(challenger=CHALLENGER, opponent=OPPONENT, seed=1, best_of=1, **challenger_settings):
    return OfflineSimulator(entrant(challenger, **challenger_settings), entrant(opponent), seed=seed, best_of=best_of).simulate()


def test_identity() -> None:
    print("\nIDENTITY")
    game = play().games[0].game
    check("each club is named for its real team", game.away_team_identity.name == "Team AAA" and game.home_team_identity.name == "Team BBB")
    check("the result shows the day played, not the engine's date", game.date == date.today(), str(game.date))

    twin = team_row(OPPONENT_ID, "AAA", "b")
    check("a shared abbreviation still plays", play(opponent=twin).winner_side is not None)

    copy = team_row(OPPONENT_ID, "BBB", "a")
    game = play(opponent=copy).games[0].game
    hitters = {entry.hitter_id for entry in game.log}
    check("shared cards stay on their own side in the engine", any("CHALLENGER" in h for h in hitters) and any("OPPONENT" in h for h in hitters))
    away = {line.id for line in game.away_box_score.batting}
    home = {line.id for line in game.home_box_score.batting}
    check("box scores carry bare card ids", away == home and all(real_card_id(i) == i for i in away))


def test_setup() -> None:
    print("\nSETUP")
    result = play()
    check("the challenged team is home", result.games[0].home_side == FaceoffSide.OPPONENT)
    check("the first starter is the default", result.games[0].game.away_starting_pitcher.id == "aSP1")

    chosen = play(starter_card_id="aSP3").games[0].game
    check("a chosen starter starts", chosen.away_starting_pitcher.id == "aSP3", chosen.away_starting_pitcher.id)
    try:
        play(starter_card_id="bSP1")
        check("a starter from the wrong rotation is refused", False)
    except FaceoffError:
        check("a starter from the wrong rotation is refused", True)
    check("a snapshot keeps the roster and settings", len(result.challenger.roster) == 19 and result.opponent.total_points == 5000)

    ordered_rows = roster("a")
    ordered_rows[-1]["roster_position"] = "CL"
    ordered = Team.from_db_row(team_row(CHALLENGER_ID, "AAA", "a", roster=list(reversed(ordered_rows)), bullpen_order_custom=True))
    default = Team.from_db_row(team_row(CHALLENGER_ID, "AAA", "a", roster=ordered_rows))
    build = lambda team: SimTeam.from_builder_team(team=team, cards=stub_cards([s.model_dump() for s in team.roster]), year=YEAR, name_override="X")
    club, plain = build(ordered), build(default)
    ranked = sorted(club.bullpen.role_order, key=club.bullpen.role_order.get)
    check("a saved bullpen order reaches the engine", [real_card_id(i) for i in ranked] == ["aRP5", "aRP4", "aRP3", "aRP2", "aRP1"], str(ranked))
    check("a team with no saved order keeps the default ranking", plain.bullpen.role_order == {})
    check("a chosen closer closes", real_card_id(club.bullpen.closer.id) == "aRP5")
    check("a closer still counts as bullpen", len(ordered.bullpen) == 5 and "aRP5" not in {s.card_id for s in ordered.starters})


def test_determinism() -> None:
    print("\nDETERMINISM")
    first, again, other = play(seed=7), play(seed=7), play(seed=8)
    check("the same seed plays the same game", first.games[0].game.log == again.games[0].game.log)
    check("a different seed plays a different game", first.games[0].game.log != other.games[0].game.log)


def test_series() -> None:
    print("\nSERIES")
    for seed in range(5):
        series = play(seed=seed, best_of=7)
        wins = (series.challenger_wins, series.opponent_wins)
        check(f"seed {seed}: stops at four wins", max(wins) == 4 and sum(wins) == len(series.games), str(wins))
    homes = [game.home_side.value for game in play(seed=3, best_of=7).games]
    expected = ["opponent" if top_seed_is_home(number, 7) else "challenger" for number in range(1, len(homes) + 1)]
    check("home field follows the shared pattern", homes == expected, str(homes))
    check("the pattern is 2-3-2", [top_seed_is_home(n, 7) for n in range(1, 8)] == [True, True, False, False, False, True, True])
    try:
        OfflineSimulator(entrant(CHALLENGER), entrant(OPPONENT), seed=1, best_of=2)
        check("an even series is refused", False)
    except FaceoffError:
        check("an even series is refused", True)
    check("scores map to sides, whichever is home", (
        PostgresDB._faceoff_game_scores({"home_side": "opponent", "game": {"home_score": 5, "away_score": 2}}) == (2, 5)
        and PostgresDB._faceoff_game_scores({"home_side": "challenger", "game": {"home_score": 5, "away_score": 2}}) == (5, 2)
    ))


class StubDB:
    """The two reads and one write `start_faceoff` makes, recording what was stored."""

    teams: dict[str, dict] = {}
    games_played = 0
    recorded: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def get_team(self, team_id, user_id):
        row = StubDB.teams.get(team_id)
        return row if row and (row["is_public"] or row["user_id"] == user_id) else None

    def count_recent_faceoff_games(self, _user_id):
        return StubDB.games_played

    def record_sim_faceoff(self, user_id, result, is_own_matchup):
        StubDB.recorded.append({"result": result, "is_own_matchup": is_own_matchup})
        return "faceoff-id"


def post(body: dict, user: str = ME) -> tuple[int, dict]:
    with Flask(__name__).test_request_context("/api/sim/faceoff", method="POST", json=body):
        g.user_id = user
        response = sim_api.start_faceoff.__wrapped__()
    response, status = response if isinstance(response, tuple) else (response, 200)
    return status, response.get_json()


def test_api() -> None:
    print("\nAPI")
    sim_api.PostgresDB, sim_api.TeamMatchupSimulator = StubDB, OfflineSimulator
    theirs = team_row(OPPONENT_ID, "BBB", "b", user_id=SOMEONE_ELSE)
    StubDB.teams = {CHALLENGER_ID: CHALLENGER, OPPONENT_ID: theirs}
    base = {"team_id": CHALLENGER_ID, "opponent_team_id": OPPONENT_ID}

    status, _ = post(base)
    check("a public opponent can be played", status == 201, str(status))
    check("it isn't marked as an own-team game", StubDB.recorded[-1]["is_own_matchup"] is False)
    status, _ = post({**base, "opponent_starter_card_id": "not-a-card", "opponent_manager": {"steal_aggression": 5}})
    stored = StubDB.recorded[-1]["result"]["opponent"]
    check("a public opponent can't be managed", status == 201 and stored["starter_card_id"] is None and stored["manager"] is None, str(status))

    check("you can't start with someone else's team", post({"team_id": OPPONENT_ID, "opponent_team_id": CHALLENGER_ID})[0] == 403)
    check("a team can't face itself", post({"team_id": CHALLENGER_ID, "opponent_team_id": CHALLENGER_ID})[0] == 400)
    check("both teams are required", post({"team_id": CHALLENGER_ID})[0] == 400)
    check("a malformed id is unavailable", post({**base, "opponent_team_id": "nope"})[0] == 404)
    check("a series isn't offered yet", post({**base, "best_of": 7})[0] == 400)
    check("a bad manager level is refused", post({**base, "manager": {"steal_aggression": 9}})[0] == 400)
    check("a bad starter is refused", post({**base, "starter_card_id": "not-a-card"})[0] == 400)

    StubDB.teams[OPPONENT_ID] = {**theirs, "is_public": False}
    check("a private opponent is unavailable", post(base)[0] == 404)
    StubDB.teams[OPPONENT_ID] = {**theirs, "is_archived": True}
    check("an archived opponent is unavailable", post(base)[0] == 404)
    StubDB.teams[OPPONENT_ID] = {**theirs, "source": "league"}
    check("a league team is unavailable", post(base)[0] == 404)
    StubDB.teams[OPPONENT_ID] = {**theirs, "roster": roster("b")[1:]}
    check("an incomplete roster is refused", post(base)[0] == 422)

    StubDB.teams[OPPONENT_ID] = team_row(OPPONENT_ID, "BBB", "b", is_public=False)
    status, _ = post({**base, "opponent_starter_card_id": "bSP2"})
    stored = StubDB.recorded[-1]
    check("your own private team can be played", status == 201 and stored["is_own_matchup"] is True, str(status))
    check("you manage both of your own teams", stored["result"]["opponent"]["starter_card_id"] == "bSP2")

    StubDB.games_played = sim_api._FACEOFF_GAMES_PER_HOUR
    check("the hourly limit holds", post(base)[0] == 429)
    StubDB.games_played = 0


if __name__ == "__main__":
    test_identity()
    test_setup()
    test_determinism()
    test_series()
    test_api()
    print()
    if failures:
        print(f"{len(failures)} FAILED")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)
    print("All Faceoff checks passed.")
