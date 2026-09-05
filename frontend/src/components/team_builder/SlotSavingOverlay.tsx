import { FaSpinner } from 'react-icons/fa6';

/**
 * Overlay shown on a lineup / rotation slot in the moment right after a draft pick — the
 * roster has the new card, but the server hasn't re-derived the lineup/rotation yet, so the
 * slot itself is still showing its old occupant (or an empty placeholder). Covering it with a
 * spinner keeps the pick from looking like it did nothing until the save round-trips.
 *
 * `field` = on the dark field art (FieldView); `row` = on a panel background (DepthChartPanel).
 */
export function SlotSavingOverlay({ variant = 'field' }: { variant?: 'field' | 'row' }) {
    return (
        <div
            className={`absolute inset-0 z-30 flex items-center justify-center rounded-lg backdrop-blur-[1px] animate-pulse ${
                variant === 'field' ? 'bg-black/45' : 'bg-(--background-primary)/65'
            }`}
        >
            <FaSpinner
                className={`animate-spin ${
                    variant === 'field' ? 'text-white/90 text-sm' : 'text-(--text-secondary) text-xs'
                }`}
            />
        </div>
    );
}
