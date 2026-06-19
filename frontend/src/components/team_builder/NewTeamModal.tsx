import { useState } from 'react';
import type { TeamCreatePayload } from '../../api/userTeams';
import { TeamSettingsForm } from './TeamSettingsForm';
import { FaXmark, FaPlus, FaSpinner } from 'react-icons/fa6';
import { useSiteSettings } from '../shared/SiteSettingsContext';

type NewTeamModalProps = {
    onConfirm: (payload: TeamCreatePayload) => Promise<void>;
    onCancel: () => void;
};

export function NewTeamModal({ onConfirm, onCancel }: NewTeamModalProps) {
    const { userShowdownSet } = useSiteSettings();
    const DEFAULTS: TeamCreatePayload = {
        name: '',
        abbreviation: '',
        primary_color: 'rgb(0, 0, 0)',
        secondary_color: 'rgb(255, 255, 255)',
        is_public: false,
        pts_limit: null,
        roster_size: 20,
        min_bench: 2,
        min_bullpen: 5,
        num_starters: 4,
        bench_pts_multiplier: 0.2,
        allowed_sets: [userShowdownSet],
    };
    const [draft, setDraft] = useState<TeamCreatePayload>({ ...DEFAULTS });
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const rosterUsed = 9 + (draft.num_starters ?? 4) + (draft.min_bullpen ?? 5) + (draft.min_bench ?? 2);
    const rosterValid = rosterUsed <= (draft.roster_size ?? 20);
    const ptsValid = draft.pts_limit == null || draft.pts_limit >= (draft.roster_size ?? 20) * 10;
    const canCreate = draft.name.trim().length > 0 && draft.abbreviation.trim().length > 0 && rosterValid && ptsValid && (draft.allowed_sets ?? []).length > 0;

    async function handleCreate() {
        if (!canCreate || creating) return;
        setCreating(true);
        setError(null);
        try {
            await onConfirm(draft);
        } catch (err: any) {
            setError(err.message ?? 'Failed to create team.');
            setCreating(false);
        }
    }

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            onClick={onCancel}
        >
            <div
                className="bg-(--background-primary) rounded-2xl w-full max-w-sm shadow-2xl border border-(--divider) overflow-hidden flex flex-col max-h-[90dvh]"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-4 pt-4 pb-3 border-b border-(--divider) shrink-0">
                    <div>
                        <div className="text-[14px] font-black text-(--text-primary)">New Team</div>
                        <div className="text-[11px] text-(--text-secondary) mt-0.5">Configure your team settings</div>
                    </div>
                    <button
                        type="button"
                        onClick={onCancel}
                        className="text-(--text-tertiary) hover:text-(--text-primary) transition-colors"
                    >
                        <FaXmark className="text-[14px]" />
                    </button>
                </div>

                {/* Scrollable form */}
                <div className="overflow-y-auto flex-1 min-h-0">
                    <TeamSettingsForm
                        team={draft}
                        onChange={updates => setDraft(prev => ({ ...prev, ...updates }))}
                    />
                </div>

                {/* Footer */}
                <div className="px-4 py-3 border-t border-(--divider) shrink-0 flex flex-col gap-2">
                    {error && (
                        <div className="text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                            {error}
                        </div>
                    )}
                    <div className="flex gap-2">
                        <button
                            type="button"
                            onClick={onCancel}
                            className="flex-1 py-2.5 rounded-xl text-[13px] font-semibold border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="button"
                            onClick={handleCreate}
                            disabled={!canCreate || creating}
                            className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-[13px] font-bold text-white transition-opacity
                                ${canCreate && !creating ? 'bg-(--secondary) hover:opacity-90 cursor-pointer' : 'bg-(--secondary) opacity-40 cursor-not-allowed'}`}
                        >
                            {creating
                                ? <><FaSpinner className="animate-spin text-[11px]" /> Creating…</>
                                : <><FaPlus className="text-[11px]" /> Create Team</>
                            }
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
