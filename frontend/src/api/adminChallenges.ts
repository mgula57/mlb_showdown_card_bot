/**
 * Admin-only Team Challenge template management. All routes are gated server-side by the admin
 * allowlist (`require_admin`); the UI only shows the panel when `useAuth().isAdmin` is true.
 *
 * Mirrors the `showdown_bot challenges` CLI: templates are hand-authored content, `rotate` keeps
 * one live instance per category, and `generateInstance` forces one for a single template.
 */

import type { ChallengeCategory, ChallengeGoalType, ChallengeInstance } from './sim';

const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:5000/api';

/** A hand-authored challenge template, with rotation status joined on. */
export type ChallengeTemplate = {
    template_id: string;
    slug: string;
    title: string;
    description: string;
    goal_type: ChallengeGoalType;
    goal_value: { min_wins?: number; target_abbr?: string } | null;
    pts_limit: number | null;
    roster_size: number;
    /** 'any' | comma list of years | 'random_range:lo,hi' */
    year_pool: string;
    /** 'any' | 'worst_record' | comma list of abbrs */
    replaces_pool: string;
    active: boolean;
    player_filters: Record<string, unknown> | null;
    category: ChallengeCategory;
    created_at: string;
    /** Newest instance's created_at, or null if this template has never been instanced. */
    last_instanced_at: string | null;
    /** Unexpired instances pointing at this template (0 or 1 in normal operation). */
    live_instance_count: number;
};

/** The create/edit payload. `min_wins` / `beat_team_abbr` are only read for the matching
 *  `goal_type`; the server re-derives `goal_value` from them. */
export type ChallengeTemplateInput = {
    slug: string;
    title: string;
    description: string;
    goal_type: ChallengeGoalType;
    min_wins?: number | null;
    beat_team_abbr?: string | null;
    category: ChallengeCategory;
    pts_limit?: number | null;
    roster_size: number;
    year_pool: string;
    replaces_pool: string;
    player_filters?: Record<string, unknown> | null;
    active: boolean;
};

export type GeneratedInstance = {
    instance_id: string;
    slug: string;
    year: number;
    replaces_abbr: string;
};

export type RotationResult = {
    pruned: number;
    created: GeneratedInstance[];
    /** Human-readable "category 'x': reason" lines for categories the rotation couldn't fill. */
    skipped: string[];
};

async function fail(res: Response, fallback: string): Promise<never> {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `${fallback} (${res.status})`);
}

function jsonHeaders(token: string) {
    return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
}

export async function fetchAdminChallenges(
    token: string,
): Promise<{ templates: ChallengeTemplate[]; live_instances: ChallengeInstance[] }> {
    const res = await fetch(`${API_BASE}/admin/challenges`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) await fail(res, 'Failed to load challenge templates');
    return res.json();
}

export async function createChallengeTemplate(
    token: string,
    input: ChallengeTemplateInput,
): Promise<ChallengeTemplate> {
    const res = await fetch(`${API_BASE}/admin/challenges/templates`, {
        method: 'POST', headers: jsonHeaders(token), body: JSON.stringify(input),
    });
    if (!res.ok) await fail(res, 'Failed to create template');
    return res.json();
}

export async function updateChallengeTemplate(
    token: string,
    templateId: string,
    input: Partial<ChallengeTemplateInput>,
): Promise<ChallengeTemplate> {
    const res = await fetch(`${API_BASE}/admin/challenges/templates/${templateId}`, {
        method: 'PUT', headers: jsonHeaders(token), body: JSON.stringify(input),
    });
    if (!res.ok) await fail(res, 'Failed to update template');
    return res.json();
}

export async function deleteChallengeTemplate(token: string, templateId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/admin/challenges/templates/${templateId}`, {
        method: 'DELETE', headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) await fail(res, 'Failed to delete template');
}

/** Force one live instance for this template now, outside the category rotation. */
export async function generateChallengeInstance(
    token: string,
    templateId: string,
    force = false,
): Promise<GeneratedInstance> {
    const res = await fetch(`${API_BASE}/admin/challenges/templates/${templateId}/instance`, {
        method: 'POST', headers: jsonHeaders(token), body: JSON.stringify({ force }),
    });
    if (!res.ok) await fail(res, 'Failed to generate instance');
    return res.json();
}

/** Prune expired instances, then fill every category that has no live challenge. */
export async function runChallengeRotation(token: string): Promise<RotationResult> {
    const res = await fetch(`${API_BASE}/admin/challenges/rotate`, {
        method: 'POST', headers: jsonHeaders(token),
    });
    if (!res.ok) await fail(res, 'Rotation failed');
    return res.json();
}
