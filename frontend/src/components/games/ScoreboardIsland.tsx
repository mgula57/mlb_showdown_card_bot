/**
 * @fileoverview A tab that grows out of the bottom edge of the scoreboard when there's something to
 * say (whose turn it is, a move that failed) and folds back into it when there isn't, the way the
 * iPhone's Dynamic Island does. It hangs over the top of the board rather than taking a row, so
 * appearing never pushes the field down. It's in the scoreboard's layer, so where it crosses the
 * field it's always on top.
 */
import { useLayoutEffect, useRef, useState, type ReactNode } from "react";

type Size = { width: number; height: number };

/** Measures `ref`'s box, kept current as it changes. A `ResizeObserver` reports once as soon as it
 *  starts observing, so that's the first measurement too. */
function useBoxSize(ref: React.RefObject<HTMLElement | null>): Size | null {
    const [size, setSize] = useState<Size | null>(null);
    useLayoutEffect(() => {
        const element = ref.current;
        if (!element) return;
        const observer = new ResizeObserver(() => setSize({ width: element.offsetWidth, height: element.offsetHeight }));
        observer.observe(element);
        return () => observer.disconnect();
    }, [ref]);
    return size;
}

type ScoreboardIslandProps = {
    /** The scoreboard it hangs from. */
    children: ReactNode;
    /** What the island says. Nothing (null, false) folds it away. */
    content?: ReactNode;
    /** Changes whenever the message does, so the new one pops in rather than swapping silently. */
    contentKey: string;
    className?: string;
};

export default function ScoreboardIsland({ children, content, contentKey, className = "" }: ScoreboardIslandProps) {
    const isOpen = !!content;

    // Folding away keeps the last message on screen while it shrinks, rather than emptying first.
    const [last, setLast] = useState<{ content: ReactNode; key: string }>({ content, key: contentKey });
    if (isOpen && last.key !== contentKey) setLast({ content, key: contentKey });
    const shown = isOpen ? { content, key: contentKey } : last;

    const innerRef = useRef<HTMLDivElement>(null);
    const size = useBoxSize(innerRef);

    return (
        <div className={`relative ${className}`}>
            {children}
            <div
                aria-live="polite"
                className="pointer-events-none absolute left-1/2 top-full z-20 -mt-px flex -translate-x-1/2 justify-center"
            >
                {/* The tab's own size animates, from a sliver tucked under the scoreboard to the
                    message's measured size, so it grows out of the edge instead of fading in. */}
                <div
                    className={`
                        overflow-hidden rounded-b-card border border-t-0 border-(--divider) bg-(--background-primary)
                        transition-[width,height,opacity] duration-300 ease-[cubic-bezier(0.34,1.3,0.64,1)]
                        ${isOpen ? "pointer-events-auto opacity-100" : "opacity-0"}
                    `}
                    style={{
                        width: isOpen && size ? size.width : 48,
                        height: isOpen && size ? size.height : 0,
                    }}
                >
                    <div className="bg-(--background-secondary)/30">
                        <div ref={innerRef} className="w-max max-w-[min(22rem,80vw)] px-3 py-1.5">
                            <div key={shown.key} className={isOpen ? "island-content" : ""}>
                                {shown.content}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
