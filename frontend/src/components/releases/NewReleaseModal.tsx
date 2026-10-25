import { useState } from 'react';
import type { ReleaseCreatePayload } from '../../api/releases';
import FormInput from '../customs/FormInput';
import { useSiteSettings } from '../shared/SiteSettingsContext';
import { SET_SELECT_OPTIONS } from '../shared/SetBadge';
import { FaPlus, FaSpinner } from 'react-icons/fa6';
import CustomSelect from '../shared/CustomSelect';

import { InlineError } from '../shared/InlineError';
import { buttonClass } from '../shared/buttonStyles';
import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { Modal } from '../shared/Modal';
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

    const footer = (
        <div className="flex flex-col gap-2">
            {error && <InlineError>{error}</InlineError>}
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
    );

    return (
        <Modal
            title="New Release"
            subtitle="Name your set — you can add editions and cards next"
            size="sm"
            onClose={onCancel}
            footer={footer}
        >
            <div className="px-4 py-4 flex flex-col gap-3">
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
                <div className="flex flex-col gap-1">
                    <label className={FIELD_LABEL_CLASS}>Default Showdown Set</label>
                    <CustomSelect
                        value={draft.default_showdown_set ?? userShowdownSet}
                        onChange={v => setDraft(prev => ({ ...prev, default_showdown_set: v }))}
                        options={SET_SELECT_OPTIONS}
                    />
                    <span className="text-[11px] text-(--text-tertiary)">
                        This is just a starting point — you can add cards from other sets too.
                    </span>
                </div>
            </div>
        </Modal>
    );
}
