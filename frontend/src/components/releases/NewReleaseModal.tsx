import { useState } from 'react';
import type { ReleaseCreatePayload } from '../../api/releases';
import FormInput from '../customs/FormInput';
import { useSiteSettings, showdownSets } from '../shared/SiteSettingsContext';
import { FaXmark, FaPlus, FaSpinner } from 'react-icons/fa6';
import CustomSelect from '../shared/CustomSelect';

import { InlineError } from '../shared/InlineError';
import { buttonClass } from '../shared/buttonStyles';
import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { Heading } from '../shared/Heading';
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
                className="bg-(--background-primary) rounded-card w-full max-w-lg shadow-overlay border border-(--divider) overflow-hidden flex flex-col max-h-[90dvh]"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-4 pt-4 pb-3 border-b border-(--divider) shrink-0">
                    <div>
                        <Heading level="section">New Release</Heading>
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
                        <label className={FIELD_LABEL_CLASS}>Default Showdown Set</label>
                        <CustomSelect
                            value={draft.default_showdown_set ?? userShowdownSet}
                            onChange={v => setDraft(prev => ({ ...prev, default_showdown_set: v }))}
                            options={showdownSets}
                            imageClassName="object-contain w-18 rounded-control"
                        />
                        <span className="text-[11px] text-(--text-tertiary)">
                            This is just a starting point — you can add cards from other sets too.
                        </span>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-4 py-3 border-t border-(--divider) shrink-0 flex flex-col gap-2">
                    {error && (
                        <InlineError>
                            {error}
                        </InlineError>
                    )}
                    <div className="flex gap-2">
                        <button
                            type="button"
                            onClick={onCancel}
                            className={buttonClass('secondary', 'md', 'flex-1 py-2.5!')}
                        >
                            Cancel
                        </button>
                        <button
                            type="button"
                            onClick={handleCreate}
                            disabled={!canCreate || creating}
                            className={buttonClass('primary', 'md', 'flex-1 py-2.5!')}
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
