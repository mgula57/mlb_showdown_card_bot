"""Offline checks for `ManagerPreference` - the per-run, team-wide manager tendencies.

No database, no network: cards are built from `build_replacement_level_stats_for_card`, the same
offline generator `test_game_takeover.py` uses, so this runs as
`python tests/test_manager_preference.py` anywhere.

Three things are under test:
  1. SCALARS - every derived scalar is an EXACT no-op at level 3, monotonic across levels, and
     the 1-5 bounds are enforced.
  2. DETERMINISM - a neutral manager (or none at all) produces a byte-identical game for a given
     seed; a non-neutral one diverges but is itself reproducible.
  3. DIRECTION - an aggressive manager actually moves the needle (more steal attempts, quicker
     hook) versus a neutral one, aggregated over many seeds.
"""

import os
import sys
from datetime import date
from pathlib import Path
from random import Random

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from pydantic import ValidationError

from mlb_showdown_bot.core.card.sets import Set
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.core.card.stats.stats_period import StatsPeriod, StatsPeriodType
from mlb_showdown_bot.core.data.replacement_season_averages import build_replacement_level_stats_for_card
from mlb_showdown_bot.core.shared.player_position import Position
from mlb_showdown_bot.core.simulation.game import Game
from mlb_showdown_bot.core.simulation.inning import Inning
from mlb_showdown_bot.core.simulation.models import NEUTRAL_MANAGER, ManagerPreference, SimTeamIdentity
from mlb_showdown_bot.core.simulation.player import SimPitcher
from mlb_showdown_bot.core.simulation.team import SimTeam

YEAR = 2023
GAME_DATE = date(YEAR, 6, 15)
LINEUP_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]

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
    if key in _card_cache:
        return _card_cache[key].model_copy(deep=True)
    is_pitcher = position in ("STARTER", "RELIEVER")
    stats = build_replacement_level_stats_for_card(
        year=YEAR, player_type="PITCHER" if is_pitcher else "HITTER", positions=[Position(position)],
    )
    stats["name"] = name
    card = ShowdownPlayerCard(
        name=name, year=str(YEAR), set=Set._2000, stats=stats,
        stats_period=StatsPeriod(year=str(YEAR), type=StatsPeriodType.REPLACEMENT),
    )
    _card_cache[key] = card
    return card.model_copy(deep=True)


def build_team(abbreviation: str, manager: ManagerPreference = None) -> SimTeam:
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
        position_player_ids=[player_id for player_id, _ in lineup], bullpen_ids=bullpen_ids,
        manager=manager,
    )


def play(seed: int, away_manager: ManagerPreference = None, home_manager: ManagerPreference = None):
    game = Game(index=0, date=GAME_DATE, home_team_name="HOM", away_team_name="AWY",
                home_team_game_number=1, away_team_game_number=1)
    game.setup(home_team=build_team("HOM", home_manager), away_team=build_team("AWY", away_manager))
    game.simulate(rng=Random(seed), collect_log=True, collect_box_score=True)
    return game


# ----------------------------------------------------------
# MARK: - SCALARS
# ----------------------------------------------------------

print("\nScalar math")

neutral = ManagerPreference()
check("default is neutral", neutral.is_neutral)
check("NEUTRAL_MANAGER is neutral", NEUTRAL_MANAGER.is_neutral)
check("one non-3 level is not neutral", not ManagerPreference(steal_aggression=4).is_neutral)

check("steal_attempt_factor level 3 == 1.0", neutral.steal_attempt_factor == 1.0)
check("advance_probability_threshold level 3 == 0.5", neutral.advance_probability_threshold == 0.5)
check("hook_ip_adjustment level 3 == 0.0", neutral.hook_ip_adjustment == 0.0)
check("closer_nonsave_fit_multiplier level 3 == 0.5", neutral.closer_nonsave_fit_multiplier == 0.5)
check("closer_save_inning level 3 == 9", neutral.closer_save_inning == 9)

