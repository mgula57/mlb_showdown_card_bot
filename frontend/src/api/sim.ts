const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// =============================================================================
// MARK: - TYPES
// =============================================================================

/** Mirrors `SimTeamIdentity` — branding for any team referenced by schedule key. */
export type SimTeamIdentity = {
    abbreviation: string;
    name: string;
    primary_color: string | null;
    secondary_color: string | null;
    league: string | null;
};

/** A real club available to take over, with the record it actually posted. */
export type TakeoverClub = {
    abbreviation: string;
    name: string;
    league: string | null;
    division: string | null;
    wins: number;
    losses: number;
};

/**
 * A statline with rate stats already computed server-side. `stats` is keyed by StatCategory
 * value ('ops', 'ops+', 'era', 'wRC+', …) — the backend materializes these because they are
 * Python properties that need league context, so never recompute them here.
 */
export type SimStatLine = {
    id: string;
    name: string;
    team: string | null;
    position: string | null;
    points: number;
    command: number;
    player_type: string | null;
    stats: Record<string, number>;
    /** Set only for players on the takeover team's own roster — pairs with `id` as the
     * (card_id, card_source) `useCardMap` fetches roster cards with. Null/absent for players from
     * other clubs, and for summaries persisted before this field existed. */
    card_source?: string | null;
};

/** One award winner. `value`/`value_label` are the deciding stat for that category, already
 * formatted server-side (see `AwardsBuilder` in `core/simulation/awards.py`). */
export type AwardWinner = {
    category: 'MVP' | 'CY_YOUNG' | 'ROY' | 'SILVER_SLUGGER';
    league: string;
    position?: string | null;
    value: number;
    value_label: string;
    player: SimStatLine;
};

/** Absent/empty for summaries persisted before awards existed. */
export type SeasonAwards = {
    mvp: AwardWinner[];
    cy_young: AwardWinner[];
    rookie_of_year: AwardWinner[];
    silver_sluggers: AwardWinner[];
};

/** Mirrors `PlayerSubType` — keys of `SeasonSimSummary.top_players`. */
export type PlayerSubType = 'position_player' | 'starting_pitcher' | 'relief_pitcher';

export type SimGameLine = {
    date: string;
    opponent: string;
    opponent_identity: SimTeamIdentity | null;
    is_home: boolean;
    runs_scored: number;
    runs_allowed: number;
    is_win: boolean;
    /** Running record after this game — backs the streak chart. */
    wins: number;
    losses: number;
};

export type SimPostseasonGameLine = {
    date: string;
    home_team: string;
    away_team: string;
    home_score: number;
    away_score: number;
    winner: string | null;
};

export type SimSeriesLine = {
    round: string;
    league: string | null;
    home_team: string;
    away_team: string;
    home_team_wins: number;
    away_team_wins: number;
    winner: string | null;
    /** Absent for summaries persisted before per-game postseason data existed. */
    games?: SimPostseasonGameLine[];
};

export type SimTeamRecord = {
    name: string;
    identity: SimTeamIdentity | null;
    league: string | null;
    division: string | null;
    points: number;
    wins: number;
    losses: number;
    win_pct: number;
    games_back: number | null;
    playoff_seeding: number | null;
};

export type SimTeamSeason = {
    identity: SimTeamIdentity | null;
    replaced_abbr: string | null;
    wins: number;
    losses: number;
    win_pct: number;
    points: number;
    division: string | null;
    division_rank: number | null;
    division_size: number | null;
    games_back: number | null;
    playoff_seeding: number | null;
    made_playoffs: boolean;
    is_champion: boolean;
    longest_win_streak: number;
    longest_losing_streak: number;
};

export type SeasonSimSummary = {
    year: number;
    set: string;
    seed: number | null;
    runtime_seconds: number;
    schedule_length: number;
    original_schedule_length: number;
    generated_at: string;
    team: SimTeamSeason;
    games: SimGameLine[];
    players: SimStatLine[];
    standings: { divisions: Record<string, SimTeamRecord[]> };
    postseason: SimSeriesLine[];
    champion: string | null;
    /** Schedule key -> branding, for every club in the league. */
    identities: Record<string, SimTeamIdentity>;
    top_players: Record<PlayerSubType, SimStatLine[]>;
    league_totals: Record<string, SimStatLine>;
    real_league_averages: Record<string, SimStatLine>;
    /** Absent for summaries persisted before awards existed. */
    awards?: SeasonAwards | null;
};

