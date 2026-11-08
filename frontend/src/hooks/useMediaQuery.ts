import { useCallback, useSyncExternalStore } from "react";

/** JS mirror of the `short` CSS variant in index.css (keep the 40rem in sync). */
export const SHORT_SCREEN_QUERY = '(height < 40rem)';

/** Mirrors a CSS media query into React state, updating as the viewport crosses it. */
export function useMediaQuery(query: string): boolean {
    const subscribe = useCallback((onChange: () => void) => {
        const mq = window.matchMedia(query);
        mq.addEventListener("change", onChange);
        return () => mq.removeEventListener("change", onChange);
    }, [query]);
    return useSyncExternalStore(subscribe, () => window.matchMedia(query).matches);
}
