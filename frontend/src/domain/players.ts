/**
 * @fileoverview Single home for the two-way-player card-map key convention, previously
 * duplicated (with three different key formats) across GameSchedule, GameItem, GameDetail,
 * SeasonLeaders, and AwardWinners.
 */

// TODO: replace hard-coded IDs with a general two-way player detection strategy
export const TWO_WAY_PLAYER_IDS = new Set([660271]); // Ohtani

/** Returns the cardMap key for a player, adding a role suffix for two-way players. */
export const cardKey = (id: number, role: "H" | "P"): string =>
    TWO_WAY_PLAYER_IDS.has(id) ? `${id}-${role}` : String(id);

/** cardKey() is keyed on numeric MLB player ids; sim card_ids (strings) don't need the two-way suffix. */
export const resolveCardKey = (id: number | string | undefined, role: "H" | "P"): string | undefined => {
    if (id == null) return undefined;
    return typeof id === "number" ? cardKey(id, role) : String(id);
};
