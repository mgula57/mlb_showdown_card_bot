"""Offline checks for live games - games people play by hand, a seat each.

No database, no network: the clubs are the same stub teams `test_faceoff.py` builds, frozen into
card snapshots the way a live game stores them, and a historical club is served by a stubbed
`SyntheticTeams`. Runs as `python tests/test_live_game.py`.

Under test:
  1. ENGINE - the sim's own manager is unchanged by the controller seam (Faceoff results match).
  2. TURNS - the defense rolls the pitch and the offense the swing, alternating to a final, and a
     game waiting on a swing already knows the pitch.
  3. REPLAY - the same actions always rebuild the same game.
  4. MOVES - a pitching change and a pinch hitter land where they should, and the box score
     carries the sub; illegal moves are refused.
  5. AUTOPILOT - a side on autopilot is never waited on; the idle timer switches it on only when
     set; a seat the sim plays is never waited on and can't be taken off autopilot.
  6. API - every way to fill the seats (an invite to bring a team, an invite to a picked team, the
     sim, yourself, a club from history), played to a final through the routes, against an
     in-memory database; the context hook sees the final.
  7. FACEOFF - a Faceoff is one user of live games: an instant one plays the same game as a live game
     with the sim in both seats, and one played by hand is stored as a Faceoff at its final out.
"""

import copy
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(os.path.dirname(__file__)).parent))
sys.path.insert(0, os.path.dirname(__file__))

import test_faceoff as tf
from flask import Flask, g

import mlb_showdown_bot.api.live_games as live_api
import mlb_showdown_bot.api.sim as sim_api
import mlb_showdown_bot.core.simulation.live_contexts as live_contexts

from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.core.card.team_builder.team import Team
from mlb_showdown_bot.core.simulation.controller import RollKind
from mlb_showdown_bot.core.simulation.live_game import (
    LiveAction,
    LiveActionKind,
    LiveMatch,
    LiveMatchError,
    LiveMatchSettings,
    LiveMatchState,
    LiveSide,
)
from mlb_showdown_bot.core.simulation.matchup import MatchupClub

check = tf.check
AWAY, HOME = LiveSide.AWAY, LiveSide.HOME


def with_bench(row: dict, prefix: str) -> dict:
    """The stub team plus two bench outfielders, so there's someone to pinch hit."""
    bench = [{"card_id": f"{prefix}BE{i}", "card_source": "BOT", "roster_position": "BE"} for i in (1, 2)]
    return {**row, "roster": [*row["roster"], *bench]}


CHALLENGER = with_bench(tf.CHALLENGER, "a")
OPPONENT = with_bench(tf.OPPONENT, "b")


def frozen_cards(rows: list[dict]) -> dict[str, ShowdownPlayerCard]:
    """Round-trip each card through JSON, as a stored live game would."""
    cards = tf.stub_cards([slot for slot in rows if slot["roster_position"] != "BE"])
    cards.update({slot["card_id"]: tf.stub_card(slot["card_id"], "LF") for slot in rows if slot["roster_position"] == "BE"})
    return {card_id: ShowdownPlayerCard(**card.model_dump(mode='json')) for card_id, card in cards.items()}


def match(seed: int = 7, sim_sides: frozenset = frozenset(), every_roll_by_hand: bool = False) -> LiveMatch:
    return LiveMatch(
        clubs={AWAY: tf.entrant(CHALLENGER), HOME: tf.entrant(OPPONENT)},
        cards={AWAY: frozen_cards(CHALLENGER["roster"]), HOME: frozen_cards(OPPONENT["roster"])},
        seed=seed, sim_sides=sim_sides, every_roll_by_hand=every_roll_by_hand,
    )


def roll(state: LiveMatchState) -> LiveAction:
    return LiveAction(side=state.pending.side, kind=LiveActionKind.ROLL, roll=state.pending.roll)


def play_out(live: LiveMatch, actions: list[LiveAction]) -> tuple[list[LiveAction], LiveMatchState]:
    """Make every roll the game asks for until it's over."""
    state = live.replay(actions)
    while not state.is_final:
        actions = [*actions, roll(state)]
        state = live.replay(actions)
    return actions, state


