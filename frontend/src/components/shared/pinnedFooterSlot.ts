import { createContext } from 'react';

/** The enclosing `PinnedFooterScrollArea`'s footer element, for `PinnedFooterPortal`. `undefined` =
 * not inside one; `null` = inside one whose footer hasn't mounted yet. Kept component-free so the
 * component files stay Fast-Refresh-friendly. */
export const PinnedFooterSlotContext = createContext<HTMLElement | null | undefined>(undefined);
