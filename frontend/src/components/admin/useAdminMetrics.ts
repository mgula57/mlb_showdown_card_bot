import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { fetchAdminMetrics, type AdminMetricsPath, type AdminPeriod } from '../../api/adminMetrics';

// Browser-session cache so switching tabs or periods back and forth doesn't refetch
const _cache = new Map<string, unknown>();

/** Drops every cached view (the page's Refresh button), so tabs opened afterwards refetch too. */
export function clearAdminMetricsCache() {
    _cache.clear();
}

type AdminMetricsState<T> = {
    /** Null until the view has loaded (show a skeleton). */
    data: T | null;
    error: string | null;
    retry: () => void;
};

/** Loads one admin metrics view. A `refreshKey` change (the page's Refresh button) also skips the
 *  server's cache. Pass a null path to load nothing. */
export function useAdminMetrics<T>(path: AdminMetricsPath | null, days: AdminPeriod, refreshKey: number): AdminMetricsState<T> {
    const { session } = useAuth();
    const token = session?.access_token ?? null;
    const cacheKey = path ? `${path}:${days}` : null;
    // Bumped when a fetch lands, to re-read the cache
    const [, setLoadedCount] = useState(0);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [retryCount, setRetryCount] = useState(0);
    const seenRefreshKey = useRef(refreshKey);

    useEffect(() => {
        if (!path || !cacheKey || !token) return;
        const forceRefresh = seenRefreshKey.current !== refreshKey;
        seenRefreshKey.current = refreshKey;
        if (_cache.has(cacheKey) && !forceRefresh) return;

        let cancelled = false;
        fetchAdminMetrics<T>(path, token, days, forceRefresh)
            .then(result => {
                _cache.set(cacheKey, result);
                if (!cancelled) setLoadedCount(count => count + 1);
            })
            .catch(err => {
                if (!cancelled) setErrors(prev => ({ ...prev, [cacheKey]: err instanceof Error ? err.message : String(err) }));
            });
        return () => { cancelled = true; };
    }, [path, cacheKey, days, token, refreshKey, retryCount]);

    const retry = useCallback(() => {
        if (cacheKey) {
            setErrors(prev => {
                const next = { ...prev };
                delete next[cacheKey];
                return next;
            });
        }
        setRetryCount(count => count + 1);
    }, [cacheKey]);

    return {
        data: cacheKey ? (_cache.get(cacheKey) as T | undefined) ?? null : null,
        error: cacheKey ? errors[cacheKey] ?? null : null,
        retry,
    };
}
