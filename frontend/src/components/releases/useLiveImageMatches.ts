import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { fetchLiveImageMatches, type LiveImageMatch, type ReleaseCard } from '../../api/releases';

type LiveImageMatchesState = {
    /** `cards` with each snapshot's `image_match_type` replaced by its live match, once checked. */
    cards: ReleaseCard[];
    loading: boolean;
    error: string | null;
    /** ISO time the libraries were last read from Drive. */
    checkedAt: string | null;
    /** Libraries (Drive folders or Showdown Bot) the checked cards pull images from, most used first. */
    libraryNames: string[];
    /** Re-reads the image libraries from Google Drive, bypassing the server cache. */
    refresh: () => void;
};

/** Snapshots store the auto image match from when the card was built, which goes stale as images
 * are uploaded and ignores the owner's own Drive libraries. This re-checks the cards on screen
 * against those libraries (in the user's search order) whenever the set of cards changes. */
export function useLiveImageMatches(releaseId: string, editionId: string, cards: ReleaseCard[], token: string | undefined, enabled: boolean): LiveImageMatchesState {
    const [matches, setMatches] = useState<Record<string, LiveImageMatch>>({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [checkedAt, setCheckedAt] = useState<string | null>(null);
    const requestSeq = useRef(0);

    // One entry per snapshot — the same player-season can appear in several Showdown sets
    const snapshots = useMemo(
        () => [...new Map(cards.map(c => [c.card_snapshot.id, c.card_snapshot])).values()],
        [cards]
    );
    const snapshotKey = useMemo(() => snapshots.map(s => s.id).sort().join('|'), [snapshots]);
    // Saves give every card a new object, so requests key off the ids rather than the array
    const snapshotsRef = useRef(snapshots);
    useEffect(() => { snapshotsRef.current = snapshots; }, [snapshots]);

    const load = useCallback(async (refresh: boolean) => {
        if (!enabled || !token || snapshotsRef.current.length === 0) return;
        const seq = ++requestSeq.current;
        setLoading(true);
        setError(null);
        try {
            const result = await fetchLiveImageMatches(releaseId, editionId, snapshotsRef.current, token, refresh);
            if (seq !== requestSeq.current) return;
            setMatches(prev => ({ ...prev, ...result.matches }));
            setCheckedAt(result.checked_at);
        } catch (err) {
            if (seq === requestSeq.current) setError(err instanceof Error ? err.message : 'Failed to check image matches.');
        } finally {
            if (seq === requestSeq.current) setLoading(false);
        }
    }, [releaseId, editionId, token, enabled]);

    useEffect(() => { load(false); }, [load, snapshotKey]);

    const liveCards = useMemo(() => cards.map(card => {
        const match = matches[card.card_snapshot.id];
        if (!match || match.image_match_type === card.card_snapshot.image_match_type) return card;
        return { ...card, card_snapshot: { ...card.card_snapshot, image_match_type: match.image_match_type } };
    }), [cards, matches]);

    const libraryNames = useMemo(() => {
        const counts = new Map<string, number>();
        for (const snapshot of snapshots) {
            const name = matches[snapshot.id]?.library_name;
            if (name) counts.set(name, (counts.get(name) ?? 0) + 1);
        }
        return [...counts.entries()].sort((a, b) => b[1] - a[1]).map(([name]) => name);
    }, [snapshots, matches]);

    const refresh = useCallback(() => { load(true); }, [load]);

    return { cards: liveCards, loading, error, checkedAt, libraryNames, refresh };
}
