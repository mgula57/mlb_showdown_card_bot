import { useState } from 'react';
import { FaSpinner, FaUsers, FaRightToBracket } from 'react-icons/fa6';
import FormInput from '../customs/FormInput';
import BackButton from '../shared/BackButton';
import { SeasonSimSetupForm } from './SeasonSimSetupForm';
import { createSimLobby, joinSimLobby, type CreateSimLobbyPayload, type SimLobbyState } from '../../api/sim';

import { InlineError } from '../shared/InlineError';
import { Heading } from '../shared/Heading';
import { buttonClass } from '../shared/buttonStyles';
import { Tabs } from '../shared/Tabs';
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
                <Tabs
                    size="sm"
                    value={mode}
                    onChange={next => { setMode(next); setError(null); }}
                    tabs={[
                        { id: 'create', label: 'Create', icon: <FaUsers className="text-[11px]" /> },
                        { id: 'join', label: 'Join', icon: <FaRightToBracket className="text-[11px]" /> },
                    ]}
                />
            </div>

            {mode === 'create' ? (
                <SeasonSimSetupForm mode="lobby" token={token} onCreateLobby={handleCreateLobby} />
            ) : (
                <div className="flex flex-col gap-4 max-w-md mx-auto w-full p-4">
                    <div>
                        <Heading level="page">Join a Lobby</Heading>
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
                        className={buttonClass('primary', 'md')}
                    >
                        {busy ? <FaSpinner className="animate-spin text-[11px]" /> : <FaRightToBracket className="text-[11px]" />}
                        Join lobby
                    </button>
                    {error && (
                        <InlineError size="md">
                            {error}
                        </InlineError>
                    )}
                </div>
            )}
        </div>
    );
}
