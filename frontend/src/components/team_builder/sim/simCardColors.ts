import type { CardDatabaseRecord } from '../../../api/card_db/cardDatabase';
import type { SimTeamIdentity } from '../../../api/sim';

/** A card recolored to the sim club it played for - a takeover/tournament team's players should
 *  wear that team's colors, not their card's own archived ones. Unchanged without an identity. */
export function withSimTeamColors(
    record: CardDatabaseRecord | null | undefined,
    identity: SimTeamIdentity | null | undefined,
    team?: string | null,
): CardDatabaseRecord | null | undefined {
    if (!record || !identity) return record;
    return {
        ...record,
        team: team ?? record.team,
        color_primary: identity.primary_color ?? record.color_primary,
        color_secondary: identity.secondary_color ?? record.color_secondary,
    };
}
