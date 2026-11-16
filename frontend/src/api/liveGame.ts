/**
 * @fileoverview Live games: games people play by hand, a turn at a time. Two seats (away, home),
 * each holding any club (one of your teams, a public team, a club from baseball history) and played
 * by a person or by the sim. Mirrors the `/sim/live*` routes in `mlb_showdown_bot/api/live_games.py`
 * and the models in `core/simulation/live_game.py`, so field names are snake_case.
 *
 * The server owns every die. A Roll only says "go", and each response carries the whole game as it
 * now stands (`LiveGameState`), rebuilt from the actions so far.
 */
import type { SimGameResultJson, SimTeamIdentityJson } from "../domain/adapters/fromSim";
import type { ShowdownBotCardAPIResponse } from "./showdownBotCard";
import type { ManagerPreference } from "./manager";

/** Live games are hidden in the UI until they're released. Flip to true to show the Play Live button
 * on a team page and the /teams/live and /teams/play pages. */
export const LIVE_GAMES_ENABLED = true;

const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

export type LiveSide = "away" | "home";
export type RollKind = "pitch" | "swing";
export type LiveActionKind = "roll" | "pitching_change" | "pinch_hit" | "autopilot";

export type LiveAction = {
    side: LiveSide;
    kind: LiveActionKind;
    roll?: RollKind | null;
    player_id?: string | null;
    for_player_id?: string | null;
    enabled?: boolean | null;
    by_timeout?: boolean;
};

/** Idle timer choices, in minutes. `null` is "take your time": the game waits as long as it takes. */
export const IDLE_AUTOPILOT_CHOICES = [null, 2, 5, 15, 60] as const;
export type IdleAutopilotMinutes = (typeof IDLE_AUTOPILOT_CHOICES)[number];

export type LiveGameSettings = { idle_autopilot_minutes: IdleAutopilotMinutes };

export type PendingRoll = {
    side: LiveSide;
    roll: RollKind;
    /** Set while waiting on the swing: the matchup is locked and the pitch is known. */
    pitcher_id?: string | null;
    hitter_id?: string | null;
    pitch_roll?: number | null;
    /** "padv" (pitcher's advantage) or "hadv" (hitter's). */
    pitch_result?: string | null;
};

export type LiveSideState = {
    side: LiveSide;
    autopilot: boolean;
    pitcher_id: string;
    pitcher_fatigue: number;
    pitcher_is_tired: boolean;
    available_reliever_ids: string[];
    bench_ids: string[];
    lineup_ids: string[];
    due_up_id: string;
    at_bat_id?: string | null;
    queued: LiveAction[];
};

export type LiveGameState = {
    seq: number;
    game: SimGameResultJson;
    is_final: boolean;
    winner_side: LiveSide | null;
    pending: PendingRoll | null;
    situation: { inning: number; is_top: boolean; outs: number } | null;
    player_names: Record<string, string>;
    sides: Record<LiveSide, LiveSideState>;
};

export type LiveGameStatus = "invited" | "active" | "final" | "cancelled";

/** Which club takes a seat. `random_historical` lands on a historical club when the game is made. */
export type TeamRef =
    | { kind: "saved"; team_id: string }
    | { kind: "historical"; season: number; team_id: number; sport_id?: number }
    | { kind: "era"; era: string; team_id: number; sport_id?: number }
    | { kind: "random_historical"; season?: number; sport_id?: number };

export type SeatController = "human" | "sim";

export type LiveSeat = {
    controller: SeatController;
    /** The club in the seat; null while an invitee is still to bring their own. */
    identity: SimTeamIdentityJson | null;
    is_mine: boolean;
    /** A person's seat nobody has taken yet. */
    is_open: boolean;
};

export type LiveGameContext = { kind: string; ref: string | null };

export type LiveGame = {
    live_game_id: string;
    status: LiveGameStatus;
    context: LiveGameContext;
    settings: LiveGameSettings;
    seats: Record<LiveSide, LiveSeat>;
    /** The seats this viewer plays: none for a spectator, both for someone playing themselves. */
    my_sides: LiveSide[];
    invite_code: string | null;
    is_creator: boolean;
    last_action_at: string | null;
    state: LiveGameState | null;
};

export type LiveGameInvite = {
    live_game_id: string;
    status: LiveGameStatus;
    open_side: LiveSide | null;
    seats: Record<LiveSide, LiveSeat>;
    /** Null: the invitee brings their own team. */
    open_seat_team_ref: TeamRef | null;
    settings: LiveGameSettings;
    is_mine: boolean;
};

export type LiveGameListItem = {
    live_game_id: string;
    status: LiveGameStatus;
    context: LiveGameContext;
    identities: Record<LiveSide, SimTeamIdentityJson | null>;
    controllers: Record<LiveSide, SeatController>;
    my_sides: LiveSide[];
    is_my_turn: boolean;
    winner_side: LiveSide | null;
    invite_code: string | null;
    last_action_at: string | null;
};

