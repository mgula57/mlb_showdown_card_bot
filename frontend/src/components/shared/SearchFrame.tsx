import type { ReactNode } from 'react';
import { searchFrameClass } from './searchFrameStyles';

/**
 * Shared navy-to-red gradient frame around every search field and search button so search UI
 * reads consistently across the app.
 *
 * Wrap the already-styled inner element (input shell, icon button, …). It gets a 2px frame; the
 * child should use a slightly smaller radius (e.g. `rounded-card` inside the default `rounded-card`)
 * and paint its own background.
 */
export function SearchFrame({
    children,
    className = '',
    rounded = 'rounded-card',
}: {
    children: ReactNode;
    /** Extra classes for the frame (positioning, shadow, width…). */
    className?: string;
    /** Corner radius of the frame. */
    rounded?: string;
}) {
    return (
        <div className={`${searchFrameClass(rounded)} ${className}`}>
            {children}
        </div>
    );
}

export default SearchFrame;
