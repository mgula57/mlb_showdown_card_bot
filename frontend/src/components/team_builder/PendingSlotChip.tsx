import { FaXmark } from 'react-icons/fa6';

/** Pulsing amber pill naming the slot being filled, with an optional dismiss (×). */
export function PendingSlotChip({ label, onDismiss }: { label: string; onDismiss?: () => void }) {
    return (
        <span className="flex items-center gap-1.5 shrink-0 rounded-full border border-amber-500 dark:border-amber-400 bg-amber-500/10 px-2 py-1 text-[11px] font-bold whitespace-nowrap text-amber-600 dark:text-amber-400">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            {label}
            {onDismiss && (
                <button
                    type="button"
                    onClick={onDismiss}
                    className="hover:opacity-70 cursor-pointer"
                    aria-label="Cancel filling"
                >
                    <FaXmark className="text-[10px]" />
                </button>
            )}
        </span>
    );
}
