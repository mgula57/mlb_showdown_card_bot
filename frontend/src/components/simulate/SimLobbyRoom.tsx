import { useEffect, useRef, useState } from 'react';
import { FaSpinner, FaPlay, FaRightFromBracket, FaCopy, FaCheck, FaUserGroup } from 'react-icons/fa6';
import FormDropdown from '../customs/FormDropdown';
import {
    fetchSimSeasonTeams, claimSimLobbyClub, leaveSimLobby, startSimLobby, fetchSimLobby,
    SimAlreadyRunningError, type SimLobbyState, type TakeoverClub,
} from '../../api/sim';
import { fetchUserTeams, type TeamSummary } from '../../api/userTeams';

// Matches the cadence the plan settled on for lobby state - fast enough to feel live, no new
// infrastructure (no websockets/Realtime) needed.
const POLL_INTERVAL_MS = 2000;

function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}

type Props = {
    lobbyId: string;
    initialState?: SimLobbyState;
    token?: string;
    userId?: string;
    onRunning: (jobId: string) => void;
    onLeave: () => void;
    onViewExisting: (jobId: string) => void;
};

/**
 * The waiting room: join code, member list, a claim form, and (host-only) the start button.
 * Once the lobby leaves 'open' status, `onRunning` fires so the caller can hand off to the same
 * `SeasonSimView` a solo open sim uses — a running/finished lobby is just that screen plus the
 * lobby's own job id, nothing lobby-specific left to render.
 */
