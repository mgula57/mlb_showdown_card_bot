import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { ResponsiveContainer, BarChart, Bar, ScatterChart, Scatter, ZAxis, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, type TooltipContentProps } from 'recharts';
import { fetchWotcBaseSet, WOTC_BASE_SETS, type ReleaseCard, type WotcBaseSet } from '../../api/releases';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { defenseAtPosition } from '../shared/DefenseUtils';
import CustomSelect from '../shared/CustomSelect';
import FormEnabler from '../customs/FormEnabler';
import { headingClass } from '../shared/headingStyles';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';
import { choiceClass } from '../shared/choiceStyles';
import { EmptyState } from '../shared/EmptyState';
import { DEFENSE_POSITION_ORDER, FRANCHISE_CODE, HAND_ORDER, PARENT_POSITION_ORDER, POSITION_ORDER, handLabel, parentPositionGroup, type ParentPositionGroup } from './cardGroups';

type SummaryChartsProps = {
    cards: ReleaseCard[];
    /** Scopes the saved WOTC comparison selection to this edition. */
    editionId: string;
};

const POINTS_BUCKET_SIZE = 50;
const CHART_ACCENT = 'var(--secondary)';
// WOTC reference series: red separates it from the dark bars in light mode; blue remains clearer in dark.
const COMPARE_ACCENT = 'var(--chart-compare)';

// =============================================================================
// MARK: - AGGREGATION
// =============================================================================

type BreakdownKey = string | number;

/** One bar group. `compare` is the WOTC count scaled to this set's size; `compareRaw` is unscaled.
 * Average breakdowns put the average in `count`/`compare` (no `compareRaw`) and the number of cards
 * behind it in `sampleSize`/`compareSampleSize`. */
type BreakdownRow = {
    label: string;
    count: number;
    compare?: number;
    compareRaw?: number;
    sampleSize?: number;
    compareSampleSize?: number;
    /** Section the row belongs to; horizontal charts draw a divider wherever it changes. */
    group?: string;
    /** Blank spacer row that holds a section divider, not data. */
    isDivider?: boolean;
};

/** How to bucket cards for one chart. `sort: 'key'` orders ascending by key (numeric stats like
 * command/IP); `'count'` orders by frequency descending (categorical fields); a function sorts keys directly. */
type BreakdownSpec = {
    /** A list counts the card once under each key (e.g. every icon on it). */
    keyFn: (snapshot: CardDatabaseRecord) => BreakdownKey | BreakdownKey[] | null | undefined;
    labelFn?: (key: BreakdownKey) => string;
    sort: 'key' | 'count' | ((a: BreakdownKey, b: BreakdownKey) => number);
    /** Optional section for each key, e.g. the position of a "SS +5" defense key. */
    groupFn?: (key: BreakdownKey) => string;
    /** Scale the comparison per `groupFn` section (e.g. WOTC shortstops scaled to your shortstop
     * count) instead of by overall set size. */
    scaleWithinGroup?: boolean;
};

/** Cards being compared against, already narrowed to the same subset as the user's cards. */
type Comparison = { snapshots: CardDatabaseRecord[] };

function countBy(snapshots: CardDatabaseRecord[], keyFn: BreakdownSpec['keyFn']): Map<BreakdownKey, number> {
    const counts = new Map<BreakdownKey, number>();
    for (const snapshot of snapshots) {
        const keys = keyFn(snapshot);
        for (const key of Array.isArray(keys) ? keys : [keys]) {
            if (key === null || key === undefined || key === '') continue;
            counts.set(key, (counts.get(key) ?? 0) + 1);
        }
    }
    return counts;
}

const roundTenth = (value: number) => Math.round(value * 10) / 10;

/** How to average a value per key, e.g. each position's average points. `entries` yields a card's
 * [key, value] pairs; a card can feed several keys (one per chart result). */
type AverageSpec = {
    entries: (snapshot: CardDatabaseRecord) => [BreakdownKey, number][];
    sort: (a: BreakdownKey, b: BreakdownKey) => number;
    labelFn?: (key: BreakdownKey) => string;
    groupFn?: (key: BreakdownKey) => string;
};

function averagesBy(snapshots: CardDatabaseRecord[], entries: AverageSpec['entries']): Map<BreakdownKey, { sum: number; cards: number }> {
    const totals = new Map<BreakdownKey, { sum: number; cards: number }>();
    for (const snapshot of snapshots) {
        for (const [key, value] of entries(snapshot)) {
            const total = totals.get(key) ?? { sum: 0, cards: 0 };
            totals.set(key, { sum: total.sum + value, cards: total.cards + 1 });
        }
    }
    return totals;
}

/** Average per key for this set and the comparison set (unscaled: an average needs no size scaling). */
function buildAverageBreakdown(snapshots: CardDatabaseRecord[], spec: AverageSpec, comparison: Comparison | null): BreakdownRow[] {
    const totals = averagesBy(snapshots, spec.entries);
    const compareTotals = comparison ? averagesBy(comparison.snapshots, spec.entries) : null;
    const keys = [...new Set([...totals.keys(), ...(compareTotals?.keys() ?? [])])].sort(spec.sort);
    const averageOf = (total?: { sum: number; cards: number }) => total && total.cards > 0 ? roundTenth(total.sum / total.cards) : 0;
    return keys.map(key => {
        const row: BreakdownRow = {
            label: spec.labelFn ? spec.labelFn(key) : String(key),
            count: averageOf(totals.get(key)),
            sampleSize: totals.get(key)?.cards ?? 0,
            group: spec.groupFn?.(key),
        };
        if (compareTotals) {
            row.compare = averageOf(compareTotals.get(key));
            row.compareSampleSize = compareTotals.get(key)?.cards ?? 0;
        }
        return row;
    });
}

function compareKeys(a: BreakdownKey, b: BreakdownKey): number {
    return (typeof a === 'number' && typeof b === 'number') ? a - b : String(a).localeCompare(String(b));
}

/** Sums key counts into per-section totals. */
function totalsByGroup(counts: Map<BreakdownKey, number>, groupFn: (key: BreakdownKey) => string): Map<string, number> {
    const totals = new Map<string, number>();
    for (const [key, count] of counts) {
        const group = groupFn(key);
        totals.set(group, (totals.get(group) ?? 0) + count);
    }
    return totals;
}

/** Counts `snapshots` by `spec`. With a `comparison`, each row also carries the comparison set's
 * count scaled proportionally to this set's size, so a 100-card set vs a 462-card WOTC set plots
 * both on the same 100-card footing (or per section, with `scaleWithinGroup`). Keys present in
 * only one set still get a row. */
