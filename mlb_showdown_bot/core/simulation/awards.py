from typing import Optional

from pydantic import BaseModel

from ..card.team_builder.team import CardSource
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
      - MVP: wRC+ weighted by playing time, with small bumps for defensive value and net base
        stealing. Hitters only - wRC+ has no pitcher equivalent.
      - Cy Young: runs saved below the league-average ERA, scaled by innings pitched (see
        `_cy_young_score`). A pure ERA race would hand the award to any reliever who ran a tiny
        sample of scoreless innings - weighting by IP means a reliever has to be truly
        exceptional (elite ERA AND a heavy workload for the role) to beat a workhorse starter.
      - Rookie of the Year: reuses the MVP score for rookie hitters and the Cy Young score for
        rookie pitchers, then picks whichever rookie ranks higher by percentile within their own
        type's full qualified pool - i.e. "how dominant were you relative to your peers,"
        which is comparable across hitters and pitchers even though the raw scores aren't.
        Best-effort - the card's `is_rookie` flag is only reliably populated for MLB-API-sourced
        seasons (2026+), so a league with nobody flagged simply has no RoY rather than a guessed
        one.
      - Silver Slugger: highest OPS per position, one per league. The engine's fielding model
        never assigns a bare LF or RF - only the combined `LF/RF` slot, or CF/OF (see
        `Position.is_valid_in_game`) - so outfield gets one combined LF/RF award instead of the
        real three.
    """

    _SILVER_SLUGGER_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'CF', 'LF/RF', 'DH']
    _DEFENSE_BOOST_PER_POINT = 0.01     # EACH +1 CARD DEFENSE RATING NUDGES MVP SCORE UP 1%
    _NET_SB_BOOST_PER_STEAL = 0.001     # EACH NET STOLEN BASE (SB - CS) NUDGES MVP SCORE UP 0.1%

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

    @property
    def _takeover_player_leagues(self) -> dict[str, str]:
        """Player id -> league, for a takeover roster's own players.

        Statlines report the builder team's own abbreviation rather than the replaced club's
        schedule key (see `SimTeam.from_builder_team`), so `_team_leagues.get(s.team)` never
        finds them. Resolve by roster membership instead, mirroring
        `SeasonSummaryBuilder.roster_player_ids`.
        """
        takeover_team = self.result.config.takeover_team
        if takeover_team is None:
            return {}
        league = self._team_leagues.get(self.result.config.takeover_replaces_abbr)
        if league is None:
            return {}
        return {slot.card_id: league for slot in takeover_team.roster}

    def _players_in_league(self, league: str, player_type: PlayerType) -> list[Stats]:
        team_leagues = self._team_leagues
        takeover_leagues = self._takeover_player_leagues
        return [
            s for s in self.result.player_stats
            if s.player_type == player_type and (takeover_leagues.get(s.id) or team_leagues.get(s.team)) == league
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
            card_source=self.result.config.card_sources.get(stats.id, CardSource.BOT.value),
        )

    def _mvp_score(self, stats: Stats) -> float:
        league_stats = self.result.league_totals.get(PlayerType.HITTER.value)
        wrc_plus = stats.stat(StatCategory.wRC_PLUS, league_stats=league_stats, woba_weights=self.result.woba_weights)
        games = stats.stat(StatCategory.G)
        playing_time_pct = (games / self.result.schedule_length) if self.result.schedule_length else 0
        net_steals = stats.stat(StatCategory.SB) - stats.stat(StatCategory.CS)
        defense_bonus = self._DEFENSE_BOOST_PER_POINT * stats.defense
        baserunning_bonus = self._NET_SB_BOOST_PER_STEAL * net_steals
        return wrc_plus * playing_time_pct * (1 + defense_bonus + baserunning_bonus)

    def _cy_young_score(self, stats: Stats) -> float:
        """Runs saved below the league-average ERA, scaled by innings pitched.

        Plain ERA rewards a reliever's small sample as much as a starter's full workload -
        (league ERA - ERA) * (IP / 9) is the earned runs they saved versus a league-average
        pitcher who threw exactly as many innings, so a short, dominant relief season only
        outscores a good, deep starting season if it's truly special.
        """
        league_stats = self.result.league_totals.get(PlayerType.PITCHER.value)
        league_era = league_stats.era if league_stats else 0.0
        if league_era <= 0:
            return -stats.era
        ip = stats.stat(StatCategory.IP)
        return (league_era - stats.era) * (ip / 9)

    @staticmethod
    def _percentile_rank(value: float, population: list[float]) -> float:
        """Fraction of `population` that `value` meets or beats - a unitless [0, 1] score that
        lets MVP-scale and Cy-Young-scale numbers be compared on equal footing for RoY."""
        if not population:
            return 0.0
        return sum(1 for v in population if v <= value) / len(population)

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
            best = max(candidates, key=self._cy_young_score)
            ip = best.stat(StatCategory.IP)
            winners.append(AwardWinner(
                category='CY_YOUNG', league=league, value=round(self._cy_young_score(best), 1),
                value_label=f"{best.era:.2f} ERA, {ip:.0f} IP",
                player=self._line(best, PlayerType.PITCHER),
            ))
        return winners

    def rookie_of_year(self) -> list[AwardWinner]:
        winners = []
        for league in self.leagues:
            all_hitters = self._qualified_hitters(league)
            all_pitchers = self._qualified_pitchers(league)
            rookie_hitters = [s for s in all_hitters if s.is_rookie]
            rookie_pitchers = [s for s in all_pitchers if s.is_rookie]
            if not rookie_hitters and not rookie_pitchers:
                continue  # BEST EFFORT - OMITTED WHEN THE SEASON NEVER POPULATED is_rookie

            candidates = []
            if rookie_hitters:
                best_hitter = max(rookie_hitters, key=self._mvp_score)
                score = self._mvp_score(best_hitter)
                percentile = self._percentile_rank(score, [self._mvp_score(s) for s in all_hitters])
                candidates.append((percentile, best_hitter, score, f"{round(score)} MVP score"))
            if rookie_pitchers:
                best_pitcher = max(rookie_pitchers, key=self._cy_young_score)
                score = self._cy_young_score(best_pitcher)
                percentile = self._percentile_rank(score, [self._cy_young_score(s) for s in all_pitchers])
                candidates.append((percentile, best_pitcher, score, f"{best_pitcher.era:.2f} ERA, {best_pitcher.stat(StatCategory.IP):.0f} IP"))

            _, best, score, label = max(candidates, key=lambda c: c[0])
            winners.append(AwardWinner(
                category='ROY', league=league, value=round(score, 1),
                value_label=label,
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
