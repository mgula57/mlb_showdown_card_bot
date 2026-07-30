/**
 * @fileoverview Canonical team view model shared by every surface that renders a team chip
 * (real MLB, box scores, leaders, historical teams, user rosters, and eventually sim/PVP teams).
 *
 * This is a view model, not a wire type — API modules keep their own response shapes; the
 * `domain/adapters/*` map them into this at the boundary.
 */

export type TeamIdentity = {
    /** Stable dedupe/react key, e.g. "147-2026" for an MLB team-season, or a team_id for a roster. */
    key: string;
    id?: number | string;
    abbreviation: string;
    name: string;
    primaryColor?: string;
    secondaryColor?: string;
    /** Resolved once at the adapter boundary — components should never re-derive this from sportId. */
    countryCode?: string | null;
};

export type TeamRecordLine = {
    wins: number;
    losses: number;
    pct?: number;
    gamesBack?: string;
    points?: number;
};
