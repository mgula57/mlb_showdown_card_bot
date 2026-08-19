import { useEffect, useRef, useState } from 'react';

export type SnapPoint = 'closed' | 'peek' | 'expanded';

type BottomSheetProps = {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
    /**
     * When false the sheet can never be fully dismissed — dragging below peek
     * bounces back, and the backdrop (shown only when expanded) collapses to peek
     * instead of closing. Defaults to true.
     */
    dismissible?: boolean;
    /**
     * Change this value (e.g. pass a new object/id) to force the sheet to snap
     * to 'expanded' — used to spring the sheet open when a new slot is picked.
     */
    expandTrigger?: unknown;
    /**
     * Optional element rendered inside the drag handle, below the grabber bar
     * (and title, if any). Shares the handle's drag behavior.
     */
    handleContent?: React.ReactNode;
    /** Called whenever the sheet settles on a snap point — e.g. to swap in a bigger
     * `handleContent` only once the sheet is actually expanded. */
    onSnapChange?: (snap: SnapPoint) => void;
};

/**
 * iOS-style bottom sheet with two snap points:
 *   peek     — sheet edge visible at ~40% screen height
 *   expanded — nearly full screen
 * Drag the handle up/down to switch; flick to dismiss.
 * Hidden on lg+ (use the desktop panel instead).
 */
