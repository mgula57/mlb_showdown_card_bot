import { useEffect } from 'react';

// Shared across every overlay so nested ones (e.g. a modal opened from the side menu) only
// apply/release the lock once.
let lockCount = 0;
let prevOverflow = { html: '', body: '' };

/**
 * Locks background scrolling while `active` is true.
 *
 * Uses `overflow: hidden` + `overscroll-behavior: none` on html/body rather than pinning the body
 * with `position: fixed`. Pinning the body leaves the page non-scrollable, and mobile Safari then
 * keeps its bottom toolbar opaque and stops the layout at its top edge, so full-screen overlays
 * ended above it with a bar of page background underneath. Overflow locking keeps the scroll
 * position without touching layout.
 */
export function useBodyScrollLock(active: boolean) {
    useEffect(() => {
        if (!active) return;
        const html = document.documentElement;
        const body = document.body;
        lockCount += 1;
        if (lockCount === 1) {
            prevOverflow = { html: html.style.overflow, body: body.style.overflow };
            html.style.overflow = 'hidden';
            body.style.overflow = 'hidden';
            html.style.overscrollBehavior = 'none';
        }
        return () => {
            lockCount -= 1;
            if (lockCount === 0) {
                html.style.overflow = prevOverflow.html;
                body.style.overflow = prevOverflow.body;
                html.style.overscrollBehavior = '';
            }
        };
    }, [active]);
}
