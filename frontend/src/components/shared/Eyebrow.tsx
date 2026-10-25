import type { ReactNode } from 'react';

/**
 * Small, widely spaced caps above a title — the "M L B   S H O W D O W N" treatment from the card
 * header. Labels a section or gives context ("Edition 2 of 3 · 2001 Set"); never body copy.
 */
export function Eyebrow({ children, className = '' }: { children: ReactNode; className?: string }) {
    return (
        <span className={`font-display text-xs uppercase tracking-[0.42em] text-(--text-tertiary) ${className}`}>
            {children}
        </span>
    );
}

export default Eyebrow;
