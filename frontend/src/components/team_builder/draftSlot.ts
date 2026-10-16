/**
 * @fileoverview The roster slot a drafter clicked to fill, shared by the team builder and the
 * league draft room: which search filters it implies, how it's labelled, and how the field view /
 * depth chart highlight it.
 */
import type { LineupSlot, PitcherAssignment } from '../../api/userTeams';
import type { FilterSelections } from '../cards/ShowdownCardSearch';

export type PendingSlot =
    | { kind: 'field'; position: string; current: LineupSlot | null }
    | { kind: 'rotation'; role: string; current: PitcherAssignment | null }
    | { kind: 'bench'; current: { card_id: string } | null }
    | { kind: 'bullpen'; current: { card_id: string } | null }
    | { kind: 'roster' };

/** Card search filters that narrow the pool to cards that can fill `slot`. */
export function getSearchFiltersForSlot(slot: PendingSlot | null): Partial<FilterSelections> {
    if (!slot) return {};
    if (slot.kind === 'field') {
        if (slot.position === 'SP') return { positions: ['STARTER'] };
        const posMap: Record<string, string[]> = {
            C: ['C'], '1B': ['1B'], '2B': ['2B'], '3B': ['3B'],
            SS: ['SS'], LF: ['LF/RF'], RF: ['LF/RF'], CF: ['CF'], DH: ['DH'],
        };
        const positions = posMap[slot.position];
        return { ...(positions ? { positions } : {}), player_type: ['HITTER'] };
    }
    if (slot.kind === 'rotation') {
        if (slot.role.startsWith('SP')) return { positions: ['STARTER'] };
        return { positions: ['RELIEVER', 'CLOSER'] };
    }
    if (slot.kind === 'bullpen') {
        return { positions: ['RELIEVER', 'CLOSER'] };
    }
    if (slot.kind === 'bench') {
        return { player_type: ['HITTER'] };
    }
    return {};
}

/** "Filling: SS", "Adding to Bench", ... - or null when no slot is being filled. */
export function pendingSlotLabel(slot: PendingSlot | null): string | null {
    if (!slot) return null;
    switch (slot.kind) {
        case 'field': return `Filling: ${slot.position}`;
        case 'rotation': return `Filling: ${slot.role}`;
        case 'bullpen': return slot.current ? 'Replacing bullpen arm' : 'Adding to Bullpen';
        case 'bench': return slot.current ? 'Replacing bench player' : 'Adding to Bench';
        default: return 'Adding to roster';
    }
}

/** The `activePosition` / `activeRole` FieldView and DepthChartPanel highlight for `slot`. */
export function pendingSlotHighlight(slot: PendingSlot | null): { activePosition: string | null; activeRole: string | null } {
    return {
        activePosition: slot?.kind === 'field' ? slot.position : null,
        activeRole: slot?.kind === 'rotation' ? slot.role
            : slot?.kind === 'bullpen' ? 'RP'
            : slot?.kind === 'bench' ? 'BE'
            : null,
    };
}
