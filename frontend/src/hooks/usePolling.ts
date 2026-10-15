import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Loads `load()` now and then every `intervalMs` (no repeat when `intervalMs` is null), keeping the
 * last good result on screen while each refresh is in flight so polled views never flash a
 * loading state. A response that lands after a newer request started is dropped.
 *
 * `deps` restarts the cycle (and clears the data) when what's being loaded changes. Leave out
 * inputs that change without changing *what* loads - notably the auth token, which Supabase
 * renews hourly: `load` is always called fresh, so the next request picks the new token up
 * without blanking the screen.
 */
export function usePolling<T>(load: () => Promise<T>, intervalMs: number | null, deps: unknown[]) {
    const [data, setData] = useState<T | null>(null);
    const [error, setError] = useState<string | null>(null);
    const loadRef = useRef(load);
    loadRef.current = load;
    const requestId = useRef(0);

    const refresh = useCallback(async () => {
        const id = ++requestId.current;
        try {
            const next = await loadRef.current();
            if (id !== requestId.current) return;
            setData(next);
            setError(null);
        } catch (err) {
            if (id !== requestId.current) return;
            setError(err instanceof Error ? err.message : String(err));
        }
    }, []);

    useEffect(() => {
        setData(null);
        setError(null);
        refresh();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, deps);

    useEffect(() => {
        if (intervalMs === null) return;
        const timer = window.setInterval(refresh, intervalMs);
        return () => window.clearInterval(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [intervalMs, ...deps]);

    return { data, setData, error, refresh };
}
