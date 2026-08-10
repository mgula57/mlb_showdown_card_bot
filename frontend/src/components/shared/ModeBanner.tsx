/**
 * @fileoverview The full-width gradient strip that marks a page as being in a special mode —
 * the team builder's DRAFTING/EDITING bar, and the game page's TAKEOVER SIM bar.
 *
 * The gradient runs left→right between two identity colors, so text on the left has to contrast
 * against the first color and controls on the right against the second. `bannerTokens` resolves
 * that per side; use `left` for the label and `right` for anything trailing.
 */
import type { ReactNode } from "react";
import { bannerTokens } from "../../functions/colors";

type ModeBannerProps = {
    /** Gradient start — the label contrasts against this. */
    primaryColor: string;
    /** Gradient end — `children` contrasts against this. */
    secondaryColor: string;
    label: ReactNode;
    /** Hidden below md, where the bar is too narrow for a full sentence. */
    detail?: ReactNode;
    /** Whether the leading status dot pulses. */
    pulse?: boolean;
    /** Trailing controls, rendered against `secondaryColor`. */
    children?: ReactNode;
    className?: string;
};

export function ModeBanner({
    primaryColor, secondaryColor, label, detail, pulse = false, children, className = '',
}: ModeBannerProps) {
    const left = bannerTokens(primaryColor);
    return (
        <div
            className={`flex items-center gap-3 px-4 py-2 shrink-0 ${className}`}
            style={{ background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})` }}
        >
            <span
                className={`w-2 h-2 rounded-full shrink-0 ${pulse ? 'animate-pulse' : ''}`}
                style={{ backgroundColor: left.dot }}
            />
            <span className="text-[11px] font-bold flex-1 drop-shadow-sm flex items-center gap-4" style={{ color: left.fill }}>
                {label}
                {detail && <span className="hidden md:inline font-normal">{detail}</span>}
            </span>
            {children && <div className="flex items-center gap-2 shrink-0">{children}</div>}
        </div>
    );
}
