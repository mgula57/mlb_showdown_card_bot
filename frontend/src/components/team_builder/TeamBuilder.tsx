import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import {
    fetchUserTeams,
    fetchPublicTeams,
    fetchTeam,
    createTeam,
    updateTeam,
    type Team,
    type TeamSummary,
    type TeamUpdatePayload,
} from '../../api/userTeams';
import { TeamCard } from './TeamCard';
import { TeamDetail } from './TeamDetail';
import { NewTeamModal } from './NewTeamModal';
import { RecentTeamsCarousel, trackRecentTeam } from './RecentTeamsCarousel';
import { FaPlus, FaSpinner } from 'react-icons/fa6';
import type { TeamCreatePayload } from '../../api/userTeams';

type ViewState =
    | { mode: 'list' }
    | { mode: 'loading' }
    | { mode: 'editor'; team: Team; readOnly: boolean };

export default function TeamBuilder() {
    const { session } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const token = session?.access_token;

    const [userTeams, setUserTeams] = useState<TeamSummary[]>([]);
    const [officialTeams, setOfficialTeams] = useState<TeamSummary[]>([]);
    const [view, setView] = useState<ViewState>({ mode: 'list' });
    const [loading, setLoading] = useState(true);
    const [listLoaded, setListLoaded] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);

    // Extract teamId from URL: /teams/:teamId — only when actually on a /teams/ path
    const teamIdFromUrl = location.pathname.startsWith('/teams/')
        ? (location.pathname.split('/')[2] ?? null)
        : null;

    // Auth change invalidates the cached list
    useEffect(() => { setListLoaded(false); }, [token]);

    // Load the (lightweight) teams list lazily — only when viewing the list, so a direct
    // visit to /teams/:teamId opens the team without first loading every team.
    useEffect(() => {
        if (teamIdFromUrl || listLoaded) return;
        loadTeams();
    }, [teamIdFromUrl, listLoaded, token]);

    // When URL contains a team ID, fetch and open that full team independently of the list
    useEffect(() => {
        if (!teamIdFromUrl) {
            setView(v => v.mode === 'list' ? v : { mode: 'list' });
            return;
        }
        if (view.mode === 'editor' && view.team.team_id === teamIdFromUrl) return;

        setView({ mode: 'loading' });
        fetchTeam(teamIdFromUrl, token ?? undefined)
            .then(team => {
                const readOnly = !token || team.user_id !== session?.user?.id;
                setView({ mode: 'editor', team, readOnly });
            })
            .catch(() => {
                navigate('/teams', { replace: true });
            });
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [teamIdFromUrl, token]);

    async function loadTeams() {
        setLoading(true);
        setError(null);
        try {
            const [publicTeams, myTeams] = await Promise.all([
                fetchPublicTeams(undefined, 100),
                token ? fetchUserTeams(token) : Promise.resolve([]),
            ]);
            setOfficialTeams(publicTeams.filter(t => t.source !== 'user'));
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

    // Refetch the currently open team (used by the "updated on another device" reload prompt)
    function reloadCurrentTeam() {
        if (!teamIdFromUrl) { setListLoaded(false); return; }
        fetchTeam(teamIdFromUrl, token ?? undefined)
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
        return (
            <div className="flex flex-col h-full">
                <TeamDetail
                    team={team}
                    readOnly={readOnly}
                    onSave={updates => handleSave(team.team_id, updates)}
                    onBack={goBack}
                    onReload={reloadCurrentTeam}
                    token={token}
                />
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6 py-4 max-w-4xl mx-auto w-full">
            {/* Header */}
            <div className="flex items-center px-4 justify-between">
                <div>
                    <h1 className="text-[20px] font-black text-(--text-primary)">Teams</h1>
                    <p className="text-[13px] text-(--text-secondary)">
                        Build and share your own Showdown rosters
                    </p>
                </div>
                {token && (
                    <button
                        type="button"
                        onClick={() => setShowCreateModal(true)}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-(--secondary) text-[12px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity"
                    >
                        <FaPlus className="text-[10px]" /> 
                        New
                        <span className="hidden sm:inline">Team</span>
                    </button>
                )}
            </div>

            {showCreateModal && (
                <NewTeamModal
                    onConfirm={handleCreate}
                    onCancel={() => setShowCreateModal(false)}
                />
            )}

            {error && (
                <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                    {error}
                </div>
            )}

            {!loading && (
                <RecentTeamsCarousel
                    teams={[...userTeams, ...officialTeams]}
                    onClick={openTeam}
                />
            )}

            {loading ? (
                <div className="flex justify-center py-12">
                    <FaSpinner className="animate-spin text-(--text-tertiary) text-xl" />
                </div>
            ) : (
                <>
                    {/* My Teams */}
                    {token && (
                        <section className="px-4">
                            <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide mb-2">
                                My Teams
                            </div>
                            {userTeams.length === 0 ? (
                                <p className="text-[13px] text-(--text-tertiary) py-4">
                                    You haven't created any teams yet.
                                </p>
                            ) : (
                                <div className="flex flex-col gap-2">
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

                    {/* Official & ASG Teams */}
                    {officialTeams.length > 0 && (
                        <section className="px-4">
                            <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide mb-2">
                                Official &amp; All-Star Teams
                            </div>
                            <div className="flex flex-col gap-2">
                                {officialTeams.map(team => (
                                    <TeamCard
                                        key={team.team_id}
                                        team={team}
                                        onClick={() => openTeam(team)}
                                    />
                                ))}
                            </div>
                        </section>
                    )}

                    {!token && officialTeams.length === 0 && (
                        <p className="text-[13px] text-(--text-tertiary) py-4 text-center">
                            Sign in to create your own teams.
                        </p>
                    )}
                </>
            )}
        </div>
    );
}
