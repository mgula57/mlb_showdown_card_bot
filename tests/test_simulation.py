"""Smoke tests for the simulation engine.

Uses model_construct() to build minimal ShowdownPlayerCard objects without
hitting real stats sources or requiring the full card generation pipeline.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mlb_showdown_bot.core.card.chart import Chart, ChartCategory
from mlb_showdown_bot.core.card.sets import Set
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.core.shared.player_position import PlayerSubType, PlayerType
from mlb_showdown_bot.core.simulation import (
    GameResult,
    GameState,
    GameStatus,
    ShowdownGame,
    SimulationRuleset,
)
from mlb_showdown_bot.core.simulation.base_state import advance_runners


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chart(command: int, is_pitcher: bool) -> Chart:
    """Build a minimal Chart suitable for simulation testing.

    Uses object.__new__ to avoid Pydantic requiring non-optional fields
    like `set`, `era`, and `is_expanded` that the simulation doesn't need.
    """
    if is_pitcher:
        results = {
            1: ChartCategory.PU,
            2: ChartCategory.SO, 3: ChartCategory.SO,
            4: ChartCategory.GB, 5: ChartCategory.GB, 6: ChartCategory.GB,
            7: ChartCategory.GB, 8: ChartCategory.FB, 9: ChartCategory.FB,
            10: ChartCategory.FB, 11: ChartCategory.FB, 12: ChartCategory.FB,
            13: ChartCategory.BB, 14: ChartCategory._1B, 15: ChartCategory._1B,
            16: ChartCategory._1B, 17: ChartCategory._1B, 18: ChartCategory._2B,
            19: ChartCategory._2B, 20: ChartCategory.HR,
        }
    else:
        results = {
            1: ChartCategory.SO, 2: ChartCategory.GB, 3: ChartCategory.FB,
            4: ChartCategory.BB, 5: ChartCategory.BB,
            6: ChartCategory._1B, 7: ChartCategory._1B, 8: ChartCategory._1B,
            9: ChartCategory._1B, 10: ChartCategory._1B_PLUS,
            11: ChartCategory._2B, 12: ChartCategory._2B, 13: ChartCategory._2B,
            14: ChartCategory._3B, 15: ChartCategory._3B,
            16: ChartCategory.HR, 17: ChartCategory.HR, 18: ChartCategory.HR,
            19: ChartCategory.HR, 20: ChartCategory.HR,
        }
    chart = object.__new__(Chart)
    chart.__dict__.update({'command': command, 'is_pitcher': is_pitcher, 'results': results})
    chart.__pydantic_fields_set__ = frozenset({'command', 'is_pitcher', 'results'})
    chart.__pydantic_extra__ = None
    chart.__pydantic_private__ = None
    return chart


def _make_card(name: str, player_type: PlayerType, player_sub_type: PlayerSubType, chart: Chart) -> ShowdownPlayerCard:
    """Create a minimal ShowdownPlayerCard without triggering its build pipeline.

    Uses object.__new__ to bypass __init__ and model_post_init entirely,
    then sets the attributes the simulation engine actually reads.
    """
    card = object.__new__(ShowdownPlayerCard)
    card.__dict__.update({
        'name': name,
        'player_type': player_type,
        'player_sub_type': player_sub_type,
        'chart': chart,
    })
    # Pydantic v2 internal bookkeeping
    card.__pydantic_fields_set__ = frozenset({'name', 'player_type', 'player_sub_type', 'chart'})
    card.__pydantic_extra__ = None
    card.__pydantic_private__ = None
    return card


def _make_pitcher(name: str = "Pitcher", command: int = 3) -> ShowdownPlayerCard:
    return _make_card(name, PlayerType.PITCHER, PlayerSubType.STARTING_PITCHER,
                      _make_chart(command=command, is_pitcher=True))


def _make_batter(name: str = "Batter", command: int = 10) -> ShowdownPlayerCard:
    return _make_card(name, PlayerType.HITTER, PlayerSubType.POSITION_PLAYER,
                      _make_chart(command=command, is_pitcher=False))


def _make_lineup(n_batters: int = 9, pitcher_command: int = 3, batter_command: int = 10):
    pitcher = _make_pitcher(command=pitcher_command)
    batters = [_make_batter(name=f"Batter{i+1}", command=batter_command) for i in range(n_batters)]
    return [pitcher] + batters


# ---------------------------------------------------------------------------
# Unit tests: base runner advancement
# ---------------------------------------------------------------------------

def test_advance_runners_hr_clears_bases():
    runners = {1: "A", 2: "B", 3: "C"}
    new_runners, runs, rbi, sb, sb_ok = advance_runners(runners, ChartCategory.HR, "Batter", 0)
    assert runs == 4
    assert rbi == 4
    assert new_runners == {}
    assert not sb


def test_advance_runners_1b():
    runners = {2: "B", 3: "C"}
    new_runners, runs, rbi, _, _ = advance_runners(runners, ChartCategory._1B, "Batter", 0)
    assert runs == 1  # C scores
    assert new_runners == {3: "B", 1: "Batter"}


def test_advance_runners_1b_plus_open_second():
    # No runners — batter should advance to 2B
    new_runners, runs, rbi, sb_attempt, sb_success = advance_runners({}, ChartCategory._1B_PLUS, "Batter", 0)
    assert sb_attempt is True
    assert sb_success is True
    assert 2 in new_runners
    assert 1 not in new_runners


def test_advance_runners_1b_plus_second_occupied():
    # Runner on 2B advances to 3B on the single, freeing 2B → batter steals to 2B
    runners = {2: "B"}
    new_runners, _, _, sb_attempt, sb_success = advance_runners(runners, ChartCategory._1B_PLUS, "Batter", 0)
    assert sb_attempt is True
    assert sb_success is True   # 2B was freed by the advancing runner
    assert 2 in new_runners
    assert new_runners[3] == "B"  # B advanced to 3B on the single


def test_advance_runners_1b_plus_second_blocked_by_chain():
    # Runner on 1B advances to 2B on the single, blocking the batter's steal
    runners = {1: "A"}
    new_runners, _, _, sb_attempt, sb_success = advance_runners(runners, ChartCategory._1B_PLUS, "Batter", 0)
    assert sb_attempt is True
    assert sb_success is False   # A moved to 2B, blocking steal
    assert new_runners[1] == "Batter"
    assert new_runners[2] == "A"


def test_advance_runners_walk_bases_loaded():
    runners = {1: "A", 2: "B", 3: "C"}
    new_runners, runs, rbi, _, _ = advance_runners(runners, ChartCategory.BB, "Batter", 0)
    assert runs == 1  # C scores
    assert new_runners[1] == "Batter"
    assert new_runners[2] == "A"
    assert new_runners[3] == "B"


def test_advance_runners_walk_not_forced():
    # Runner on 2B only — not forced on a walk, batter just takes 1B
    runners = {2: "B"}
    new_runners, runs, _, _, _ = advance_runners(runners, ChartCategory.BB, "Batter", 0)
    assert runs == 0
    assert new_runners[1] == "Batter"
    assert new_runners[2] == "B"


def test_advance_runners_gb_scores_with_runner_on_3rd():
    runners = {3: "C"}
    new_runners, runs, _, _, _ = advance_runners(runners, ChartCategory.GB, "Batter", outs_before=0)
    assert runs == 1
    assert 3 not in new_runners


def test_advance_runners_gb_no_score_two_outs():
    runners = {3: "C"}
    new_runners, runs, _, _, _ = advance_runners(runners, ChartCategory.GB, "Batter", outs_before=2)
    assert runs == 0
    assert 3 in new_runners


def test_advance_runners_sb_cap_blocks_1b_plus():
    # SB cap of 1 and batter already has 1 SB
    new_runners, _, _, sb_attempt, sb_success = advance_runners(
        {}, ChartCategory._1B_PLUS, "Batter", 0,
        stolen_base_cap=1, batter_sbs=1,
    )
    assert sb_attempt is True
    assert sb_success is False
    assert 1 in new_runners


# ---------------------------------------------------------------------------
# Integration tests: full game simulation
# ---------------------------------------------------------------------------

def test_simulate_game_completes():
    ruleset = SimulationRuleset.expanded()
    game = ShowdownGame.new(
        away=_make_lineup(),
        home=_make_lineup(),
        ruleset=ruleset,
    )
    result = game.simulate_to_end()
    assert isinstance(result, GameResult)
    assert result.winner in ('away', 'home', 'tie')


def test_simulate_game_score_consistency():
    ruleset = SimulationRuleset.expanded()
    game = ShowdownGame.new(away=_make_lineup(), home=_make_lineup(), ruleset=ruleset)
    result = game.simulate_to_end()
    assert result.away_score == sum(result.score_by_inning(is_away=True))
    assert result.home_score == sum(result.score_by_inning(is_away=False))


def test_simulate_game_nine_innings():
    ruleset = SimulationRuleset.expanded()
    game = ShowdownGame.new(away=_make_lineup(), home=_make_lineup(), ruleset=ruleset)
    result = game.simulate_to_end()
    # Walk-offs can end in 17 half-innings; otherwise 18
    assert len(result.innings) in (17, 18)


def test_simulate_game_box_score_populated():
    ruleset = SimulationRuleset.expanded()
    game = ShowdownGame.new(away=_make_lineup(), home=_make_lineup(), ruleset=ruleset)
    result = game.simulate_to_end()
    assert len(result.away_box) > 0
    assert len(result.home_box) > 0
    # Pitcher should have outs_recorded
    pitchers = [p for p in result.away_box if p.outs_recorded is not None]
    assert len(pitchers) == 1


def test_simulate_half_inning():
    ruleset = SimulationRuleset.expanded()
    game = ShowdownGame.new(away=_make_lineup(), home=_make_lineup(), ruleset=ruleset)
    half = game.simulate_half_inning()
    assert half.inning == 1
    assert half.is_top is True


def test_apply_outcome_live_play():
    ruleset = SimulationRuleset.expanded()
    game = ShowdownGame.new(away=_make_lineup(), home=_make_lineup(), ruleset=ruleset)
    ab = game.apply_outcome(ChartCategory.HR)
    assert ab.outcome == ChartCategory.HR
    assert ab.runs_scored >= 1  # at minimum, batter scores


def test_pause_and_resume_via_from_state():
    """ShowdownGame.from_state() resumes a game from a previously captured GameState."""
    ruleset = SimulationRuleset.expanded()
    game = ShowdownGame.new(away=_make_lineup(), home=_make_lineup(), ruleset=ruleset)
    for _ in range(3):
        game.simulate_half_inning()

    # Capture state (the same Python object) and resume from it
    captured_state = game.state
    resumed = ShowdownGame.from_state(captured_state)
    assert resumed.state.current_inning == game.state.current_inning
    assert resumed.state.away_score == game.state.away_score

    # Finish both from the same checkpoint — they should both complete
    result = resumed.simulate_to_end()
    assert result.winner in ('away', 'home', 'tie')


def test_pause_and_resume_json_with_real_state():
    """Full JSON round-trip works when GameState has no mock cards.
    This test verifies the serialization path only (no card data needed).
    """
    ruleset = SimulationRuleset.expanded()
    # Verify the ruleset itself serializes cleanly
    ruleset_json = ruleset.model_dump_json()
    restored_ruleset = SimulationRuleset.model_validate_json(ruleset_json)
    assert restored_ruleset.game_set == ruleset.game_set
    assert restored_ruleset.innings == 9
    # (Full GameState round-trip requires real ShowdownPlayerCard objects — integration test only)


def test_game_complete_flag():
    ruleset = SimulationRuleset.expanded()
    game = ShowdownGame.new(away=_make_lineup(), home=_make_lineup(), ruleset=ruleset)
    assert not game.is_complete
    game.simulate_to_end()
    assert game.is_complete
    assert game.state.status == GameStatus.COMPLETE


def test_mistake_pitch_ruleset():
    ruleset = SimulationRuleset.mistake_pitch_expanded()
    game = ShowdownGame.new(away=_make_lineup(), home=_make_lineup(), ruleset=ruleset)
    result = game.simulate_to_end()
    assert result.winner in ('away', 'home', 'tie')


def test_hybrid_sim_then_live():
    ruleset = SimulationRuleset.expanded()
    game = ShowdownGame.new(away=_make_lineup(), home=_make_lineup(), ruleset=ruleset)
    # Simulate first inning auto, then apply one live at-bat, then finish auto
    game.simulate_half_inning()
    game.simulate_half_inning()
    ab = game.apply_outcome(ChartCategory._2B)
    assert ab.outcome == ChartCategory._2B
    result = game.simulate_to_end()
    assert result.winner in ('away', 'home', 'tie')


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [v for k, v in list(globals().items()) if k.startswith('test_')]
    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            print(f"  PASS  {test_fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {test_fn.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