function buildBreakdown(snapshots: CardDatabaseRecord[], spec: BreakdownSpec, comparison: Comparison | null): BreakdownRow[] {
    const counts = countBy(snapshots, spec.keyFn);
    const compareCounts = comparison ? countBy(comparison.snapshots, spec.keyFn) : null;
    const overallScale = comparison && comparison.snapshots.length > 0 ? snapshots.length / comparison.snapshots.length : 0;

    const groupFn = spec.scaleWithinGroup ? spec.groupFn : undefined;
    const groupTotals = groupFn ? totalsByGroup(counts, groupFn) : null;
    const compareGroupTotals = groupFn && compareCounts ? totalsByGroup(compareCounts, groupFn) : null;
    const scaleFor = (key: BreakdownKey): number => {
        if (!groupFn || !groupTotals || !compareGroupTotals) return overallScale;
        const group = groupFn(key);
        const compareTotal = compareGroupTotals.get(group) ?? 0;
        return compareTotal > 0 ? (groupTotals.get(group) ?? 0) / compareTotal : 0;
    };

    const keys = [...new Set([...counts.keys(), ...(compareCounts?.keys() ?? [])])];
    if (spec.sort === 'key') keys.sort(compareKeys);
    else if (spec.sort === 'count') keys.sort((a, b) =>
        (counts.get(b) ?? 0) - (counts.get(a) ?? 0) || (compareCounts?.get(b) ?? 0) - (compareCounts?.get(a) ?? 0)
    );
    else keys.sort(spec.sort);

    return keys.map(key => {
        const row: BreakdownRow = {
            label: spec.labelFn ? spec.labelFn(key) : String(key),
            count: counts.get(key) ?? 0,
            group: spec.groupFn?.(key),
        };
        if (compareCounts) {
            row.compareRaw = compareCounts.get(key) ?? 0;
            row.compare = roundTenth(row.compareRaw * scaleFor(key));
        }
        return row;
    });
}

// Command keys pack [hitter flag][command][outs] into one sortable number so pitchers (Control)
// sort ahead of hitters (On-Base) and each side gets its own section. Outs never reach 100.
const COMMAND_OUTS_MULTIPLIER = 100;
const COMMAND_HITTER_OFFSET = 100 * COMMAND_OUTS_MULTIPLIER;

function commandKey(c: CardDatabaseRecord, includeOuts: boolean): number {
    const command = (c.command ?? 0) * (includeOuts ? COMMAND_OUTS_MULTIPLIER : 1);
    return (c.is_pitcher ? 0 : COMMAND_HITTER_OFFSET) + command + (includeOuts ? (c.outs ?? 0) : 0);
}

const GROUP_HITTERS = 'Hitters';
const GROUP_PITCHERS = 'Pitchers';
const sideGroup = (snapshot: CardDatabaseRecord) => snapshot.is_pitcher ? GROUP_PITCHERS : GROUP_HITTERS;

function commandKeyGroup(key: BreakdownKey): string {
    return Number(key) >= COMMAND_HITTER_OFFSET ? GROUP_HITTERS : GROUP_PITCHERS;
}

// IP is split by role; starters and relievers work on very different innings scales.
const IP_ROLE_ORDER = ['Starters', 'Relievers'];

/** Group of a "GROUP N" key, e.g. "SS" for the defense key "SS +5" or "Starters" for "Starters 7". */
function groupedKeyGroup(key: BreakdownKey): string {
    return String(key).split(' ')[0];
}

/** Numeric value of a "GROUP N" key or row label. */
function groupedKeyValue(key: BreakdownKey): number {
    return Number(String(key).split(' ')[1]);
}

/** Orders "GROUP N" keys by `groupOrder`, then by value (`descending` for defense ratings). */
function compareGroupedKeys(groupOrder: string[], descending: boolean) {
    const groupIndex = (key: BreakdownKey) => {
        const index = groupOrder.indexOf(groupedKeyGroup(key));
        return index === -1 ? groupOrder.length : index;
    };
    return (a: BreakdownKey, b: BreakdownKey) =>
        groupIndex(a) - groupIndex(b) || (groupedKeyValue(a) - groupedKeyValue(b)) * (descending ? -1 : 1);
}

function comparePositions(a: BreakdownKey, b: BreakdownKey): number {
    const index = (key: BreakdownKey) => POSITION_ORDER.includes(String(key)) ? POSITION_ORDER.indexOf(String(key)) : POSITION_ORDER.length;
    return index(a) - index(b) || String(a).localeCompare(String(b));
}

// Hitter icons, then pitcher icons, then the ones both can carry.
const ICON_ORDER = ['S', 'G', 'HR', 'SB', 'CY', '20', 'K', 'RP', 'V', 'R', 'RY'];

// Outs, then walks and hits, in the order they run down a card's chart.
const CHART_RESULT_ORDER = ['PU', 'SO', 'GB', 'FB', 'BB', '1B', '1B+', '2B', '3B', 'HR'];
const CHART_GROUP_ORDER = [GROUP_PITCHERS, GROUP_HITTERS];
const chartResultOf = (key: BreakdownKey) => String(key).split(' ')[1];

/** Each chart result's slot count on the card, keyed "Hitters HR"; results not on the chart count as 0. */
function chartResultEntries(snapshot: CardDatabaseRecord): [BreakdownKey, number][] {
    const values: Record<string, number> | null | undefined = snapshot.chart_values;
    if (!values) return [];
    return CHART_RESULT_ORDER.map(result => [`${sideGroup(snapshot)} ${result}`, Number(values[result] ?? 0)]);
}

const AVERAGE_SPECS = {
    pointsByPosition: {
        entries: c => [[c.positions_list?.[0] ?? c.player_type, c.points ?? 0]],
        sort: comparePositions,
        groupFn: key => ['STARTER', 'RELIEVER', 'CLOSER'].includes(String(key)) ? GROUP_PITCHERS : GROUP_HITTERS,
    },
    chartResults: {
        entries: chartResultEntries,
        sort: (a, b) => CHART_GROUP_ORDER.indexOf(groupedKeyGroup(a)) - CHART_GROUP_ORDER.indexOf(groupedKeyGroup(b))
            || CHART_RESULT_ORDER.indexOf(chartResultOf(a)) - CHART_RESULT_ORDER.indexOf(chartResultOf(b)),
        labelFn: chartResultOf,
        groupFn: groupedKeyGroup,
    },
} satisfies Record<string, AverageSpec>;

