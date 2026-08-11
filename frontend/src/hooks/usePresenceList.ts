import { useEffect, useRef, useState } from "react";

export type Presence = "entering" | "present" | "leaving";

/**
 * Keeps items keyed out of `items` mounted for `exitMs` after removal so they can animate out
 * (a scoring runner fading at home, an out-recorded card fading at its base), and marks a
 * freshly-added item `"entering"` for one render before flipping it to `"present"` — the same
 * "commit a start state, then move on the next frame" idiom as the `requestAnimationFrame` bar
 * fill in `RealVsProjectedVisual.tsx`, generalized to a keyed list.
 *
 * Callers render every returned item regardless of `presence`; `presence` only drives which
 * transition class applies.
 */
export function usePresenceList<T extends { key: string }>(items: T[], exitMs: number): (T & { presence: Presence })[] {
    const [rendered, setRendered] = useState<(T & { presence: Presence })[]>(
        () => items.map((item) => ({ ...item, presence: "present" as const })),
    );
    const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
    const prevKeysRef = useRef<Set<string>>(new Set(items.map((item) => item.key)));

    useEffect(() => {
        const nextKeys = new Set(items.map((item) => item.key));
        const timers = timersRef.current;

        setRendered((prevRendered) => {
            const next: (T & { presence: Presence })[] = [];

            // Present/updated/entering items — take the fresh data, cancel any pending exit.
            for (const item of items) {
                const existing = timers.get(item.key);
                if (existing) { clearTimeout(existing); timers.delete(item.key); }
                const isNew = !prevKeysRef.current.has(item.key);
                next.push({ ...item, presence: isNew ? "entering" : "present" });
            }

            // Removed items — keep them mounted, flagged "leaving", and schedule the actual removal.
            for (const item of prevRendered) {
                if (nextKeys.has(item.key)) continue;
                next.push({ ...item, presence: "leaving" });
                if (!timers.has(item.key)) {
                    timers.set(item.key, setTimeout(() => {
                        timers.delete(item.key);
                        setRendered((current) => current.filter((c) => c.key !== item.key));
                    }, exitMs));
                }
            }

            return next;
        });

        prevKeysRef.current = nextKeys;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [items]);

    // Flip any "entering" items to "present" on the next tick so the initial render has a start
    // state for the enter transition to animate from.
    useEffect(() => {
        if (!rendered.some((item) => item.presence === "entering")) return;
        const frame = requestAnimationFrame(() => {
            setRendered((prev) => prev.map((item) => (item.presence === "entering" ? { ...item, presence: "present" } : item)));
        });
        return () => cancelAnimationFrame(frame);
    }, [rendered]);

    useEffect(() => {
        const timers = timersRef.current;
        return () => { timers.forEach((t) => clearTimeout(t)); timers.clear(); };
    }, []);

    return rendered;
}
