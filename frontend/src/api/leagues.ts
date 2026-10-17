/**
 * @fileoverview Typed wrappers for the `/api/leagues` routes: leagues, membership, the draft, and
 * season play. Every route needs a signed-in user, so every call takes the session token.
 */

import type { SeasonAwards, SeasonSimSummary } from './sim';
import type { RosterMove } from '../domain/roster';

const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// =============================================================================
// MARK: - TYPES
// =============================================================================

export type LuxuryTaxType = 'linear' | 'exponential';

/** Makes `pts_cap` a soft cap: picks may go over it, and every team pays the buy-in plus a tax
 *  on the points it's over the cap. */
export type LuxuryTax = {
    buy_in: number;
    type: LuxuryTaxType;
};

export const DEFAULT_LUXURY_TAX: LuxuryTax = { buy_in: 50, type: 'linear' };

export type LeagueSettings = {
    team_count: number;
    roster_size: number;
    min_bench: number;
    min_bullpen: number;
    num_starters: number;
    pts_cap: number | null;
    /** Null for no tax (a hard cap). Needs `pts_cap`. */
    luxury_tax?: LuxuryTax | null;
    draft_order_mode: 'random' | 'manual';
};

export const DEFAULT_LEAGUE_SETTINGS: LeagueSettings = {
    team_count: 8,
    roster_size: 20,
    min_bench: 2,
    min_bullpen: 5,
    num_starters: 4,
    pts_cap: null,
    luxury_tax: null,
    draft_order_mode: 'random',
};

export type LeagueStatus = 'open' | 'active' | 'archived';
export type LeagueSeasonStatus = 'drafting' | 'setup' | 'regular' | 'postseason' | 'complete';
export type LeagueJobStatus = 'idle' | 'running' | 'failed';

export type League = {
    league_id: string;
    name: string;
    commissioner_user_id: string;
    join_code: string;
    showdown_set: string;
    edition_ids: string[];
    settings: LeagueSettings;
    status: LeagueStatus;
    created_at: string;
    updated_at: string;
};

export type LeagueListItem = Omit<League, 'join_code'> & {
    member_count: number;
    current_season_number: number | null;
    current_season_status: LeagueSeasonStatus | null;
};

export type LeagueMember = {
    member_id: string;
    league_id: string;
    /** Null for a bot seat. */
    user_id: string | null;
    display_name: string;
    draft_slot: number | null;
    joined_at: string;
    username: string | null;
    avatar_url: string | null;
};

export type BracketConfig = {
    /** 0, 2, 4, 6 or 8. 6 gives the top 2 seeds a first-round bye. */
    teams: number;
    /** One odd length per round, first round first. */
    series_lengths: number[];
};

export type SeasonConfig = {
    games_per_team: number;
    postseason: BracketConfig;
};

export const DEFAULT_SEASON_CONFIG: SeasonConfig = {
    games_per_team: 162,
    postseason: { teams: 4, series_lengths: [5, 7] },
};

export type LeagueSeason = {
    season_id: string;
    league_id: string;
    season_number: number;
    status: LeagueSeasonStatus;
    config: Partial<SeasonConfig>;
    seed: number | null;
    champion_team_id: string | null;
    awards: SeasonAwards | null;
    /** Standings, leaders, postseason and awards so far - null until the first games are played. */
    summary: SeasonSimSummary | null;
    created_at: string;
    completed_at: string | null;
    job_status: LeagueJobStatus;
    job_progress: number;
    job_total: number;
    job_error: string | null;
    job_started_at: string | null;
};

export type LeagueTeam = {
    season_id: string;
    member_id: string;
    team_id: string;
    user_id: string | null;
    display_name: string;
    draft_slot: number | null;
    name: string;
    abbreviation: string;
    primary_color: string | null;
    secondary_color: string | null;
    logo_url: string | null;
};

export type LeagueState = {
    league: League;
    members: LeagueMember[];
    season: LeagueSeason | null;
    teams: LeagueTeam[];
    my_member_id: string | null;
    is_commissioner: boolean;
};

