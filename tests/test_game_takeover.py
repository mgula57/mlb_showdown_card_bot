"""Offline checks for the single-game engine and its mid-game resume seam.

No database, no network: cards are built from `build_replacement_level_stats_for_card`, which is
the same offline generator `PostgresDB` falls back to for a player with no card. That keeps this
runnable as `python tests/test_game_takeover.py` in any environment.

Two things are under test:
  1. REGRESSION - `Game.setup` with no start state must behave exactly as it did before the
     resume seam existed: first pitch, top of the 1st, both starters on the mound, and the same
     result for the same seed.
  2. TAKEOVER - `Game.setup(start_state=...)` resumes mid-game with the score, inning, outs,
     baserunners, batting order spot, and pitcher workload all carried in.
"""

import os
import sys
from datetime import date
from pathlib import Path
from random import Random

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from mlb_showdown_bot.core.card.sets import Set
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.core.card.stats.stats_period import StatsPeriod, StatsPeriodType
from mlb_showdown_bot.core.data.replacement_season_averages import build_replacement_level_stats_for_card
from mlb_showdown_bot.core.shared.player_position import Position
from mlb_showdown_bot.core.simulation.game import Game
from mlb_showdown_bot.core.simulation.models import (
    CompletedHalfInning,
    GameStartState,
    PitcherAppearance,
    SimTeamIdentity,
    TeamStartState,
)
from mlb_showdown_bot.core.simulation.runners import Runner, Runners
from mlb_showdown_bot.core.simulation.team import SimTeam

YEAR = 2023
GAME_DATE = date(YEAR, 6, 15)

# ONE STUB CARD PER LINEUP SLOT, IN BATTING ORDER. THE POSITION DOUBLES AS THE PLAYER'S NAME SO A
# FAILURE MESSAGE SAYS WHICH SLOT BROKE.
LINEUP_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]

_card_cache: dict[tuple, ShowdownPlayerCard] = {}


def stub_card(name: str, position: str) -> ShowdownPlayerCard:
    """A replacement-level card at one position. Cached because card construction dominates the
    runtime of this file and the cards are read-only once built."""

    key = (name, position)
    if key in _card_cache:
        return _card_cache[key].model_copy(deep=True)

    is_pitcher = position in ("STARTER", "RELIEVER")
    showdown_position = Position(position)
    stats = build_replacement_level_stats_for_card(
        year=YEAR,
        player_type="PITCHER" if is_pitcher else "HITTER",
        positions=[showdown_position],
    )
    stats["name"] = name
    card = ShowdownPlayerCard(
        name=name, year=str(YEAR), set=Set._2000, stats=stats,
        stats_period=StatsPeriod(year=str(YEAR), type=StatsPeriodType.REPLACEMENT),
    )
    _card_cache[key] = card
    return card.model_copy(deep=True)


def build_team(abbreviation: str, use_lineup: bool = True) -> SimTeam:
    """A full nine plus a starter and three relievers, ids prefixed by team so both sides are
    distinguishable in a merged log."""

    cards: dict[str, ShowdownPlayerCard] = {}
    lineup: list[tuple[str, str]] = []
    for position in LINEUP_POSITIONS:
        player_id = f"{abbreviation}-{position}"
        cards[player_id] = stub_card(f"{abbreviation} {position}", position)
        lineup.append((player_id, position))

    starter_id = f"{abbreviation}-SP"
    cards[starter_id] = stub_card(f"{abbreviation} SP", "STARTER")
    bullpen_ids = []
    for index in range(1, 4):
        reliever_id = f"{abbreviation}-RP{index}"
        cards[reliever_id] = stub_card(f"{abbreviation} RP{index}", "RELIEVER")
        bullpen_ids.append(reliever_id)

    return SimTeam.from_mlb_game_roster(
        year=YEAR,
        cards=cards,
        identity=SimTeamIdentity(abbreviation=abbreviation, name=abbreviation),
        lineup=lineup if use_lineup else [],
        starting_pitcher_id=starter_id,
        position_player_ids=[player_id for player_id, _ in lineup],
        bullpen_ids=bullpen_ids,
    )


def play(seed: int, start_state: GameStartState = None, use_lineup: bool = True):
    """One game, from scratch teams so no state leaks between cases."""
    game = Game(index=0, date=GAME_DATE, home_team_name="HOM", away_team_name="AWY",
                home_team_game_number=1, away_team_game_number=1)
    game.setup(home_team=build_team("HOM", use_lineup), away_team=build_team("AWY", use_lineup), start_state=start_state)
    game.simulate(rng=Random(seed), collect_log=True, collect_box_score=True)
    return game


failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  PASS  {label}")
    else:
        failures.append(f"{label}{f' -- {detail}' if detail else ''}")
        print(f"  FAIL  {label}{f' -- {detail}' if detail else ''}")


