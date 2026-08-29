import type { CardSource } from '../types/cardSource';
import type { CardDatabaseRecord } from './card_db/cardDatabase';
import { activeSources, allowedSetsForSource } from '../domain/teamSets';

const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// =============================================================================
// MARK: - TYPES
// =============================================================================

export type PickSource = 'MANUAL' | 'AUTOFILL' | 'IMPORTED';

export type TeamRosterSlot = {
    card_id: string;
    card_source: CardSource;
    roster_position: string;
    draft_order: number | null;
    pick_source: PickSource;
};

export type LineupSlot = {
    card_id: string;
    card_source: CardSource;
    /** Server-derived from roster_position — read-only, never sent to the backend. */
    field_position: string;
    batting_order: number; // 1–9
};

export type Lineup = {
    name: string;
    /** 0 = computed Default (read-only). >0 = user-created, persisted. */
    index: number;
    slots: LineupSlot[];
};

export type PitcherAssignment = {
    card_id: string;
    card_source: CardSource;
    role: string;
};

export type TeamSource = 'user' | 'official' | 'asg' | 'mlb';

export type Team = {
    team_id: string;
    user_id: string | null;
    name: string;
    abbreviation: string;
    primary_color: string;
    secondary_color: string;
    is_public: boolean;
    source: TeamSource;
    logo_url: string | null;
    pts_limit: number | null;
    roster_size: number;
    min_bench: number;
    min_bullpen: number;
    num_starters: number;
    bench_pts_multiplier: number;
    allowed_sets: string[] | null;
    /** Per-source set restrictions — the source of truth; `allowed_sets` mirrors its union. */
    allowed_sets_by_source?: Record<string, string[]> | null;
    allowed_card_sources: string[] | null;
    /** Which challenge_template this team was built for, if any — set by the Quick Start /
     *  Build from Scratch challenge routes, null for teams built outside that flow. */
    origin_template_id: string | null;
    player_filters: Record<string, unknown> | null;
    roster: TeamRosterSlot[];
    lineups: Lineup[];
    rotation: PitcherAssignment[];
    created_at: string | null;
    updated_at: string | null;
    total_points: number;
};

/**
 * Lightweight team shape returned by the list endpoints (user + public teams).
 * Excludes the full roster/lineups/rotation — carries only what the team list and
 * Recent carousel render: counts, total points, a precomputed drafting flag, and the
 * top-3 player cards (already hydrated server-side, so the carousel needs no extra fetches).
 */
export type TeamSummary = {
    team_id: string;
    user_id: string | null;
    name: string;
    abbreviation: string;
    primary_color: string;
    secondary_color: string;
    is_public: boolean;
    source: TeamSource;
    logo_url: string | null;
    pts_limit: number | null;
    roster_size: number;
    min_bench: number;
    min_bullpen: number;
    num_starters: number;
    bench_pts_multiplier: number;
    allowed_sets: string[] | null;
    allowed_sets_by_source?: Record<string, string[]> | null;
    allowed_card_sources: string[] | null;
    origin_template_id: string | null;
    created_at: string | null;
    updated_at: string | null;
    total_points: number;
    roster_count: number;
    is_drafting: boolean;
    top_players: CardDatabaseRecord[];
};

const FIELD_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'] as const;

/**
 * Rotation role slots, SP1..SP10. The builder supports up to `MAX_STARTERS` starters
 * (`num_starters`); a team's active rotation is `ROTATION_ROLES.slice(0, num_starters)`.
 * Keep in sync with ROTATION_ROLES / MAX_STARTERS in
 * mlb_showdown_bot/core/card/team_builder/team.py.
 */
export const MAX_STARTERS = 10;
export const ROTATION_ROLES: string[] = Array.from({ length: MAX_STARTERS }, (_, i) => `SP${i + 1}`);
export const BULLPEN_ROLES: string[] = ['RP', 'CL'];

export function isTeamDrafting(team: Team): boolean {
    if (team.source === 'mlb') return false;

    const slots = team.lineups[0]?.slots ?? [];
    const filledLineup = FIELD_POSITIONS.filter(pos => slots.some(s => s.field_position === pos)).length;
    if (filledLineup < 9) return true;

    const starterRoles = ROTATION_ROLES.slice(0, team.num_starters);
    const filledStarters = team.rotation.filter(r => starterRoles.includes(r.role)).length;
    if (filledStarters < team.num_starters) return true;

    const filledBench = team.roster.filter(s => s.roster_position === 'BE').length;
    if (filledBench < team.min_bench) return true;

    const filledBullpen = team.rotation.filter(r => !ROTATION_ROLES.includes(r.role)).length;
    if (filledBullpen < team.min_bullpen) return true;

    return false;
}

