import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';

/** A player-year the user forced into or out of the Algorithm's pool. `id` is the card record's
 * `{year}-{bref_id}-{type override}` id, so it covers that year's card in every showdown set.
 * (The backend also accepts a bare player id, meaning every year.) */
export type ManualPick = { id: string; name: string; year?: number | string };

/** Saved under the edition's `attributes.manual_picks`, separately from the algorithm settings,
 * so it updates as soon as a card is added or removed in the pool. */
export type ManualPicks = { included: ManualPick[]; excluded: ManualPick[] };

export const EMPTY_MANUAL_PICKS: ManualPicks = { included: [], excluded: [] };

export function manualPickFor(record: CardDatabaseRecord): ManualPick {
    return { id: record.id, name: record.name, year: record.year };
}

/** e.g. "2023 Aaron Judge" */
export function manualPickLabel(pick: ManualPick): string {
    return pick.year ? `${pick.year} ${pick.name}` : pick.name;
}

function isManualPickList(value: unknown): value is ManualPick[] {
    return Array.isArray(value) && value.every(p => p && typeof p === 'object' && typeof p.id === 'string');
}

export function parseManualPicks(attributes: Record<string, unknown>): ManualPicks {
    const raw = attributes.manual_picks as Partial<ManualPicks> | undefined;
    if (!raw || typeof raw !== 'object') return EMPTY_MANUAL_PICKS;
    return {
        included: isManualPickList(raw.included) ? raw.included : [],
        excluded: isManualPickList(raw.excluded) ? raw.excluded : [],
    };
}

/** Moves `pick` into `list` ('included' or 'excluded'), taking it out of the other one. */
export function withManualPick(picks: ManualPicks, pick: ManualPick, list: keyof ManualPicks): ManualPicks {
    const other: keyof ManualPicks = list === 'included' ? 'excluded' : 'included';
    return {
        [list]: [...picks[list].filter(p => p.id !== pick.id), pick],
        [other]: picks[other].filter(p => p.id !== pick.id),
    } as ManualPicks;
}

/** Takes the player with `id` out of `list`. */
export function withoutManualPick(picks: ManualPicks, id: string, list: keyof ManualPicks): ManualPicks {
    return { ...picks, [list]: picks[list].filter(p => p.id !== id) };
}
