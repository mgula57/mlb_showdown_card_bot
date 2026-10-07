from dataclasses import dataclass, field
from typing import Optional

from .team import FIELD_POSITIONS
from .roster_to_team_converter import RosterToTeamConverter


@dataclass
class HistoricalRosterAuditThresholds:
    """Minimums a pre-processed historical roster must meet to count as "filled".

    `min_roster` / `max_roster` default to the season's real active-roster limit
    (RosterToTeamConverter._max_roster_size: 21 pre-1920, 25 through 2019, 26 from 2020),
    since that's the size build-historical composes toward. Bench and bullpen depth is pooled
    by the converter (a thin bench on a pitching-heavy roster is legitimate), so those floors
    are deliberately loose.
    """
    min_roster: Optional[int] = None
    max_roster: Optional[int] = None
    min_starters: int = RosterToTeamConverter.MAX_ROTATION_SLOTS
    min_bullpen: int = 3
    min_bench: int = 1

    def roster_range(self, season: int) -> tuple[int, int]:
        expected = RosterToTeamConverter._max_roster_size(season)
        return (self.min_roster or expected, self.max_roster or expected)


@dataclass
class HistoricalRosterAuditResult:
    season: int
    team_id: int
    abbreviation: str
    name: str
    stored_total: int
    resolved_total: int
    resolved_starters: int
    resolved_bullpen: int
    resolved_bench: int
    missing_positions: list[str]
    issues: list[str] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        return not self.issues


class HistoricalRosterAuditor:
    """Flags pre-processed historical rosters that won't render as a complete team.

    Checks run against the slots that resolve to a card in the requested set (what the
    Historical tab shows), and separately call out slots that were stored but have no card
    for that set -- the fix for those is rebuilding cards, not re-running build-historical.
    """

    def __init__(self, thresholds: Optional[HistoricalRosterAuditThresholds] = None) -> None:
        self.thresholds = thresholds or HistoricalRosterAuditThresholds()

    def audit_row(self, row: dict) -> HistoricalRosterAuditResult:
        season = row['season']
        resolved_positions = set(row.get('resolved_field_positions') or [])
        result = HistoricalRosterAuditResult(
            season=season,
            team_id=row['team_id'],
            abbreviation=row.get('abbreviation') or str(row['team_id']),
            name=row.get('name') or '',
            stored_total=row['stored_total'],
            resolved_total=row['resolved_total'],
            resolved_starters=row['resolved_starters'],
            resolved_bullpen=row['resolved_bullpen'],
            resolved_bench=row['resolved_bench'],
            missing_positions=[p for p in FIELD_POSITIONS if p not in resolved_positions],
        )
        issues = result.issues
        t = self.thresholds

        if row['stored_total'] == 0:
            issues.append("no stored roster slots")
            return result
        if row['recorded_roster_count'] != row['stored_total']:
            issues.append(f"roster_count column {row['recorded_roster_count']} != {row['stored_total']} stored slots")
        missing_cards = row['stored_total'] - row['resolved_total']
        if missing_cards:
            issues.append(f"{missing_cards} stored slot(s) have no card in set")

        lo, hi = t.roster_range(season)
        if not lo <= result.resolved_total <= hi:
            expected = f"{lo}" if lo == hi else f"{lo}-{hi}"
            issues.append(f"roster {result.resolved_total} (expected {expected})")
        if result.missing_positions:
            issues.append(f"missing {','.join(result.missing_positions)}")
        if result.resolved_starters < t.min_starters:
            issues.append(f"{result.resolved_starters} SP (min {t.min_starters})")
        if result.resolved_bullpen < t.min_bullpen:
            issues.append(f"{result.resolved_bullpen} RP (min {t.min_bullpen})")
        if result.resolved_bench < t.min_bench:
            issues.append(f"{result.resolved_bench} BE (min {t.min_bench})")
        return result

    def audit(self, rows: list[dict]) -> list[HistoricalRosterAuditResult]:
        return [self.audit_row(r) for r in rows]

    @staticmethod
    def missing_seasons(rows: list[dict], start_season: int, end_season: int) -> list[int]:
        """Seasons in the range with no pre-processed teams at all."""
        present = {r['season'] for r in rows if r['stored_total'] > 0}
        return [s for s in range(end_season, start_season - 1, -1) if s not in present]

    @staticmethod
    def missing_teams(rows: list[dict], expected_by_season: dict[int, dict[int, str]]) -> dict[int, list[str]]:
        """Teams the MLB API lists for a season that have no stored roster.

        `expected_by_season` maps season -> {team_id: abbreviation}. Seasons with no stored teams
        at all are skipped (missing_seasons already reports those).
        """
        present: dict[int, set[int]] = {}
        for r in rows:
            if r['stored_total'] > 0:
                present.setdefault(r['season'], set()).add(r['team_id'])
        return {
            season: [f"{abbr} ({team_id})" for team_id, abbr in sorted(expected.items(), key=lambda kv: kv[1]) if team_id not in present[season]]
            for season, expected in sorted(expected_by_season.items(), reverse=True)
            if season in present and set(expected) - present[season]
        }
