import type { ReactNode } from 'react';
import { FrameCorners } from './FrameCorners';

type FramedTileProps = {
    children: ReactNode;
    /** Leave out for a display-only tile. */
    onClick?: () => void;
    /** Width and height or aspect ratio. */
    className?: string;
};

/**
 * The feature tile frame from the 2001 card back (see frontend/DESIGN.md, "Frames"): the double rule
 * with a base on each corner, pressable when it has an `onClick`. It's a Tailwind `group`, so
 * children can react to its hover, and its contents stack in a clipped column.
 */
export function FramedTile({ children, onClick, className = '' }: FramedTileProps) {
    const Frame = onClick ? 'button' : 'div';
    return (
        <Frame
            {...(onClick ? { type: 'button' as const, onClick } : {})}
            className={`
                ${className} group relative p-0.75 text-left rounded-trading-card
                border-2 border-(--rule-strong) bg-(--background-secondary)
                ${onClick ? `
                    [@media(hover:hover)]:hover:scale-[1.025] [@media(hover:hover)]:active:scale-[0.975]
                    [@media(hover:hover)]:transition-transform [@media(hover:hover)]:duration-150
                    cursor-pointer
                ` : ''}
            `}
        >
            <FrameCorners />
            <div className="relative h-full flex flex-col overflow-hidden rounded-card border border-(--divider)">
                {children}
            </div>
        </Frame>
    );
}

export default FramedTile;
