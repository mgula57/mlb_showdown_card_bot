"""Offline checks for rest-based postseason starter selection (`Rotation.starter_for_date`).

No database, no network: cards are built from `build_replacement_level_stats_for_card`, the same
offline generator `test_manager_preference.py` uses, so this runs as
`python tests/test_rotation_rest.py` anywhere.

Two things are under test:
  1. SELECTOR - `Rotation.starter_for_date` in isolation: reproduces the plain round robin on a
     daily schedule, uses at most 4 of 5 starters across a real postseason series (LDS 2-2-1,
     LCS 2-3-2, built from the real `PostseasonSeries` date generator), and never crashes when
     nobody is rested.
  2. WIRING - through the real `Game.setup`/`Game.simulate`: a postseason game never misclassifies
     a reliever as a start, and a non-postseason game (the default) is completely untouched - the
     regular season's plain round robin still drives starter selection exactly as before.
"""

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from random import Random

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from mlb_showdown_bot.core.card.sets import Set
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.core.card.stats.stats_period import StatsPeriod, StatsPeriodType
from mlb_showdown_bot.core.data.replacement_season_averages import build_replacement_level_stats_for_card
from mlb_showdown_bot.core.shared.player_position import Position, PositionSlot
from mlb_showdown_bot.core.simulation.game import Game
from mlb_showdown_bot.core.simulation.models import PostseasonFormat, PostseasonRound, SimTeamIdentity
from mlb_showdown_bot.core.simulation.player import SimPitcher
from mlb_showdown_bot.core.simulation.player_group import Rotation
from mlb_showdown_bot.core.simulation.postseason import PostseasonSeries
from mlb_showdown_bot.core.simulation.team import SimTeam

YEAR = 2023
GAME_DATE = date(YEAR, 10, 3)
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


def build_rotation(size: int = 5) -> Rotation:
    return Rotation(players=[
        SimPitcher(card=stub_card(f"SP{i}", "STARTER"), id=f"SP{i}", position_slot=PositionSlot.SP)
        for i in range(size)
    ])


def build_team(abbreviation: str) -> SimTeam:
    cards: dict[str, ShowdownPlayerCard] = {}
    lineup: list[tuple[str, str]] = []
    for position in LINEUP_POSITIONS:
        player_id = f"{abbreviation}-{position}"
        cards[player_id] = stub_card(f"{abbreviation} {position}", position)
        lineup.append((player_id, position))
    starter_id = f"{abbreviation}-SP0"
    cards[starter_id] = stub_card(f"{abbreviation} SP0", "STARTER")
    bullpen_ids = []
    for index in range(1, 5):
        reliever_id = f"{abbreviation}-RP{index}"
        cards[reliever_id] = stub_card(f"{abbreviation} RP{index}", "RELIEVER")
        bullpen_ids.append(reliever_id)
    team = SimTeam.from_mlb_game_roster(
        year=YEAR, cards=cards,
        identity=SimTeamIdentity(abbreviation=abbreviation, name=abbreviation),
        lineup=lineup, starting_pitcher_id=starter_id,
        position_player_ids=[player_id for player_id, _ in lineup], bullpen_ids=bullpen_ids,
    )
    # `from_mlb_game_roster` ONLY BUILDS A SINGLE-PITCHER ROTATION (FINE FOR A ONE-OFF TAKEOVER
    # GAME) - PAD IT OUT TO A FULL 5-MAN ROTATION SO THE WIRING TESTS BELOW CAN EXERCISE SELECTION
    # ACROSS A SERIES.
    for i in range(1, 5):
        pid = f"{abbreviation}-SP{i}"
        team.rotation.players.append(SimPitcher(card=stub_card(f"{abbreviation} SP{i}", "STARTER"), id=pid, position_slot=PositionSlot.SP))
    return team


def series_dates(round: PostseasonRound, fmt: PostseasonFormat, start: date) -> list[date]:
    home = build_team("HOM")
    away = build_team("AWY")
    series = PostseasonSeries(id="test", league="AL", round=round, format=fmt, start_date=start, home_team=home, away_team=away)
    return [game.date for game in series.games]


# ----------------------------------------------------------
# MARK: - SELECTOR
# ----------------------------------------------------------

print("\nSelector: starter_for_date in isolation")

# DAILY SCHEDULE, NO OFF DAYS -> REPRODUCES THE PLAIN ROUND ROBIN
rotation = build_rotation()
daily_dates = [GAME_DATE + timedelta(days=i) for i in range(10)]
picks = []
for d in daily_dates:
    starter = rotation.starter_for_date(d)
    picks.append(rotation.players.index(starter))
    starter.last_start_date = d
    starter.postseason_starts += 1
check("daily schedule reproduces round robin", picks == [0, 1, 2, 3, 4, 0, 1, 2, 3, 4], str(picks))

