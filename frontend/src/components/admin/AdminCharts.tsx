/**
 * Chart and list pieces shared by the admin dashboard tabs. One measure per chart (never a second
 * y-axis), thin marks, a hover tooltip on every chart, and text in text tokens (see the dataviz
 * rules and frontend/DESIGN.md). Chart colors are CSS variables so they follow the theme.
 */
import type { ReactNode } from 'react';
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, type TooltipContentProps } from 'recharts';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';
import { formatCount, formatDay } from './adminFormat';

/** Series colors. `failed` is the status red: failures are a state, not a category. */
export const SERIES_COLORS = {
    primary: 'var(--showdown-blue)',
    failed: 'var(--red)',
} as const;

const AXIS_TICK = { fill: 'var(--tertiary)', fontSize: 10 };

export type ChartSeries = { key: string; label: string; color: string };

function ChartTooltip({ active, payload, series, formatValue }: Pick<TooltipContentProps<number, string>, 'active' | 'payload'> & {
    series: ChartSeries[]; formatValue: (v: number) => string;
}) {
    if (!active || !payload?.length) return null;
    const date = String(payload[0].payload?.date ?? '');
    return (
        <div className="bg-(--background-secondary) border border-(--divider) rounded-card px-2.5 py-1.5 text-[11px] shadow-overlay">
            <p className="font-bold text-(--text-primary)">{formatDay(date)}</p>
            {series.map(s => {
                const entry = payload.find(p => p.dataKey === s.key);
                if (!entry) return null;
                return (
                    <p key={s.key} className="flex items-center gap-1.5 text-(--text-secondary) tabular-nums">
                        <span className="inline-block size-2 rounded-plate" style={{ background: s.color }} />
                        {s.label} <span className="font-semibold text-(--text-primary)">{formatValue(Number(entry.value ?? 0))}</span>
                    </p>
                );
            })}
        </div>
    );
}

function ChartLegend({ series }: { series: ChartSeries[] }) {
    if (series.length < 2) return null;
    return (
        <div className="flex flex-wrap gap-3 text-[11px] text-(--text-secondary)">
            {series.map(s => (
                <span key={s.key} className="flex items-center gap-1.5">
                    <span className="inline-block size-2 rounded-plate" style={{ background: s.color }} />
                    {s.label}
                </span>
            ))}
        </div>
    );
}

type DailyChartProps = {
    data: Record<string, unknown>[];
    series: ChartSeries[];
    /** `bar` stacks the series (counts); `line` is for a rate or a single running measure. */
    kind?: 'bar' | 'line';
    formatValue?: (value: number) => string;
    height?: number;
};

/** One measure per day across the period. */
export function DailyChart({ data, series, kind = 'bar', formatValue = formatCount, height = 200 }: DailyChartProps) {
    const axes = (
        <>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--divider)" vertical={false} />
            <XAxis dataKey="date" tickFormatter={formatDay} tickLine={false} axisLine={{ stroke: 'var(--divider)' }}
                tick={AXIS_TICK} tickMargin={6} minTickGap={24} />
            <YAxis tickFormatter={(v: number) => formatValue(v)} tickLine={false} axisLine={false} tick={AXIS_TICK} width={44} allowDecimals={false} />
            <Tooltip
                cursor={kind === 'bar' ? { fill: 'var(--background-tertiary)' } : { stroke: 'var(--rule-strong)' }}
                content={(props) => <ChartTooltip active={props.active} payload={props.payload} series={series} formatValue={formatValue} />}
            />
        </>
    );
    return (
        <div className="flex flex-col gap-2">
            <ChartLegend series={series} />
            <div style={{ height }}>
                <ResponsiveContainer width="100%" height="100%">
                    {kind === 'bar' ? (
                        <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }} barCategoryGap={2}>
                            {axes}
                            {series.map((s, index) => (
                                <Bar key={s.key} dataKey={s.key} stackId="stack" fill={s.color} isAnimationActive={false}
                                    radius={index === series.length - 1 ? [2, 2, 0, 0] : 0} />
                            ))}
                        </BarChart>
                    ) : (
                        <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                            {axes}
                            {series.map(s => (
                                <Line key={s.key} type="monotone" dataKey={s.key} stroke={s.color} strokeWidth={2}
                                    dot={false} activeDot={{ r: 4 }} isAnimationActive={false} />
                            ))}
                        </LineChart>
                    )}
                </ResponsiveContainer>
            </div>
        </div>
    );
}

