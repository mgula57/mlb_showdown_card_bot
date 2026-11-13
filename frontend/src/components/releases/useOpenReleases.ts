import { useEffect, useRef, useState } from 'react';
import { matchPath, useLocation, useNavigate } from 'react-router-dom';
import { fetchRelease, ReleaseNotFoundError, type Release } from '../../api/releases';

/** A card link opens that card in its edition. */
const RELEASE_BUILDER_ROUTE = '/release-builder/:releaseId?/:editionSlug?/:cardRef?';

/** Where the URL is in the Release Builder: the list (no release id), or a release, edition and card. */
export function useReleaseBuilderRoute() {
    const { pathname } = useLocation();
    const params = matchPath(RELEASE_BUILDER_ROUTE, pathname)?.params;
    return {
        isOnReleaseBuilder: !!params,
        releaseId: params?.releaseId ?? null,
        editionSlug: params?.editionSlug ?? null,
        cardRef: params?.cardRef ?? null,
    };
}

export type ReleaseBuilderRoute = ReturnType<typeof useReleaseBuilderRoute>;

/** Other people's releases kept mounted at once. They have no unsaved work to protect, so the
 *  least recently viewed one unmounts (and refetches if reopened) rather than piling up in memory. */
const MAX_MOUNTED_READ_ONLY = 3;

/** A release that has been opened in this session. Each one keeps its own mounted ReleaseDetail
 *  (hidden when not addressed by the URL) so unsaved builder progress survives navigation. */
export type OpenRelease = {
    release: Release;
    readOnly: boolean;
    /** Last edition slug viewed in this release — restored when navigating back to it. */
    editionSlug: string | null;
    /** When it was last on screen, as a sequence number, for unmounting the stalest read-only one. */
    lastViewed: number;
};

/** `open` without the read-only releases past `MAX_MOUNTED_READ_ONLY`, least recently viewed first. */
function withReadOnlyCap(open: Record<string, OpenRelease>): Record<string, OpenRelease> {
    const stale = Object.values(open)
        .filter(o => o.readOnly)
        .sort((a, b) => b.lastViewed - a.lastViewed)
        .slice(MAX_MOUNTED_READ_ONLY);
    if (stale.length === 0) return open;
    const kept = { ...open };
    for (const o of stale) delete kept[o.release.id];
    return kept;
}

type UseOpenReleasesOptions = {
    route: ReleaseBuilderRoute;
    authLoading: boolean;
    token?: string;
    userId?: string;
    /** The URL's release is private or gone; the list opens in its place. */
    onNotFound: () => void;
};

/** The releases opened this session, kept mounted (see `OpenRelease`), and the URL's release:
 *  fetched and mounted when the URL addresses one that isn't open yet, its last edition restored
 *  for a bare release URL. */
