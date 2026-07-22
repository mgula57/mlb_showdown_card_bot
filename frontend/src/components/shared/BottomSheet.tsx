import { useEffect, useRef, useState } from 'react';

type SnapPoint = 'closed' | 'peek' | 'expanded';

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
};

/**
 * iOS-style bottom sheet with two snap points:
 *   peek     — sheet edge visible at ~40% screen height
 *   expanded — nearly full screen
 * Drag the handle up/down to switch; flick to dismiss.
 * Hidden on lg+ (use the desktop panel instead).
 */
export function BottomSheet({ isOpen, onClose, title, children, dismissible = true, expandTrigger }: BottomSheetProps) {
    const sheetRef  = useRef<HTMLDivElement>(null);
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

    // Lock body scroll only when fully expanded
    useEffect(() => {
        document.body.style.overflow = snapState === 'expanded' ? 'hidden' : '';
        return () => { document.body.style.overflow = ''; };
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
    // Touch handlers (wired to the drag handle)
    // ----------------------------------------------------------------

    const handleTouchStart = (e: React.TouchEvent) => startDrag(e.touches[0].clientY);
    const handleTouchMove  = (e: React.TouchEvent) => moveDrag(e.touches[0].clientY);
    const handleTouchEnd   = () => endDrag();

    // ----------------------------------------------------------------
    // Mouse handlers — mousedown on handle, move/up on document
    // ----------------------------------------------------------------

    const handleMouseDown = (e: React.MouseEvent) => {
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
            {/* Backdrop */}
            <div
                className={`
                    lg:hidden fixed inset-0 bg-black/50 z-40
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

            {/* Sheet — starts off-screen; JS drives all position changes */}
            <div
                ref={sheetRef}
                className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-(--background-primary) rounded-t-2xl flex flex-col shadow-[0_-8px_30px_rgba(0,0,0,0.18)] border-t border-(--divider)"
                style={{ height: '90vh', transform: 'translateY(100%)', willChange: 'transform' }}
            >
                {/* Drag handle */}
                <div
                    className="flex flex-col items-center pt-3 pb-1 shrink-0 touch-none select-none cursor-grab active:cursor-grabbing"
                    onTouchStart={handleTouchStart}
                    onTouchMove={handleTouchMove}
                    onTouchEnd={handleTouchEnd}
                    onMouseDown={handleMouseDown}
                >
                    <div className="w-10 h-1 rounded-full bg-(--divider)" />
                    {title && (
                        <div className="text-[13px] font-bold text-(--text-primary) mt-2">{title}</div>
                    )}
                </div>

                {/* Content — scrollable only when expanded so drag doesn't fight scroll.
                    While collapsed (peek/closed) it also acts as a drag handle so a
                    swipe anywhere on the sheet — not just the tiny handle — opens it. */}
                <div
                    className={`flex-1 min-h-0 ${
                        snapState === 'expanded' ? 'overflow-y-auto' : 'overflow-hidden touch-none select-none'
                    }`}
                    {...(snapState !== 'expanded' ? {
                        onTouchStart: handleTouchStart,
                        onTouchMove: handleTouchMove,
                        onTouchEnd: handleTouchEnd,
                        onMouseDown: handleMouseDown,
                    } : {})}
                >
                    {children}
                </div>
            </div>
        </>
    );
}
