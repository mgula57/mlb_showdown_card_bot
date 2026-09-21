import { useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { FaCircleInfo } from 'react-icons/fa6';

const TOOLTIP_WIDTH = 192; // px, matches w-48
const VIEWPORT_MARGIN = 8; // px, min gap kept from the viewport edge

/** A small (i) icon that reveals an explanatory tooltip on click/tap — for a label that needs
 * more context than fits inline. Click-triggered rather than hover-only so it works on touch
 * devices, and closes on an outside click, scroll, or Escape.
 *
 * The tooltip content is rendered in a portal to `document.body` and positioned from the
 * trigger's bounding rect rather than CSS `absolute`, so it escapes clipping by a scrollable or
 * `overflow-hidden` ancestor (e.g. the card builder's collapsible form sections) instead of
 * being cut off inside them.
 *
 * `iconSize` accepts a Tailwind text-size class (e.g. `'text-[13px]'`, `'text-sm'`) to scale the
 * (i) icon to match the surrounding label — defaults to the original `text-[11px]`. */
export function InfoTooltip({ text, className = '', iconSize = 'text-[11px]' }: { text: string; className?: string; iconSize?: string }) {
    const [open, setOpen] = useState(false);
    const [position, setPosition] = useState<{ top: number; left: number; placement: 'above' | 'below' } | null>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const tooltipRef = useRef<HTMLDivElement>(null);

    useLayoutEffect(() => {
        if (!open) return;

        const reposition = () => {
            const buttonRect = buttonRef.current?.getBoundingClientRect();
            if (!buttonRect) return;

            const tooltipHeight = tooltipRef.current?.offsetHeight ?? 0;
            const placement: 'above' | 'below' = buttonRect.top - tooltipHeight - VIEWPORT_MARGIN >= 0 ? 'above' : 'below';
            const left = Math.min(
                Math.max(buttonRect.left + buttonRect.width / 2, TOOLTIP_WIDTH / 2 + VIEWPORT_MARGIN),
                window.innerWidth - TOOLTIP_WIDTH / 2 - VIEWPORT_MARGIN
            );
            const top = placement === 'above' ? buttonRect.top - 8 : buttonRect.bottom + 8;

            setPosition({ top, left, placement });
        };

        reposition();
        // Re-measure once the tooltip has actually rendered, since its real height (not the
        // guess from the first pass) determines whether it fits above the trigger.
        const raf = requestAnimationFrame(reposition);

        const close = (e: MouseEvent | KeyboardEvent) => {
            if (e instanceof KeyboardEvent) {
                if (e.key === 'Escape') setOpen(false);
                return;
            }
            const target = e.target as Node;
            if (buttonRef.current?.contains(target) || tooltipRef.current?.contains(target)) return;
            setOpen(false);
        };
        const closeOnScroll = () => setOpen(false);

        document.addEventListener('mousedown', close);
        document.addEventListener('keydown', close);
        window.addEventListener('scroll', closeOnScroll, true);
        window.addEventListener('resize', closeOnScroll);
        return () => {
            cancelAnimationFrame(raf);
            document.removeEventListener('mousedown', close);
            document.removeEventListener('keydown', close);
            window.removeEventListener('scroll', closeOnScroll, true);
            window.removeEventListener('resize', closeOnScroll);
        };
    }, [open]);

    return (
        <div className={`relative inline-flex ${className}`}>
            <button
                ref={buttonRef}
                type="button"
                onClick={() => setOpen(o => !o)}
                aria-label="More info"
                aria-expanded={open}
                className="cursor-pointer flex items-center text-(--text-tertiary) hover:text-(--text-primary) transition-colors"
            >
                <FaCircleInfo className={iconSize} />
            </button>
            {open && position && createPortal(
                <div
                    ref={tooltipRef}
                    role="tooltip"
                    style={{
                        position: 'fixed',
                        top: position.top,
                        left: position.left,
                        transform: position.placement === 'above' ? 'translate(-50%, -100%)' : 'translate(-50%, 0)',
                    }}
                    className="w-48 p-2 rounded-lg bg-(--background-tertiary) border border-(--divider) shadow-xl text-[11px] font-normal normal-case text-(--text-secondary) text-left z-50"
                >
                    {text}
                </div>,
                document.body
            )}
        </div>
    );
}
