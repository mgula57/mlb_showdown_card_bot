from datetime import date, timedelta
from typing import Optional, Union

from pydantic import BaseModel, Field

from ..card.chart import Chart
from ..card.showdown_player_card import ShowdownPlayerCard
from ..shared.player_position import PlayerSubType, PlayerType, Position, PositionSlot
from .result import Result
from .runners import Runner

#-------------------------------------------------------

class SimPlayer(BaseModel):
    """A ShowdownPlayerCard wrapped with simulation state.

    The card itself is treated as immutable; all mutable per-game/per-season state
    (position slot, pitching usage) lives on the wrapper.
    """

    card: ShowdownPlayerCard
    id: str = None
    position_slot: PositionSlot = PositionSlot.NONE
    preset_lineup_spot: Optional[int] = None                 # BATTING ORDER (1-9) FROM A BUILDER TEAM LINEUP
    preset_position_slot: Optional[PositionSlot] = None      # FIELD POSITION FROM A BUILDER TEAM LINEUP
    results_list: list[Result] = Field(default_factory=list) # PRECOMPUTED ROLL (1-N) -> RESULT LOOKUP

    def model_post_init(self, __context) -> None:
        if self.id is None:
            self.id = self.card.id
        if len(self.results_list) == 0:
            self.results_list = [Result(category.value.lower()) for category in self.card.chart.results_as_list]

    # ------------------------------------------------------------------
    # CARD PASS-THROUGHS
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self.card.name

    @property
    def team(self) -> Optional[str]:
        return self.card.team.value if self.card.team else None

    @property
    def points(self) -> int:
        return self.card.points

    @property
    def speed(self) -> int:
        return self.card.speed.speed

    @property
    def chart(self) -> Chart:
        return self.card.chart

    @property
    def stats(self) -> dict:
        return self.card.stats

    @property
    def projected(self) -> dict:
        return self.card.projected

    @property
    def real_ops(self) -> Optional[float]:
        value = self.card.stats.get('onbase_plus_slugging', None)
        return float(value) if value is not None else None

    @property
    def player_type(self) -> PlayerType:
        return self.card.player_type

    @property
    def player_sub_type(self) -> PlayerSubType:
        return self.card.player_sub_type

    @property
    def positions_list(self) -> list[Position]:
        return self.card.positions_list

    @property
    def positions_and_defense(self) -> dict[Position, int]:
        return self.card.positions_and_defense

    @property
    def primary_position(self) -> Position:
        return self.card.primary_position

    def has_position(self, position: Position) -> bool:
        return self.card.has_position(position)

    def defense_for_position_slot(self, position_slot: PositionSlot) -> int:
        return self.card.defense_for_position_slot(position_slot)

    # ------------------------------------------------------------------
    # SIMULATION
    # ------------------------------------------------------------------

    def result_for_roll(self, roll: int) -> Result:
        """Chart result for a swing roll. Rolls above the chart's range use the last (best) result."""
        index = min(roll, len(self.results_list)) - 1
        return self.results_list[index]

    @property
    def expected_games_between_rest(self) -> int:
        """ Expected number of games between rest days.

        Player's with more value (PTS) will have longer periods between rest. Catchers will be lower than other positions.
        """

        # VARIABLES
        rest_multiplier = min([pos.rest_multiplier for pos in self.positions_list])
        max_rest = 15
        min_rest = 2
        max_pts = 500
        min_pts = 0
        pts_for_calc = min(max(self.points, 100), 500)

        # PCT RANK
        pts_percentile = (pts_for_calc - min_pts) / (max_pts - min_pts)
        rest_games = ( (max_rest - min_rest) * pts_percentile ) + min_pts
        rest_games_adjusted_for_ca = max(int(rest_multiplier * rest_games), 1)
        return rest_games_adjusted_for_ca

    def player_rest_rating(self, games_since_rest: int, add_pts_multiplier: bool = True) -> float:
        return (1.0 - (float(games_since_rest) / float(self.expected_games_between_rest))) * (max(self.stats.get("G", 70), 70) if add_pts_multiplier else 1.0)

    def convert_to_runner(self, base: int, pitcher_id: str) -> Runner:
        """ Converts player to runner object """
        return Runner(id=self.id, name=self.name, base=base, speed=self.speed, pitcher_id=pitcher_id)


class SimPitcher(SimPlayer):

    start_inning: Union[int, float, None] = None
    end_inning: Union[int, float, None] = None
    runs_allowed: int = 0

    @property
    def ip(self) -> int:
        return self.card.ip

    def innings_pitched(self, inning) -> float:
        return (self.end_inning or inning.inning_num_full) - (self.start_inning or 0)

    def is_tired(self, inning) -> bool:

        if self.start_inning == 0 and self.runs_allowed == 0 and self.ip == self.innings_pitched(inning):
            return False

        return (self.innings_pitched(inning) + int(self.runs_allowed / 3.0)) >= self.ip

    def situational_fit(self, ops_index: int, total_pitchers: int, run_diff: int, inning: int, recent_ip: float, is_save_situation: bool = False, is_closer: bool = False) -> float:
        """ Creates a situational fit rating, 1.0 being the best and 0.0 the worst fit

        Factors:
          1. Situation: Does the reliever fit the situation well?
          2. Rest: Has the pitcher pitched recently?

        Args:
          recent_ip: Innings this pitcher has thrown in the last few days.
        """

        staff_pct_rank = 1 - ( (ops_index + 1) / total_pitchers )

        score_tightness_pct_rank = 1 - ( abs(run_diff) / 6.0 )
        score_tightness_score_min = 0.5
        score_tightness_score = ( (1.0 - score_tightness_score_min) * (1 - abs(score_tightness_pct_rank - staff_pct_rank)) ) + score_tightness_score_min

        game_rp_completion_pct = min(max(inning - 5.0, 0.0) / 4.0, 1.0)
        game_completion_score_min = 0.4
        game_completion_score = ( (1.0 - game_completion_score_min) * (1 - abs(game_rp_completion_pct - staff_pct_rank)) ) + game_completion_score_min

        rest_multiplier = 1 - min(recent_ip / 3.1, 0.9)

        # REDUCE LIKELIHOOD OF PITCHING THE CLOSER IN A NON-SAVE SITUATION
        closer_fit_multiplier = 0.5 if is_closer and not is_save_situation else 1.0

        final_score = (score_tightness_score + game_completion_score) / 2.0 * rest_multiplier * closer_fit_multiplier

        return final_score

    def reset(self) -> None:
        self.start_inning = None
        self.end_inning = None
        self.runs_allowed = 0
