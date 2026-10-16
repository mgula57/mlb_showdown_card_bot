/**
 * @fileoverview Leagues page - the user's leagues, creating and joining one, and each league's
 * page. URL shape:
 *   /leagues                         list
 *   /leagues/join/:code              list + the join modal, prefilled (an invite link)
 *   /leagues/:id[/members|season|history]
 *   /leagues/:id/draft               the full-screen draft room
 *   /leagues/:id/seasons/:n          a past season's results
 *   /leagues/:id/board               the TV Big Board for the current draft
 */

import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FaPlus, FaRightToBracket, FaTrophy } from 'react-icons/fa6';
import { useAuth } from '../auth/AuthContext';
import { SignInPrompt } from '../shared/SignInPrompt';
import { fetchMyLeagues, type LeagueListItem, type LeagueState } from '../../api/leagues';
import { usePolling } from '../../hooks/usePolling';
import { ERROR_BOX_CLASS, PRIMARY_BUTTON_CLASS, SECONDARY_BUTTON_CLASS, SECTION_LABEL_CLASS, SEASON_STATUS_LABEL } from './leagueUi';
import { LeagueDetail, type LeagueTab } from './LeagueDetail';
import { NewLeagueModal } from './NewLeagueModal';
import { JoinLeagueModal } from './JoinLeagueModal';
import { DraftBigBoard } from './draft/DraftBigBoard';

const LEAGUE_TABS: LeagueTab[] = ['members', 'season', 'history'];
const px = 'px-4 sm:px-8';

type Route =
    | { kind: 'list'; joinCode: string | null }
    | { kind: 'league'; leagueId: string; tab: LeagueTab | null; pastSeasonNumber: number | null; isDraftOpen: boolean }
    | { kind: 'board'; leagueId: string };

function parseRoute(pathname: string): Route {
    const [, root, first, second, third] = pathname.split('/');
    if (root !== 'leagues' || !first) return { kind: 'list', joinCode: null };
    if (first === 'join') return { kind: 'list', joinCode: second ?? null };
    if (second === 'board') return { kind: 'board', leagueId: first };
    if (second === 'seasons' && third && /^\d+$/.test(third)) return { kind: 'league', leagueId: first, tab: null, pastSeasonNumber: Number(third), isDraftOpen: false };
    const tab = LEAGUE_TABS.includes(second as LeagueTab) ? second as LeagueTab : null;
    return { kind: 'league', leagueId: first, tab, pastSeasonNumber: null, isDraftOpen: second === 'draft' };
}

export default function Leagues() {
    const { session, loading: authLoading } = useAuth();
    const token = session?.access_token;
    const userId = session?.user?.id;
    const location = useLocation();
    const navigate = useNavigate();
    const route = location.pathname.startsWith('/leagues') ? parseRoute(location.pathname) : { kind: 'list' as const, joinCode: null };
    const [showCreate, setShowCreate] = useState(false);
    const [showJoin, setShowJoin] = useState(false);

    const onList = route.kind === 'list';
    const { data: leagues, error, refresh } = usePolling<LeagueListItem[]>(
        () => (token ? fetchMyLeagues(token) : Promise.resolve([])),
        null,
        [!!token, onList],
    );

    function openLeague(state: LeagueState) {
        setShowCreate(false);
        setShowJoin(false);
        refresh();
        navigate(`/leagues/${state.league.league_id}`);
    }

    if (authLoading) return null;
    if (!token) {
        return (
            <div className={`py-10 ${px}`}>
                <SignInPrompt icon={<FaTrophy />} title="Sign in to play in leagues" message="Draft a team with friends from a Release Builder card pool, then play out seasons together." />
            </div>
        );
    }

    if (route.kind === 'board') {
        return <DraftBigBoard leagueId={route.leagueId} token={token} onExit={() => navigate(`/leagues/${route.leagueId}/draft`)} />;
    }

    if (route.kind === 'league') {
        return (
            <LeagueDetail
                key={route.leagueId}
                leagueId={route.leagueId}
                tab={route.tab}
                pastSeasonNumber={route.pastSeasonNumber}
                isDraftOpen={route.isDraftOpen}
                token={token}
                userId={userId}
                onNavigate={(path, replace) => navigate(path, { replace })}
                onBack={() => navigate('/leagues')}
            />
        );
    }

    const joinCode = route.joinCode;
    return (
        <div className="@container w-full">
            <div className="flex flex-col gap-6 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
                <div className={`flex items-center justify-between gap-3 ${px}`}>
                    <div>
                        <h1 className="text-[20px] font-black text-(--text-primary)">Leagues</h1>
                        <p className="text-[13px] text-(--text-secondary)">Draft a team with friends, then play out seasons together</p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                        <button type="button" onClick={() => setShowJoin(true)} className={SECONDARY_BUTTON_CLASS}>
                            <FaRightToBracket className="text-[11px]" /> Join
                        </button>
                        <button type="button" onClick={() => setShowCreate(true)} className={PRIMARY_BUTTON_CLASS}>
                            <FaPlus className="text-[10px]" /> New <span className="hidden sm:inline">League</span>
                        </button>
                    </div>
                </div>

                {error && <div className={px}><div className={ERROR_BOX_CLASS}>{error}</div></div>}

                <section className={px}>
                    <div className={`${SECTION_LABEL_CLASS} mb-2`}>My Leagues</div>
                    {!leagues ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                            {Array.from({ length: 3 }, (_, i) => <div key={i} className="h-24 rounded-xl bg-(--background-secondary) animate-pulse" />)}
                        </div>
                    ) : leagues.length === 0 ? (
                        <p className="text-[13px] text-(--text-tertiary) py-4">
                            You're not in any leagues yet. Start one, or join with a code from a friend.
                        </p>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                            {leagues.map(league => (
                                <button
                                    key={league.league_id}
                                    type="button"
                                    onClick={() => navigate(`/leagues/${league.league_id}`)}
                                    className="flex flex-col gap-1 rounded-xl border border-(--divider) bg-(--background-secondary) hover:bg-(--background-tertiary) transition-colors px-4 py-3 text-left cursor-pointer"
                                >
                                    <div className="text-[15px] font-black text-(--text-primary) truncate">{league.name}</div>
                                    <div className="text-[12px] text-(--text-secondary)">
                                        {league.current_season_number
                                            ? `Season ${league.current_season_number} · ${SEASON_STATUS_LABEL[league.current_season_status!]}`
                                            : 'Waiting for the draft'}
                                    </div>
                                    <div className="text-[11px] text-(--text-tertiary)">
                                        Set {league.showdown_set} · {league.member_count}/{league.settings.team_count} teams
                                        {league.commissioner_user_id === userId ? ' · Commissioner' : ''}
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </section>
            </div>

            {showCreate && <NewLeagueModal token={token} onCreated={openLeague} onClose={() => setShowCreate(false)} />}
            {(showJoin || joinCode) && (
                <JoinLeagueModal
                    token={token}
                    initialCode={joinCode ?? ''}
                    onJoined={openLeague}
                    onClose={() => { setShowJoin(false); if (joinCode) navigate('/leagues', { replace: true }); }}
                />
            )}
        </div>
    );
}
