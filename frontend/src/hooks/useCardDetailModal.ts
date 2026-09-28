import { useCallback, useRef, useState } from 'react';
import { fetchCardById, type ShowdownBotCardAPIResponse } from '../api/showdownBotCard';

/**
 * Lazily fetches a full `ShowdownBotCard` for a (card_id, source) pair on demand and holds the
 * "currently open in a modal" selection — the same click-to-open pattern `GameDetail.tsx` uses
 * for boxscore rows, generalized so any table backed by a lighter-weight card record (e.g.
 * `CardDatabaseRecord`) can open the same full-card modal without refetching on repeat clicks.
 */
export function useCardDetailModal() {
    const [selected, setSelected] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [fetchingId, setFetchingId] = useState<string | null>(null);
    const cache = useRef<Map<string, ShowdownBotCardAPIResponse>>(new Map());

    const open = useCallback((cardId: string, source: string) => {
        const cached = cache.current.get(cardId);
        if (cached) {
            setSelected(cached);
            return;
        }
        setFetchingId(cardId);
        fetchCardById(cardId, source)
            .then((resp) => {
                cache.current.set(cardId, resp);
                setSelected(resp);
            })
            .catch(() => { /* card fetch is supplementary — fail silently, same as GameDetail */ })
            .finally(() => setFetchingId((current) => (current === cardId ? null : current)));
    }, []);

    const close = useCallback(() => setSelected(null), []);

    return { selected, open, close, isFetching: (cardId: string) => fetchingId === cardId };
}
