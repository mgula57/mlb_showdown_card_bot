// Position group fallbacks: if a card lists "OF" or "IF" instead of a specific spot, map it.
const POSITION_GROUPS: Record<string, string[]> = {
    IF: ['1B', '2B', '3B', 'SS'],
    OF: ['LF', 'CF', 'RF'],
    C: ['C', 'CA'],
    CA: ['C', 'CA'],
    'LF/RF': ['LF', 'RF'],
};

export const OF_POSITIONS = ['LF', 'CF', 'RF'] as const;
export const IF_POSITIONS = ['1B', '2B', '3B', 'SS'] as const;

/**
 * Returns the defensive rating for a position from a positions_and_defense map.
 * Strips "PH-" prefixes, skips DH, and falls back to group keys (IF, OF, LF/RF).
 */
export function defenseAtPosition(
    positionsAndDefense: Record<string, number> | null | undefined,
    position: string | null | undefined,
): number | null {
    if (!positionsAndDefense || !position || position === 'DH') return null;

    const pos = position.startsWith('PH-') ? position.slice(3) : position;

    const exact = positionsAndDefense[pos];
    if (exact !== undefined) return exact;

    for (const [group, members] of Object.entries(POSITION_GROUPS)) {
        if (members.includes(pos)) {
            const groupVal = positionsAndDefense[group];
            if (groupVal !== undefined) return groupVal;
        }
    }

    return null;
}