const SPECS = {
    parentPosition: {
        keyFn: parentPositionGroup,
        sort: (a, b) => PARENT_POSITION_ORDER.indexOf(a as ParentPositionGroup) - PARENT_POSITION_ORDER.indexOf(b as ParentPositionGroup),
    },
    points: {
        keyFn: c => Math.floor((c.points ?? 0) / POINTS_BUCKET_SIZE) * POINTS_BUCKET_SIZE,
        labelFn: key => `${key}-${Number(key) + POINTS_BUCKET_SIZE - 1}`,
        sort: 'key',
    },
    command: {
        keyFn: c => c.command == null ? null : commandKey(c, false),
        labelFn: key => String(Number(key) % COMMAND_HITTER_OFFSET),
        sort: 'key',
        groupFn: commandKeyGroup,
        scaleWithinGroup: true,
    },
    commandOuts: {
        keyFn: c => c.command == null ? null : commandKey(c, true),
        labelFn: key => {
            const commandOuts = Number(key) % COMMAND_HITTER_OFFSET;
            return `${Math.floor(commandOuts / COMMAND_OUTS_MULTIPLIER)}/${commandOuts % COMMAND_OUTS_MULTIPLIER}`;
        },
        sort: 'key',
        groupFn: commandKeyGroup,
        scaleWithinGroup: true,
    },
    position: { keyFn: c => c.positions_list?.[0] ?? c.player_type, sort: 'count' },
    team: { keyFn: c => c.team ? (FRANCHISE_CODE[c.team] ?? c.team) : c.team, sort: 'count' },
    speed: { keyFn: c => c.is_pitcher ? null : c.speed, sort: 'key' },
    ip: {
        keyFn: c => !c.is_pitcher || c.ip == null ? null : `${parentPositionGroup(c) === 'Starting Pitcher' ? 'Starters' : 'Relievers'} ${c.ip}`,
        sort: compareGroupedKeys(IP_ROLE_ORDER, false),
        groupFn: groupedKeyGroup,
        scaleWithinGroup: true,
    },
    defense: {
        keyFn: c => {
            const primaryPosition = c.positions_list?.[0];
            if (c.is_pitcher || !primaryPosition || primaryPosition === 'DH') return null;
            const defValue = defenseAtPosition(c.positions_and_defense, primaryPosition);
            if (defValue === null) return null;
            return `${primaryPosition} ${defValue >= 0 ? '+' : ''}${defValue}`;
        },
        sort: compareGroupedKeys(DEFENSE_POSITION_ORDER, true),
        groupFn: groupedKeyGroup,
        scaleWithinGroup: true,
    },
    hand: {
        keyFn: handLabel,
        sort: (a, b) => HAND_ORDER.indexOf(String(a)) - HAND_ORDER.indexOf(String(b)),
        groupFn: key => String(key).endsWith('HP') ? GROUP_PITCHERS : GROUP_HITTERS,
        scaleWithinGroup: true,
    },
    icons: {
        keyFn: c => [...new Set(c.icons_list ?? [])],
        sort: (a, b) => {
            const index = (key: BreakdownKey) => ICON_ORDER.includes(String(key)) ? ICON_ORDER.indexOf(String(key)) : ICON_ORDER.length;
            return index(a) - index(b);
        },
    },
} satisfies Record<string, BreakdownSpec>;

function average(
    snapshots: CardDatabaseRecord[],
    keyFn: (snapshot: CardDatabaseRecord) => number | null | undefined,
    decimals: number,
): number {
    if (snapshots.length === 0) return 0;
    const sum = snapshots.reduce((total, c) => total + (keyFn(c) ?? 0), 0);
    const factor = 10 ** decimals;
    return Math.round((sum / snapshots.length) * factor) / factor;
}

type SummaryAverages = { points: number; onBase: number; control: number; speed: number; ip: number; icons: number };

function buildAverages(snapshots: CardDatabaseRecord[]): SummaryAverages {
    return {
        icons: average(snapshots, c => new Set(c.icons_list ?? []).size, 2),
        points: average(snapshots, c => c.points, 0),
        onBase: average(snapshots.filter(c => !c.is_pitcher), c => c.command, 1),
        control: average(snapshots.filter(c => c.is_pitcher), c => c.command, 1),
        speed: average(snapshots.filter(c => !c.is_pitcher), c => c.speed, 1),
        ip: average(snapshots.filter(c => c.is_pitcher), c => c.ip, 1),
    };
}

// =============================================================================
// MARK: - WOTC FIT
// =============================================================================

/** How closely a breakdown tracks the WOTC comparison set. Only 'warn'/'off' get color. */
type Fit = 'ok' | 'warn' | 'off';
type FitCheck = { fit: Fit; detail: string };
type Tolerance = { warn: number; off: number };

const FIT_RANK: Record<Fit, number> = { ok: 0, warn: 1, off: 2 };

const COMMAND_AVERAGE_TOLERANCE: Tolerance = { warn: 0.4, off: 0.8 };
const IP_AVERAGE_TOLERANCE: Tolerance = { warn: 0.4, off: 0.8 };
const POINTS_AVERAGE_TOLERANCE: Tolerance = { warn: 20, off: 40 };
const SPEED_AVERAGE_TOLERANCE: Tolerance = { warn: 1, off: 2 };
const ICONS_AVERAGE_TOLERANCE: Tolerance = { warn: 0.15, off: 0.3 };
/** Share of chart slots that would have to change result to match WOTC; 5% is one slot of a 20-slot chart. */
const CHART_RESULTS_TOLERANCE: Tolerance = { warn: 0.05, off: 0.1 };

/** Share of cards that would have to move buckets to match WOTC's shape (total variation distance). */
const DISTRIBUTION_TOLERANCE: Tolerance = { warn: 0.15, off: 0.3 };
/** Defense panels are small and split over many rating buckets, so their spread is noisier — judge it more loosely. */
const DEFENSE_DISTRIBUTION_TOLERANCE: Tolerance = { warn: 0.25, off: 0.45 };
/** Below this many cards a full-width chart's shape is mostly sampling noise, so it isn't judged. */
const MIN_CARDS_TO_SCORE = 20;
/** Same floor for the small per-group panels (a defensive position, a pitcher role). */
const MIN_PANEL_CARDS_TO_SCORE = 10;

function fitFor(delta: number, tolerance: Tolerance): Fit {
    return delta >= tolerance.off ? 'off' : delta >= tolerance.warn ? 'warn' : 'ok';
}

/** Total variation distance between two sets of bucket amounts, each taken as shares of its own total. */
function shareDistance(pairs: [number, number][]): number {
    const total = pairs.reduce((sum, [value]) => sum + value, 0);
    const compareTotal = pairs.reduce((sum, [, compare]) => sum + compare, 0);
    if (total === 0 || compareTotal === 0) return 1;
    return pairs.reduce((sum, [value, compare]) => sum + Math.abs(value / total - compare / compareTotal), 0) / 2;
}

/** Compares one chart's bucket shares against WOTC's (raw counts, so scaling doesn't matter).
 * Null when there are fewer than `minCards` cards to judge. */
function distributionCheck(rows: BreakdownRow[], minCards = MIN_CARDS_TO_SCORE, tolerance = DISTRIBUTION_TOLERANCE, label = 'Distribution'): FitCheck | null {
    const count = rows.reduce((sum, row) => sum + row.count, 0);
    if (count < minCards) return null;
    const distance = shareDistance(rows.map(row => [row.count, row.compareRaw ?? 0]));
    return { fit: fitFor(distance, tolerance), detail: `${label} ${Math.round(distance * 100)}% off` };
}

/** Compares a panel's average chart (slots per result) against WOTC's; null below `MIN_PANEL_CARDS_TO_SCORE` cards. */
function chartResultsCheck(rows: BreakdownRow[]): FitCheck | null {
    if ((rows[0]?.sampleSize ?? 0) < MIN_PANEL_CARDS_TO_SCORE) return null;
    const distance = shareDistance(rows.map(row => [row.count, row.compare ?? 0]));
    return { fit: fitFor(distance, CHART_RESULTS_TOLERANCE), detail: `Chart ${Math.round(distance * 100)}% off` };
}

