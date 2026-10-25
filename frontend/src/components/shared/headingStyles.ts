/**
 * @fileoverview Class strings for the three heading levels (see `Heading.tsx` and frontend/DESIGN.md).
 * Component-free so `Heading.tsx` stays Fast-Refresh-friendly and elements that can't be a
 * `<Heading>` (e.g. a title inside a button) can share the exact classes.
 */
export type HeadingLevel = 'page' | 'section' | 'panel';

const LEVEL_CLASSES: Record<HeadingLevel, string> = {
    page: 'font-display uppercase text-[28px] leading-none',
    section: 'font-display uppercase text-xl leading-none',
    panel: 'font-display-upright uppercase text-[15px] leading-5',
};

export function headingClass(level: HeadingLevel): string {
    return `${LEVEL_CLASSES[level]} text-(--text-primary)`;
}
