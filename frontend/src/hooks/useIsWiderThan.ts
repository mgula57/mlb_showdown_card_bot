import { useCallback, useState } from "react";

/** Tracks whether an element is at least `minWidth` px wide, for layouts that depend on the space
 *  they actually get rather than the viewport (e.g. beside a collapsible sidebar). Attach the
 *  returned ref to the element. It measures in the ref callback, which commits before paint, so a
 *  wide element never flashes its narrow layout. */
export function useIsWiderThan<T extends HTMLElement>(minWidth: number): [(element: T | null) => (() => void) | void, boolean] {
    const [isWider, setIsWider] = useState(false);

    const ref = useCallback((element: T | null) => {
        if (!element) return;
        setIsWider(element.getBoundingClientRect().width >= minWidth);
        const observer = new ResizeObserver(([entry]) => setIsWider(entry.contentRect.width >= minWidth));
        observer.observe(element);
        return () => observer.disconnect();
    }, [minWidth]);

    return [ref, isWider];
}
