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

/** The field label's type without its color or `block`, for group labels that carry a status
 *  color (green "Overperformers") or sit inline in a row. */
export const CAPS_LABEL_CLASS = 'text-[11px] font-semibold uppercase tracking-[0.08em] leading-4';

/** A label inside a small field, before its value ("Sort Points", "Positions All", a filter chip's
 *  "Small Samples? No"): semibold in the tertiary ink, same size as the field's text. */
export const INLINE_FIELD_LABEL_CLASS = 'font-semibold text-(--text-tertiary) whitespace-nowrap';

/** Border, surface and states only, for wrappers that size themselves (e.g. an input row). */
export const FIELD_FRAME_CLASS =
    'rounded-control border border-(--divider) bg-(--background-secondary) text-(--text-primary) ' +
    'hover:border-(--rule-strong) focus-within:border-(--showdown-blue) transition-colors';

/** The square checklist box (`FormEnabler`, `MultiSelect` options): empty with a strong rule when
 *  off, navy with a white check when on. The caller adds the size (`w-4 h-4 text-[9px]`). */
export function checkBoxClass(checked: boolean): string {
    return `shrink-0 flex items-center justify-center rounded-plate border-2 transition-colors ${
        checked ? 'bg-(--showdown-blue-fill) border-(--showdown-blue) text-white' : 'border-(--rule-strong)'
    }`;
}

export function fieldClass(size: FieldSize = 'md', className = ''): string {
    return `${FIELD_FRAME_CLASS} ${SIZE_CLASSES[size]} disabled:opacity-40 disabled:cursor-not-allowed ${className}`;
}