export type SimJobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';

/**
 * Progress only — never carries the result. Job rows expire after a week, so once `status` is
 * 'succeeded' the result is read from `fetchSimSeason(job_id)` instead, which is permanent.
 */
export type SimJob = {
    job_id: string;
    user_id: string | null;
    team_id: string | null;
    status: SimJobStatus;
    phase: string | null;
    games_completed: number;
    games_total: number;
    config: Record<string, unknown> | null;
    error: string | null;
    created_at: string;
    updated_at: string;
    finished_at: string | null;
};

/**
 * A played season's list-view fields — shared by the leaderboard and personal history.
 * Branding is snapshotted from when the season was played, since the team can change afterward.
 */
export type SimSeasonListItem = {
    entry_id: number;
    job_id: string | null;
    team_id: string | null;
    team_name: string | null;
    team_abbreviation: string | null;
    primary_color: string | null;
    secondary_color: string | null;
    year: number;
    showdown_set: string | null;
    replaced_abbr: string | null;
    wins: number;
    losses: number;
    win_pct: number;
    points: number;
    division: string | null;
    division_rank: number | null;
    made_playoffs: boolean;
    is_champion: boolean;
    longest_win_streak: number;
    seed: number | null;
    created_at: string;
    /** Belongs to the signed-in viewer. */
    is_own: boolean;
};

/** A leaderboard row: one team's best run at a season, ranked against every other team's best. */
export type SimLeaderboardEntry = SimSeasonListItem & {
    /** Rank within the season, among the entries this viewer can see. */
    rank: number;
    /** How many times this team has played this season. The row shows its best run. */
    attempts: number;
};

export type SimLeaderboardSeason = {
    year: number;
    entries: SimLeaderboardEntry[];
    has_own_entry: boolean;
};

/** A season's full result, permanently addressable by the job id that produced it. */
export type SimSeasonDetail = SimSeasonListItem & {
    summary: SeasonSimSummary;
};

export type StartSeasonSimPayload = {
    team_id: string;
    year: number;
    set?: string;
    /** Era-correct club abbreviation. Omitted means the season's worst club. */
    replaces?: string;
    seed?: number | null;
};

/** The signed-in user's own in-flight job - at most one can exist at a time. */
export type ActiveSimJob = {
    job_id: string;
    team_id: string | null;
    phase: string | null;
    games_completed: number;
    games_total: number;
    created_at: string;
};

/**
 * Thrown by `startSeasonSim` when the user already has a simulation running. Carries the
 * blocking job's own id/team - which may belong to a different team than the one just
 * requested, since the cap is per-user, not per-team - so the caller can link straight to it.
 */
export class SimAlreadyRunningError extends Error {
    jobId: string;
    teamId: string | null;

    constructor(message: string, jobId: string, teamId: string | null) {
        super(message);
        this.name = 'SimAlreadyRunningError';
        this.jobId = jobId;
        this.teamId = teamId;
    }
}

// =============================================================================
// MARK: - REQUESTS
// =============================================================================

async function parseError(res: Response, fallback: string): Promise<never> {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `${fallback}: ${res.status}`);
}

// Season and club lists are stable for a given year, so they are cached for the browser
// session the same way `_splitsCache` works in mlbAPI.
const _seasonsCache: { value: number[] | null } = { value: null };
const _clubsCache = new Map<number, { teams: TakeoverClub[]; default: string | null }>();

export async function fetchSimSeasons(): Promise<number[]> {
    if (_seasonsCache.value) return _seasonsCache.value;
    const res = await fetch(`${API_BASE}/sim/seasons`);
    if (!res.ok) await parseError(res, 'Failed to load seasons');
    const data = await res.json();
    _seasonsCache.value = data.seasons ?? [];
    return _seasonsCache.value!;
}

