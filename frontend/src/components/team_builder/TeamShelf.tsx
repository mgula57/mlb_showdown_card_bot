import type { ReactNode } from 'react';
import { FaChevronRight } from 'react-icons/fa6';

type TeamShelfProps = {
    title: string;
    subtitle?: string;
    className?: string;
    /** Optional "See all" affordance shown on the right of the header. */
    onSeeAll?: () => void;
    /**
     * Let the scrolling row run flush to the right edge of the nearest `@container`
     * ancestor (the full content region), ignoring the page's centered max-width and
     * right padding. The header keeps its normal alignment.
     */
    bleedRight?: boolean;
    children: ReactNode;
};

/** A titled, horizontally-scrolling row of team tiles — the music-app "shelf" pattern. */
export function TeamShelf({ title, subtitle, onSeeAll, children, className, bleedRight }: TeamShelfProps) {
    return (
        <section className="flex flex-col">
            <div className={`flex items-baseline justify-between mb-1.5 ${className ?? ''}`}>
                <div className="flex items-baseline gap-2 min-w-0">
                    <h3 className="text-[15px] font-black text-(--text-primary) truncate">{title}</h3>
                    {subtitle && <span className="text-[11px] text-(--text-tertiary) shrink-0">{subtitle}</span>}
                </div>
                {onSeeAll && (
                    <button
                        type="button"
                        onClick={onSeeAll}
                        className="flex items-center gap-1 text-[11px] font-bold text-(--text-secondary) hover:text-(--text-primary) cursor-pointer shrink-0"
                    >
                        See all <FaChevronRight className="text-[9px]" />
                    </button>
                )}
            </div>
            <div
                className={`flex gap-3 overflow-y-hidden overflow-x-scroll pb-1 py-2 scrollbar-hide ${className ?? ''}`}
                style={{
                    // No explicit `touch-action` — the native overflow scroller detects drag
                    // direction on its own. Forcing `pan-x` here swallowed vertical swipes that
                    // began on a tile, so the page couldn't scroll from over the shelf.
                    WebkitOverflowScrolling: 'touch',
                    overscrollBehaviorX: 'contain',
                    // Keep the left inset (from `className`) but drop the right one and pull the
                    // row out to the container edge so it reaches the end of the screen.
                    ...(bleedRight ? { paddingRight: 0, marginRight: 'calc((100% - 100cqw) / 2)' } : {}),
                }}
            >
                {children}
            </div>
        </section>
    );
}

export default TeamShelf;
