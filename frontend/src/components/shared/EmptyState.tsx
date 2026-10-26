import type { ReactNode } from 'react';

export type EmptyStateSize = 'page' | 'panel' | 'inline';

const SIZE_CLASSES: Record<EmptyStateSize, { container: string; title: string; body: string }> = {
    /** A screen or tab with nothing in it yet. */
    page: { container: 'py-14 px-4 gap-3', title: 'text-[28px] sm:text-[32px]', body: 'text-sm max-w-md' },
    /** An empty section inside a page. */
    panel: { container: 'py-8 px-4 gap-2', title: 'text-xl', body: 'text-[13px] max-w-sm' },
    /** One quiet line: a search with no matches, a panel with no data. */
    inline: { container: 'py-6 px-2', title: '', body: 'text-[13px] max-w-md' },
};

type EmptyStateProps = {
    /** The slab headline, in the voice of the 2000 print ads: short caps ending in a period ("NO TEAMS YET."). Ignored by `inline`. */
    title?: string;
    /** One plain line under the headline (or the whole message, for `inline`). */
    children?: ReactNode;
    /** The next step, usually a `buttonClass('primary')` button or link. */
    action?: ReactNode;
    size?: EmptyStateSize;
    className?: string;
};

/** What a screen shows when there's nothing in it yet (see frontend/DESIGN.md, "Empty states"). */
export function EmptyState({ title, children, action, size = 'page', className = '' }: EmptyStateProps) {
    const classes = SIZE_CLASSES[size];
    return (
        <div className={`flex flex-col items-center text-center ${classes.container} ${className}`}>
            {title && size !== 'inline' && (
                <p className={`font-slab uppercase leading-none text-balance text-(--text-primary) ${classes.title}`}>{title}</p>
            )}
            {children && <div className={`text-(--text-tertiary) leading-snug ${classes.body}`}>{children}</div>}
            {action && <div className="mt-2 flex flex-wrap justify-center gap-2">{action}</div>}
        </div>
    );
}

export default EmptyState;
