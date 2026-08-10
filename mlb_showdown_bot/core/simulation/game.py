from datetime import date
from random import Random
from typing import Callable, Optional

from ..shared.player_position import PlayerType
from .inning import Inning
from .models import (
    BoxScoreBattingStats,
    BoxScoreBatter,
    BoxScorePitcher,
    BoxScorePitchingStats,
    GameLogEntry,
    GameResult,
    GameStartState,
    InningLineScore,
    LineScoreResult,
    TeamBoxScore,
    TeamLineScoreTotals,
)
from .plate_appearance import PlateAppearance
from .stats import StatCategory

_RUNS_SCORED = StatCategory.RUNS_SCORED.value

_ORDINAL_SUFFIXES = {1: "st", 2: "nd", 3: "rd"}


def _ordinal(n: int) -> str:
    suffix = "th" if 11 <= n % 100 <= 13 else _ORDINAL_SUFFIXES.get(n % 10, "th")
    return f"{n}{suffix}"


def _ip_string(outs: int) -> str:
    return f"{outs // 3}.{outs % 3}"


def _batting_summary(stats) -> str:
    hits = int(stats.stat(StatCategory.HITS))
    at_bats = int(stats.stat(StatCategory.AB))
    doubles = int(stats.stat(StatCategory.DOUBLES))
    triples = int(stats.stat(StatCategory.TRIPLES))
    home_runs = int(stats.stat(StatCategory.HOMERUNS))
    rbi = int(stats.stat(StatCategory.RBI))
    bb = int(stats.stat(StatCategory.BB))
    extras = []
    if doubles: extras.append(f"{doubles} 2B" if doubles > 1 else "2B")
    if triples: extras.append(f"{triples} 3B" if triples > 1 else "3B")
    if home_runs: extras.append(f"{home_runs} HR" if home_runs > 1 else "HR")
    if rbi: extras.append(f"{rbi} RBI")
    if bb: extras.append(f"{bb} BB" if bb > 1 else "BB")
    extra_str = f", {', '.join(extras)}" if extras else ""
    return f"{hits}-{at_bats}{extra_str}"


def _pitching_summary(stats, outs: int) -> str:
    earned_runs = int(stats.stat(StatCategory.EARNED_RUNS))
    strike_outs = int(stats.stat(StatCategory.SO))
    return f"{_ip_string(outs)} IP, {earned_runs} ER, {strike_outs} K"


def _sum_batting_stats(rows: list) -> BoxScoreBattingStats:
    totals = BoxScoreBattingStats()
    for row in rows:
        totals.at_bats += row.stats.at_bats
        totals.runs += row.stats.runs
        totals.hits += row.stats.hits
        totals.doubles += row.stats.doubles
        totals.triples += row.stats.triples
        totals.home_runs += row.stats.home_runs
        totals.rbi += row.stats.rbi
        totals.base_on_balls += row.stats.base_on_balls
        totals.strike_outs += row.stats.strike_outs
        totals.stolen_bases += row.stats.stolen_bases
        totals.caught_stealing += row.stats.caught_stealing
        totals.ground_into_double_play += row.stats.ground_into_double_play
        totals.plate_appearances += row.stats.plate_appearances
    return totals


