import { useMemo } from 'react';
import type { AdminCardTrends, AdminPeriod, TrendDimension } from '../../api/adminMetrics';
import type { SelectOption } from '../shared/CustomSelect';
import { KpiTile } from '../team_builder/sim/KpiTile';
import { SectionCard } from '../team_builder/sim/SectionCard';
import { RetryableError } from '../shared/RetryableError';
import { SetBadge } from '../shared/SetBadge';
import { chartVersionOptions, editionOptions, expansionOptions, imageParallelOptions, statNormalizerOptions } from '../customs/cardStyle';
import { AdminTabSkeleton, BreakdownList, ColumnHeader, Sparkline } from './AdminCharts';
import { formatCount, formatPct, GENERATION_SOURCE_LABELS, humanizeLabel, ratio } from './adminFormat';
import { useAdminMetrics } from './useAdminMetrics';

/** Breakdown panels, in display order. `options` reuses the builder's own labels for coded values. */
const TREND_PANELS: { dimension: TrendDimension; title: string; options?: SelectOption[] }[] = [
    { dimension: 'expansion', title: 'Expansion', options: expansionOptions },
    { dimension: 'edition', title: 'Edition', options: editionOptions },
    { dimension: 'image_parallel', title: 'Parallel', options: imageParallelOptions },
    { dimension: 'period', title: 'Stats period' },
    { dimension: 'year_bucket', title: 'Year' },
    { dimension: 'era', title: 'Era' },
    { dimension: 'chart_version', title: 'Chart version', options: chartVersionOptions },
    { dimension: 'stat_normalizer', title: 'Normalizer', options: statNormalizerOptions },
    { dimension: 'image_source', title: 'Image source' },
    { dimension: 'data_source', title: 'Stats loaded from' },
    { dimension: 'league', title: 'League' },
    { dimension: 'generation_source', title: 'Built from',
      options: Object.entries(GENERATION_SOURCE_LABELS).map(([value, label]) => ({ value, label })) },
];

function optionLabel(value: string, options?: SelectOption[]): string {
    const match = options?.find(o => String(o.value) === value);
    return typeof match?.label === 'string' && match.label ? match.label : humanizeLabel(value);
}

/** What people build in the Card Builder: share of successful builds by each setting. */
export function CardTrendsTab({ days, refreshKey }: { days: AdminPeriod; refreshKey: number }) {
    const { data, error, retry } = useAdminMetrics<AdminCardTrends>('card-trends', days, refreshKey);

    // One daily series per set, aligned to the same days, for the sparklines
    const setSeries = useMemo(() => {
        if (!data) return new Map<string, number[]>();
        const dates = [...new Set(data.daily_by_set.map(d => d.date))].sort();
        const index = new Map(dates.map((date, i) => [date, i]));
        const series = new Map<string, number[]>();
        for (const row of data.daily_by_set) {
            const set = row.set ?? 'None';
            if (!series.has(set)) series.set(set, Array(dates.length).fill(0));
            series.get(set)![index.get(row.date)!] = row.count;
        }
        return series;
    }, [data]);

    if (error) return <RetryableError onRetry={retry}>{error}</RetryableError>;
    if (!data) return <AdminTabSkeleton tiles={6} />;

    const { flags } = data;
    const share = (count: number) => formatPct(ratio(count, flags.builds));

    return (
        <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                <KpiTile label="Cards built" value={formatCount(flags.builds)} info="Successful builds only." />
                <KpiTile label="Shuffled" value={share(flags.shuffles)} />
                <KpiTile label="Dark mode" value={share(flags.dark_mode)} />
                <KpiTile label="Bordered" value={share(flags.bordered)} />
                <KpiTile label="Own image" value={share(flags.own_image)} info="Built with an uploaded image or an image link." />
                <KpiTile label="Variable speed" value={share(flags.variable_speed)} info="2000/2001 variable speed, as a share of all builds." />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <SectionCard title="Sets" info="Successful builds per set, with each set's daily trend across the period.">
                    <ul className="flex flex-col gap-2">
                        {data.breakdowns.set.map(bucket => (
                            <li key={bucket.label} className="flex items-center gap-3 text-[12px]">
                                <span className="w-24 shrink-0">
                                    <SetBadge set={bucket.label} size="sm" />
                                </span>
                                <Sparkline values={setSeries.get(bucket.label) ?? []} className="flex-1" />
                                <span className="w-28 shrink-0 text-right tabular-nums font-semibold text-(--text-primary)">
                                    {formatCount(bucket.count)}
                                    <span className="ml-1.5 font-normal text-(--text-tertiary)">{share(bucket.count)}</span>
                                </span>
                            </li>
                        ))}
                    </ul>
                </SectionCard>

                <SectionCard title="Most built players" count={data.top_players.length}>
                    <div className="overflow-x-auto -mx-3 px-3 max-h-80 overflow-y-auto">
                        <table className="w-full text-[12px] tabular-nums">
                            <thead>
                                <tr className="border-b border-(--divider)">
                                    <ColumnHeader>Player</ColumnHeader>
                                    <ColumnHeader align="right">Builds</ColumnHeader>
                                    <ColumnHeader align="right">Accounts</ColumnHeader>
                                    <ColumnHeader align="right">Shuffled</ColumnHeader>
                                </tr>
                            </thead>
                            <tbody>
                                {data.top_players.map(player => (
                                    <tr key={player.bref_id} className="border-b border-(--divider) last:border-b-0">
                                        <td className="px-2 py-1.5 text-(--text-primary)" title={player.bref_id}>{player.name}</td>
                                        <td className="px-2 py-1.5 text-right font-semibold text-(--text-primary)">{formatCount(player.count)}</td>
                                        <td className="px-2 py-1.5 text-right text-(--text-secondary)">{formatCount(player.users)}</td>
                                        <td className="px-2 py-1.5 text-right text-(--text-tertiary)">{player.shuffles ? formatCount(player.shuffles) : '–'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </SectionCard>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {TREND_PANELS.map(({ dimension, title, options }) => (
                    <SectionCard key={dimension} title={title}>
                        <BreakdownList
                            rows={(data.breakdowns[dimension] ?? []).slice(0, 8).map(bucket => ({
                                label: optionLabel(bucket.label, options),
                                value: bucket.count,
                                note: share(bucket.count),
                                title: `${formatCount(bucket.users)} signed-in accounts`,
                            }))}
                        />
                    </SectionCard>
                ))}
            </div>
        </div>
    );
}
