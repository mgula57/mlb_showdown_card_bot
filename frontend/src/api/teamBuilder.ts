/**
 * @fileoverview Team Builder API client
 *
 * Typed wrappers for the /api/teams/builder endpoints.
 * All requests include the Supabase session token in Authorization header.
 */

import { supabase } from './supabase';

const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:5000/api';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TeamBuilderCardSnapshot {
    name: string;
    year: string | number;
    team: string;
    points: number;
    command: number;
    outs: number;
    is_pitcher: boolean;
    color_primary?: string | null;
    color_secondary?: string | null;
    positions_and_defense_string?: string | null;
    ip?: number | null;
    speed?: number | null;
    showdown_set: string;
    card_year?: string;
}

export interface TeamBuilderSlot {
    id: number;
    team_id: number;
    slot_key: string;
    card_source: 'bot' | 'wotc';
    card_id: string;
    card_snapshot: TeamBuilderCardSnapshot | null;
    created_at: string;
}

export interface TeamBuilderTeam {
    id: number;
    user_id: string;
    name: string;
    team_type: string;
    showdown_set: string;
    roster_size: number;
    bullpen_size: number;
    bench_multiplier: number;
    metadata: Record<string, unknown> | null;
    created_at: string;
    updated_at: string;
}

export interface TeamBuilderTeamWithSlots extends TeamBuilderTeam {
    slots: TeamBuilderSlot[];
}

export type TeamBuilderTeamUpdates = Partial<
    Pick<TeamBuilderTeam, 'name' | 'team_type' | 'showdown_set' | 'roster_size' | 'bullpen_size' | 'bench_multiplier' | 'metadata'>
>;

// ─── Internal helpers ─────────────────────────────────────────────────────────

async function _authHeaders(): Promise<Record<string, string>> {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
}

async function _getUserId(): Promise<string | null> {
    const { data } = await supabase.auth.getSession();
    return data.session?.user?.id ?? null;
}

// ─── API Functions ────────────────────────────────────────────────────────────

export async function createTeam(payload: {
    name: string;
    showdown_set: string;
    team_type?: string;
    roster_size?: number;
    bullpen_size?: number;
    bench_multiplier?: number;
    metadata?: Record<string, unknown>;
}): Promise<TeamBuilderTeam> {
    const userId = await _getUserId();
    const headers = await _authHeaders();
    const res = await fetch(`${API_BASE}/teams/builder`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ ...payload, user_id: userId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to create team');
    return data.team;
}

export async function listTeams(teamType = 'custom'): Promise<TeamBuilderTeam[]> {
    const userId = await _getUserId();
    if (!userId) return [];
    const headers = await _authHeaders();
    const params = new URLSearchParams({ user_id: userId, team_type: teamType });
    const res = await fetch(`${API_BASE}/teams/builder?${params}`, { headers });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch teams');
    return data.teams ?? [];
}

export async function getTeamWithSlots(teamId: number): Promise<TeamBuilderTeamWithSlots> {
    const userId = await _getUserId();
    const headers = await _authHeaders();
    const params = new URLSearchParams({ user_id: userId ?? '' });
    const res = await fetch(`${API_BASE}/teams/builder/${teamId}?${params}`, { headers });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch team');
    return data.team;
}

export async function updateTeam(teamId: number, updates: TeamBuilderTeamUpdates): Promise<void> {
    const userId = await _getUserId();
    const headers = await _authHeaders();
    const res = await fetch(`${API_BASE}/teams/builder/${teamId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ ...updates, user_id: userId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to update team');
}

export async function deleteTeam(teamId: number): Promise<void> {
    const userId = await _getUserId();
    const headers = await _authHeaders();
    const res = await fetch(`${API_BASE}/teams/builder/${teamId}`, {
        method: 'DELETE',
        headers,
        body: JSON.stringify({ user_id: userId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to delete team');
}

export async function upsertSlot(
    teamId: number,
    slotKey: string,
    cardSource: 'bot' | 'wotc',
    cardId: string,
    cardSnapshot: TeamBuilderCardSnapshot,
): Promise<void> {
    const userId = await _getUserId();
    const headers = await _authHeaders();
    const res = await fetch(`${API_BASE}/teams/builder/${teamId}/slots/${slotKey}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ user_id: userId, card_source: cardSource, card_id: cardId, card_snapshot: cardSnapshot }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to update slot');
}

export async function deleteSlot(teamId: number, slotKey: string): Promise<void> {
    const userId = await _getUserId();
    const headers = await _authHeaders();
    const res = await fetch(`${API_BASE}/teams/builder/${teamId}/slots/${slotKey}`, {
        method: 'DELETE',
        headers,
        body: JSON.stringify({ user_id: userId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to delete slot');
}