# BEST-OF-5 LDS (2-2-1): AT MOST 4 OF 5 STARTERS USED, THE 5TH NEVER TOUCHED
rotation = build_rotation()
dates = series_dates(PostseasonRound.DIVISIONAL, PostseasonFormat.WILDCARD_3, date(YEAR, 10, 3))
check("LDS has 5 games", len(dates) == 5, str(dates))
used = set()
for d in dates:
    starter = rotation.starter_for_date(d)
    used.add(rotation.players.index(starter))
    starter.last_start_date = d
    starter.postseason_starts += 1
check("LDS uses at most 4 of 5 starters", len(used) <= 4, str(sorted(used)))
check("LDS never uses the 5th (weakest) starter", 4 not in used, str(sorted(used)))

# BEST-OF-7 LCS (2-3-2): SAME EXPECTATION OVER A LONGER SERIES
rotation = build_rotation()
dates = series_dates(PostseasonRound.CHAMPIONSHIP, PostseasonFormat.WILDCARD_3, date(YEAR, 10, 12))
check("LCS has 7 games", len(dates) == 7, str(dates))
used = set()
for d in dates:
    starter = rotation.starter_for_date(d)
    used.add(rotation.players.index(starter))
    starter.last_start_date = d
    starter.postseason_starts += 1
check("LCS uses at most 4 of 5 starters", len(used) <= 4, str(sorted(used)))
check("LCS never uses the 5th (weakest) starter", 4 not in used, str(sorted(used)))

# FALLBACK, DIFFERENTIATED REST: NOBODY IS FULLY RESTED -> PICKS WHOEVER IS CLOSEST TO READY
rotation = build_rotation()
for i, p in enumerate(rotation.players):
    p.last_start_date = GAME_DATE - timedelta(days=4 - i)  # SP0 RESTED 4 DAYS, SP4 RESTED 0
    p.postseason_starts = 1
fallback = rotation.starter_for_date(GAME_DATE)
check("fallback picks the most-rested arm when none are fully rested", fallback is rotation.players[0], fallback.id)

# FALLBACK, FULLY TIED: SAME REST AND USAGE FOR EVERYONE -> BREAKS THE TIE BY RANK, NEVER CRASHES
rotation = build_rotation()
yesterday = GAME_DATE - timedelta(days=1)
for p in rotation.players:
    p.last_start_date = yesterday
    p.postseason_starts = 1
fallback = rotation.starter_for_date(GAME_DATE)
check("fallback returns a rotation pitcher", fallback in rotation.players)
check("fallback tie-break falls back to rank", fallback is rotation.players[0], fallback.id)


# ----------------------------------------------------------
# MARK: - WIRING
# ----------------------------------------------------------

print("\nWiring: through Game.setup / Game.simulate")

home = build_team("HOM")
away = build_team("AWY")
series = PostseasonSeries(
    id="wiring-test", league="AL", round=PostseasonRound.DIVISIONAL, format=PostseasonFormat.WILDCARD_3,
    start_date=date(YEAR, 10, 3), home_team=home, away_team=away,
)
starters_used = set()
for i, sim_game in enumerate(series.games):
    sim_game.setup(home_team=home, away_team=away, postseason=True)
    sim_game.simulate(rng=Random(1000 + i), collect_box_score=True)
    starters_used.add(sim_game.home_starting_pitcher.id)
    starters_used.add(sim_game.away_starting_pitcher.id)

check("postseason series uses at most 8 total starters (<=4 per side)", len(starters_used) <= 8, str(sorted(starters_used)))
for team in (home, away):
    relievers_started = [p.id for p in team.bullpen.players if p.last_start_date is not None]
    check(f"{team.name}: no reliever was ever recorded as a start", relievers_started == [], str(relievers_started))
    total_recorded_starts = sum(p.postseason_starts for p in team.rotation.players)
    check(f"{team.name}: recorded starts match games actually played", total_recorded_starts == len(series.games), f"{total_recorded_starts} != {len(series.games)}")

# NON-POSTSEASON GAME (THE DEFAULT) IS COMPLETELY UNTOUCHED
home = build_team("HOM")
away = build_team("AWY")
regular_game = Game(index=0, date=GAME_DATE, home_team_name="HOM", away_team_name="AWY", home_team_game_number=1, away_team_game_number=1)
regular_game.setup(home_team=home, away_team=away)  # postseason DEFAULTS TO False
regular_game.simulate(rng=Random(1), collect_box_score=True)
check("regular-season starter is still rotation slot 0 (the pointer, untouched)", regular_game.home_starting_pitcher.id == home.rotation.players[0].id)
check("regular-season game never writes last_start_date", all(p.last_start_date is None for p in home.rotation.players))
check("regular-season game never writes postseason_starts", all(p.postseason_starts == 0 for p in home.rotation.players))


# ----------------------------------------------------------

if failures:
    print(f"\n{len(failures)} CHECK(S) FAILED:")
    for line in failures:
        print(f"  - {line}")
    sys.exit(1)
print("\nAll checks passed.")
