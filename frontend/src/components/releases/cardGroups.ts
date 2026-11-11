import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';

// Card grouping shared by the release Summary charts and the pool's group-by options.

export const PARENT_POSITION_ORDER = ['Position Player', 'Starting Pitcher', 'Relief Pitcher'] as const;
export type ParentPositionGroup = typeof PARENT_POSITION_ORDER[number];

/** Closers (and any other non-starter pitcher) roll up into Relief Pitcher. */
export function parentPositionGroup(snapshot: CardDatabaseRecord): ParentPositionGroup {
    if (!snapshot.is_pitcher) return 'Position Player';
    return (snapshot.positions_list ?? []).includes('STARTER') ? 'Starting Pitcher' : 'Relief Pitcher';
}

// Scorecard order (C through RF), with the grouped IF/OF/LF-RF ratings older sets use slotted in beside their members.
export const DEFENSE_POSITION_ORDER = ['C', 'CA', '1B', '2B', '3B', 'SS', 'IF', 'LF', 'LF/RF', 'CF', 'RF', 'OF'];

/** Scorecard order for a card's primary position, hitters then pitchers. */
export const POSITION_ORDER = [...DEFENSE_POSITION_ORDER, 'DH', 'STARTER', 'RELIEVER', 'CLOSER'];

/** "Bats L/R/S" for hitters, "LHP/RHP" for pitchers; null when unknown. Hand is stored as "Left"/"Right"/"Both" or a single letter. */
export function handLabel(snapshot: CardDatabaseRecord): string | null {
    const letter = (snapshot.hand ?? '').trim().charAt(0).toUpperCase();
    if (!letter) return null;
    if (snapshot.is_pitcher) return `${letter}HP`;
    return `Bats ${letter === 'B' ? 'S' : letter}`;
}

export const HAND_ORDER = ['Bats R', 'Bats L', 'Bats S', 'RHP', 'LHP', 'Unknown'];

/** Historical team codes (as on WOTC cards) mapped to the franchise's current code, so the Teams
 * breakdown groups e.g. WOTC's MON with WSN. Applies to both sets, which keeps the comparison aligned. */
export const FRANCHISE_CODE: Record<string, string> = {
    MON: 'WSN',
    FLA: 'MIA',
    CAL: 'LAA',
    ANA: 'LAA',
    TBD: 'TBR',
    OAK: 'ATH',
};
