/**
 * @fileoverview An applied filter in the card search's chip row ("Small Samples? No"), styled as
 * a small field to sit level with the Sort and Positions controls beside it: same height, frame
 * and text size, with the label in the tertiary semibold those controls use for "Sort" and
 * "Positions". Locked filters (set by team settings) show a lock instead of the remove button.
 */
import { FaLock, FaXmark } from 'react-icons/fa6';
import { FIELD_FRAME_CLASS, INLINE_FIELD_LABEL_CLASS } from '../shared/fieldStyles';

/** Label/value pair for a chip; `value` may carry its own comparison (">= 3"). */
export type FilterChipText = { label: string; value: string };

type FilterChipProps = {
    text: FilterChipText;
    locked?: boolean;
    onRemove: () => void;
};

export function FilterChip({ text, locked = false, onRemove }: FilterChipProps) {
    return (
        <div className={`flex items-center gap-1 shrink-0 h-8 pl-2.5 ${locked ? 'pr-2.5 bg-(--background-tertiary)!' : 'pr-1'} text-[12px] text-nowrap ${FIELD_FRAME_CLASS}`}>
            <span className={INLINE_FIELD_LABEL_CLASS}>{text.label}</span>
            <span className="max-w-72 overflow-x-clip">{text.value}</span>
            {locked ? (
                <FaLock className="shrink-0 text-[10px] text-(--text-tertiary)" title="Locked by team settings" />
            ) : (
                <button
                    type="button"
                    onClick={onRemove}
                    aria-label={`Remove ${text.label} filter`}
                    className="flex items-center justify-center w-6 h-6 rounded-control text-(--text-tertiary) hover:text-(--text-primary) hover:bg-(--background-tertiary) cursor-pointer"
                >
                    <FaXmark className="text-[12px]" />
                </button>
            )}
        </div>
    );
}

export default FilterChip;