def refused(live: LiveMatch, actions: list[LiveAction], action: LiveAction) -> bool:
    try:
        live.apply(actions, action)
    except LiveMatchError:
        return True
    return False


def test_turns() -> None:
    print("\nTURNS")
    live = match()
    state = live.replay([])
    check("the game opens waiting on the home club's pitch", state.pending.side == HOME and state.pending.roll == RollKind.PITCH, str(state.pending))

    actions = [roll(state)]
    state = live.replay(actions)
    check("then on the visitors' swing", state.pending.side == AWAY and state.pending.roll == RollKind.SWING, str(state.pending))
    check("a game waiting on a swing knows the pitch", state.pending.pitch_roll is not None and state.pending.hitter_id is not None)
    check("the batter at the plate is locked in", state.sides[AWAY].at_bat_id == state.pending.hitter_id)
    check("a game in progress names both clubs", state.game.home_team_identity is not None and state.game.away_team_identity is not None)

    actions, final = play_out(live, actions)
    check("rolling every die reaches a final with a winner", final.is_final and final.winner_side is not None)
    winner_score = final.game.home_score if final.winner_side == HOME else final.game.away_score
    loser_score = final.game.away_score if final.winner_side == HOME else final.game.home_score
    check("the winner scored more", winner_score > loser_score, f"{winner_score}-{loser_score}")
    pitch_rolls = sum(1 for a in actions if a.roll == RollKind.PITCH)
    check("one pitch roll per plate appearance", pitch_rolls == len(final.game.log), f"{pitch_rolls} rolls, {len(final.game.log)} plays")
    check("a final carries both box scores", final.game.home_box_score is not None and final.game.away_box_score is not None)


def first_throw(kind: RollKind, seeds=range(1, 60)) -> tuple[LiveMatch, list[LiveAction], LiveMatchState]:
    """The first game (by seed) that stops on `kind`, with the actions that got it there."""
    for seed in seeds:
        live, actions = match(seed=seed), []
        state = live.replay(actions)
        while not state.is_final:
            if state.pending.roll == kind:
                return live, actions, state
            actions = [*actions, roll(state)]
            state = live.replay(actions)
    raise AssertionError(f"no game stopped on a {kind.value} throw")


def test_throws() -> None:
    print("\nTHROWS")
    for kind in (RollKind.STEAL, RollKind.ADVANCE):
        live, actions, state = first_throw(kind)
        pending = state.pending
        fielding = HOME if state.situation.is_top else AWAY
        check(f"the fielding club throws on a {kind.value}", pending.side == fielding, str(pending))
        check(f"a {kind.value} throw names the runner and the test", pending.runner_id is not None and pending.defense is not None and pending.target is not None, str(pending))
        check(f"the batter is locked in during a {kind.value}", state.sides[fielding.other].at_bat_id == pending.hitter_id)
        check(f"the batting club can't throw a {kind.value}", refused(live, actions, LiveAction(side=fielding.other, kind=LiveActionKind.ROLL, roll=kind)))
        if kind == RollKind.ADVANCE:
            check("the swing is shown before the extra-base throw", state.play_in_progress is not None and state.play_in_progress.swing_roll == pending.swing_roll and pending.swing_roll)
        log_count = len(state.game.log)
        state = live.replay([*actions, roll(state)])
        check(f"the {kind.value} throw resolves", state.pending is None or state.pending.roll != kind or len(state.game.log) > log_count)

    live = match(seed=11)
    actions, final = play_out(live, [])
    steals = sum(len(e.steal_rolls) for e in final.game.log)
    advances = sum(len(e.advance_rolls) for e in final.game.log)
    check("one steal throw per steal attempt", steals == sum(1 for a in actions if a.roll == RollKind.STEAL), f"{steals} attempts")
    check("one extra-base throw per send", advances == sum(1 for a in actions if a.roll == RollKind.ADVANCE), f"{advances} sends")


