import type { ReactNode } from 'react';
import { FaChevronRight } from 'react-icons/fa6';

type TeamShelfProps = {
    title: string;
    subtitle?: string;
    /** Optional "See all" affordance shown on the right of the header. */
    onSeeAll?: () => void;
    children: ReactNode;
};

/** A titled, horizontally-scrolling row of team tiles — the music-app "shelf" pattern. */
export function TeamShelf({ title, subtitle, onSeeAll, children }: TeamShelfProps) {
    return (
        <section className="flex flex-col">
            <div className="flex items-baseline justify-between px-4 mb-1.5">
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
                className="flex gap-3 overflow-y-hidden overflow-x-scroll pb-1 py-2 px-4 scrollbar-hide"
                style={{ touchAction: 'pan-x' }}
            >
                {children}
            </div>
        </section>
    );
}

export default TeamShelf;
