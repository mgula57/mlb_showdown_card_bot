import { useState, useEffect, useRef } from 'react';
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
import { TeamDetail } from './TeamDetail';
import { NewTeamModal } from './NewTeamModal';
import { RecentTeamsCarousel, trackRecentTeam } from './RecentTeamsCarousel';
import { CommunityTeams } from './CommunityTeams';
import { HistoricalTeams, asgIdentity, type HistoricalNavState } from './HistoricalTeams';
import { SimSeasonView } from './sim/SimSeasonView';
import { SimulationsTab } from './sim/SimulationsTab';
import { FaPlus, FaSpinner, FaUsers, FaGlobe, FaClockRotateLeft, FaRankingStar } from 'react-icons/fa6';
import type { TeamCreatePayload } from '../../api/userTeams';

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
    if (parts[1] !== 'historical' && parts[1] !== 'asg') {
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

type ViewState =
    | { mode: 'list' }
    | { mode: 'loading' }
    | { mode: 'editor'; team: Team; readOnly: boolean };

type TabId = 'mine' | 'community' | 'historical' | 'simulations';
const ACTIVE_TAB_KEY = 'teams.activeTab';
const TAB_IDS: TabId[] = ['mine', 'community', 'historical', 'simulations'];
// `shortLabel` keeps four tabs readable on a phone; the full label returns at sm.
const TABS: { id: TabId; label: string; shortLabel: string; icon: React.ReactNode }[] = [
    { id: 'mine', label: 'My Teams', shortLabel: 'Mine', icon: <FaUsers /> },
    { id: 'community', label: 'Community', shortLabel: 'Community', icon: <FaGlobe /> },
    { id: 'historical', label: 'Historical', shortLabel: 'History', icon: <FaClockRotateLeft /> },
    { id: 'simulations', label: 'Simulations', shortLabel: 'Sims', icon: <FaRankingStar /> },
];

export default function TeamBuilder() {
    const { session } = useAuth();
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
    const [activeTab, setActiveTab] = useState<TabId>(() => {
        const stored = typeof window !== 'undefined' ? window.localStorage.getItem(ACTIVE_TAB_KEY) : null;
        return TAB_IDS.includes(stored as TabId) ? (stored as TabId) : 'mine';
    });

    // Parse the team addressed by the current URL (saved UUID, historical, or All-Star).
    const teamRef = parseTeamRef(location.pathname);
    const simJobId = parseSimJobId(location.pathname);
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
        if (teamRef || listLoaded) return;
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
        navigate('/teams/' + newTeam.team_id);
        setView({ mode: 'editor', team: newTeam, readOnly: false });
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
                    />
                </div>
            );
        }

        // A public team owned by someone else can be forked into the current user's own copy.
        const canFork = readOnly && !!token && team.source === 'user' && team.is_public;
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
                />
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-4 py-4 max-w-4xl mx-auto w-full">
            {/* Header */}
            <div className="flex items-center px-4 justify-between">
                <div>
                    <h1 className="text-[20px] font-black text-(--text-primary)">Teams</h1>
                    <p className="text-[13px] text-(--text-secondary)">
                        Build your own rosters, browse community creations, and explore real historical teams 
                    </p>
                </div>
                {token && activeTab === 'mine' && (
                    <button
                        type="button"
                        onClick={() => setShowCreateModal(true)}
                        className="flex items-center gap-1 px-4 py-3 rounded-lg bg-(--secondary) text-[12px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity cursor-pointer"
                    >
                        <FaPlus className="text-[10px]" />
                        New
                        <span className="hidden sm:inline">Team</span>
                    </button>
                )}
            </div>

            {/* Tabs */}
            <div className="px-4">
                <div className="flex gap-1 rounded-lg bg-(--background-tertiary) p-1">
                    {TABS.map(tab => (
                        <button
                            key={tab.id}
                            type="button"
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex flex-1 items-center justify-center gap-1.5 px-3 py-2 text-[12px] font-semibold rounded-md whitespace-nowrap transition-colors cursor-pointer ${
                                activeTab === tab.id
                                    ? 'bg-(--showdown-blue) text-white shadow-sm'
                                    : 'text-(--text-tertiary) hover:text-(--text-secondary)'
                            }`}
                        >
                            <span>{tab.icon}</span>
                            <span className="hidden sm:inline">{tab.label}</span>
                            <span className="sm:hidden">{tab.shortLabel}</span>
                        </button>
                    ))}
                </div>
            </div>

            {showCreateModal && (
                <NewTeamModal
                    onConfirm={handleCreate}
                    onCancel={() => setShowCreateModal(false)}
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
                    {!loading && userTeams.length > 0 && (
                        <RecentTeamsCarousel teams={userTeams} onClick={openTeam} />
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
                        <section className="px-4">
                            {userTeams.length === 0 ? (
                                <p className="text-[13px] text-(--text-tertiary) py-4">
                                    You haven't created any teams yet.
                                </p>
                            ) : (
                                <div className="grid grid-cols-2 gap-2">
                                    {userTeams.map(team => (
                                        <TeamCard
                                            key={team.team_id}
                                            team={team}
                                            onClick={() => openTeam(team)}
                                        />
                                    ))}
                                </div>
                            )}
                        </section>
                    )}
                </>
            )}

            {/* Community tab */}
            {activeTab === 'community' && (
                <CommunityTeams onOpen={openTeam} currentUserId={session?.user?.id} />
            )}

            {/* Historical tab */}
            {activeTab === 'historical' && (
                <HistoricalTeams />
            )}

            {/* Simulations tab */}
            {activeTab === 'simulations' && (
                <SimulationsTab
                    token={token}
                    onOpenSeason={(teamId, jobId) => {
                        trackRecentTeam(teamId);
                        navigate(`/teams/${teamId}/sim/${jobId}`);
                    }}
                />
            )}
        </div>
    );
}