def test_replay() -> None:
    print("\nREPLAY")
    live = match(seed=11)
    actions, final = play_out(live, [])
    check("the same actions rebuild the same game", match(seed=11).replay(actions).game.log == final.game.log)
    check("the score matches the log", final.game.home_score == final.game.log[-1].home_score)
    check("a different seed plays a different game", play_out(match(seed=12), [])[1].game.log != final.game.log)
    check("a roll out of turn is refused", refused(live, [], LiveAction(side=AWAY, kind=LiveActionKind.ROLL, roll=RollKind.PITCH)))
    check("a move after the final is refused", refused(live, actions, LiveAction(side=AWAY, kind=LiveActionKind.AUTOPILOT, enabled=True)))


def test_moves() -> None:
    print("\nMOVES")
    live = match(seed=3)
    state = live.replay([])

    # PITCHING CHANGE ON THE HOME CLUB'S OWN PITCH TURN: HE FACES THE FIRST BATTER.
    reliever = state.sides[HOME].available_reliever_ids[0]
    change = LiveAction(side=HOME, kind=LiveActionKind.PITCHING_CHANGE, player_id=reliever)
    state = live.apply([], change)
    check("a queued pitching change waits for the roll", state.sides[HOME].queued == [change] and state.sides[HOME].pitcher_id != reliever)
    actions = [change, roll(state)]
    state = live.replay(actions)
    check("it takes effect before that pitch", state.pending.pitcher_id == reliever, f"{state.pending.pitcher_id} != {reliever}")
    check("a reliever who's pitched can't come back in", reliever not in state.sides[HOME].available_reliever_ids)
    check("a second change for the same reliever is refused", refused(live, actions, change))

    # PINCH HIT: THE BATTER AT THE PLATE CAN'T BE PINCH HIT FOR; THE ONE DUE UP NEXT CAN.
    at_bat = state.sides[AWAY].at_bat_id
    bench = state.sides[AWAY].bench_ids
    check("the visitors have a bench", len(bench) > 0, str(bench))
    check("pinch hitting for the batter at the plate is refused", refused(live, actions, LiveAction(side=AWAY, kind=LiveActionKind.PINCH_HIT, player_id=bench[0], for_player_id=at_bat)))

    actions = [*actions, roll(state)]  # THE SWING
    state = live.replay(actions)
    due = state.sides[AWAY].due_up_id
    pinch = LiveAction(side=AWAY, kind=LiveActionKind.PINCH_HIT, player_id=bench[0], for_player_id=due)
    state = live.apply(actions, pinch)
    actions = [*actions, pinch, roll(state)]  # THE NEXT PITCH, WHICH LOCKS IN THE MATCHUP
    state = live.replay(actions)
    check("the pinch hitter bats for the player named", state.pending.hitter_id == bench[0], f"{state.pending.hitter_id} != {bench[0]}")
    check("he takes the slot in the lineup", bench[0] in state.sides[AWAY].lineup_ids and due not in state.sides[AWAY].lineup_ids)
    check("the replaced player can't come back", due not in state.sides[AWAY].bench_ids)

    actions, final = play_out(live, actions)
    sub_rows = [line for line in final.game.away_box_score.batting if line.is_substitute]
    check("the box score lists the pinch hitter as a sub", any(line.id == bench[0] for line in sub_rows), str([l.id for l in sub_rows]))
    replaced = next((line for line in final.game.away_box_score.batting if line.id == due), None)
    check("and keeps the player he replaced", replaced is not None and not replaced.is_in_lineup)


