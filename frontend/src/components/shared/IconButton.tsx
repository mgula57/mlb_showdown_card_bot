/**
 * @fileoverview Small square icon-only button — the toggle style used for expand/collapse and
 * similar single-glyph controls. Extracted from GameField's expand/collapse button so the
 * playback transport bar can reuse the exact same look instead of a second inline copy.
 */
import type { ReactNode } from "react";

type IconButtonProps = {
    icon: ReactNode;
    onClick: () => void;
    label: string;
    disabled?: boolean;
    className?: string;
};

export default function IconButton({ icon, onClick, label, disabled, className = "" }: IconButtonProps) {
    return (
        <button
            type="button"
            onClick={onClick}
            disabled={disabled}
            aria-label={label}
            className={`
                cursor-pointer rounded-md border border-(--divider) bg-(--background-secondary)/90 p-1.5
                text-(--secondary) transition-colors hover:text-(--primary)
                disabled:cursor-not-allowed disabled:opacity-40
                ${className}
            `}
        >
            {icon}
        </button>
    );
}
