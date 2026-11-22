import { Fragment } from 'react';
import type { AdminOverview, AdminPeriod, FeatureArea } from '../../api/adminMetrics';
import { KpiTile } from '../team_builder/sim/KpiTile';
import { SectionCard } from '../team_builder/sim/SectionCard';
import { RetryableError } from '../shared/RetryableError';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';
import { AdminTabSkeleton, ColumnHeader, DailyChart, SERIES_COLORS } from './AdminCharts';
import { formatCount, formatPct, periodComparison, ratio, rateComparison } from './adminFormat';
import { useAdminMetrics } from './useAdminMetrics';
import { VisitorsSection } from './VisitorsSection';

const FEATURE_AREAS: FeatureArea[] = ['Site', 'Cards', 'Release Builder', 'Teams & Sims', 'Community'];

function ChangeCell({ current, previous }: { current: number; previous: number }) {
    const comparison = periodComparison(current, previous);
    const tone = comparison.direction === 'flat' ? 'text-(--text-tertiary)' : comparison.isGood ? 'text-(--green)' : 'text-(--red)';
    return <span className={`text-[11px] font-semibold ${tone}`}>{comparison.label.replace(' vs prev', '')}</span>;
}

/** Headline numbers, daily activity and usage per feature. */
export function OverviewTab({ days, refreshKey }: { days: AdminPeriod; refreshKey: number }) {
    const { data, error, retry } =useAdminMetrics<AdminOverview>('overview', days, refreshKey);

    if (error) return <RetryableError onRetry={retry}>{error}</RetryableError>;
    if (!data) return <AdminTabSkeleton tiles={8} />;

    const { builds: b, accounts: a } = data;
    const failureRate = ratio(b.failed, b.builds);
    const previousFailureRate = ratio(b.previous_failed, b.previous_builds);
    const anonymousShare = ratio(b.anonymous_builds, b.builds);
    const previousAnonymousShare = ratio(b.previous_anonymous_builds, b.previous_builds);
    const successData = data.daily.map(d => ({ ...d, succeeded: d.builds - d.failed }));

    return (
        <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
                <KpiTile label="Cards built" value={formatCount(b.builds)} comparison={periodComparison(b.builds, b.previous_builds)} />
                <KpiTile label="Failure rate" value={formatPct(failureRate)} comparison={rateComparison(failureRate, previousFailureRate, false)} />
                <KpiTile label="Signed-in builders" value={formatCount(b.signed_in_builders)} comparison={periodComparison(b.signed_in_builders, b.previous_signed_in_builders)} />
                <KpiTile label="Anonymous builds" value={formatPct(anonymousShare)} info="Share of builds with no signed-in account. Anonymous visitors can't be told apart yet."
                    comparison={rateComparison(anonymousShare, previousAnonymousShare, false)} />
                <KpiTile label="Active accounts" value={formatCount(a.active_accounts)} info="Accounts that did anything the app records (built, searched, opened a card, created a team or release, ran a sim, commented, liked) in the period."
                    comparison={periodComparison(a.active_accounts, a.previous_active_accounts)} />
                <KpiTile label="Signups" value={formatCount(a.signups)} comparison={periodComparison(a.signups, a.previous_signups)} />
                <KpiTile label="Signed in" value={formatCount(a.signed_in)} info="Accounts whose most recent sign-in falls in this period. Supabase keeps only the latest sign-in, so there's no previous-period comparison." />
                <KpiTile label="Accounts" value={formatCount(a.total_accounts)} />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <SectionCard title="Cards built per day">
                    <DailyChart
                        data={successData}
                        series={[
                            { key: 'succeeded', label: 'Built', color: SERIES_COLORS.primary },
                            { key: 'failed', label: 'Failed', color: SERIES_COLORS.failed },
                        ]}
                    />
                </SectionCard>
                <SectionCard title="Active accounts per day" info="Distinct signed-in accounts with any recorded action that day (UTC).">
                    <DailyChart data={data.daily} kind="line" series={[{ key: 'active_accounts', label: 'Active accounts', color: SERIES_COLORS.primary }]} />
                </SectionCard>
                <SectionCard title="Signups per day">
                    <DailyChart data={data.daily} series={[{ key: 'signups', label: 'Signups', color: SERIES_COLORS.primary }]} height={160} />
                </SectionCard>
                <SectionCard title="Anonymous builds per day">
                    <DailyChart data={data.daily} series={[{ key: 'anonymous_builds', label: 'Anonymous builds', color: SERIES_COLORS.primary }]} height={160} />
                </SectionCard>
            </div>

            <VisitorsSection visitors={data.visitors} />

            <SectionCard title="Usage by feature" info="Actions are rows each feature records. Accounts are distinct signed-in users. Changes compare with the previous period of the same length.">
                <div className="overflow-x-auto -mx-3 px-3">
                    <table className="w-full text-[12px] tabular-nums">
                        <thead>
                            <tr className="border-b border-(--divider)">
                                <ColumnHeader>Feature</ColumnHeader>
                                <ColumnHeader align="right">Actions</ColumnHeader>
                                <ColumnHeader align="right">Change</ColumnHeader>
                                <ColumnHeader align="right">Accounts</ColumnHeader>
                                <ColumnHeader align="right">Change</ColumnHeader>
                                <ColumnHeader align="right">Anonymous</ColumnHeader>
                            </tr>
                        </thead>
                        <tbody>
                            {FEATURE_AREAS.map(area => (
                                <Fragment key={area}>
                                    <tr>
                                        <td colSpan={6} className={`${CAPS_LABEL_CLASS} text-(--text-tertiary) px-2 pt-3 pb-1`}>{area}</td>
                                    </tr>
                                    {data.features.filter(f => f.area === area).map(f => (
                                        <tr key={f.key} className="border-b border-(--divider) last:border-b-0">
                                            <td className="px-2 py-1.5 text-(--text-primary)">{f.label}</td>
                                            <td className="px-2 py-1.5 text-right font-semibold text-(--text-primary)">{formatCount(f.actions)}</td>
                                            <td className="px-2 py-1.5 text-right"><ChangeCell current={f.actions ?? 0} previous={f.previous_actions ?? 0} /></td>
                                            <td className="px-2 py-1.5 text-right text-(--text-primary)">{formatCount(f.users)}</td>
                                            <td className="px-2 py-1.5 text-right"><ChangeCell current={f.users ?? 0} previous={f.previous_users ?? 0} /></td>
                                            <td className="px-2 py-1.5 text-right text-(--text-tertiary)">{f.anonymous_actions ? formatCount(f.anonymous_actions) : '–'}</td>
                                        </tr>
                                    ))}
                                </Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>
            </SectionCard>
        </div>
    );
}
