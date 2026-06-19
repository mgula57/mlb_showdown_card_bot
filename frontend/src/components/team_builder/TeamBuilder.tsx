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
    type TeamUpdatePayload,
} from '../../api/userTeams';
import { TeamCard } from './TeamCard';
import { TeamDetail } from './TeamDetail';
import { FaPlus, FaSpinner } from 'react-icons/fa6';
import { useSiteSettings } from '../shared/SiteSettingsContext';

type ViewState =
    | { mode: 'list' }
    | { mode: 'editor'; team: Team; readOnly: boolean };

export default function TeamBuilder() {
    const { session } = useAuth();
    const { userShowdownSet } = useSiteSettings();
    const location = useLocation();
    const navigate = useNavigate();
    const token = session?.access_token;

    const [userTeams, setUserTeams] = useState<Team[]>([]);
    const [officialTeams, setOfficialTeams] = useState<Team[]>([]);
    const [view, setView] = useState<ViewState>({ mode: 'list' });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Extract teamId from URL: /teams/:teamId
    const teamIdFromUrl = location.pathname.split('/')[2] ?? null;

    useEffect(() => {
        loadTeams();
    }, [token]);

    // When URL contains a team ID, fetch and open that team
    useEffect(() => {
        if (!teamIdFromUrl) {
            setView({ mode: 'list' });
            return;
        }
        if (view.mode === 'editor' && view.team.team_id === teamIdFromUrl) return;

        fetchTeam(teamIdFromUrl, token ?? undefined)
            .then(team => {
                const readOnly = !token || team.user_id !== session?.user?.id;
                setView({ mode: 'editor', team, readOnly });
            })
            .catch(() => {
                navigate('/teams', { replace: true });
            });
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
        } catch (err: any) {
            setError(err.message ?? 'Failed to load teams.');
        } finally {
            setLoading(false);
        }
    }

    function openTeam(team: Team, readOnly: boolean) {
        navigate('/teams/' + team.team_id);
        setView({ mode: 'editor', team, readOnly });
    }

    function goBack() {
        navigate('/teams');
        setView({ mode: 'list' });
    }

    async function handleCreate() {
        if (!token) return;
        const newTeam = await createTeam(
            { name: 'New Team', abbreviation: 'NEW', showdown_set: userShowdownSet },
            token,
        );
        setUserTeams(prev => [newTeam, ...prev]);
        navigate('/teams/' + newTeam.team_id);
        setView({ mode: 'editor', team: newTeam, readOnly: false });
    }

    async function handleSave(teamId: string, updates: TeamUpdatePayload) {
        if (!token) return;
        const saved = await updateTeam(teamId, updates, token);
        setUserTeams(prev => prev.map(t => t.team_id === teamId ? saved : t));
        setView(prev => prev.mode === 'editor' && prev.team.team_id === teamId
            ? { ...prev, team: saved }
            : prev
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
                    token={token}
                />
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6 p-4 max-w-4xl mx-auto w-full">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-[20px] font-black text-(--text-primary)">Teams</h1>
                    <p className="text-[13px] text-(--text-secondary)">
                        Build and manage your Showdown rosters
                    </p>
                </div>
                {token && (
                    <button
                        type="button"
                        onClick={handleCreate}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-(--secondary) text-[12px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity"
                    >
                        <FaPlus className="text-[10px]" /> New Team
                    </button>
                )}
            </div>

            {error && (
                <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                    {error}
                </div>
            )}

            {loading ? (
                <div className="flex justify-center py-12">
                    <FaSpinner className="animate-spin text-(--text-tertiary) text-xl" />
                </div>
            ) : (
                <>
                    {/* My Teams */}
                    {token && (
                        <section>
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
                                            onClick={() => openTeam(team, false)}
                                        />
                                    ))}
                                </div>
                            )}
                        </section>
                    )}

                    {/* Official & ASG Teams */}
                    {officialTeams.length > 0 && (
                        <section>
                            <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide mb-2">
                                Official &amp; All-Star Teams
                            </div>
                            <div className="flex flex-col gap-2">
                                {officialTeams.map(team => (
                                    <TeamCard
                                        key={team.team_id}
                                        team={team}
                                        onClick={() => openTeam(team, true)}
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
