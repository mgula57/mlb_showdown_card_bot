/**
 * @fileoverview Default payload for a brand-new user team. A team is now created immediately
 * (with these defaults) when the user clicks "New Team" — configuration happens on the team
 * page's setup step, not in a pre-creation modal — so the same defaults back the plain
 * "New Team" flow and a challenge's "New Team" flow (which layers challenge-specific
 * overrides — name, budget, 26-man roster — on top).
 */
import type { TeamCreatePayload } from '../api/userTeams';
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
