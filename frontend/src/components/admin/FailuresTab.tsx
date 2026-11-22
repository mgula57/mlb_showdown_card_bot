import { Fragment, useState } from 'react';
import { FaChevronDown, FaChevronRight } from 'react-icons/fa6';
import type { AdminFailures, AdminPeriod, FailureDimension } from '../../api/adminMetrics';
import { KpiTile } from '../team_builder/sim/KpiTile';
import { SectionCard } from '../team_builder/sim/SectionCard';
import { RetryableError } from '../shared/RetryableError';
import { EmptyState } from '../shared/EmptyState';
import { Plate } from '../shared/Plate';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';
import { relativeTime, formatShortDate } from '../../functions/formatters';
import { AdminTabSkeleton, BreakdownList, ColumnHeader, DailyChart, SERIES_COLORS } from './AdminCharts';
import { ERROR_STAGE_LABELS, formatCount, formatPct, GENERATION_SOURCE_LABELS, humanizeLabel, ratio } from './adminFormat';
import { useAdminMetrics } from './useAdminMetrics';
import { AccountLink } from './AccountLink';

const BREAKDOWN_TITLES: Record<FailureDimension, string> = {
    set: 'By set',
    period: 'By stats period',
    requested_source: 'By requested source',
    year_bucket: 'By year',
    version: 'By app version',
    generation_source: 'By screen',
};

const bucketLabel = (dimension: FailureDimension, label: string) =>
    dimension === 'generation_source' ? GENERATION_SOURCE_LABELS[label] ?? label : humanizeLabel(label);

/** Card Builder failures: rate over time, errors grouped into one row per bug, where they happen,
 *  and the latest failed builds. */
