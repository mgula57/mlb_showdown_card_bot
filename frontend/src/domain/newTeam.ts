/**
 * @fileoverview Default payload for a brand-new user team. A team is now created immediately
 * (with these defaults) when the user clicks "New Team" — configuration happens on the team
 * page's setup step, not in a pre-creation modal — so the same defaults back the plain
 * "New Team" flow and a challenge's "New Team" flow (which layers challenge-specific
 * overrides — name, budget, 26-man roster — on top).
 */
import type { TeamCreatePayload, TeamRosterSlot } from '../api/userTeams';
import { CardSource } from '../types/cardSource';
import { DEFAULT_PRIMARY_COLOR, DEFAULT_SECONDARY_COLOR } from '../api/userSettings';

type BuildDefaultTeamPayloadArgs = {
    /** A single display handle, e.g. the profile username or the email local-part. */
    displayName: string;
    /** The user's preferred Showdown set — the team pins to this for its Bot cards. */
    showdownSet: string;
    /** The user's saved default team colors (account settings), used in place of the stock
     *  Showdown blue/red when set. */
    defaultPrimaryColor?: string;
    defaultSecondaryColor?: string;
    /** Merged last — e.g. a challenge's pts_limit / origin_template_id / player_filters, or the
     *  creation_source tag identifying which entry point built the team. */
    overrides?: Partial<TeamCreatePayload>;
};

/** Appends a "next" ordinal to a base name, e.g. for the Nth auto-named team sharing that base.
 *  `priorCount` is how many teams already exist with that base name (0 for the first one). The
 *  first team is left unnumbered ("Name"), matching how people naturally count: the second is
 *  "Name 2", not "Name 1". */
export function numberedName(base: string, priorCount: number): string {
    return priorCount === 0 ? base : `${base} ${priorCount + 1}`;
}

export function buildDefaultTeamPayload({ displayName, showdownSet, defaultPrimaryColor, defaultSecondaryColor, overrides }: BuildDefaultTeamPayloadArgs): TeamCreatePayload {
    const name = `${displayName} New Team`;
    const abbreviation = displayName.replace(/[^a-zA-Z0-9]/g, '').slice(0, 5).toUpperCase() || 'TEAM';
    return {
        name,
        abbreviation,
        primary_color: defaultPrimaryColor ?? DEFAULT_PRIMARY_COLOR,
        secondary_color: defaultSecondaryColor ?? DEFAULT_SECONDARY_COLOR,
        is_public: true,
        pts_limit: 5000,
        roster_size: 20,
        min_bench: 2,
        min_bullpen: 5,
        num_starters: 4,
        bench_pts_multiplier: 0.2,
        // A new team starts as a single-set Bot team; the settings step opens up WOTC / Customs
        // (and their combinable sets) from there.
        allowed_card_sources: [CardSource.BOT],
        allowed_sets: [showdownSet],
        allowed_sets_by_source: { [CardSource.BOT]: [showdownSet] },
        ...overrides,
    };
}

/** A player a challenge requires on the roster (`required_players` in its `player_filters`). */
export type RequiredPlayer = { bref_id: string; position: string; name?: string };

/** Splits a challenge's `player_filters` into the real picker filters and its `required_players`.
 *  The latter is a challenge-only convention key, so it's kept off the team's own filters. */
export function splitRequiredPlayers(playerFilters: Record<string, unknown> | null | undefined): {
    filters: Record<string, unknown> | null;
    required: RequiredPlayer[];
} {
    if (!playerFilters) return { filters: null, required: [] };
    const { required_players, ...filters } = playerFilters;
    return { filters: Object.keys(filters).length ? filters : null, required: (required_players as RequiredPlayer[] | undefined) ?? [] };
}

/** Roster slots that pre-populate a challenge's new team with its required players, each at the
 *  position the challenge names (e.g. Mantle in CF). The card is the player's `year` card in the
 *  team's own Showdown set. */
export function requiredPlayerSlots(required: RequiredPlayer[], year: number, showdownSet: string): TeamRosterSlot[] {
    return required.map((player, index) => ({
        card_id: `${year}-${player.bref_id}-${showdownSet}`,
        card_source: CardSource.BOT,
        roster_position: player.position,
        // Non-null so they show as the first picks in the draft history (which hides null orders).
        draft_order: index + 1,
        pick_source: 'IMPORTED',
    }));
}
