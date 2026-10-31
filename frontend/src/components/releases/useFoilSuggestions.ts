/**
 * @fileoverview State for the Release Builder's foil suggestions (see `FoilSuggestions`): the last
 * run's picks, the ones the owner skipped, and the "only suggested" grid filter.
 */

import { useEffect, useMemo, useState } from 'react';
import { suggestEditionFoils, type FoilSetType, type FoilSuggestion, type FoilSuggestionResult } from '../../api/releases';

/** A suggestion's reasons as a hover title on its chip. */
export function foilSuggestionTitle(suggestion: FoilSuggestion): string {
    const reasons = suggestion.reasons.length > 0 ? suggestion.reasons.join(' · ') : 'Strong season';
    return `Suggested foil (score ${Math.round(suggestion.score)}): ${reasons}`;
}

/** The run's result, minus the picks the owner skipped. Cleared when the edition changes. */
export function useFoilSuggestions(releaseId: string, editionId: string, token?: string) {
    const [result, setResult] = useState<FoilSuggestionResult | null>(null);
    const [skipped, setSkipped] = useState<Set<string>>(() => new Set());
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [onlySuggested, setOnlySuggested] = useState(false);

    function clear() {
        setResult(null);
        setSkipped(new Set());
        setOnlySuggested(false);
    }

    useEffect(() => {
        clear();
        setError(null);
    }, [editionId]);

    const suggestions = useMemo(
        () => new Map((result?.suggestions ?? []).filter(s => !skipped.has(s.source_card_id)).map(s => [s.source_card_id, s])),
        [result, skipped]
    );

    async function run(setType: FoilSetType): Promise<boolean> {
        if (!token) return false;
        setIsLoading(true);
        setError(null);
        try {
            setResult(await suggestEditionFoils(releaseId, editionId, setType, token));
            setSkipped(new Set());
            return true;
        } catch (err) {
            setError(err instanceof Error ? err.message : "Couldn't suggest foils. Try again.");
            return false;
        } finally {
            setIsLoading(false);
        }
    }

    function skip(sourceCardId: string) {
        setSkipped(prev => new Set(prev).add(sourceCardId));
    }

    return { result, suggestions, isLoading, error, onlySuggested, setOnlySuggested, run, skip, clear };
}

export type FoilSuggestionsState = ReturnType<typeof useFoilSuggestions>;
