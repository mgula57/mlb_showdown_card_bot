import { useMemo, useState } from 'react';
import type { AdminPeriod, AdminUserDetail, AdminUsers, FeatureArea } from '../../api/adminMetrics';
import { KpiTile } from '../team_builder/sim/KpiTile';
import { SectionCard } from '../team_builder/sim/SectionCard';
import { RetryableError } from '../shared/RetryableError';
import { EmptyState } from '../shared/EmptyState';
import { Heading } from '../shared/Heading';
import { Plate } from '../shared/Plate';
import BackButton from '../shared/BackButton';
import FormInput from '../customs/FormInput';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';
import { formatShortDate, relativeTime } from '../../functions/formatters';
import { AdminTabSkeleton, ColumnHeader, DailyChart, SERIES_COLORS } from './AdminCharts';
import { formatCount, humanizeLabel } from './adminFormat';
import { useAdminMetrics } from './useAdminMetrics';

const AREA_ORDER: FeatureArea[] = ['Site', 'Cards', 'Release Builder', 'Teams & Sims', 'Community'];

const formatWhen = (iso: string | null) => (iso ? relativeTime(iso) : '–');

/** Every account, most active in the period first; picking one opens its detail. */
export function UsersTab({ days, refreshKey, selectedUserId, onSelectUser }: {
    days: AdminPeriod;
    refreshKey: number;
    selectedUserId: string | null;
    onSelectUser: (userId: string | null) => void;
}) {
    if (selectedUserId) {
        return <UserDetail userId={selectedUserId} days={days} refreshKey={refreshKey} onBack={() => onSelectUser(null)} />;
    }
    return <UserList days={days} refreshKey={refreshKey} onSelectUser={onSelectUser} />;
}

