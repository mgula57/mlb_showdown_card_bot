"""Builds a set per WOTC base set through the Release Builder's algorithm and compares it to the
original WOTC base set, mirroring the Edition Builder's Summary tab (`SummaryCharts.tsx`).

Each set uses the "<set> Base Set" blueprint (WOTC's card count, position mix and average points),
plus optional point buckets. Prints a Markdown report and optionally writes the raw numbers as JSON.

Usage (from repo root):
    python mlb_showdown_bot/scripts/review_set_build.py --rerun
    python mlb_showdown_bot/scripts/review_set_build.py -s 2001 --rerun --buckets "2001=10-100:0.08"
"""

import argparse
import contextlib
import io
import json
import os
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[2]))
load_dotenv(Path(__file__).resolve().parents[2] / '.env')

from mlb_showdown_bot.core.card.sets import Set
from mlb_showdown_bot.core.card.stats.metrics import DefenseMetric
from mlb_showdown_bot.core.database.postgres_db import PostgresDB
from mlb_showdown_bot.core.set_builder.showdown_bot_set import AlgorithmPreviewRequest, PointBucket
from mlb_showdown_bot.core.set_builder.wotc_set_profile import WotcSetProfile
from mlb_showdown_bot.core.shared.player_position import Position

WOTC_SETS = ['2000', '2001', '2002', '2003', '2004', '2005']
POINTS_BUCKET_SIZE = 50
LOW_POINTS_RANGE = (10, 100)
PARENT_GROUPS = ['Position Player', 'Starting Pitcher', 'Relief Pitcher']

# Mirrors POSITION_GROUPS / DEFENSE_POSITION_ORDER in the frontend's DefenseUtils.ts / SummaryCharts.tsx
DEFENSE_POSITION_GROUPS = {'IF': ['1B', '2B', '3B', 'SS'], 'OF': ['LF', 'CF', 'RF'], 'C': ['C', 'CA'], 'CA': ['C', 'CA'], 'LF/RF': ['LF', 'RF']}
DEFENSE_POSITION_ORDER = ['C', 'CA', '1B', '2B', '3B', 'SS', 'IF', 'LF', 'LF/RF', 'CF', 'RF', 'OF']


# =============================================================================
# MARK: - CARD ROW HELPERS
# =============================================================================

class CardRow:
    """Accessors over a `card_bot` / `card_wotc` list row, matching the Summary tab's bucketing"""

    @staticmethod
    def parent_group(row: dict) -> str:
        if not row.get('is_pitcher'):
            return 'Position Player'
        return 'Starting Pitcher' if 'STARTER' in (row.get('positions_list') or []) else 'Relief Pitcher'

    @staticmethod
    def primary_position(row: dict) -> Optional[str]:
        positions = row.get('positions_list') or []
        return positions[0] if positions else None

    @classmethod
    def defense_key(cls, row: dict) -> Optional[tuple]:
        """(position, rating) at the card's primary position, or None for pitchers / DH"""
        position = cls.primary_position(row)
        if row.get('is_pitcher') or not position or position == 'DH':
            return None
        position = position[3:] if position.startswith('PH-') else position
        defense = row.get('positions_and_defense') or {}
        if position in defense:
            return (position, defense[position])
        for group, members in DEFENSE_POSITION_GROUPS.items():
            if position in members and group in defense:
                return (position, defense[group])
        return None


# =============================================================================
# MARK: - DISTRIBUTIONS
# =============================================================================

