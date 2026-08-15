import { useState } from 'react';
import type { TeamCreatePayload } from '../../api/userTeams';
import { TeamSettingsForm } from './TeamSettingsForm';
import { FaPlus, FaSpinner } from 'react-icons/fa6';
import { useSiteSettings } from '../shared/SiteSettingsContext';
import { CardSource } from '../../types/cardSource';
import { activeSources, allowedSetsForSource } from '../../domain/teamSets';
import { Modal } from '../shared/Modal';

type NewTeamModalProps = {
    onConfirm: (payload: TeamCreatePayload) => Promise<void>;
    onCancel: () => void;
    /** Overrides merged over the usual defaults — e.g. a challenge's pts_limit/origin tag when
     *  this modal is opened from the "Build from Scratch" challenge route. Not locked/read-only:
     *  the budget is still enforced server-side when the team is actually used for a challenge
     *  run, so there's no harm in letting the user adjust it here. */
    initialPayload?: Partial<TeamCreatePayload>;
};

export function NewTeamModal({ onConfirm, onCancel, initialPayload }: NewTeamModalProps) {
    const { userShowdownSet } = useSiteSettings();
    const DEFAULTS: TeamCreatePayload = {
        name: '',
        abbreviation: '',
        primary_color: 'rgb(0, 0, 0)',
        secondary_color: 'rgb(255, 255, 255)',
        is_public: true,
        pts_limit: 5000,
        roster_size: 20,
        min_bench: 2,
        min_bullpen: 5,
        num_starters: 4,
        bench_pts_multiplier: 0.2,
        // A new team starts as a single-set Bot team; the settings form opens up WOTC (and its
        // combinable sets) from there.
        allowed_card_sources: [CardSource.BOT],
        allowed_sets: [userShowdownSet],
        allowed_sets_by_source: { [CardSource.BOT]: [userShowdownSet] },
    };
    const [draft, setDraft] = useState<TeamCreatePayload>({ ...DEFAULTS, ...initialPayload });
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const rosterUsed = 9 + (draft.num_starters ?? 4) + (draft.min_bullpen ?? 5) + (draft.min_bench ?? 2);
    const rosterValid = rosterUsed <= (draft.roster_size ?? 20);
    const ptsValid = draft.pts_limit == null || draft.pts_limit >= (draft.roster_size ?? 20) * 10;
    // Every source the team drafts from needs at least one set of its own.
    const setsValid = activeSources(draft).every(source => allowedSetsForSource(draft, source).length > 0);
    const canCreate = draft.name.trim().length > 0 && draft.abbreviation.trim().length > 0 && rosterValid && ptsValid && setsValid;

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

    const footer = (
        <>
            {error && (
                <div className="text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                    {error}
                </div>
            )}
            <div className="flex gap-2">
                <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 py-2.5 rounded-xl text-[13px] font-semibold border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors cursor-pointer"
                >
                    Cancel
                </button>
                <button
                    type="button"
                    onClick={handleCreate}
                    disabled={!canCreate || creating}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-[13px] font-bold text-white transition-opacity
                        ${canCreate && !creating ? 'bg-linear-to-r from-blue-500 to-red-500 hover:opacity-90 cursor-pointer' : 'bg-(--secondary) opacity-40 cursor-not-allowed'}`}
                >
                    {creating
                        ? <><FaSpinner className="animate-spin text-[11px]" /> Creating…</>
                        : <><FaPlus className="text-[11px]" /> Create Team</>
                    }
                </button>
            </div>
        </>
    );

    return (
        <Modal title="New Team" subtitle="Configure your team settings" onClose={onCancel} size="sm" footer={footer}>
            <TeamSettingsForm
                team={draft}
                onChange={updates => setDraft(prev => ({ ...prev, ...updates }))}
            />
        </Modal>
    );
}
