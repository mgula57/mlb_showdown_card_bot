import { useEffect, useState } from 'react';
import { fetchMyReleases, fetchPublicReleases, type Release } from '../api/releases';
import type { SetMultiSelectOption } from '../components/cards/SetMultiSelect';

/** One option per selectable edition, grouped under its release: every edition of the user's own
 * releases (drafts included), published editions of everyone else's. */
const editionOptions = (myReleases: Release[], publicReleases: Release[]): SetMultiSelectOption[] => {
    const myReleaseIds = new Set(myReleases.map(r => r.id));
    const releases = [...myReleases, ...publicReleases.filter(r => !myReleaseIds.has(r.id))];
    return releases.flatMap(release => release.editions
        .filter(edition => myReleaseIds.has(release.id) || edition.is_published)
        .map(edition => ({
            value: edition.id,
            label: edition.is_published ? edition.name : `${edition.name} (Draft)`,
            group: release.name,
        }))
    );
};

/**
 * The Release Builder editions the signed-in user can pick from (theirs + published ones), for
 * edition pickers like the release card search and league creation. `null` while loading.
 */
export function useReleaseEditionOptions(token?: string | null): SetMultiSelectOption[] | null {
    const [options, setOptions] = useState<SetMultiSelectOption[] | null>(null);

    useEffect(() => {
        let cancelled = false;
        Promise.all([
            token ? fetchMyReleases(token).catch(() => []) : Promise.resolve([]),
            fetchPublicReleases(200).catch(() => []),
        ]).then(([mine, published]) => {
            if (!cancelled) setOptions(editionOptions(mine, published));
        });
        return () => { cancelled = true; };
    }, [token]);

    return options;
}
