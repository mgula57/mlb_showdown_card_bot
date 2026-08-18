import { useState } from 'react';
import { FaSpinner, FaUsers, FaRightToBracket } from 'react-icons/fa6';
import FormInput from '../customs/FormInput';
import BackButton from '../shared/BackButton';
import { SeasonSimSetupForm } from './SeasonSimSetupForm';
import { createSimLobby, joinSimLobby, type CreateSimLobbyPayload, type SimLobbyState } from '../../api/sim';

function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}

type Props = {
    token?: string;
    onEnterLobby: (state: SimLobbyState) => void;
    onBack: () => void;
    /** Which tab to land on — e.g. the header's "Join" button skips straight to 'join'. */
    initialMode?: 'create' | 'join';
};

/**
 * Entry point for a shared multiplayer sim: create a new lobby or join one with a code. Lobby
 * creation reuses `SeasonSimSetupForm` (the same engine-settings form a solo sim uses) since the
 * host fixes those up front — who follows or takes over which club is a per-member claim made
 * inside the lobby room, not here.
 */
export function SimLobbyEntry({ token, onEnterLobby, onBack, initialMode }: Props) {
    const [mode, setMode] = useState<'create' | 'join'>(initialMode ?? 'create');
    const [joinCode, setJoinCode] = useState('');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleCreateLobby(payload: CreateSimLobbyPayload) {
        if (!token) throw new Error('Sign in to create a lobby.');
        const state = await createSimLobby(payload, token);
        onEnterLobby(state);
    }

    async function handleJoin() {
        const code = joinCode.trim().toUpperCase();
        if (!code) {
            setError('Enter a join code.');
            return;
        }
        setBusy(true);
        setError(null);
        try {
            const state = await joinSimLobby(code);
            if (!state) {
                setError('No lobby found for that code — it may have expired.');
                return;
            }
            onEnterLobby(state);
        } catch (err: unknown) {
            setError(errorMessage(err));
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="flex flex-col gap-4">
            <div className="max-w-2xl mx-auto w-full px-4 pt-3 flex items-center justify-between gap-3">
                <BackButton onBack={onBack} label="Back" />
                <div className="flex rounded-lg bg-(--background-tertiary) p-1 gap-1">
                    <button
                        type="button"
                        onClick={() => { setMode('create'); setError(null); }}
                        className={`flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-bold cursor-pointer transition-colors ${mode === 'create' ? 'bg-(--secondary) text-(--background-primary)' : 'text-(--text-secondary)'}`}
                    >
                        <FaUsers className="text-[11px]" /> Create
                    </button>
                    <button
                        type="button"
                        onClick={() => { setMode('join'); setError(null); }}
                        className={`flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-bold cursor-pointer transition-colors ${mode === 'join' ? 'bg-(--secondary) text-(--background-primary)' : 'text-(--text-secondary)'}`}
                    >
                        <FaRightToBracket className="text-[11px]" /> Join
                    </button>
                </div>
            </div>

            {mode === 'create' ? (
                <SeasonSimSetupForm mode="lobby" token={token} onCreateLobby={handleCreateLobby} />
            ) : (
                <div className="flex flex-col gap-4 max-w-md mx-auto w-full p-4">
                    <div>
                        <h1 className="text-[20px] font-black text-(--text-primary)">Join a Lobby</h1>
                        <p className="text-[13px] text-(--text-secondary) mt-1">
                            Enter the code someone sent you to jump into their simulated season.
                        </p>
                    </div>
                    <FormInput
                        label="Join Code"
                        value={joinCode}
                        onChange={value => setJoinCode((value ?? '').toUpperCase())}
                        placeholder="e.g. AB12CD"
                        isClearable
                    />
                    <button
                        type="button"
                        onClick={handleJoin}
                        disabled={busy}
                        className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-lg bg-(--secondary) text-[13px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        {busy ? <FaSpinner className="animate-spin text-[11px]" /> : <FaRightToBracket className="text-[11px]" />}
                        Join Lobby
                    </button>
                    {error && (
                        <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                            {error}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
