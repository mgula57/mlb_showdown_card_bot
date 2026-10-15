/**
 * @fileoverview ReleaseCardSearch - card search over Release Builder editions. Wraps ShowdownCardSearch
 * (source RELEASE) with an edition picker in its search bar; the picked editions are fed in as a locked
 * `release_edition_id` filter so the rest of the filter/sort UI works unchanged. Nothing is searched
 * until the user picks at least one edition; the picks are remembered in localStorage.
 */

import { useMemo, useState } from 'react';
import ShowdownCardSearch, { type FilterSelections } from './ShowdownCardSearch';
import SetMultiSelect from './SetMultiSelect';
import { CardSource } from '../../types/cardSource';
import { useReleaseEditionOptions } from '../../hooks/useReleaseEditionOptions';
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

export default function ReleaseCardSearch() {
    const { session } = useAuth();
    const token = session?.access_token;

    const options = useReleaseEditionOptions(token);
    const [savedEditionIds, setSavedEditionIds] = useState<string[]>(loadSelectedEditions);

    // Saved picks that are no longer searchable (deleted, unpublished, signed out) are left out
    const selectedEditionIds = useMemo(() => {
        if (options === null) return savedEditionIds;
        const available = new Set(options.map(o => o.value));
        return savedEditionIds.filter(id => available.has(id));
    }, [options, savedEditionIds]);

    const handleSelectionChange = (editionIds: string[]) => {
        setSavedEditionIds(editionIds);
        saveSelectedEditions(editionIds);
    };

    const defaultFilters = useMemo<Partial<FilterSelections>>(
        () => ({ release_edition_id: selectedEditionIds }),
        [selectedEditionIds]
    );

    const editionPicker = options === null ? (
        <div className="h-11 w-28 md:w-48 shrink-0 rounded-xl bg-(--background-secondary) animate-pulse" />
    ) : (
        <SetMultiSelect
            className="shrink-0"
            options={options}
            selections={selectedEditionIds}
            onChange={handleSelectionChange}
            placeholder={options.length === 0 ? 'No editions' : 'Pick editions'}
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
