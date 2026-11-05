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
import { SEASON_STATUS_LABEL } from './leagueUi';
import { Heading } from '../shared/Heading';
import { InlineError } from '../shared/InlineError';
import { EmptyState } from '../shared/EmptyState';
import { PinstripeBackdrop } from '../shared/PinstripeBackdrop';
import { buttonClass } from '../shared/buttonStyles';
import { LeagueDetail, type LeagueTab } from './LeagueDetail';
import { NewLeagueModal } from './NewLeagueModal';
import { JoinLeagueModal } from './JoinLeagueModal';
import { DraftBigBoard } from './draft/DraftBigBoard';

const LEAGUE_TABS: LeagueTab[] = ['members', 'season', 'history'];
const px = 'px-4 sm:px-8';
const TOUCH_TARGET = 'max-sm:min-h-11';

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
                <SignInPrompt icon={<FaTrophy />} title="Start a league with friends." message="Draft teams from a Release Builder card pool, then play out seasons together." />
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
        <div className="@container w-full relative isolate">
            <PinstripeBackdrop heightClass="h-72" />
            <div className="flex flex-col gap-6 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
                <div className={`flex items-center justify-between gap-3 ${px}`}>
                    <div className="min-w-0">
                        <Heading level="page">Leagues</Heading>
                        <p className="text-[13px] text-(--text-secondary)">Draft a team with friends, then play out seasons together</p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                        <button type="button" onClick={() => setShowJoin(true)} className={buttonClass('secondary', 'sm', TOUCH_TARGET)}>
                            <FaRightToBracket className="text-[11px]" /> Join
                        </button>
                        <button type="button" onClick={() => setShowCreate(true)} className={buttonClass('primary', 'sm', TOUCH_TARGET)}>
                            <FaPlus className="text-[10px]" /> <span>New<span className="hidden sm:inline"> league</span></span>
                        </button>
                    </div>
                </div>

                {error && <div className={px}><InlineError size="md">{error}</InlineError></div>}

                <section className={px}>
                    <Heading level="section" as="h2" className="mb-3">My Leagues</Heading>
                    {!leagues ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                            {Array.from({ length: 3 }, (_, i) => <LeagueTileSkeleton key={i} />)}
                        </div>
                    ) : leagues.length === 0 ? (
                        <EmptyState
                            size="panel"
                            title="No leagues yet."
                            action={
                                <button type="button" onClick={() => setShowCreate(true)} className={buttonClass('primary', 'md')}>
                                    <FaPlus className="text-[10px]" /> New league
                                </button>
                            }
                        >
                            Start one, or join with a code from a friend.
                        </EmptyState>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                            {leagues.map(league => (
                                <button
                                    key={league.league_id}
                                    type="button"
                                    onClick={() => navigate(`/leagues/${league.league_id}`)}
                                    className="flex flex-col gap-1 min-w-0 rounded-card border border-(--divider) bg-(--background-secondary) hover:border-(--rule-strong) transition-colors px-4 py-3 text-left cursor-pointer"
                                >
                                    <Heading level="panel" as="div" fit>{league.name}</Heading>
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

/** Placeholder shaped like a league tile: name, status line, meta line. */
function LeagueTileSkeleton() {
    return (
        <div aria-hidden className="flex flex-col gap-2 rounded-card border border-(--divider) px-4 py-3 animate-pulse">
            <div className="h-4 w-40 rounded-plate bg-(--background-tertiary)" />
            <div className="h-3 w-32 rounded-plate bg-(--background-tertiary)" />
            <div className="h-2.5 w-44 rounded-plate bg-(--background-tertiary)" />
        </div>
    );
}
