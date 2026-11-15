import { useCallback, useState } from "react";

/** Tracks an element's rendered height in px, for layouts that place something relative to a
 *  sibling whose height depends on its content (e.g. a field running up under the scoreboard laid
 *  over it). Attach the returned ref to the element. Measures in the ref callback, which commits
 *  before paint, then on every resize. */
export function useElementHeight<T extends HTMLElement>(): [(element: T | null) => (() => void) | void, number] {
    const [height, setHeight] = useState(0);

    const ref = useCallback((element: T | null) => {
        if (!element) return;
        setHeight(element.getBoundingClientRect().height);
        const observer = new ResizeObserver(() => setHeight(element.getBoundingClientRect().height));
        observer.observe(element);
        return () => observer.disconnect();
    }, []);

    return [ref, height];
}
