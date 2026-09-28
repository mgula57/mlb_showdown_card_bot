import type { ReactNode } from 'react';

/**
 * Shared red→blue gradient border used to frame every search field and search
 * button so search UI reads consistently across the app.
 *
 * Wrap the already-styled inner element (input shell, icon button, …). It gets a
 * 2px (`p-0.5`) gradient frame; the child should use a slightly smaller radius
 * (e.g. `rounded-md` inside the default `rounded-lg`) and paint its own background.
 */
export function SearchGradientBorder({
    children,
    className = '',
    rounded = 'rounded-lg',
}: {
    children: ReactNode;
    /** Extra classes for the gradient wrapper (positioning, shadow, width…). */
    className?: string;
    /** Corner radius of the gradient frame. */
    rounded?: string;
}) {
    return (
        <div className={`bg-linear-to-r from-blue-500 to-red-500 p-0.5 ${rounded} ${className}`}>
            {children}
        </div>
    );
}

export default SearchGradientBorder;
