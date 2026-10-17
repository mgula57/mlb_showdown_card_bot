import { useState } from 'react';
import type { CardDatabaseRecord } from '../api/card_db/cardDatabase';
import type { TeamRosterSlot } from '../api/userTeams';
import { type RosterMove, getEligiblePositions } from '../domain/roster';

export type { RosterMove };

/** How one roster slot reads while a player is being moved. */
export type RosterMoveSlotState = {
    /** This slot holds the player being moved. */
    isMoving: boolean;
    /** The player being moved can go here (an open spot, or a swap). */
    isTarget: boolean;
    /** A move is underway and this slot can't take part in it. */
    isDimmed: boolean;
    /** What a click on the slot does mid-move: drop here, or cancel on the moving player. */
    onClick?: () => void;
};

export type RosterMoveControls = {
    movingCardId: string | null;
    isSaving: boolean;
    error: string | null;
    /** Pick up `cardId` to move it (again on the same card puts it back). */
    start: (cardId: string) => void;
    cancel: () => void;
    /** `position` is the slot's roster position - a field spot, a rotation role, or 'BE' / 'RP'
     *  for any bench / bullpen row; `occupantId` the card in it, if any. */
    slotState: (position: string, occupantId: string | null) => RosterMoveSlotState;
};

type Options = {
    roster: TeamRosterSlot[];
    cardMap: Record<string, CardDatabaseRecord | null>;
    numStarters: number;
    /** Extra rule for a move into an open spot, given the roster positions it would leave -
     *  e.g. a league draft keeping enough picks to fill what the move opens. */
    canOpen?: (positionsAfter: string[]) => boolean;
    onMove: (move: RosterMove) => Promise<void>;
};

/** Ring / fade for a slot while a player is being moved. */
export function moveSlotClass(state: RosterMoveSlotState): string {
    if (state.isTarget) return 'rounded-lg ring-2 ring-(--secondary) cursor-pointer';
    if (state.isDimmed) return 'opacity-40';
    return '';
}

const IDLE: RosterMoveSlotState = { isMoving: false, isTarget: false, isDimmed: false };

/** Bench and bullpen rows are interchangeable, so a move within one goes nowhere. */
const bucket = (position: string) => (position === 'CL' ? 'RP' : position);

/**
 * Moving a player already on the roster to another spot: pick the player up, then click an open
 * spot to move there or another player to swap the two. Only spots both players can play light
 * up. Mirrors `LeagueRosterMove` in mlb_showdown_bot/core/league/roster_move.py.
 */
export function useRosterMove({ roster, cardMap, numStarters, canOpen, onMove }: Options): RosterMoveControls {
    const [movingCardId, setMovingCardId] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const positionOf = (cardId: string) => roster.find(slot => slot.card_id === cardId)?.roster_position ?? null;
    const canPlay = (cardId: string, position: string) => {
        const card = cardMap[cardId];
        return !!card && getEligiblePositions(card, numStarters).includes(bucket(position));
    };

    function canDrop(cardId: string, position: string, occupantId: string | null): boolean {
        const from = positionOf(cardId);
        if (!from || bucket(from) === bucket(position) || !canPlay(cardId, position)) return false;
        if (occupantId) return canPlay(occupantId, from);
        if (!canOpen) return true;
        const after = roster.map(slot => (slot.card_id === cardId ? position : slot.roster_position));
        return canOpen(after);
    }

    async function drop(position: string, occupantId: string | null) {
        if (!movingCardId) return;
        setIsSaving(true);
        setError(null);
        try {
            await onMove({ cardId: movingCardId, toPosition: bucket(position), swapWithCardId: occupantId });
            setMovingCardId(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        } finally {
            setIsSaving(false);
        }
    }

    const cancel = () => { setMovingCardId(null); setError(null); };

    return {
        movingCardId,
        isSaving,
        error,
        start: cardId => { setError(null); setMovingCardId(current => (current === cardId ? null : cardId)); },
        cancel,
        slotState: (position, occupantId) => {
            if (!movingCardId) return IDLE;
            if (occupantId === movingCardId) return { isMoving: true, isTarget: false, isDimmed: false, onClick: isSaving ? undefined : cancel };
            const isTarget = !isSaving && canDrop(movingCardId, position, occupantId);
            return { isMoving: false, isTarget, isDimmed: !isTarget, onClick: isTarget ? () => drop(position, occupantId) : undefined };
        },
    };
}