export async function fetchSimSeasonTeams(year: number): Promise<{ teams: TakeoverClub[]; default: string | null }> {
    const cached = _clubsCache.get(year);
    if (cached) return cached;
    const res = await fetch(`${API_BASE}/sim/seasons/${year}/teams`);
    if (!res.ok) await parseError(res, 'Failed to load teams');
    const data = await res.json();
    const value = { teams: data.teams ?? [], default: data.default ?? null };
    _clubsCache.set(year, value);
    return value;
}

export async function startSeasonSim(payload: StartSeasonSimPayload, token: string): Promise<{ job_id: string; replaces: string }> {
    const res = await fetch(`${API_BASE}/sim/season`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
    });
    if (res.status === 429) {
        const err = await res.json().catch(() => ({}));
        if (err.job_id) throw new SimAlreadyRunningError(err.error ?? 'A simulation is already running.', err.job_id, err.team_id ?? null);
    }
    if (!res.ok) await parseError(res, 'Failed to start simulation');
    return res.json();
}

/**
 * Played seasons with their ranked entries, newest season first. Public teams only, plus the
 * viewer's own private results when a token is supplied.
 */
export async function fetchSimLeaderboard(token?: string, year?: number): Promise<SimLeaderboardSeason[]> {
    const params = year ? `?year=${year}` : '';
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/sim/leaderboard${params}`, { headers });
    if (!res.ok) await parseError(res, 'Failed to load leaderboard');
    const data = await res.json();
    return data.seasons ?? [];
}

/** Poll a job's progress. Returns 404 once the job row has expired — the result outlives it. */
export async function fetchSimJob(jobId: string, token: string): Promise<SimJob> {
    const res = await fetch(`${API_BASE}/sim/jobs/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) await parseError(res, 'Failed to load simulation');
    return res.json();
}

/** Cancel the signed-in user's own queued/running job. The worker thread notices on its next
 *  progress write and stops simulating - the caller's next poll picks up the new status. */
export async function cancelSimJob(jobId: string, token: string): Promise<void> {
    const res = await fetch(`${API_BASE}/sim/jobs/${jobId}/cancel`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) await parseError(res, 'Failed to cancel simulation');
}

/** The signed-in user's own in-flight job, if any - lets a caller check without attempting a
 *  start first. */
export async function fetchActiveSimJob(token: string): Promise<ActiveSimJob | null> {
    const res = await fetch(`${API_BASE}/sim/jobs/active`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) await parseError(res, 'Failed to check for an active simulation');
    const data = await res.json();
    return data.job ?? null;
}

/**
 * A played season's full result. Works indefinitely, including for jobs whose progress row has
 * long since expired — this is the permanent record. `token` is optional: an anonymous caller
 * sees it if the team is public.
 */
export async function fetchSimSeason(jobId: string, token?: string): Promise<SimSeasonDetail | null> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/sim/season/${jobId}`, { headers });
    if (res.status === 404) return null;
    if (!res.ok) await parseError(res, 'Failed to load season');
    return res.json();
}

/** The signed-in user's own played seasons, newest first — every run, not just the best. */
export async function fetchSimHistory(token: string, teamId?: string): Promise<SimSeasonListItem[]> {
    const params = teamId ? `?team_id=${teamId}` : '';
    const res = await fetch(`${API_BASE}/sim/history${params}`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) await parseError(res, 'Failed to load your simulation history');
    const data = await res.json();
    return data.seasons ?? [];
}

/**
 * Every season played with a specific team, newest first, regardless of who ran it — a public
 * team can be simulated by any signed-in user. Used to decide whether a team's own "Sims" tab
 * has anything to show.
 */
export async function fetchTeamSimSeasons(teamId: string, token?: string, limit = 10): Promise<SimSeasonListItem[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/sim/teams/${teamId}/seasons?limit=${limit}`, { headers });
    if (!res.ok) await parseError(res, 'Failed to load simulations for this team');
    const data = await res.json();
    return data.seasons ?? [];
}
