/**
 * @fileoverview Player search results (`GET /api/players/search`) and how two-way players' Hitter
 * and Pitcher results merge into one row. Shared by PlayerSearchInput and the Custom Card Builder's
 * two-way check on hand-typed names.
 */

/**
 * Player search result option with comprehensive metadata
 */
export interface PlayerSearchOption {
    /** Player's full name */
    name: string;
    /** Season year or special designation (CAREER, etc.) */
    year: number | string;
    /** Formatted year display (e.g., "2020-2024" for multi-year) */
    year_display?: string | null;
    /** Baseball Reference player ID or MLB player ID */
    player_id: string;
    /** Whether player is in Hall of Fame */
    is_hof: boolean;
    /** Summary of major awards (MVP, Cy Young, etc.) */
    award_summary?: string | null;
    /** Either bWAR or fWAR depending on the source */
    war: number;
    /** Type of WAR (bWAR or fWAR) */
    war_type?: string | null;
    /** Team abbreviation for the season */
    team?: string | null;
    /** Override for player type (Hitter/Pitcher) if ambiguous */
    player_type_override?: string | null;
}

export type PlayerTypeKey = 'HITTER' | 'PITCHER';

/** A result row. Two-way players come back as a Hitter and a Pitcher result for the same season,
 *  merged into one row whose `versions` hold both. */
export type PlayerSearchRow = PlayerSearchOption & {
    versions?: Partial<Record<PlayerTypeKey, PlayerSearchOption>>;
};

/** "(Hitter)" -> "HITTER" */
export const playerTypeKey = (override?: string | null): PlayerTypeKey | undefined => {
    const key = override?.toUpperCase().replace(/[()]/g, '').trim();
    return key === 'HITTER' || key === 'PITCHER' ? key : undefined;
};

const seasonKey = (option: PlayerSearchOption) => `${option.year}-${option.player_id}`;

/** Merges each season's Hitter/Pitcher results into one row, kept where the first of them ranked.
 *  player_search often tags only one side (e.g. "(pitcher)") and leaves the other untyped, so an
 *  untyped result is the other side when its season has a tagged one. */
export const mergeTwoWayRows = (results: PlayerSearchOption[]): PlayerSearchRow[] => {
    const taggedTypes = new Map<string, PlayerTypeKey>();
    for (const option of results) {
        const type = playerTypeKey(option.player_type_override);
        if (type) taggedTypes.set(seasonKey(option), type);
    }
    const rows: PlayerSearchRow[] = [];
    const rowsByKey = new Map<string, PlayerSearchRow>();
    for (const option of results) {
        const taggedType = taggedTypes.get(seasonKey(option));
        const type = playerTypeKey(option.player_type_override)
            ?? (taggedType ? (taggedType === 'HITTER' ? 'PITCHER' : 'HITTER') : undefined);
        if (!type) {
            rows.push(option);
            continue;
        }
        const key = seasonKey(option);
        const existing = rowsByKey.get(key);
        if (existing?.versions) {
            existing.versions[type] = option;
            continue;
        }
        const row: PlayerSearchRow = { ...option, versions: { [type]: option } };
        rowsByKey.set(key, row);
        rows.push(row);
    }
    return rows;
};

/** Both sides came back, so the row offers a version choice */
export const isTwoWayRow = (row: PlayerSearchRow | undefined): boolean => !!row?.versions?.HITTER && !!row.versions.PITCHER;

/** Search names are stored lowercase; typed names may carry a "(HITTER)"-style suffix */
const normalizedName = (name: string) => name.replace(/\s*\((hitter|hitting|pitcher|pitching)\)/gi, '').trim().toLowerCase();

/** Whether a hand-typed name (and year, if it's a single season) is a two-way player: some season
 *  of that exact name comes back with both a Hitter and a Pitcher result. */
export async function fetchIsTwoWayPlayer(name: string, year: string, signal?: AbortSignal): Promise<boolean> {
    const target = normalizedName(name);
    if (target.length < 3) return false;
    const season = /^\d{4}$/.test(year.trim()) ? ` ${year.trim()}` : '';
    const response = await fetch(`/api/players/search?${new URLSearchParams({ q: `${target}${season}` })}`, { signal });
    if (!response.ok) return false;
    const rows = mergeTwoWayRows(await response.json());
    return rows.some(row => isTwoWayRow(row) && normalizedName(row.name) === target);
}