def test_autopilot() -> None:
    print("\nAUTOPILOT")
    live = match(seed=5)
    actions = [LiveAction(side=HOME, kind=LiveActionKind.AUTOPILOT, enabled=True)]
    state = live.replay(actions)
    check("a side on autopilot is never waited on", state.pending.side == AWAY, str(state.pending))
    actions, final = play_out(live, actions)
    check("the game still reaches a final", final.is_final)
    check("only the other side rolled", all(a.side == AWAY for a in actions if a.kind == LiveActionKind.ROLL))
    both = [LiveAction(side=s, kind=LiveActionKind.AUTOPILOT, enabled=True) for s in LiveSide]
    check("both sides on autopilot plays straight through", live.replay(both).is_final)

    against_sim = match(seed=5, sim_sides=frozenset({HOME}))
    state = against_sim.replay([])
    check("a seat the sim plays is on autopilot from the first pitch", state.sides[HOME].autopilot and state.pending.side == AWAY, str(state.pending))
    check("and can't be taken off it", refused(against_sim, [], LiveAction(side=HOME, kind=LiveActionKind.AUTOPILOT, enabled=False)))
    check("nor moved for", refused(against_sim, [], LiveAction(side=HOME, kind=LiveActionKind.PITCHING_CHANGE, player_id=state.sides[HOME].available_reliever_ids[0])))
    check("a game against the sim plays to a final", play_out(against_sim, [])[1].is_final)

    state = live.replay([])
    then = datetime.now(timezone.utc) - timedelta(minutes=30)
    check("no idle timer, no autopilot", LiveMatch.idle_autopilot_action(state, LiveMatchSettings(), then) is None)
    owed = LiveMatch.idle_autopilot_action(state, LiveMatchSettings(idle_autopilot_minutes=10), then)
    check("an expired timer switches the waited-on side to autopilot", owed is not None and owed.side == state.pending.side and owed.by_timeout)
    check("a running timer doesn't", LiveMatch.idle_autopilot_action(state, LiveMatchSettings(idle_autopilot_minutes=60), then) is None)

    by_hand = match(seed=5, sim_sides=frozenset({HOME}), every_roll_by_hand=True)
    state = by_hand.replay([])
    check("by hand, the sim's seat waits for its roll", state.pending.side == HOME and state.pending.roll == RollKind.PITCH, str(state.pending))
    check("an autopilot side's roll owes no idle autopilot", LiveMatch.idle_autopilot_action(state, LiveMatchSettings(idle_autopilot_minutes=10), then) is None)
    check("the sim's roll can be made", not refused(by_hand, [], roll(state)))
    check("but it still can't be moved for", refused(by_hand, [], LiveAction(side=HOME, kind=LiveActionKind.PITCHING_CHANGE, player_id=state.sides[HOME].available_reliever_ids[0])))
    actions, final = play_out(by_hand, [])
    check("by hand, both sides roll to a final", final.is_final and {a.side for a in actions} == {AWAY, HOME})
    check("and it's the same game as the sim rolling for itself", final.game.home_score == play_out(against_sim, [])[1].game.home_score)


def test_engine_unchanged() -> None:
    print("\nENGINE")
    check("a Faceoff still plays the same game from a seed", tf.play(seed=9).games[0].game.log == tf.play(seed=9).games[0].game.log)


# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------

HISTORICAL_TEAM = with_bench(tf.team_row("33333333-3333-3333-3333-333333333333", "NYY", "h"), "h")


