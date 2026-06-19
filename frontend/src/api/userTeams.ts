import type { CardSource } from '../types/cardSource';

const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// =============================================================================
// MARK: - TYPES
// =============================================================================

export type TeamRosterSlot = {
    card_id: string;
    card_source: CardSource;
    roster_position: string;
    draft_order: number | null;
};

export type LineupSlot = {
    card_id: string;
    card_source: CardSource;
    field_position: string;
    batting_order: number | null;
};

export type Lineup = {
    name: string;
    slots: LineupSlot[];
};

export type PitcherAssignment = {
    card_id: string;
    card_source: CardSource;
    role: string;
};

export type TeamSource = 'user' | 'official' | 'asg';

export type Team = {
    team_id: string;
    user_id: string | null;
    name: string;
    abbreviation: string;
    primary_color: string;
    secondary_color: string;
    showdown_set: string;
    is_public: boolean;
    source: TeamSource;
    pts_limit: number | null;
    roster_size: number;
    min_bench: number;
    min_bullpen: number;
    bench_pts_multiplier: number;
    allowed_sets: string[] | null;
    roster: TeamRosterSlot[];
    lineups: Lineup[];
    rotation: PitcherAssignment[];
    created_at: string | null;
    updated_at: string | null;
    total_points: number;
};

export type TeamCreatePayload = Partial<Omit<Team, 'team_id' | 'user_id' | 'created_at' | 'updated_at'>> & {
    name: string;
    abbreviation: string;
};

export type TeamUpdatePayload = Partial<Omit<Team, 'team_id' | 'user_id' | 'created_at' | 'updated_at'>>;

// =============================================================================
// MARK: - API CALLS
// =============================================================================

export async function fetchUserTeams(token: string): Promise<Team[]> {
    const res = await fetch(`${API_BASE}/user/teams`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Failed to fetch teams: ${res.status}`);
    return res.json();
}

export async function fetchPublicTeams(source?: TeamSource, limit = 50, offset = 0): Promise<Team[]> {
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