export function BottomSheet({ isOpen, onClose, title, children, dismissible = true, expandTrigger, handleContent, onSnapChange }: BottomSheetProps) {
    const sheetRef  = useRef<HTMLDivElement>(null);
    const handleRef = useRef<HTMLDivElement>(null);
    const contentRef = useRef<HTMLDivElement>(null);
    const snapRef   = useRef<SnapPoint>('closed');
    const [snapState, setSnapState] = useState<SnapPoint>('closed');

    // Drag state — all mutable, no re-renders during gesture
    const isDragging        = useRef(false);
    const touchMoved        = useRef(false); // true once finger moves >8px (distinguishes tap from drag)
    const startY            = useRef(0);
    const startTranslatePx  = useRef(0);
    const lastY             = useRef(0);
    const lastTime          = useRef(0);
    const velocity          = useRef(0); // px/ms, positive = downward
    // Timestamp of the last real touch interaction. Browsers replay a synthetic
    // mousedown/mouseup ~300ms after a touchend for mouse-only-code compatibility;
    // without this guard that replay re-triggers handleMouseDown and immediately
    // undoes the tap's snap change.
    const lastTouchTime     = useRef(0);

    // ----------------------------------------------------------------
    // Snap helpers
    // ----------------------------------------------------------------

    function sheetH(): number {
        return sheetRef.current?.offsetHeight ?? window.innerHeight * 0.9;
    }

    function snapPx(point: SnapPoint): number {
        const h = sheetH();
        switch (point) {
            case 'expanded': return h * 0.1; // leave ~10% visible above the sheet
            // dismissible=false: only show the handle + a small peek (~18% of screen)
            // dismissible=true:  show ~40% of the sheet
            case 'peek':     return dismissible ? h * 0.58 : h * 0.82;
            case 'closed':   return h;
        }
    }

    function currentTranslatePx(): number {
        const sheet = sheetRef.current;
        if (!sheet) return snapPx('closed');
        // DOMMatrix gives the computed pixel value even for % transforms
        return new DOMMatrix(getComputedStyle(sheet).transform).m42;
    }

    function snapTo(point: SnapPoint, animate = true) {
        const sheet = sheetRef.current;
        if (!sheet) return;
        snapRef.current = point;
        setSnapState(point);
        onSnapChange?.(point);
        const px = snapPx(point);
        if (animate) {
            sheet.style.transition = 'transform 0.35s cubic-bezier(0.32, 0.72, 0, 1)';
            setTimeout(() => {
                if (sheetRef.current) sheetRef.current.style.transition = '';
            }, 350);
        }
        sheet.style.transform = `translateY(${px}px)`;
    }

    // ----------------------------------------------------------------
    // Respond to isOpen prop
    // ----------------------------------------------------------------

    useEffect(() => {
        if (isOpen) {
            snapTo('peek');
        } else if (snapRef.current !== 'closed') {
            snapTo('closed');
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isOpen]);

    // Spring the sheet open whenever a new slot is picked
    useEffect(() => {
        if (expandTrigger === undefined || expandTrigger === null) return;
        snapTo('expanded');
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [expandTrigger]);

    // Lock the background only when fully expanded — a peeking sheet only
    // covers part of the screen, and the underlying view should stay
    // scrollable/tappable wherever the touch isn't actually on the sheet
    // (that part is handled by the sheet's own non-passive touch listeners
    // below). Once expanded the sheet is meant to be fully modal, so on top
    // of pinning body scroll (`overflow: hidden` alone isn't reliable on
    // mobile Safari), also cut pointer-events to everything except the sheet
    // and backdrop themselves — this is the one guarantee that no tap can
    // ever reach whatever's behind it, regardless of z-index/layout quirks
    // in whatever page happens to be rendered underneath.
    useEffect(() => {
        if (snapState !== 'expanded') return;
        const sheet = sheetRef.current;
        const scrollY = window.scrollY;
        const body = document.body;
        const prev = { position: body.style.position, top: body.style.top, width: body.style.width, overflow: body.style.overflow, pointerEvents: body.style.pointerEvents };
        body.style.position = 'fixed';
        body.style.top = `-${scrollY}px`;
        body.style.width = '100%';
        body.style.overflow = 'hidden';
        body.style.pointerEvents = 'none';
        if (sheet) sheet.style.pointerEvents = 'auto';
        return () => {
            body.style.position = prev.position;
            body.style.top = prev.top;
            body.style.width = prev.width;
            body.style.overflow = prev.overflow;
            body.style.pointerEvents = prev.pointerEvents;
            if (sheet) sheet.style.pointerEvents = '';
            window.scrollTo(0, scrollY);
        };
    }, [snapState]);

    // ----------------------------------------------------------------
    // Shared drag logic (used by both touch and mouse handlers)
    // ----------------------------------------------------------------

    function startDrag(clientY: number) {
        isDragging.current       = true;
        touchMoved.current       = false;
        startY.current           = clientY;
        lastY.current            = clientY;
        lastTime.current         = Date.now();
        velocity.current         = 0;
        startTranslatePx.current = currentTranslatePx();
        if (sheetRef.current) sheetRef.current.style.transition = 'none';
    }

    function moveDrag(clientY: number) {
        if (!isDragging.current || !sheetRef.current) return;
        const delta = clientY - startY.current;
        if (Math.abs(delta) > 8) touchMoved.current = true;
        const clamped = Math.max(-24, startTranslatePx.current + delta);
        sheetRef.current.style.transform = `translateY(${clamped}px)`;

        const now = Date.now();
        const dt  = now - lastTime.current;
        if (dt > 0) velocity.current = (clientY - lastY.current) / dt;
        lastY.current    = clientY;
        lastTime.current = now;
    }

    function endDrag() {
        if (!isDragging.current) return;
        isDragging.current = false;

        // Tap/click on handle: toggle between expanded and peek
        if (!touchMoved.current) {
            if (sheetRef.current) sheetRef.current.style.transition = '';
            snapTo(snapRef.current === 'expanded' ? 'peek' : 'expanded');
            return;
        }

        const current = currentTranslatePx();
        const h       = sheetH();
        const pct     = current / h;
        const vel     = velocity.current;
        const isFlick = Math.abs(vel) > 0.3;

        let target: SnapPoint;
        if (isFlick) {
            target = vel < 0 ? 'expanded' : (snapRef.current === 'expanded' ? 'peek' : 'closed');
        } else {
            if (pct < 0.3)      target = 'expanded';
            else if (pct < 0.8) target = 'peek';
            else                target = 'closed';
        }

        if (target === 'closed') {
            if (dismissible) { snapTo('closed'); onClose(); }
            else              { snapTo('peek'); }
        } else {
            snapTo(target);
        }
    }

    // ----------------------------------------------------------------
    // Touch handlers — attached as real (non-passive) DOM listeners rather
    // than JSX props. React registers its synthetic touchmove listener as
    // passive, so calling preventDefault() from a JSX onTouchMove is a no-op;
    // without it, iOS Safari can scroll-chain the drag into whatever's behind
    // the sheet even though `touch-none` is set. A raw listener with
    // `{ passive: false }` lets preventDefault actually block that.
    // ----------------------------------------------------------------

    function attachDragTouchListeners(el: HTMLElement | null) {
        if (!el) return () => {};
        const onTouchStart = (e: TouchEvent) => { lastTouchTime.current = Date.now(); startDrag(e.touches[0].clientY); };
        const onTouchMove  = (e: TouchEvent) => { e.preventDefault(); moveDrag(e.touches[0].clientY); };
        const onTouchEnd   = () => endDrag();
        el.addEventListener('touchstart', onTouchStart, { passive: true });
        el.addEventListener('touchmove', onTouchMove, { passive: false });
        el.addEventListener('touchend', onTouchEnd);
        el.addEventListener('touchcancel', onTouchEnd);
        return () => {
            el.removeEventListener('touchstart', onTouchStart);
            el.removeEventListener('touchmove', onTouchMove);
            el.removeEventListener('touchend', onTouchEnd);
            el.removeEventListener('touchcancel', onTouchEnd);
        };
    }

    // The handle always drags, regardless of snap state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => attachDragTouchListeners(handleRef.current), []);

    // The content area only drags while collapsed (peek); once expanded it's
    // a normal scroll surface, so we detach the drag listeners entirely.
    useEffect(() => {
        if (snapState === 'expanded') return;
        return attachDragTouchListeners(contentRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [snapState]);

    // ----------------------------------------------------------------
    // Mouse handlers — mousedown on handle, move/up on document
    // ----------------------------------------------------------------

    const handleMouseDown = (e: React.MouseEvent) => {
        // Ignore synthetic mousedown replayed by the browser shortly after a real
        // touch tap — otherwise it re-triggers the drag/toggle a second time and
        // immediately reverses whatever the touch just did.
        if (Date.now() - lastTouchTime.current < 500) return;
        e.preventDefault();
        startDrag(e.clientY);

        const onMove = (ev: MouseEvent) => moveDrag(ev.clientY);
        const onUp   = () => {
            endDrag();
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    };

    // ----------------------------------------------------------------
    // Render
    // ----------------------------------------------------------------

    const visible = snapState !== 'closed';
    // Non-dismissible sheets only show a backdrop when expanded (to signal they cover content)
    const backdropVisible = dismissible ? visible : snapState === 'expanded';

    return (
        <>
            {/* Backdrop — height uses the large viewport (lvh) rather than inset-0's
                visual-viewport sizing so it overshoots the visible area and bleeds
                under Safari mobile's translucent URL bar instead of leaving a gap. */}
            <div
                className={`
                    lg:hidden fixed top-0 left-0 right-0 h-lvh bg-black/50 z-40
                    transition-opacity duration-300
                    ${backdropVisible ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
                `}
                onClick={() => {
                    if (dismissible) {
                        onClose();
                    } else {
                        snapTo('peek');
                        onClose(); // clears external context (e.g. pendingSlot) without closing
                    }
                }}
            />

            {/* Sheet — starts off-screen; JS drives all position changes. Height uses
                lvh (large viewport, same reasoning as the backdrop above) rather than
                dvh — dvh shrinks/grows live as Safari's URL bar animates, and a
                bottom-anchored element sized off it can lag a frame behind, exposing
                a gap (rendered as a black bar) at the bottom edge. lvh never changes,
                so the sheet always overshoots downward and bleeds under the URL bar
                instead of leaving a gap. */}
            <div
                ref={sheetRef}
                className="lg:hidden fixed bottom-0 left-0 right-0 z-49 bg-(--background-primary) rounded-t-2xl flex flex-col shadow-[0_-8px_30px_rgba(0,0,0,0.18)] border-t border-(--divider)"
                style={{ height: '90lvh', transform: 'translateY(100%)', willChange: 'transform' }}
            >
                {/* Drag handle */}
                <div
                    ref={handleRef}
                    className="flex flex-col items-center pt-3 pb-1 shrink-0 touch-none select-none cursor-grab active:cursor-grabbing"
                    onMouseDown={handleMouseDown}
                >
                    <div className="w-10 h-1 rounded-full bg-(--divider)" />
                    {title && (
                        <div className="text-[13px] font-bold text-(--text-primary) mt-2">{title}</div>
                    )}
                    {handleContent && (
                        <div className="w-full mt-2">{handleContent}</div>
                    )}
                </div>

                {/* Content — scrollable only when expanded so drag doesn't fight scroll.
                    While collapsed (peek/closed) it also acts as a drag handle so a
                    swipe anywhere on the sheet — not just the tiny handle — opens it. */}
                <div
                    ref={contentRef}
                    className={`flex-1 min-h-0 ${
                        snapState === 'expanded' ? 'overflow-y-auto overscroll-contain' : 'overflow-hidden touch-none select-none'
                    }`}
                    {...(snapState !== 'expanded' ? { onMouseDown: handleMouseDown } : {})}
                >
                    {children}
                </div>
            </div>
        </>
    );
}
