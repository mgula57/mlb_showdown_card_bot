import { useState } from 'react';
import { createPortal } from 'react-dom';

type UnderToolbarFillProps = {
    /** Positioning/colour classes (horizontal extent and background), e.g. `left-0 w-full bg-black/50` */
    className: string;
    /** Stacking order; set above whatever page content sits under the toolbar */
    zIndex?: number;
};

/**
 * Continues a full-screen `position: fixed` overlay down behind mobile Safari's bottom toolbar.
 *
 * Fixed elements are clipped to the layout viewport, which ends at the toolbar's top edge, while the
 * page itself keeps painting beneath the toolbar - so a fixed backdrop leaves a strip of live page
 * content showing under it. This renders a document-anchored (absolute, portalled to <body> so no
 * fixed ancestor becomes its containing block) strip starting where the layout viewport ends.
 * Position is captured on mount; callers should mount it only while the overlay is open, when
 * scrolling is locked (see useBodyScrollLock).
 */
export function UnderToolbarFill({ className, zIndex = 50 }: UnderToolbarFillProps) {
    const [top] = useState(() => window.scrollY + window.innerHeight);
    return createPortal(
        <div
            aria-hidden="true"
            className={`absolute h-[50vh] pointer-events-none ${className}`}
            style={{ top, zIndex }}
        />,
        document.body,
    );
}
