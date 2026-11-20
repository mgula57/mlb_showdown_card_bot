import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Optional

from .models import NPBPlayerTeamSeason


def _effective_games(s: dict) -> float:
    return s.get('eff_G') or s.get('G', 0) or 0

def _per_effective_game(numerator: Callable[[dict], float]) -> Callable[[dict], Optional[float]]:
    return lambda s: numerator(s) / _effective_games(s) if _effective_games(s) else None

def _chances(s: dict) -> float:
    return (s.get('PO', 0) or 0) + (s.get('A', 0) or 0) + (s.get('E', 0) or 0)

def _fielding_pct(s: dict) -> Optional[float]:
    chances = _chances(s)
    return ((s.get('PO', 0) or 0) + (s.get('A', 0) or 0)) / chances if chances else None

_RANGE = _per_effective_game(lambda s: (s.get('PO', 0) or 0) + (s.get('A', 0) or 0))
_ASSISTS = _per_effective_game(lambda s: s.get('A', 0) or 0)
_PASSED_BALLS = _per_effective_game(lambda s: s.get('PB', 0) or 0)


@dataclass(frozen=True)
class _Component:
    """One input to a position group's rating.
    value_fn: the rate stat. sample_fn: the sample it's based on. The rate is regressed toward the league
    mean by regression_k units of that sample before scoring."""
    name: str
    weight: float
    value_fn: Callable[[dict], Optional[float]]
    sample_fn: Callable[[dict], float]
    regression_k: float
    higher_is_better: bool = True


@dataclass(frozen=True)
class _PositionGroupConfig:
    components: list[_Component]
    # RUNS PER 150 GAMES THAT ONE STANDARD DEVIATION IS WORTH AMONG REGULARS, SIZED TO MATCH THE SPREAD OF
    # TZR/DRS AMONG MLB REGULARS SO THE RESULT FITS THE EXISTING TZR SCALE
    runs_sd_per_150: float


