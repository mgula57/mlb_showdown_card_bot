import { useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import type { ReleaseEdition } from '../../api/releases';
import { updateEdition } from '../../api/releases';
import { Modal } from '../shared/Modal';
import { CardStyleSections } from '../customs/CardStyleFields';
import type { CardStyleSettings } from '../customs/cardStyle';
import { CARD_STYLE_DEFAULTS, parseEditionStyle } from './editionStyle';

import { InlineError } from '../shared/InlineError';
import { buttonClass } from '../shared/buttonStyles';
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
                        className={buttonClass('ghost', 'sm', 'mr-auto')}
                    >
                        Reset to defaults
                    </button>
                    <button
                        type="button"
                        onClick={onClose}
                        className={buttonClass('secondary', 'sm')}
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={handleSave}
                        disabled={!token || saving}
                        className={buttonClass('primary', 'sm')}
                    >
                        {saving && <FaSpinner className="animate-spin text-[12px]" />} Save
                    </button>
                </div>
            }
        >
            <div className="flex flex-col gap-3 p-4">
                {error && (
                    <InlineError size="md">
                        {error}
                    </InlineError>
                )}
                <CardStyleSections values={style} onChange={updateStyle} defaults={CARD_STYLE_DEFAULTS} />
            </div>
        </Modal>
    );
}
