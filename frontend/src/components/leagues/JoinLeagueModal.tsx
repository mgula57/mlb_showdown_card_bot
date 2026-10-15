import { useEffect, useState } from 'react';
import { FaRightToBracket, FaSpinner } from 'react-icons/fa6';
import { Modal } from '../shared/Modal';
import FormInput from '../customs/FormInput';
import { joinLeague, previewLeague, type LeaguePreview, type LeagueState } from '../../api/leagues';
import { ERROR_BOX_CLASS, PRIMARY_BUTTON_CLASS, SECONDARY_BUTTON_CLASS, errorMessage } from './leagueUi';

const JOIN_CODE_LENGTH = 6;

type Props = {
    token: string;
    /** Prefilled from a shared link. */
    initialCode?: string;
    onJoined: (state: LeagueState) => void;
    onClose: () => void;
};

/** Join a league by its 6-character code: shows which league the code leads to before joining. */
export function JoinLeagueModal({ token, initialCode = '', onJoined, onClose }: Props) {
    const [code, setCode] = useState(initialCode.toUpperCase());
    const [displayName, setDisplayName] = useState('');
    // EACH LOOKUP IS STORED WITH THE CODE IT WAS FOR, SO EDITING THE CODE HIDES A STALE RESULT
    const [lookup, setLookup] = useState<{ code: string; preview: LeaguePreview | null; error: string | null } | null>(null);
    const [joining, setJoining] = useState(false);
    const [joinError, setJoinError] = useState<string | null>(null);

    const isCompleteCode = code.trim().length === JOIN_CODE_LENGTH;
    useEffect(() => {
        if (!isCompleteCode) return;
        let cancelled = false;
        previewLeague(token, code)
            .then(preview => { if (!cancelled) setLookup({ code, preview, error: null }); })
            .catch(err => { if (!cancelled) setLookup({ code, preview: null, error: errorMessage(err) }); });
        return () => { cancelled = true; };
    }, [code, isCompleteCode, token]);

    const current = isCompleteCode && lookup?.code === code ? lookup : null;
    const preview = current?.preview ?? null;
    const previewing = isCompleteCode && current === null;
    const error = joinError ?? current?.error ?? null;

    const isFull = preview ? preview.member_count >= preview.team_count : false;
    const canJoin = !!preview && (preview.is_member || (preview.status === 'open' && !isFull)) && !joining;

    async function handleJoin() {
        if (!canJoin) return;
        setJoining(true);
        setJoinError(null);
        try {
            onJoined(await joinLeague(token, code, displayName.trim() || undefined));
        } catch (err) {
            setJoinError(errorMessage(err));
            setJoining(false);
        }
    }

    const footer = (
        <div className="flex flex-col gap-2 w-full">
            {error && <div className={ERROR_BOX_CLASS}>{error}</div>}
            <div className="flex justify-end gap-2">
                <button type="button" onClick={onClose} className={SECONDARY_BUTTON_CLASS}>Cancel</button>
                <button type="button" onClick={handleJoin} disabled={!canJoin} className={PRIMARY_BUTTON_CLASS}>
                    {joining ? <FaSpinner className="animate-spin" /> : <FaRightToBracket className="text-[11px]" />}
                    {preview?.is_member ? 'Open League' : 'Join League'}
                </button>
            </div>
        </div>
    );

    return (
        <Modal title="Join a League" subtitle="Enter the code the commissioner shared" onClose={onClose} footer={footer} size="sm">
            <div className="flex flex-col gap-4 p-4">
                <FormInput
                    label="Join code"
                    value={code}
                    onChange={v => { setCode((v ?? '').toUpperCase().slice(0, JOIN_CODE_LENGTH)); setJoinError(null); }}
                    placeholder="ABC123"
                />

                {previewing && <div className="h-16 rounded-xl bg-(--background-secondary) animate-pulse" />}
                {preview && (
                    <div className="rounded-xl border border-(--divider) bg-(--background-secondary) px-3 py-2.5">
                        <div className="text-[14px] font-black text-(--text-primary)">{preview.name}</div>
                        <div className="text-[11px] text-(--text-secondary)">
                            {preview.commissioner_name ? `Run by ${preview.commissioner_name} · ` : ''}
                            Set {preview.showdown_set} · {preview.member_count}/{preview.team_count} teams
                        </div>
                        {!preview.is_member && preview.status !== 'open' && (
                            <div className="text-[11px] text-(--warning) mt-1">This league has already drafted.</div>
                        )}
                        {!preview.is_member && preview.status === 'open' && isFull && (
                            <div className="text-[11px] text-(--warning) mt-1">This league is full.</div>
                        )}
                        {preview.is_member && <div className="text-[11px] text-(--success) mt-1">You're already in this league.</div>}
                    </div>
                )}

                {preview && !preview.is_member && (
                    <FormInput label="Your name in the league" value={displayName} onChange={v => setDisplayName(v ?? '')} placeholder="Defaults to your username" />
                )}
            </div>
        </Modal>
    );
}