class Distribution(BaseModel):
    """Counts of one breakdown for this set vs WOTC. `compare` is WOTC scaled to this set's size."""

    rows: List[dict]  # {label, count, compare, compare_raw}

    @classmethod
    def build(cls, cards: List[dict], wotc: List[dict], key_fn: Callable[[dict], object], label_fn: Callable[[object], str] = str) -> 'Distribution':
        counts, wotc_counts = cls._count(cards, key_fn), cls._count(wotc, key_fn)
        scale = len(cards) / len(wotc) if wotc else 0
        keys = sorted(set(counts) | set(wotc_counts))
        return cls(rows=[
            {'label': label_fn(k), 'count': counts.get(k, 0), 'compare': round(wotc_counts.get(k, 0) * scale, 1), 'compare_raw': wotc_counts.get(k, 0)}
            for k in keys
        ])

    @staticmethod
    def _count(cards: List[dict], key_fn: Callable[[dict], object]) -> Dict[object, int]:
        counts: Dict[object, int] = {}
        for card in cards:
            key = key_fn(card)
            if key is None or key == '':
                continue
            counts[key] = counts.get(key, 0) + 1
        return counts

    @property
    def total_variation(self) -> float:
        """0 = identical shape, 1 = no overlap. Compares shares, so set size doesn't matter."""
        total, compare_total = sum(r['count'] for r in self.rows), sum(r['compare_raw'] for r in self.rows)
        if not total or not compare_total:
            return 0.0
        return round(0.5 * sum(abs(r['count'] / total - r['compare_raw'] / compare_total) for r in self.rows), 3)

    def biggest_gaps(self, limit: int = 3) -> List[dict]:
        return sorted(self.rows, key=lambda r: abs(r['count'] - r['compare']), reverse=True)[:limit]

    def markdown(self) -> str:
        lines = ['| Value | This set | WOTC (scaled) | WOTC (actual) | Diff |', '|---|---|---|---|---|']
        for r in self.rows:
            diff = r['count'] - r['compare']
            lines.append(f"| {r['label']} | {r['count']} | {r['compare']} | {r['compare_raw']} | {diff:+.1f} |")
        lines.append(f"\nShape difference (total variation, 0-1): **{self.total_variation}**")
        return '\n'.join(lines)


class DefenseShape(BaseModel):
    """Per-position defense rating distribution for this set vs WOTC, scaled within the position"""

    position: str
    distribution: Distribution
    count: int
    wotc_count: int
    avg: Optional[float]
    wotc_avg: Optional[float]
    stdev: Optional[float]
    wotc_stdev: Optional[float]

    @classmethod
    def build(cls, position: str, ratings: List[int], wotc_ratings: List[int]) -> 'DefenseShape':
        as_cards = lambda values: [{'r': v} for v in values]
        return cls(
            position=position,
            distribution=Distribution.build(as_cards(ratings), as_cards(wotc_ratings), lambda c: c['r'], lambda k: f"{k:+d}"),
            count=len(ratings), wotc_count=len(wotc_ratings),
            avg=cls._round(statistics.mean, ratings), wotc_avg=cls._round(statistics.mean, wotc_ratings),
            stdev=cls._round(statistics.pstdev, ratings), wotc_stdev=cls._round(statistics.pstdev, wotc_ratings),
        )

    @staticmethod
    def _round(fn: Callable, values: List[int]) -> Optional[float]:
        return round(fn(values), 2) if values else None


# =============================================================================
# MARK: - DEFENSE RANGE CONTEXT
# =============================================================================

class DefenseRangeContext:
    """How `metrics.py` currently maps a real-life metric onto in-game defense for a position.

    percentile = (rating - range_min) / (range_max - range_min); defense = pos_min + percentile * (pos_max - pos_min).
    So `rating_0_maps_to` is where a league-average defender lands, and `metric_per_point` is how much
    of the metric it takes to move one point of in-game defense."""

    DEFAULT_METRICS = [DefenseMetric.OAA, DefenseMetric.DRS]

    @classmethod
    def describe(cls, position: str, showdown_set: str, max_year: int, metrics: List[DefenseMetric]) -> List[str]:
        game_set = Set(showdown_set)
        metrics = metrics or cls.DEFAULT_METRICS
        if position == '1B':
            return [
                f"{metric.name}: +1 if > {metric.first_base_plus_1_cutoff(showdown_set, max_year)}, "
                f"+2 if > {metric.first_base_plus_2_cutoff} (and 90+ games), else 0 (per-150 game rate)"
                for metric in metrics
            ]
        try:
            position_enum = Position('C' if position == 'CA' else position)
        except ValueError:
            return []
        # metrics.py keys LF/RF ranges off 'LF'/'RF'
        metric_position = 'LF' if position == 'LF/RF' else position
        pos_min, pos_max = game_set.position_defense_min(position_enum), game_set.position_defense_max(position_enum)
        lines = []
        for metric in metrics:
            range_min = metric.range_min(metric_position, showdown_set, max_year)
            range_max = metric.range_max(metric_position, showdown_set, max_year)
            width = range_max - range_min
            rating_0 = pos_min + (-range_min / width) * (pos_max - pos_min)
            per_point = width / (pos_max - pos_min) if pos_max != pos_min else None
            lines.append(
                f"{metric.name}: range_min {range_min:.2f}, range_max {range_max:.2f}, in-game {pos_min}-{pos_max} | "
                f"avg defender (0) -> {rating_0:.2f} | {per_point:.2f} {metric.name}/150 per +1"
            )
        return lines