/** A tiny trend line with no axes, for a row in a list. */
export function Sparkline({ values, className = '' }: { values: number[]; className?: string }) {
    const data = values.map((value, index) => ({ index, value }));
    return (
        <div className={`h-6 w-24 ${className}`} aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
                    <YAxis hide domain={[0, 'dataMax']} />
                    <Line type="monotone" dataKey="value" stroke={SERIES_COLORS.primary} strokeWidth={1.5} dot={false} isAnimationActive={false} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}

export type BreakdownRow = {
    label: string;
    /** Sets the bar length, relative to the longest row. */
    value: number;
    /** Right-aligned primary readout, defaults to the formatted value. */
    display?: ReactNode;
    /** Tertiary readout after the display (a share or a user count). */
    note?: ReactNode;
    /** A mark beside the label (e.g. a set badge). */
    leading?: ReactNode;
    /** Draws the bar in the status red (failure rates). */
    tone?: 'primary' | 'failed';
    title?: string;
};

/** A ranked list with a thin bar per row: how a total splits across one setting. */
export function BreakdownList({ rows, emptyLabel = 'No data in this period.' }: { rows: BreakdownRow[]; emptyLabel?: string }) {
    if (!rows.length) return <p className="text-[12px] text-(--text-tertiary)">{emptyLabel}</p>;
    const max = Math.max(...rows.map(r => r.value), 0) || 1;
    return (
        <ul className="flex flex-col gap-1.5">
            {rows.map(row => (
                <li key={row.label} className="flex flex-col gap-0.5" title={row.title}>
                    <div className="flex items-baseline justify-between gap-2 text-[12px]">
                        <span className="flex items-center gap-1.5 min-w-0 text-(--text-primary)">
                            {row.leading}
                            <span className="truncate">{row.label}</span>
                        </span>
                        <span className="shrink-0 tabular-nums text-(--text-primary) font-semibold">
                            {row.display ?? formatCount(row.value)}
                            {row.note != null && <span className="ml-1.5 font-normal text-(--text-tertiary)">{row.note}</span>}
                        </span>
                    </div>
                    <div className="h-1 w-full rounded-plate bg-(--background-tertiary)">
                        <div
                            className={`h-1 rounded-plate ${row.tone === 'failed' ? 'bg-(--red)' : 'bg-(--showdown-blue)'}`}
                            style={{ width: `${Math.max((row.value / max) * 100, row.value ? 1 : 0)}%` }}
                        />
                    </div>
                </li>
            ))}
        </ul>
    );
}

/** A small caps column header for hand-built tables. */
export function ColumnHeader({ children, align = 'left' }: { children: ReactNode; align?: 'left' | 'right' }) {
    return (
        <th className={`${CAPS_LABEL_CLASS} text-(--text-tertiary) px-2 py-1.5 ${align === 'right' ? 'text-right' : 'text-left'} whitespace-nowrap`}>
            {children}
        </th>
    );
}

/** Skeleton for a dashboard tab: a KPI row over two chart panels. */
export function AdminTabSkeleton({ tiles = 6 }: { tiles?: number }) {
    return (
        <div className="flex flex-col gap-4 animate-pulse" aria-label="Loading metrics">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                {Array.from({ length: tiles }, (_, i) => (
                    <div key={i} className="h-17 rounded-card border border-(--divider) bg-(--background-secondary)" />
                ))}
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
                {[0, 1].map(i => (
                    <div key={i} className="h-64 rounded-card border border-(--divider) bg-(--background-secondary) p-3">
                        <div className="h-3 w-32 rounded-plate bg-(--background-tertiary)" />
                    </div>
                ))}
            </div>
        </div>
    );
}