export function SimLobbyRoom({ lobbyId, initialState, token, userId, onRunning, onLeave, onViewExisting }: Props) {
    const [state, setState] = useState<SimLobbyState | null>(initialState ?? null);
    const [error, setError] = useState<string | null>(null);
    const [clubs, setClubs] = useState<TakeoverClub[]>([]);
    const [userTeams, setUserTeams] = useState<TeamSummary[] | null>(null);
    const [claimClub, setClaimClub] = useState('');
    const [claimTeamId, setClaimTeamId] = useState('');
    const [claiming, setClaiming] = useState(false);
    const [starting, setStarting] = useState(false);
    const [codeCopied, setCodeCopied] = useState(false);
    const cancelled = useRef(false);
    const handedOff = useRef(false);

    const lobby = state?.lobby;
    const isHost = !!userId && lobby?.host_user_id === userId;
    const myMember = state?.members.find(m => m.user_id === userId);

    // Poll lobby state while the room is open. Hands off to the running job the moment it isn't.
    useEffect(() => {
        cancelled.current = false;
        let timer: number | undefined;

        async function poll() {
            try {
                const next = await fetchSimLobby(lobbyId);
                if (cancelled.current) return;
                if (!next) {
                    setError('This lobby no longer exists — it may have expired.');
                    return;
                }
                setState(next);
                if (next.lobby.status !== 'open' && next.lobby.job_id && !handedOff.current) {
                    handedOff.current = true;
                    onRunning(next.lobby.job_id);
                    return;
                }
                timer = window.setTimeout(poll, POLL_INTERVAL_MS);
            } catch (err: unknown) {
                if (!cancelled.current) setError(errorMessage(err));
            }
        }

        // If a running job was already known at mount (rejoining a link mid-run), hand off
        // immediately instead of waiting for the first poll.
        if (initialState && initialState.lobby.status !== 'open' && initialState.lobby.job_id) {
            handedOff.current = true;
            onRunning(initialState.lobby.job_id);
        } else {
            poll();
        }

        return () => {
            cancelled.current = true;
            if (timer) window.clearTimeout(timer);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [lobbyId]);

    // Real clubs for this lobby's season, for the claim picker. Depends on the primitive year
    // (not `lobby` itself), which would otherwise change - and refetch - on every 2s poll tick.
    const lobbyYear = lobby?.year;
    useEffect(() => {
        if (!lobbyYear) return;
        let stale = false;
        fetchSimSeasonTeams(lobbyYear)
            .then(({ teams }) => { if (!stale) setClubs(teams); })
            .catch(() => { if (!stale) setClubs([]); });
        return () => { stale = true; };
    }, [lobbyYear]);

    useEffect(() => {
        if (!token || userTeams !== null) return;
        fetchUserTeams(token).then(setUserTeams).catch(() => setUserTeams([]));
    }, [token, userTeams]);

    const claimedAbbrs = new Set((state?.members ?? []).filter(m => m.user_id !== userId).map(m => m.club_abbr));
    const availableClubs = clubs.filter(club => !claimedAbbrs.has(club.abbreviation));

    async function handleClaim() {
        if (!token || !claimClub) return;
        setClaiming(true);
        setError(null);
        try {
            const next = await claimSimLobbyClub(lobbyId, { club_abbr: claimClub, team_id: claimTeamId || undefined }, token);
            setState(next);
        } catch (err: unknown) {
            setError(errorMessage(err));
        } finally {
            setClaiming(false);
        }
    }

    async function handleLeave() {
        if (!token) return;
        try {
            await leaveSimLobby(lobbyId, token);
        } catch {
            // Leaving is best-effort - the member just navigates away regardless.
        }
        onLeave();
    }

    async function handleStart() {
        if (!token) return;
        setStarting(true);
        setError(null);
        try {
            const next = await startSimLobby(lobbyId, token);
            setState(next);
            if (next.lobby.job_id) {
                handedOff.current = true;
                onRunning(next.lobby.job_id);
            }
        } catch (err: unknown) {
            if (err instanceof SimAlreadyRunningError) {
                onViewExisting(err.jobId);
                return;
            }
            setError(errorMessage(err));
            setStarting(false);
        }
    }

    function copyCode() {
        if (!lobby) return;
        navigator.clipboard?.writeText(lobby.join_code).then(() => {
            setCodeCopied(true);
            setTimeout(() => setCodeCopied(false), 1500);
        }).catch(() => {});
    }

    if (!lobby) {
        return (
            <div className="flex flex-col items-center justify-center gap-3 py-16 px-4 text-center">
                {error ? (
                    <p className="text-[13px] text-(--text-secondary) max-w-sm">{error}</p>
                ) : (
                    <FaSpinner className="animate-spin text-(--text-tertiary) text-xl" />
                )}
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-4 max-w-2xl mx-auto w-full p-4">
            <div className="flex items-center justify-between gap-3">
                <div>
                    <h1 className="text-[20px] font-black text-(--text-primary)">{lobby.year} Lobby</h1>
                    <p className="text-[13px] text-(--text-secondary)">Set {lobby.showdown_set} · waiting for the host to start</p>
                </div>
                <button
                    type="button"
                    onClick={copyCode}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-(--background-tertiary) text-[13px] font-bold text-(--text-primary) hover:opacity-90 transition-opacity cursor-pointer"
                >
                    {lobby.join_code}
                    {codeCopied ? <FaCheck className="text-[11px] text-(--success)" /> : <FaCopy className="text-[11px]" />}
                </button>
            </div>

            <div className="rounded-xl bg-(--background-secondary) p-3 flex flex-col gap-2">
                <p className="text-[12px] font-bold text-(--text-primary) flex items-center gap-1.5">
                    <FaUserGroup className="text-[11px]" /> Players ({state?.members.length ?? 0})
                </p>
                {state?.members.length === 0 ? (
                    <p className="text-[12px] text-(--text-tertiary)">No one has claimed a club yet.</p>
                ) : (
                    <div className="flex flex-col gap-1.5">
                        {state?.members.map(member => (
                            <div key={member.user_id} className="flex items-center justify-between text-[12px] rounded-lg bg-(--background-tertiary) px-3 py-2">
                                <span className="font-semibold text-(--text-primary)">
                                    {member.club_abbr}
                                    {member.user_id === lobby.host_user_id && <span className="text-(--text-tertiary) font-normal"> · host</span>}
                                </span>
                                <span className="text-(--text-tertiary)">
                                    {member.team_name ? `Takeover: ${member.team_name}` : 'Following'}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {token && (
                <div className="rounded-xl bg-(--background-secondary) p-3 flex flex-col gap-3">
                    <p className="text-[12px] font-bold text-(--text-primary)">
                        {myMember ? 'Change your claim' : 'Claim a club'}
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <FormDropdown
                            label="Club"
                            options={availableClubs.map(club => ({ label: `${club.name} (${club.wins}-${club.losses})`, value: club.abbreviation }))}
                            selectedOption={claimClub || myMember?.club_abbr || ''}
                            onChange={setClaimClub}
                            placeholder="Select a club"
                        />
                        <FormDropdown
                            label="Take over with (optional)"
                            options={[{ label: 'Follow only', value: '' }, ...(userTeams ?? []).map(team => ({ label: `${team.name} (${team.abbreviation})`, value: team.team_id }))]}
                            selectedOption={claimTeamId || myMember?.team_id || ''}
                            onChange={setClaimTeamId}
                            disabled={userTeams === null}
                        />
                    </div>
                    <button
                        type="button"
                        onClick={handleClaim}
                        disabled={claiming || !(claimClub || myMember)}
                        className="self-start flex items-center gap-1.5 px-3 py-2 rounded-lg bg-(--secondary) text-[12px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        {claiming ? <FaSpinner className="animate-spin text-[10px]" /> : <FaCheck className="text-[10px]" />}
                        {myMember ? 'Update Claim' : 'Claim Club'}
                    </button>
                </div>
            )}

            {error && (
                <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                    {error}
                </div>
            )}

            <div className="flex items-center justify-between gap-2 pt-1">
                {!isHost && token && (
                    <button
                        type="button"
                        onClick={handleLeave}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[12px] font-semibold text-(--text-secondary) hover:text-(--text-primary) transition-colors cursor-pointer"
                    >
                        <FaRightFromBracket className="text-[10px]" /> Leave Lobby
                    </button>
                )}
                {isHost && (
                    <button
                        type="button"
                        onClick={handleStart}
                        disabled={starting || (state?.members.length ?? 0) === 0}
                        className="ml-auto flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-(--secondary) text-[13px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        {starting ? <FaSpinner className="animate-spin text-[11px]" /> : <FaPlay className="text-[11px]" />}
                        Start Simulation
                    </button>
                )}
            </div>
        </div>
    );
}