class NPBSyntheticDefense:
    """Synthetic defensive runs for NPB fielders, built from range factor and fielding percentage.

    NPB has no public play-by-play fielding metric (UZR/DRS/OAA), and the register only has the traditional
    fielding line (G, PO, A, E, DP; PB for catchers) with innings blank. Each position group is rated against
    the league's regulars that season:

      - Range: (PO + A) per game. For 1B, A per game (putouts at 1B are almost all routine throws).
        For C, A per game as an arm proxy (catcher assists are mostly caught stealing), plus passed balls.
      - Sure-handedness: fielding percentage.

    Games are converted to "effective" full games first: a defensive sub or platoon player is credited with a
    game for a few innings, which would otherwise read as poor range. Without innings, a player's share of full
    games is estimated from plate appearances per game relative to an everyday regular.

    Each component is regressed toward the league mean for small samples and z-scored; the weighted score is
    then standardized among regulars and scaled to runs per 150 games. The rating ('rf_fld') is a counting stat
    on the same scale as TZR, so the card's existing defense conversion applies unchanged.

    Outfield is one combined 'OF' line in NPB data, so center fielders are identified by range: each club's
    widest-ranging regular outfielder (when above the league outfield average), plus anyone far above average,
    is rated and listed as 'CF' against the other center fielders. Everyone else is a corner 'OF' (LF/RF).
    """

    REGULAR_MIN_EFFECTIVE_GAMES = 80    # MIN EFFECTIVE GAMES AT A POSITION TO COUNT AS A REGULAR FOR BASELINES
    REGULAR_MIN_PA = 400                # MIN PA TO DEFINE AN EVERYDAY PLAYER'S PA PER GAME
    MIN_FULL_GAME_SHARE = 0.25          # FLOOR ON THE ESTIMATED SHARE OF FULL GAMES PLAYED

    CF_MIN_GAMES = 40                   # MIN OF GAMES TO BE CLASSIFIED AS A CENTER FIELDER
    CF_TEAM_LEADER_MULTIPLIER = 1.05    # A CLUB'S TOP-RANGE OUTFIELDER IS ITS CF WHEN >= 105% OF THE LEAGUE OF RANGE
    CF_ANY_PLAYER_MULTIPLIER = 1.20     # ANY OUTFIELDER >= 120% OF THE LEAGUE OF RANGE IS A CF
    Z_CAP = 3.0

    GROUPS: dict[str, _PositionGroupConfig] = {
        'C':  _PositionGroupConfig([
                _Component('arm', 0.5, _ASSISTS, _effective_games, 30),
                _Component('passed_balls', 0.2, _PASSED_BALLS, _effective_games, 30, higher_is_better=False),
                _Component('fielding_pct', 0.3, _fielding_pct, _chances, 300),
              ], runs_sd_per_150=5.0),
        '1B': _PositionGroupConfig([
                _Component('range', 0.5, _ASSISTS, _effective_games, 20),
                _Component('fielding_pct', 0.5, _fielding_pct, _chances, 300),
              ], runs_sd_per_150=4.0),
        '2B': _PositionGroupConfig([
                _Component('range', 0.7, _RANGE, _effective_games, 20),
                _Component('fielding_pct', 0.3, _fielding_pct, _chances, 150),
              ], runs_sd_per_150=7.0),
        '3B': _PositionGroupConfig([
                _Component('range', 0.7, _RANGE, _effective_games, 20),
                _Component('fielding_pct', 0.3, _fielding_pct, _chances, 150),
              ], runs_sd_per_150=6.5),
        'SS': _PositionGroupConfig([
                _Component('range', 0.7, _RANGE, _effective_games, 20),
                _Component('fielding_pct', 0.3, _fielding_pct, _chances, 150),
              ], runs_sd_per_150=8.0),
        'CF': _PositionGroupConfig([
                _Component('range', 0.75, _RANGE, _effective_games, 20),
                _Component('fielding_pct', 0.25, _fielding_pct, _chances, 150),
              ], runs_sd_per_150=7.5),
        'OF': _PositionGroupConfig([
                _Component('range', 0.75, _RANGE, _effective_games, 20),
                _Component('fielding_pct', 0.25, _fielding_pct, _chances, 150),
              ], runs_sd_per_150=6.0),
    }

    def apply(self, rows: list[NPBPlayerTeamSeason]) -> None:
        """Adds 'eff_G' and 'rf_fld' to every non-pitcher fielding line, in place. Rows must be one full season
        (both leagues). Outfield lines identified as center field are moved from 'OF' to 'CF'."""
        self._set_effective_games(rows)
        self._split_center_field(rows)
        for group, config in self.GROUPS.items():
            lines = [row.fielding[group] for row in rows if group in row.fielding]
            self._rate_group(lines, config)

    # -------------------------
    # EFFECTIVE GAMES
    # -------------------------

    def _set_effective_games(self, rows: list[NPBPlayerTeamSeason]) -> None:
        regular_pa_per_game = [
            row.batting['PA'] / row.batting['G'] for row in rows
            if (row.batting.get('PA', 0) or 0) >= self.REGULAR_MIN_PA and row.batting.get('G')
        ]
        full_game_pa = statistics.median(regular_pa_per_game) if regular_pa_per_game else None
        for row in rows:
            games, plate_appearances = row.batting.get('G', 0) or 0, row.batting.get('PA', 0) or 0
            share = 1.0
            if full_game_pa and games:
                share = max(self.MIN_FULL_GAME_SHARE, min(1.0, (plate_appearances / games) / full_game_pa))
            for position, line in row.fielding.items():
                if position != 'P':
                    line['eff_G'] = round((line.get('G', 0) or 0) * share, 1)

    # -------------------------
    # CENTER FIELD
    # -------------------------

    def _split_center_field(self, rows: list[NPBPlayerTeamSeason]) -> None:
        outfielders = [row for row in rows if 'OF' in row.fielding and row.fielding['OF'].get('G', 0) >= self.CF_MIN_GAMES]
        regular_ranges = [_RANGE(r.fielding['OF']) for r in outfielders if _effective_games(r.fielding['OF']) >= self.REGULAR_MIN_EFFECTIVE_GAMES]
        if not regular_ranges:
            return
        league_range = statistics.mean(regular_ranges)

        by_team: dict[str, list[NPBPlayerTeamSeason]] = defaultdict(list)
        for row in outfielders:
            by_team[row.team].append(row)

        center_fielders: set[int] = set()
        for team_rows in by_team.values():
            ranked = sorted(team_rows, key=lambda r: (_RANGE(r.fielding['OF']) or 0) * min(1.0, _effective_games(r.fielding['OF']) / 100), reverse=True)
            if (_RANGE(ranked[0].fielding['OF']) or 0) >= league_range * self.CF_TEAM_LEADER_MULTIPLIER:
                center_fielders.add(id(ranked[0]))
            center_fielders.update(id(r) for r in team_rows if (_RANGE(r.fielding['OF']) or 0) >= league_range * self.CF_ANY_PLAYER_MULTIPLIER)

        for row in outfielders:
            if id(row) in center_fielders:
                row.fielding['CF'] = row.fielding.pop('OF')

    # -------------------------
    # RATING
    # -------------------------

    def _rate_group(self, lines: list[dict[str, Any]], config: _PositionGroupConfig) -> None:
        regulars = [line for line in lines if _effective_games(line) >= self.REGULAR_MIN_EFFECTIVE_GAMES]
        if len(regulars) < 3:
            for line in lines:
                line['rf_fld'] = 0.0
            return

        # 1. BASELINE EACH COMPONENT AMONG REGULARS
        baselines: dict[str, tuple[float, float]] = {}
        for component in config.components:
            values = [v for v in (component.value_fn(line) for line in regulars) if v is not None]
            if len(values) >= 3 and statistics.pstdev(values) > 0:
                baselines[component.name] = (statistics.mean(values), statistics.pstdev(values))

        # 2. WEIGHTED, REGRESSED Z-SCORE PER LINE
        scores = {id(line): self._weighted_z(line, config, baselines) for line in lines}

        # 3. RE-STANDARDIZE AMONG REGULARS SO THE SPREAD MATCHES runs_sd_per_150
        regular_scores = [scores[id(line)] for line in regulars]
        mean, sd = statistics.mean(regular_scores), statistics.pstdev(regular_scores)
        for line in lines:
            z = 0.0 if sd == 0 else (scores[id(line)] - mean) / sd
            z = max(-self.Z_CAP, min(self.Z_CAP, z))
            line['rf_fld'] = round(z * config.runs_sd_per_150 * _effective_games(line) / 150, 2)

    def _weighted_z(self, line: dict[str, Any], config: _PositionGroupConfig, baselines: dict[str, tuple[float, float]]) -> float:
        weighted_z, total_weight = 0.0, 0.0
        for component in config.components:
            baseline, value = baselines.get(component.name), component.value_fn(line)
            if baseline is None or value is None:
                continue
            mean, sd = baseline
            sample = component.sample_fn(line)
            regressed = (value * sample + mean * component.regression_k) / (sample + component.regression_k)
            z = (regressed - mean) / sd * (1 if component.higher_is_better else -1)
            weighted_z += max(-self.Z_CAP, min(self.Z_CAP, z)) * component.weight
            total_weight += component.weight
        return weighted_z / total_weight if total_weight else 0.0
