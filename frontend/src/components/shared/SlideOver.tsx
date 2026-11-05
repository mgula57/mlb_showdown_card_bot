import { useEffect } from 'react';
import { FaCaretDown } from 'react-icons/fa6';
import { FloatingActionButton, type FloatingSide } from './FloatingActionButton';
import { Heading } from './Heading';
import { useBodyScrollLock } from '../../hooks/useBodyScrollLock';
import { UnderToolbarFill } from './UnderToolbarFill';

type SlideOverProps = {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
    /**
     * Optional element rendered below the title, inside the panel's fixed header
     * (not part of the scrollable content).
     */
    handleContent?: React.ReactNode;
    /** Corner for the floating dismiss button - match the button that opened the panel. */
    dismissSide?: FloatingSide;
};

/**
 * Full-height mobile slideover: hidden until triggered, then slides up from the
 * bottom over a flat scrim. Unlike BottomSheet there's no drag
 * gesture or peek snap point — it's either open (~90% of the screen) or closed.
 * Dismiss via the backdrop or the floating circular button in a bottom corner
 * (right unless `dismissSide` says otherwise). Hidden on lg+ (use the desktop panel instead).
 */
export function SlideOver({ isOpen, onClose, title, children, handleContent, dismissSide = 'right' }: SlideOverProps) {
    // Lock the background while open: overflow lock for scrolling, plus cutting pointer-events to
    // everything except the panel/backdrop themselves.
    useBodyScrollLock(isOpen);
    useEffect(() => {
        if (!isOpen) return;
        const body = document.body;
        const prev = body.style.pointerEvents;
        body.style.pointerEvents = 'none';
        return () => { body.style.pointerEvents = prev; };
    }, [isOpen]);

    return (
        <>
            {/* Backdrop — the same flat scrim as Modal; height uses the large viewport (lvh) so it
                bleeds under Safari mobile's translucent URL bar instead of leaving a gap. */}
            <div
                className={`
                    lg:hidden fixed top-0 left-0 right-0 h-lvh z-40
                    bg-black/50
                    transition-opacity duration-300
                    ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
                `}
                onClick={onClose}
            />
            {isOpen && <UnderToolbarFill zIndex={40} className="left-0 w-full bg-black/50 lg:hidden" />}

            {/* Panel — slides up from fully off-screen. Height uses lvh (same reasoning as
                the backdrop) rather than dvh so it never exposes a gap at the bottom edge
                as Safari's URL bar animates. */}
            <div
                className={`
                    lg:hidden fixed bottom-0 left-0 right-0 z-49
                    bg-(--background-primary) rounded-t-card flex flex-col
                    shadow-sheet border-t border-(--divider)
                    transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)]
                    ${isOpen ? 'translate-y-0 pointer-events-auto' : 'translate-y-full pointer-events-none'}
                `}
                style={{ height: '90lvh' }}
            >
                {(title || handleContent) && (
                    <div className="flex flex-col items-center pt-3 pb-1 shrink-0">
                        {title && <Heading level="section">{title}</Heading>}
                        {handleContent && <div className="w-full mt-2">{handleContent}</div>}
                    </div>
                )}

                <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain">
                    {children}
                </div>
            </div>

            {/* Floating circular dismiss button, in the same corner as the button that opened the panel */}
            {isOpen && (
                <FloatingActionButton side={dismissSide}>
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close"
                        className="
                            pointer-events-auto
                            w-12 h-12 rounded-full flex items-center justify-center
                            bg-(--showdown-red-fill) text-white
                            shadow-overlay
                            cursor-pointer hover:opacity-90 transition-opacity
                        "
                    >
                        <FaCaretDown className="text-[24px]" />
                    </button>
                </FloatingActionButton>
            )}
        </>
    );
}