# =============================================================================
# MARK: - SET REVIEW
# =============================================================================

class SetBuildReview(BaseModel):
    """Builds one set from its WOTC base set blueprint and compares it against that base set"""

    showdown_set: str
    years: str
    rerun_cards: bool = False
    point_buckets: List[PointBucket] = []
    set_size: Optional[int] = None

    cards: List[dict] = []
    wotc_cards: List[dict] = []
    warnings: List[str] = []
    metrics_by_position: Dict[str, Dict[str, int]] = {}  # e.g. {'SS': {'oaa': 20, 'drs': 1}}

    def run(self, db: PostgresDB) -> 'SetBuildReview':
        profile = WotcSetProfile.load(self.showdown_set)
        request = AlgorithmPreviewRequest(
            set_size=self.set_size or profile.set_size,
            years=self.years,
            showdown_sets=[self.showdown_set],
            point_buckets=self.point_buckets,
            position_targets=profile.position_targets,
        )
        showdown_set = request.to_showdown_bot_set()
        # The set builder prints a full set summary - keep the report readable
        with contextlib.redirect_stdout(io.StringIO()):
            self.cards = showdown_set.build_preview_rows(db, rerun_cards=self.rerun_cards)
        self.warnings = showdown_set.warnings
        self.wotc_cards = db.fetch_card_list({'source': 'WOTC', 'showdown_set': [self.showdown_set], 'expansion': ['BS'], 'limit': 1000})
        self.metrics_by_position = self._tally_defense_metrics(db)
        return self

    def _tally_defense_metrics(self, db: PostgresDB) -> Dict[str, Dict[str, int]]:
        """Which real-life metric (OAA, DRS, ...) drove each card's defense at its primary position"""
        full_cards = db.fetch_cards_for_roster_slots([{'card_id': r['card_id'], 'card_source': 'BOT'} for r in self.cards if r.get('card_id')])
        tally: Dict[str, Dict[str, int]] = {}
        for row in self.cards:
            key, card = CardRow.defense_key(row), full_cards.get(str(row.get('card_id')))
            if not key or card is None:
                continue
            ratings = {str(getattr(p, 'value', p)): v for p, v in (card.positions_and_real_life_ratings or {}).items()}
            position_ratings = next((ratings[p] for p in [key[0], *DEFENSE_POSITION_GROUPS.get(key[0], [])] if p in ratings), None)
            if not position_ratings:
                continue
            metric = str(getattr(next(iter(position_ratings)), 'value', next(iter(position_ratings))))
            tally.setdefault(key[0], {}).setdefault(metric, 0)
            tally[key[0]][metric] += 1
        return tally

    def defense_metrics(self, position: str) -> List[DefenseMetric]:
        return [DefenseMetric(m) for m in sorted(self.metrics_by_position.get(position, {}), key=lambda m: -self.metrics_by_position[position][m])]

    @property
    def max_year(self) -> int:
        return max(int(y) for y in self.years.replace('+', '-').split('-') if y.isdigit())

    # ---- Breakdowns ----

    def averages(self) -> Dict[str, Dict[str, float]]:
        def avg(cards: List[dict], field: str, pitchers: Optional[bool]) -> float:
            values = [c.get(field) or 0 for c in cards if pitchers is None or bool(c.get('is_pitcher')) == pitchers]
            return round(statistics.mean(values), 1) if values else 0
        build = lambda cards: {'points': avg(cards, 'points', None), 'onbase': avg(cards, 'command', False),
                               'control': avg(cards, 'command', True), 'speed': avg(cards, 'speed', False), 'ip': avg(cards, 'ip', True)}
        return {'this_set': build(self.cards), 'wotc': build(self.wotc_cards)}

    def points(self, group: Optional[str] = None) -> Distribution:
        cards, wotc = self._in_group(self.cards, group), self._in_group(self.wotc_cards, group)
        return Distribution.build(cards, wotc,
                                  lambda c: (c.get('points') or 0) // POINTS_BUCKET_SIZE * POINTS_BUCKET_SIZE,
                                  lambda k: f"{k}-{k + POINTS_BUCKET_SIZE - 1}")

    def low_points(self) -> List[dict]:
        """Cards in 10-100 pts per player type, with the share a point bucket would need to target"""
        low, high = LOW_POINTS_RANGE
        is_low = lambda c: low <= (c.get('points') or 0) <= high
        results = []
        for group in PARENT_GROUPS:
            cards, wotc = self._in_group(self.cards, group), self._in_group(self.wotc_cards, group)
            count, wotc_count = sum(map(is_low, cards)), sum(map(is_low, wotc))
            wotc_share = wotc_count / len(wotc) if wotc else 0
            results.append({
                'group': group, 'count': count, 'cards': len(cards), 'share': round(count / len(cards), 3) if cards else 0,
                'wotc_count': wotc_count, 'wotc_cards': len(wotc), 'wotc_share': round(wotc_share, 3),
                'wotc_scaled': round(wotc_share * len(cards), 1),
            })
        return results

    def command(self, pitchers: bool) -> Distribution:
        cards = [c for c in self.cards if bool(c.get('is_pitcher')) == pitchers]
        wotc = [c for c in self.wotc_cards if bool(c.get('is_pitcher')) == pitchers]
        return Distribution.build(cards, wotc, lambda c: c.get('command'))

    def speed(self) -> Distribution:
        hitters = lambda cards: [c for c in cards if not c.get('is_pitcher')]
        return Distribution.build(hitters(self.cards), hitters(self.wotc_cards), lambda c: c.get('speed'))

    def defense(self) -> List[DefenseShape]:
        def ratings_by_position(cards: List[dict]) -> Dict[str, List[int]]:
            result: Dict[str, List[int]] = {}
            for card in cards:
                key = CardRow.defense_key(card)
                if key:
                    result.setdefault(key[0], []).append(key[1])
            return result
        ours, theirs = ratings_by_position(self.cards), ratings_by_position(self.wotc_cards)
        positions = sorted(set(ours) | set(theirs), key=lambda p: DEFENSE_POSITION_ORDER.index(p) if p in DEFENSE_POSITION_ORDER else 99)
        return [DefenseShape.build(p, ours.get(p, []), theirs.get(p, [])) for p in positions]

    @staticmethod
    def _in_group(cards: List[dict], group: Optional[str]) -> List[dict]:
        return cards if group is None else [c for c in cards if CardRow.parent_group(c) == group]

    # ---- Output ----

    def as_dict(self) -> dict:
        return {
            'showdown_set': self.showdown_set, 'years': self.years, 'rerun_cards': self.rerun_cards,
            'point_buckets': [b.model_dump() for b in self.point_buckets],
            'card_count': len(self.cards), 'wotc_card_count': len(self.wotc_cards), 'warnings': self.warnings,
            'averages': self.averages(),
            'points': self.points().rows, 'points_by_group': {g: self.points(g).rows for g in PARENT_GROUPS},
            'low_points': self.low_points(),
            'command_hitters': self.command(False).rows, 'command_pitchers': self.command(True).rows,
            'speed': self.speed().rows,
            'defense': [{**shape.model_dump(exclude={'distribution'}), 'rows': shape.distribution.rows,
                         'total_variation': shape.distribution.total_variation,
                         'metrics_used': self.metrics_by_position.get(shape.position, {})} for shape in self.defense()],
        }

    def markdown(self) -> str:
        buckets = ', '.join(f"{b.label} @ {b.percentage:.0%}" for b in self.point_buckets) or 'none'
        out = [f"# {self.showdown_set} Set — {self.years} ({len(self.cards)} cards vs WOTC {len(self.wotc_cards)})",
               f"Re-run cards: {self.rerun_cards} | Point buckets: {buckets}"]
        if self.warnings:
            out.append('Warnings:\n' + '\n'.join(f"- {w}" for w in self.warnings))

        averages = self.averages()
        out.append('\n## Averages\n| Stat | This set | WOTC |\n|---|---|---|')
        out += [f"| {k} | {v} | {averages['wotc'][k]} |" for k, v in averages['this_set'].items()]

        out.append(f"\n## Points distribution (all)\n{self.points().markdown()}")
        out.append(f"\n### Low point cards ({LOW_POINTS_RANGE[0]}-{LOW_POINTS_RANGE[1]}) by player type")
        out.append('| Type | This set | Share | WOTC scaled | WOTC share |\n|---|---|---|---|---|')
        out += [f"| {r['group']} | {r['count']}/{r['cards']} | {r['share']:.1%} | {r['wotc_scaled']} | {r['wotc_share']:.1%} |" for r in self.low_points()]

        out.append(f"\n## Command — Hitters (On-Base)\n{self.command(False).markdown()}")
        out.append(f"\n## Command — Pitchers (Control)\n{self.command(True).markdown()}")
        out.append(f"\n## Speed (hitters)\n{self.speed().markdown()}")

        out.append('\n## Defense by primary position (WOTC scaled within position)')
        for shape in self.defense():
            out.append(f"\n### {shape.position} — {shape.count} cards (WOTC {shape.wotc_count})")
            out.append(f"Avg {shape.avg} vs WOTC {shape.wotc_avg} | Std dev {shape.stdev} vs WOTC {shape.wotc_stdev}")
            metric_counts = self.metrics_by_position.get(shape.position, {})
            if metric_counts:
                out.append('Metric used: ' + ', '.join(f"{DefenseMetric(m).name} {n}" for m, n in sorted(metric_counts.items(), key=lambda i: -i[1])))
            out += [f"- {line}" for line in DefenseRangeContext.describe(shape.position, self.showdown_set, self.max_year, self.defense_metrics(shape.position))]
            out.append(shape.distribution.markdown())
        return '\n'.join(out)


