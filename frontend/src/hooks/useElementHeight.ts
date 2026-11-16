import { useCallback, useState } from "react";

export type ElementSize = { width: number; height: number };

/** Tracks an element's rendered size in px, for layouts that fit one zone to the room another
 *  leaves (e.g. how tall the board's corner cards can stand beside the field). Attach the returned
 *  ref to the element. Measures in the ref callback, which commits before paint, then on every
 *  resize. */
export function useElementSize<T extends HTMLElement>(): [(element: T | null) => (() => void) | void, ElementSize] {
    const [size, setSize] = useState<ElementSize>({ width: 0, height: 0 });

    const ref = useCallback((element: T | null) => {
        if (!element) return;
        const measure = () => {
            const { width, height } = element.getBoundingClientRect();
            setSize((current) => (current.width === width && current.height === height ? current : { width, height }));
        };
        measure();
        const observer = new ResizeObserver(measure);
        observer.observe(element);
        return () => observer.disconnect();
    }, []);

    return [ref, size];
}

/** Tracks an element's rendered height in px, for layouts that place something relative to a
 *  sibling whose height depends on its content (e.g. a field running up under the scoreboard laid
 *  over it). See `useElementSize`. */
export function useElementHeight<T extends HTMLElement>(): [(element: T | null) => (() => void) | void, number] {
    const [ref, size] = useElementSize<T>();
    return [ref, size.height];
}
