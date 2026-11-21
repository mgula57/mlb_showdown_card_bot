import { useEffect, useState } from 'react';
import { fetchCardById, type ShowdownBotCard, type ShowdownBotCardAPIResponse } from '../api/showdownBotCard';

/** A card picked from a list. `cardId` marks a slim card (e.g. from the transactions feed, which
 * strips the detail-only diagnostics: points breakdown, chart accuracy, real vs projected stats)
 * whose full version should be fetched before opening CardDetail. */
export type CardSelection = { card: ShowdownBotCard; cardId?: string | null };

// Full cards already fetched this session, keyed by card id
const fullCardCache = new Map<string, ShowdownBotCardAPIResponse>();

/**
 * The response to hand CardDetail for a selected card. A slim card is swapped for the full card
 * fetched by id; until it lands `data` is null and `isLoading` true (CardDetail treats the same
 * player arriving twice as one card, so it can't start slim and upgrade in place). Falls back to
 * the slim card if the fetch fails.
 */
export function useFullCardResponse(selection: CardSelection | null, source: string): { data: ShowdownBotCardAPIResponse | null; isLoading: boolean } {
    const cardId = selection?.cardId ?? null;
    const [result, setResult] = useState<{ id: string; response: ShowdownBotCardAPIResponse | null } | null>(null);

    useEffect(() => {
        if (!cardId || fullCardCache.has(cardId)) return;
        let isCurrent = true;
        fetchCardById(cardId, source)
            .then((response) => {
                if (response?.card) fullCardCache.set(cardId, response);
                if (isCurrent) setResult({ id: cardId, response: response?.card ? response : null });
            })
            .catch(() => { if (isCurrent) setResult({ id: cardId, response: null }); });
        return () => { isCurrent = false; };
    }, [cardId, source]);

    if (!selection) return { data: null, isLoading: false };
    const slim = { card: selection.card } as ShowdownBotCardAPIResponse;
    if (!cardId) return { data: slim, isLoading: false };
    const cached = fullCardCache.get(cardId);
    if (cached) return { data: cached, isLoading: false };
    if (result?.id !== cardId) return { data: null, isLoading: true };
    return { data: result.response ?? slim, isLoading: false };
}
