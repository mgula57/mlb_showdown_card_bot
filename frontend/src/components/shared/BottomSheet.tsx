import { useEffect, useRef } from 'react';

type BottomSheetProps = {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
    /** Height as a vh string, e.g. "75vh". Defaults to "78vh". */
    height?: string;
};

/**
 * Mobile swipe-up bottom sheet. Hidden on lg+ (use the desktop panel instead).
 * Swipe the drag handle downward ≥120px to dismiss.
 */
export function BottomSheet({ isOpen, onClose, title, children, height = '78vh' }: BottomSheetProps) {
    const sheetRef = useRef<HTMLDivElement>(null);
    const startY = useRef(0);
    const dragOffset = useRef(0);
    const isDragging = useRef(false);

    // Lock body scroll while open
    useEffect(() => {
        document.body.style.overflow = isOpen ? 'hidden' : '';
        return () => { document.body.style.overflow = ''; };
    }, [isOpen]);

    const handleTouchStart = (e: React.TouchEvent) => {
        startY.current = e.touches[0].clientY;
        dragOffset.current = 0;
        isDragging.current = true;
    };

    const handleTouchMove = (e: React.TouchEvent) => {
        if (!isDragging.current || !sheetRef.current) return;
        const delta = e.touches[0].clientY - startY.current;
        if (delta > 0) {
            dragOffset.current = delta;
            sheetRef.current.style.transform = `translateY(${delta}px)`;
            sheetRef.current.style.transition = 'none';
        }
    };

    const handleTouchEnd = () => {
        isDragging.current = false;
        const sheet = sheetRef.current;
        if (!sheet) return;
        sheet.style.transition = '';
        sheet.style.transform = '';
        if (dragOffset.current > 120) {
            onClose();
        }
    };

    return (
        <>
            {/* Backdrop — mobile only */}
            <div
                className={`
                    lg:hidden fixed inset-0 bg-black/50 z-40
                    transition-opacity duration-300
                    ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
                `}
                onClick={onClose}
            />

            {/* Sheet — mobile only */}
            <div
                ref={sheetRef}
                className={`
                    lg:hidden fixed bottom-0 left-0 right-0 z-50
                    bg-(--background-primary) rounded-t-2xl shadow-2xl
                    flex flex-col
                    transition-transform duration-300 ease-out
                    ${isOpen ? 'translate-y-0' : 'translate-y-full'}
                `}
                style={{ height, maxHeight: height }}
            >
                {/* Drag handle */}
                <div
                    className="flex flex-col items-center pt-3 pb-1 shrink-0 touch-none cursor-grab"
                    onTouchStart={handleTouchStart}
                    onTouchMove={handleTouchMove}
                    onTouchEnd={handleTouchEnd}
                >
                    <div className="w-10 h-1 rounded-full bg-(--divider)" />
                    {title && (
                        <div className="text-[13px] font-bold text-(--text-primary) mt-2">{title}</div>
                    )}
                </div>

                {/* Scrollable content */}
                <div className="flex-1 min-h-0 overflow-hidden">
                    {children}
                </div>
            </div>
        </>
    );
}