/** Card-weighted average gap between this set's per-key averages and WOTC's (e.g. points per position). */
function averageGapCheck(rows: BreakdownRow[], tolerance: Tolerance, unit: string): FitCheck | null {
    const judged = rows.filter(row => (row.sampleSize ?? 0) > 0 && (row.compareSampleSize ?? 0) > 0);
    const cards = judged.reduce((sum, row) => sum + (row.sampleSize ?? 0), 0);
    if (cards < MIN_CARDS_TO_SCORE) return null;
    const gap = judged.reduce((sum, row) => sum + Math.abs(row.count - (row.compare ?? 0)) * (row.sampleSize ?? 0), 0) / cards;
    return { fit: fitFor(gap, tolerance), detail: `Off by ${Math.round(gap)} ${unit} on average` };
}

/** Worst of several checks that each stand alone (e.g. one per hitter/pitcher section); null when none can be judged. */
function worstCheck(checks: (FitCheck | null)[]): FitCheck | null {
    const [first, ...rest] = checks.filter((check): check is FitCheck => check !== null);
    return first ? combineChecks(first, ...rest) : null;
}

function averageCheck(label: string, value: number, compareValue: number, tolerance: Tolerance): FitCheck {
    return { fit: fitFor(Math.abs(value - compareValue), tolerance), detail: `${label} ${value} vs ${compareValue}` };
}

/** Worst of a section's checks; null (no dot) when its distribution can't be judged. */
function combineChecks(distribution: FitCheck | null, ...averages: (FitCheck | null)[]): FitCheck | null {
    if (!distribution) return null;
    const checks = [distribution, ...averages.filter((check): check is FitCheck => check !== null)];
    const fit = checks.reduce<Fit>((worst, check) => FIT_RANK[check.fit] > FIT_RANK[worst] ? check.fit : worst, 'ok');
    return { fit, detail: checks.map(check => check.detail).join(' · ') };
}

// =============================================================================
// MARK: - PRESENTATION
// =============================================================================

const FIT_DOT_CLASS: Record<Fit, string> = {
    ok: 'bg-(--green)',
    warn: 'bg-(--gold)',
    off: 'bg-(--red)',
};

const FIT_LABEL: Record<Fit, string> = { ok: 'Close to WOTC', warn: 'Drifting from WOTC', off: 'Far from WOTC' };

/** Small status dot beside a section title; the hover text explains the rating. */
function FitDot({ check }: { check: FitCheck }) {
    const text = `${FIT_LABEL[check.fit]} — ${check.detail}`;
    return <span title={text} aria-label={text} className={`inline-block w-2 h-2 rounded-full shrink-0 cursor-help ${FIT_DOT_CLASS[check.fit]}`} />;
}

function Section({ title, action, fit, className, children }: { title: string; action?: ReactNode; fit?: FitCheck | null; className?: string; children: ReactNode }) {
    return (
        <div className={className}>
            <div className="flex items-center justify-between gap-2 mb-2">
                <div className={`flex items-center gap-1.5 ${headingClass('panel')}`}>
                    {title}
                    {fit && <FitDot check={fit} />}
                </div>
                {action}
            </div>
            {children}
        </div>
    );
}

