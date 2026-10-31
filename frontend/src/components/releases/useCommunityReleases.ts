import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchPublicReleases, type PublicReleaseSort, type Release } from '../../api/releases';

/** Releases per page of the Community list. */
export const COMMUNITY_PAGE_SIZE = 24;
/** Wait for typing to pause before searching. */
const SEARCH_DEBOUNCE_MS = 300;

/** Every listed community release for the Community list, the viewer's own included, sorted and searched on the server,
 *  a page at a time. A new sort or search starts over from the first page; coming back to the list (re-enabling)
 *  keeps the pages already loaded. */
export function useCommunityReleases(sort: PublicReleaseSort, search: string, enabled: boolean) {
    const [releases, setReleases] = useState<Release[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [debouncedSearch, setDebouncedSearch] = useState(search);
    const requestSeq = useRef(0);
    // The sort + search the loaded pages are for, so re-enabling with the same ones doesn't refetch
    const loadedQueryRef = useRef<string | null>(null);
    const query = `${sort}|${debouncedSearch}`;

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS);
        return () => clearTimeout(timer);
    }, [search]);

    const load = useCallback(async (offset: number) => {
        const seq = ++requestSeq.current;
        loadedQueryRef.current = query;
        setLoading(true);
        setError(null);
        try {
            const page = await fetchPublicReleases(COMMUNITY_PAGE_SIZE, offset, {
                section: 'community', sort, search: debouncedSearch,
            });
            if (seq !== requestSeq.current) return;
            setReleases(prev => {
                if (offset === 0 || !prev) return page;
                // Offset pages shift as likes and publishes come in, so a release can show up on two pages
                const seen = new Set(prev.map(r => r.id));
                return [...prev, ...page.filter(r => !seen.has(r.id))];
            });
            setHasMore(page.length === COMMUNITY_PAGE_SIZE);
        } catch (err) {
            if (seq !== requestSeq.current) return;
            // Let the next visit retry
            loadedQueryRef.current = null;
            setError(err instanceof Error ? err.message : 'Failed to load community releases.');
        } finally {
            if (seq === requestSeq.current) setLoading(false);
        }
    }, [query, sort, debouncedSearch]);

    useEffect(() => {
        if (enabled && loadedQueryRef.current !== query) load(0);
    }, [enabled, query, load]);

    const loadMore = useCallback(() => { load(releases?.length ?? 0); }, [load, releases?.length]);

    /** Updates the releases already loaded in place (a like, a delete), without refetching. `fn`
     *  returns the release to show, or null to drop it. */
    const mapReleases = useCallback((fn: (release: Release) => Release | null) => {
        setReleases(prev => prev && prev.flatMap(release => fn(release) ?? []));
    }, []);

    return { releases, loading, hasMore, error, loadMore, mapReleases, searching: debouncedSearch.trim() !== '' };
}
