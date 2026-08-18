import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FaUsers } from 'react-icons/fa6';
import { FaDiceD20 } from 'react-icons/fa';
import { useAuth } from '../auth/AuthContext';
import { startOpenSim, type OpenSimPayload, type SimLobbyState } from '../../api/sim';
import { SeasonSimSetupForm } from './SeasonSimSetupForm';
import { SeasonSimView } from './SeasonSimView';
import { SimLobbyEntry } from './SimLobbyEntry';
import { SimLobbyRoom } from './SimLobbyRoom';
import { RecentSims } from './RecentSims';
import BackButton from '../shared/BackButton';

// A running/finished simulation gets its own URL (/simulate/:jobId), the same pattern
// team_builder's SimSeasonView uses at /teams/:teamId/sim/:jobId - a refresh mid-run reconnects
// to the job instead of losing it, since the job's state lives in Postgres. `/simulate/lobby` and
// `/simulate/lobby/:lobbyId` are parsed out first so they don't get mistaken for a job id.
function parseLobbyRef(pathname: string): { lobbyId?: string } | null {
    const parts = pathname.split('/').filter(Boolean);
    if (parts[0] !== 'simulate' || parts[1] !== 'lobby') return null;
    return { lobbyId: parts[2] };
}

function parseSimJobId(pathname: string): string | null {
    const parts = pathname.split('/').filter(Boolean);
    if (parts[0] !== 'simulate' || !parts[1] || parts[1] === 'lobby') return null;
    return parts[1];
}

/** Entry point for the Open Sim page (`/simulate`, `/simulate/:jobId`, `/simulate/lobby[/:id]`) -
 *  simulate any season solo or with friends, optionally take over any number of clubs, and
 *  browse the result club by club. */
export default function SeasonSimulator() {
    const location = useLocation();
    const navigate = useNavigate();
    const { session, user } = useAuth();
    const token = session?.access_token;
    const userId = user?.id;
    const [showCreateForm, setShowCreateForm] = useState(false);

    const lobbyRef = parseLobbyRef(location.pathname);
    const jobId = parseSimJobId(location.pathname);
    const queryParams = new URLSearchParams(location.search);
    const focusAbbrParam = queryParams.get('focus') ?? undefined;
    const yearParam = queryParams.get('year');
    const initialYear = yearParam && /^\d+$/.test(yearParam) ? Number(yearParam) : undefined;
    const lobbyInitialMode = queryParams.get('mode') === 'join' ? 'join' : undefined;

    async function handleStart(payload: OpenSimPayload) {
        if (!token) throw new Error('Sign in to simulate a season.');
        const { job_id, focus_abbr } = await startOpenSim(payload, token);
        navigate(`/simulate/${job_id}${focus_abbr ? `?focus=${focus_abbr}` : ''}`);
    }

    function handleViewExisting(existingJobId: string) {
        navigate(`/simulate/${existingJobId}`);
    }

    function handleRunAgain() {
        navigate('/simulate');
    }

    function handleEnterLobby(state: SimLobbyState) {
        navigate(`/simulate/lobby/${state.lobby.lobby_id}`);
    }

    if (lobbyRef) {
        if (!lobbyRef.lobbyId) {
            return (
                <SimLobbyEntry
                    token={token}
                    onEnterLobby={handleEnterLobby}
                    onBack={() => navigate('/simulate')}
                    initialMode={lobbyInitialMode}
                />
            );
        }
        return (
            <SimLobbyRoom
                lobbyId={lobbyRef.lobbyId}
                token={token}
                userId={userId}
                onRunning={runningJobId => navigate(`/simulate/${runningJobId}`, { replace: true })}
                onLeave={() => navigate('/simulate/lobby')}
                onViewExisting={handleViewExisting}
            />
        );
    }

    if (jobId) {
        return (
            <SeasonSimView jobId={jobId} token={token} initialFocusAbbr={focusAbbrParam} onRunAgain={handleRunAgain} />
        );
    }

    if (!token) {
        return (
            <div className="flex flex-col items-center justify-center gap-3 py-16 px-4 text-center">
                <p className="text-[14px] text-(--text-secondary)">Sign in to simulate a season.</p>
            </div>
        );
    }

    if (showCreateForm) {
        return (
            <div className="flex flex-col gap-3">
                <div className="max-w-2xl mx-auto w-full px-4 pt-3">
                    <BackButton onBack={() => setShowCreateForm(false)} label="Back" />
                </div>
                <SeasonSimSetupForm mode="solo" token={token} onStart={handleStart} onViewExisting={handleViewExisting} initialYear={initialYear} />
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-4 max-w-2xl mx-auto w-full p-4">
            <div>
                <h1 className="text-[20px] font-black text-(--text-primary)">Simulate</h1>
                <p className="text-[13px] text-(--text-secondary) mt-1">
                    Play out any MLB season, solo or with friends.
                </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
                <button
                    type="button"
                    onClick={() => setShowCreateForm(true)}
                    className="relative overflow-hidden rounded-2xl p-4 flex flex-col items-start gap-1 border border-(--divider) bg-(--background-tertiary) text-left transition-all duration-200 hover:scale-[1.02] active:scale-95 cursor-pointer"
                >
                    <FaDiceD20 className="absolute -bottom-2 -right-2 text-7xl opacity-5" />
                    <FaDiceD20 className="text-3xl mb-1 text-purple-500" />
                    <span className="font-bold text-sm text-(--text-primary)">Solo Sim</span>
                    <span className="text-xs leading-snug text-(--text-tertiary)">Simulate a season on your own</span>
                </button>
                <button
                    type="button"
                    onClick={() => navigate('/simulate/lobby')}
                    className="relative overflow-hidden rounded-2xl p-4 flex flex-col items-start gap-1 border border-(--divider) bg-(--background-tertiary) text-left transition-all duration-200 hover:scale-[1.02] active:scale-95 cursor-pointer"
                >
                    <FaUsers className="absolute -bottom-2 -right-2 text-7xl opacity-5" />
                    <FaUsers className="text-3xl mb-1 text-orange-500" />
                    <span className="font-bold text-sm text-(--text-primary)">Collab Sim</span>
                    <span className="text-xs leading-snug text-(--text-tertiary)">Create or join a lobby with friends</span>
                </button>
            </div>

            <RecentSims token={token} onOpen={handleViewExisting} />
        </div>
    );
}
