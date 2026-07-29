from datetime import date
from random import Random
from typing import Callable, Optional

from ..shared.player_position import PositionSlot
from .inning import Inning
from .models import GameLogEntry, GameResult
from .plate_appearance import PlateAppearance
from .stats import StatCategory

_RUNS_SCORED = StatCategory.RUNS_SCORED.value


class Game:

    def __init__(self, index: int, date: date, home_team_name: str, away_team_name: str, home_team_game_number: int, away_team_game_number: int) -> None:
        self.index = index
        self.date = date
        self.home_team_name = home_team_name
        self.away_team_name = away_team_name
        self.home_team_game_number = int(home_team_game_number)
        self.away_team_game_number = int(away_team_game_number)
        self.is_game_over = False
        self.home_team_final_score = 0
        self.away_team_final_score = 0
        self.logs: list[GameLogEntry] = []

    def setup(self, home_team, away_team) -> None:
        self.innings = [Inning(inning=1, is_top=True)]
        self.plate_appearances = []
        home_team.add_new_game(game=self, opposing_team=away_team)
        away_team.add_new_game(game=self, opposing_team=home_team)
        home_team.mark_pitcher_entered(home_team.rotation.current_pitcher, 1)
        away_team.mark_pitcher_entered(away_team.rotation.current_pitcher, 1)
        self.home_team = home_team
        self.away_team = away_team

        self.logs = []

    def simulate(self, rng: Random, collect_log: bool = False, log_callback: Optional[Callable[[str], None]] = None):

        while not self.is_game_over:

            # DEFINE CURRENT PLATE APPEARANCE OBJECTS
            inning = self.innings[-1]
            team_pitching = self.home_team if inning.is_top else self.away_team
            team_hitting = self.away_team if inning.is_top else self.home_team
            team_pitching.check_for_pitcher_sub(game_date=self.date, inning=inning, runs_allowed=team_hitting.current_game_stats.totals.get(_RUNS_SCORED, 0))
            pitcher = team_pitching.current_pitcher()
            hitter = team_hitting.current_hitter(game=self)
            plate_appearance = PlateAppearance(hitter=hitter, pitcher=pitcher, inning=inning, rng=rng, was_last_result_single_plus=False)

            # ROLL THE DICE
            plate_appearance.check_and_execute_steal(catcher=team_pitching.catcher)
            plate_appearance.execute_pitch()
            plate_appearance.execute_swing()
            plate_appearance.check_and_execute_double_play(infield_defense=team_pitching.infield_defense)
            plate_appearance.check_and_execute_advance(outfield_defense=team_pitching.outfield_defense)

            # UPDATE OBJECTS BASED ON RESULT
            inning.runners = plate_appearance.runners
            inning.outs += plate_appearance.outs

            if plate_appearance.runs_scored:
                team_hitting.current_game_stats.add_stat(StatCategory.RUNS_SCORED, plate_appearance.runs_scored)
                team_pitching.current_game_stats.add_stat(StatCategory.RUNS_ALLOWED, plate_appearance.runs_scored)

            # UPDATE STATS
            team_hitting.log_player_appearance(game=self,player_id=hitter.id)
            team_pitching.log_player_appearance(game=self,player_id=pitcher.id)
            team_hitting.stats.update_stats_for_player(player=hitter, additional_stats=plate_appearance.hitter_stats)
            team_hitting.stats.merge_stats_dict(stats_dict=plate_appearance.runner_steals_stats_dict)
            team_hitting.stats.merge_stats_dict(stats_dict=plate_appearance.runner_advances_stats_dict)
            team_hitting.stats.merge_stats_dict(stats_dict=plate_appearance.double_play_stats_dict(is_pitcher=False))
            team_pitching.stats.update_stats_for_player(player=pitcher, additional_stats=plate_appearance.pitcher_stats)
            team_pitching.stats.merge_stats_dict(stats_dict=plate_appearance.prior_pitcher_stats_dict())
            team_pitching.update_pitcher_runs_allowed(plate_appearance.pitcher_runs_allowed)
            team_pitching.stats.merge_stats_dict(stats_dict=plate_appearance.double_play_stats_dict(is_pitcher=True))
            home_score = self.home_team.current_game_stats.totals.get(_RUNS_SCORED, 0)
            away_score = self.away_team.current_game_stats.totals.get(_RUNS_SCORED, 0)

            if not plate_appearance.swing.is_empty():
                team_hitting.update_lineup_index()

            if collect_log or log_callback:
                log_entry = GameLogEntry(
                    inning=inning.inning,
                    is_top=inning.is_top,
                    outs=inning.outs,
                    bases=inning.runners.base_squares_str(),
                    away_score=int(away_score),
                    home_score=int(home_score),
                    pitcher=plate_appearance.pitcher.name,
                    hitter=plate_appearance.hitter.name,
                    pitch_roll=plate_appearance.pitch.roll,
                    pitch_result=plate_appearance.pitch.result.value,
                    swing_roll=plate_appearance.swing.roll,
                    swing_result=plate_appearance.swing.result.value,
                    detail=plate_appearance.detail_str.strip(),
                    summary=f"{inning.summary_str}  {self.away_team.name}:{away_score}|{self.home_team.name}:{home_score}  {plate_appearance.summary_str()}",
                )
                if collect_log:
                    self.logs.append(log_entry)
                if log_callback:
                    log_callback(log_entry.summary)

            is_3_outs = inning.outs >= 3

            if is_3_outs:
                if (inning.inning >= 9 and inning.is_top and home_score > away_score) or ((not inning.is_top) and inning.inning >= 9 and away_score > home_score):
                    self.finalize_game()
                else:
                    if log_callback:
                        log_callback('---------------')
                    inning_num = inning.inning + (0 if inning.is_top else 1)
                    self.innings.append(Inning(inning=inning_num, is_top=(not inning.is_top)))

            if inning.inning >= 9 and (not inning.is_top) and home_score > away_score:
                self.finalize_game()

    def finalize_game(self):

        self.away_team.finalize_stats_post_game(game=self)
        self.home_team.finalize_stats_post_game(game=self)
        self.home_team_final_score = self.home_team.current_game_stats.totals.get(_RUNS_SCORED, 0)
        self.away_team_final_score = self.away_team.current_game_stats.totals.get(_RUNS_SCORED, 0)
        self.is_game_over = True

    @property
    def winning_team(self):
        if not self.is_game_over:
            return None

        return self.away_team if self.away_team_final_score > self.home_team_final_score else self.home_team

    def as_result(self) -> GameResult:
        return GameResult(
            index=self.index,
            date=self.date,
            home_team=self.home_team_name,
            away_team=self.away_team_name,
            home_score=int(self.home_team_final_score),
            away_score=int(self.away_team_final_score),
            winner=self.winning_team.name if self.is_game_over else None,
            log=self.logs,
        )
