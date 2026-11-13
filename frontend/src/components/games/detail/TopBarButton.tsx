/**
 * @fileoverview A button in `GameDetail`'s top bar (Replay, Past Sims, Simulate, and the sim's
 * Watch / Skip / Exit controls). Never wraps its label - when the bar runs out of room the label
 * truncates with an ellipsis instead, so the bar keeps a single row on narrow screens.
 */
import type { ReactNode } from "react";
import { CornerCount } from "../../shared/CornerCount";
import { SLANT_ROOM_CLASS } from "../../shared/headingStyles";

type TopBarButtonProps = {
    label: string;
    /** Shorter label swapped in below the `sm` breakpoint, where the bar is tightest. */
    shortLabel?: string;
    onClick: () => void;
    icon?: ReactNode;
    /** Small count pinned to the top-right corner. Hidden when 0 or absent. */
    badge?: number;
    /** Colors/border/padding for this button's look — layout and truncation are handled here. */
    className?: string;
};

export default function TopBarButton({ label, shortLabel, onClick, icon, badge, className = "" }: TopBarButtonProps) {
    return (
        <button
            type="button"
            onClick={onClick}
            title={label}
            className={`relative inline-flex min-w-0 shrink items-center gap-x-1 whitespace-nowrap cursor-pointer text-[11px] font-bold transition-colors ${className}`}
        >
            {icon && <span className="shrink-0 flex items-center">{icon}</span>}
            {shortLabel ? (
                <>
                    <span className={`truncate sm:hidden ${SLANT_ROOM_CLASS}`}>{shortLabel}</span>
                    <span className={`truncate hidden sm:inline ${SLANT_ROOM_CLASS}`}>{label}</span>
                </>
            ) : (
                <span className={`truncate ${SLANT_ROOM_CLASS}`}>{label}</span>
            )}
            <CornerCount count={badge ?? 0} />
        </button>
    );
}
