import { useEffect, useRef, useState } from 'react';
import { PinnedFooterSlotContext } from './pinnedFooterSlot';

/** Translucent + blurred so the scrolling content bleeds through behind it. */
const FOOTER_LAYER_CLASS = 'border-t border-form-element bg-(--background-primary)/60 backdrop-blur-md p-3';

type PinnedFooterScrollAreaProps = {
    children: React.ReactNode;
    /** Footer content owned by the caller (e.g. a Modal's `footer` buttons), pinned below any
     * content descendants portal in. */
    footer?: React.ReactNode;
    /** Sizes the area, e.g. `flex-1` inside a flex column. */
    className?: string;
};

/** A scrolling content area with translucent footers pinned over its bottom edge: the caller's
 * `footer`, plus a slot descendants fill via `PinnedFooterPortal` (hidden while empty). The content
 * pads by the footers' live height so nothing ends up stuck underneath. */
export default function PinnedFooterScrollArea({ children, footer, className = '' }: PinnedFooterScrollAreaProps) {
    // State rather than a ref, so portaling descendants re-render once the slot mounts
    const [footerSlot, setFooterSlot] = useState<HTMLDivElement | null>(null);
    const footersRef = useRef<HTMLDivElement>(null);
    const [footersHeight, setFootersHeight] = useState(0);
    useEffect(() => {
        const footers = footersRef.current;
        if (!footers) return;
        const observer = new ResizeObserver(() => setFootersHeight(footers.offsetHeight));
        observer.observe(footers);
        return () => observer.disconnect();
    }, []);

    return (
        <div className={`relative min-h-0 flex flex-col ${className}`}>
            <div className="flex-1 min-h-0 overflow-y-auto" style={footersHeight ? { paddingBottom: footersHeight } : undefined}>
                <PinnedFooterSlotContext.Provider value={footerSlot}>
                    {children}
                </PinnedFooterSlotContext.Provider>
            </div>
            <div ref={footersRef} className="absolute inset-x-0 bottom-0 z-10 flex flex-col">
                <div ref={setFooterSlot} className={`empty:hidden flex items-center justify-end gap-2 ${FOOTER_LAYER_CLASS}`} />
                {footer && (
                    <div className={`flex flex-col gap-2 ${FOOTER_LAYER_CLASS}`}>
                        {footer}
                    </div>
                )}
            </div>
        </div>
    );
}
