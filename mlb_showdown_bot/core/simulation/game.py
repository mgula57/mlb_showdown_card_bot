from __future__ import annotations

from ..card.chart import ChartCategory
from ..card.showdown_player_card import ShowdownPlayerCard
from .at_bat import apply_outcome as _apply_outcome_fn, resolve_at_bat as _resolve_at_bat_fn
from .lineup import Lineup
from .models import AtBatResult, GameResult, HalfInningResult, PlayerBoxScore
from .ruleset import SimulationRuleset
from .state import GameState, GameStatus
from .team import ShowdownTeam

_OUT_OUTCOMES = {ChartCategory.SO, ChartCategory.PU, ChartCategory.GB, ChartCategory.FB}


class ShowdownGame:
    """Wraps GameState and exposes a step-by-step play API.

    Supports full auto-simulation, live play (caller provides outcomes),
    hybrid modes, and pause/resume via GameState serialization.
    """

    def __init__(self, state: GameState) -> None:
        self.state = state

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def new(
        cls,
        *,
        ruleset: SimulationRuleset,
        away: list[ShowdownPlayerCard] | ShowdownTeam | None = None,
        home: list[ShowdownPlayerCard] | ShowdownTeam | None = None,
    ) -> 'ShowdownGame':
        """Create a new game from card lists or ShowdownTeam objects."""
        away_lineup = _to_lineup(away, label='away')
        home_lineup = _to_lineup(home, label='home')

        # Use model_construct to avoid re-validating embedded ShowdownPlayerCard objects,
        # which have expensive model_post_init side-effects (card rendering pipeline).
        state = GameState.model_construct(
            ruleset=ruleset,
            away_batting_order=away_lineup.batting_order,
            away_pitcher=away_lineup.pitcher,
            home_batting_order=home_lineup.batting_order,
            home_pitcher=home_lineup.pitcher,
            away_cursor=0,
            home_cursor=0,
            completed_half_innings=[],
            current_half_at_bats=[],
            current_inning=1,
            is_top_half=True,
            outs=0,
            runners={},
            away_box={},
            home_box={},
            status=GameStatus.IN_PROGRESS,
        )
        return cls(state)

    @classmethod
    def from_state(cls, state: GameState) -> 'ShowdownGame':
        """Resume a game from a previously serialized GameState."""
        return cls(state)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def current_batter(self) -> ShowdownPlayerCard:
        return self.state.current_batter

    @property
    def current_pitcher(self) -> ShowdownPlayerCard:
        return self.state.current_pitcher

    @property
    def is_complete(self) -> bool:
        return self.state.status == GameStatus.COMPLETE

    # ------------------------------------------------------------------
    # Step-by-step operations
    # ------------------------------------------------------------------

    def simulate_at_bat(self) -> AtBatResult:
        """Auto-roll dice and advance the game by one at-bat."""
        if self.is_complete:
            raise RuntimeError("Game is already complete.")
        batter_sbs = _stolen_bases_this_game(self.state, self.state.current_batter.name)
        ab_result, new_runners = _resolve_at_bat_fn(
            pitcher=self.state.current_pitcher,
            batter=self.state.current_batter,
            ruleset=self.state.ruleset,
            runners=dict(self.state.runners),
            outs_before=self.state.outs,
            batter_sbs=batter_sbs,
        )
        self._apply_at_bat_result(ab_result, new_runners)
        return ab_result

    def apply_outcome(self, outcome: ChartCategory) -> AtBatResult:
        """Apply a caller-provided outcome (live play). Skips dice rolls."""
        if self.is_complete:
            raise RuntimeError("Game is already complete.")
        batter_sbs = _stolen_bases_this_game(self.state, self.state.current_batter.name)
        ab_result, new_runners = _apply_outcome_fn(
            pitcher=self.state.current_pitcher,
            batter=self.state.current_batter,
            outcome=outcome,
            runners=dict(self.state.runners),
            outs_before=self.state.outs,
            ruleset=self.state.ruleset,
            batter_sbs=batter_sbs,
        )
        self._apply_at_bat_result(ab_result, new_runners)
        return ab_result

    def simulate_half_inning(self) -> HalfInningResult:
        """Auto-simulate until 3 outs are recorded in the current half-inning."""
        if self.is_complete:
            raise RuntimeError("Game is already complete.")
        start_inning = self.state.current_inning
        start_half = self.state.is_top_half
        while (
            not self.is_complete
            and self.state.current_inning == start_inning
            and self.state.is_top_half == start_half
        ):
            self.simulate_at_bat()
        # Return the half-inning that just completed
        return self.state.completed_half_innings[-1]

    def simulate_to_end(self) -> GameResult:
        """Auto-simulate all remaining at-bats to game completion."""
        while not self.is_complete:
            self.simulate_at_bat()
        return self.to_result()

    def to_result(self) -> GameResult:
        """Convert completed game state to a GameResult. Raises if game not complete."""
        if not self.is_complete:
            raise RuntimeError("Game is not yet complete. Call simulate_to_end() or play to completion first.")
        return GameResult(
            game_set=self.state.ruleset.game_set.value,
            away_score=self.state.away_score,
            home_score=self.state.home_score,
            innings=list(self.state.completed_half_innings),
            away_box=list(self.state.away_box.values()),
            home_box=list(self.state.home_box.values()),
        )

    # ------------------------------------------------------------------
    # Internal state mutation
    # ------------------------------------------------------------------

    def _apply_at_bat_result(self, ab: AtBatResult, new_runners: dict[int, str]) -> None:
        """Mutate self.state to reflect a completed at-bat."""
        state = self.state
        is_out = ab.outcome in _OUT_OUTCOMES

        # Update box scores
        self._update_box_scores(ab, is_out)

        # Advance batting cursor
        if state.is_top_half:
            state.away_cursor += 1
        else:
            state.home_cursor += 1

        # Accumulate at-bat in current half-inning
        state.current_half_at_bats.append(ab)

        if is_out:
            state.outs += 1
            if state.outs >= 3:
                self._end_half_inning()
                return
            # Runners don't advance on outs (already handled by advance_runners)
            state.runners = new_runners
        else:
            state.runners = new_runners

        # Walk-off: home team leads after bottom of final inning
        if not state.is_top_half and state.home_score > state.away_score:
            final_inning = state.ruleset.innings
            if state.current_inning >= final_inning:
                self._end_half_inning()

    def _end_half_inning(self) -> None:
        """Close the current half-inning and check for game end."""
        state = self.state
        half = HalfInningResult(
            inning=state.current_inning,
            is_top=state.is_top_half,
            at_bats=list(state.current_half_at_bats),
        )
        state.completed_half_innings.append(half)
        state.current_half_at_bats = []
        state.runners = {}
        state.outs = 0

        if state.is_top_half:
            # Top half done — switch to bottom
            state.is_top_half = False
        else:
            # Bottom half done — check for game end
            final_inning = state.ruleset.innings
            if state.current_inning >= final_inning:
                tied = state.away_score == state.home_score
                if not tied or not state.ruleset.extra_innings:
                    state.status = GameStatus.COMPLETE
                    return
            state.current_inning += 1
            state.is_top_half = True

    def _update_box_scores(self, ab: AtBatResult, is_out: bool) -> None:
        """Update batting and pitching box score entries for this at-bat."""
        state = self.state
        bat_box = state.batting_team_box
        pit_box = state.fielding_team_box

        # Batter box score
        batter_name = ab.batter_name
        if batter_name not in bat_box:
            bat_box[batter_name] = PlayerBoxScore(name=batter_name)
        bs = bat_box[batter_name]

        if ab.outcome != ChartCategory.BB:
            bs.ab += 1
        if ab.is_hit:
            bs.hits += 1
        if ab.outcome == ChartCategory._2B:
            bs.doubles += 1
        elif ab.outcome == ChartCategory._3B:
            bs.triples += 1
        elif ab.outcome == ChartCategory.HR:
            bs.home_runs += 1
        elif ab.outcome == ChartCategory.BB:
            bs.walks += 1
        if ab.outcome == ChartCategory.SO:
            bs.strikeouts += 1
        bs.rbi += ab.rbi
        if ab.stolen_base_success:
            bs.stolen_bases += 1

        # Pitcher box score
        pitcher_name = ab.pitcher_name
        if pitcher_name not in pit_box:
            pit_box[pitcher_name] = PlayerBoxScore(
                name=pitcher_name,
                outs_recorded=0,
                runs_allowed=0,
                pitcher_strikeouts=0,
                pitcher_walks=0,
            )
        ps = pit_box[pitcher_name]
        if is_out:
            ps.outs_recorded = (ps.outs_recorded or 0) + 1
        ps.runs_allowed = (ps.runs_allowed or 0) + ab.runs_scored
        if ab.outcome == ChartCategory.SO:
            ps.pitcher_strikeouts = (ps.pitcher_strikeouts or 0) + 1
        if ab.outcome == ChartCategory.BB:
            ps.pitcher_walks = (ps.pitcher_walks or 0) + 1


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _to_lineup(
    source: list[ShowdownPlayerCard] | ShowdownTeam | None,
    label: str,
) -> Lineup:
    if source is None:
        raise ValueError(f"'{label}' team/cards must be provided.")
    if isinstance(source, ShowdownTeam):
        return Lineup.from_team(source)
    return Lineup.from_cards(source)


def _stolen_bases_this_game(state: GameState, player_name: str) -> int:
    box = state.away_box if state.is_top_half else state.home_box
    entry = box.get(player_name)
    return entry.stolen_bases if entry else 0
