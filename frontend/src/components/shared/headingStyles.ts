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

/** Room on the right for the italic display face, which leans past its own box; without it an
 *  `overflow: hidden` edge (truncate, line-clamp) shaves the last letter. */
export const SLANT_ROOM_CLASS = 'pr-[0.12em]';

export function headingClass(level: HeadingLevel): string {
    return `${LEVEL_CLASSES[level]} text-(--text-primary)`;
}
