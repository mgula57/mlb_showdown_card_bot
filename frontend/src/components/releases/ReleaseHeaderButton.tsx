import type { ReactNode } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import { buttonVariantClass } from '../shared/buttonStyles';

const HEADER_BUTTON_TONES = {
    neutral: buttonVariantClass('secondary'),
    primary: buttonVariantClass('primary'),
    // A like the viewer has given (TeamDetail's `liked` header action)
    liked: 'bg-(--showdown-red)/15 text-(--showdown-red) hover:bg-(--showdown-red)/25 cursor-pointer',
} as const;

type ReleaseHeaderButtonProps = {
    icon: ReactNode;
    label: string;
    onClick: () => void;
    tone?: keyof typeof HEADER_BUTTON_TONES;
    /** Swaps the icon for a spinner and blocks re-entry while an async action is in flight. */
    busy?: boolean;
    /** Icon-only below `sm`, so secondary actions don't crowd the release name on phones. */
    collapseLabel?: boolean;
    /** A tally after the label, e.g. the like count. Hidden at 0. */
    count?: number;
    title?: string;
};

/** The compact action buttons in the Release Builder's headers. */
export function ReleaseHeaderButton({ icon, label, onClick, tone = 'neutral', busy = false, collapseLabel = false, count, title }: ReleaseHeaderButtonProps) {
    return (
        <button
            type="button"
            onClick={onClick}
            disabled={busy}
            title={title ?? label}
            aria-label={count ? `${label} (${count})` : label}
            className={`flex items-center justify-center gap-1.5 h-8 min-w-8 px-2 sm:px-3 rounded-control text-[12px] font-semibold whitespace-nowrap transition-colors disabled:opacity-50 ${HEADER_BUTTON_TONES[tone]}`}
        >
            <span className="text-[12px]">{busy ? <FaSpinner className="animate-spin" /> : icon}</span>
            <span className={collapseLabel ? 'hidden sm:inline' : ''}>{label}</span>
            {!!count && <span className="text-[11px] font-bold tabular-nums opacity-75">{count}</span>}
        </button>
    );
}
