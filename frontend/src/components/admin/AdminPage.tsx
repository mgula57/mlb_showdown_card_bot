/**
 * @fileoverview Admin dashboard (`/admin`): usage across features, accounts and adoption, Card
 * Builder failures and card trends, and per-account activity. Only admins see it (the server
 * gates every route with `require_admin`; this page and its nav item check `useAuth().isAdmin`).
 *
 * The tab, period and selected account live in the URL (`?tab=users&user=<id>&days=30`) so a
 * view can be bookmarked or shared between admins.
 */
import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FaRotate } from 'react-icons/fa6';
import { useAuth } from '../auth/AuthContext';
import { ADMIN_PERIODS, type AdminPeriod } from '../../api/adminMetrics';
import { Heading } from '../shared/Heading';
import { PageSubtitle } from '../shared/PageSubtitle';
import { PinstripeBackdrop } from '../shared/PinstripeBackdrop';
import { SignInPrompt } from '../shared/SignInPrompt';
import { EmptyState } from '../shared/EmptyState';
import { Tabs, type TabItem } from '../shared/Tabs';
import { buttonClass } from '../shared/buttonStyles';
import { choiceClass } from '../shared/choiceStyles';
import { OverviewTab } from './OverviewTab';
import { FailuresTab } from './FailuresTab';
import { CardTrendsTab } from './CardTrendsTab';
import { UsersTab } from './UsersTab';
import { clearAdminMetricsCache } from './useAdminMetrics';

type AdminTab = 'overview' | 'failures' | 'trends' | 'users';

const ADMIN_TABS: TabItem<AdminTab>[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'failures', label: 'Builder Failures', shortLabel: 'Failures' },
    { id: 'trends', label: 'Card Trends', shortLabel: 'Trends' },
    { id: 'users', label: 'Users' },
];

const PERIOD_LABELS: Record<AdminPeriod, string> = { 7: '7D', 30: '30D', 90: '90D', 365: '1Y' };

const PX = 'px-4 sm:px-8';

export default function AdminPage() {
    const { user, isAdmin, loading } = useAuth();
    const [params, setParams] = useSearchParams();
    const [refreshKey, setRefreshKey] = useState(0);

    const tab = (ADMIN_TABS.some(t => t.id === params.get('tab')) ? params.get('tab') : 'overview') as AdminTab;
    const daysParam = Number(params.get('days'));
    const days: AdminPeriod = (ADMIN_PERIODS as readonly number[]).includes(daysParam) ? daysParam as AdminPeriod : 30;
    const selectedUserId = params.get('user');

    const update = (changes: Record<string, string | null>) => {
        setParams(prev => {
            const next = new URLSearchParams(prev);
            for (const [key, value] of Object.entries(changes)) {
                if (value === null) next.delete(key);
                else next.set(key, value);
            }
            return next;
        });
    };
    const openUser = (userId: string | null) => update({ tab: 'users', user: userId });

    if (loading) return null;
    if (!user) {
        return <SignInPrompt title="Sign in to view the admin dashboard." message="The dashboard is for site admins." className="min-h-screen" />;
    }
    if (!isAdmin) {
        return <EmptyState title="ADMINS ONLY." className="min-h-screen">This dashboard is only available to site admins.</EmptyState>;
    }

    return (
        <div className="@container w-full relative isolate">
            <PinstripeBackdrop heightClass="h-72" />
            <div className="flex flex-col gap-4 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
                <div className={`flex flex-wrap items-end justify-between gap-3 ${PX}`}>
                    <div className="min-w-0">
                        <Heading level="page" fit>Admin</Heading>
                        <PageSubtitle>Usage, adoption and Card Builder health</PageSubtitle>
                    </div>
                    <div className="flex flex-wrap items-center gap-1.5">
                        {ADMIN_PERIODS.map(period => (
                            <button key={period} type="button" onClick={() => update({ days: String(period) })}
                                className={choiceClass(period === days, 'sm', 'cursor-pointer')}>
                                {PERIOD_LABELS[period]}
                            </button>
                        ))}
                        <button type="button" onClick={() => { clearAdminMetricsCache(); setRefreshKey(k => k + 1); }} className={buttonClass('secondary', 'sm')} title="Reload without cached numbers">
                            <FaRotate className="text-[11px]" />
                            Refresh
                        </button>
                    </div>
                </div>

                <div className={PX}>
                    <Tabs tabs={ADMIN_TABS} value={tab} onChange={id => update({ tab: id, user: null })} />
                </div>

                <div className={PX}>
                    {tab === 'overview' && <OverviewTab days={days} refreshKey={refreshKey} />}
                    {tab === 'failures' && <FailuresTab days={days} refreshKey={refreshKey} onOpenUser={openUser} />}
                    {tab === 'trends' && <CardTrendsTab days={days} refreshKey={refreshKey} />}
                    {tab === 'users' && <UsersTab days={days} refreshKey={refreshKey} selectedUserId={selectedUserId} onSelectUser={openUser} />}
                </div>
            </div>
        </div>
    );
}
