/**
 * @fileoverview Default payload for a brand-new user team. A team is now created immediately
 * (with these defaults) when the user clicks "New Team" — configuration happens on the team
 * page's setup step, not in a pre-creation modal — so the same defaults back the plain
 * "New Team" flow and the challenge Quick Start / Build from Scratch flows.
 */
import type { TeamCreatePayload } from '../api/userTeams';
import { CardSource } from '../types/cardSource';

type BuildDefaultTeamPayloadArgs = {
    /** A single display handle, e.g. the profile username or the email local-part. */
    displayName: string;
    /** The user's preferred Showdown set — the team pins to this for its Bot cards. */
    showdownSet: string;
    /** Merged last — e.g. a challenge's pts_limit / origin_template_id / player_filters. */
    overrides?: Partial<TeamCreatePayload>;
};

export function buildDefaultTeamPayload({ displayName, showdownSet, overrides }: BuildDefaultTeamPayloadArgs): TeamCreatePayload {
    const name = `${displayName} New Team`;
    const abbreviation = displayName.replace(/[^a-zA-Z0-9]/g, '').slice(0, 5).toUpperCase() || 'TEAM';
    return {
        name,
        abbreviation,
        primary_color: 'rgb(0, 0, 0)',
        secondary_color: 'rgb(255, 255, 255)',
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
