import type { CardSource } from '../types/cardSource';
import type { CardDatabaseRecord } from './card_db/cardDatabase';

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
    pts_limit: number | null;
    roster_size: number;
    min_bench: number;
    min_bullpen: number;
    num_starters: number;
    bench_pts_multiplier: number;
    allowed_sets: string[] | null;
    allowed_card_sources: string[] | null;
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
    pts_limit: number | null;
    roster_size: number;
    min_bench: number;
    min_bullpen: number;
    num_starters: number;
    bench_pts_multiplier: number;
    allowed_sets: string[] | null;
    allowed_card_sources: string[] | null;
    created_at: string | null;
    updated_at: string | null;
    total_points: number;
    roster_count: number;
    is_drafting: boolean;
    top_players: CardDatabaseRecord[];
};

const FIELD_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'] as const;
const STARTER_ROLES   = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5'] as const;

export function isTeamDrafting(team: Team): boolean {
    if (team.source === 'mlb') return false;

    const slots = team.lineups[0]?.slots ?? [];
    const filledLineup = FIELD_POSITIONS.filter(pos => slots.some(s => s.field_position === pos)).length;
    if (filledLineup < 9) return true;

    const starterRoles = STARTER_ROLES.slice(0, team.num_starters);
    const filledStarters = team.rotation.filter(r => (starterRoles as readonly string[]).includes(r.role)).length;
    if (filledStarters < team.num_starters) return true;

    const filledBench = team.roster.filter(s => s.roster_position === 'BE').length;
    if (filledBench < team.min_bench) return true;

    const filledBullpen = team.rotation.filter(r => !(STARTER_ROLES as readonly string[]).includes(r.role)).length;
    if (filledBullpen < team.min_bullpen) return true;

    return false;
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

export async function fetchPublicTeams(source?: TeamSource, limit = 50, offset = 0): Promise<TeamSummary[]> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (source) params.set('source', source);
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
            active_filters: activeFilters ?? {},
        }),
    });
    if (res.status === 422) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.message || 'Autofill failed');
    }
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Autofill request failed: ${res.status}`);
    }
    return res.json();
}
