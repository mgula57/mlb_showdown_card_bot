import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchPublicReleases, type PublicReleaseSort, type Release } from '../../api/releases';

/** Releases per page of the Community list. */
export const COMMUNITY_PAGE_SIZE = 24;
/** Wait for typing to pause before searching. */
const SEARCH_DEBOUNCE_MS = 300;

/** Everyone else's published releases for the Community list, sorted and searched on the server,
 *  a page at a time. A new sort or search starts over from the first page. */
export function useCommunityReleases(sort: PublicReleaseSort, search: string, token: string | undefined, enabled: boolean) {
    const [releases, setReleases] = useState<Release[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [debouncedSearch, setDebouncedSearch] = useState(search);
    const requestSeq = useRef(0);

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS);
        return () => clearTimeout(timer);
    }, [search]);

    const load = useCallback(async (offset: number) => {
        if (!enabled) return;
        const seq = ++requestSeq.current;
        setLoading(true);
        setError(null);
        try {
            const page = await fetchPublicReleases(COMMUNITY_PAGE_SIZE, offset, {
                section: 'community', sort, search: debouncedSearch, excludeMine: !!token, token,
            });
            if (seq !== requestSeq.current) return;
            setReleases(prev => offset === 0 || !prev ? page : [...prev, ...page]);
            setHasMore(page.length === COMMUNITY_PAGE_SIZE);
        } catch (err) {
            if (seq === requestSeq.current) setError(err instanceof Error ? err.message : 'Failed to load community releases.');
        } finally {
            if (seq === requestSeq.current) setLoading(false);
        }
    }, [enabled, sort, debouncedSearch, token]);

    useEffect(() => { load(0); }, [load]);

    const loadMore = useCallback(() => { load(releases?.length ?? 0); }, [load, releases?.length]);

    return { releases, loading, hasMore, error, loadMore, searching: debouncedSearch.trim() !== '' };
}