/**
 * Whether a team's settings are internally consistent enough to move on from the setup step
 * into drafting: it has an identity, the required roster buckets fit inside the roster size,
 * the points budget can cover a minimal roster, and every drafted-from source has ≥1 set.
 */
export function isTeamSetupValid(team: Partial<Team>): boolean {
    const name = (team.name ?? '').trim();
    const abbreviation = (team.abbreviation ?? '').trim();
    const rosterSize = team.roster_size ?? 20;
    const numStarters = team.num_starters ?? 4;
    const minBullpen = team.min_bullpen ?? 5;
    const minBench = team.min_bench ?? 2;

    const rosterUsed = 9 + numStarters + minBullpen + minBench;
    const rosterValid = rosterUsed <= rosterSize;
    const ptsValid = team.pts_limit == null || team.pts_limit >= rosterSize * 10;
    const setsValid = activeSources(team).every(source => allowedSetsForSource(team, source).length > 0);

    return name.length > 0 && abbreviation.length > 0 && rosterValid && ptsValid && setsValid;
}

export type TeamCreatePayload = Partial<Omit<Team, 'team_id' | 'user_id' | 'created_at' | 'updated_at'>> & {
    name: string;
    abbreviation: string;
};

export type TeamUpdatePayload = Partial<Omit<Team, 'team_id' | 'user_id' | 'created_at' | 'updated_at'>>;

// =============================================================================
// MARK: - API CALLS
// =============================================================================

export async function fetchUserTeams(token: string): Promise<TeamSummary[]> {
    const res = await fetch(`${API_BASE}/user/teams`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Failed to fetch teams: ${res.status}`);
    return res.json();
}

export async function fetchPublicTeams(source?: TeamSource, limit = 50, offset = 0, q?: string): Promise<TeamSummary[]> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (source) params.set('source', source);
    if (q) params.set('q', q);
    const res = await fetch(`${API_BASE}/teams/public?${params}`);
    if (!res.ok) throw new Error(`Failed to fetch public teams: ${res.status}`);
    return res.json();
}

export async function fetchTeam(teamId: string, token?: string): Promise<Team> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/user/teams/${teamId}`, { headers });
    if (!res.ok) throw new Error(`Failed to fetch team: ${res.status}`);
    return res.json();
}

export async function createTeam(payload: TeamCreatePayload, token: string): Promise<Team> {
    const res = await fetch(`${API_BASE}/user/teams`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to create team: ${res.status}`);
    }
    return res.json();
}

/**
 * Fork a (public) team into a new team owned by the current user. Copies the roster, settings,
 * and any user-created lineups. Roster slots are marked IMPORTED. The copy is always private.
 */
export async function forkTeam(teamId: string, token: string): Promise<Team> {
    const source = await fetchTeam(teamId, token);
    const payload: TeamCreatePayload = {
        name: `${source.name} (Copy)`,
        abbreviation: source.abbreviation,
        primary_color: source.primary_color,
        secondary_color: source.secondary_color,
        is_public: false,
        pts_limit: source.pts_limit,
        roster_size: source.roster_size,
        min_bench: source.min_bench,
        min_bullpen: source.min_bullpen,
        num_starters: source.num_starters,
        bench_pts_multiplier: source.bench_pts_multiplier,
        allowed_sets: source.allowed_sets,
        allowed_sets_by_source: source.allowed_sets_by_source,
        allowed_card_sources: source.allowed_card_sources,
        player_filters: source.player_filters,
        // roster_position encodes rotation roles (SP1..CL) and bench (BE), so the rotation is
        // rederived server-side — only the roster slots need to be copied.
        roster: source.roster.map(slot => ({ ...slot, pick_source: 'IMPORTED', draft_order: null })),
        // Only user-created lineups (index > 0) are persisted; the Default (index 0) is computed.
        lineups: source.lineups.filter(l => l.index > 0),
    };
    return createTeam(payload, token);
}

export async function updateTeam(teamId: string, payload: TeamUpdatePayload, token: string): Promise<Team> {
    const res = await fetch(`${API_BASE}/user/teams/${teamId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to update team: ${res.status}`);
    }
    return res.json();
}

export async function uploadTeamLogo(teamId: string, file: File, token: string): Promise<Team> {
    const formData = new FormData();
    formData.append('logo', file);
    const res = await fetch(`${API_BASE}/user/teams/${teamId}/logo`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to upload logo: ${res.status}`);
    }
    return res.json();
}

