import type { ReactNode } from 'react';

import { useMediaQuery } from '../../hooks/useMediaQuery';
import { SideDrawer } from './SideDrawer';
import { SlideOver } from './SlideOver';

type RightPanelProps = {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    /** Under the title, desktop only. */
    subtitle?: string;
    children: ReactNode;
};

/** A panel that comes in from the right on every screen: a docked `SideDrawer` on desktop (lg+), a
 *  `SlideOver` from the right below it. Stays mounted while closed, so reopening it is instant. */
export function RightPanel({ isOpen, onClose, title, subtitle, children }: RightPanelProps) {
    const isDesktop = useMediaQuery('(min-width: 1024px)');

    if (isDesktop) {
        return (
            <SideDrawer isOpen={isOpen} onClose={onClose} title={title} subtitle={subtitle}>
                <div className="px-4 py-4">{children}</div>
            </SideDrawer>
        );
    }
    return (
        <SlideOver isOpen={isOpen} onClose={onClose} title={title} side="right">
            {/* Room at the bottom for the floating close button */}
            <div className="px-4 pt-2 pb-28">{children}</div>
        </SlideOver>
    );
}
