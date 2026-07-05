import { useState, useEffect, useCallback, useMemo } from 'react';
import type { CardDatabaseRecord } from '../api/card_db/cardDatabase';
import { fetchCardData } from '../api/card_db/cardDatabase';
import { CardSource } from '../types/cardSource';
import type { CardSource as CardSourceType } from '../types/cardSource';

export type CardSlotRef = { card_id: string; card_source: CardSourceType };

/**
 * Fetches cards for a list of roster slots, routing each fetch to the correct
 * source table (BOT / WOTC / WBC). Missing card IDs are stored as null to
 * prevent repeated re-fetch attempts.
 */
export function useCardMap(slots: CardSlotRef[]) {
    const [cardMap, setCardMap] = useState<Record<string, CardDatabaseRecord | null>>({});
    const [loading, setLoading] = useState(false);

    // Stable key so the effect only fires when the slot set actually changes
    const slotKey = useMemo(
        () => slots.map(s => `${s.card_id}:${s.card_source}`).sort().join(','),
        [slots],
    );

    useEffect(() => {
        // Build id→source map for slots not yet in cardMap
        const toFetch = new Map<string, CardSourceType>();
        for (const s of slots) {
            if (!(s.card_id in cardMap)) {
                toFetch.set(s.card_id, s.card_source ?? CardSource.BOT);
            }
        }
        if (toFetch.size === 0) return;

        // Group by source so each table gets one request
        const bySource = new Map<CardSourceType, string[]>();
        for (const [id, src] of toFetch) {
            if (!bySource.has(src)) bySource.set(src, []);
            bySource.get(src)!.push(id);
        }

        let cancelled = false;
        setLoading(true);
        (async () => {
            try {
                const results = await Promise.all(
                    [...bySource].map(([src, ids]) => {
                        const key = src === CardSource.BOT ? 'card_id' : 'id';
                        return fetchCardData(src, { [key]: ids, limit: ids.length });
                    }),
                );
                if (cancelled) return;
                const found = Object.fromEntries(results.flat().map(c => [c.card_id, c]));
                // Mark unfound IDs as null to prevent re-fetch on next render
                const entries = Object.fromEntries(
                    [...toFetch.keys()].map(id => [id, found[id] ?? null]),
                );
                setCardMap(prev => ({ ...prev, ...entries }));
            } catch {
                // ignore — slots will simply render without card data
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();

        return () => { cancelled = true; };
    // cardMap intentionally omitted: we only grow it, never shrink, so reading
    // it inside the effect without declaring it as a dep is safe here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [slotKey]);

    const addCard = useCallback((card: CardDatabaseRecord) => {
        setCardMap(prev => ({ ...prev, [card.card_id]: card }));
    }, []);

    return { cardMap, loading, addCard };
}
