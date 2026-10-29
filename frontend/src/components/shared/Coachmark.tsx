import { useState, type ReactNode } from 'react';
import {
    useFloating, autoUpdate, offset, flip, shift, arrow, hide, FloatingArrow, FloatingPortal,
    type Middleware, type Placement,
} from '@floating-ui/react';
import { buttonClass } from './buttonStyles';
import { Heading } from './Heading';
import { Eyebrow } from './Eyebrow';

/** Flags an anchor that isn't laid out (it or an ancestor is `display: none`), which `hide()` misses. */
const unrendered: Middleware = {
    name: 'unrendered',
    fn: ({ rects }) => ({ data: { hidden: rects.reference.width === 0 && rects.reference.height === 0 } }),
};

type CoachmarkProps = {
    /** The element the tip points at. Nothing shows until it's set. */
    anchor: HTMLElement | null;
    placement?: Placement;
    /** Progress line above the title, e.g. "Tip 2 of 6". */
    eyebrow?: string;
    title: string;
    children: ReactNode;
    /** "Got it": done with this tip. */
    onDismiss: () => void;
    /** "Skip tips": done with every tip in the tour. */
    onSkipAll?: () => void;
};

/**
 * A one-time onboarding tip pointing at a piece of UI. Portaled and positioned with floating-ui so
 * scrolling and `overflow-hidden` ancestors don't clip it, and it hides itself while its anchor is
 * off screen or not rendered (an inactive tab, a collapsed panel).
 */
export function Coachmark({ anchor, placement = 'bottom', eyebrow, title, children, onDismiss, onSkipAll }: CoachmarkProps) {
    const [floatingElement, setFloatingElement] = useState<HTMLDivElement | null>(null);
    const [arrowElement, setArrowElement] = useState<SVGSVGElement | null>(null);
    const { floatingStyles, context, middlewareData } = useFloating({
        open: true,
        placement,
        elements: { reference: anchor, floating: floatingElement },
        middleware: [offset(10), flip({ padding: 8 }), shift({ padding: 8 }), arrow({ element: arrowElement }), hide(), unrendered],
        whileElementsMounted: autoUpdate,
    });
    const isHidden = !anchor || !!middlewareData.hide?.referenceHidden || !!middlewareData.unrendered?.hidden;

    return (
        <FloatingPortal>
            <div
                ref={setFloatingElement}
                role="dialog"
                aria-label={title}
                style={{ ...floatingStyles, visibility: isHidden ? 'hidden' : 'visible' }}
                className="w-64 p-3 bg-(--background-secondary) border border-(--divider) rounded-card shadow-overlay text-left z-40 animate-fade-in"
            >
                {eyebrow && <Eyebrow className="block mb-1.5 text-[10px]!">{eyebrow}</Eyebrow>}
                <Heading level="panel" as="div" className="mb-1">{title}</Heading>
                <div className="text-[12px] leading-snug text-(--text-secondary) mb-3">{children}</div>
                <div className="flex items-center gap-2">
                    <button type="button" onClick={onDismiss} className={buttonClass('primary', 'sm')}>
                        Got it
                    </button>
                    {onSkipAll && (
                        <button type="button" onClick={onSkipAll} className={buttonClass('ghost', 'sm')}>
                            Skip tips
                        </button>
                    )}
                </div>
                <FloatingArrow
                    ref={setArrowElement}
                    context={context}
                    width={12}
                    height={6}
                    fill="var(--background-secondary)"
                    stroke="var(--divider)"
                    strokeWidth={1}
                />
            </div>
        </FloatingPortal>
    );
}
