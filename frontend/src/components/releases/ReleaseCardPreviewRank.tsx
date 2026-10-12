/**
 * @fileoverview User-chosen slot for a Release Builder card on the release's list tile (see
 * `ReleaseItem`): a badge for the pool grid and a picker for the card detail modal.
 */

import { FaStar } from 'react-icons/fa6';

/** Mirrors the backend's `_RELEASE_CARD_MAX_PREVIEW_RANK` (and the tile's fan size). */
export const MAX_PREVIEW_RANK = 3;
const RANKS = Array.from({ length: MAX_PREVIEW_RANK }, (_, i) => i + 1);

export function ReleaseCardPreviewRankBadge({ rank }: { rank: number }) {
    return (
        <span
            title={`Release preview #${rank}`}
            className="inline-flex items-center gap-0.5 rounded-md bg-(--secondary) text-(--background-primary) text-[9px] font-black py-0.5 px-1.5 shadow-sm ring-1 ring-black/20"
        >
            <FaStar className="text-[8px]" />
            {rank}
        </span>
    );
}

type ReleaseCardPreviewRankPickerProps = {
    rank: number | null;
    readOnly: boolean;
    onChange: (rank: number | null) => void;
};

/** Picking a slot another card holds moves it to this card (handled by the caller). */
export function ReleaseCardPreviewRankPicker({ rank, readOnly, onChange }: ReleaseCardPreviewRankPickerProps) {
    if (readOnly) {
        return rank ? <ReleaseCardPreviewRankBadge rank={rank} /> : null;
    }

    const options: Array<{ label: string; value: number | null }> = [
        { label: 'Auto', value: null },
        ...RANKS.map(r => ({ label: String(r), value: r })),
    ];

    return (
        <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-bold text-(--text-tertiary) uppercase tracking-wide">Release Preview</span>
            <div className="flex items-center rounded-lg border border-(--divider) overflow-hidden">
                {options.map(opt => {
                    const selected = opt.value === rank;
                    return (
                        <button
                            key={opt.label}
                            type="button"
                            onClick={() => onChange(opt.value)}
                            aria-pressed={selected}
                            className={`min-h-8 px-2.5 text-[11px] font-bold uppercase tracking-wide transition-colors cursor-pointer
                                ${selected ? 'bg-(--secondary) text-(--background-primary)' : 'text-(--text-tertiary) hover:text-(--text-primary)'}`}
                        >
                            {opt.label}
                        </button>
                    );
                })}
            </div>
            <span className="text-[10px] text-(--text-tertiary)">Slot 1 sits in front. Needs a rendered image.</span>
        </div>
    );
}
