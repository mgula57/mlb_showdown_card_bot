from enum import Enum
from random import Random
from typing import Optional

from ..shared.player_position import PlayerType, PositionSlot
from .inning import Inning
from .models import NEUTRAL_MANAGER, ManagerPreference
from .narration import PlateAppearanceNarrator
from .player import SimPitcher, SimPlayer
from .result import Result
from .runners import Runner
from .stats import StatCategory, Stats


# PRE-RESOLVED StatCategory KEYS - THESE ARE LOOKED UP ON EVERY PLATE APPEARANCE
_PA = StatCategory.PA.value
_AB = StatCategory.AB.value
_HITS = StatCategory.HITS.value
_IP = StatCategory.IP.value
_EARNED_RUNS = StatCategory.EARNED_RUNS.value
_RBI = StatCategory.RBI.value
_RUNS = StatCategory.RUNS.value
_SB = StatCategory.SB.value
_CS = StatCategory.CS.value
_GDP = StatCategory.GDP.value
_GDPa = StatCategory.GDPa.value
_HADV = StatCategory.HITTER_ADVANTAGE.value
_PADV = StatCategory.PITCHER_ADVANTAGE.value
_OWN_CHART_OUT = StatCategory.OWN_CHART_OUT.value


def _stat_event(id: str, totals: dict[str, float], name: str = "", player_type=None, position=None, team=None, speed: int = 0, command: float = 0, positions_played: Optional[dict[str, int]] = None) -> Stats:
    """Build a per-event Stats line, skipping Pydantic validation.

    These are created several times per plate appearance from values the sim already controls, so
    validation is pure overhead here. Every field is passed explicitly because `model_construct`
    bypasses validators and field coercion.
    """
    return Stats.model_construct(
        id=id, name=name, player_type=player_type, position=position, team=team,
        points=0, speed=speed, command=command, real_ops=None, totals=totals,
        positions_played=positions_played or {},
    )


class PlateAppearanceState(Enum):
    PITCH = "p"
    SWING = "s"


class Roll:

    def __init__(self, roll=0, result=Result.NONE, runner: Runner = None, adjustment: int = 0, base: int = 0) -> None:
        self.roll = roll
        self.result = result
        self.runner = runner
        self.adjustment = adjustment
        # THE BASE THE RUNNER OCCUPIED WHEN THIS ROLL HAPPENED. CAPTURED BECAUSE A SUCCESSFUL STEAL
        # OR ADVANCE MUTATES `runner.base` IMMEDIATELY, SO READING IT BACK LATER (AS THE
        # PLAY-BY-PLAY NARRATION DOES) WOULD REPORT WHERE THEY ENDED UP, NOT WHERE THEY RAN FROM.
        self.base = base

    def is_empty(self) -> bool:
        return self.result == Result.NONE

