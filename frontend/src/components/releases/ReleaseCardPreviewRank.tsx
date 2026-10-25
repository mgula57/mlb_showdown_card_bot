/**
 * @fileoverview User-chosen slot for a Release Builder card on the release's list tile (see
 * `ReleaseItem`): a badge for the pool grid and a picker for the card detail modal.
 */

import { FaStar } from 'react-icons/fa6';
import { Plate } from '../shared/Plate';
import { choiceClass } from '../shared/choiceStyles';
import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';

/** Mirrors the backend's `_RELEASE_CARD_MAX_PREVIEW_RANK` (and the tile's fan size). */
export const MAX_PREVIEW_RANK = 3;
const RANKS = Array.from({ length: MAX_PREVIEW_RANK }, (_, i) => i + 1);

export function ReleaseCardPreviewRankBadge({ rank }: { rank: number }) {
    return (
        <Plate variant="navy" size="sm" title={`Release preview #${rank}`} className="gap-0.5">
            <FaStar className="text-[8px]" />
            {rank}
        </Plate>
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
            <span className={FIELD_LABEL_CLASS}>Release Preview</span>
            <div className="flex flex-wrap items-center gap-1">
                {options.map(opt => {
                    const selected = opt.value === rank;
                    return (
                        <button
                            key={opt.label}
                            type="button"
                            onClick={() => onChange(opt.value)}
                            aria-pressed={selected}
                            className={choiceClass(selected, 'sm', 'tabular-nums')}
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
