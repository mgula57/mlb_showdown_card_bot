import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, type TooltipContentProps } from 'recharts';
import { fetchWotcBaseSet, WOTC_BASE_SETS, type ReleaseCard, type WotcBaseSet } from '../../api/releases';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { defenseAtPosition } from '../shared/DefenseUtils';
import FormDropdown from '../customs/FormDropdown';
import FormEnabler from '../customs/FormEnabler';

type SummaryChartsProps = {
    cards: ReleaseCard[];
};

const POINTS_BUCKET_SIZE = 50;
const CHART_ACCENT = 'var(--secondary)';
// WOTC reference series: a distinct hue from the user's near-monochrome bars, defined in both themes.
const COMPARE_ACCENT = 'var(--showdown-blue)';

// =============================================================================
// MARK: - AGGREGATION
// =============================================================================

type BreakdownKey = string | number;

/** One bar group. `compare` is the WOTC count scaled to this set's size; `compareRaw` is unscaled. */
type BreakdownRow = {
    label: string;
    count: number;
    compare?: number;
    compareRaw?: number;
    /** Section the row belongs to; horizontal charts draw a divider wherever it changes. */
    group?: string;
    /** Blank spacer row that holds a section divider, not data. */
    isDivider?: boolean;
};

/** How to bucket cards for one chart. `sort: 'key'` orders ascending by key (numeric stats like
 * command/IP); `'count'` orders by frequency descending (categorical fields); a function sorts keys directly. */
type BreakdownSpec = {
    keyFn: (snapshot: CardDatabaseRecord) => BreakdownKey | null | undefined;
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
        const key = keyFn(snapshot);
        if (key === null || key === undefined || key === '') continue;
        counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return counts;
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
            row.compare = Math.round(row.compareRaw * scaleFor(key) * 10) / 10;
        }
        return row;
    });
}

const PARENT_POSITION_ORDER = ['Position Player', 'Starting Pitcher', 'Relief Pitcher'] as const;
type ParentPositionGroup = typeof PARENT_POSITION_ORDER[number];

/** Closers (and any other non-starter pitcher) roll up into Relief Pitcher. */
function parentPositionGroup(snapshot: CardDatabaseRecord): ParentPositionGroup {
    if (!snapshot.is_pitcher) return 'Position Player';
    return (snapshot.positions_list ?? []).includes('STARTER') ? 'Starting Pitcher' : 'Relief Pitcher';
}

// Command keys pack [hitter flag][command][outs] into one sortable number so pitchers (Control)
// sort ahead of hitters (On-Base) and each side gets its own section. Outs never reach 100.
const COMMAND_OUTS_MULTIPLIER = 100;
const COMMAND_HITTER_OFFSET = 100 * COMMAND_OUTS_MULTIPLIER;

function commandKey(c: CardDatabaseRecord, includeOuts: boolean): number {
    const command = (c.command ?? 0) * (includeOuts ? COMMAND_OUTS_MULTIPLIER : 1);
    return (c.is_pitcher ? 0 : COMMAND_HITTER_OFFSET) + command + (includeOuts ? (c.outs ?? 0) : 0);
}

function commandKeyGroup(key: BreakdownKey): string {
    return Number(key) >= COMMAND_HITTER_OFFSET ? 'Hitters' : 'Pitchers';
}

// Scorecard order (C through RF), with the grouped IF/OF/LF-RF ratings older sets use slotted in beside their members.
const DEFENSE_POSITION_ORDER = ['C', 'CA', '1B', '2B', '3B', 'SS', 'IF', 'LF', 'LF/RF', 'CF', 'RF', 'OF'];

function defenseKeyPosition(key: BreakdownKey): string {
    return String(key).split(' ')[0];
}