/** `compareLoading` holds the WOTC line's space with a skeleton while a comparison set loads. */
function StatTile({ label, value, compareValue, compareLoading = false }: { label: string; value: string | number; compareValue?: string | number; compareLoading?: boolean }) {
    return (
        <div className="flex flex-col items-center justify-center rounded-card border border-(--divider) px-3 py-2 min-w-22">
            <span className="font-display-upright text-[22px] leading-none tabular-nums text-(--text-primary)">{value}</span>
            <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary) mt-1`}>{label}</span>
            {compareLoading ? (
                <span className="h-3.5 w-14 rounded-plate bg-(--background-tertiary) animate-pulse" />
            ) : compareValue !== undefined && (
                <span className="text-[10px] text-(--text-secondary)">WOTC {compareValue}</span>
            )}
        </div>
    );
}

function EmptyChartState({ message }: { message: string }) {
    return (
        <div className="flex items-center justify-center h-20 text-[12px] text-(--text-tertiary)">
            {message}
        </div>
    );
}

function pluralizeCards(count: number): string {
    return `${count} card${count === 1 ? '' : 's'}`;
}

/** " (12 cards)" after an average, or nothing for a plain count. */
function sampleSuffix(cards: number | undefined): string {
    return cards === undefined ? '' : ` (${pluralizeCards(cards)})`;
}

/** Wraps a chart tooltip's lines in the shared tooltip box. */
function TooltipBox({ title, children }: { title: ReactNode; children: ReactNode }) {
    return (
        <div className="bg-(--background-primary) border border-(--divider) px-2 py-1.5 rounded-card text-[11px]">
            <div className="font-bold text-(--text-primary)">{title}</div>
            {children}
        </div>
    );
}

/** Tooltip for both single-series and comparison charts; `compareLabel` names the WOTC series and
 * `formatAmount` renders a bar's value (card counts by default, or an average). */
function makeChartTooltip(compareLabel: string | null, compareLoading: boolean, formatAmount: (value: number) => string) {
    return ({ active, payload, label }: TooltipContentProps) => {
        if (!active || !payload?.length) return null;
        const row: BreakdownRow = payload[0].payload as BreakdownRow;
        if (row.isDivider) return null;
        const thisSet = `${formatAmount(row.count)}${sampleSuffix(row.sampleSize)}`;
        const compare = row.compareRaw === undefined
            ? `${formatAmount(row.compare ?? 0)}${sampleSuffix(row.compareSampleSize)}`
            : `${row.compare ?? 0} scaled (${row.compareRaw} actual)`;
        return (
            <TooltipBox title={label}>
                {compareLoading ? (
                    <>
                        <LegendEntry color={CHART_ACCENT} label={`This set: ${thisSet}`} />
                        <LegendEntry color={PLACEHOLDER_FILL} label="WOTC: loading…" />
                    </>
                ) : compareLabel === null ? (
                    <div className="text-(--text-secondary)">{thisSet}</div>
                ) : (
                    <>
                        <LegendEntry color={CHART_ACCENT} label={`This set: ${thisSet}`} />
                        <LegendEntry color={COMPARE_ACCENT} label={`${compareLabel}: ${compare}`} />
                    </>
                )}
            </TooltipBox>
        );
    };
}

function LegendEntry({ color, label }: { color: string; label: string }) {
    return (
        <div className="flex items-center gap-1.5 text-(--text-secondary)">
            <span className="inline-block size-2.5 rounded-control shrink-0" style={{ backgroundColor: color }} />
            {label}
        </div>
    );
}

/** Stand-in for the WOTC legend entry while its set loads. */
function LegendEntrySkeleton({ label }: { label: string }) {
    return (
        <div aria-label={label} className="flex items-center gap-1.5 animate-pulse">
            <span className="inline-block size-2.5 rounded-control shrink-0" style={{ backgroundColor: COMPARE_ACCENT }} />
            <span className="h-3 w-36 rounded-plate bg-(--background-tertiary)" />
        </div>
    );
}

/** `compareLoading` swaps the WOTC series for pulsing placeholder bars while a comparison set loads.
 * `formatAmount` renders a bar's value in the tooltip (defaults to a card count). */
type ChartProps = {
    data: BreakdownRow[];
    emptyMessage: string;
    compareLabel: string | null;
    compareLoading: boolean;
    formatAmount?: (value: number) => string;
};

const PLACEHOLDER_FILL = 'var(--background-quaternary)';

/** Placeholder height for a loading WOTC bar: the last set's value if one is shown, else this set's count. */
function placeholderCompare(row: BreakdownRow): number {
    return row.isDivider ? 0 : (row.compare ?? row.count);
}

/** Props for the WOTC `<Bar>`, or null when there's no comparison to draw. Recharts needs `<Bar>` as a
 * direct chart child, so this returns props rather than wrapping it in a component. */
function compareBarProps(compareLabel: string | null, compareLoading: boolean, radius: [number, number, number, number]) {
    if (compareLoading) return { dataKey: placeholderCompare, fill: PLACEHOLDER_FILL, radius, className: 'animate-pulse' };
    return compareLabel === null ? null : { dataKey: (row: BreakdownRow) => row.compare ?? 0, fill: COMPARE_ACCENT, radius };
}

// barGap/barCategoryGap keep a small surface gap between the paired bars.
const BAR_GAP = 2;
const DIVIDER_STROKE = 'var(--quaternary)';
const CHART_GRID_STROKE = 'var(--table-header)';
const CHART_CURSOR = { fill: CHART_GRID_STROKE, opacity: 0.3 };

const DIVIDER_LABEL_PREFIX = '__divider-';

/** Inserts a blank spacer row wherever `group` changes, so the chart can draw a divider line through the gap. */
function withSectionDividers(data: BreakdownRow[]): BreakdownRow[] {
    const result: BreakdownRow[] = [];
    data.forEach((row, index) => {
        if (index > 0 && row.group !== undefined && row.group !== data[index - 1].group) {
            result.push({ label: `${DIVIDER_LABEL_PREFIX}${index}`, count: 0, isDivider: true });
        }
        result.push(row);
    });
    return result;
}

function hideDividerTick(label: string): string {
    return label.startsWith(DIVIDER_LABEL_PREFIX) ? '' : label;
}

/** `scrollable` gives each column a minimum width and scrolls horizontally instead of squeezing labels together. */
/** Default height of a VerticalBarChart; charts sitting beside one can match it. */
const VERTICAL_CHART_HEIGHT = 200;

function VerticalBarChart({ data, emptyMessage, compareLabel, compareLoading, formatAmount = pluralizeCards, scrollable = false, height = VERTICAL_CHART_HEIGHT }: ChartProps & { scrollable?: boolean; height?: number }) {
    if (data.length === 0) return <EmptyChartState message={emptyMessage} />;
    const rows = withSectionDividers(data);
    const compareBar = compareBarProps(compareLabel, compareLoading, [4, 4, 0, 0]);
    const columnWidth = compareBar === null ? 36 : 48;
    return (
        <div className={scrollable ? 'overflow-x-auto' : undefined}>
            <div style={scrollable ? { minWidth: rows.length * columnWidth } : undefined}>
                <ResponsiveContainer width="100%" height={height}>
                    <BarChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }} barGap={BAR_GAP}>
                        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID_STROKE} vertical={false} />
                        <XAxis dataKey="label" fontSize={11} tickLine={false} interval={0} tickFormatter={hideDividerTick} />
                        <YAxis fontSize={11} width={28} allowDecimals={false} tickLine={false} />
                        <Tooltip content={makeChartTooltip(compareLabel, compareLoading, formatAmount)} cursor={CHART_CURSOR} />
                        {rows.filter(row => row.isDivider).map(row => (
                            <ReferenceLine key={row.label} x={row.label} stroke={DIVIDER_STROKE} strokeWidth={1} />
                        ))}
                        <Bar dataKey="count" fill={CHART_ACCENT} radius={[4, 4, 0, 0]} />
                        {compareBar && <Bar {...compareBar} />}
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

/** Count-weighted average value of "GROUP N" rows; `useCompare` weights by the unscaled WOTC counts. */
function averageGroupedValue(rows: BreakdownRow[], useCompare: boolean): number | null {
    let total = 0;
    let weight = 0;
    for (const row of rows) {
        const rowWeight = useCompare ? (row.compareRaw ?? 0) : row.count;
        total += groupedKeyValue(row.label) * rowWeight;
        weight += rowWeight;
    }
    return weight > 0 ? Math.round((total / weight) * 10) / 10 : null;
}

const formatRating = (rating: number) => `${rating >= 0 ? '+' : ''}${rating}`;

/** "Avg X · WOTC Y" label shown above a chart; omits the WOTC part when there's no comparison. */
function ChartAverage({ value, compareValue, label = 'Avg' }: { value: string | null; compareValue?: string | null; label?: string }) {
    return (
        <span className="text-[10px] text-(--text-tertiary)">
            {`${label} ${value ?? '–'}`}
            {compareValue != null && ` · WOTC ${compareValue}`}
        </span>
    );
}

/** Distinct `group` values of `rows`, in row order. */
function rowGroups(rows: BreakdownRow[]): string[] {
    return [...new Set(rows.map(row => row.group ?? ''))];
}

/** Bordered card holding one titled chart, with its average vs WOTC's in the header. */
function ChartPanel({ title, average, fit, className, children }: { title: string; average?: ReactNode; fit?: FitCheck | null; className?: string; children: ReactNode }) {
    return (
        <div className={`rounded-card border border-(--divider) p-2 min-w-0 ${className ?? ''}`}>
            <div className="flex items-baseline justify-between gap-2 px-1">
                <span className={`flex items-center gap-1.5 ${headingClass('panel')}`}>
                    {title}
                    {fit && <FitDot check={fit} />}
                </span>
                {average}
            </div>
            {children}
        </div>
    );
}

/** One small column chart per group of "GROUP N" rows (defensive position, pitcher role), each with
 * the release's average value vs WOTC's. `formatValue` renders both the averages and the column labels. */
function GroupedColumnCharts({ data, emptyMessage, compareLabel, compareLoading, formatValue = String, averageTolerance, distributionTolerance }: ChartProps & {
    formatValue?: (value: number) => string;
    /** When set, each panel's WOTC fit also checks its average against this tolerance. */
    averageTolerance?: Tolerance;
    distributionTolerance?: Tolerance;
}) {
    if (data.length === 0) return <EmptyChartState message={emptyMessage} />;
    return (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
            {rowGroups(data).map(group => {
                const rows = data.filter(row => row.group === group);
                const average = averageGroupedValue(rows, false);
                const compareAverage = compareLabel === null ? null : averageGroupedValue(rows, true);
                const fit = compareLabel === null ? null : combineChecks(
                    distributionCheck(rows, MIN_PANEL_CARDS_TO_SCORE, distributionTolerance),
                    averageTolerance && average !== null && compareAverage !== null
                        ? averageCheck('Avg', average, compareAverage, averageTolerance)
                        : null,
                );
                return (
                    <ChartPanel
                        key={group}
                        title={group}
                        fit={fit}
                        average={<ChartAverage
                            value={average !== null ? formatValue(average) : null}
                            compareValue={compareAverage !== null ? formatValue(compareAverage) : null}
                        />}
                    >
                        <VerticalBarChart
                            data={rows.map(row => ({ ...row, label: formatValue(groupedKeyValue(row.label)) }))}
                            emptyMessage={emptyMessage}
                            compareLabel={compareLabel}
                            compareLoading={compareLoading}
                            height={140}
                        />
                    </ChartPanel>
                );
            })}
        </div>
    );
}

const COMMAND_PANELS: Record<string, { title: string; averageKey: keyof SummaryAverages }> = {
    [GROUP_PITCHERS]: { title: 'Pitchers · Control', averageKey: 'control' },
    [GROUP_HITTERS]: { title: 'Hitters · On-Base', averageKey: 'onBase' },
};

type PanelInfo = { title: string; average?: ReactNode; fit?: FitCheck | null };

/** One column chart per row `group` (e.g. Hitters / Pitchers): side by side, or stacked on their own
 * lines with scrolling columns when `stacked`. `panels` titles each group. */
function PanelCharts({ data, panels, stacked = false, ...chartProps }: ChartProps & { panels: Record<string, PanelInfo>; stacked?: boolean }) {
    if (data.length === 0) return <EmptyChartState message={chartProps.emptyMessage} />;
    return (
        <div className={`flex gap-4 ${stacked ? 'flex-col' : 'flex-wrap'}`}>
            {rowGroups(data).map(group => (
                <ChartPanel
                    key={group}
                    title={panels[group]?.title ?? group}
                    fit={panels[group]?.fit}
                    className={stacked ? undefined : 'flex-1 basis-64'}
                    average={panels[group]?.average}
                >
                    <VerticalBarChart data={data.filter(row => row.group === group)} scrollable={stacked} {...chartProps} />
                </ChartPanel>
            ))}
        </div>
    );
}

/** One scatter dot: a card's command against its points. */
type ScatterPoint = { x: number; y: number; name: string; year: string | number; command: number };

// Cards share whole-number commands, so dots spread sideways a little to stay visible.
const SCATTER_JITTER = 0.5;

function scatterPoints(snapshots: CardDatabaseRecord[]): ScatterPoint[] {
    return snapshots.filter(c => c.command != null).map((c, index) => ({
        // Golden-ratio spacing spreads neighbours evenly without randomness, so dots don't jump on re-render.
        x: c.command + ((index * 0.618) % 1 - 0.5) * SCATTER_JITTER,
        y: c.points ?? 0,
        name: c.name,
        year: c.year,
        command: c.command,
    }));
}

function ScatterTooltip({ active, payload }: TooltipContentProps) {
    if (!active || !payload?.length) return null;
    const point = payload[0].payload as ScatterPoint;
    return (
        <TooltipBox title={`${point.year} ${point.name}`}>
            <div className="text-(--text-secondary)">{`Command ${point.command} · ${point.y} PTS`}</div>
        </TooltipBox>
    );
}

/** Points against On-Base (hitters) and Control (pitchers), one panel each, with the WOTC set's cards behind. */
function PointsCommandScatter({ snapshots, compareSnapshots, compareLoading }: {
    snapshots: CardDatabaseRecord[];
    compareSnapshots: CardDatabaseRecord[] | null;
    compareLoading: boolean;
}) {
    return (
        <div className="flex flex-wrap gap-4">
            {CHART_GROUP_ORDER.map(group => {
                const ofGroup = (cards: CardDatabaseRecord[]) => cards.filter(c => sideGroup(c) === group);
                const points = scatterPoints(ofGroup(snapshots));
                if (points.length === 0) return null;
                const comparePoints = compareSnapshots ? scatterPoints(ofGroup(compareSnapshots)) : [];
                return (
                    <ChartPanel key={group} title={COMMAND_PANELS[group].title} className="flex-1 basis-64">
                        <ResponsiveContainer width="100%" height={240}>
                            <ScatterChart margin={{ top: 8, right: 8, left: 0, bottom: 4 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID_STROKE} />
                                <XAxis type="number" dataKey="x" fontSize={11} tickLine={false} allowDecimals={false} domain={['dataMin - 1', 'dataMax + 1']} />
                                <YAxis type="number" dataKey="y" fontSize={11} width={36} tickLine={false} />
                                <ZAxis range={[28, 28]} />
                                <Tooltip content={ScatterTooltip} cursor={false} />
                                {comparePoints.length > 0 && (
                                    <Scatter
                                        data={comparePoints}
                                        fill={compareLoading ? PLACEHOLDER_FILL : COMPARE_ACCENT}
                                        fillOpacity={0.35}
                                        className={compareLoading ? 'animate-pulse' : undefined}
                                    />
                                )}
                                <Scatter data={points} fill={CHART_ACCENT} fillOpacity={0.8} />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </ChartPanel>
                );
            })}
        </div>
    );
}

type SubsetFilter = 'all' | ParentPositionGroup;

const SUBSET_OPTIONS: { label: string; value: SubsetFilter }[] = [
    { label: 'All', value: 'all' },
    { label: 'Position Players', value: 'Position Player' },
    { label: 'Starting Pitchers', value: 'Starting Pitcher' },
    { label: 'Relief Pitchers', value: 'Relief Pitcher' },
];

function filterToSubset(snapshots: CardDatabaseRecord[], subset: SubsetFilter): CardDatabaseRecord[] {
    return subset === 'all' ? snapshots : snapshots.filter(c => parentPositionGroup(c) === subset);
}

function SubsetFilterBar({ value, onChange }: { value: SubsetFilter; onChange: (v: SubsetFilter) => void }) {
    return (
        <div className="flex flex-wrap gap-1.5">
            {SUBSET_OPTIONS.map(opt => (
                <button
                    key={opt.value}
                    type="button"
                    onClick={() => onChange(opt.value)}
                    className={choiceClass(value === opt.value, 'sm')}
                >
                    {opt.label}
                </button>
            ))}
        </div>
    );
}

/** `minHeight` lets a short chart (few rows) stretch its bars to match a neighbouring chart's height. */
function HorizontalBarChart({ data, emptyMessage, compareLabel, compareLoading, formatAmount = pluralizeCards, minHeight = 120 }: ChartProps & { minHeight?: number }) {
    if (data.length === 0) return <EmptyChartState message={emptyMessage} />;
    const rows = withSectionDividers(data);
    const compareBar = compareBarProps(compareLabel, compareLoading, [0, 4, 4, 0]);
    const rowHeight = compareBar === null ? 32 : 44;
    return (
        <ResponsiveContainer width="100%" height={Math.max(minHeight, rows.length * rowHeight)}>
            <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }} barGap={BAR_GAP}>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID_STROKE} horizontal={false} />
                <XAxis type="number" fontSize={11} allowDecimals={false} tickLine={false} />
                <YAxis
                    type="category"
                    dataKey="label"
                    fontSize={11}
                    width={64}
                    tickLine={false}
                    interval={0}
                    tickFormatter={hideDividerTick}
                />
                <Tooltip content={makeChartTooltip(compareLabel, compareLoading, formatAmount)} cursor={CHART_CURSOR} />
                {rows.filter(row => row.isDivider).map(row => (
                    <ReferenceLine key={row.label} y={row.label} stroke={DIVIDER_STROKE} strokeWidth={1} />
                ))}
                <Bar dataKey="count" fill={CHART_ACCENT} radius={[0, 4, 4, 0]} />
                {compareBar && <Bar {...compareBar} />}
            </BarChart>
        </ResponsiveContainer>
    );
}

const NO_COMPARISON = '';

const COMPARISON_OPTIONS = [
    { value: NO_COMPARISON, label: 'None' },
    ...WOTC_BASE_SETS.map(set => ({ value: set, label: `${set} Base Set` })),
];

const comparisonStorageKey = (editionId: string) => `releaseBuilder.wotcComparisonSet.${editionId}`;

/** Last WOTC comparison set selected for this edition, restored across visits. */
function loadComparisonSet(editionId: string): WotcBaseSet | null {
    try {
        const stored = localStorage.getItem(comparisonStorageKey(editionId));
        return (WOTC_BASE_SETS as readonly string[]).includes(stored ?? '') ? stored as WotcBaseSet : null;
    } catch { return null; }
}

function saveComparisonSet(editionId: string, set: WotcBaseSet | null) {
    try {
        if (set) localStorage.setItem(comparisonStorageKey(editionId), set);
        else localStorage.removeItem(comparisonStorageKey(editionId));
    } catch { /* storage unavailable */ }
}

/** Loads the selected WOTC base set. While a new set loads, the last loaded one stays in `snapshots`
 * (`set` names it) so the charts don't collapse and re-expand; `snapshots` is null with no selection. */
function useWotcComparison(selectedSet: WotcBaseSet | null) {
    // Tagged with the set it belongs to, so a stale result is ignored (and "loading" derived) after the selection changes.
    const [result, setResult] = useState<{ set: WotcBaseSet; snapshots: CardDatabaseRecord[] | null; error: string | null } | null>(null);

    useEffect(() => {
        if (!selectedSet) return;
        let cancelled = false;
        fetchWotcBaseSet(selectedSet)
            .then(snapshots => { if (!cancelled) setResult({ set: selectedSet, snapshots, error: null }); })
            .catch(err => { if (!cancelled) setResult({ set: selectedSet, snapshots: null, error: err.message ?? 'Failed to load WOTC set.' }); });
        return () => { cancelled = true; };
    }, [selectedSet]);

    const current = selectedSet && result?.set === selectedSet ? result : null;
    const loading = selectedSet !== null && current === null;
    const shown = loading && result?.snapshots ? result : current;
    return {
        set: shown?.set ?? null,
        snapshots: shown?.snapshots ?? null,
        loading,
        error: current?.error ?? null,
    };
}

// =============================================================================
// MARK: - COMPONENT
// =============================================================================

export function SummaryCharts({ cards, editionId }: SummaryChartsProps) {
    const [subsetFilter, setSubsetFilter] = useState<SubsetFilter>('all');
    const [comparisonSet, setComparisonSet] = useState<WotcBaseSet | null>(() => loadComparisonSet(editionId));
    const [commandIncludesOuts, setCommandIncludesOuts] = useState(false);
    const wotc = useWotcComparison(comparisonSet);

    useEffect(() => saveComparisonSet(editionId, comparisonSet), [editionId, comparisonSet]);

    const filteredSnapshots = useMemo(
        () => filterToSubset(cards.map(c => c.card_snapshot), subsetFilter),
        [cards, subsetFilter]
    );
    // The WOTC set is narrowed to the same subset, so scaling compares like-for-like
    // (e.g. your 30 starters vs WOTC's starters, scaled to 30).
    const comparison = useMemo<Comparison | null>(
        () => wotc.snapshots ? { snapshots: filterToSubset(wotc.snapshots, subsetFilter) } : null,
        [wotc.snapshots, subsetFilter]
    );
    const compareLabel = comparison && wotc.set ? `WOTC ${wotc.set}` : null;

    const breakdowns = useMemo(() => {
        const build = (spec: BreakdownSpec) => buildBreakdown(filteredSnapshots, spec, comparison);
        return {
            parentPosition: build(SPECS.parentPosition),
            points: build(SPECS.points),
            command: build(SPECS.command),
            commandOuts: build(SPECS.commandOuts),
            position: build(SPECS.position),
            team: build(SPECS.team),
            speed: build(SPECS.speed),
            ip: build(SPECS.ip),
            defense: build(SPECS.defense),
            hand: build(SPECS.hand),
            icons: build(SPECS.icons),
            pointsByPosition: buildAverageBreakdown(filteredSnapshots, AVERAGE_SPECS.pointsByPosition, comparison),
            // A result neither set's charts use (e.g. PU for hitters) gets no column.
            chartResults: buildAverageBreakdown(filteredSnapshots, AVERAGE_SPECS.chartResults, comparison)
                .filter(row => row.count > 0 || (row.compare ?? 0) > 0),
        };
    }, [filteredSnapshots, comparison]);

    const averages = buildAverages(filteredSnapshots);
    const compareAverages = comparison ? buildAverages(comparison.snapshots) : null;

    // Per-chart WOTC fit for the single-chart sections; Command, IP and Defense rate each of their
    // panels instead. Teams is left out since team spread says little about set balance.
    const fits = compareAverages ? {
        parentPosition: combineChecks(distributionCheck(breakdowns.parentPosition)),
        points: combineChecks(distributionCheck(breakdowns.points),
            averageCheck('Avg PTS', averages.points, compareAverages.points, POINTS_AVERAGE_TOLERANCE)),
        // Judged on On-Base/Control alone so "Include Outs" doesn't change it.
        command: Object.fromEntries(Object.entries(COMMAND_PANELS).map(([group, { averageKey }]) => [
            group,
            combineChecks(
                distributionCheck(breakdowns.command.filter(row => row.group === group), MIN_PANEL_CARDS_TO_SCORE),
                averageCheck('Avg', averages[averageKey], compareAverages[averageKey], COMMAND_AVERAGE_TOLERANCE),
            ),
        ])),
        chartResults: Object.fromEntries(CHART_GROUP_ORDER.map(group => [
            group,
            chartResultsCheck(breakdowns.chartResults.filter(row => row.group === group)),
        ])),
        position: combineChecks(distributionCheck(breakdowns.position)),
        pointsByPosition: averageGapCheck(breakdowns.pointsByPosition, POINTS_AVERAGE_TOLERANCE, 'PTS'),
        speed: combineChecks(distributionCheck(breakdowns.speed),
            averageCheck('Avg Speed', averages.speed, compareAverages.speed, SPEED_AVERAGE_TOLERANCE)),
        hand: worstCheck(CHART_GROUP_ORDER.map(group => distributionCheck(
            breakdowns.hand.filter(row => row.group === group), MIN_PANEL_CARDS_TO_SCORE, DISTRIBUTION_TOLERANCE, group,
        ))),
        icons: combineChecks(distributionCheck(breakdowns.icons),
            averageCheck('Icons per card', averages.icons, compareAverages.icons, ICONS_AVERAGE_TOLERANCE)),
    } : null;

    if (cards.length === 0) {
        return (
            <EmptyState size="panel" title="No cards yet.">
                Add cards to see distribution charts.
            </EmptyState>
        );
    }

    const chartProps = { compareLabel, compareLoading: wotc.loading };

    return (
        <div className="flex flex-col gap-6 p-4">
            <div className="flex flex-wrap items-end justify-between gap-3">
                <SubsetFilterBar value={subsetFilter} onChange={setSubsetFilter} />
                <CustomSelect
                    size="sm"
                    prefix="Compare to WOTC"
                    options={COMPARISON_OPTIONS}
                    value={comparisonSet ?? NO_COMPARISON}
                    onChange={value => setComparisonSet(value === NO_COMPARISON ? null : value as WotcBaseSet)}
                />
            </div>

            {wotc.error && (
                <div className="text-[12px] text-(--red)">{wotc.error}</div>
            )}
            {(wotc.loading || (compareLabel && comparison)) && (
                <div className="flex flex-col gap-1 text-[11px]">
                    <div className="flex flex-wrap gap-4">
                        <LegendEntry color={CHART_ACCENT} label={`This set (${pluralizeCards(filteredSnapshots.length)})`} />
                        {wotc.loading || !comparison ? (
                            <LegendEntrySkeleton label={`Loading WOTC ${comparisonSet}`} />
                        ) : (
                            <LegendEntry color={COMPARE_ACCENT} label={`${compareLabel} (${pluralizeCards(comparison.snapshots.length)})`} />
                        )}
                    </div>
                    {comparison && comparison.snapshots.length !== filteredSnapshots.length && (
                        <span className="text-(--text-tertiary)">
                            {compareLabel} counts are scaled to this set's size.
                        </span>
                    )}
                </div>
            )}

            <div className="flex flex-wrap gap-3">
                <StatTile label={subsetFilter === 'all' ? 'Cards' : 'Cards in Subset'} value={filteredSnapshots.length} />
                <StatTile label="Avg PTS" value={averages.points} compareValue={compareAverages?.points} compareLoading={wotc.loading} />
                <StatTile label="Avg OnBase" value={averages.onBase} compareValue={compareAverages?.onBase} compareLoading={wotc.loading} />
                <StatTile label="Avg Control" value={averages.control} compareValue={compareAverages?.control} compareLoading={wotc.loading} />
                <StatTile label="Avg Speed" value={averages.speed} compareValue={compareAverages?.speed} compareLoading={wotc.loading} />
                <StatTile label="Avg IP" value={averages.ip} compareValue={compareAverages?.ip} compareLoading={wotc.loading} />
            </div>

            {filteredSnapshots.length === 0 ? (
                <EmptyState size="inline">No cards match this subset.</EmptyState>
            ) : (
                <>
                    {/* Side by side (1/3 – 2/3) when there's room, stacked otherwise. */}
                    <div className="flex flex-wrap gap-6">
                        <Section title="Position Group" fit={fits?.parentPosition} className="flex-[1_1_0%] min-w-[min(20rem,100%)]">
                            <HorizontalBarChart data={breakdowns.parentPosition} emptyMessage="No data yet." minHeight={VERTICAL_CHART_HEIGHT} {...chartProps} />
                        </Section>

                        <Section
                            title="Points Distribution"
                            fit={fits?.points}
                            action={<ChartAverage value={String(averages.points)} compareValue={compareAverages && String(compareAverages.points)} />}
                            className="flex-[2_1_0%] min-w-[min(20rem,100%)]"
                        >
                            <VerticalBarChart data={breakdowns.points} emptyMessage="No point data yet." {...chartProps} />
                        </Section>
                    </div>

                    <Section
                        title="Command (Control / On-Base)"
                        action={<FormEnabler label="Include Outs" isEnabled={commandIncludesOuts} onChange={enabled => setCommandIncludesOuts(!enabled)} />}
                    >
                        <PanelCharts
                            data={commandIncludesOuts ? breakdowns.commandOuts : breakdowns.command}
                            emptyMessage="No command data yet."
                            stacked={commandIncludesOuts}
                            panels={Object.fromEntries(Object.entries(COMMAND_PANELS).map(([group, { title, averageKey }]) => [group, {
                                title,
                                fit: fits?.command[group],
                                average: <ChartAverage value={String(averages[averageKey])} compareValue={compareAverages && String(compareAverages[averageKey])} />,
                            }]))}
                            {...chartProps}
                        />
                    </Section>

                    <Section title="Points vs Command">
                        <PointsCommandScatter snapshots={filteredSnapshots} compareSnapshots={comparison?.snapshots ?? null} compareLoading={wotc.loading} />
                    </Section>

                    <Section title="Chart Results (Avg Slots)">
                        <PanelCharts
                            data={breakdowns.chartResults}
                            emptyMessage="No chart data yet."
                            panels={Object.fromEntries(CHART_GROUP_ORDER.map(group => [group, { title: group, fit: fits?.chartResults[group] }]))}
                            formatAmount={value => `${value} avg slots`}
                            {...chartProps}
                        />
                    </Section>

                    <Section title="Position Breakdown" fit={fits?.position}>
                        <HorizontalBarChart data={breakdowns.position} emptyMessage="No position data yet." {...chartProps} />
                    </Section>

                    <Section title="Avg Points by Position" fit={fits?.pointsByPosition}>
                        <HorizontalBarChart data={breakdowns.pointsByPosition} emptyMessage="No position data yet." formatAmount={value => `${value} PTS avg`} {...chartProps} />
                    </Section>

                    <div className="flex flex-wrap gap-6">
                        <Section title="Handedness" fit={fits?.hand} className="flex-[1_1_0%] min-w-[min(20rem,100%)]">
                            <HorizontalBarChart data={breakdowns.hand} emptyMessage="No handedness data yet." minHeight={VERTICAL_CHART_HEIGHT} {...chartProps} />
                        </Section>

                        <Section
                            title="Icons"
                            fit={fits?.icons}
                            action={<ChartAverage label="Per card" value={String(averages.icons)} compareValue={compareAverages && String(compareAverages.icons)} />}
                            className="flex-[2_1_0%] min-w-[min(20rem,100%)]"
                        >
                            <VerticalBarChart data={breakdowns.icons} emptyMessage="No cards with icons." {...chartProps} />
                        </Section>
                    </div>

                    <Section title="Teams">
                        <VerticalBarChart data={breakdowns.team} emptyMessage="No team data yet." scrollable {...chartProps} />
                    </Section>

                    <Section title="Speed" fit={fits?.speed} action={<ChartAverage value={String(averages.speed)} compareValue={compareAverages && String(compareAverages.speed)} />}>
                        <VerticalBarChart data={breakdowns.speed} emptyMessage="No hitters with speed yet." {...chartProps} />
                    </Section>

                    <Section title="IP">
                        <GroupedColumnCharts data={breakdowns.ip} emptyMessage="No pitchers yet." averageTolerance={IP_AVERAGE_TOLERANCE} {...chartProps} />
                    </Section>

                    <Section title="Defense">
                        <GroupedColumnCharts data={breakdowns.defense} emptyMessage="No defensive ratings yet." formatValue={formatRating} distributionTolerance={DEFENSE_DISTRIBUTION_TOLERANCE} {...chartProps} />
                    </Section>
                </>
            )}
        </div>
    );
}
