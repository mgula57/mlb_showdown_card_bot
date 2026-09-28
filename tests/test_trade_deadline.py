"""Offline checks for the in-sim trade deadline (`config.enable_trade_deadline`).

No database, no network. The planner is exercised with lightweight fake cards/schedule; the
roster surgery and `apply()` use real `SimTeam`s built from the same replacement-level stub cards
`test_manager_preference.py` uses. Run as `python tests/test_trade_deadline.py`.

Under test:
  1. DEADLINE DATE - era boundary (mid-June pre-1986, July 31 since).
  2. PLANNER - trivial-stint floor, 3-team collapse to first/last, takeover exclusion, unknown
     club skipped, and the happy path (start on origin, one queued move).
  3. ROSTER SURGERY - `release_player` detaches and returns the player (or None when injured);
     `acquire_player` lands him on the new club; the object is on exactly one roster afterward.
  4. APPLY - a queued move relocates the player mid-season; the standings gate holds a
     contender's player; the pass is deterministic (no rng, repeatable).
"""

import os
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from mlb_showdown_bot.core.card.sets import Set
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.core.card.stats.stats_period import StatsPeriod, StatsPeriodType
from mlb_showdown_bot.core.data.replacement_season_averages import build_replacement_level_stats_for_card
from mlb_showdown_bot.core.shared.player_position import Position
from mlb_showdown_bot.core.simulation.models import SimTeamIdentity
from mlb_showdown_bot.core.simulation.team import SimTeam
from mlb_showdown_bot.core.simulation.trade_deadline import TradeDeadline

YEAR = 2023
LINEUP_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]

failures: list[str] = []
_card_cache: dict[tuple, ShowdownPlayerCard] = {}


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
        _card_cache[key] = ShowdownPlayerCard(
            name=name, year=str(YEAR), set=Set._2000, stats=stats,
            stats_period=StatsPeriod(year=str(YEAR), type=StatsPeriodType.REPLACEMENT),
        )
    return _card_cache[key].model_copy(deep=True)


def build_team(abbreviation: str) -> SimTeam:
    cards: dict[str, ShowdownPlayerCard] = {}
    lineup: list[tuple[str, str]] = []
    for position in LINEUP_POSITIONS:
        player_id = f"{abbreviation}-{position}"
        cards[player_id] = stub_card(f"{abbreviation} {position}", position)
        lineup.append((player_id, position))
    starter_id = f"{abbreviation}-SP"
    cards[starter_id] = stub_card(f"{abbreviation} SP", "STARTER")
    bullpen_ids = []
    for index in range(1, 5):
        reliever_id = f"{abbreviation}-RP{index}"
        cards[reliever_id] = stub_card(f"{abbreviation} RP{index}", "RELIEVER")
        bullpen_ids.append(reliever_id)
    return SimTeam.from_mlb_game_roster(
        year=YEAR, cards=cards,
        identity=SimTeamIdentity(abbreviation=abbreviation, name=abbreviation),
        lineup=lineup, starting_pitcher_id=starter_id,
        position_player_ids=[pid for pid, _ in lineup], bullpen_ids=bullpen_ids,
    )


# ----------------------------------------------------------
# MARK: - DEADLINE DATE
# ----------------------------------------------------------

print("\nDeadline date")
check("1985 -> mid-June", TradeDeadline.deadline_date_for(1985) == date(1985, 6, 15))
check("1986 -> July 31", TradeDeadline.deadline_date_for(1986) == date(1986, 7, 31))
check("2023 -> July 31", TradeDeadline.deadline_date_for(2023) == date(2023, 7, 31))


# ----------------------------------------------------------
# MARK: - PLANNER
# ----------------------------------------------------------

print("\nPlanner")

CLUBS = ["AAA", "BBB", "CCC", "DDD"]


def fake_card(card_id: str, team: str):
    return SimpleNamespace(id=card_id, team=SimpleNamespace(value=team))


def fake_config(*, year=YEAR, takeover_abbrs=(), respect_standings=False):
    """Only the surface `TradeDeadline` reads: `year`, `all_takeovers`, `trade_deadline_respects_standings`."""
    return SimpleNamespace(
        year=year,
        all_takeovers={abbr: SimpleNamespace() for abbr in takeover_abbrs},
        trade_deadline_respects_standings=respect_standings,
    )


