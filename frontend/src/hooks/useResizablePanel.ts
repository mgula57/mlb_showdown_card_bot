/**
 * @fileoverview A panel at the end of a container (a sidebar on the right, a sheet at the bottom)
 * that the user resizes by dragging its leading edge with a mouse, pen or finger, or with the arrow
 * keys. The size is kept as a fraction of the container so it scales with the window, and it's
 * remembered on this device once a drag ends. Pair with `ResizeHandle`.
 */
import { useCallback, useEffect, useRef, useState, type KeyboardEvent, type PointerEvent as ReactPointerEvent, type RefObject } from "react";

export type ResizeAxis = "x" | "y";

type Options = {
    /** localStorage key for the remembered size. */
    storageKey: string;
    /** "x" resizes a panel on the right by its width, "y" one at the bottom by its height. */
    axis?: ResizeAxis;
    /** The element the panel shares space with, measured for the fraction and the limits. */
    containerRef: RefObject<HTMLElement | null>;
    /** Size in px until the user resizes. Null leaves the panel to its own CSS. */
    defaultSize: number | null;
    minSize: number;
    /** The largest size in px, given the container's size. */
    maxSize: (containerSize: number) => number;
};

/** How far one arrow key press moves the edge. */
const KEY_STEP_PX = 24;

const loadFraction = (key: string): number | null => {
    try {
        const fraction = parseFloat(localStorage.getItem(key) ?? "");
        return fraction > 0 && fraction < 1 ? fraction : null;
    } catch {
        return null;
    }
};

const saveFraction = (key: string, fraction: number | null) => {
    try {
        if (fraction === null) localStorage.removeItem(key);
        else localStorage.setItem(key, String(fraction));
    } catch {
        // Storage unavailable (private window, blocked site data): the size just isn't remembered.
    }
};

export function useResizablePanel({ storageKey, axis = "x", containerRef, defaultSize, minSize, maxSize }: Options) {
    const [fraction, setFraction] = useState<number | null>(() => loadFraction(storageKey));
    const [containerSize, setContainerSize] = useState(() =>
        typeof window === "undefined" ? 0 : axis === "x" ? window.innerWidth : window.innerHeight);
    const [isResizing, setIsResizing] = useState(false);

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        const observer = new ResizeObserver(([entry]) => {
            setContainerSize(axis === "x" ? entry.contentRect.width : entry.contentRect.height);
        });
        observer.observe(el);
        return () => observer.disconnect();
    }, [containerRef, axis]);

    const clamp = useCallback(
        (px: number, container: number) => Math.min(Math.max(px, minSize), Math.max(minSize, maxSize(container))),
        [minSize, maxSize],
    );

    const size = fraction === null ? defaultSize : clamp(Math.round(fraction * containerSize), containerSize);

    // The panel's size right now: its measured box, so a CSS-sized panel starts from what's on screen.
    const currentSize = (handle: HTMLElement) => {
        const panel = handle.parentElement?.getBoundingClientRect();
        return panel ? (axis === "x" ? panel.width : panel.height) : (size ?? minSize);
    };
    const measureContainer = () => {
        const el = containerRef.current;
        return el ? (axis === "x" ? el.clientWidth : el.clientHeight) : containerSize;
    };

    const latest = useRef<number | null>(null);

    const onPointerDown = (e: ReactPointerEvent<HTMLElement>) => {
        if (e.button !== 0) return;
        e.preventDefault();
        const start = axis === "x" ? e.clientX : e.clientY;
        const startSize = currentSize(e.currentTarget);
        const container = measureContainer();
        latest.current = startSize / container;
        setIsResizing(true);

        // The panel trails the handle, so dragging toward the start of the axis grows it.
        const onMove = (ev: PointerEvent) => {
            const delta = start - (axis === "x" ? ev.clientX : ev.clientY);
            latest.current = clamp(startSize + delta, container) / container;
            setFraction(latest.current);
        };
        const onUp = () => {
            setIsResizing(false);
            saveFraction(storageKey, latest.current);
            document.removeEventListener("pointermove", onMove);
            document.removeEventListener("pointerup", onUp);
            document.removeEventListener("pointercancel", onUp);
            document.body.style.cursor = "";
            document.body.style.userSelect = "";
        };
        document.body.style.cursor = axis === "x" ? "ew-resize" : "ns-resize";
        document.body.style.userSelect = "none";
        document.addEventListener("pointermove", onMove);
        document.addEventListener("pointerup", onUp);
        document.addEventListener("pointercancel", onUp);
    };

    const onKeyDown = (e: KeyboardEvent<HTMLElement>) => {
        const grow = axis === "x" ? "ArrowLeft" : "ArrowUp";
        const shrink = axis === "x" ? "ArrowRight" : "ArrowDown";
        if (e.key !== grow && e.key !== shrink) return;
        e.preventDefault();
        const container = measureContainer();
        const next = clamp(currentSize(e.currentTarget) + (e.key === grow ? KEY_STEP_PX : -KEY_STEP_PX), container) / container;
        setFraction(next);
        saveFraction(storageKey, next);
    };

    const reset = () => {
        setFraction(null);
        saveFraction(storageKey, null);
    };

    return {
        /** Px to size the panel at, or null to leave it to its CSS. */
        size,
        isResizing,
        /** Spread onto `ResizeHandle`. */
        handleProps: {
            axis,
            onPointerDown,
            onKeyDown,
            onDoubleClick: reset,
            isResizing,
            value: size,
            min: minSize,
            max: Math.max(minSize, maxSize(containerSize)),
        },
    };
}

export type ResizeHandleProps = ReturnType<typeof useResizablePanel>["handleProps"];