export function useOpenReleases({ route, authLoading, token, userId, onNotFound }: UseOpenReleasesOptions) {
    const navigate = useNavigate();
    const { isOnReleaseBuilder, releaseId: releaseIdFromUrl, editionSlug: editionSlugFromUrl } = route;
    const [open, setOpen] = useState<Record<string, OpenRelease>>({});
    /** A release link that failed to load for another reason (offline, server error), kept on screen to retry. */
    const [openError, setOpenError] = useState<{ releaseId: string; message: string } | null>(null);
    const [openAttempt, setOpenAttempt] = useState(0);
    const viewSeq = useRef(0);

    const active = releaseIdFromUrl ? open[releaseIdFromUrl] : undefined;
    const isActiveMounted = !!active;

    // Stamps the release on screen as most recently viewed (see `MAX_MOUNTED_READ_ONLY`)
    useEffect(() => {
        if (!releaseIdFromUrl) return;
        const seq = ++viewSeq.current;
        setOpen(prev => prev[releaseIdFromUrl] ? { ...prev, [releaseIdFromUrl]: { ...prev[releaseIdFromUrl], lastViewed: seq } } : prev);
    }, [releaseIdFromUrl, isActiveMounted]);

    // readOnly is resolved per release when it mounts, so a different signed-in user needs fresh
    // mounts. Keyed on the user id (not the token) so routine token refreshes keep progress.
    const mountedForUserRef = useRef(userId);
    useEffect(() => {
        if (mountedForUserRef.current === userId) return;
        mountedForUserRef.current = userId;
        setOpen({});
    }, [userId]);

    // When the URL addresses a release that isn't mounted yet, fetch and mount it. Waits for the
    // auth session to restore first — on a page reload the token isn't available on the first
    // render, and an unpublished release fetched anonymously 404s and bounces back to the list.
    useEffect(() => {
        // This page stays mounted while hidden, so leaving the route must not touch open releases.
        if (authLoading || !isOnReleaseBuilder || !releaseIdFromUrl || open[releaseIdFromUrl]) return;

        let cancelled = false;
        const releaseId = releaseIdFromUrl;
        fetchRelease(releaseId, token)
            .then(release => {
                if (!cancelled) mount(release, !token || release.created_by !== userId);
            })
            .catch(err => {
                if (cancelled) return;
                // Private or gone: nothing to retry, so the list says why. Anything else (offline,
                // a server error) stays on the link so it can be retried.
                if (err instanceof ReleaseNotFoundError) {
                    onNotFound();
                    navigate('/release-builder', { replace: true });
                } else {
                    setOpenError({ releaseId, message: "Couldn't load this release. Check your connection and try again." });
                }
            });
        return () => { cancelled = true; };
    // isActiveMounted: a sign-out or account switch clears the open releases in the same commit
    // this runs in (seeing the stale map), so it must run again once the release unmounts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [authLoading, releaseIdFromUrl, isOnReleaseBuilder, token, isActiveMounted, openAttempt]);

    // Bare release URL (no edition slug) → restore the edition last viewed in that release.
    useEffect(() => {
        if (!isOnReleaseBuilder || !active || editionSlugFromUrl || !active.editionSlug) return;
        navigate(`/release-builder/${active.release.id}/${active.editionSlug}`, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [releaseIdFromUrl, editionSlugFromUrl, isOnReleaseBuilder, isActiveMounted]);

    // Remember the edition being viewed so returning to this release lands on it.
    useEffect(() => {
        if (!isOnReleaseBuilder || !releaseIdFromUrl || !editionSlugFromUrl) return;
        setOpen(prev => !prev[releaseIdFromUrl] || prev[releaseIdFromUrl].editionSlug === editionSlugFromUrl
            ? prev
            : { ...prev, [releaseIdFromUrl]: { ...prev[releaseIdFromUrl], editionSlug: editionSlugFromUrl } }
        );
    }, [releaseIdFromUrl, editionSlugFromUrl, isOnReleaseBuilder, isActiveMounted]);

    function mount(release: Release, readOnly: boolean, editionSlug: string | null = null) {
        const seq = ++viewSeq.current;
        setOpen(prev => prev[release.id]
            ? prev
            : withReadOnlyCap({ ...prev, [release.id]: { release, readOnly, editionSlug, lastViewed: seq } })
        );
    }

    /** Swaps in a newer copy of an open release. */
    function update(release: Release) {
        setOpen(prev => prev[release.id] ? { ...prev, [release.id]: { ...prev[release.id], release } } : prev);
    }

    function remove(releaseId: string) {
        setOpen(prev => {
            const rest = { ...prev };
            delete rest[releaseId];
            return rest;
        });
    }

    function retry() {
        setOpenError(null);
        setOpenAttempt(n => n + 1);
    }

    return {
        releases: Object.values(open),
        active,
        get: (releaseId: string): Release | undefined => open[releaseId]?.release,
        /** Why the URL's release didn't load, when it can be retried. */
        error: openError && openError.releaseId === releaseIdFromUrl ? openError.message : null,
        mount, update, remove, retry,
    };
}
