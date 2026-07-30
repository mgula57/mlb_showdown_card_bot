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