# ----------------------------------------------------------
# MARK: - REGRESSION: THE FROM-SCRATCH PATH IS UNCHANGED
# ----------------------------------------------------------

print("\nFrom-scratch game (no start state)")

game = play(seed=42)
result = game.as_result()

check("starts in the top of the 1st", game.logs[0].inning == 1 and game.logs[0].is_top,
      f"got inning {game.logs[0].inning} is_top {game.logs[0].is_top}")
check("both starters take the mound", (game.home_team._pitchers_used[0].id == "HOM-SP"
                                       and game.away_team._pitchers_used[0].id == "AWY-SP"))
check("plays at least 9 innings", result.innings_played >= 9, f"got {result.innings_played}")
check("linescore starts at inning 1", result.linescore.innings[0].num == 1)
check("game is over", game.is_game_over)

repeat = play(seed=42).as_result()
check("same seed reproduces the game exactly", repeat.model_dump() == result.model_dump())
check("a different seed produces a different game", play(seed=7).as_result().model_dump() != result.model_dump())

# THE LOG IDS ARE WHAT LETS A RENDERED PLAY-BY-PLAY RESOLVE CARDS.
check("every log entry carries player ids", all(entry.hitter_id and entry.pitcher_id for entry in result.log))
check("log ids match the rostered players",
      all(entry.hitter_id.startswith(("HOM-", "AWY-")) for entry in result.log))
scoring_entries = [entry for entry in result.log if entry.runs_scored > 0]
check("runs_scored agrees with the final score",
      sum(entry.runs_scored for entry in result.log) == result.home_score + result.away_score,
      f"log {sum(e.runs_scored for e in result.log)} vs final {result.home_score + result.away_score}")
check("at least one scoring play was logged", len(scoring_entries) > 0)

# THE ANNOUNCED LINEUP MUST COME OUT VERBATIM.
check("preset batting order is honored",
      [p.id for p in game.away_team.batting_order] == [f"AWY-{pos}" for pos in LINEUP_POSITIONS],
      str([p.id for p in game.away_team.batting_order]))

# NO LINEUP GIVEN -> THE HEURISTIC FILLS ONE, WHICH IS THE PRE-ANNOUNCEMENT PATH.
auto = play(seed=42, use_lineup=False)
check("an unset lineup still fields nine", len(auto.away_team.batting_order) == 9,
      f"got {len(auto.away_team.batting_order)}")


# ----------------------------------------------------------
# MARK: - TAKEOVER
# ----------------------------------------------------------

print("\nTakeover in the bottom of the 7th, 2 out, runners on 1st and 3rd, 4-2 away")

completed = []
for inning in range(1, 7):
    completed.append(CompletedHalfInning(inning=inning, is_top=True, runs=1 if inning in (2, 5) else 0))
    completed.append(CompletedHalfInning(inning=inning, is_top=False, runs=1 if inning == 3 else 0))
completed.append(CompletedHalfInning(inning=7, is_top=True, runs=2))

takeover = GameStartState(
    inning=7,
    is_top=False,
    outs=2,
    runs=1,
    runners=Runners(runners=[
        Runner(id="HOM-CF", name="HOM CF", base=1, speed=15, pitcher_id="AWY-SP"),
        Runner(id="HOM-SS", name="HOM SS", base=3, speed=15, pitcher_id="AWY-SP"),
    ]),
    completed_innings=completed,
    away=TeamStartState(
        runs_scored=4, hits=8, lineup_index=3,
        # THE STARTER IS DONE (SIX INNINGS, THEN PULLED) AND A RELIEVER IS ON THE MOUND - THE
        # ORDINARY MID-GAME SHAPE, AND THE ONE THAT EXERCISES `end_inning`.
        pitchers_used=[
            PitcherAppearance(player_id="AWY-SP", start_inning=1.0, end_inning=7.0, runs_allowed=2),
            PitcherAppearance(player_id="AWY-RP1", start_inning=7.0, runs_allowed=0),
        ],
    ),
    home=TeamStartState(
        runs_scored=2, hits=5, lineup_index=6,
        pitchers_used=[PitcherAppearance(player_id="HOM-SP", start_inning=3.0, runs_allowed=4)],
    ),
)

game = play(seed=99, start_state=takeover)
result = game.as_result()
first = result.log[0]

check("resumes in the bottom of the 7th", first.inning == 7 and not first.is_top,
      f"got inning {first.inning} is_top {first.is_top}")
check("resumes with the seeded score", (first.away_score, first.home_score) == (4, 2),
      f"got away {first.away_score} home {first.home_score}")
check("resumes with the seeded baserunners", first.bases[0] == "■" and first.bases[2] == "■",
      f"got {first.bases}")