class StubLiveDB:
    """Just enough of `PostgresDB` for the live game routes, kept in memory. Values go through JSON
    on the way in, as JSONB would."""

    teams: dict = {}
    games: dict = {}
    actions: dict = {}

    def __init__(self, *_args, **_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def get_team(self, team_id, user_id):
        row = StubLiveDB.teams.get(team_id)
        return row if row and (row["is_public"] or row["user_id"] == user_id) else None

    def fetch_cards_for_roster_slots(self, slots, strip_diagnostics=False):
        return frozen_cards([slot.model_dump() for slot in slots])

    def fetch_random_historical_team(self, sport_id=1, season=None):
        return {"season": season or 1927, "sport_id": sport_id, "team_id": 147}

    def create_live_game(self, created_by, seats, setup, settings, invite_code=None, context_kind='open', context_ref=None, seed=None, pending_side=None):
        game_id = f"00000000-0000-0000-0000-{len(StubLiveDB.games) + 1:012d}"
        ready = all(side in setup for side in ('away', 'home'))
        row = {
            "live_game_id": game_id, "invite_code": invite_code, "status": 'active' if ready and invite_code is None else 'invited',
            "created_by": created_by, "context_kind": context_kind, "context_ref": context_ref,
            "settings": json.loads(json.dumps(settings)), "setup": json.loads(json.dumps(setup)), "seed": seed, "seq": 0,
            "pending_side": pending_side, "winner_side": None, "result": None, "last_action_at": datetime.now(timezone.utc),
        }
        for side, seat in seats.items():
            row[f"{side}_controller"] = seat["controller"]
            row[f"{side}_user_id"] = seat.get("user_id")
            row[f"{side}_team_ref"] = json.loads(json.dumps(seat.get("team_ref")))
        StubLiveDB.games[game_id] = row
        StubLiveDB.actions[game_id] = []
        return game_id

    def fetch_live_game(self, live_game_id=None, invite_code=None, include_setup=True):
        row = StubLiveDB.games.get(live_game_id) if live_game_id else next((r for r in StubLiveDB.games.values() if r["invite_code"] == invite_code), None)
        return copy.deepcopy(row) if row else None

    def accept_live_game(self, live_game_id, side, user_id, seed, pending_side, side_setup=None, team_ref=None):
        row = StubLiveDB.games[live_game_id]
        if row["status"] != "invited" or row[f"{side}_user_id"] is not None:
            return False
        row.update({f"{side}_user_id": user_id, "seed": seed, "status": "active", "pending_side": pending_side})
        if team_ref:
            row[f"{side}_team_ref"] = json.loads(json.dumps(team_ref))
        if side_setup:
            row["setup"][side] = json.loads(json.dumps(side_setup))
        return True

    def fetch_live_game_actions(self, live_game_id):
        return copy.deepcopy(StubLiveDB.actions[live_game_id])

    def append_live_game_action(self, live_game_id, expected_seq, user_id, action, pending_side, final=None, on_final=None):
        row = StubLiveDB.games[live_game_id]
        if row["seq"] != expected_seq or row["status"] != "active":
            return False
        StubLiveDB.actions[live_game_id].append(json.loads(json.dumps(action)))
        row.update(seq=expected_seq + 1, pending_side=pending_side, last_action_at=datetime.now(timezone.utc))
        if final is not None:
            row.update(status="final", winner_side=final["winner_side"], result=final["result"])
            if on_final:
                on_final(FakeCursor())
        return True

    def count_recent_faceoff_games(self, _user_id):
        return 0

    def fetch_live_games_for_user(self, user_id, limit=20, context_kind=None):
        mine = lambda r: user_id in (r["away_user_id"], r["home_user_id"]) or (r["created_by"] == user_id and r["status"] == "invited")
        return [copy.deepcopy(r) for r in StubLiveDB.games.values() if mine(r) and r["status"] != "cancelled"]


class FakeCursor:
    """Stands in for the transaction's cursor: applies the one statement a context runs directly."""

    def execute(self, query, params):
        if "SET context_ref" in query:
            StubLiveDB.games[params[1]]["context_ref"] = params[0]


ALICE, BOB, CAROL = "user-alice", "user-bob", "user-carol"
viewer = {"user": None}


def call(route, path: str = "/x", method: str = "GET", body: dict | None = None, user: str | None = None, **kwargs) -> tuple[int, dict]:
    viewer["user"] = user
    with Flask(__name__).test_request_context(path, method=method, json=body):
        g.user_id = user
        response = getattr(route, "__wrapped__", route)(**kwargs)
    response, status = response if isinstance(response, tuple) else (response, 200)
    return status, response.get_json()


def create(user: str, body: dict) -> tuple[int, dict]:
    return call(live_api.create_live_game, "/api/sim/live", "POST", body, user=user)


def play_through_api(game_id: str, players: dict[str, str]) -> tuple[dict, int]:
    """Roll whatever the game waits on, as whoever plays that seat, until it's final."""
    _, data = call(live_api.get_live_game, user=next(iter(players.values())), live_game_id=game_id)
    moves = 0
    while data["state"]["pending"] is not None and moves < 400:
        pending = data["state"]["pending"]
        status, data = call(live_api.post_live_game_action, method="POST", user=players[pending["side"]], live_game_id=game_id,
                            body={"expected_seq": data["state"]["seq"], "action": {"side": pending["side"], "kind": "roll", "roll": pending["roll"]}})
        if status != 200:
            check("every roll in turn is accepted", False, f"{status} {data}")
            break
        moves += 1
    return data, moves


def test_api() -> None:
    print("\nAPI")
    live_api.PostgresDB = sim_api.PostgresDB = StubLiveDB
    live_api.optional_user_id = lambda: viewer["user"]
    broadcasts = []
    live_api._broadcast_seq = lambda game_id, seq: broadcasts.append(seq)
    history_calls = []
    live_api.SyntheticTeams.historical = classmethod(
        lambda cls, season, team_id, sport_id=1, showdown_set='2000', **_: history_calls.append((season, team_id)) or {
            **Team.from_db_row({**HISTORICAL_TEAM, "name": f"{season} Yankees", "team_id": None, "user_id": None}).model_dump(mode='json'),
            "total_points": 4800,
        }
    )
    finals = []

    class RecordingContext(live_api.LiveGameContext):
        kind = 'open'

        def on_final(self, cur, row, state):
            finals.append((row["live_game_id"], state.winner_side))

    live_api._CONTEXTS['open'] = RecordingContext()
    StubLiveDB.teams = {tf.CHALLENGER_ID: {**CHALLENGER, "user_id": ALICE}, tf.OPPONENT_ID: {**OPPONENT, "user_id": BOB}}
    alice_team = {"kind": "saved", "team_id": tf.CHALLENGER_ID}
    bob_team = {"kind": "saved", "team_id": tf.OPPONENT_ID}

    # INVITE, BRING YOUR OWN TEAM.
    status, created = create(ALICE, {"team": alice_team})
    check("an invite opens with a team in your seat", status == 201 and created["invite_code"], str(created))
    check("a game needs your team", create(ALICE, {})[0] == 400)
    check("the sim needs a team to play", create(ALICE, {"team": alice_team, "opponent": {"controller": "sim"}})[0] == 400)
    check("an unknown idle timer is refused", create(ALICE, {"team": alice_team, "idle_autopilot_minutes": 7})[0] == 400)
    code, game_id = created["invite_code"], created["live_game_id"]

    status, invite = call(live_api.get_live_game_invite, user=BOB, invite_code=code)
    check("the invite offers the home seat to bring a team to", status == 200 and invite["open_side"] == "home" and invite["open_seat_team_ref"] is None, str(invite)[:200])
    check("bringing nothing is refused", call(live_api.accept_live_game, method="POST", body={}, user=BOB, invite_code=code)[0] == 400)
    check("bringing the inviter's own team is refused", call(live_api.accept_live_game, method="POST", body={"team": alice_team}, user=BOB, invite_code=code)[0] in (400, 404))
    status, _ = call(live_api.accept_live_game, method="POST", body={"team": bob_team}, user=BOB, invite_code=code)
    check("accepting with your own team starts the game", status == 200 and StubLiveDB.games[game_id]["status"] == "active")
    check("the seat can only be taken once", call(live_api.accept_live_game, method="POST", body={"team": bob_team}, user=CAROL, invite_code=code)[0] == 410)

    status, watched = call(live_api.get_live_game, user=CAROL, live_game_id=game_id)
    check("anyone with the link can watch", status == 200 and watched["my_sides"] == [] and watched["state"]["pending"] is not None)
    check("a spectator never sees the invite code", watched["invite_code"] is None)
    pending = watched["state"]["pending"]
    act = {"expected_seq": 0, "action": {"side": pending["side"], "kind": "roll", "roll": pending["roll"]}}
    wrong = ALICE if pending["side"] == "home" else BOB
    check("a roll for the other seat is refused", call(live_api.post_live_game_action, method="POST", body=act, user=wrong, live_game_id=game_id)[0] == 403)
    check("a spectator can't move", call(live_api.post_live_game_action, method="POST", body=act, user=CAROL, live_game_id=game_id)[0] == 403)
    check("a stale seq is refused", call(live_api.post_live_game_action, method="POST", body={**act, "expected_seq": 3}, user=BOB, live_game_id=game_id)[0] == 409)
    check("polling an unchanged game is cheap", call(live_api.get_live_game, "/x?since=0", user=CAROL, live_game_id=game_id)[1].get("unchanged") is True)

    data, moves = play_through_api(game_id, {"away": ALICE, "home": BOB})
    check("rolling in turn plays to a final", data["status"] == "final" and data["state"]["is_final"], data["status"])
    check("the result is stored on the game", StubLiveDB.games[game_id]["result"] is not None and StubLiveDB.games[game_id]["winner_side"] in ("away", "home"))
    check("the game's context records the final", finals == [(game_id, data["state"]["winner_side"])], str(finals))
    check("every move was broadcast", len(broadcasts) == moves + 1, f"{len(broadcasts)} vs {moves + 1}")
    status, cards = call(live_api.get_live_game_cards, user=CAROL, live_game_id=game_id)
    check("the game's cards are served from its snapshot", status == 200 and len(cards["cards"]) == len(CHALLENGER["roster"]) * 2)

    # INVITE TO A TEAM THE CREATOR PICKED: A CLUB FROM HISTORY, PLAYED BY A FRIEND.
    status, created = create(ALICE, {"team": alice_team, "my_side": "home", "opponent": {"controller": "invite", "team": {"kind": "historical", "season": 1927, "team_id": 147}}})
    check("an invite can offer a club from history", status == 201 and history_calls[-1] == (1927, 147), str(created))
    status, invite = call(live_api.get_live_game_invite, user=BOB, invite_code=created["invite_code"])
    check("the seat on offer comes with that club", invite["open_side"] == "away" and invite["seats"]["away"]["identity"]["name"] == "1927 Yankees", str(invite)[:200])
    status, _ = call(live_api.accept_live_game, method="POST", body={}, user=BOB, invite_code=created["invite_code"])
    check("taking it needs no team of your own", status == 200)
    data, _ = play_through_api(created["live_game_id"], {"home": ALICE, "away": BOB})
    check("and plays to a final", data["status"] == "final")

    # AGAINST THE SIM, WITH A CLUB PICKED AT RANDOM FROM HISTORY: NO INVITE, IT STARTS AT ONCE.
    status, created = create(ALICE, {"team": alice_team, "opponent": {"controller": "sim", "team": {"kind": "random_historical"}}})
    check("a game against the sim starts at once", status == 201 and created["invite_code"] is None and StubLiveDB.games[created["live_game_id"]]["status"] == "active", str(created))
    check("the random club is stored as the club it landed on", StubLiveDB.games[created["live_game_id"]]["home_team_ref"]["kind"] == "historical")
    _, data = call(live_api.get_live_game, user=ALICE, live_game_id=created["live_game_id"])
    check("the sim's seat waits for its roll", data["state"]["pending"]["side"] == "home" and data["seats"]["home"]["controller"] == "sim", str(data["state"]["pending"]))
    pending = data["state"]["pending"]
    sim_roll = {"expected_seq": 0, "action": {"side": "home", "kind": "roll", "roll": pending["roll"]}}
    check("a spectator can't roll for the sim", call(live_api.post_live_game_action, method="POST", body=sim_roll, user=CAROL, live_game_id=created["live_game_id"])[0] == 403)
    status, mine = call(live_api.get_my_live_games, user=ALICE)
    check("the sim's roll is the player's turn", any(g_["live_game_id"] == created["live_game_id"] and g_["is_my_turn"] for g_ in mine["games"]))
    data, _ = play_through_api(created["live_game_id"], {"away": ALICE, "home": ALICE})
    check("a game against the sim plays to a final", data["status"] == "final")

    # BOTH SEATS YOURS.
    status, created = create(ALICE, {"team": alice_team, "opponent": {"controller": "me", "team": {"kind": "historical", "season": 1998, "team_id": 147}}})
    _, data = call(live_api.get_live_game, user=ALICE, live_game_id=created["live_game_id"])
    check("you can play both seats", status == 201 and sorted(data["my_sides"]) == ["away", "home"], str(data.get("my_sides")))

    # THE IDLE TIMER.
    _, created = create(ALICE, {"team": alice_team, "idle_autopilot_minutes": 2})
    call(live_api.accept_live_game, method="POST", body={"team": bob_team}, user=BOB, invite_code=created["invite_code"])
    idle_id = created["live_game_id"]
    StubLiveDB.games[idle_id]["last_action_at"] = datetime.now(timezone.utc) - timedelta(minutes=3)
    _, data = call(live_api.get_live_game, user=CAROL, live_game_id=idle_id)
    first = StubLiveDB.actions[idle_id][0] if StubLiveDB.actions[idle_id] else {}
    check("an idle side goes on autopilot when the game is next looked at", first.get("kind") == "autopilot" and first.get("by_timeout") is True, str(first))
    pending = data["state"]["pending"]
    check("and still waits for that side's roll", pending["side"] == first.get("side"), str(pending))
    other = BOB if pending["side"] == "away" else ALICE
    status, _ = call(live_api.post_live_game_action, method="POST", user=other, live_game_id=idle_id,
                     body={"expected_seq": data["state"]["seq"], "action": {"side": pending["side"], "kind": "roll", "roll": pending["roll"]}})
    check("which the other player rolls for it", status == 200, str(status))

    status, mine = call(live_api.get_my_live_games, user=BOB)
    turns = {game["live_game_id"]: game["is_my_turn"] for game in mine["games"]}
    check("a player's games list whose turn it is", status == 200 and turns.get(game_id) is False and turns.get(idle_id) is (StubLiveDB.games[idle_id]["pending_side"] == "home"), str(turns))


def test_faceoff() -> None:
    print("\nFACEOFF")
    from mlb_showdown_bot.core.simulation.live_game import LiveMatch as _LiveMatch
    key = lambda game: [(e.inning, e.is_top, e.pitch_roll, e.swing_roll, e.swing_result, e.away_score, e.home_score) for e in game.log]
    instant = tf.play(seed=21).games[0].game
    as_live = _LiveMatch(
        clubs={AWAY: tf.entrant(tf.CHALLENGER), HOME: tf.entrant(tf.OPPONENT)},
        cards={AWAY: frozen_cards(tf.CHALLENGER["roster"]), HOME: frozen_cards(tf.OPPONENT["roster"])},
        seed=21, sim_sides=frozenset(LiveSide),
    ).replay([])
    check("an instant Faceoff is a live game with the sim in both seats", key(instant) == key(as_live.game))

    recorded = []
    live_contexts.PostgresDB.insert_sim_faceoff = classmethod(lambda cls, cur, user_id, result, is_own_matchup: recorded.append((user_id, result, is_own_matchup)) or "faceoff-1")
    StubLiveDB.teams[tf.OPPONENT_ID] = {**OPPONENT, "user_id": BOB, "is_public": True}
    status, data = call(sim_api.start_faceoff, method="POST", user=ALICE, body={"team_id": tf.CHALLENGER_ID, "opponent_team_id": tf.OPPONENT_ID, "play_live": True})
    check("a Faceoff can be played live", status == 201 and "live_game_id" in data, str(data))
    game_id = data["live_game_id"]
    row = StubLiveDB.games[game_id]
    check("it's a live game in the Faceoff context", row["context_kind"] == "faceoff" and row["status"] == "active")
    check("the challenger is away, the challenged team home and played by the sim", row["away_user_id"] == ALICE and row["home_controller"] == "sim")
    data, _ = play_through_api(game_id, {"away": ALICE, "home": ALICE})
    check("it plays to a final", data["status"] == "final")
    user_id, result, is_own = recorded[-1] if recorded else (None, {}, None)
    winner = "challenger" if data["state"]["winner_side"] == "away" else "opponent"
    check("its final is stored as a Faceoff", user_id == ALICE and result.get("winner_side") == winner and not is_own, str(result.get("winner_side")))
    check("and the game points at it", StubLiveDB.games[game_id]["context_ref"] == "faceoff-1")


if __name__ == "__main__":
    test_engine_unchanged()
    test_turns()
    test_replay()
    test_throws()
    test_moves()
    test_autopilot()
    test_api()
    test_faceoff()
    if tf.failures:
        print(f"\n{len(tf.failures)} check(s) failed:")
        for failure in tf.failures:
            print(f"  - {failure}")
        sys.exit(1)
    print("\nAll live game checks passed.")
