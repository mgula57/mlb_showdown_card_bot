import { useEffect, useState } from 'react';
import { fetchMyReleases, fetchPublicReleases, fetchSavedReleases, type Release } from '../api/releases';
import type { SetMultiSelectOption } from '../components/cards/SetMultiSelect';

/** Which releases besides the user's own to offer: every published one, or only those they saved. */
export type ReleaseEditionScope = 'public' | 'saved';

/** One option per selectable edition, grouped under its release: every edition of the user's own
 * releases (drafts included), published editions of the others. */
const editionOptions = (myReleases: Release[], otherReleases: Release[]): SetMultiSelectOption[] => {
    const myReleaseIds = new Set(myReleases.map(r => r.id));
    const releases = [...myReleases, ...otherReleases.filter(r => !myReleaseIds.has(r.id))];
    return releases.flatMap(release => release.editions
        .filter(edition => myReleaseIds.has(release.id) || edition.is_published)
        .map(edition => ({
            value: edition.id,
            label: edition.is_published ? edition.name : `${edition.name} (Draft)`,
            group: release.name,
        }))
    );
};

const fetchOtherReleases = (scope: ReleaseEditionScope, token?: string | null): Promise<Release[]> => {
    if (scope === 'public') return fetchPublicReleases(200).catch(() => []);
    return token ? fetchSavedReleases(token).catch(() => []) : Promise.resolve([]);
};

/**
 * The Release Builder editions the signed-in user can pick from - theirs plus published editions
 * of the releases in `scope` - for edition pickers like the release card search (`saved`) and
 * league creation (`public`). `null` while loading.
 */
export function useReleaseEditionOptions(token?: string | null, scope: ReleaseEditionScope = 'public'): SetMultiSelectOption[] | null {
    const [options, setOptions] = useState<SetMultiSelectOption[] | null>(null);

    useEffect(() => {
        let cancelled = false;
        Promise.all([
            token ? fetchMyReleases(token).catch(() => []) : Promise.resolve([]),
            fetchOtherReleases(scope, token),
        ]).then(([mine, others]) => {
            if (!cancelled) setOptions(editionOptions(mine, others));
        });
        return () => { cancelled = true; };
    }, [token, scope]);

    return options;
}
