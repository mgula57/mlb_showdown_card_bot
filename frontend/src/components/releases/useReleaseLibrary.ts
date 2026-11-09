import { useEffect, useRef, useState } from 'react';
import { fetchMyReleases, fetchPublicReleases, fetchSavedReleases, type Release } from '../../api/releases';

/** A list tile with the like/save state from a fuller copy of the release. Only those, since the
 *  owner's copy also carries unpublished editions a public tile mustn't show. */
export function withEngagement(tile: Release, updated: Release): Release {
    return { ...tile, like_count: updated.like_count, liked_by_me: updated.liked_by_me, saved_by_me: updated.saved_by_me, comment_count: updated.comment_count };
}

/** The sections above Community: the viewer's own releases, the ones they saved, and the official
 *  ones (less the viewer's own). Loaded lazily, the first time `enabled` (the list is on screen), so a
 *  direct visit to a release URL opens the release without first loading every release. Signing in,
 *  out, or as someone else starts over. Keyed on the user id (not the token) so routine token
 *  refreshes don't reload it. */
export function useReleaseLibrary(enabled: boolean, token?: string, userId?: string) {
    const [mine, setMine] = useState<Release[]>([]);
    const [saved, setSaved] = useState<Release[]>([]);
    const [official, setOfficial] = useState<Release[]>([]);
    const [loading, setLoading] = useState(true);
    /** Every section loaded, so showing the list again doesn't refetch. */
    const [loaded, setLoaded] = useState(false);
    /** The lists hold this viewer's releases (from a load since the last sign-in change), so a reload
     *  can keep them on screen instead of going back to the skeleton. */
    const [ready, setReady] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const loadSeq = useRef(0);

    // Bumping the load sequence drops any load still in flight for the previous user, and the
    // previous user's own lists are cleared so they never show under the new one.
    useEffect(() => {
        loadSeq.current++;
        setLoaded(false);
        setReady(false);
        setMine([]);
        setSaved([]);
    }, [userId]);

    useEffect(() => {
        if (enabled && !loaded) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [enabled, loaded, userId]);

    /** Loads each section on its own, so one failing (say, Saved) doesn't blank the others. A
     *  partial load isn't marked loaded, so coming back to the list retries. Only the latest load
     *  applies, so a slow one from before a sign-out can't restore the previous user's lists. */
    async function load() {
        const seq = ++loadSeq.current;
        setLoading(true);
        setError(null);
        const results = await Promise.allSettled([
            fetchPublicReleases(100, 0, { section: 'official', sort: 'new' }, token),
            token ? fetchMyReleases(token) : Promise.resolve([]),
            token ? fetchSavedReleases(token) : Promise.resolve([]),
        ]);
        if (seq !== loadSeq.current) return;
        const [officialResult, mineResult, savedResult] = results;
        setReady(true);
        if (officialResult.status === 'fulfilled') setOfficial(officialResult.value.filter(r => r.created_by !== userId));
        if (mineResult.status === 'fulfilled') setMine(mineResult.value);
        if (savedResult.status === 'fulfilled') setSaved(savedResult.value);
        const failed = results.filter(result => result.status === 'rejected');
        if (failed.length === 0) {
            setLoaded(true);
        } else {
            const reason = failed[0].reason;
            setError(failed.length === results.length
                ? (reason instanceof Error ? reason.message : 'Failed to load releases.')
                : 'Some releases didn\'t load.');
        }
        setLoading(false);
    }

    /** Shows a change made in an open release on its tiles. */
    function applyUpdate(updated: Release) {
        setMine(prev => prev.map(r => r.id === updated.id ? updated : r));
        // A like from the release's header shows on its official tile too
        setOfficial(prev => prev.map(r => r.id === updated.id ? withEngagement(r, updated) : r));
        // Saving or unsaving in the release's header adds it to (or drops it from) Saved, in place if it's already there
        if (updated.saved_by_me !== undefined) {
            setSaved(prev => !updated.saved_by_me ? prev.filter(r => r.id !== updated.id)
                : prev.some(r => r.id === updated.id) ? prev.map(r => r.id === updated.id ? updated : r)
                : [updated, ...prev]);
        }
    }

    function remove(releaseId: string) {
        const without = (list: Release[]) => list.filter(r => r.id !== releaseId);
        setMine(without);
        setSaved(without);
        setOfficial(without);
    }

    /** A release the user just made (new or remixed), at the front of My Releases. */
    function addMine(created: Release) {
        setMine(prev => [created, ...prev]);
    }

    return { mine, saved, official, loading, ready, error, reload: load, applyUpdate, remove, addMine };
}

export type ReleaseLibrary = ReturnType<typeof useReleaseLibrary>;
