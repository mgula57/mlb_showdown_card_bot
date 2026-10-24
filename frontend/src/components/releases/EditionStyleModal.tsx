import { useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import type { ReleaseEdition } from '../../api/releases';
import { updateEdition } from '../../api/releases';
import { Modal } from '../shared/Modal';
import { CardStyleSections } from '../customs/CardStyleFields';
import type { CardStyleSettings } from '../customs/cardStyle';
import { CARD_STYLE_DEFAULTS, parseEditionStyle } from './editionStyle';

type EditionStyleModalProps = {
    releaseId: string;
    edition: ReleaseEdition;
    token?: string;
    onClose: () => void;
    onEditionUpdated: (edition: ReleaseEdition) => void;
};

/** Edits the default Set/Image style applied to every card in an edition — the same fields as the
 * Custom Card Builder, minus per-card inputs (set number, linked/uploaded images). */
export function EditionStyleModal({ releaseId, edition, token, onClose, onEditionUpdated }: EditionStyleModalProps) {
    const [style, setStyle] = useState<CardStyleSettings>(() => parseEditionStyle(edition.attributes));
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateStyle = (patch: Partial<CardStyleSettings>) => setStyle(prev => ({ ...prev, ...patch }));

    async function handleSave() {
        if (!token) return;
        setSaving(true);
        setError(null);
        try {
            const updated = await updateEdition(releaseId, edition.id, { attributes: { style } }, token);
            onEditionUpdated(updated);
            onClose();
        } catch (err: any) {
            setError(err.message ?? 'Failed to save card style.');
        } finally {
            setSaving(false);
        }
    }

    return (
        <Modal
            title="Card Style"
            subtitle={`Default set and image settings for every card in ${edition.name}.`}
            size="md"
            onClose={onClose}
            footer={
                <div className="flex items-center justify-end gap-2">
                    <button
                        type="button"
                        onClick={() => setStyle(CARD_STYLE_DEFAULTS)}
                        className="min-h-9 px-3.5 py-2 mr-auto rounded-lg text-[13px] font-semibold text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer"
                    >
                        Reset to Defaults
                    </button>
                    <button
                        type="button"
                        onClick={onClose}
                        className="min-h-9 px-3.5 py-2 rounded-lg text-[13px] font-bold border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors cursor-pointer"
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={handleSave}
                        disabled={!token || saving}
                        className="flex items-center gap-1.5 min-h-9 px-3.5 py-2 rounded-lg text-[13px] font-bold bg-(--secondary) text-(--background-primary) disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                    >
                        {saving && <FaSpinner className="animate-spin text-[12px]" />} Save
                    </button>
                </div>
            }
        >
            <div className="flex flex-col gap-3 p-4">
                {error && (
                    <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                        {error}
                    </div>
                )}
                <CardStyleSections values={style} onChange={updateStyle} defaults={CARD_STYLE_DEFAULTS} />
            </div>
        </Modal>
    );
}
