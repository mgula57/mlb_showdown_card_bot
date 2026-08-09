from typing import Optional

from pydantic import BaseModel

from ..shared.player_position import PlayerSubType, PlayerType
from .models import SeasonSimulationResult
from .reporting import HITTER_CATEGORIES, PITCHER_CATEGORIES
from .stats import SimStatLine, StatCategory, Stats


class AwardWinner(BaseModel):
    category: str            # "MVP" | "CY_YOUNG" | "ROY" | "SILVER_SLUGGER"
    league: str
    position: Optional[str] = None   # SILVER SLUGGER ONLY
    value: float                     # THE DECIDING METRIC, FOR SORTING
    value_label: str                 # FORMATTED FOR DISPLAY, E.G. "2.87 ERA"
    player: SimStatLine


class SeasonAwards(BaseModel):
    mvp: list[AwardWinner] = []
    cy_young: list[AwardWinner] = []
    rookie_of_year: list[AwardWinner] = []
    silver_sluggers: list[AwardWinner] = []


class AwardsBuilder:
    """Computes end-of-season awards from a finished season's full player pool - one set per
    league, mirroring how the real awards are split.

    None of these are the real voting criteria (there are no all-star ballots or beat-writer
    votes in the sim), so each category picks a single deciding stat already materialized
    elsewhere in the pipeline:
      - MVP: wRC+ weighted by playing time, with a small bump for defensive value. Hitters only -
        wRC+ has no pitcher equivalent.
      - Cy Young: lowest ERA among qualified pitchers (starters and relievers together).
      - Rookie of the Year: highest Showdown points among qualified rookies. Best-effort - the
        card's `is_rookie` flag is only reliably populated for MLB-API-sourced seasons (2026+), so
        a league with nobody flagged simply has no RoY rather than a guessed one.
      - Silver Slugger: highest OPS per position, one per league. The engine's fielding model
        never assigns a bare LF or RF - only the combined `LF/RF` slot, or CF/OF (see
        `Position.is_valid_in_game`) - so outfield gets one combined LF/RF award instead of the
        real three.
    """

    _SILVER_SLUGGER_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'CF', 'LF/RF', 'DH']
    _DEFENSE_BOOST_PER_POINT = 0.01  # EACH +1 CARD DEFENSE RATING NUDGES MVP SCORE UP 1%

    def __init__(self, result: SeasonSimulationResult) -> None:
        self.result = result

    # ------------------------------------------------------------------
    # LEAGUE / QUALIFICATION
    # ------------------------------------------------------------------

    @property
    def _team_leagues(self) -> dict[str, str]:
        return {
            record.name: record.league
            for records in self.result.standings.divisions.values()
            for record in records
            if record.league
        }

    @property
    def leagues(self) -> list[str]:
        return sorted(set(self._team_leagues.values()))

    def _players_in_league(self, league: str, player_type: PlayerType) -> list[Stats]:
        team_leagues = self._team_leagues
        return [
            s for s in self.result.player_stats
            if s.player_type == player_type and team_leagues.get(s.team) == league
        ]

    def _qualified_hitters(self, league: str) -> list[Stats]:
        return [s for s in self._players_in_league(league, PlayerType.HITTER) if s.stat(StatCategory.PA) >= self.result.stats_min_pa]

    def _qualified_pitchers(self, league: str) -> list[Stats]:
        starters = [
            s for s in self._players_in_league(league, PlayerType.PITCHER)
            if s.player_sub_type == PlayerSubType.STARTING_PITCHER and s.stat(StatCategory.IP) >= self.result.stats_min_ip
        ]
        relievers = [
            s for s in self._players_in_league(league, PlayerType.PITCHER)
            if s.player_sub_type == PlayerSubType.RELIEF_PITCHER and s.stat(StatCategory.IP) >= self.result.stats_min_ip_rp
        ]
        return starters + relievers

    # ------------------------------------------------------------------
    # STATLINE MATERIALIZATION
    # ------------------------------------------------------------------

    def _line(self, stats: Stats, player_type: PlayerType) -> SimStatLine:
        return SimStatLine.build(
            stats=stats,
            categories=HITTER_CATEGORIES if player_type == PlayerType.HITTER else PITCHER_CATEGORIES,
            league_stats=self.result.league_totals.get(player_type.value),
            woba_weights=self.result.woba_weights,
        )

    def _mvp_score(self, stats: Stats) -> float:
        league_stats = self.result.league_totals.get(PlayerType.HITTER.value)
        wrc_plus = stats.stat(StatCategory.wRC_PLUS, league_stats=league_stats, woba_weights=self.result.woba_weights)
        games = stats.stat(StatCategory.G)
        playing_time_pct = (games / self.result.schedule_length) if self.result.schedule_length else 0
        return wrc_plus * playing_time_pct * (1 + self._DEFENSE_BOOST_PER_POINT * stats.defense)

    # ------------------------------------------------------------------
    # CATEGORIES
    # ------------------------------------------------------------------

    def mvp(self) -> list[AwardWinner]:
        winners = []
        for league in self.leagues:
            candidates = self._qualified_hitters(league)
            if not candidates:
                continue
            best = max(candidates, key=self._mvp_score)
            score = self._mvp_score(best)
            winners.append(AwardWinner(
                category='MVP', league=league, value=round(score, 1),
                value_label=f"{round(score)} MVP score",
                player=self._line(best, PlayerType.HITTER),
            ))
        return winners

    def cy_young(self) -> list[AwardWinner]:
        winners = []
        for league in self.leagues:
            candidates = self._qualified_pitchers(league)
            if not candidates:
                continue
            best = min(candidates, key=lambda s: s.era)
            winners.append(AwardWinner(
                category='CY_YOUNG', league=league, value=best.era,
                value_label=f"{best.era:.2f} ERA",
                player=self._line(best, PlayerType.PITCHER),
            ))
        return winners

    def rookie_of_year(self) -> list[AwardWinner]:
        winners = []
        for league in self.leagues:
            candidates = [s for s in (self._qualified_hitters(league) + self._qualified_pitchers(league)) if s.is_rookie]
            if not candidates:
                continue  # BEST EFFORT - OMITTED WHEN THE SEASON NEVER POPULATED is_rookie
            best = max(candidates, key=lambda s: s.points)
            winners.append(AwardWinner(
                category='ROY', league=league, value=float(best.points),
                value_label=f"{best.points} PTS",
                player=self._line(best, best.player_type),
            ))
        return winners

    def silver_sluggers(self) -> list[AwardWinner]:
        winners = []
        for league in self.leagues:
            candidates = self._qualified_hitters(league)
            for position in self._SILVER_SLUGGER_POSITIONS:
                at_position = [s for s in candidates if s.position == position]
                if not at_position:
                    continue
                best = max(at_position, key=lambda s: s.ops)
                winners.append(AwardWinner(
                    category='SILVER_SLUGGER', league=league, position=position, value=best.ops,
                    value_label=f"{best.ops:.3f} OPS",
                    player=self._line(best, PlayerType.HITTER),
                ))
        return winners

    def build(self) -> SeasonAwards:
        return SeasonAwards(
            mvp=self.mvp(),
            cy_young=self.cy_young(),
            rookie_of_year=self.rookie_of_year(),
            silver_sluggers=self.silver_sluggers(),
        )
