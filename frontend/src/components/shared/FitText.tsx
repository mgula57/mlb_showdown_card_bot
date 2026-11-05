/**
 * @fileoverview One-line headline that shrinks to fit its width instead of clipping (see
 * frontend/DESIGN.md, "Type"). The display faces are wide and the italic one leans past its own
 * box, so a plain `truncate` cuts off both long names and the slant of the last letter.
 *
 * The CSS font size on the element (a `Heading` level, `text-[44px]`, responsive classes) is the
 * maximum; the text scales down from it, never below `minScale`, then ellipsizes. Its width must
 * come from the layout (a block, `flex-1`, or a shrinking flex item), not from the text alone.
 */
import { useLayoutEffect, useRef, type CSSProperties, type ElementType, type ReactNode } from 'react';
import { SLANT_ROOM_CLASS } from './headingStyles';

type FitTextProps = {
    children: ReactNode;
    /** Smallest size as a fraction of the CSS size before the text ellipsizes. */
    minScale?: number;
    as?: ElementType;
    className?: string;
    style?: CSSProperties;
    title?: string;
};

export function FitText({ children, minScale = 0.6, as: Tag = 'div', className = '', style, title }: FitTextProps) {
    const outerRef = useRef<HTMLElement>(null);
    const innerRef = useRef<HTMLSpanElement>(null);

    useLayoutEffect(() => {
        const outer = outerRef.current;
        const inner = innerRef.current;
        if (!outer || !inner) return;

        const fit = () => {
            // Measure at full size so any content-sized ancestors re-expand to their own limits first
            inner.style.fontSize = '1em';
            const available = outer.clientWidth;
            const natural = inner.getBoundingClientRect().width;
            const scale = available > 0 && natural > available ? Math.max(minScale, available / natural) : 1;
            inner.style.fontSize = `${scale}em`;
            outer.dataset.clipped = String(natural * scale > available + 0.5);
        };

        fit();
        const observer = new ResizeObserver(fit);
        observer.observe(outer);
        if (outer.parentElement) observer.observe(outer.parentElement);
        window.addEventListener('resize', fit);
        document.fonts?.ready.then(fit).catch(() => { /* fonts API unavailable */ });
        return () => {
            observer.disconnect();
            window.removeEventListener('resize', fit);
        };
    }, [children, minScale]);

    return (
        <Tag
            ref={outerRef}
            title={title}
            style={style}
            className={`min-w-0 whitespace-nowrap data-[clipped=true]:overflow-hidden data-[clipped=true]:text-ellipsis ${className}`}
        >
            <span ref={innerRef} className={SLANT_ROOM_CLASS}>{children}</span>
        </Tag>
    );
}

export default FitText;