function UserList({ days, refreshKey, onSelectUser }: { days: AdminPeriod; refreshKey: number; onSelectUser: (userId: string) => void }) {
    const { data, error, retry } = useAdminMetrics<AdminUsers>('users', days, refreshKey);
    const [query, setQuery] = useState('');

    const users = useMemo(() => {
        const q = query.trim().toLowerCase();
        if (!data) return [];
        if (!q) return data.users;
        return data.users.filter(u => [u.email, u.username, u.user_id].some(v => v?.toLowerCase().includes(q)));
    }, [data, query]);

    if (error) return <RetryableError onRetry={retry}>{error}</RetryableError>;
    if (!data) return <AdminTabSkeleton tiles={0} />;

    const activeCount = data.users.filter(u => u.actions > 0).length;

    return (
        <SectionCard title="Accounts" count={data.users.length}>
            <div className="flex flex-wrap items-end justify-between gap-2">
                <FormInput label="Search" value={query} onChange={v => setQuery(v ?? '')} isClearable placeholder="Email, username or id" className="w-full sm:w-72" />
                <p className="text-[12px] text-(--text-tertiary)">{formatCount(activeCount)} active in the last {days} days</p>
            </div>
            {users.length === 0 ? (
                <EmptyState size="inline">No accounts match “{query}”.</EmptyState>
            ) : (
                <div className="overflow-x-auto -mx-3 px-3">
                    <table className="w-full text-[12px] tabular-nums">
                        <thead>
                            <tr className="border-b border-(--divider)">
                                <ColumnHeader>Account</ColumnHeader>
                                <ColumnHeader>Sign-in</ColumnHeader>
                                <ColumnHeader align="right">Joined</ColumnHeader>
                                <ColumnHeader align="right">Last sign-in</ColumnHeader>
                                <ColumnHeader align="right">Last active</ColumnHeader>
                                <ColumnHeader align="right">Actions</ColumnHeader>
                                <ColumnHeader align="right">Builds</ColumnHeader>
                                <ColumnHeader align="right">Features</ColumnHeader>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.user_id} onClick={() => onSelectUser(u.user_id)}
                                    className="border-b border-(--divider) last:border-b-0 cursor-pointer hover:bg-(--background-tertiary)">
                                    <td className="px-2 py-1.5">
                                        <span className="block text-(--text-primary) break-all">{u.email ?? u.user_id}</span>
                                        {u.username && <span className="block text-(--text-tertiary)">@{u.username}</span>}
                                    </td>
                                    <td className="px-2 py-1.5 text-(--text-secondary)">{u.provider ? humanizeLabel(u.provider) : '–'}</td>
                                    <td className="px-2 py-1.5 text-right whitespace-nowrap text-(--text-secondary)">{formatShortDate(u.created_at)}</td>
                                    <td className="px-2 py-1.5 text-right whitespace-nowrap text-(--text-secondary)">{formatWhen(u.last_sign_in_at)}</td>
                                    <td className="px-2 py-1.5 text-right whitespace-nowrap text-(--text-secondary)">{formatWhen(u.last_active_at)}</td>
                                    <td className="px-2 py-1.5 text-right font-semibold text-(--text-primary)">{u.actions ? formatCount(u.actions) : '–'}</td>
                                    <td className="px-2 py-1.5 text-right text-(--text-primary)">{u.builds ? formatCount(u.builds) : '–'}</td>
                                    <td className="px-2 py-1.5 text-right text-(--text-secondary)">{u.features_used || '–'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </SectionCard>
    );
}

function UserDetail({ userId, days, refreshKey, onBack }: { userId: string; days: AdminPeriod; refreshKey: number; onBack: () => void }) {
    const { data, error, retry } = useAdminMetrics<AdminUserDetail>(`users/${userId}`, days, refreshKey);

    if (error) return <RetryableError onRetry={retry} actions={<BackButton onBack={onBack} label="All accounts" />}>{error}</RetryableError>;
    if (!data) return <AdminTabSkeleton tiles={6} />;

    const { profile } = data;
    const usedFeatures = data.features.filter(f => f.all_time > 0);
    const periodActions = data.features.reduce((sum, f) => sum + f.period, 0);
    const builds = data.features.find(f => f.key === 'card_builds');
    const lastActive = usedFeatures.reduce<string | null>((latest, f) => (f.last_at && (!latest || f.last_at > latest) ? f.last_at : latest), null);

    return (
        <div className="flex flex-col gap-4">
            <div className="flex flex-wrap items-center gap-3">
                <BackButton onBack={onBack} label="All accounts" />
                <div className="min-w-0">
                    <Heading level="section" className="break-all">{profile.username ? `@${profile.username}` : (profile.email ?? profile.user_id)}</Heading>
                    <p className="flex flex-wrap items-center gap-2 text-[12px] text-(--text-secondary)">
                        {profile.username && <span className="break-all">{profile.email}</span>}
                        {profile.provider && <Plate variant="outline" size="xs">{humanizeLabel(profile.provider)}</Plate>}
                        <span className="font-mono text-[11px] text-(--text-tertiary)">{profile.user_id}</span>
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                <KpiTile label="Joined" value={formatShortDate(profile.created_at)} />
                <KpiTile label="Last sign-in" value={formatWhen(profile.last_sign_in_at)} />
                <KpiTile label="Last active" value={formatWhen(lastActive)} />
                <KpiTile label={`Actions, ${days}d`} value={formatCount(periodActions)} />
                <KpiTile label="Cards built" value={formatCount(builds?.all_time)} info="All time." />
                <KpiTile label="Features used" value={`${usedFeatures.length} of ${data.features.length}`} info="All time." />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <SectionCard title="Actions per day">
                    <DailyChart data={data.daily} series={[{ key: 'actions', label: 'Actions', color: SERIES_COLORS.primary }]} height={180} />
                </SectionCard>
                <SectionCard title="Features">
                    <table className="w-full text-[12px] tabular-nums">
                        <thead>
                            <tr className="border-b border-(--divider)">
                                <ColumnHeader>Feature</ColumnHeader>
                                <ColumnHeader align="right">{`${days}d`}</ColumnHeader>
                                <ColumnHeader align="right">All time</ColumnHeader>
                                <ColumnHeader align="right">First</ColumnHeader>
                                <ColumnHeader align="right">Last</ColumnHeader>
                            </tr>
                        </thead>
                        <tbody>
                            {AREA_ORDER.flatMap(area => usedFeatures.filter(f => f.area === area)).map(f => (
                                <tr key={f.key} className="border-b border-(--divider) last:border-b-0">
                                    <td className="px-2 py-1.5 text-(--text-primary)">{f.label}</td>
                                    <td className="px-2 py-1.5 text-right font-semibold text-(--text-primary)">{f.period ? formatCount(f.period) : '–'}</td>
                                    <td className="px-2 py-1.5 text-right text-(--text-secondary)">{formatCount(f.all_time)}</td>
                                    <td className="px-2 py-1.5 text-right whitespace-nowrap text-(--text-tertiary)">{f.first_at ? formatShortDate(f.first_at) : '–'}</td>
                                    <td className="px-2 py-1.5 text-right whitespace-nowrap text-(--text-secondary)">{formatWhen(f.last_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {usedFeatures.length === 0 && <EmptyState size="inline">No recorded activity yet.</EmptyState>}
                </SectionCard>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <SectionCard title="Recent activity" count={data.timeline.length}>
                    <ol className="flex flex-col max-h-96 overflow-y-auto">
                        {data.timeline.map((event, i) => (
                            <li key={`${event.feature}-${event.at}-${i}`} className="flex items-baseline gap-3 border-b border-(--divider) last:border-b-0 py-1.5 text-[12px]">
                                <span className="w-16 shrink-0 text-right tabular-nums text-(--text-tertiary)" title={new Date(event.at).toLocaleString()}>{relativeTime(event.at)}</span>
                                <span className="min-w-0">
                                    <span className="text-(--text-primary)">{event.action}</span>
                                    {event.detail && <span className="ml-1.5 text-(--text-secondary) break-all">{event.detail}</span>}
                                </span>
                            </li>
                        ))}
                    </ol>
                    {data.timeline.length === 0 && <EmptyState size="inline">No recorded activity yet.</EmptyState>}
                </SectionCard>

                <SectionCard title="Recent card builds" count={data.recent_builds.length}>
                    <div className="overflow-x-auto -mx-3 px-3 max-h-96 overflow-y-auto">
                        <table className="w-full text-[12px] tabular-nums">
                            <thead>
                                <tr className="border-b border-(--divider)">
                                    <ColumnHeader>When</ColumnHeader>
                                    <ColumnHeader>Player</ColumnHeader>
                                    <ColumnHeader>Set</ColumnHeader>
                                    <ColumnHeader>Style</ColumnHeader>
                                </tr>
                            </thead>
                            <tbody>
                                {data.recent_builds.map(b => (
                                    <tr key={b.id} className="border-b border-(--divider) last:border-b-0 align-top">
                                        <td className="px-2 py-1.5 whitespace-nowrap text-(--text-tertiary)" title={`Log id ${b.id}`}>{relativeTime(b.created_on)}</td>
                                        <td className="px-2 py-1.5 text-(--text-primary)">
                                            {b.name} <span className="text-(--text-tertiary)">{b.year}</span>
                                            {b.error && <p className="text-(--red) wrap-break-word" title={b.error}>{b.error_for_user || b.error}</p>}
                                        </td>
                                        <td className="px-2 py-1.5 text-(--text-secondary)">{b.set ?? '–'}</td>
                                        <td className="px-2 py-1.5 text-(--text-secondary)">
                                            {[b.expansion, b.edition !== 'NONE' ? b.edition : null, b.image_parallel !== 'NONE' ? b.image_parallel : null, b.period !== 'REGULAR' ? b.period : null]
                                                .filter(Boolean).map(v => humanizeLabel(String(v))).join(' · ') || '–'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {data.recent_builds.length === 0 && <EmptyState size="inline">No card builds.</EmptyState>}
                </SectionCard>
            </div>

            <p className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Times are this browser's local time. Daily buckets are UTC.</p>
        </div>
    );
}