export function FailuresTab({ days, refreshKey, onOpenUser }: { days: AdminPeriod; refreshKey: number; onOpenUser: (userId: string) => void }) {
    const { data, error, retry } = useAdminMetrics<AdminFailures>('failures', days, refreshKey);
    const [expanded, setExpanded] = useState<string | null>(null);

    if (error) return <RetryableError onRetry={retry}>{error}</RetryableError>;
    if (!data) return <AdminTabSkeleton tiles={4} />;

    const { totals } = data;
    const dailyRate = data.daily.map(d => ({ ...d, rate: ratio(d.failed, d.builds) }));

    return (
        <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                <KpiTile label="Failed builds" value={formatCount(totals.failed)} />
                <KpiTile label="Failure rate" value={formatPct(ratio(totals.failed, totals.builds))} />
                <KpiTile label="Error types" value={formatCount(totals.signatures)} info="Failures grouped by message, with player names, years and numbers stripped out." />
                <KpiTile label="Raw error shown" value={formatPct(ratio(totals.shown_raw, totals.failed))}
                    info="Failures where the user saw the exception text itself instead of a written message. Usually an unhandled bug." />
                <KpiTile label="No response" value={formatCount(totals.client_errors)}
                    info="Builds the browser reported as never getting a response (network errors, server crashes, timeouts). The server has no log row for these." />
            </div>

            <SectionCard title="Failure rate per day">
                <DailyChart data={dailyRate} kind="line" formatValue={formatPct} series={[{ key: 'rate', label: 'Failure rate', color: SERIES_COLORS.failed }]} />
            </SectionCard>

            <SectionCard title="Errors" count={data.groups.length}>
                {data.groups.length === 0 ? (
                    <EmptyState size="panel" title="NO FAILURES.">Every build in this period worked.</EmptyState>
                ) : (
                    <div className="overflow-x-auto -mx-3 px-3">
                        <table className="w-full text-[12px] tabular-nums">
                            <thead>
                                <tr className="border-b border-(--divider)">
                                    <ColumnHeader>Error</ColumnHeader>
                                    <ColumnHeader align="right">Failures</ColumnHeader>
                                    <ColumnHeader align="right">Accounts</ColumnHeader>
                                    <ColumnHeader align="right">Anonymous</ColumnHeader>
                                    <ColumnHeader align="right">Last seen</ColumnHeader>
                                </tr>
                            </thead>
                            <tbody>
                                {data.groups.map(group => {
                                    const isOpen = expanded === group.signature;
                                    return (
                                        <Fragment key={group.signature}>
                                            <tr
                                                className="border-b border-(--divider) cursor-pointer hover:bg-(--background-tertiary)"
                                                onClick={() => setExpanded(isOpen ? null : group.signature)}
                                            >
                                                <td className="px-2 py-1.5 text-(--text-primary)">
                                                    <span className="flex items-start gap-1.5">
                                                        {isOpen ? <FaChevronDown className="mt-0.5 shrink-0 text-[10px]" /> : <FaChevronRight className="mt-0.5 shrink-0 text-[10px]" />}
                                                        <span className="min-w-0 wrap-break-word">{group.signature}</span>
                                                        {group.shown_raw > 0 && <Plate variant="red" size="xs" className="shrink-0" title="Users saw the raw error text">Raw</Plate>}
                                                    </span>
                                                </td>
                                                <td className="px-2 py-1.5 text-right font-semibold text-(--text-primary)">{formatCount(group.count)}</td>
                                                <td className="px-2 py-1.5 text-right text-(--text-primary)">{formatCount(group.users)}</td>
                                                <td className="px-2 py-1.5 text-right text-(--text-tertiary)">{group.anonymous ? formatCount(group.anonymous) : '–'}</td>
                                                <td className="px-2 py-1.5 text-right text-(--text-secondary) whitespace-nowrap">{relativeTime(group.last_seen)}</td>
                                            </tr>
                                            {isOpen && (
                                                <tr className="border-b border-(--divider) bg-(--background-primary)">
                                                    <td colSpan={5} className="px-3 py-2">
                                                        <dl className="grid gap-x-4 gap-y-2 sm:grid-cols-[auto_1fr] text-[12px]">
                                                            <dt className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Logged error</dt>
                                                            <dd className="font-mono text-[11px] whitespace-pre-wrap wrap-break-word text-(--text-primary)">{group.sample_error}</dd>
                                                            {group.error_types.length > 0 && (
                                                                <>
                                                                    <dt className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Exception</dt>
                                                                    <dd className="font-mono text-[11px] text-(--text-primary)">{group.error_types.join(', ')}</dd>
                                                                </>
                                                            )}
                                                            {Object.keys(group.stages).length > 0 && (
                                                                <>
                                                                    <dt className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Stage</dt>
                                                                    <dd className="text-(--text-secondary)">
                                                                        {Object.entries(group.stages).map(([stage, count]) => `${ERROR_STAGE_LABELS[stage] ?? stage} (${count})`).join(', ')}
                                                                    </dd>
                                                                </>
                                                            )}
                                                            <dt className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>User saw</dt>
                                                            <dd className="text-(--text-secondary)">{group.sample_error_for_user || '–'}</dd>
                                                            <dt className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Seen</dt>
                                                            <dd className="text-(--text-secondary)">{formatShortDate(group.first_seen)} – {formatShortDate(group.last_seen)}</dd>
                                                            <dt className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Versions</dt>
                                                            <dd className="text-(--text-secondary)">{group.versions.join(', ') || '–'}</dd>
                                                            <dt className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Log ids</dt>
                                                            <dd className="font-mono text-[11px] text-(--text-secondary)">{group.sample_ids.join(', ')}</dd>
                                                            {group.sample_detail && (
                                                                <>
                                                                    <dt className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Latest traceback</dt>
                                                                    <dd>
                                                                        <pre className="max-h-64 overflow-auto rounded-control border border-(--divider) bg-(--background-secondary) p-2 font-mono text-[11px] whitespace-pre text-(--text-primary)">{group.sample_detail}</pre>
                                                                    </dd>
                                                                </>
                                                            )}
                                                        </dl>
                                                    </td>
                                                </tr>
                                            )}
                                        </Fragment>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </SectionCard>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {(Object.keys(BREAKDOWN_TITLES) as FailureDimension[]).map(dimension => (
                    <SectionCard key={dimension} title={BREAKDOWN_TITLES[dimension]} info="Failures in each bucket, with that bucket's failure rate.">
                        <BreakdownList
                            rows={(data.breakdowns[dimension] ?? []).filter(b => b.failed > 0).slice(0, 8).map(b => ({
                                label: bucketLabel(dimension, b.label),
                                value: b.failed,
                                note: `${formatPct(b.failure_rate)} of ${formatCount(b.count)}`,
                                tone: 'failed',
                            }))}
                            emptyLabel="No failures."
                        />
                    </SectionCard>
                ))}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
                <SectionCard title="By build stage" info="The step a build was in when it failed. Recorded for failures since this logging shipped.">
                    <BreakdownList rows={data.by_stage.map(b => ({ label: ERROR_STAGE_LABELS[b.label] ?? b.label, value: b.count, tone: 'failed' }))} />
                </SectionCard>
                <SectionCard title="By exception">
                    <BreakdownList rows={data.by_type.map(b => ({ label: b.label, value: b.count, tone: 'failed' }))} />
                </SectionCard>
            </div>

            {data.client_errors.length > 0 && (
                <SectionCard title="Builds with no response" count={data.client_errors.length}>
                    <div className="overflow-x-auto -mx-3 px-3">
                        <table className="w-full text-[12px] tabular-nums">
                            <thead>
                                <tr className="border-b border-(--divider)">
                                    <ColumnHeader>When</ColumnHeader>
                                    <ColumnHeader>Screen</ColumnHeader>
                                    <ColumnHeader>Account</ColumnHeader>
                                    <ColumnHeader>Message</ColumnHeader>
                                </tr>
                            </thead>
                            <tbody>
                                {data.client_errors.map((row, i) => (
                                    <tr key={`${row.created_at}-${i}`} className="border-b border-(--divider) last:border-b-0 align-top">
                                        <td className="px-2 py-1.5 whitespace-nowrap text-(--text-secondary)">{relativeTime(row.created_at)}</td>
                                        <td className="px-2 py-1.5 text-(--text-secondary)">{row.generation_source ? GENERATION_SOURCE_LABELS[row.generation_source] ?? row.generation_source : '–'}</td>
                                        <td className="px-2 py-1.5"><AccountLink userId={row.user_id} label={row.email} onOpen={onOpenUser} /></td>
                                        <td className="px-2 py-1.5 text-(--text-secondary) wrap-break-word">{row.message}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </SectionCard>
            )}

            <SectionCard title="Latest failed builds" count={data.recent.length}>
                <div className="overflow-x-auto -mx-3 px-3">
                    <table className="w-full text-[12px] tabular-nums">
                        <thead>
                            <tr className="border-b border-(--divider)">
                                <ColumnHeader>When</ColumnHeader>
                                <ColumnHeader>Player</ColumnHeader>
                                <ColumnHeader>Set</ColumnHeader>
                                <ColumnHeader>Period</ColumnHeader>
                                <ColumnHeader>Stage</ColumnHeader>
                                <ColumnHeader>Account</ColumnHeader>
                                <ColumnHeader>Error</ColumnHeader>
                            </tr>
                        </thead>
                        <tbody>
                            {data.recent.map(row => (
                                <tr key={row.id} className="border-b border-(--divider) last:border-b-0 align-top">
                                    <td className="px-2 py-1.5 whitespace-nowrap text-(--text-secondary)" title={`Log id ${row.id}`}>{relativeTime(row.created_on)}</td>
                                    <td className="px-2 py-1.5 whitespace-nowrap text-(--text-primary)">{row.name} <span className="text-(--text-tertiary)">{row.year}</span></td>
                                    <td className="px-2 py-1.5 text-(--text-secondary)">{row.set ?? '–'}</td>
                                    <td className="px-2 py-1.5 text-(--text-secondary)">{row.period ? humanizeLabel(row.period) : '–'}</td>
                                    <td className="px-2 py-1.5 whitespace-nowrap text-(--text-secondary)">{row.error_stage ? ERROR_STAGE_LABELS[row.error_stage] ?? row.error_stage : '–'}</td>
                                    <td className="px-2 py-1.5"><AccountLink userId={row.user_id} label={row.email} onOpen={onOpenUser} /></td>
                                    <td className="px-2 py-1.5 text-(--text-secondary) min-w-64 wrap-break-word" title={row.error ?? undefined}>{row.error}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </SectionCard>
        </div>
    );
}
