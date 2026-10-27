import { createContext, useContext, useLayoutEffect } from 'react';

/** The enclosing panel's (an untitled `Modal`, the card search sidebar) close action, for content that
 * puts its own close button in its header row (`CardDetail`). `claim` tells the panel to hide its own
 * floating close button while the content is mounted. Kept component-free so component files stay
 * Fast-Refresh-friendly. */
export type PanelClose = {
    onClose: () => void;
    /** Returns the release function. */
    claim: () => () => void;
};

export const PanelCloseContext = createContext<PanelClose | null>(null);

/** Claims the enclosing panel's close button and returns its close action (undefined outside a panel).
 * Layout effect, so the panel's floating button never flashes in beside the claimed one. */
export function usePanelClose(): (() => void) | undefined {
    const panelClose = useContext(PanelCloseContext);
    useLayoutEffect(() => panelClose?.claim(), [panelClose]);
    return panelClose?.onClose;
}
