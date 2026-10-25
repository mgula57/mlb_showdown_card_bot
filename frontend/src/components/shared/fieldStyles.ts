/**
 * @fileoverview The one look for form fields: text inputs, selects and the compact filter
 * dropdowns (see frontend/DESIGN.md). A flat surface with a hairline that darkens on hover and
 * turns navy on focus, in the 4px control corner. Kept component-free so `FormInput`,
 * `CustomSelect` and any one-off field share the exact same classes.
 */
export type FieldSize = 'sm' | 'md' | 'lg';

const SIZE_CLASSES: Record<FieldSize, string> = {
    sm: 'h-8 px-2.5 text-[12px]',
    md: 'h-10 px-3 text-sm',
    /** The card search toolbar row, next to the 44px search frame */
    lg: 'h-11 px-3 text-sm',
};

/** Label above a field, toggle group or picker: small semibold caps, lightly spaced, in the
 *  tertiary ink, like the ON-BASE / SPEED labels on the card front. Body face, never display. */
export const FIELD_LABEL_CLASS = 'block text-[11px] font-semibold uppercase tracking-[0.08em] leading-4 text-(--text-tertiary)';

/** Border, surface and states only, for wrappers that size themselves (e.g. an input row). */
export const FIELD_FRAME_CLASS =
    'rounded-control border border-(--divider) bg-(--background-secondary) text-(--text-primary) ' +
    'hover:border-(--rule-strong) focus-within:border-(--showdown-blue) transition-colors';

export function fieldClass(size: FieldSize = 'md', className = ''): string {
    return `${FIELD_FRAME_CLASS} ${SIZE_CLASSES[size]} disabled:opacity-40 disabled:cursor-not-allowed ${className}`;
}
