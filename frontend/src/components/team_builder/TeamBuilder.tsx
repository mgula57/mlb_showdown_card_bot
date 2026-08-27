import { useState, useEffect, useMemo, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import {
    fetchUserTeams,
    fetchTeam,
    createTeam,
    updateTeam,
    forkTeam,
    type Team,
    type TeamSummary,
    type TeamUpdatePayload,
} from '../../api/userTeams';
import {
    fetchShowdownTeam, fetchAsgShowdownTeam,
    type Season,
} from '../../api/mlbAPI';
import { useSiteSettings } from '../shared/SiteSettingsContext';
import { TeamCard } from './TeamCard';
import { TeamPreviewCard } from './TeamPreviewCard';
import { TeamShelf } from './TeamShelf';
import { TeamDetail } from './TeamDetail';
import { NewTeamModal } from './NewTeamModal';
import { TeamBuilderWelcome } from './TeamBuilderWelcome';
import { CommunityTeams } from './CommunityTeams';
import { HistoricalTeams, asgIdentity, type HistoricalNavState } from './HistoricalTeams';
import { SimSeasonView } from './sim/SimSeasonView';
import { SimulationsTab } from './sim/SimulationsTab';
import { ChallengeDetail } from './sim/ChallengeDetail';
import { Tabs, type TabItem } from '../shared/Tabs';
import { FaPlus, FaSpinner, FaUsers, FaGlobe, FaClockRotateLeft, FaRankingStar } from 'react-icons/fa6';
import type { TeamCreatePayload } from '../../api/userTeams';
import type { ChallengeInstance } from '../../api/sim';
import { CardSource } from '../../types/cardSource';

// A team can be addressed by URL three ways: a saved UUID, a historical MLB team, or an All-Star team.
type TeamRef =
    | { kind: 'saved'; teamId: string }
    | { kind: 'historical'; sportId: number; season: string; teamId: number }
    | { kind: 'asg'; season: string; league: string };

function parseTeamRef(pathname: string): TeamRef | null {
    const parts = pathname.split('/').filter(Boolean);
    if (parts[0] !== 'teams' || !parts[1]) return null;
    if (parts[1] === 'historical' && parts[4] !== undefined) {
        return { kind: 'historical', sportId: Number(parts[2]), season: parts[3], teamId: Number(parts[4]) };
    }
    if (parts[1] === 'asg' && parts[3] !== undefined) {
        return { kind: 'asg', season: parts[2], league: parts[3].toUpperCase() };
    }
    if (parts[1] !== 'historical' && parts[1] !== 'asg' && parts[1] !== 'challenges') {
        return { kind: 'saved', teamId: parts[1] };
    }
    return null;
}

// A running simulation gets its own URL (/teams/:teamId/sim/:jobId) so a refresh mid-run
// reconnects to the job instead of losing it — the job's state lives in Postgres.
function parseSimJobId(pathname: string): string | null {
    const parts = pathname.split('/').filter(Boolean);
    return parts[0] === 'teams' && parts[2] === 'sim' && parts[3] ? parts[3] : null;
}

// A challenge gets its own shareable URL (/teams/challenges/:instanceId), independent of the
// team editor/list state below — landing here bypasses both entirely.
function parseChallengeInstanceId(pathname: string): string | null {
    const parts = pathname.split('/').filter(Boolean);
    return parts[0] === 'teams' && parts[1] === 'challenges' && parts[2] ? parts[2] : null;
}

// =============================================================================
// MARK: - Recent Team Tracking
// =============================================================================

const RECENTLY_VIEWED_KEY = 'showdown_recent_teams';
const MAX_RECENT = 10;

export function trackRecentTeam(teamId: string) {
    try {
        const ids: string[] = JSON.parse(localStorage.getItem(RECENTLY_VIEWED_KEY) ?? '[]');
        const next = [teamId, ...ids.filter(id => id !== teamId)].slice(0, MAX_RECENT);
        localStorage.setItem(RECENTLY_VIEWED_KEY, JSON.stringify(next));
    } catch {}
}

function getRecentTeamIds(): string[] {
    try { return JSON.parse(localStorage.getItem(RECENTLY_VIEWED_KEY) ?? '[]'); }
    catch { return []; }
}

type ViewState =
    | { mode: 'list' }
    | { mode: 'loading' }
    | { mode: 'editor'; team: Team; readOnly: boolean };

type TabId = 'mine' | 'community' | 'historical' | 'simulations';
const ACTIVE_TAB_KEY = 'teams.activeTab';
const TAB_IDS: TabId[] = ['mine', 'community', 'historical', 'simulations'];
// `shortLabel` keeps four tabs readable on a phone; the full label returns at sm.
const TABS: TabItem<TabId>[] = [
    { id: 'mine', label: 'My Teams', shortLabel: 'Mine', icon: <FaUsers /> },
    { id: 'simulations', label: 'Challenges', shortLabel: 'Challenges', icon: <FaRankingStar /> },
    { id: 'community', label: 'Community', shortLabel: 'Community', icon: <FaGlobe /> },
    { id: 'historical', label: 'Historical', shortLabel: 'Historical', icon: <FaClockRotateLeft /> },
];

export default function TeamBuilder() {
    const { session, username } = useAuth();
    const { userShowdownSet } = useSiteSettings();
    const location = useLocation();
    const navigate = useNavigate();
    const token = session?.access_token;

    const [userTeams, setUserTeams] = useState<TeamSummary[]>([]);
    const [view, setView] = useState<ViewState>({ mode: 'list' });
    const [loading, setLoading] = useState(true);
    const [listLoaded, setListLoaded] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    // Set only when "Build from Scratch" was opened from a challenge card - pre-fills the new
    // team's budget/origin tag and, once created, carries the challenge through to the team page.
    const [challengeForNewTeam, setChallengeForNewTeam] = useState<ChallengeInstance | null>(null);
    const [activeTab, setActiveTab] = useState<TabId>(() => {
        const stored = typeof window !== 'undefined' ? window.localStorage.getItem(ACTIVE_TAB_KEY) : null;
        return TAB_IDS.includes(stored as TabId) ? (stored as TabId) : 'mine';
    });

    // UX Spacing
    const px = 'px-4 sm:px-8';

    // Recent teams shelf — recently viewed teams (from localStorage) first, then most recently updated.
    const recentTeamIds = useMemo(getRecentTeamIds, []);
    const recentTeams = useMemo(() => {
        const withPlayers = userTeams.filter(t => t.roster_count > 0);

        if (recentTeamIds.length > 0) {
            const teamById = new Map(withPlayers.map(t => [t.team_id, t]));
            const ordered: TeamSummary[] = [];
            for (const id of recentTeamIds) {
                const t = teamById.get(id);
                if (t) ordered.push(t);
            }
            const inOrdered = new Set(ordered.map(t => t.team_id));
            const rest = withPlayers
                .filter(t => !inOrdered.has(t.team_id))
                .sort((a, b) => (b.updated_at ?? '') > (a.updated_at ?? '') ? 1 : -1);
            return [...ordered, ...rest].slice(0, 6);
        }

        return [...withPlayers]
            .sort((a, b) => (b.updated_at ?? '') > (a.updated_at ?? '') ? 1 : -1)
            .slice(0, 8);
    }, [userTeams, recentTeamIds]);

    // Parse the team addressed by the current URL (saved UUID, historical, or All-Star).
    const teamRef = parseTeamRef(location.pathname);
    const simJobId = parseSimJobId(location.pathname);
    const challengeInstanceId = parseChallengeInstanceId(location.pathname);
    // The team currently resolved into the editor, so we don't re-resolve on re-render. Keyed on
    // the ref rather than the pathname so entering/leaving a sim URL doesn't refetch the team.
    const teamRefKey = teamRef ? JSON.stringify(teamRef) : null;
    const resolvedPathRef = useRef<string | null>(null);

    useEffect(() => {
        window.localStorage.setItem(ACTIVE_TAB_KEY, activeTab);
    }, [activeTab]);

    // Auth change invalidates the cached list
    useEffect(() => { setListLoaded(false); }, [token]);

    // Load the (lightweight) teams list lazily — only when viewing the list, so a direct
    // visit to a team URL opens the team without first loading every team.
    useEffect(() => {
        if (teamRef || challengeInstanceId || listLoaded) return;
        loadTeams();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [location.pathname, listLoaded, token]);

    // When the URL addresses a team, resolve and open it in the full-detail editor. Works for
    // saved teams (DB fetch) as well as synthetic historical / All-Star teams (built on the fly),
    // so every team type gets its own shareable link.
    useEffect(() => {
        if (!teamRef) {
            resolvedPathRef.current = null;
            setView(v => v.mode === 'list' ? v : { mode: 'list' });
            return;
        }
        if (resolvedPathRef.current === teamRefKey && view.mode === 'editor') return;

        setView({ mode: 'loading' });
        resolveTeamRef(teamRef)
            .then(({ team, readOnly }) => {
                resolvedPathRef.current = teamRefKey;
                setView({ mode: 'editor', team, readOnly });
            })
            .catch(() => {
                navigate('/teams', { replace: true });
            });
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [teamRefKey, token, userShowdownSet]);

    // Resolve a URL team ref into a full Team + read-only flag for the editor.
    async function resolveTeamRef(ref: TeamRef): Promise<{ team: Team; readOnly: boolean }> {
        if (ref.kind === 'saved') {
            const team = await fetchTeam(ref.teamId, token ?? undefined);
            const readOnly = !token || team.user_id !== session?.user?.id;
            return { team, readOnly };
        }
        if (ref.kind === 'asg') {
            const team = await fetchAsgShowdownTeam(ref.season, ref.league, 1, userShowdownSet);
            const id = asgIdentity(ref.season, ref.league);
            return {
                team: {
                    ...team,
                    name: id.name,
                    primary_color: id.primary_color || team.primary_color,
                    secondary_color: id.secondary_color || team.secondary_color,
                },
                readOnly: true,
            };
        }
        // historical MLB team — nav state is the warm-path optimization only. Pre-processed teams
        // carry their own identity on the payload, so a cold link needs no client-side resolution.
        const navState = location.state as HistoricalNavState | null;
        const seasonObj = { season_id: ref.season } as Season;
        const team = await fetchShowdownTeam(
            seasonObj, ref.teamId, ref.sportId,
            navState?.abbr ?? String(ref.teamId), navState?.name, userShowdownSet,
        );
        return {
            team: {
                ...team,
                name: navState?.name || team.name,
                primary_color: navState?.primary_color || team.primary_color,
                secondary_color: navState?.secondary_color || team.secondary_color,
            },
            readOnly: true,
        };
    }

    async function loadTeams() {
        setLoading(true);
        setError(null);
        try {
            const myTeams = token ? await fetchUserTeams(token) : [];
            setUserTeams(myTeams);
            setListLoaded(true);
        } catch (err: any) {
            setError(err.message ?? 'Failed to load teams.');
        } finally {
            setLoading(false);
        }
    }

    function openTeam(team: TeamSummary) {
        trackRecentTeam(team.team_id);
        setView({ mode: 'loading' });
        navigate('/teams/' + team.team_id);
    }

    function goBack() {
        navigate('/teams');
        setView({ mode: 'list' });
    }

    // Refetch the currently open team (used by the "updated on another device" reload prompt).
    // Only saved teams can go stale; synthetic historical/ASG teams are rebuilt from the URL.
    function reloadCurrentTeam() {
        if (!teamRef || teamRef.kind !== 'saved') { setListLoaded(false); return; }
        fetchTeam(teamRef.teamId, token ?? undefined)
            .then(team => {
                const readOnly = !token || team.user_id !== session?.user?.id;
                setView({ mode: 'editor', team, readOnly });
            })
            .catch(() => {});
    }

    async function handleCreate(payload: TeamCreatePayload) {
        if (!token) return;
        const newTeam = await createTeam(payload, token);
        setShowCreateModal(false);
        setListLoaded(false); // list must refresh to include the new team
        trackRecentTeam(newTeam.team_id);
        // "Build from Scratch" opened this modal from a challenge card - carry the challenge
        // through so the team page can offer "Play Challenge" as soon as the roster is ready.
        const challenge = challengeForNewTeam;
        setChallengeForNewTeam(null);
        navigate('/teams/' + newTeam.team_id, challenge ? { state: { challenge } } : undefined);
        setView({ mode: 'editor', team: newTeam, readOnly: false });
    }

    // Quick Start: skip the New Team modal entirely and create an already-configured (but empty)
    // team, landing straight on the team page where autofill is one click away - the strategy/
    // filter controls there are already the "guided" draft experience, no separate UI needed.
    async function handleQuickStart(challenge: ChallengeInstance) {
        if (!token) return;
        // Prefer the profile username (a single handle, not a full name) over the email's local
        // part, matching how AccountAvatar derives a display identity elsewhere in the app.
        const displayName = username || session?.user?.email?.split('@')[0] || 'My';
        const abbreviation = displayName.replace(/[^a-zA-Z0-9]/g, '').slice(0, 5).toUpperCase() || challenge.replaces_abbr.slice(0, 5);
        const payload: TeamCreatePayload = {
            name: `${displayName}'s Team`,
            abbreviation,
            primary_color: 'rgb(0, 0, 0)',
            secondary_color: 'rgb(255, 255, 255)',
            is_public: false,
            pts_limit: challenge.pts_limit,
            roster_size: 20,
            min_bench: 2,
            min_bullpen: 5,
            num_starters: 4,
            bench_pts_multiplier: 0.2,
            allowed_card_sources: [CardSource.BOT],
            allowed_sets: [userShowdownSet],
            allowed_sets_by_source: { [CardSource.BOT]: [userShowdownSet] },
            origin_template_id: challenge.template_id,
            player_filters: challenge.player_filters,
        };
        const newTeam = await createTeam(payload, token);
        setListLoaded(false);
        trackRecentTeam(newTeam.team_id);
        navigate('/teams/' + newTeam.team_id, { state: { challenge } });
        setView({ mode: 'editor', team: newTeam, readOnly: false });
    }

    function handleBuildFromScratch(challenge: ChallengeInstance) {
        setChallengeForNewTeam(challenge);
        setShowCreateModal(true);
    }

    function handleUseExistingTeam(challenge: ChallengeInstance, teamId: string) {
        trackRecentTeam(teamId);
        navigate('/teams/' + teamId, { state: { challenge } });
    }

    // Opens a challenge's own shareable page. The challenge is carried as router state too, so
    // the card that linked here can paint the header instantly instead of waiting on the fetch.
    function openChallenge(challenge: ChallengeInstance) {
        navigate('/teams/challenges/' + challenge.instance_id, { state: { challenge } });
    }

    async function handleFork(teamId: string) {
        if (!token) return;
        const newTeam = await forkTeam(teamId, token);
        setListLoaded(false); // list must refresh to include the forked copy
        setActiveTab('mine');
        trackRecentTeam(newTeam.team_id);
        navigate('/teams/' + newTeam.team_id);
        setView({ mode: 'editor', team: newTeam, readOnly: false });
    }

    async function handleSave(teamId: string, updates: TeamUpdatePayload) {
        if (!token) return;
        const saved = await updateTeam(teamId, updates, token);
        setListLoaded(false); // summary (points, drafting, top players) may have changed
        setView(prev => prev.mode === 'editor' && prev.team.team_id === teamId
            ? { ...prev, team: saved }
            : prev
        );
    }

    // A challenge addressed by URL takes over the view entirely, independent of the team
    // list/editor state above — this is the shareable page, so it must resolve on a cold link
    // with no prior navigation state.
    if (challengeInstanceId) {
        return (
            <div className="flex flex-col gap-4 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
                <div className={px}>
                    <ChallengeDetail
                        key={challengeInstanceId}
                        instanceId={challengeInstanceId}
                        initialChallenge={(location.state as { challenge?: ChallengeInstance } | null)?.challenge}
                        token={token}
                        onBack={() => navigate('/teams')}
                        onQuickStart={handleQuickStart}
                        onBuildFromScratch={handleBuildFromScratch}
                        onUseExistingTeam={handleUseExistingTeam}
                        onOpenSeason={(teamId, jobId) => {
                            trackRecentTeam(teamId);
                            navigate(`/teams/${teamId}/sim/${jobId}`);
                        }}
                    />
                </div>
            </div>
        );
    }

    if (view.mode === 'loading') {
        return (
            <div className="flex flex-col h-full items-center justify-center py-12">
                <FaSpinner className="animate-spin text-(--text-tertiary) text-xl" />
            </div>
        );
    }

    if (view.mode === 'editor') {
        const { team, readOnly } = view;

        // A simulation addressed by URL takes over the view; the team is still resolved behind
        // it so going back is instant and the sim can show whose season it is.
        if (simJobId) {
            return (
                <div className="flex flex-col h-full">
                    <SimSeasonView
                        // Remounts on a new job id so state resets naturally instead of an
                        // effect clearing it — going straight from one result to another (e.g.
                        // via the leaderboard) must not show the previous season's data.
                        key={simJobId}
                        jobId={simJobId}
                        teamName={team.name}
                        token={token}
                        onBack={() => navigate('/teams/' + team.team_id)}
                        onBackToChallenges={() => { setActiveTab('simulations'); navigate('/teams'); }}
                    />
                </div>
            );
        }

        // A public team owned by someone else can be forked into the current user's own copy.
        const canFork = readOnly && !!token && team.source === 'user' && team.is_public;
        // Set only when this team page was reached from a challenge card - not stored on the
        // team itself, so a team isn't permanently bound to one instance and a page refresh just
        // drops back to the team's normal "Play" action.
        const challenge = (location.state as { challenge?: ChallengeInstance } | null)?.challenge;
        return (
            <div className="flex flex-col h-full">
                <TeamDetail
                    team={team}
                    readOnly={readOnly}
                    onSave={updates => handleSave(team.team_id, updates)}
                    onBack={goBack}
                    onReload={reloadCurrentTeam}
                    token={token}
                    onFork={canFork ? () => handleFork(team.team_id) : undefined}
                    challenge={challenge}
                />
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-4 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
            {/* Header */}
            <div className={`flex items-center ${px} justify-between`}>
                <div>
                    <h1 className="text-[20px] font-black text-(--text-primary)">Team Builder</h1>
                    <p className="text-[12px] text-(--text-secondary)">
                        Build your team, compete in challenges, and explore community creations.
                    </p>
                </div>
                {token && (
                    <button
                        type="button"
                        onClick={() => setShowCreateModal(true)}
                        className={`flex items-center gap-1 ${px} py-3 text-sm rounded-xl bg-(--secondary) font-bold text-(--background-primary) hover:opacity-90 transition-opacity cursor-pointer`}
                    >
                        <FaPlus />
                        New
                        <span className="hidden md:inline">Team</span>
                    </button>
                )}
            </div>

            {/* Tabs */}
            <Tabs tabs={TABS} value={activeTab} onChange={setActiveTab} className={px} fullWidth />

            {showCreateModal && (
                <NewTeamModal
                    onConfirm={handleCreate}
                    onCancel={() => { setShowCreateModal(false); setChallengeForNewTeam(null); }}
                    initialPayload={challengeForNewTeam ? {
                        pts_limit: challengeForNewTeam.pts_limit,
                        origin_template_id: challengeForNewTeam.template_id,
                        player_filters: challengeForNewTeam.player_filters,
                    } : undefined}
                />
            )}

            {error && (
                <div className="mx-4 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                    {error}
                </div>
            )}

            {/* My Teams tab */}
            {activeTab === 'mine' && (
                <>
                    {!loading && recentTeams.length > 0 && (
                        <TeamShelf title="Recent Teams" className={px}>
                            {recentTeams.map(team => (
                                <TeamPreviewCard key={team.team_id} team={team} onClick={() => openTeam(team)} />
                            ))}
                        </TeamShelf>
                    )}
                    {loading ? (
                        <div className="flex justify-center py-12">
                            <FaSpinner className="animate-spin text-(--text-tertiary) text-xl" />
                        </div>
                    ) : !token ? (
                        <p className="text-[13px] text-(--text-tertiary) py-8 text-center">
                            Sign in to create your own teams.
                        </p>
                    ) : (
                        <section className={`${px}`}>
                            {userTeams.length === 0 ? (
                                <TeamBuilderWelcome
                                    px=""
                                    onCreate={() => setShowCreateModal(true)}
                                    onGoToTab={setActiveTab}
                                    onOpenTeam={openTeam}
                                />
                            ) : (
                                <div className="space-y-3" >
                                    <h3 className="text-[15px] font-black text-(--text-primary) truncate">All Teams</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
                                        {userTeams.map(team => (
                                            <TeamCard
                                                key={team.team_id}
                                                team={team}
                                                onClick={() => openTeam(team)}
                                            />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </section>
                    )}
                </>
            )}

            {/* Community tab */}
            {activeTab === 'community' && (
                <CommunityTeams onOpen={openTeam} className={px} currentUserId={session?.user?.id} />
            )}

            {/* Historical tab */}
            {activeTab === 'historical' && (
                <HistoricalTeams horizontalPadding={px} />
            )}

            {/* Team Challenges tab */}
            {activeTab === 'simulations' && (
                <SimulationsTab
                    token={token}
                    horizontalPadding={px}
                    onOpenSeason={(teamId, jobId) => {
                        trackRecentTeam(teamId);
                        navigate(`/teams/${teamId}/sim/${jobId}`);
                    }}
                    onQuickStart={handleQuickStart}
                    onBuildFromScratch={handleBuildFromScratch}
                    onUseExistingTeam={handleUseExistingTeam}
                    onOpenChallenge={openChallenge}
                />
            )}
        </div>
    );
}
