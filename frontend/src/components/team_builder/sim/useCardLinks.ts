import { useMemo, useState } from 'react';
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
    const { selected, open: openModal, close, isFetching } = useCardDetailModal();
    // THE SIM STATLINE BEHIND THE CARD CURRENTLY OPEN IN THE MODAL - feeds CardDetail's `simStats`
    // so its "Card vs Real Stats" table can show what this player did in THIS simulated season.
    const [selectedSimStats, setSelectedSimStats] = useState<Record<string, number> | undefined>(undefined);

    const recordFor = (row: SimStatLine) => (enabled && row.card_source ? cardMap[row.id] : undefined);
    const isLoadingCard = (row: SimStatLine) =>
        enabled && !!row.card_source && isLoadingCards && cardMap[row.id] === undefined;

    const open = (cardId: string, source: string, stats?: Record<string, number>) => {
        setSelectedSimStats(stats);
        openModal(cardId, source);
    };

    return { cardMap, isLoadingCards, recordFor, isLoadingCard, selected, selectedSimStats, open, close, isFetching };
}
