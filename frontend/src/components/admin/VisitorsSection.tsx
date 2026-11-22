import type { AdminVisitors } from '../../api/adminMetrics';
import { KpiTile } from '../team_builder/sim/KpiTile';
import { SectionCard } from '../team_builder/sim/SectionCard';
import { EmptyState } from '../shared/EmptyState';
import { Eyebrow } from '../shared/Eyebrow';
import { formatShortDate } from '../../functions/formatters';
import { BreakdownList, DailyChart, SERIES_COLORS } from './AdminCharts';
import { formatCount, formatPct, humanizeLabel, periodComparison, ratio } from './adminFormat';

/** Visitors, sessions, sign-ins and traffic from the event log. Event logging started with the
 *  phase 2 release, so the section says how far back it goes. */
export function VisitorsSection({ visitors }: { visitors: AdminVisitors }) {
    const { totals } = visitors;

    if (!totals.tracked_since) {
        return (
            <SectionCard title="Visitors">
                <EmptyState size="panel" title="NO VISITS YET.">Page views, sessions and sign-ins show up here once event logging is live.</EmptyState>
            </SectionCard>
        );
    }

    return (
        <div className="flex flex-col gap-4">
            <div className="flex items-baseline justify-between gap-2">
                <Eyebrow>Visitors</Eyebrow>
                <p className="text-[12px] text-(--text-tertiary)">Tracked since {formatShortDate(totals.tracked_since)}</p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                <KpiTile label="Visitors" value={formatCount(totals.visitors)} info="Distinct browsers, counted by a random id the app keeps in each browser."
                    comparison={periodComparison(totals.visitors, totals.previous_visitors)} />
                <KpiTile label="Sessions" value={formatCount(totals.sessions)} comparison={periodComparison(totals.sessions, totals.previous_sessions)} />
                <KpiTile label="Sign-ins" value={formatCount(totals.sign_ins)} info="Each sign-in counts once per browser tab session."
                    comparison={periodComparison(totals.sign_ins, totals.previous_sign_ins)} />
                <KpiTile label="Page views" value={formatCount(totals.page_views)} />
                <KpiTile label="Signed in" value={formatPct(ratio(totals.signed_in_visitors, totals.visitors))} info="Share of visitors who were signed in at some point in the period." />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <SectionCard title="Visitors per day">
                    <DailyChart data={visitors.daily} kind="line" series={[{ key: 'visitors', label: 'Visitors', color: SERIES_COLORS.primary }]} />
                </SectionCard>
                <SectionCard title="Sign-ins per day">
                    <DailyChart data={visitors.daily} series={[{ key: 'sign_ins', label: 'Sign-ins', color: SERIES_COLORS.primary }]} />
                </SectionCard>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <SectionCard title="Page views by section">
                    <BreakdownList rows={visitors.sections.map(s => ({
                        label: s.label, value: s.count, note: `${formatCount(s.visitors)} visitors`,
                    }))} />
                </SectionCard>
                <SectionCard title="Sessions by referrer">
                    <BreakdownList rows={visitors.referrers.map(r => ({ label: r.label, value: r.count, note: formatPct(ratio(r.count, totals.sessions)) }))} />
                </SectionCard>
                <SectionCard title="Sessions by device">
                    <BreakdownList rows={visitors.devices.map(d => ({ label: humanizeLabel(d.label), value: d.count, note: formatPct(ratio(d.count, totals.sessions)) }))} />
                </SectionCard>
                <SectionCard title="Sessions by campaign" info="From utm_source and utm_campaign on the link a visit started from.">
                    <BreakdownList rows={visitors.campaigns.map(c => ({ label: c.label, value: c.count }))} />
                </SectionCard>
            </div>
        </div>
    );
}