check("resumes at the seeded batting order spot", first.hitter_id == f"HOM-{LINEUP_POSITIONS[6]}",
      f"got {first.hitter_id}")
check("the pitcher who was actually in the game is still in", first.pitcher_id == "AWY-RP1",
      f"got {first.pitcher_id}")
check("the pulled starter keeps his place in the box score",
      [p.id for p in game.away_team._pitchers_used][:2] == ["AWY-SP", "AWY-RP1"],
      str([p.id for p in game.away_team._pitchers_used]))
check("the pulled starter is not brought back in",
      [p.id for p in game.away_team._pitchers_used].count("AWY-SP") == 1)
check("neither side loses runs it already had",
      result.away_score >= 4 and result.home_score >= 2,
      f"got away {result.away_score} home {result.home_score}")

linescore = result.linescore
check("the linescore keeps all seven real frames", len(linescore.innings) >= 7, f"got {len(linescore.innings)}")
check("real innings keep their real runs",
      [i.away_runs for i in linescore.innings[:6]] == [0, 1, 0, 0, 1, 0],
      str([i.away_runs for i in linescore.innings[:6]]))
check("the 7th keeps the runs scored before takeover",
      linescore.innings[6].away_runs == 2 and linescore.innings[6].home_runs >= 1,
      f"got away {linescore.innings[6].away_runs} home {linescore.innings[6].home_runs}")
check("linescore runs equal the final score",
      linescore.away.runs == result.away_score and linescore.home.runs == result.home_score)
check("carried-over hits are in the linescore", linescore.away.hits >= 8 and linescore.home.hits >= 5,
      f"got away {linescore.away.hits} home {linescore.home.hits}")
check("innings 1-6 are not re-simulated",
      all(entry.inning >= 7 for entry in result.log),
      f"earliest logged inning {min(e.inning for e in result.log)}")
check("takeover games are reproducible",
      play(seed=99, start_state=takeover).as_result().model_dump() == result.model_dump())


print("\nA starter resumed deep into the game gets pulled")

tired = takeover.model_copy(deep=True)
# SIX INNINGS ALREADY THROWN. `innings_pitched` IS `current inning_num_full - start_inning`, so
# starting him at 1.0 in the 7th is exactly six innings of work.
tired.away.pitchers_used = [PitcherAppearance(player_id="AWY-SP", start_inning=1.0, runs_allowed=4)]
game = play(seed=5, start_state=tired)
away_arms = [p.id for p in game.away_team._pitchers_used]
check("the bullpen is used", len(away_arms) > 1, f"pitchers used: {away_arms}")
check("the starter is the first arm listed", away_arms[0] == "AWY-SP", str(away_arms))

fresh = takeover.model_copy(deep=True)
fresh.away.pitchers_used = [PitcherAppearance(player_id="AWY-RP1", start_inning=7.0, runs_allowed=0)]
game = play(seed=5, start_state=fresh)
check("a reliever already in the game stays in", game.as_result().log[0].pitcher_id == "AWY-RP1",
      f"got {game.as_result().log[0].pitcher_id}")
check("an already-used arm is not brought back in",
      [p.id for p in game.away_team._pitchers_used].count("AWY-RP1") == 1)


print("\nWalk-off from the bottom of the 9th, home down one")

walkoff = GameStartState(
    inning=9,
    is_top=False,
    outs=0,
    completed_innings=(
        [CompletedHalfInning(inning=i, is_top=True, runs=1 if i == 4 else 0) for i in range(1, 10)]
        + [CompletedHalfInning(inning=i, is_top=False, runs=0) for i in range(1, 9)]
    ),
    away=TeamStartState(runs_scored=1, pitchers_used=[PitcherAppearance(player_id="AWY-SP", start_inning=8.0)]),
    home=TeamStartState(runs_scored=0, pitchers_used=[PitcherAppearance(player_id="HOM-SP", start_inning=8.0)]),
)

# THE HOME TEAM EVENTUALLY WINS OR THE GAME GOES TO EXTRAS - EITHER WAY IT MUST END CLEANLY, WITH
# NO PHANTOM HALF-INNING IN THE LINESCORE.
for seed in range(6):
    game = play(seed=seed, start_state=walkoff)
    result = game.as_result()
    label = f"seed {seed}"
    if not game.is_game_over:
        check(f"walk-off {label}: game ends", False)
        continue
    ends_in_bottom_half = result.linescore.innings[-1].home_runs is not None
    won_at_home = result.home_score > result.away_score
    check(f"walk-off {label}: no phantom frame after a home win",
          (not won_at_home) or ends_in_bottom_half,
          f"home {result.home_score} away {result.away_score}, last frame home_runs {result.linescore.innings[-1].home_runs}")
    check(f"walk-off {label}: never ends tied", result.home_score != result.away_score,
          f"{result.away_score}-{result.home_score}")


print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print("All checks passed.")
