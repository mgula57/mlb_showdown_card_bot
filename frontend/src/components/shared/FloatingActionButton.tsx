import type { ReactNode } from 'react';

export type FloatingSide = 'left' | 'right';

/**
 * Mobile-only floating button slot in a bottom corner of the screen (right by default). A larger halo sits
 * behind the button so it stays legible over busy scrolling content (e.g. a wall of card
 * results) — both its blur and its tint feather out via a radial mask rather than cutting off
 * in a hard circle, so it reads as a soft glow rather than a visible disc.
 *
 * The halo ignores pointer events; give the child `pointer-events-auto`.
 */
export function FloatingActionButton({ children, side = 'right' }: { children: ReactNode; side?: FloatingSide }) {
    return (
        <div
            className={`lg:hidden fixed bottom-0 ${side === 'left' ? 'left-0' : 'right-0'} z-50 w-24 h-24 flex items-center justify-center pointer-events-none`}
            style={{
                background: 'radial-gradient(circle, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.2) 40%, rgba(0,0,0,0) 72%)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                maskImage: 'radial-gradient(circle, black 40%, transparent 72%)',
                WebkitMaskImage: 'radial-gradient(circle, black 40%, transparent 72%)',
            }}
        >
            {children}
        </div>
    );
}