def plan_for(history: dict[str, tuple[list[str], dict[str, int]]], *, takeover_abbrs=(), year=YEAR):
    cards_by_player_id = {pid: fake_card(f"card-{pid}", team_list[-1]) for pid, (team_list, _) in history.items()}
    archive_card_ids = {c.id: f"sim-{pid}" for pid, c in cards_by_player_id.items()}
    card_pool = SimpleNamespace(
        team_history=history, cards_by_player_id=cards_by_player_id, archive_card_ids=archive_card_ids,
    )
    schedule = SimpleNamespace(unique_team_names=list(CLUBS), original_games_per_team=162)
    config = fake_config(year=year, takeover_abbrs=takeover_abbrs)
    return TradeDeadline(config=config, schedule=schedule, card_pool=card_pool).plan


# Happy path: a genuine mid-season split -> start on origin, one queued move.
p = plan_for({"p1": (["AAA", "BBB"], {"AAA": 70, "BBB": 80})})
check("happy path: rostered under origin", p.initial_team_by_card_id.get("card-p1") == "AAA")
check("happy path: one move queued", len(p.pending_moves) == 1)
check("happy path: move is AAA -> BBB", p.pending_moves and (p.pending_moves[0].origin, p.pending_moves[0].destination) == ("AAA", "BBB"))
check("happy path: move carries the sim id", p.pending_moves and p.pending_moves[0].sim_player_id == "sim-p1")

# Trivial stint: 4 games for the origin -> pinned to primary club, no move.
p = plan_for({"p2": (["AAA", "BBB"], {"AAA": 4, "BBB": 150})})
check("trivial origin stint: no move queued", len(p.pending_moves) == 0)
check("trivial origin stint: pinned to primary (BBB, already card.team) -> no override", "card-p2" not in p.initial_team_by_card_id)

# Trivial stint where primary != card.team: override, still no move.
p = plan_for({"p3": (["AAA", "BBB"], {"AAA": 150, "BBB": 5})})
check("trivial dest stint: no move", len(p.pending_moves) == 0)
check("trivial dest stint: pinned to primary AAA", p.initial_team_by_card_id.get("card-p3") == "AAA")

# 3-team player collapses to first -> last.
p = plan_for({"p4": (["AAA", "CCC", "DDD"], {"AAA": 50, "CCC": 40, "DDD": 60})})
check("3-team: starts on first (AAA)", p.initial_team_by_card_id.get("card-p4") == "AAA")
check("3-team: single move AAA -> DDD", p.pending_moves and (p.pending_moves[0].origin, p.pending_moves[0].destination) == ("AAA", "DDD"))

# Takeover club on either end -> skipped entirely.
p = plan_for({"p5": (["AAA", "BBB"], {"AAA": 70, "BBB": 80})}, takeover_abbrs=["BBB"])
check("takeover destination: no move", len(p.pending_moves) == 0)
check("takeover destination: no override", "card-p5" not in p.initial_team_by_card_id)

# Unknown club (not in the schedule) -> skipped.
p = plan_for({"p6": (["AAA", "ZZZ"], {"AAA": 70, "ZZZ": 80})})
check("unknown club: no move", len(p.pending_moves) == 0)

# Deterministic: two builds of the same plan are identical.
h = {"p1": (["AAA", "BBB"], {"AAA": 70, "BBB": 80}), "p4": (["AAA", "CCC", "DDD"], {"AAA": 50, "CCC": 40, "DDD": 60})}
a, b = plan_for(h), plan_for(h)
check("planner is deterministic", a.initial_team_by_card_id == b.initial_team_by_card_id and
      [(m.origin, m.destination, m.sim_player_id) for m in a.pending_moves] ==
      [(m.origin, m.destination, m.sim_player_id) for m in b.pending_moves])


# ----------------------------------------------------------
# MARK: - ROSTER SURGERY
# ----------------------------------------------------------

print("\nRoster surgery")

origin = build_team("AAA")
dest = build_team("BBB")
traded_id = "AAA-CF"

before_origin = {p.id for p in origin.active_players}
before_dest = {p.id for p in dest.active_players}
check("target starts on origin", traded_id in before_origin)

player = origin.release_player(traded_id)
check("release returns the player", player is not None and player.id == traded_id)
check("release detaches from origin", traded_id not in {p.id for p in origin.active_players})

dest.acquire_player(player)
check("acquire lands on destination", traded_id in {p.id for p in dest.active_players})
check("player is on exactly one roster", (traded_id in {p.id for p in dest.active_players}) and (traded_id not in {p.id for p in origin.active_players}))
check("destination keeps its own players", before_dest <= {p.id for p in dest.active_players})

