import { useState } from 'react';
import type { ReleaseCreatePayload } from '../../api/releases';
import FormInput from '../customs/FormInput';
import { useSiteSettings, showdownSets } from '../shared/SiteSettingsContext';
import { FaXmark, FaPlus, FaSpinner } from 'react-icons/fa6';
import CustomSelect from '../shared/CustomSelect';

type NewReleaseModalProps = {
    onConfirm: (payload: ReleaseCreatePayload) => Promise<void>;
    onCancel: () => void;
};

export function NewReleaseModal({ onConfirm, onCancel }: NewReleaseModalProps) {
    const { userShowdownSet } = useSiteSettings();
    const [draft, setDraft] = useState<ReleaseCreatePayload>({ name: '', description: '', default_showdown_set: userShowdownSet });
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const canCreate = draft.name.trim().length > 0;

    async function handleCreate() {
        if (!canCreate || creating) return;
        setCreating(true);
        setError(null);
        try {
            await onConfirm(draft);
        } catch (err: any) {
            setError(err.message ?? 'Failed to create release.');
            setCreating(false);
        }
    }

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            onClick={onCancel}
        >
            <div
                className="bg-(--background-primary) rounded-2xl w-full max-w-lg shadow-2xl border border-(--divider) overflow-hidden flex flex-col max-h-[90dvh]"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-4 pt-4 pb-3 border-b border-(--divider) shrink-0">
                    <div>
                        <div className="text-[14px] font-black text-(--text-primary)">
                            New Release
                        </div>
                        <div className="text-[11px] text-(--text-secondary) mt-0.5">Name your set — you can add editions and cards next</div>
                    </div>
                    <button
                        type="button"
                        onClick={onCancel}
                        className="text-(--text-tertiary) hover:text-(--text-primary) transition-colors"
                    >
                        <FaXmark className="text-[14px]" />
                    </button>
                </div>

                {/* Form */}
                <div className="overflow-y-auto flex-1 min-h-0 px-4 py-4 flex flex-col gap-3">
                    <FormInput
                        label="Name"
                        value={draft.name}
                        onChange={v => setDraft(prev => ({ ...prev, name: v ?? '' }))}
                        placeholder="2026 Base Set"
                    />
                    <FormInput
                        label="Description"
                        value={draft.description ?? ''}
                        onChange={v => setDraft(prev => ({ ...prev, description: v ?? '' }))}
                        placeholder="Optional"
                    />
                    <div className="flex flex-col gap-1 ">
                        <label className="text-sm font-medium text-secondary">Default Showdown Set</label>
                        <CustomSelect
                            value={draft.default_showdown_set ?? userShowdownSet}
                            onChange={v => setDraft(prev => ({ ...prev, default_showdown_set: v }))}
                            options={showdownSets}
                            imageClassName="object-contain w-18 rounded-sm"
                        />
                        <span className="text-[11px] text-(--text-tertiary)">
                            This is just a starting point — you can add cards from other sets too.
                        </span>
                    </div>
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
                                ${canCreate && !creating ? 'bg-linear-to-r from-blue-500 to-red-500 hover:opacity-90 cursor-pointer' : 'bg-(--secondary) opacity-40 cursor-not-allowed'}`}
                        >
                            {creating
                                ? <><FaSpinner className="animate-spin text-[11px]" /> Creating…</>
                                : <><FaPlus className="text-[11px]" /> Create Release</>
                            }
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
