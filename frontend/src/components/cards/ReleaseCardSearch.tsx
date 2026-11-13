/**
 * @fileoverview ReleaseCardSearch - card search over Release Builder editions. Wraps ShowdownCardSearch
 * (source RELEASE) with an edition picker in its search bar; the picked editions are fed in as a locked
 * `release_edition_id` filter so the rest of the filter/sort UI works unchanged. Only the signed-in
 * user's own releases and the ones they saved in the Release Builder are offered. Nothing is searched
 * until the user picks at least one edition; the picks are remembered in localStorage.
 */

import { useEffect, useMemo, useState } from 'react';
import ShowdownCardSearch, { type FilterSelections } from './ShowdownCardSearch';
import SetMultiSelect, { type SetMultiSelectOption } from './SetMultiSelect';
import { CardSource } from '../../types/cardSource';
import { fetchMyReleases, fetchSavedReleases, type Release } from '../../api/releases';
import { useAuth } from '../auth/AuthContext';

const SELECTED_EDITIONS_STORAGE_KEY = 'release-card-search-editions';
const LOCKED_FILTERS = ['release_edition_id'];

const loadSelectedEditions = (): string[] => {
    try {
        const parsed = JSON.parse(localStorage.getItem(SELECTED_EDITIONS_STORAGE_KEY) ?? 'null');
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
};

const saveSelectedEditions = (editionIds: string[]) => {
    try {
        localStorage.setItem(SELECTED_EDITIONS_STORAGE_KEY, JSON.stringify(editionIds));
    } catch {
        // Storage unavailable — the selection just won't persist
    }
};

/** One option per searchable edition, grouped under its release: every edition of the user's own
 * releases (drafts included), published editions of the ones they saved. */
const editionOptions = (myReleases: Release[], savedReleases: Release[]): SetMultiSelectOption[] => {
    const myReleaseIds = new Set(myReleases.map(r => r.id));
    const releases = [...myReleases, ...savedReleases.filter(r => !myReleaseIds.has(r.id))];
    return releases.flatMap(release => release.editions
        .filter(edition => myReleaseIds.has(release.id) || edition.is_published)
        .map(edition => ({
            value: edition.id,
            label: edition.is_published ? edition.name : `${edition.name} (Draft)`,
            group: release.name,
        }))
    );
};

export default function ReleaseCardSearch() {
    const { session } = useAuth();
    const token = session?.access_token;

    const [options, setOptions] = useState<SetMultiSelectOption[] | null>(null);
    const [selectedEditionIds, setSelectedEditionIds] = useState<string[]>(loadSelectedEditions);

    useEffect(() => {
        let cancelled = false;
        Promise.all([
            token ? fetchMyReleases(token).catch(() => []) : Promise.resolve([]),
            token ? fetchSavedReleases(token).catch(() => []) : Promise.resolve([]),
        ]).then(([mine, saved]) => {
            if (cancelled) return;
            const nextOptions = editionOptions(mine, saved);
            setOptions(nextOptions);
            // Drop remembered picks that are no longer searchable (deleted, unpublished, unsaved, signed out)
            const available = new Set(nextOptions.map(o => o.value));
            setSelectedEditionIds(prev => {
                const kept = prev.filter(id => available.has(id));
                return kept.length === prev.length ? prev : kept;
            });
        });
        return () => { cancelled = true; };
    }, [token]);

    const handleSelectionChange = (editionIds: string[]) => {
        setSelectedEditionIds(editionIds);
        saveSelectedEditions(editionIds);
    };

    const defaultFilters = useMemo<Partial<FilterSelections>>(
        () => ({ release_edition_id: selectedEditionIds }),
        [selectedEditionIds]
    );

    const editionPicker = options === null ? (
        <div className="h-11 w-28 md:w-48 shrink-0 rounded-card bg-(--background-secondary) animate-pulse" />
    ) : (
        <SetMultiSelect
            className="shrink-0"
            options={options}
            selections={selectedEditionIds}
            onChange={handleSelectionChange}
            placeholder={options.length === 0 ? (token ? 'No releases' : 'Sign in') : 'Pick editions'}
            disabled={options.length === 0}
        />
    );

    return (
        <ShowdownCardSearch
            source={CardSource.RELEASE}
            defaultFilters={defaultFilters}
            lockedFilters={LOCKED_FILTERS}
            toolbarSlot={editionPicker}
            enableSetSwitcher
        />
    );
}
