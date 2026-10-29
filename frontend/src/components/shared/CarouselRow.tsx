/**
 * @fileoverview A sideways-scrolling row of cards or tiles that bleeds to its container's edges.
 *
 * The row cancels its parent's horizontal padding with negative margins and adds the same amount
 * back as padding inside the scroller. At rest the first item lines up with the rest of the
 * container's content; once scrolled, items run under the container's edges on both sides instead
 * of being clipped at an invisible inner margin. See frontend/DESIGN.md, "Carousels".
 */
import type { ReactNode } from 'react';

/** Which container padding the row bleeds through. Must match the parent's horizontal padding. */
export type CarouselGutter = 'panel' | 'page' | 'ticker' | 'seasonsTab';

const GUTTER_CLASSES: Record<CarouselGutter, string> = {
    // HomePanel and other `p-5` panels
    panel: '-mx-5 px-5',
    // Full-width page containers padded `px-6 md:px-8` (Home)
    page: '-mx-6 px-6 md:-mx-8 md:px-8',
    // Home's Today's Games ticker body, padded `px-4 md:px-6`
    ticker: '-mx-4 px-4 md:-mx-6 md:px-6',
    // Seasons tab content: `px-3` on mobile; on `lg` flush left against the sidebar and flush to the
    // screen's right edge, with the `lg:pr-6` inset the tab's headers use added back at the end
    seasonsTab: '-mx-3 px-3 lg:mx-0 lg:pl-0 lg:pr-6',
};

type CarouselRowProps = {
    children: ReactNode;
    gutter?: CarouselGutter;
    className?: string;
};

export function CarouselRow({ children, gutter = 'panel', className = '' }: CarouselRowProps) {
    return (
        <div className={`flex gap-3 overflow-x-auto scrollbar-hide ${GUTTER_CLASSES[gutter]} ${className}`}>
            {children}
        </div>
    );
}

export default CarouselRow;
