/**
 * @fileoverview Shared image library state for the signed-in user.
 *
 * Account settings and the Custom Card Builder stay mounted across routes, so both read one
 * module-level store: a change saved on the Account page shows up in the builder immediately.
 */

import { useEffect, useSyncExternalStore } from 'react';
import { useAuth } from '../auth/AuthContext';
import { getImageLibraries, SHOWDOWN_BOT_LIBRARY_ID } from '../../api/imageLibraries';
import type { ImageLibrariesOverview, ImageLibrary } from '../../api/imageLibraries';

/** Deep link target for the Account page's Image Libraries section, ex: from the Custom Card Builder. */
export const IMAGE_LIBRARIES_SECTION_ID = 'image-libraries';
export const IMAGE_LIBRARIES_PATH = `/account#${IMAGE_LIBRARIES_SECTION_ID}`;

type Snapshot = { userId: string | null; overview: ImageLibrariesOverview | null; error: string | null };

let snapshot: Snapshot = { userId: null, overview: null, error: null };
let inflightUserId: string | null = null;
const listeners = new Set<() => void>();

function setSnapshot(next: Snapshot) {
    snapshot = next;
    listeners.forEach(listener => listener());
}

function subscribe(listener: () => void) {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
}

/** A library in search order, with display info for the built-in Showdown Bot library. */
export type OrderedImageLibrary = {
    id: string;
    name: string;
    isShowdownBot: boolean;
    library: ImageLibrary | null;
};

export function orderedLibraries(overview: ImageLibrariesOverview | null): OrderedImageLibrary[] {
    if (!overview) return [];
    const byId = new Map(overview.libraries.map(lib => [lib.id, lib]));
    return overview.order.map(id => {
        const library = byId.get(id) ?? null;
        return {
            id,
            name: library?.name ?? 'Showdown Bot',
            isShowdownBot: id === SHOWDOWN_BOT_LIBRARY_ID,
            library,
        };
    });
}

export function useImageLibraries() {
    const { user, session } = useAuth();
    const state = useSyncExternalStore(subscribe, () => snapshot);
    const userId = user?.id ?? null;
    const token = session?.access_token ?? null;

    useEffect(() => {
        if (!userId || !token) return;
        if (snapshot.userId === userId && (snapshot.overview || snapshot.error)) return;
        if (inflightUserId === userId) return;
        inflightUserId = userId;
        getImageLibraries(token)
            .then(overview => setSnapshot({ userId, overview, error: null }))
            .catch((err: Error) => setSnapshot({ userId, overview: null, error: err.message }))
            .finally(() => { inflightUserId = null; });
    }, [userId, token]);

    const isCurrentUser = !!userId && state.userId === userId;
    const overview = isCurrentUser ? state.overview : null;
    return {
        token,
        overview,
        ordered: orderedLibraries(overview),
        error: isCurrentUser ? state.error : null,
        isLoading: !!userId && !(isCurrentUser && (state.overview || state.error)),
        setOverview: (next: ImageLibrariesOverview) => setSnapshot({ userId, overview: next, error: null }),
    };
}