export type LeaguePreview = {
    league_id: string;
    name: string;
    status: LeagueStatus;
    showdown_set: string;
    team_count: number;
    member_count: number;
    commissioner_name: string | null;
    is_member: boolean;
};

export type DraftPick = {
    overall_pick: number;
    round: number;
    member_id: string;
    release_card_id: string;
    source_card_id: string | null;
    is_auto: boolean;
    picked_at?: string;
    name: string;
    year?: string | null;
    team?: string | null;
    points: number;
    player_type?: string | null;
    bref_id?: string | null;
    positions_and_defense?: Record<string, number> | null;
    roster_position?: string;
};

export type DraftMyRoster = {
    picks_left: number;
    points: number;
    open_field_positions: string[];
    open_rotation_roles: string[];
    bullpen_count: number;
    bench_count: number;
    hard_needs: number;
    slack: number;
};

export type DraftState = {
    status: LeagueSeasonStatus;
    total_picks: number;
    rounds: number;
    next_pick: number | null;
    current_round: number | null;
    on_the_clock_member_id: string | null;
    upcoming: { overall_pick: number; round: number; member_id: string }[];
    teams: LeagueTeam[];
    picks: DraftPick[];
    my_roster: DraftMyRoster | null;
};

export type DraftPayload = {
    season: LeagueSeason;
    draft: DraftState;
};

export type SeasonPayload = {
    season: LeagueSeason;
    teams: LeagueTeam[];
    is_commissioner: boolean;
};

export type SimTarget = 'day' | 'week' | 'regular_end' | 'round' | 'postseason_end';

export type LeagueGame = {
    game_index: number;
    day: number;
    round: string;
    series_id: string | null;
    home_key: string;
    away_key: string;
    home_score: number | null;
    away_score: number | null;
    status: 'scheduled' | 'final';
    result?: Record<string, unknown> | null;
};

export type LeagueHistoryEntry = {
    season_id: string;
    season_number: number;
    status: LeagueSeasonStatus;
    awards: SeasonAwards | null;
    completed_at: string | null;
    champion_team_id: string | null;
    champion_name: string | null;
    champion_abbreviation: string | null;
    champion_primary_color: string | null;
    champion_secondary_color: string | null;
    champion_member_name: string | null;
};

// =============================================================================
// MARK: - REQUESTS
// =============================================================================

async function request<T>(path: string, token: string, init: { method?: string; body?: unknown } = {}): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: init.method ?? 'GET',
        headers: {
            Authorization: `Bearer ${token}`,
            ...(init.body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        },
        body: init.body !== undefined ? JSON.stringify(init.body) : undefined,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new LeagueRequestError(err.error || `Request failed: ${res.status}`, res.status);
    }
    return res.json();
}

/** A failed league request. `status` 409 means the board or season moved - refetch and retry. */
export class LeagueRequestError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.status = status;
    }
}

const leaguePath = (leagueId: string) => `/leagues/${leagueId}`;
const seasonPath = (leagueId: string, seasonNumber: number) => `${leaguePath(leagueId)}/seasons/${seasonNumber}`;

// Leagues

export const fetchMyLeagues = (token: string) =>
    request<LeagueListItem[]>('/leagues/mine', token);

export const createLeague = (token: string, payload: { name: string; edition_ids: string[]; settings: Partial<LeagueSettings>; display_name?: string }) =>
    request<LeagueState>('/leagues', token, { method: 'POST', body: payload });

export const fetchLeague = (token: string, leagueId: string) =>
    request<LeagueState>(leaguePath(leagueId), token);

export const updateLeague = (token: string, leagueId: string, payload: { name?: string; settings?: Partial<LeagueSettings> }) =>
    request<LeagueState>(leaguePath(leagueId), token, { method: 'PATCH', body: payload });

export const previewLeague = (token: string, code: string) =>
    request<LeaguePreview>(`/leagues/code/${encodeURIComponent(code.trim())}`, token);

export const joinLeague = (token: string, code: string, displayName?: string) =>
    request<LeagueState>(`/leagues/join/${encodeURIComponent(code.trim())}`, token, { method: 'POST', body: { display_name: displayName } });

