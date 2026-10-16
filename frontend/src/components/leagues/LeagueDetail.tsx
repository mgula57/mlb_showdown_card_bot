import { useEffect } from 'react';
import { FaClockRotateLeft, FaListOl, FaUsers, FaCalendarDays, FaArrowRightToBracket } from 'react-icons/fa6';
import BackButton from '../shared/BackButton';
import { Tabs, type TabItem } from '../shared/Tabs';
import { fetchLeague, type LeagueState } from '../../api/leagues';
import { usePolling } from '../../hooks/usePolling';
import { ERROR_BOX_CLASS, PRIMARY_BUTTON_CLASS, SECONDARY_BUTTON_CLASS, SEASON_STATUS_LABEL } from './leagueUi';
import { LeagueMembersTab } from './LeagueMembersTab';
import { LeagueHistoryTab } from './LeagueHistoryTab';
import { LeagueDraftScreen } from './draft/LeagueDraftScreen';
import { LeagueSeasonTab } from './season/LeagueSeasonTab';

const POLL_MS = 10000;

export type LeagueTab = 'members' | 'season' | 'history';

type Props = {
    leagueId: string;
    /** Tab from the URL, or null for the default for the league's current status. */
    tab: LeagueTab | null;
    /** A past season opened from History (`/leagues/:id/seasons/:n`). */
    pastSeasonNumber: number | null;
    /** The full-screen draft room is open (`/leagues/:id/draft`). */
    isDraftOpen: boolean;
    token: string;
    userId?: string;
    onNavigate: (path: string, replace?: boolean) => void;
    onBack: () => void;
};

/** One league: header, then Members / Season / History tabs. The draft opens as its own
 *  full-screen page, joined from the header once the commissioner starts it. */
export function LeagueDetail({ leagueId, tab, pastSeasonNumber, isDraftOpen, token, userId, onNavigate, onBack }: Props) {
    const { data: state, setData, error, refresh } = usePolling<LeagueState>(() => fetchLeague(token, leagueId), POLL_MS, [leagueId]);
    const base = `/leagues/${leagueId}`;
    const season = state?.season ?? null;

    // No draft to show until the commissioner starts one
    const hasNoDraft = isDraftOpen && !!state && !season;
    useEffect(() => {
        if (hasNoDraft) onNavigate(base, true);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [hasNoDraft]);

    if (!state) {
        return (
            <div className="flex flex-col gap-4 py-4 px-4 sm:px-8 max-w-4xl lg:max-w-7xl mx-auto w-full">
                <BackButton onBack={onBack} label="Leagues" className="self-start" />
                {error ? <div className={ERROR_BOX_CLASS}>{error}</div> : <LeagueDetailSkeleton />}
            </div>
        );
    }

    const { league, is_commissioner: isCommissioner, my_member_id: myMemberId } = state;

    if (isDraftOpen && season) {
        return (
            <LeagueDraftScreen
                state={state}
                token={token}
                onBack={() => onNavigate(base)}
                onOpenBigBoard={() => onNavigate(`${base}/board`)}
                onComplete={refresh}
            />
        );
    }

    const isDrafting = season?.status === 'drafting';
    const tabs: TabItem<LeagueTab>[] = [
        { id: 'members', label: 'Members', icon: <FaUsers /> },
        ...(season ? [
            { id: 'season' as const, label: 'Season', icon: <FaCalendarDays /> },
            { id: 'history' as const, label: 'History', icon: <FaClockRotateLeft /> },
        ] : []),
    ];
    const defaultTab: LeagueTab = !season || isDrafting ? 'members' : 'season';
    const activeTab = tab && tabs.some(t => t.id === tab) ? tab : defaultTab;

    return (
        <div className="flex flex-col gap-4 py-4 px-4 sm:px-8 max-w-4xl lg:max-w-7xl mx-auto w-full">
            <div className="flex items-start gap-3">
                <BackButton onBack={onBack} label="" />
                <div className="flex-1 min-w-0">
                    <h1 className="text-[20px] font-black text-(--text-primary) truncate">{league.name}</h1>
                    <p className="text-[12px] text-(--text-secondary)">
                        Set {league.showdown_set}
                        {season ? ` · Season ${season.season_number} · ${SEASON_STATUS_LABEL[season.status]}` : ' · Waiting for the draft'}
                        {isCommissioner ? ' · You run this league' : ''}
                    </p>
                </div>
                {/* Joinable once the commissioner starts the draft; the finished board stays viewable */}
                {isDrafting ? (
                    <button type="button" onClick={() => onNavigate(`${base}/draft`)} className={`${PRIMARY_BUTTON_CLASS} shrink-0`}>
                        <FaArrowRightToBracket className="text-[11px]" /> Join Draft
                    </button>
                ) : season && (
                    <button type="button" onClick={() => onNavigate(`${base}/draft`)} className={`${SECONDARY_BUTTON_CLASS} shrink-0`}>
                        <FaListOl className="text-[11px]" /> <span className="hidden sm:inline">Draft</span> Results
                    </button>
                )}
            </div>

            {pastSeasonNumber !== null ? (
                <>
                    <BackButton onBack={() => onNavigate(`${base}/history`)} label="History" className="self-start" />
                    <LeagueSeasonTab
                        key={pastSeasonNumber}
                        league={league}
                        seasonNumber={pastSeasonNumber}
                        token={token}
                        myMemberId={myMemberId}
                        isCommissioner={isCommissioner}
                        readOnly={!season || pastSeasonNumber !== season.season_number}
                        onLeagueChange={refresh}
                    />
                </>
            ) : (
                <>
                    <Tabs<LeagueTab> tabs={tabs} value={activeTab} onChange={id => onNavigate(`${base}/${id}`, true)} />

                    {activeTab === 'members' && (
                        <LeagueMembersTab
                            state={state}
                            token={token}
                            userId={userId}
                            onStateChange={setData}
                            onDraftStarted={async () => { await refresh(); onNavigate(`${base}/draft`); }}
                            onLeft={onBack}
                        />
                    )}
                    {activeTab === 'season' && season && (
                        <LeagueSeasonTab
                            key={season.season_number}
                            league={league}
                            seasonNumber={season.season_number}
                            token={token}
                            myMemberId={myMemberId}
                            isCommissioner={isCommissioner}
                            onLeagueChange={refresh}
                        />
                    )}
                    {activeTab === 'history' && (
                        <LeagueHistoryTab leagueId={leagueId} token={token} onOpenSeason={n => onNavigate(`${base}/seasons/${n}`)} />
                    )}
                </>
            )}
        </div>
    );
}

function LeagueDetailSkeleton() {
    return (
        <div className="flex flex-col gap-4 animate-pulse">
            <div className="h-7 w-64 rounded bg-(--background-secondary)" />
            <div className="h-4 w-48 rounded bg-(--background-secondary)" />
            <div className="h-10 w-full rounded-lg bg-(--background-secondary)" />
            <div className="h-64 w-full rounded-xl bg-(--background-secondary)" />
        </div>
    );
}
