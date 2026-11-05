import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchReleaseReview, type ReleaseReview } from '../../api/releases';

export type ReleaseReviewState = {
    data: ReleaseReview | null;
    loading: boolean;
    error: string | null;
    refresh: () => void;
};

/** The release's pre-publish checklist. Reloads each time `enabled` turns on, since the builder may
 * have changed the release while the Review step was closed. */
export function useReleaseReview(releaseId: string, token: string | undefined, enabled: boolean): ReleaseReviewState {
    const [data, setData] = useState<ReleaseReview | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const requestSeq = useRef(0);

    const load = useCallback(async () => {
        if (!enabled || !token) return;
        const seq = ++requestSeq.current;
        setLoading(true);
        setError(null);
        try {
            const result = await fetchReleaseReview(releaseId, token);
            if (seq === requestSeq.current) setData(result);
        } catch (err) {
            if (seq === requestSeq.current) setError(err instanceof Error ? err.message : 'Failed to load the review.');
        } finally {
            if (seq === requestSeq.current) setLoading(false);
        }
    }, [releaseId, token, enabled]);

    useEffect(() => { load(); }, [load]);

    const refresh = useCallback(() => { load(); }, [load]);

    return { data, loading, error, refresh };
}
