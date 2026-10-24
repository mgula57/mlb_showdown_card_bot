/**
 * @fileoverview CardStyleEditor - Inline Card Style (Set + Image) editor for a single card, shown
 * inside CardDetail. Edits auto-save after a pause; the caller owns persistence and re-renders the
 * card by passing CardDetail updated `styleOverrides`.
 */

import { useEffect, useRef, useState } from 'react';
import { FaCheck, FaPalette, FaRotateLeft, FaSpinner, FaXmark } from 'react-icons/fa6';
import { CardStyleSections } from '../../customs/CardStyleFields';
import { useMediaQuery } from '../../../hooks/useMediaQuery';
import { isCardStyleDifferent, type CardStyleSettings } from '../../customs/cardStyle';

/** Enables in-place style editing on CardDetail (see its `styleEditor` prop) */
export type CardStyleEditorConfig = {
    /** The card's current style */
    style: CardStyleSettings;
    /** What Revert resets to and what collapsed section summaries compare against, e.g. the
     * edition's default style */
    defaults: CardStyleSettings;
    /** Persists the style — called automatically once edits pause. Throw to show an error (the
     * next edit retries). */
    onSave: (style: CardStyleSettings) => Promise<void> | void;
    /** Revert button tooltip, e.g. "Revert to the edition style" */
    revertTitle?: string;
};

/** How long edits must pause before they're saved — each save re-renders the card image */
const SAVE_DELAY_MS = 800;

type CardStyleEditorProps = CardStyleEditorConfig & {
    onClose: () => void;
};

export function CardStyleEditor({ style: initialStyle, defaults, onSave, revertTitle = 'Revert to the default style', onClose }: CardStyleEditorProps) {
    const [style, setStyle] = useState<CardStyleSettings>(initialStyle);
    // On phones the editor sits above the card — start collapsed so the card still peeks out below
    const isDesktop = useMediaQuery('(min-width: 768px)');
    const [saving, setSaving] = useState(false);
    const [hasSaved, setHasSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateStyle = (patch: Partial<CardStyleSettings>) => setStyle(prev => ({ ...prev, ...patch }));

    // Auto-save once edits pause, one save at a time (an edit made mid-save goes out after it).
    // Starts from the card's own style, so opening the editor (or toggling a field back) saves nothing.
    const lastSavedRef = useRef<CardStyleSettings>(initialStyle);
    const styleRef = useRef(style);
    styleRef.current = style;
    const isUnsaved = isCardStyleDifferent(style, lastSavedRef.current);
    useEffect(() => {
        if (saving || !isCardStyleDifferent(style, lastSavedRef.current)) return;
        const timer = setTimeout(async () => {
            setSaving(true);
            setError(null);
            try {
                await onSave(style);
                lastSavedRef.current = style;
                setHasSaved(true);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to save card style.');
            } finally {
                setSaving(false);
            }
        }, SAVE_DELAY_MS);
        return () => clearTimeout(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [style, saving]);

    /** Closing mid-pause still saves the latest edit */
    function handleClose() {
        if (!saving && isCardStyleDifferent(styleRef.current, lastSavedRef.current)) {
            Promise.resolve(onSave(styleRef.current)).catch(err => console.error('Failed to save card style:', err));
        }
        onClose();
    }

    return (
        <div className="flex-1 flex flex-col min-h-0 bg-secondary rounded-xl border border-form-element fade-in">
            {/* Header */}
            <div className="flex items-center gap-2 pl-4 pr-2 py-2 border-b border-form-element shrink-0">
                <FaPalette className="text-[12px] opacity-60" />
                <div className="text-[12px] font-semibold opacity-60 uppercase tracking-widest">Card Style</div>
                <span className="flex items-center gap-1 text-[11px] text-(--text-tertiary)">
                    {saving ? (
                        <><FaSpinner className="animate-spin text-[10px]" /> Saving</>
                    ) : hasSaved && !isUnsaved && !error ? (
                        <><FaCheck className="text-[10px]" /> Saved</>
                    ) : null}
                </span>
                <div className="ml-auto flex items-center gap-1">
                    <button
                        type="button"
                        onClick={() => setStyle(defaults)}
                        disabled={!isCardStyleDifferent(style, defaults)}
                        title={revertTitle}
                        className="flex items-center gap-1.5 min-h-8 px-2.5 py-1.5 rounded-lg text-[13px] font-semibold text-(--text-tertiary) hover:text-(--text-primary) disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
                    >
                        <FaRotateLeft className="text-[11px]" /> Revert
                    </button>
                    <button
                        type="button"
                        onClick={handleClose}
                        title="Close"
                        className="p-2 rounded-lg text-(--text-tertiary) hover:text-(--text-primary) hover:bg-(--background-tertiary) transition-colors cursor-pointer"
                    >
                        <FaXmark className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>

            {/* Fields */}
            <div className="flex flex-col gap-3 p-3 min-h-0 overflow-y-auto">
                {error && (
                    <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                        {error}
                    </div>
                )}
                <CardStyleSections values={style} onChange={updateStyle} defaults={defaults} isOpenByDefault={isDesktop} />
            </div>
        </div>
    );
}
