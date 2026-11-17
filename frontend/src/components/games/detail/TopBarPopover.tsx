/**
 * @fileoverview A `TopBarButton` that opens a floating panel under it (a game's settings). Fixed
 * and positioned with floating-ui so the bar's truncating row never clips it, but rendered in place,
 * not portaled to `<body>`: game pages are a full-screen `GameOverlay` layer (z-55) that a body
 * portal would sit under. In place, it rides the top bar's layer above the board and rail. A click
 * outside or Escape closes it.
 */
import { useEffect, useState, type ReactNode } from "react";
import { autoUpdate, flip, offset, shift, useFloating } from "@floating-ui/react";
import TopBarButton from "./TopBarButton";

type TopBarPopoverProps = {
    label: string;
    shortLabel?: string;
    icon?: ReactNode;
    /** Colors/border/padding for the button, as on `TopBarButton`. */
    className?: string;
    /** Hides the label so the button is just its icon (the label stays as its title). */
    isIconOnly?: boolean;
    children: ReactNode;
};

export default function TopBarPopover({ label, shortLabel, icon, className, isIconOnly = false, children }: TopBarPopoverProps) {
    const [isOpen, setIsOpen] = useState(false);
    // Elements held in state (not floating-ui's refs) so render never reads a ref
    const [referenceElement, setReferenceElement] = useState<HTMLSpanElement | null>(null);
    const [floatingElement, setFloatingElement] = useState<HTMLDivElement | null>(null);
    const { floatingStyles } = useFloating({
        open: isOpen,
        elements: { reference: referenceElement, floating: floatingElement },
        placement: "bottom-end",
        strategy: "fixed",
        middleware: [offset(6), flip({ padding: 8 }), shift({ padding: 8 })],
        whileElementsMounted: autoUpdate,
    });

    useEffect(() => {
        if (!isOpen) return;
        const handlePointerDown = (event: PointerEvent) => {
            const target = event.target as Node;
            if (referenceElement?.contains(target) || floatingElement?.contains(target)) return;
            setIsOpen(false);
        };
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") setIsOpen(false);
        };
        document.addEventListener("pointerdown", handlePointerDown);
        document.addEventListener("keydown", handleKeyDown);
        return () => {
            document.removeEventListener("pointerdown", handlePointerDown);
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [isOpen, referenceElement, floatingElement]);

    return (
        <>
            <span ref={setReferenceElement} className="inline-flex min-w-0 shrink" aria-expanded={isOpen} aria-haspopup="dialog">
                <TopBarButton label={label} shortLabel={shortLabel} icon={icon} isIconOnly={isIconOnly} onClick={() => setIsOpen((open) => !open)} className={className} />
            </span>
            {isOpen && (
                <div
                    ref={setFloatingElement}
                    role="dialog"
                    aria-label={label}
                    style={floatingStyles}
                    className="z-50 w-64 max-w-[calc(100vw-1rem)] p-3 flex flex-col gap-3 bg-(--background-secondary) border border-(--divider) rounded-card shadow-overlay"
                >
                    {children}
                </div>
            )}
        </>
    );
}
