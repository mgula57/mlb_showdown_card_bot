/**
 * @fileoverview Faceoffs: one builder team played against another, then watched back. Mirrors the
 * `/sim/faceoff*` routes in `mlb_showdown_bot/api/sim.py` and the models in
 * `core/simulation/faceoff.py`, so field names are snake_case.
 *
 * A Faceoff is always a list of games, even when it's a single one, so a series needs no new shape.
 */
import type { SimGameResultJson, SimTeamIdentityJson } from "../domain/adapters/fromSim";
import type { ShowdownBotCardAPIResponse } from "./showdownBotCard";
import type { ManagerPreference } from "./manager";
import type { CardSource } from "../types/cardSource";

/** Faceoffs are hidden in the UI for now (the backend stays live). Flip to true to bring back the
 * Faceoff button, the team Faceoffs tab, the Recent Faceoffs shelf and the /teams/faceoffs/:id page. */
export const FACEOFFS_ENABLED = false;

const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

export type FaceoffSide = "challenger" | "opponent";

export type FaceoffGameScore = {
    game_number: number;
    home_side: FaceoffSide;
    challenger_score: number;
    opponent_score: number;
};

/** A Faceoff as listed, without its game logs. */
export type FaceoffSummary = {
    faceoff_id: string;
    user_id: string;
    challenger_team_id: string | null;
    opponent_team_id: string | null;
    best_of: number;
    challenger_wins: number;
    opponent_wins: number;
    winner_side: FaceoffSide | null;
    is_own_matchup: boolean;
    created_at: string;
    challenger_identity: SimTeamIdentityJson;
    opponent_identity: SimTeamIdentityJson;
    is_mine: boolean;
    game_scores: FaceoffGameScore[];
};

/** A side as it stood when the Faceoff was played. */
export type FaceoffTeamSnapshot = {
    team_id: string | null;
    identity: SimTeamIdentityJson;
    total_points: number;
    allowed_sets: string[];
    roster: { card_id: string; card_source: CardSource; roster_position: string }[];
    starter_card_id?: string | null;
    manager?: ManagerPreference | null;
};

export type FaceoffGame = FaceoffGameScore & { game: SimGameResultJson };

export type Faceoff = FaceoffSummary & {
    seed: number;
    teams: Record<FaceoffSide, FaceoffTeamSnapshot>;
    games: FaceoffGame[];
};

export type StartFaceoffPayload = {
    team_id: string;
    opponent_team_id: string;
    best_of?: number;
    starter_card_id?: string;
    manager?: ManagerPreference;
    /** Only honored when the user owns both teams — a public opponent plays as saved. */
    opponent_starter_card_id?: string;
    opponent_manager?: ManagerPreference;
};

/** The same matchup again: both teams as they're saved now, with this Faceoff's starters and
 *  managers. Null when a side has no team to play. */
export function rematchPayload(faceoff: Faceoff): StartFaceoffPayload | null {
    const { challenger, opponent } = faceoff.teams;
    if (!challenger.team_id || !opponent.team_id) return null;
    return {
        team_id: challenger.team_id,
        opponent_team_id: opponent.team_id,
        best_of: faceoff.best_of,
        starter_card_id: challenger.starter_card_id ?? undefined,
        manager: challenger.manager ?? undefined,
        opponent_starter_card_id: opponent.starter_card_id ?? undefined,
        opponent_manager: opponent.manager ?? undefined,
    };
}

const authHeaders = (token?: string): HeadersInit => (token ? { Authorization: `Bearer ${token}` } : {});

async function parseError(res: Response, fallback: string): Promise<never> {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `${fallback}: ${res.status}`);
}

export async function startFaceoff(payload: StartFaceoffPayload, token: string): Promise<string> {
    const res = await fetch(`${API_BASE}/sim/faceoff`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders(token) },
        body: JSON.stringify(payload),
    });
    if (!res.ok) await parseError(res, "Failed to start Faceoff");
    return (await res.json()).faceoff_id;
}

export async function fetchFaceoff(faceoffId: string, token?: string): Promise<Faceoff> {
    const res = await fetch(`${API_BASE}/sim/faceoff/${faceoffId}`, { headers: authHeaders(token) });
    if (!res.ok) await parseError(res, "Failed to load Faceoff");
    return res.json();
}

/** Every card in a Faceoff, keyed by card id, across all card sources. */
export async function fetchFaceoffCards(faceoffId: string, token?: string): Promise<Record<string, ShowdownBotCardAPIResponse>> {
    const res = await fetch(`${API_BASE}/sim/faceoff/${faceoffId}/cards`, { headers: authHeaders(token) });
    if (!res.ok) await parseError(res, "Failed to load Faceoff cards");
    const { cards } = await res.json() as { cards: Record<string, ShowdownBotCardAPIResponse["card"]> };
    return Object.fromEntries(Object.entries(cards).map(([id, card]) => [id, { card, error: null, error_for_user: null }]));
}

export async function fetchMyFaceoffs(token: string, limit = 20): Promise<FaceoffSummary[]> {
    const res = await fetch(`${API_BASE}/sim/faceoffs/mine?limit=${limit}`, { headers: authHeaders(token) });
    if (!res.ok) await parseError(res, "Failed to load Faceoffs");
    return (await res.json()).faceoffs;
}

export async function fetchTeamFaceoffs(teamId: string, token?: string, limit = 20): Promise<FaceoffSummary[]> {
    const res = await fetch(`${API_BASE}/sim/teams/${teamId}/faceoffs?limit=${limit}`, { headers: authHeaders(token) });
    if (!res.ok) await parseError(res, "Failed to load Faceoffs");
    return (await res.json()).faceoffs;
}