export async function deleteTeamLogo(teamId: string, token: string): Promise<Team> {
    const res = await fetch(`${API_BASE}/user/teams/${teamId}/logo`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to delete logo: ${res.status}`);
    }
    return res.json();
}

export async function deleteTeam(teamId: string, token: string): Promise<void> {
    const res = await fetch(`${API_BASE}/user/teams/${teamId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to delete team: ${res.status}`);
    }
}

// ---------------------------------------------------------------------------
// Autofill
// ---------------------------------------------------------------------------

export type PtsDistribution = {
    offense: number;   // fractions summing to 1.0
    rotation: number;
    bullpen: number;
    bench: number;
};

export type AutofillStrategy = {
    pts_distribution: PtsDistribution;
    pitching_strategy: string | null;
    hitting_strategy: string | null;
    defense_strategy: string | null;
    catcher_defense_strategy: string | null;
    /** Only sent when the team has no pts_limit — the one-off target the user picked in the modal. */
    pts_target?: number;
};

export type AutofillResult = {
    roster: TeamRosterSlot[];
    lineups: Lineup[];
    rotation: PitcherAssignment[];
};

export const DEFAULT_PTS_DISTRIBUTION: PtsDistribution = {
    offense: 0.52,
    rotation: 0.28,
    bullpen: 0.19,
    bench: 0.01,
};

export const AUTOFILL_PRESETS: { label: string; distribution: PtsDistribution }[] = [
    { label: 'Balanced',        distribution: { offense: 0.52, rotation: 0.28, bullpen: 0.19, bench: 0.01 } },
    { label: 'Ace-Heavy',       distribution: { offense: 0.42, rotation: 0.38, bullpen: 0.18, bench: 0.02 } },
    { label: 'Power Lineup',    distribution: { offense: 0.57, rotation: 0.25, bullpen: 0.17, bench: 0.01 } },
    { label: 'Lights-Out Pen',  distribution: { offense: 0.47, rotation: 0.25, bullpen: 0.27, bench: 0.01 } },
];

export const PITCHING_STRATEGY_OPTIONS: { value: string | null; label: string }[] = [
    { value: null, label: 'Balanced' },
    { value: 'high_control', label: 'High Control' },
    { value: 'groundball', label: 'Groundball' },
    { value: 'no_doubles', label: 'No Doubles' },
    { value: 'strikeout', label: 'Strikeout Stuff' },
];

export const HITTING_STRATEGY_OPTIONS: { value: string | null; label: string }[] = [
    { value: null, label: 'Balanced' },
    { value: 'high_ob', label: 'High OB' },
    { value: 'speed', label: 'Speed' },
    { value: 'slug', label: 'Slug' },
    { value: 'contact', label: 'Contact' },
];

export const DEFENSE_STRATEGY_OPTIONS: { value: string | null; label: string }[] = [
    { value: null, label: 'Balanced' },
    { value: 'low_defense', label: 'Low' },
    { value: 'high_defense', label: 'High' },
    { value: 'elite_defense', label: 'Elite' },
];

export const CATCHER_DEFENSE_STRATEGY_OPTIONS: { value: string | null; label: string }[] = [
    { value: null, label: 'Balanced' },
    { value: 'low_catcher_defense', label: 'Low' },
    { value: 'high_catcher_defense', label: 'High' },
    { value: 'elite_catcher_defense', label: 'Elite' },
];

export async function autofillTeam(
    teamId: string,
    strategy: AutofillStrategy,
    token: string,
    activeFilters?: Record<string, unknown>,
): Promise<AutofillResult> {
    const res = await fetch(`${API_BASE}/user/teams/${teamId}/autofill`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
            pts_distribution: strategy.pts_distribution,
            pitching_strategy: strategy.pitching_strategy,
            hitting_strategy: strategy.hitting_strategy,
            pts_target: strategy.pts_target,
            active_filters: activeFilters ?? {},
        }),
    });
    if (res.status === 422) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.message || body.error || 'Autofill failed');
    }
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Autofill request failed: ${res.status}`);
    }
    return res.json();
}
