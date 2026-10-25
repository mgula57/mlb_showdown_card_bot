import type { ReactNode } from 'react';
import { headingClass, type HeadingLevel } from './headingStyles';

const DEFAULT_TAG: Record<HeadingLevel, 'h1' | 'h2' | 'h3'> = { page: 'h1', section: 'h2', panel: 'h3' };

type HeadingProps = {
    level: HeadingLevel;
    children: ReactNode;
    /** Overrides the semantic tag when the outline needs a different level than the look. */
    as?: 'h1' | 'h2' | 'h3' | 'h4' | 'div' | 'span';
    className?: string;
    title?: string;
};

/**
 * Every title in the app (see frontend/DESIGN.md, "Type"). Pick the level by role, not by size:
 *
 * - `page`: the one title at the top of a screen ("My Teams", "Release Builder"). Display italic.
 * - `section`: a standalone headline for a block of the page or a modal ("Card Settings",
 *   "Recent Sims"). Display italic.
 * - `panel`: a title that sits inline with counts, chips or controls, or names an item in a list
 *   (a challenge, a shelf, a form section). Upright condensed, because the italic never sits next
 *   to upright plates.
 *
 * Small spaced group labels above content are `Eyebrow`, not a heading.
 */
export function Heading({ level, children, as, className = '', title }: HeadingProps) {
    const Tag = as ?? DEFAULT_TAG[level];
    return <Tag title={title} className={`${headingClass(level)} ${className}`}>{children}</Tag>;
}

export default Heading;
