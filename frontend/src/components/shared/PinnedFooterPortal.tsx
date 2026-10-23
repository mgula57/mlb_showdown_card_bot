import { useContext } from 'react';
import { createPortal } from 'react-dom';
import { PinnedFooterSlotContext } from './pinnedFooterSlot';

/** Renders `children` in the enclosing `PinnedFooterScrollArea`'s footer (a Modal's body, the card
 * detail sidebar), pinned below the scrolling content — e.g. a card's action buttons, so they stay
 * reachable while the detail scrolls. Outside one, the children render in place instead. */
export default function PinnedFooterPortal({ children }: { children: React.ReactNode }) {
    const slot = useContext(PinnedFooterSlotContext);
    if (slot === undefined) return <>{children}</>;
    if (slot === null) return null;
    return createPortal(children, slot);
}
