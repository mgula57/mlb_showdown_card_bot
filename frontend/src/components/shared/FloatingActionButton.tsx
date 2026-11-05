import type { ReactNode } from 'react';

export type FloatingSide = 'left' | 'right';

/**
 * Mobile-only floating button slot in a bottom corner of the screen (right by default). Give the
 * child button `shadow-overlay` so it stays legible over busy scrolling content (e.g. a wall of
 * card results).
 *
 * The slot ignores pointer events; give the child `pointer-events-auto`.
 */
export function FloatingActionButton({ children, side = 'right', hideAt = 'lg' }: {
    children: ReactNode;
    side?: FloatingSide;
    /** Breakpoint at which the slot hides (the desktop layout takes over) - `lg` by default, or
     *  `split` for pages that switch to side-by-side at `--breakpoint-split`. */
    hideAt?: 'lg' | 'split';
}) {
    return (
        <div className={`${hideAt === 'split' ? 'split:hidden' : 'lg:hidden'} fixed bottom-0 ${side === 'left' ? 'left-0' : 'right-0'} z-50 w-24 h-24 flex items-center justify-center pointer-events-none`}>
            {children}
        </div>
    );
}
