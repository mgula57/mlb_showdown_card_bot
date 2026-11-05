import { useState, type ReactNode } from 'react';
import { FaSpinner, FaTrashCan } from 'react-icons/fa6';
import { InlineError } from '../shared/InlineError';
import { buttonClass } from '../shared/buttonStyles';
import { Modal } from '../shared/Modal';

type ReleaseDeleteModalProps = {
    title: string;
    /** What deleting does, in plain words (whether it's undoable, what happens to teams). */
    children: ReactNode;
    confirmLabel: string;
    /** Rejects with the error to show; the modal stays open so the user can retry. */
    onConfirm: () => Promise<void>;
    onCancel: () => void;
};

/** Confirms deleting a release or an edition. */
export function ReleaseDeleteModal({ title, children, confirmLabel, onConfirm, onCancel }: ReleaseDeleteModalProps) {
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleConfirm() {
        if (deleting) return;
        setDeleting(true);
        setError(null);
        try {
            await onConfirm();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete.');
            setDeleting(false);
        }
    }

    const footer = (
        <div className="flex flex-col gap-2">
            {error && <InlineError>{error}</InlineError>}
            <div className="flex gap-2">
                <button type="button" onClick={onCancel} className={buttonClass('secondary', 'md', 'flex-1 py-2.5!')}>
                    Cancel
                </button>
                <button type="button" onClick={handleConfirm} disabled={deleting} className={buttonClass('danger', 'md', 'flex-1 py-2.5!')}>
                    {deleting ? <FaSpinner className="animate-spin text-[11px]" /> : <FaTrashCan className="text-[11px]" />}
                    {confirmLabel}
                </button>
            </div>
        </div>
    );

    return (
        <Modal title={title} size="sm" onClose={onCancel} footer={footer}>
            <div className="px-4 py-4 flex flex-col gap-2 text-[13px] text-(--text-secondary)">
                {children}
            </div>
        </Modal>
    );
}
