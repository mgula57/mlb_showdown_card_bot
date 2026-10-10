from dataclasses import dataclass, field

PINNED_PRIORITY = -1
"""Sorts ahead of every standard accolade (awards/triple crown are 0)"""


@dataclass(frozen=True)
class StatComboFeat:
    """Single-season feat earned by clearing every stat threshold (ex: 40 HR / 40 SB).

    Feats sharing a `group` are tiers of the same feat; only the first match in a group is
    awarded, so list higher tiers first.
    """

    label: str
    thresholds: dict[str, int]
    group: str
    is_pitcher: bool = False
    priority: int = PINNED_PRIORITY
    """Lower sorts first. Common feats (ex: 20/20) use a softer priority so they don't bury awards"""

    def is_achieved(self, stats: dict) -> bool:
        for stat, minimum in self.thresholds.items():
            try:
                if float(stats.get(stat, 0) or 0) < minimum:
                    return False
            except (TypeError, ValueError):
                return False
        return True


@dataclass(frozen=True)
class HistoricFeat:
    """Specific player-season feat that can't be derived from season stats (ex: DiMaggio's streak)."""

    bref_id: str
    year: int
    label: str
    priority: int = PINNED_PRIORITY
    supersedes: tuple[str, ...] = field(default_factory=tuple)
    """Standard accolade strings (ex: "73 HOME RUNS") made redundant by this one on a single-season card"""


class SpecialAccolades:
    """Registry of special-case accolades that are pinned to the top of a card's accolade list."""

    MAX_SPECIAL: int = 3

    STAT_COMBO_FEATS: list[StatComboFeat] = [
        StatComboFeat(label='40 HR / 70 SB', thresholds={'HR': 40, 'SB': 70}, group='HR_SB'),
        StatComboFeat(label='50 HR / 50 SB', thresholds={'HR': 50, 'SB': 50}, group='HR_SB'),
        StatComboFeat(label='40 HR / 40 SB', thresholds={'HR': 40, 'SB': 40}, group='HR_SB'),
        StatComboFeat(label='30 HR / 30 SB', thresholds={'HR': 30, 'SB': 30}, group='HR_SB', priority=1),
        StatComboFeat(label='20 HR / 20 SB', thresholds={'HR': 20, 'SB': 20}, group='HR_SB', priority=5),
        StatComboFeat(label='50 HR / 50 2B', thresholds={'HR': 50, '2B': 50}, group='HR_2B'),
        StatComboFeat(label='30 GAME WINNER', thresholds={'W': 30}, group='WINS', is_pitcher=True),
    ]

    HISTORIC_FEATS: list[HistoricFeat] = [
        HistoricFeat(bref_id='dimagjo01', year=1941, label='56 GAME STREAK'),
        HistoricFeat(bref_id='suzukic01', year=2004, label='262 HIT RECORD', supersedes=('262 HITS',)),
        HistoricFeat(bref_id='bondsba01', year=2001, label='73 HR RECORD', supersedes=('73 HOME RUNS',)),
        HistoricFeat(bref_id='bondsba01', year=2004, label='232 BB RECORD'),
        HistoricFeat(bref_id='marisro01', year=1961, label="61 IN '61", supersedes=('61 HOME RUNS',)),
        HistoricFeat(bref_id='judgeaa01', year=2022, label='AL HR RECORD'),
        HistoricFeat(bref_id='alonspe01', year=2019, label='ROOKIE HR REC'),
        HistoricFeat(bref_id='judgeaa01', year=2017, label='ROOKIE HR REC'),
        HistoricFeat(bref_id='wilsoha01', year=1930, label='191 RBI RECORD', supersedes=('191 RBI',)),
        HistoricFeat(bref_id='henderi01', year=1982, label='130 SB RECORD'),
        HistoricFeat(bref_id='webbea01', year=1931, label='67 2B RECORD'),
        HistoricFeat(bref_id='wilsoch01', year=1912, label='36 3B RECORD'),
        HistoricFeat(bref_id='rodrifr03', year=2008, label='62 SV RECORD', supersedes=('62 SAVES',)),
    ]

    def __init__(self, bref_id: str, years: list, stats: dict, is_pitcher: bool) -> None:
        self.bref_id = bref_id
        self.years = {int(y) for y in years if str(y).isdigit()}
        self.stats = stats
        self.is_pitcher = is_pitcher

    @property
    def is_single_season(self) -> bool:
        return len(self.years) == 1

    @property
    def historic_feats(self) -> list[HistoricFeat]:
        return [f for f in self.HISTORIC_FEATS if f.bref_id == self.bref_id and f.year in self.years]

    @property
    def stat_combo_feats(self) -> list[StatComboFeat]:
        # COMBOS ARE SINGLE-SEASON FEATS, MULTI-YEAR TOTALS WOULD FALSELY QUALIFY
        if not self.is_single_season:
            return []
        feats, groups_awarded = [], set()
        for feat in self.STAT_COMBO_FEATS:
            if feat.is_pitcher != self.is_pitcher or feat.group in groups_awarded:
                continue
            if feat.is_achieved(self.stats):
                feats.append(feat)
                groups_awarded.add(feat.group)
        return feats

    @property
    def feats(self) -> list[StatComboFeat | HistoricFeat]:
        """Special accolades in display priority order (historic first)"""
        feats = self.historic_feats + self.stat_combo_feats
        return sorted(feats, key=lambda f: f.priority)[:self.MAX_SPECIAL]

    @property
    def superseded_accolades(self) -> list[str]:
        """Standard accolades to drop because a special accolade already covers them"""
        if not self.is_single_season:
            return []
        return [s for f in self.feats if isinstance(f, HistoricFeat) for s in f.supersedes]