# A pitcher move keeps the origin bullpen non-empty (backfill or graceful shrink) and never raises.
origin2 = build_team("CCC")
rp = origin2.release_player("CCC-RP2")
check("release a reliever returns him", rp is not None and rp.id == "CCC-RP2")
check("origin bullpen still has arms", len(origin2.bullpen.players) >= 1)

# Missing id -> None, nothing mutated.
snapshot = {p.id for p in origin.active_players}
check("release of unknown id returns None", origin.release_player("NOBODY") is None)
check("release of unknown id is a no-op", snapshot == {p.id for p in origin.active_players})


# ----------------------------------------------------------
# MARK: - APPLY
# ----------------------------------------------------------

print("\nApply")


class FakeStandings:
    """Minimal `Standings` surface `_is_contending` reads: `teams`, `team_leagues`, `divisions_dict`."""

    def __init__(self, records: dict[str, tuple[int, int]], leagues: dict[str, str], divisions: dict[str, list[str]]):
        self.teams = {abbr: SimpleNamespace(
            name=abbr, wins=w, losses=l, win_pct=round(w / max(w + l, 1), 3),
        ) for abbr, (w, l) in records.items()}
        self.team_leagues = leagues
        self.divisions_dict = {d: {abbr: self.teams[abbr] for abbr in abbrs} for d, abbrs in divisions.items()}


def run_apply(respect_standings: bool, origin_record=(40, 65)):
    teams = {"AAA": build_team("AAA"), "BBB": build_team("BBB")}
    teams["AAA"].wins, teams["AAA"].losses = origin_record
    teams["BBB"].wins, teams["BBB"].losses = (80, 25)
    config = fake_config(respect_standings=respect_standings)
    schedule = SimpleNamespace(unique_team_names=["AAA", "BBB"], original_games_per_team=162)
    card = fake_card("card-x", "BBB")
    card_pool = SimpleNamespace(
        team_history={"x": (["AAA", "BBB"], {"AAA": 70, "BBB": 80})},
        cards_by_player_id={"x": card},
        archive_card_ids={"card-x": "AAA-CF"},   # SIM ID == A REAL SLOT ON THE AAA STUB ROSTER
    )
    td = TradeDeadline(config=config, schedule=schedule, card_pool=card_pool)
    standings = FakeStandings(
        records={"AAA": origin_record, "BBB": (80, 25)},
        leagues={"AAA": "AL", "BBB": "AL"},
        divisions={"AL EAST": ["AAA", "BBB"]},
    )
    trades = td.apply(standings, teams, date(YEAR, 8, 1))
    return teams, trades, td


teams, trades, td = run_apply(respect_standings=False)
check("apply: one trade recorded", len(trades) == 1)
check("apply: player left AAA", "AAA-CF" not in {p.id for p in teams["AAA"].active_players})
check("apply: player joined BBB", "AAA-CF" in {p.id for p in teams["BBB"].active_players})
check("apply: trade records from/to", trades and (trades[0].from_team, trades[0].to_team) == ("AAA", "BBB"))
check("apply: trade records the deadline-day records", trades and trades[0].from_team_record == "40-65")
check("apply: idempotent flag set", td.applied)

# Standings gate ON, selling club is buried -> trade still happens.
teams, trades, _ = run_apply(respect_standings=True, origin_record=(40, 65))
check("gate on, seller buried: trade happens", len(trades) == 1 and "AAA-CF" in {p.id for p in teams["BBB"].active_players})

# Standings gate ON, selling club is right behind the leader -> player held.
teams, trades, _ = run_apply(respect_standings=True, origin_record=(78, 27))
check("gate on, seller contending: player held", len(trades) == 0 and "AAA-CF" in {p.id for p in teams["AAA"].active_players})

# apply() takes no rng and repeats identically.
t1, r1, _ = run_apply(respect_standings=False)
t2, r2, _ = run_apply(respect_standings=False)
check("apply is deterministic", [(t.player_id, t.from_team, t.to_team) for t in r1] == [(t.player_id, t.from_team, t.to_team) for t in r2])


# ----------------------------------------------------------

if failures:
    print(f"\n{len(failures)} CHECK(S) FAILED:")
    for line in failures:
        print(f"  - {line}")
    sys.exit(1)
print("\nAll checks passed.")
