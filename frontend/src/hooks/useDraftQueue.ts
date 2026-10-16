import { useCallback, useMemo, useState } from 'react';
import type { CardDatabaseRecord } from '../api/card_db/cardDatabase';

const STORAGE_PREFIX = 'league-draft-queue';

function load(key: string): CardDatabaseRecord[] {
    try {
        const raw = localStorage.getItem(key);
        const parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
}

function save(key: string, cards: CardDatabaseRecord[]) {
    try {
        localStorage.setItem(key, JSON.stringify(cards));
    } catch {
        // Storage full or blocked - the queue still works for this visit
    }
}

/**
 * The drafter's own ranked wish list for one league season's draft. Kept in this browser
 * (localStorage) - it's private, and only steers the drafter's own picks. Cards are stored whole
 * so the list renders without refetching. Anything in `draftedIds` is hidden as soon as it's
 * drafted, and pruned from storage on the next change.
 */
export function useDraftQueue(leagueId: string, seasonNumber: number, draftedIds: string[]) {
    const key = `${STORAGE_PREFIX}:${leagueId}:${seasonNumber}`;
    const [stored, setStored] = useState<CardDatabaseRecord[]>(() => load(key));
    const drafted = useMemo(() => new Set(draftedIds), [draftedIds]);

    // Each change also prunes cards drafted since (by anyone), so the saved list doesn't grow stale
    const update = useCallback((next: (cards: CardDatabaseRecord[]) => CardDatabaseRecord[]) => {
        setStored(prev => {
            const cards = next(prev.filter(card => !drafted.has(card.id)));
            save(key, cards);
            return cards;
        });
    }, [key, drafted]);

    const queue = useMemo(() => stored.filter(card => !drafted.has(card.id)), [stored, drafted]);
    const queuedIds = useMemo(() => new Set(queue.map(card => card.id)), [queue]);

    return {
        queue,
        isQueued: (cardId: string) => queuedIds.has(cardId),
        toggle: (card: CardDatabaseRecord) => update(cards =>
            cards.some(c => c.id === card.id) ? cards.filter(c => c.id !== card.id) : [...cards, card]),
        remove: (cardId: string) => update(cards => cards.filter(c => c.id !== cardId)),
        /** Move a card one spot up (-1) or down (+1). */
        move: (cardId: string, direction: -1 | 1) => update(cards => {
            const index = cards.findIndex(c => c.id === cardId);
            const target = index + direction;
            if (index < 0 || target < 0 || target >= cards.length) return cards;
            const next = [...cards];
            [next[index], next[target]] = [next[target], next[index]];
            return next;
        }),
    };
}