steals = [ManagerPreference(steal_aggression=lvl).steal_attempt_factor for lvl in range(1, 6)]
check("steal_attempt_factor is strictly increasing", all(a < b for a, b in zip(steals, steals[1:])), str(steals))
advs = [ManagerPreference(baserunning_aggression=lvl).advance_probability_threshold for lvl in range(1, 6)]
check("advance threshold is strictly decreasing (more aggressive)", all(a > b for a, b in zip(advs, advs[1:])), str(advs))
hooks = [ManagerPreference(bullpen_hook=lvl).hook_ip_adjustment for lvl in range(1, 6)]
check("hook_ip_adjustment goes negative->positive", hooks[0] < 0 < hooks[-1] and hooks == sorted(hooks), str(hooks))
check("save-only closer has 0 non-save fit", ManagerPreference(closer_usage=1).closer_nonsave_fit_multiplier == 0.0)
check("high closer usage pulls save inning earlier", ManagerPreference(closer_usage=5).closer_save_inning == 7)
check("low closer usage never moves save inning past 9", ManagerPreference(closer_usage=1).closer_save_inning == 9)

for bad in (0, 6, -1):
    try:
        ManagerPreference(steal_aggression=bad)
        check(f"level {bad} rejected", False)
    except ValidationError:
        check(f"level {bad} rejected", True)


# ----------------------------------------------------------
# MARK: - DETERMINISM
# ----------------------------------------------------------

print("\nDeterminism: a neutral manager is a no-op")

for seed in (1, 42, 99, 2024):
    baseline = play(seed=seed).as_result().model_dump()
    explicit_neutral = play(seed=seed, away_manager=ManagerPreference(), home_manager=ManagerPreference()).as_result().model_dump()
    check(f"seed {seed}: explicit-neutral game == no-manager game", explicit_neutral == baseline)

aggressive = ManagerPreference(steal_aggression=5, baserunning_aggression=5, bullpen_hook=1, closer_usage=5)
changed_any = False
for seed in (1, 42, 99, 2024):
    baseline = play(seed=seed).as_result().model_dump()
    with_manager = play(seed=seed, away_manager=aggressive).as_result().model_dump()
    if with_manager != baseline:
        changed_any = True
    repeat = play(seed=seed, away_manager=aggressive).as_result().model_dump()
    check(f"seed {seed}: non-neutral manager is reproducible", with_manager == repeat)
check("a non-neutral manager changes at least one game", changed_any)


# ----------------------------------------------------------
# MARK: - DIRECTION
# ----------------------------------------------------------

print("\nDirection: an aggressive manager moves the needle")

SEEDS = range(40)

def steal_attempts(manager: ManagerPreference) -> int:
    total = 0
    for seed in SEEDS:
        box = play(seed=seed, away_manager=manager).as_result().away_box_score.batting_totals
        total += box.stolen_bases + box.caught_stealing
    return total

neutral_steals = steal_attempts(ManagerPreference())
aggressive_steals = steal_attempts(ManagerPreference(steal_aggression=5))
timid_steals = steal_attempts(ManagerPreference(steal_aggression=1))
check("steal aggression 5 attempts more steals than neutral", aggressive_steals > neutral_steals,
      f"aggressive {aggressive_steals} vs neutral {neutral_steals}")
check("steal aggression 1 attempts fewer steals than neutral", timid_steals < neutral_steals,
      f"timid {timid_steals} vs neutral {neutral_steals}")


# `is_tired` directly: a starter 5.2 innings into a 6 IP outing, no runs. Neutral leaves him in,
# a quick hook pulls him, a slow hook would leave him well past his printed IP.
sp = SimPitcher(card=stub_card("hooktest", "STARTER"), id="hooktest", start_inning=1.0)
sp.card.ip = 6
sixth_two_out = Inning(inning=6, is_top=True, outs=2)   # inning_num_full 6.667 -> 5.667 IP thrown
check("neutral hook: starter mid-6th of a 6 IP outing is not tired",
      not sp.is_tired(sixth_two_out, ip_adjustment=NEUTRAL_MANAGER.hook_ip_adjustment))
check("quick hook (level 1): same starter IS tired",
      sp.is_tired(sixth_two_out, ip_adjustment=ManagerPreference(bullpen_hook=1).hook_ip_adjustment))
check("slow hook (level 5): same starter is not tired",
      not sp.is_tired(sixth_two_out, ip_adjustment=ManagerPreference(bullpen_hook=5).hook_ip_adjustment))


# ----------------------------------------------------------

if failures:
    print(f"\n{len(failures)} CHECK(S) FAILED:")
    for line in failures:
        print(f"  - {line}")
    sys.exit(1)
print("\nAll checks passed.")