# =============================================================================
# MARK: - CLI
# =============================================================================

def parse_buckets(values: List[str], buckets_file: Optional[str]) -> Dict[str, List[PointBucket]]:
    """`--buckets-file` JSON ({"2002": "10-50:0.06"}) overridden by `--buckets "2002=10-50:0.06"` flags"""
    raw: Dict[str, str] = {}
    if buckets_file and os.path.exists(buckets_file):
        with open(buckets_file) as f:
            raw.update({str(k): v for k, v in json.load(f).items() if v})
    for value in values:
        showdown_set, buckets = value.split('=', 1)
        raw[showdown_set.strip()] = buckets.strip()
    return {s: PointBucket.validate_list(PointBucket.parse_cli(b)) for s, b in raw.items() if b}


def main():
    parser = argparse.ArgumentParser(description='Build sets from WOTC base set blueprints and compare them to WOTC.')
    parser.add_argument('-s', '--sets', default=','.join(WOTC_SETS), help='Comma-separated WOTC sets (2000-2005)')
    parser.add_argument('-y', '--years', default=str(datetime.now().year), help='Year string, e.g. 2026')
    parser.add_argument('-r', '--rerun', action='store_true', help='Re-run each card through the current card algorithm')
    parser.add_argument('-b', '--buckets', action='append', default=[], help='Per-set point buckets, e.g. "2002=10-50:0.06"')
    parser.add_argument('-bf', '--buckets-file', help='JSON file of per-set point buckets, e.g. {"2002": "10-50:0.06"}')
    parser.add_argument('-ss', '--set-size', type=int, help="Override the blueprint's set size")
    parser.add_argument('-o', '--json-out', help='Write the raw comparison data to this JSON path')
    args = parser.parse_args()

    buckets_by_set = parse_buckets(args.buckets, args.buckets_file)
    db = PostgresDB()
    reviews = []
    try:
        for showdown_set in [s.strip() for s in args.sets.split(',') if s.strip()]:
            print(f"Building {showdown_set}...", file=sys.stderr)
            review = SetBuildReview(showdown_set=showdown_set, years=args.years, rerun_cards=args.rerun,
                                    point_buckets=buckets_by_set.get(showdown_set, []), set_size=args.set_size).run(db)
            reviews.append(review)
            print(review.markdown() + '\n')
    finally:
        db.close_connection()

    if args.json_out:
        with open(args.json_out, 'w') as f:
            json.dump([r.as_dict() for r in reviews], f, indent=2, default=str)
        print(f"Wrote {args.json_out}", file=sys.stderr)


if __name__ == '__main__':
    main()
