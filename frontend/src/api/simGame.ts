/**
 * @fileoverview Simulating a single real MLB game. Mirrors `mlb_showdown_bot/api/sim.py`'s
 * `/sim/game/*` routes and the Pydantic models in `core/simulation/mlb_game.py` — field names are
 * snake_case because that's the wire format.
 *
 * Two flows, one endpoint pair: a game that hasn't started is simulated from the first pitch, and
 * a game in progress is taken over from its current state. `MLBGameSetup` describes either, so the
 * UI reads `is_takeover` rather than branching on which call it made.
 */
import type { SimGameResultJson } from "../domain/adapters/fromSim";
import type { ManagerPreference } from "./manager";
import type { MostRecentPlay } from "./mlbAPI";

const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

async function parseError(res: Response, fallback: string): Promise<never> {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `${fallback}: ${res.status}`);
}

/** Where a player's card came from. `REPLACEMENT` means one was invented — flag it in the UI. */
export type CardOrigin = "PREBUILT" | "GENERATED" | "REPLACEMENT";

export type SimGameLineupSlot = {
    batting_order: number;   // 1-9
    player_id: string;       // MLB player id, as a string
    name: string;
    position: string;
};

export type SimGamePlayerOption = {
    player_id: string;
    name: string;
    position: string;
    is_pitcher: boolean;
    points: number;
    command: number;
    ip?: number | null;
    positions_and_defense: string;
    card_origin: CardOrigin;
    /** Substituted out of a game in progress — they cannot come back, so they can't be picked. */
    is_unavailable: boolean;
};

export type SimGameTeamSetup = {
    side: "away" | "home";
    team_id?: number | null;
    identity: {
        abbreviation: string;
        name: string;
        primary_color?: string | null;
        secondary_color?: string | null;
    };
    lineup: SimGameLineupSlot[];
    starting_pitcher_id: string;
    position_players: SimGamePlayerOption[];
    bullpen: SimGamePlayerOption[];
};

/** `ANNOUNCED` when MLB has posted both batting orders; otherwise the sim picks its own nine. */
export type LineupSource = "ANNOUNCED" | "AUTO";

export type SimGameStartState = {
    inning: number;
    is_top: boolean;
    outs: number;
    runs: number;
    runners: { runners: { id: string; name: string; base: number; speed: number; pitcher_id: string }[] };
    away: { runs_scored: number; hits: number; lineup_index: number };
    home: { runs_scored: number; hits: number; lineup_index: number };
};

export type SimGameSetup = {
    game_pk: number;
    season: number;
    showdown_set: string;
    official_date: string;
    detailed_state: string;
    is_takeover: boolean;
    is_final: boolean;
    lineup_source: LineupSource;
    away: SimGameTeamSetup;
    home: SimGameTeamSetup;
    start_state?: SimGameStartState | null;
    warnings: string[];
};

export type SimGameResult = {
    game_pk: number;
    season: number;
    showdown_set: string;
    seed?: number | null;
    is_takeover: boolean;
    setup: SimGameSetup;
    game: SimGameResultJson;
    /** The real plate appearances from before the takeover, straight off the MLB feed. */
    real_plays: MostRecentPlay[];
};

/** A stored simulation. `result` is only present on the detail fetch, not on list rows. */
export type SimGameRecord = {
    sim_id: string;
    user_id: string | null;
    game_pk: number;
    season: number;
    showdown_set: string;
    game_date: string;
    away_abbr: string;
    home_abbr: string;
    away_score: number;
    home_score: number;
    is_takeover: boolean;
    takeover_inning: number | null;
    seed: number | null;
    created_at: string;
    is_own: boolean;
    result?: SimGameResult;
};

/** One side's overrides. Omit any field to keep what the setup proposed. */
export type SimGameTeamOverride = {
    lineup?: { player_id: string; position?: string }[];
    starting_pitcher_id?: string;
    /** Manager tendencies for this side. Omitted (or neutral) plays the default style. */
    manager?: ManagerPreference;
};

export type StartGameSimPayload = {
    set?: string;
    /** Fixing the seed makes a run reproducible; omit it for a fresh roll each time. */
    seed?: number | null;
    away?: SimGameTeamOverride;
    home?: SimGameTeamOverride;
};

/**
 * The lineups, rosters and mid-game state a simulation would use — fetched before committing so
 * the user can review and edit them. The server caches this briefly, so polling it is cheap.
 */
export async function fetchGameSimSetup(gamePk: number, showdownSet: string, signal?: AbortSignal): Promise<SimGameSetup> {
    const res = await fetch(`${API_BASE}/sim/game/${gamePk}/setup?set=${encodeURIComponent(showdownSet)}`, { signal });
    if (!res.ok) await parseError(res, "Failed to load game setup");
    return res.json();
}

/** Run the game. Synchronous — a single game is milliseconds, so there is no job to poll. */
export async function startGameSim(gamePk: number, payload: StartGameSimPayload, token: string): Promise<{ sim_id: string; result: SimGameResult }> {
    const res = await fetch(`${API_BASE}/sim/game/${gamePk}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
    });
    if (!res.ok) await parseError(res, "Failed to simulate game");
    return res.json();
}

/** A stored simulation by its durable id. Readable by anyone with the link. */
export async function fetchGameSimResult(simId: string, token?: string): Promise<SimGameRecord> {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/sim/game/result/${simId}`, { headers });
    if (!res.ok) await parseError(res, "Failed to load simulated game");
    return res.json();
}

/** Previous simulations of one real game, newest first. */
export async function fetchGameSimHistory(gamePk: number, token?: string, limit = 10): Promise<SimGameRecord[]> {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/sim/game/${gamePk}/history?limit=${limit}`, { headers });
    if (!res.ok) await parseError(res, "Failed to load simulation history");
    const data = await res.json();
    return data.games ?? [];
}