class PlateAppearance:

    def __init__(self, hitter: SimPlayer, pitcher: SimPitcher, inning: Inning, rng: Random, was_last_result_single_plus: bool = False, manager: Optional[ManagerPreference] = None) -> None:
        self.state = PlateAppearanceState.PITCH
        self.hitter = hitter
        self.pitcher = pitcher
        self.rng = rng
        # THE HITTING TEAM'S MANAGER - GOVERNS THE DECISION TO ATTEMPT A STEAL OR SEND A RUNNER,
        # NEVER THE FAIRNESS ROLL. A NEUTRAL MANAGER IS AN EXACT NO-OP.
        self.manager = manager or NEUTRAL_MANAGER
        self.pitch = Roll()
        self.swing = Roll()
        self.double_play_roll = None
        self.steal_attempts = []
        self.advance_attempts = []
        self.runners = inning.runners
        self.outs_start = inning.outs
        self.outs = 0
        self.runs_scored = 0
        self.pitcher_runs_allowed = {} # KEY: pitcher_id, VALUE: num runs allowed
        self.runners_scored = []
        self.was_last_result_single_plus = was_last_result_single_plus
        # BASE STATE AS THE HITTER STEPPED IN, BEFORE ANY STEAL. `runners_before_swing` BELOW IS
        # TAKEN AFTER STEALS RESOLVE, SO IT CANNOT SEE A RUNNER CAUGHT STEALING - THEY'RE ALREADY
        # REMOVED FROM `self.runners` BY THEN. `retired_runners` WALKS BOTH SNAPSHOTS SO A
        # CAUGHT-STEALING RUNNER IS STILL ACCOUNTED FOR IN THE STRUCTURED GAME LOG, EVEN THOUGH
        # NARRATION DESCRIBES THEM SEPARATELY (VIA `steal_attempts`, NOT THIS DIFF).
        self.runners_at_start: list[tuple[str, str, int]] = [(r.id, r.name, r.base) for r in inning.runners.runners]
        # BASE STATE AS THE BALL WAS PUT IN PLAY - (id, name, base) TUPLES RATHER THAN THE Runner
        # OBJECTS, WHICH ARE MUTATED IN PLACE AS THE PLAY RESOLVES. THIS IS WHAT THE NARRATION
        # DIFFS AGAINST TO WORK OUT WHO ADVANCED, SCORED, OR WAS RETIRED. SET IN `execute_swing`,
        # AFTER ANY STEALS, SO A RUNNER WHO STOLE SECOND AND THEN TOOK THIRD ON A HIT IS DESCRIBED
        # AS DOING BOTH.
        self.runners_before_swing: list[tuple[str, str, int]] = []

    def execute_pitch(self) -> None:
        if self.total_outs < 3:
            random_adjustment = self.random_plus_or_minus_to_roll(occurance_probability=0.15)
            dice_roll = self.__random_dice_roll(adjustment=random_adjustment)
            total_pitch = dice_roll + self.pitcher.chart.command
            result = (Result.HITTER_ADVANTAGE if total_pitch <= self.hitter.chart.command else Result.PITCHER_ADVANTAGE)
            self.pitch = Roll(roll = dice_roll, result=result, adjustment=random_adjustment)

    def execute_swing(self) -> None:
        if self.total_outs < 3:
            player_with_advantage = self.hitter if self.pitch.result == Result.HITTER_ADVANTAGE else self.pitcher
            random_adjustment = self.random_plus_or_minus_to_roll(occurance_probability=0.35)
            dice_roll = self.__random_dice_roll(adjustment=random_adjustment)
            self.swing = Roll(roll = dice_roll, result=player_with_advantage.result_for_roll(dice_roll), adjustment=random_adjustment)
            self.runners_before_swing = [(runner.id, runner.name, runner.base) for runner in self.runners.runners]
            self.outs += int(self.swing.result.is_out)
            self.pitcher_runs_allowed, self.runners_scored = self.runners.move(result=self.swing.result,outs=self.total_outs,hitter=self.hitter,pitcher=self.pitcher, is_double_play_attempt=self.is_double_play_opportunity)
            self.runs_scored = sum(self.pitcher_runs_allowed.values())

    def random_plus_or_minus_to_roll(self, occurance_probability:float = 0.25) -> int:
        randomizer = self.rng.randint(1, 100)
        if randomizer <= occurance_probability * 100 / 2: return self.rng.randint(-2, 2)
        elif randomizer <= occurance_probability * 100 / 4: return self.rng.randint(-3, 3)
        elif randomizer <= occurance_probability * 100: return self.rng.randint(-1, 1)

        return 0

    def check_and_execute_double_play(self, infield_defense: int) -> None:
        """ Validate situation calls for double play attempt. Return Roll object. """

        if not self.is_double_play_opportunity:
            # NO OPPORTUNITY FOR DOUBLE PLAY
            return None

        dice_roll = self.__random_dice_roll()
        double_play_result = Result.OUT if ( (infield_defense + dice_roll) > self.hitter.speed ) else Result.SAFE
        runner = self.runners.runner_for_base(1)
        self.double_play_roll = Roll(roll=dice_roll, result=double_play_result, runner=runner)
        self.outs += int(double_play_result.is_out)

        # REMOVE RUNNER, REMOVE RUN IF 3 OUTS
        if double_play_result == Result.OUT:

            if self.total_outs == 3 and self.runs_scored > 0:
                self.runs_scored -= 1

                # REMOVE EARNED RUN
                pitcher_id = list(self.pitcher_runs_allowed.keys())[0]
                self.pitcher_runs_allowed[pitcher_id] = 0

                # REMOVE RUNNER
                self.runners_scored = []

    def check_and_execute_steal(self, catcher: SimPlayer) -> None:
        if self.runners.count() < 1 or self.runners.bases_occupied == [3]:
            return

        catcher_arm = catcher.defense_for_position_slot(PositionSlot.CA) if catcher else 0
        runner_on_first = self.runners.runner_for_base(1)
        runner_on_second = self.runners.runner_for_base(2)
        for runner in [runner_on_first, runner_on_second]:
            if runner:
                is_base_open = self.runners.runner_for_base(runner.base + 1) is None
                if is_base_open:
                    # DECIDE WHETHER TO SEND THE RUNNER BASED ON:
                    # 1. PROBABILITY OF BEING SAFE
                    # 2. OUTS IN THE INNING
                    # 3. BASE STEALING TO

                    # START AT 1% CHANCE
                    probability_of_steal_attempt = 1

                    # ADD RUNNER'S PROBABILITY OF SUCCESS, SCALED BY THE MANAGER'S STEAL AGGRESSION
                    # (`steal_attempt_factor` IS EXACTLY 1.0 FOR A NEUTRAL MANAGER).
                    runner_bonus = -5 if runner.base == 2 else 0
                    probability_of_safe = self.probability_of_advance(defense=catcher_arm, speed=runner.speed, runner_bonus=runner_bonus)
                    probability_of_steal_attempt += (probability_of_safe * 85) * self.manager.steal_attempt_factor

                    # REMOVE IF 2 OUTS AND RUNNER IS ON SECOND
                    if self.outs_start == 2 and runner.base == 2:
                        probability_of_steal_attempt -= 40

                    probability_of_steal_attempt = max(min(probability_of_steal_attempt, 90),1) # ALWAYS LEAVE ROOM TO NOT ATTEMPT
                    if probability_of_steal_attempt >= self.rng.randint(35, 100):
                        dice_roll = self.__random_dice_roll()
                        steal_result = Result.OUT if ( (catcher_arm + dice_roll) > (runner.speed + runner_bonus) ) else Result.SAFE
                        steal_roll = Roll(roll=dice_roll, result=steal_result, runner=runner, base=runner.base)
                        self.steal_attempts.append(steal_roll)
                        self.outs += int(steal_result.is_out)
                        if steal_result == Result.SAFE:
                            self.runners.advance_runner(runner.base)
                        else:
                            self.runners.remove_runner(runner.base)

    def check_and_execute_advance(self, outfield_defense:int, probability_threshold: Optional[float] = None) -> None:

        # THE MANAGER'S BASERUNNING AGGRESSION SETS THE SEND THRESHOLD; `advance_probability_threshold`
        # IS EXACTLY 0.5 (THE OLD DEFAULT) FOR A NEUTRAL MANAGER. AN EXPLICIT ARG STILL WINS.
        threshold = self.manager.advance_probability_threshold if probability_threshold is None else probability_threshold

        result_is_advancable = self.total_outs < 3 if self.swing.result == Result.FB else self.swing.result.is_advanceable
        if self.runners.count() < 1 or not result_is_advancable or self.runners.bases_occupied == [1]:
            # NO OPPORTUNITY FOR ADVANCE
            return

        runner_on_second = self.runners.runner_for_base(2) if not self.swing.result == Result.DOUBLE else None
        runner_on_third = self.runners.runner_for_base(3)
        for runner in [runner_on_second, runner_on_third]:
            if runner:
                is_base_open = self.runners.runner_for_base(runner.base + 1) is None
                if is_base_open:
                    match runner.base:
                        case 2: runner_bonus = -5
                        case 3: runner_bonus = (10 if self.outs_start == 2 else 5)
                        case _: runner_bonus = 0

                    probability_of_safe = self.probability_of_advance(defense=outfield_defense, speed=runner.speed, runner_bonus=runner_bonus)
                    if probability_of_safe >= threshold:
                        dice_roll = self.__random_dice_roll()
                        advance_result = Result.OUT if ( (outfield_defense + dice_roll) > (runner.speed + runner_bonus) ) else Result.SAFE
                        advance_roll = Roll(roll=dice_roll, result=advance_result, runner=runner, base=runner.base)
                        self.advance_attempts.append(advance_roll)
                        self.outs += int(advance_result.is_out)
                        if advance_result == Result.SAFE:
                            if (runner.base + 1) == 4:
                                self.runs_scored += 1
                                self.update_pitcher_runs_dict(pitcher_id=runner.pitcher_id)
                                self.runners_scored.append(runner)
                                self.runners.remove_runner(runner.base)
                            else:
                                self.runners.advance_runner(runner.base)
                        else:
                            self.runners.remove_runner(runner.base)

    def probability_of_advance(self, defense:int, speed:int, runner_bonus:int = 0):
        return max(0, (speed + runner_bonus - defense) / 20.0)

    def __random_dice_roll(self, adjustment: int = 0) -> int:
        return max( self.rng.randint(1, 20) + adjustment , 1 )

    @property
    def is_double_play_opportunity(self) -> bool:
        return self.total_outs < 3 and self.swing.result == Result.GB and (self.runners.runner_for_base(1) is not None)

    @property
    def _pitcher_had_advantage(self) -> bool:
        return self.pitch.result == Result.PITCHER_ADVANTAGE

    @property
    def _hitter_had_advantage(self) -> bool:
        return self.pitch.result == Result.HITTER_ADVANTAGE

    @property
    def pitcher_stats(self) -> Stats:
        return _stat_event(
            id=self.pitcher.id,
            name=self.pitcher.name,
            player_type=PlayerType.PITCHER,
            position=self.pitcher.position_slot.value,
            team=self.pitcher.team,
            command=self.pitcher.chart.command,
            totals={
                _PA: 1,
                _AB: int(self.swing.result.count_as_ab),
                _HITS: int(self.swing.result.is_hit),
                self.swing.result.value: 1,
                _IP: (self.outs / 3.0),
                _EARNED_RUNS: self.pitcher_runs_allowed.get(self.pitcher.id, 0),
                _HADV: int(self._hitter_had_advantage),
                _PADV: int(self._pitcher_had_advantage),
                _OWN_CHART_OUT: int(self._pitcher_had_advantage and self.swing.result.is_out),
            },
        )

    @property
    def hitter_stats(self) -> Stats:
        return _stat_event(
            id=self.hitter.id,
            name=self.hitter.name,
            player_type=PlayerType.HITTER,
            position=self.hitter.position_slot.value,
            team=self.hitter.team,
            command=self.hitter.chart.command,
            positions_played={self.hitter.position_slot.value: 1},
            totals={
                _PA: 1,
                _AB: int(self.swing.result.count_as_ab),
                _HITS: int(self.swing.result.is_hit),
                self.swing.result.value: 1,
                _RBI: 0 if self.outs > 1 else self.runs_scored,
                _HADV: int(self._hitter_had_advantage),
                _PADV: int(self._pitcher_had_advantage),
                _OWN_CHART_OUT: int(self._hitter_had_advantage and self.swing.result.is_out),
            },
        )

    @property
    def runner_steals_stats_dict(self) -> dict[str, Stats]:
        data: dict[str, Stats] = {}
        for steal_attempt in self.steal_attempts:
            runner = steal_attempt.runner
            key = _SB if steal_attempt.result == Result.SAFE else _CS
            existing = data.get(runner.id)
            if existing is None:
                data[runner.id] = _stat_event(id=runner.id, name=runner.name, player_type=PlayerType.HITTER, totals={key: 1})
            else:
                existing.totals[key] = existing.totals.get(key, 0) + 1
        return data

    @property
    def runner_advances_stats_dict(self) -> dict[str, Stats]:
        return {runner.id: _stat_event(id=runner.id, name=runner.name, player_type=PlayerType.HITTER, totals={_RUNS: 1}) for runner in self.runners_scored}

    @property
    def retired_runners(self) -> list[tuple[str, str, int, str]]:
        """Runners retired on the bases this plate appearance: (id, name, base retired AT, reason).
        `reason` is "steal" | "advance" | "forced" - "forced" covers a runner erased by a fielder's
        choice or double play with no throw/steal roll of their own. This is the single source both
        the narration ("X out at 2nd.") and the structured game log (`GameLogEntry.retired`) read,
        so the two can never disagree about WHO was retired - narration additionally uses `reason`
        to skip a redundant "forced" sentence when the batter's own DP/FC sentence already covers it.

        Walks BOTH `runners_at_start` (pre-steal) and `runners_before_swing` (post-steal,
        pre-swing) - see the comment on `runners_at_start` for why a caught-stealing runner needs
        the earlier snapshot.
        """
        scored_ids = {runner.id for runner in self.runners_scored}
        on_base_ids = {runner.id for runner in self.runners.runners}
        thrown_out = {attempt.runner.id: attempt.base for attempt in self.advance_attempts if attempt.result == Result.OUT}
        caught_stealing = {attempt.runner.id: attempt.base for attempt in self.steal_attempts if attempt.result == Result.OUT}

        retired: list[tuple[str, str, int, str]] = []
        seen_ids: set[str] = set()
        for runner_id, name, base in [*self.runners_at_start, *self.runners_before_swing]:
            if runner_id in seen_ids or runner_id == self.hitter.id or runner_id in scored_ids or runner_id in on_base_ids:
                continue
            seen_ids.add(runner_id)
            if runner_id in caught_stealing:
                retired.append((runner_id, name, caught_stealing[runner_id] + 1, "steal"))
            elif runner_id in thrown_out:
                retired.append((runner_id, name, thrown_out[runner_id] + 1, "advance"))
            else:
                retired.append((runner_id, name, base + 1, "forced"))
        return retired

    def double_play_stats_dict(self, is_pitcher: bool) -> dict[str, Stats]:
        if self.double_play_roll is None:
            return {}
        dp_runner = self.double_play_roll.runner
        stats_totals = {
            _GDP: int(self.double_play_roll.result.is_out),
            _GDPa: 1,
        }
        if is_pitcher:
            return {self.pitcher.id: _stat_event(id=self.pitcher.id, player_type=PlayerType.PITCHER, totals=stats_totals)}
        return {dp_runner.id: _stat_event(id=dp_runner.id, name=dp_runner.name, player_type=PlayerType.HITTER, speed=dp_runner.speed, totals=stats_totals)}

    def prior_pitcher_stats_dict(self) -> dict[str, Stats]:
        return {id: _stat_event(id=id, name=id, player_type=PlayerType.PITCHER, totals={_EARNED_RUNS: runs}) for id, runs in self.pitcher_runs_allowed.items() if id != self.pitcher.id}

    @property
    def total_outs(self) -> int:
        return self.outs_start + self.outs

    def last_steal_attempt(self) -> Roll:
        return None if len(self.steal_attempts) == 0 else self.steal_attempts[-1]

    def last_advance_attempt(self) -> Roll:
        return None if len(self.advance_attempts) == 0 else self.advance_attempts[-1]

    def update_pitcher_runs_dict(self, pitcher_id: str) -> None:
        existing_runs_allowed = self.pitcher_runs_allowed.get(pitcher_id, 0)
        self.pitcher_runs_allowed[pitcher_id] = existing_runs_allowed + 1

    @property
    def detail_str(self) -> str:
        """Extra events beyond the pitch/swing (steals, advances, double plays, roll adjustments)."""
        last_steal_attempt = self.last_steal_attempt()
        last_advance_attempt = self.last_advance_attempt()
        return \
            (f" (SB: {last_steal_attempt.result.value} | {last_steal_attempt.runner.name} SPD {last_steal_attempt.runner.speed})" if last_steal_attempt else "") \
            + (f" (ADV: {last_advance_attempt.result.value})" if last_advance_attempt else "") \
            + (f" (DP: {self.double_play_roll.result.value})" if self.double_play_roll else "") \
            + (f" (PADJ: {self.pitch.adjustment})" if self.pitch.adjustment else "") \
            + (f" (SADJ: {self.swing.adjustment})" if self.swing.adjustment else "") \
            + (f" (>20 SWING: {self.swing.roll})" if self.swing.roll > 20 else "")

    @property
    def narration(self) -> 'PlateAppearanceNarrator':
        """Reader-facing wording for this plate appearance. Only valid once every step has run."""
        return PlateAppearanceNarrator(self)

    def summary_str(self) -> str:
        return \
            f"{self.pitcher.name.split(' ')[-1]} v {self.hitter.name.split(' ')[-1]}   P:{self.pitch.result.value.upper()} ({self.pitch.roll})   S:{self.swing.result.value.upper()} ({self.swing.roll})" \
            + self.detail_str
