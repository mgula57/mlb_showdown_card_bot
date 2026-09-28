import { useEffect } from 'react';
import { FaCaretDown } from 'react-icons/fa6';

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
};

/**
 * Full-height mobile slideover: hidden until triggered, then slides up from the
 * bottom over a blurred/translucent backdrop. Unlike BottomSheet there's no drag
 * gesture or peek snap point — it's either open (~90% of the screen) or closed.
 * Dismiss via the backdrop or the floating circular button in the bottom-right
 * corner. Hidden on lg+ (use the desktop panel instead).
 */
export function SlideOver({ isOpen, onClose, title, children, handleContent }: SlideOverProps) {
    // Lock the background while open, same reasoning as BottomSheet's expanded lock:
    // `overflow: hidden` alone isn't reliable on mobile Safari, so pin the body and
    // cut pointer-events to everything except the panel/backdrop themselves.
    useEffect(() => {
        if (!isOpen) return;
        const scrollY = window.scrollY;
        const body = document.body;
        const prev = { position: body.style.position, top: body.style.top, width: body.style.width, overflow: body.style.overflow, pointerEvents: body.style.pointerEvents };
        body.style.position = 'fixed';
        body.style.top = `-${scrollY}px`;
        body.style.width = '100%';
        body.style.overflow = 'hidden';
        body.style.pointerEvents = 'none';
        return () => {
            body.style.position = prev.position;
            body.style.top = prev.top;
            body.style.width = prev.width;
            body.style.overflow = prev.overflow;
            body.style.pointerEvents = prev.pointerEvents;
            window.scrollTo(0, scrollY);
        };
    }, [isOpen]);

    return (
        <>
            {/* Backdrop — blurred + translucent, height uses the large viewport (lvh) so it
                bleeds under Safari mobile's translucent URL bar instead of leaving a gap. */}
            <div
                className={`
                    lg:hidden fixed top-0 left-0 right-0 h-lvh z-40
                    bg-black/40 backdrop-blur-md
                    transition-opacity duration-300
                    ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
                `}
                onClick={onClose}
            />

            {/* Panel — slides up from fully off-screen. Height uses lvh (same reasoning as
                the backdrop) rather than dvh so it never exposes a gap at the bottom edge
                as Safari's URL bar animates. */}
            <div
                className={`
                    lg:hidden fixed bottom-0 left-0 right-0 z-49
                    bg-(--background-primary) rounded-t-2xl flex flex-col
                    shadow-[0_-8px_30px_rgba(0,0,0,0.18)] border-t border-(--divider)
                    transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)]
                    ${isOpen ? 'translate-y-0 pointer-events-auto' : 'translate-y-full pointer-events-none'}
                `}
                style={{ height: '90lvh' }}
            >
                {(title || handleContent) && (
                    <div className="flex flex-col items-center pt-3 pb-1 shrink-0">
                        {title && <div className="text-[13px] font-bold text-(--text-primary)">{title}</div>}
                        {handleContent && <div className="w-full mt-2">{handleContent}</div>}
                    </div>
                )}

                <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain">
                    {children}
                </div>
            </div>

            {/* Floating circular dismiss button, bottom-right of the screen. A larger halo sits
                behind it so the button stays legible over busy scrolling content (e.g. a wall
                of card results) — both its blur and its tint feather out via a radial mask
                rather than cutting off in a hard circle, so it reads as a soft glow rather than
                a visible disc. */}
            {isOpen && (
                <div
                    className="lg:hidden fixed bottom-0 right-0 z-50 w-24 h-24 flex items-center justify-center pointer-events-none"
                    style={{
                        background: 'radial-gradient(circle, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.2) 40%, rgba(0,0,0,0) 72%)',
                        backdropFilter: 'blur(16px)',
                        WebkitBackdropFilter: 'blur(16px)',
                        maskImage: 'radial-gradient(circle, black 40%, transparent 72%)',
                        WebkitMaskImage: 'radial-gradient(circle, black 40%, transparent 72%)',
                    }}
                >
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close"
                        className="
                            pointer-events-auto
                            w-12 h-12 rounded-full flex items-center justify-center
                            bg-(--showdown-red) text-white
                            shadow-lg
                            cursor-pointer hover:opacity-90 transition-opacity
                        "
                    >
                        <FaCaretDown className="text-[24px]" />
                    </button>
                </div>
            )}
        </>
    );
}