/** Orders "POS +N" defense keys by position, then by rating descending. */
function compareDefenseKeys(a: BreakdownKey, b: BreakdownKey): number {
    const parse = (key: BreakdownKey) => {
        const [position, rating] = String(key).split(' ');
        const positionIndex = DEFENSE_POSITION_ORDER.indexOf(position);
        return { positionIndex: positionIndex === -1 ? DEFENSE_POSITION_ORDER.length : positionIndex, rating: Number(rating) };
    };
    const left = parse(a);
    const right = parse(b);
    return left.positionIndex - right.positionIndex || right.rating - left.rating;
}

/** Historical team codes (as on WOTC cards) mapped to the franchise's current code, so the Teams
 * breakdown groups e.g. WOTC's MON with WSN. Applies to both sets, which keeps the comparison aligned. */
const FRANCHISE_CODE: Record<string, string> = {
    MON: 'WSN',
    FLA: 'MIA',
    CAL: 'LAA',
    ANA: 'LAA',
    TBD: 'TBR',
    OAK: 'ATH',
};

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
    },
    commandOuts: {
        keyFn: c => c.command == null ? null : commandKey(c, true),
        labelFn: key => {
            const commandOuts = Number(key) % COMMAND_HITTER_OFFSET;
            return `${Math.floor(commandOuts / COMMAND_OUTS_MULTIPLIER)}/${commandOuts % COMMAND_OUTS_MULTIPLIER}`;
        },
        sort: 'key',
        groupFn: commandKeyGroup,
    },
    position: { keyFn: c => c.positions_list?.[0] ?? c.player_type, sort: 'count' },
    team: { keyFn: c => c.team ? (FRANCHISE_CODE[c.team] ?? c.team) : c.team, sort: 'count' },
    speed: { keyFn: c => c.is_pitcher ? null : c.speed, sort: 'key' },
    ip: { keyFn: c => c.is_pitcher ? c.ip : null, sort: 'key' },
    defense: {
        keyFn: c => {
            const primaryPosition = c.positions_list?.[0];
            if (c.is_pitcher || !primaryPosition || primaryPosition === 'DH') return null;
            const defValue = defenseAtPosition(c.positions_and_defense, primaryPosition);
            if (defValue === null) return null;
            return `${primaryPosition} ${defValue >= 0 ? '+' : ''}${defValue}`;
        },
        sort: compareDefenseKeys,
        groupFn: defenseKeyPosition,
        scaleWithinGroup: true,
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

type SummaryAverages = { points: number; onBase: number; control: number; speed: number; ip: number };

function buildAverages(snapshots: CardDatabaseRecord[]): SummaryAverages {
    return {
        points: average(snapshots, c => c.points, 0),
        onBase: average(snapshots.filter(c => !c.is_pitcher), c => c.command, 1),
        control: average(snapshots.filter(c => c.is_pitcher), c => c.command, 1),
        speed: average(snapshots.filter(c => !c.is_pitcher), c => c.speed, 1),
        ip: average(snapshots.filter(c => c.is_pitcher), c => c.ip, 1),
    };
}

// =============================================================================
// MARK: - PRESENTATION
// =============================================================================

function Section({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
    return (
        <div>
            <div className="flex items-center justify-between gap-2 mb-2">
                <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide">
                    {title}
                </div>
                {action}
            </div>
            {children}
        </div>
    );
}

function StatTile({ label, value, compareValue }: { label: string; value: string | number; compareValue?: string | number }) {
    return (
        <div className="flex flex-col items-center justify-center rounded-lg border border-(--divider) px-3 py-2 min-w-22">
            <span className="text-[18px] font-black text-(--text-primary)">{value}</span>
            <span className="text-[10px] text-(--text-tertiary) uppercase tracking-wide">{label}</span>
            {compareValue !== undefined && (
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

/** Tooltip for both single-series and comparison charts; `compareLabel` names the WOTC series. */
function makeChartTooltip(compareLabel: string | null) {
    return ({ active, payload, label }: TooltipContentProps) => {
        if (!active || !payload?.length) return null;
        const row: BreakdownRow = payload[0].payload as BreakdownRow;
        if (row.isDivider) return null;
        return (
            <div className="bg-(--background-primary) border border-(--divider) px-2 py-1.5 rounded-lg text-[11px]">
                <div className="font-bold text-(--text-primary)">{label}</div>
                {compareLabel === null ? (
                    <div className="text-(--text-secondary)">{pluralizeCards(row.count)}</div>
                ) : (
                    <>
                        <LegendEntry color={CHART_ACCENT} label={`This set: ${pluralizeCards(row.count)}`} />
                        <LegendEntry
                            color={COMPARE_ACCENT}
                            label={`${compareLabel}: ${row.compare ?? 0} scaled (${row.compareRaw ?? 0} actual)`}
                        />
                    </>
                )}
            </div>
        );
    };
}

function LegendEntry({ color, label }: { color: string; label: string }) {
    return (
        <div className="flex items-center gap-1.5 text-(--text-secondary)">
            <span className="inline-block size-2.5 rounded-sm shrink-0" style={{ backgroundColor: color }} />
            {label}
        </div>
    );
}

type ChartProps = { data: BreakdownRow[]; emptyMessage: string; compareLabel: string | null };

// barGap/barCategoryGap keep a small surface gap between the paired bars.
const BAR_GAP = 2;
const DIVIDER_STROKE = 'var(--quaternary)';

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
function VerticalBarChart({ data, emptyMessage, compareLabel, scrollable = false, height = 200 }: ChartProps & { scrollable?: boolean; height?: number }) {
    if (data.length === 0) return <EmptyChartState message={emptyMessage} />;
    const rows = withSectionDividers(data);
    const columnWidth = compareLabel === null ? 36 : 48;
    return (
        <div className={scrollable ? 'overflow-x-auto' : undefined}>
            <div style={scrollable ? { minWidth: rows.length * columnWidth } : undefined}>
                <ResponsiveContainer width="100%" height={height}>
                    <BarChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }} barGap={BAR_GAP}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--table-header)" vertical={false} />
                        <XAxis dataKey="label" fontSize={11} tickLine={false} interval={0} tickFormatter={hideDividerTick} />
                        <YAxis fontSize={11} width={28} allowDecimals={false} tickLine={false} />
                        <Tooltip content={makeChartTooltip(compareLabel)} cursor={{ fill: 'var(--table-header)', opacity: 0.3 }} />
                        {rows.filter(row => row.isDivider).map(row => (
                            <ReferenceLine key={row.label} x={row.label} stroke={DIVIDER_STROKE} strokeWidth={1} />
                        ))}
                        <Bar dataKey="count" fill={CHART_ACCENT} radius={[4, 4, 0, 0]} />
                        {compareLabel !== null && <Bar dataKey="compare" fill={COMPARE_ACCENT} radius={[4, 4, 0, 0]} />}
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

/** Count-weighted average defense rating of "POS +N" rows; `useCompare` weights by the unscaled WOTC counts. */
function averageDefenseRating(rows: BreakdownRow[], useCompare: boolean): number | null {
    let total = 0;
    let weight = 0;
    for (const row of rows) {
        const rowWeight = useCompare ? (row.compareRaw ?? 0) : row.count;
        total += Number(row.label.split(' ')[1]) * rowWeight;
        weight += rowWeight;
    }
    return weight > 0 ? Math.round((total / weight) * 10) / 10 : null;
}

const formatRating = (rating: number) => `${rating >= 0 ? '+' : ''}${rating}`;

/** One small column chart per defensive position, with the release's average rating vs WOTC's. */
function DefensePositionCharts({ data, emptyMessage, compareLabel }: ChartProps) {
    if (data.length === 0) return <EmptyChartState message={emptyMessage} />;
    const positions = [...new Set(data.map(row => row.group ?? ''))];
    return (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4">
            {positions.map(position => {
                const rows = data.filter(row => row.group === position);
                const average = averageDefenseRating(rows, false);
                const compareAverage = compareLabel === null ? null : averageDefenseRating(rows, true);
                return (
                    <div key={position} className="rounded-lg border border-(--divider) p-2">
                        <div className="flex items-baseline justify-between gap-2 px-1">
                            <span className="text-[13px] font-black text-(--text-primary)">{position}</span>
                            <span className="text-[10px] text-(--text-tertiary)">
                                {average !== null ? `Avg ${formatRating(average)}` : 'Avg –'}
                                {compareAverage !== null && ` · WOTC ${formatRating(compareAverage)}`}
                            </span>
                        </div>
                        <VerticalBarChart
                            data={rows.map(row => ({ ...row, label: formatRating(Number(row.label.split(' ')[1])) }))}
                            emptyMessage={emptyMessage}
                            compareLabel={compareLabel}
                            height={140}
                        />
                    </div>
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
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-bold border transition-colors
                        ${value === opt.value
                            ? 'bg-(--secondary) text-(--background-primary) border-(--secondary)'
                            : 'border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary)'}`}
                >
                    {opt.label}
                </button>
            ))}
        </div>
    );
}

function HorizontalBarChart({ data, emptyMessage, compareLabel }: ChartProps) {
    if (data.length === 0) return <EmptyChartState message={emptyMessage} />;
    const rows = withSectionDividers(data);
    const rowHeight = compareLabel === null ? 32 : 44;
    return (
        <ResponsiveContainer width="100%" height={Math.max(120, rows.length * rowHeight)}>
            <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }} barGap={BAR_GAP}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--table-header)" horizontal={false} />
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
                <Tooltip content={makeChartTooltip(compareLabel)} cursor={{ fill: 'var(--table-header)', opacity: 0.3 }} />
                {rows.filter(row => row.isDivider).map(row => (
                    <ReferenceLine key={row.label} y={row.label} stroke={DIVIDER_STROKE} strokeWidth={1} />
                ))}
                <Bar dataKey="count" fill={CHART_ACCENT} radius={[0, 4, 4, 0]} />
                {compareLabel !== null && <Bar dataKey="compare" fill={COMPARE_ACCENT} radius={[0, 4, 4, 0]} />}
            </BarChart>
        </ResponsiveContainer>
    );
}

const NO_COMPARISON = '';

const COMPARISON_OPTIONS = [
    { value: NO_COMPARISON, label: 'None' },
    ...WOTC_BASE_SETS.map(set => ({ value: set, label: `${set} Base Set` })),
];

/** Loads the selected WOTC base set; `snapshots` is null while nothing is selected or loading. */
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
    return {
        snapshots: current?.snapshots ?? null,
        loading: selectedSet !== null && current === null,
        error: current?.error ?? null,
    };
}

// =============================================================================
// MARK: - COMPONENT
// =============================================================================

export function SummaryCharts({ cards }: SummaryChartsProps) {
    const [subsetFilter, setSubsetFilter] = useState<SubsetFilter>('all');
    const [comparisonSet, setComparisonSet] = useState<WotcBaseSet | null>(null);
    const [commandIncludesOuts, setCommandIncludesOuts] = useState(false);
    const wotc = useWotcComparison(comparisonSet);

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
    const compareLabel = comparison && comparisonSet ? `WOTC ${comparisonSet}` : null;

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
        };
    }, [filteredSnapshots, comparison]);

    const averages = buildAverages(filteredSnapshots);
    const compareAverages = comparison ? buildAverages(comparison.snapshots) : null;

    if (cards.length === 0) {
        return (
            <div className="flex items-center justify-center py-16 text-[13px] text-(--text-tertiary)">
                Add cards to see distribution charts.
            </div>
        );
    }

    const chartProps = { compareLabel };

    return (
        <div className="flex flex-col gap-6 p-4">
            <div className="flex flex-wrap items-end justify-between gap-3">
                <SubsetFilterBar value={subsetFilter} onChange={setSubsetFilter} />
                <FormDropdown
                    label="Compare to WOTC"
                    className="min-w-44"
                    options={COMPARISON_OPTIONS}
                    selectedOption={comparisonSet ?? NO_COMPARISON}
                    onChange={value => setComparisonSet(value === NO_COMPARISON ? null : value as WotcBaseSet)}
                />
            </div>

            {wotc.loading && (
                <div className="h-4 w-64 rounded bg-(--divider) animate-pulse" />
            )}
            {wotc.error && (
                <div className="text-[12px] text-red-400">{wotc.error}</div>
            )}
            {compareLabel && comparison && (
                <div className="flex flex-col gap-1 text-[11px]">
                    <div className="flex flex-wrap gap-4">
                        <LegendEntry color={CHART_ACCENT} label={`This set (${pluralizeCards(filteredSnapshots.length)})`} />
                        <LegendEntry color={COMPARE_ACCENT} label={`${compareLabel} (${pluralizeCards(comparison.snapshots.length)})`} />
                    </div>
                    <span className="text-(--text-tertiary)">
                        {compareLabel} counts are scaled to this set's size.
                    </span>
                </div>
            )}

            <div className="flex flex-wrap gap-3">
                <StatTile label={subsetFilter === 'all' ? 'Cards' : 'Cards in Subset'} value={filteredSnapshots.length} />
                <StatTile label="Avg PTS" value={averages.points} compareValue={compareAverages?.points} />
                <StatTile label="Avg OnBase" value={averages.onBase} compareValue={compareAverages?.onBase} />
                <StatTile label="Avg Control" value={averages.control} compareValue={compareAverages?.control} />
                <StatTile label="Avg Speed" value={averages.speed} compareValue={compareAverages?.speed} />
                <StatTile label="Avg IP" value={averages.ip} compareValue={compareAverages?.ip} />
            </div>

            {filteredSnapshots.length === 0 ? (
                <p className="text-[13px] text-(--text-tertiary) py-8 text-center">No cards match this subset.</p>
            ) : (
                <>
                    <Section title="Position Group">
                        <HorizontalBarChart data={breakdowns.parentPosition} emptyMessage="No data yet." {...chartProps} />
                    </Section>

                    <Section title="Points Distribution">
                        <VerticalBarChart data={breakdowns.points} emptyMessage="No point data yet." {...chartProps} />
                    </Section>

                    <Section
                        title="Command (Control / On-Base)"
                        action={<FormEnabler label="Include Outs" isEnabled={commandIncludesOuts} onChange={enabled => setCommandIncludesOuts(!enabled)} />}
                    >
                        <VerticalBarChart
                            data={commandIncludesOuts ? breakdowns.commandOuts : breakdowns.command}
                            emptyMessage="No command data yet."
                            scrollable={commandIncludesOuts}
                            {...chartProps}
                        />
                    </Section>

                    <Section title="Position Breakdown">
                        <HorizontalBarChart data={breakdowns.position} emptyMessage="No position data yet." {...chartProps} />
                    </Section>

                    <Section title="Teams">
                        <VerticalBarChart data={breakdowns.team} emptyMessage="No team data yet." scrollable {...chartProps} />
                    </Section>

                    <Section title="Speed">
                        <VerticalBarChart data={breakdowns.speed} emptyMessage="No hitters with speed yet." {...chartProps} />
                    </Section>

                    <Section title="IP">
                        <VerticalBarChart data={breakdowns.ip} emptyMessage="No pitchers yet." {...chartProps} />
                    </Section>

                    <Section title="Defense">
                        <DefensePositionCharts data={breakdowns.defense} emptyMessage="No defensive ratings yet." {...chartProps} />
                    </Section>
                </>
            )}
        </div>
    );
}