export type LiveSeatChoice = {
    team?: TeamRef;
    starter_card_id?: string;
    manager?: ManagerPreference;
};

/** Who plays the other seat: whoever opens the invite, the sim, or the creator too. */
export type OpponentController = "invite" | "sim" | "me";

export type CreateLiveGamePayload = LiveSeatChoice & {
    team: TeamRef;
    my_side: LiveSide;
    opponent: LiveSeatChoice & { controller: OpponentController };
    idle_autopilot_minutes: IdleAutopilotMinutes;
    /** The set a club from history is built in. */
    showdown_set: string;
};

const authHeaders = (token?: string): HeadersInit => (token ? { Authorization: `Bearer ${token}` } : {});

/** Carries the HTTP status, so the caller can tell "the game moved on" (409) from a real failure. */
export class LiveGameError extends Error {
    readonly status: number;

    constructor(message: string, status: number) {
        super(message);
        this.status = status;
    }
}

async function parse<T>(res: Response, fallback: string): Promise<T> {
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new LiveGameError(err.error || `${fallback}: ${res.status}`, res.status);
    }
    return res.json();
}

const postJson = (path: string, body: unknown, token: string) => fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify(body),
});

/** The link the challenger sends. */
export const inviteUrl = (inviteCode: string) => `${window.location.origin}/teams/play/${inviteCode}`;

export async function createLiveGame(payload: CreateLiveGamePayload, token: string) {
    return parse<{ live_game_id: string; invite_code: string | null }>(await postJson("/sim/live", payload, token), "Failed to create game");
}

export async function fetchLiveGameInvite(inviteCode: string, token?: string) {
    return parse<LiveGameInvite>(await fetch(`${API_BASE}/sim/live/invite/${inviteCode}`, { headers: authHeaders(token) }), "Failed to load invite");
}

export async function acceptLiveGame(inviteCode: string, payload: LiveSeatChoice & { showdown_set?: string }, token: string) {
    return parse<{ live_game_id: string }>(await postJson(`/sim/live/invite/${inviteCode}/accept`, payload, token), "Failed to accept invite");
}

export async function cancelLiveGame(liveGameId: string, token: string) {
    return parse<{ cancelled: boolean }>(await postJson(`/sim/live/${liveGameId}/cancel`, {}, token), "Failed to cancel invite");
}

/** The game as it stands. With `since`, an unchanged game answers `null` instead of the whole state. */
export async function fetchLiveGame(liveGameId: string, token?: string, since?: number): Promise<LiveGame | null> {
    const query = since === undefined ? "" : `?since=${since}`;
    const data = await parse<LiveGame | { unchanged: true }>(
        await fetch(`${API_BASE}/sim/live/${liveGameId}${query}`, { headers: authHeaders(token) }),
        "Failed to load game",
    );
    return "unchanged" in data ? null : data;
}

export async function postLiveAction(liveGameId: string, expectedSeq: number, action: LiveAction, token: string) {
    return parse<LiveGame>(await postJson(`/sim/live/${liveGameId}/actions`, { expected_seq: expectedSeq, action }, token), "That move didn't go through");
}

/** Every card in the game, as frozen when it began, keyed by card id. */
export async function fetchLiveGameCards(liveGameId: string, token?: string): Promise<Record<string, ShowdownBotCardAPIResponse>> {
    const { cards } = await parse<{ cards: Record<string, ShowdownBotCardAPIResponse["card"]> }>(
        await fetch(`${API_BASE}/sim/live/${liveGameId}/cards`, { headers: authHeaders(token) }),
        "Failed to load cards",
    );
    return Object.fromEntries(Object.entries(cards).map(([id, card]) => [id, { card, error: null, error_for_user: null }]));
}

/** [x, y, width, height] as fractions of a card image. */
export type CardImageBox = [number, number, number, number];

/** A card rendered as a full Showdown card image, with where each chart result (keyed by result,
 *  "1B+") and the Onbase/Control badge sit on it. */
export type LiveCardImage = {
    image_url: string;
    chart_cells: Record<string, CardImageBox>;
    command_box: CardImageBox;
};

/** One of the game's cards as an image, rendered with the viewer's image libraries. The first ask
 *  renders it (a few seconds); after that it's stored. */
export async function fetchLiveGameCardImage(liveGameId: string, cardId: string, token?: string): Promise<LiveCardImage> {
    return parse<LiveCardImage>(
        await fetch(`${API_BASE}/sim/live/${liveGameId}/cards/${encodeURIComponent(cardId)}/image`, { headers: authHeaders(token) }),
        "Failed to load card image",
    );
}

export async function fetchMyLiveGames(token: string) {
    return (await parse<{ games: LiveGameListItem[] }>(await fetch(`${API_BASE}/sim/live/mine`, { headers: authHeaders(token) }), "Failed to load games")).games;
}