def _sum_pitching_stats(rows: list) -> BoxScorePitchingStats:
    outs = sum(row.stats.outs for row in rows)
    earned_runs = sum(row.stats.earned_runs for row in rows)
    return BoxScorePitchingStats(
        innings_pitched=_ip_string(outs),
        outs=outs,
        hits=sum(row.stats.hits for row in rows),
        runs=earned_runs,
        earned_runs=earned_runs,
        base_on_balls=sum(row.stats.base_on_balls for row in rows),
        strike_outs=sum(row.stats.strike_outs for row in rows),
        home_runs=sum(row.stats.home_runs for row in rows),
        batters_faced=sum(row.stats.batters_faced for row in rows),
        era=round(9 * earned_runs / (outs / 3.0), 2) if outs > 0 else 0.0,
    )


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

        # SET IN `setup`. NON-None ONLY WHEN RESUMING A GAME ALREADY IN PROGRESS.
        self.start_state: Optional[GameStartState] = None

        # POPULATED IN `finalize_game` - THE LINESCORE IS ALWAYS BUILT, THE BOX SCORE ONLY WHEN
        # `_collect_box_score` IS SET (SEE `simulate`).
        self.linescore: Optional[LineScoreResult] = None
        self.home_box_score: Optional[TeamBoxScore] = None
        self.away_box_score: Optional[TeamBoxScore] = None
        self._collect_box_score = False

    def setup(self, home_team, away_team, start_state: Optional[GameStartState] = None) -> None:
        """Prepare both teams and the inning stack.

        Args:
          start_state: Mid-game state to resume from, for taking over a real game already in
            progress. Omitted (the season/tournament path) starts from the first pitch.
        """

        self.plate_appearances = []
        home_team.add_new_game(game=self, opposing_team=away_team)
        away_team.add_new_game(game=self, opposing_team=home_team)
        self.home_team = home_team
        self.away_team = away_team
        self.start_state = start_state

        self.logs = []

        if start_state is None:
            self.innings = [Inning(inning=1, is_top=True)]
            home_team.mark_pitcher_entered(home_team.rotation.current_pitcher, 1)
            away_team.mark_pitcher_entered(away_team.rotation.current_pitcher, 1)
            return

        # RESUME. THE COMPLETED HALF-INNINGS ARE REBUILT AS PLAYED FRAMES (`outs=3` IS WHAT MAKES
        # `Inning.is_played` TRUE FOR A SCORELESS ONE) SO `_build_linescore` RENDERS ONE CONTINUOUS
        # GAME RATHER THAN RESTARTING AT THE TAKEOVER INNING. THEIR BASERUNNERS ARE GONE, SO THE
        # LEFT-ON-BASE TOTAL COUNTS THE SIMULATED PORTION ONLY.
        self.innings = [
            Inning(inning=half.inning, is_top=half.is_top, outs=3, runs=half.runs)
            for half in start_state.completed_innings
        ]
        self.innings.append(Inning(
            inning=start_state.inning,
            is_top=start_state.is_top,
            outs=start_state.outs,
            runs=start_state.runs,
            runners=start_state.runners.model_copy(deep=True),
        ))
        home_team.resume_from(start_state.home)
        away_team.resume_from(start_state.away)

        # RUNS ALLOWED IS EACH SIDE'S VIEW OF THE OTHER'S SCORE. IT IS SEEDED HERE RATHER THAN IN
        # `resume_from` BECAUSE ONLY THE GAME KNOWS BOTH SIDES - AND `update_wins_and_losses`
        # DECIDES THE WINNER BY COMPARING THE TWO.
        home_team.current_game_stats.add_stat(StatCategory.RUNS_ALLOWED, start_state.away.runs_scored)
        away_team.current_game_stats.add_stat(StatCategory.RUNS_ALLOWED, start_state.home.runs_scored)

    def simulate(self, rng: Random, collect_log: bool = False, log_callback: Optional[Callable[[str], None]] = None, collect_box_score: bool = False):

        self._collect_box_score = collect_box_score

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
                inning.runs += plate_appearance.runs_scored
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
                narration = plate_appearance.narration
                log_entry = GameLogEntry(
                    inning=inning.inning,
                    is_top=inning.is_top,
                    outs=inning.outs,
                    bases=inning.runners.base_squares_str(),
                    away_score=int(away_score),
                    home_score=int(home_score),
                    pitcher=plate_appearance.pitcher.name,
                    pitcher_id=plate_appearance.pitcher.id,
                    hitter=plate_appearance.hitter.name,
                    hitter_id=plate_appearance.hitter.id,
                    runs_scored=int(plate_appearance.runs_scored),
                    pitch_roll=plate_appearance.pitch.roll,
                    pitch_result=plate_appearance.pitch.result.value,
                    swing_roll=plate_appearance.swing.roll,
                    swing_result=plate_appearance.swing.result.value,
                    event=narration.event,
                    description=narration.description,
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

        if self.is_game_over:
            return

        self.away_team.finalize_stats_post_game(game=self)
        self.home_team.finalize_stats_post_game(game=self)
        self.home_team_final_score = self.home_team.current_game_stats.totals.get(_RUNS_SCORED, 0)
        self.away_team_final_score = self.away_team.current_game_stats.totals.get(_RUNS_SCORED, 0)
        self.linescore = self._build_linescore()
        if self._collect_box_score:
            self.home_box_score = self._build_team_box_score(self.home_team)
            self.away_box_score = self._build_team_box_score(self.away_team)
        self.is_game_over = True

    @property
    def winning_team(self):
        if not self.is_game_over:
            return None

        return self.away_team if self.away_team_final_score > self.home_team_final_score else self.home_team

    # ------------------------------------------------------------------
    # RESULT BUILDING
    # ------------------------------------------------------------------

    def _build_linescore(self) -> LineScoreResult:
        """Called from `finalize_game`, after final scores are set. Walks inning *numbers* rather
        than `self.innings` directly so a side that never batted an inning (home team ahead after
        the top of the 9th) reports `None` runs for it, matching the real MLB API - and so the
        phantom half-inning `simulate` can append right before a walk-off finalize (see
        `Inning.is_played`) is silently dropped rather than rendered as a real frame."""

        played = [i for i in self.innings if i.is_played]
        max_inning = max((i.inning for i in played), default=1)

        innings: list[InningLineScore] = []
        for num in range(1, max_inning + 1):
            top = next((i for i in played if i.inning == num and i.is_top), None)
            bottom = next((i for i in played if i.inning == num and not i.is_top), None)
            innings.append(InningLineScore(
                num=num,
                ordinal_num=_ordinal(num),
                away_runs=top.runs if top is not None else None,
                home_runs=bottom.runs if bottom is not None else None,
            ))

        # `team.stats` ONLY HOLDS WHAT THE SIMULATION ITSELF PRODUCED, SO A TAKEOVER ADDS BACK THE
        # HITS THE REAL GAME ALREADY RECORDED. RUNS NEED NO SUCH FIXUP - THE FINAL SCORES COME FROM
        # `current_game_stats`, WHICH `resume_from` SEEDS.
        away_carryover_hits = self.start_state.away.hits if self.start_state else 0
        home_carryover_hits = self.start_state.home.hits if self.start_state else 0
        away_hits = int(self.away_team.stats.aggregated_stats(type=PlayerType.HITTER).stat(StatCategory.HITS)) + away_carryover_hits
        home_hits = int(self.home_team.stats.aggregated_stats(type=PlayerType.HITTER).stat(StatCategory.HITS)) + home_carryover_hits
        away_lob = sum(i.runners.count() for i in played if i.is_top)
        home_lob = sum(i.runners.count() for i in played if not i.is_top)

        return LineScoreResult(
            innings=innings,
            scheduled_innings=max(9, max_inning),
            away=TeamLineScoreTotals(runs=int(self.away_team_final_score), hits=away_hits, errors=0, left_on_base=away_lob),
            home=TeamLineScoreTotals(runs=int(self.home_team_final_score), hits=home_hits, errors=0, left_on_base=home_lob),
        )

    def _build_team_box_score(self, team) -> TeamBoxScore:
        """Called from `finalize_game`, gated by `_collect_box_score`. `team.stats` is a per-game
        `StatsGroup` (rebuilt in `SimTeam.add_new_game`), so this is a snapshot into plain Pydantic
        rows rather than new accounting - reading it lazily later would see the *next* game's
        stats, since `add_new_game` rebinds rather than mutates it."""

        batting: list[BoxScoreBatter] = []
        for order_index, player in enumerate(team.batting_order, start=1):
            s = team.stats.stats_for_id(player.id)
            batting.append(BoxScoreBatter(
                id=player.id,
                name=player.name,
                position=player.position_slot.value,
                batting_order=order_index,
                is_substitute=False,
                is_in_lineup=True,
                stats=BoxScoreBattingStats(
                    at_bats=int(s.stat(StatCategory.AB)),
                    runs=int(s.stat(StatCategory.RUNS)),
                    hits=int(s.stat(StatCategory.HITS)),
                    doubles=int(s.stat(StatCategory.DOUBLES)),
                    triples=int(s.stat(StatCategory.TRIPLES)),
                    home_runs=int(s.stat(StatCategory.HOMERUNS)),
                    rbi=int(s.stat(StatCategory.RBI)),
                    base_on_balls=int(s.stat(StatCategory.BB)),
                    strike_outs=int(s.stat(StatCategory.SO)),
                    stolen_bases=int(s.stat(StatCategory.SB)),
                    caught_stealing=int(s.stat(StatCategory.CS)),
                    ground_into_double_play=int(s.stat(StatCategory.GDP)),
                    plate_appearances=int(s.stat(StatCategory.PA)),
                    summary=_batting_summary(s),
                ),
            ))

        pitching: list[BoxScorePitcher] = []
        for order_index, pitcher in enumerate(team._pitchers_used):
            s = team.stats.stats_for_id(pitcher.id)
            outs = int(round(s.stat(StatCategory.IP) * 3))
            pitching.append(BoxScorePitcher(
                id=pitcher.id,
                name=pitcher.name,
                position="SP" if order_index == 0 else "RP",
                order=order_index,
                is_substitute=order_index > 0,
                entered_in_inning=pitcher.start_inning,
                stats=BoxScorePitchingStats(
                    innings_pitched=_ip_string(outs),
                    outs=outs,
                    hits=int(s.stat(StatCategory.HITS)),
                    runs=int(s.stat(StatCategory.EARNED_RUNS)),   # THE SIM DOESN'T DISTINGUISH UNEARNED RUNS
                    earned_runs=int(s.stat(StatCategory.EARNED_RUNS)),
                    base_on_balls=int(s.stat(StatCategory.BB)),
                    strike_outs=int(s.stat(StatCategory.SO)),
                    home_runs=int(s.stat(StatCategory.HOMERUNS)),
                    batters_faced=int(s.stat(StatCategory.PA)),
                    era=s.era,
                    summary=_pitching_summary(s, outs),
                ),
            ))

        return TeamBoxScore(
            team=team.identity,
            batting=batting,
            pitching=pitching,
            batting_totals=_sum_batting_stats(batting),
            pitching_totals=_sum_pitching_stats(pitching),
        )

    def as_result(self) -> GameResult:
        innings_played = max((i.inning for i in self.innings if i.is_played), default=1)
        return GameResult(
            index=self.index,
            date=self.date,
            home_team=self.home_team_name,
            away_team=self.away_team_name,
            home_score=int(self.home_team_final_score),
            away_score=int(self.away_team_final_score),
            winner=self.winning_team.name if self.is_game_over else None,
            log=self.logs,
            home_team_identity=self.home_team.identity if self.is_game_over else None,
            away_team_identity=self.away_team.identity if self.is_game_over else None,
            linescore=self.linescore,
            home_box_score=self.home_box_score,
            away_box_score=self.away_box_score,
            innings_played=innings_played,
            is_extra_innings=innings_played > 9,
        )