export const addLeagueBots = (token: string, leagueId: string, count?: number) =>
    request<LeagueState>(`${leaguePath(leagueId)}/bots`, token, { method: 'POST', body: { count } });

export const removeLeagueMember = (token: string, leagueId: string, memberId: string) =>
    request<LeagueState>(`${leaguePath(leagueId)}/members/${memberId}`, token, { method: 'DELETE' });

export const fetchLeagueHistory = (token: string, leagueId: string) =>
    request<LeagueHistoryEntry[]>(`${leaguePath(leagueId)}/history`, token);

// Draft

export const startDraft = (token: string, leagueId: string, seasonNumber: number, order?: string[]) =>
    request<DraftPayload>(`${seasonPath(leagueId, seasonNumber)}/draft/start`, token, { method: 'POST', body: { order } });

export const fetchDraft = (token: string, leagueId: string, seasonNumber: number) =>
    request<DraftPayload>(`${seasonPath(leagueId, seasonNumber)}/draft`, token);

/** Realtime channel pinged on every change to a season's draft. Matches `RealtimeBroadcaster.league_draft_topic`. */
export const leagueDraftTopic = (leagueId: string, seasonNumber: number) => `league-draft:${leagueId}:${seasonNumber}`;
export const DRAFT_CHANGED_EVENT = 'draft_changed';

/** Draft `releaseCardId`, or let the bot pick (`null`) - the commissioner's way past a stalled seat. */
/** Draft `releaseCardId` (into `rosterPosition`, or the first open spot it fits when omitted),
 *  or auto-pick when `releaseCardId` is null. */
export const makeDraftPick = (token: string, leagueId: string, seasonNumber: number, releaseCardId: string | null, rosterPosition?: string | null) =>
    request<DraftPayload>(`${seasonPath(leagueId, seasonNumber)}/draft/pick`, token, {
        method: 'POST',
        body: releaseCardId
            ? { release_card_id: releaseCardId, ...(rosterPosition ? { roster_position: rosterPosition } : {}) }
            : { auto: true },
    });

/** Move one of my drafted players into an open roster position, or swap it with another of my players. */
export const moveRosterPlayer = (token: string, leagueId: string, seasonNumber: number, move: RosterMove) =>
    request<DraftPayload>(`${seasonPath(leagueId, seasonNumber)}/roster/move`, token, {
        method: 'POST',
        body: { release_card_id: move.cardId, to_position: move.toPosition, swap_with_card_id: move.swapWithCardId },
    });

// Seasons

export const fetchSeason = (token: string, leagueId: string, seasonNumber: number) =>
    request<SeasonPayload>(seasonPath(leagueId, seasonNumber), token);

export const updateSeasonConfig = (token: string, leagueId: string, seasonNumber: number, config: SeasonConfig) =>
    request<SeasonPayload>(`${seasonPath(leagueId, seasonNumber)}/config`, token, { method: 'PUT', body: config });

export const startSeason = (token: string, leagueId: string, seasonNumber: number) =>
    request<SeasonPayload>(`${seasonPath(leagueId, seasonNumber)}/start`, token, { method: 'POST' });

export const simSeason = (token: string, leagueId: string, seasonNumber: number, until: SimTarget) =>
    request<SeasonPayload>(`${seasonPath(leagueId, seasonNumber)}/sim`, token, { method: 'POST', body: { until } });

export const fetchSeasonGames = (token: string, leagueId: string, seasonNumber: number, filters: { day?: number; team?: string } = {}) => {
    const params = new URLSearchParams();
    if (filters.day !== undefined) params.set('day', String(filters.day));
    if (filters.team) params.set('team', filters.team);
    const query = params.toString();
    return request<LeagueGame[]>(`${seasonPath(leagueId, seasonNumber)}/games${query ? `?${query}` : ''}`, token);
};

export const fetchSeasonGame = (token: string, leagueId: string, seasonNumber: number, gameIndex: number) =>
    request<LeagueGame>(`${seasonPath(leagueId, seasonNumber)}/games/${gameIndex}`, token);

export const runItBack = (token: string, leagueId: string) =>
    request<SeasonPayload>(`${leaguePath(leagueId)}/seasons/run_it_back`, token, { method: 'POST' });
