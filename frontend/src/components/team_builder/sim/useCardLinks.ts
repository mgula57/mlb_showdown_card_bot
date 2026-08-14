import { useMemo } from 'react';
import type { SimStatLine } from '../../../api/sim';
import { useCardMap, type CardSlotRef } from '../../../hooks/useCardMap';
import { useCardDetailModal } from '../../../hooks/useCardDetailModal';
import type { CardSource as CardSourceType } from '../../../types/cardSource';

/**
 * Links a list of `SimStatLine`s to their real Showdown cards via `(id, card_source)` — shared by
 * every sim result view that lists players (batting/pitching, league leaders, awards) so each
 * only owns one `useCardMap`/`useCardDetailModal` pair instead of re-deriving this wiring.
 */
export function useCardLinks(rows: SimStatLine[], enabled: boolean) {
    const slots: CardSlotRef[] = useMemo(() => (
        enabled
            ? rows.filter((r): r is SimStatLine & { card_source: string } => !!r.card_source)
                .map(r => ({ card_id: r.id, card_source: r.card_source as CardSourceType }))
            : []
    ), [rows, enabled]);
    const { cardMap, loading: isLoadingCards } = useCardMap(slots);
    const { selected, open, close, isFetching } = useCardDetailModal();

    const recordFor = (row: SimStatLine) => (enabled && row.card_source ? cardMap[row.id] : undefined);
    const isLoadingCard = (row: SimStatLine) =>
        enabled && !!row.card_source && isLoadingCards && cardMap[row.id] === undefined;

    return { cardMap, isLoadingCards, recordFor, isLoadingCard, selected, open, close, isFetching };
}
