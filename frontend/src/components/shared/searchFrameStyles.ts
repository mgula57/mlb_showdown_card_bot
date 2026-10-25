/**
 * @fileoverview Class string for the frame around every search field and search button: a 2px
 * navy-to-red gradient border, the one gradient the design language allows (see
 * frontend/DESIGN.md). The framed child paints its own background with a slightly smaller radius.
 * Kept in a component-free module so `SearchFrame.tsx` stays Fast-Refresh-friendly and
 * `FormInput` can share it.
 */
export function searchFrameClass(rounded = 'rounded-card'): string {
    // design-ok: the search frame is the sanctioned brand gradient
    return `bg-linear-to-r from-(--showdown-blue) to-(--showdown-red) p-0.5 ${rounded}`;
}
