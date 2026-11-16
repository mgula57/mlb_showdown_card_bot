/**
 * @fileoverview The thumb-sized buttons in the field's bottom corners: the strategy hand on the
 * left, the Manager and the next move (Pitch / Swing / Pass / Wait) on the right. One shape for all
 * of them, so the corners read as one set of controls on every board: a square with an icon over a
 * short label, and a live dot pinned to the corner when something needs a look.
 */
import type { ReactNode } from "react";

import { buttonClass } from "../shared/buttonStyles";

type BoardCornerButtonProps = {
    icon: ReactNode;
    label: ReactNode;
    onClick: () => void;
    /** `primary` when it's the move to make now (the player's roll or pass). */
    variant?: "primary" | "secondary";
    disabled?: boolean;
    /** Read out in place of the visible label, when the label alone doesn't say enough. */
    ariaLabel?: string;
    /** For a button that opens a panel or tray. */
    isExpanded?: boolean;
    /** Something behind it needs a look (a playable card, a tiring pitcher). */
    hasDot?: boolean;
};

export default function BoardCornerButton({ icon, label, onClick, variant = "secondary", disabled, ariaLabel, isExpanded, hasDot }: BoardCornerButtonProps) {
    return (
        <button
            type="button"
            onClick={onClick}
            disabled={disabled}
            aria-label={ariaLabel}
            aria-expanded={isExpanded}
            className={buttonClass(variant, "sm", "relative h-14 w-14 shrink-0 flex-col justify-center gap-1 p-0! text-[11px]! leading-none shadow-raised")}
        >
            <span className="flex h-6 items-center justify-center" aria-hidden>{icon}</span>
            {label}
            {hasDot && <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-(--live)" aria-hidden />}
        </button>
    );
}
