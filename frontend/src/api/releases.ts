import { fetchCardData, type CardDatabaseRecord, type ImageMatchType } from './card_db/cardDatabase';
import { CardSource } from '../types/cardSource';
import type { CardStyleSettings } from '../components/customs/cardStyle';

const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// =============================================================================
// MARK: - TYPES
// =============================================================================

export type ReleaseEditionSummary = {
    id: string;
    name: string;
    attributes: Record<string, unknown>;
    slug: string;
    is_published: boolean;
    card_count: number;
};

/** A rendered card image shown off on a release's list tile. */
export type ReleasePreviewImage = {
    /** Path in the `card_images` bucket (see `cardImagePublicUrl`). */
    thumbnail_path: string;
    name: string | null;
};

export type Release = {
    id: string;
    name: string;
    description: string | null;
    created_by: string;
    is_official: boolean;
    fork_parent_id: string | null;
    slug: string;
    default_showdown_set: string | null;
    editions: ReleaseEditionSummary[];
    /** List endpoints only: up to 3 rendered card images — user-ranked cards (`preview_rank`) first,
     * then first edition first, then highest points. */
    preview_images?: ReleasePreviewImage[];
    /** Creator's profile username (null if they haven't set one). */
    creator_username?: string | null;
    /** Distinct Showdown sets across the release's cards (published editions only in public lists).
     * List endpoints only. */
    showdown_sets?: string[];
    created_at: string;
    updated_at: string;
};

/** Per-card tweaks layered over the edition's defaults. `style` holds only the fields that differ
 * from the edition style, so later edition style changes still reach everything else. */
export type ReleaseCardOverrides = {
    style?: Partial<CardStyleSettings>;
};

export type ReleaseCard = {
    id: string;
    card_number: number | null;
    source_card_id: string | null;
    source_card_type: string | null;
    card_snapshot: CardDatabaseRecord;
    /** User labels, e.g. "FOIL" to track which cards will be printed as foils. Stored uppercase. */
    tags: string[];
    /** User-chosen slot (1-3, 1 = front) on the release's list tile; null leaves it to the default pick. */
    preview_rank: number | null;
    /** Null when the card just follows its edition's style */
    card_overrides: ReleaseCardOverrides | null;
};

export type ReleaseEdition = {
    id: string;
    release_id: string;
    name: string;
    attributes: Record<string, unknown>;
    slug: string;
    is_published: boolean;
    cards: ReleaseCard[];
    created_at: string;
    updated_at: string;
};

export type ReleaseCreatePayload = {
    name: string;
    description?: string | null;
    default_showdown_set?: string | null;
};

export type ReleaseUpdatePayload = Partial<ReleaseCreatePayload>;

export type ReleaseEditionCreatePayload = {
    name: string;
    attributes?: Record<string, unknown>;
    cards?: Array<{
        card_number?: number | null;
        source_card_id?: string | null;
        source_card_type?: string | null;
        card_snapshot: CardDatabaseRecord;
        tags?: string[];
        preview_rank?: number | null;
        card_overrides?: ReleaseCardOverrides | null;
    }>;
};

export type ReleaseEditionUpdatePayload = Partial<Omit<ReleaseEditionCreatePayload, 'cards'>> & {
    cards?: ReleaseEditionCreatePayload['cards'];
    /** Published editions are visible to everyone; a release is listed publicly once any edition is. */
    is_published?: boolean;
};

export type AlgorithmPlayerTypeDistribution = {
    hitters_percentage: number;
    starters_percentage: number;
    relievers_percentage: number;
};

export type AlgorithmPointBucket = {
    min_points: number;
    max_points: number;
    /** 0-1 share of each player type's cards targeted in this range. */
    percentage: number;
};

/** How each team's share of the set is decided: `EVEN` (WOTC 2000/2001) or more cards for stronger teams (WOTC 2002-2005). */
export type AlgorithmTeamWeighting = 'EVEN' | 'STRENGTH';

/** Cards every team gets of each player type, so each team can field a club. */
export type AlgorithmTeamMinimums = {
    hitters: number;
    starters: number;
    relievers: number;
};

/** Players who already have a card in another edition of the release: allowed, left out, or only allowed on a new team. */
export type AlgorithmOtherEditionsRule = 'ALLOW' | 'EXCLUDE' | 'NEW_TEAM_ONLY';

/** Relative importance (0-1) of each factor when the algorithm picks the next card. */
export type AlgorithmSelectionWeights = {
    /** WAR plus All-Star/award bonuses. */
    quality: number;
    /** Playing time: PA for hitters, IP for pitchers. */
    volume: number;
    /** Keep each team near its target share of the set (see `AlgorithmTeamWeighting`). */
    team_balance: number;
    /** Steer each position toward its target average points (only applies with position targets). */
    points_fit: number;
    /** Career WAR through the set's latest year, to favor established veterans. */
    career: number;
};

/** Share of the set at a position, e.g. 7% shortstops averaging 220 pts. */
export type AlgorithmPositionTarget = {
    /** Slot position: C, 1B, 2B, 3B, SS, CF, LF/RF, DH, STARTER, RELIEVER, CLOSER. */
    position: string;
    /** 0-1 share of the whole set. */
    percentage: number;
    avg_points: number | null;
};

export type AlgorithmConfig = {
    set_size: number;
    years: string;
    showdown_sets: string[];
    min_games_hitters?: number;
    min_ip_starters?: number;
    min_ip_relievers?: number;
    player_type_distribution?: AlgorithmPlayerTypeDistribution;
    include_all_stars?: boolean;
    include_award_winners?: boolean;
    /** Restrict the qualified player pool to players who received an All-Star selection that year. */
    all_stars_only?: boolean;
    /** Career WAR (through the latest year) at which a player skips the games/IP minimums and is guaranteed a card. Null to disable. */
    legend_min_career_war?: number | null;
    /** Point ranges (inclusive) with an ideal share of each player type's cards, e.g. 15% at 10-50 pts. */
    point_buckets?: AlgorithmPointBucket[];
    selection_weights?: AlgorithmSelectionWeights;
    /** Per-position composition (e.g. from a WOTC base set). Replaces `player_type_distribution` when non-empty. */
    position_targets?: AlgorithmPositionTarget[];
    /** 2000/2001 only: uncap speed (instead of 10/15/20) and recalculate each card's points. */
    variable_speed?: boolean;
    /** At most one card per player, even across multiple years or showdown sets. */
    unique_players?: boolean;
    team_weighting?: AlgorithmTeamWeighting;
    team_minimums?: AlgorithmTeamMinimums;
    other_editions_rule?: AlgorithmOtherEditionsRule;
    /** Frontend-only: the Algorithm tab template these settings started from. Saved with the edition; ignored by the backend. */
    template_id?: string;
};

export type AlgorithmPreviewPlayer = CardDatabaseRecord & { algorithm_set_number: number | null };

export type AlgorithmPreviewResult = {
    players: AlgorithmPreviewPlayer[];
    summary: {
        requested_set_size: number;
        actual_count: number;
        warnings: string[];
    };
};

// =============================================================================
// MARK: - API CALLS: RELEASES
// =============================================================================

export async function fetchMyReleases(token: string): Promise<Release[]> {
    const res = await fetch(`${API_BASE}/releases`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Failed to fetch releases: ${res.status}`);
    return res.json();
}

export async function fetchPublicReleases(limit = 50, offset = 0): Promise<Release[]> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    const res = await fetch(`${API_BASE}/releases/public?${params}`);
    if (!res.ok) throw new Error(`Failed to fetch public releases: ${res.status}`);
    return res.json();
}

export async function fetchRelease(releaseId: string, token?: string): Promise<Release> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/releases/${releaseId}`, { headers });
    if (!res.ok) throw new Error(`Failed to fetch release: ${res.status}`);
    return res.json();
}

export async function createRelease(payload: ReleaseCreatePayload, token: string): Promise<Release> {
    const res = await fetch(`${API_BASE}/releases`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to create release: ${res.status}`);
    }
    return res.json();
}

export async function updateRelease(releaseId: string, payload: ReleaseUpdatePayload, token: string): Promise<Release> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to update release: ${res.status}`);
    }
    return res.json();
}

export async function deleteRelease(releaseId: string, token: string): Promise<void> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to delete release: ${res.status}`);
    }
}

// =============================================================================
// MARK: - API CALLS: EDITIONS
// =============================================================================

export async function fetchEdition(releaseId: string, editionId: string, token?: string): Promise<ReleaseEdition> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}`, { headers });
    if (!res.ok) throw new Error(`Failed to fetch edition: ${res.status}`);
    return res.json();
}

export async function createEdition(releaseId: string, payload: ReleaseEditionCreatePayload, token: string): Promise<ReleaseEdition> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to create edition: ${res.status}`);
    }
    return res.json();
}

export async function updateEdition(releaseId: string, editionId: string, payload: ReleaseEditionUpdatePayload, token: string): Promise<ReleaseEdition> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to update edition: ${res.status}`);
    }
    return res.json();
}

export async function deleteEdition(releaseId: string, editionId: string, token: string): Promise<void> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to delete edition: ${res.status}`);
    }
}

export type AlgorithmPreviewOptions = {
    /** Admin-only: rebuild each selected card through the current card algorithm instead of
     * returning the archived version. Rejected with a 403 for non-admins. */
    rerun_cards?: boolean;
    /** Players (bref_id w/ type override) always put in the set, regardless of the eligibility minimums. */
    manually_included_ids?: string[];
    /** Players (bref_id w/ type override) always left out of the set. */
    manually_excluded_ids?: string[];
};

export async function previewAlgorithm(releaseId: string, editionId: string, config: AlgorithmConfig, token: string, options: AlgorithmPreviewOptions = {}): Promise<AlgorithmPreviewResult> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}/algorithm/preview`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ ...config, ...options }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to run algorithm: ${res.status}`);
    }
    return res.json();
}

/** The snapshot of one of the edition's Bot cards rebuilt at another chart version (1 restores the
 * archived card). Doesn't persist — save the returned snapshot through `updateEdition`. */
export async function rebuildEditionCard(releaseId: string, editionId: string, sourceCardId: string, chartVersion: number, token: string): Promise<CardDatabaseRecord> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}/cards/rebuild`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ source_card_id: sourceCardId, chart_version: chartVersion }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to rebuild card: ${res.status}`);
    }
    const data = await res.json();
    return data.card_snapshot;
}

// =============================================================================
// MARK: - API CALLS: EDITION IMAGES
// =============================================================================

/** `rendered`: image matches the card's current style/number. `stale`: an older render is shown.
 * `failed`: the current inputs failed to render. `missing`: never rendered. */
export type ReleaseCardImageStatus = 'rendered' | 'stale' | 'failed' | 'missing';

export type ReleaseCardImage = {
    source_card_id: string;
    /** Set number as printed on the card, e.g. "AS007". */
    set_number: string | null;
    status: ReleaseCardImageStatus;
    /** Paths in the `card_images` bucket (see `cardImagePublicUrl`). Set for rendered and stale images. */
    storage_path: string | null;
    thumbnail_path: string | null;
    error: string | null;
    rendered_at: string | null;
};

export type ReleaseImageJobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';

export type ReleaseImageJob = {
    id: string;
    edition_id: string;
    status: ReleaseImageJobStatus;
    total: number;
    completed: number;
    failed: number;
    error: string | null;
    created_at: string;
    updated_at: string;
    finished_at: string | null;
};

export type EditionImages = {
    images: ReleaseCardImage[];
    /** Latest render job, if one has ever run. */
    job: ReleaseImageJob | null;
};

export const isImageJobActive = (job: ReleaseImageJob | null): boolean =>
    job?.status === 'queued' || job?.status === 'running';

async function editionImagesRequest<T>(releaseId: string, editionId: string, path: string, init: RequestInit, token?: string): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}/images${path}`, { ...init, headers });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Edition images request failed: ${res.status}`);
    }
    return res.json();
}

export function fetchEditionImages(releaseId: string, editionId: string, token?: string): Promise<EditionImages> {
    return editionImagesRequest(releaseId, editionId, '', { method: 'GET' }, token);
}

/** Starts a background render of missing/out-of-date images (optionally only `sourceCardIds`). */
export async function renderEditionImages(releaseId: string, editionId: string, token: string, sourceCardIds?: string[]): Promise<ReleaseImageJob> {
    const body = JSON.stringify(sourceCardIds ? { source_card_ids: sourceCardIds } : {});
    const { job } = await editionImagesRequest<{ job: ReleaseImageJob }>(releaseId, editionId, '/render', { method: 'POST', body }, token);
    return job;
}

/** A card's auto image match against the owner's image libraries, as a render would search them. */
export type LiveImageMatch = {
    image_match_type: ImageMatchType;
    /** Library the render would pull from (a connected Google Drive folder or "Showdown Bot"); null when no library has the player. */
    library_name: string | null;
};

export type LiveImageMatches = {
    /** Keyed by card snapshot `id`. */
    matches: Record<string, LiveImageMatch>;
    /** When the oldest library listing used was read from Drive. */
    checked_at: string;
};

/** Re-checks each snapshot's auto image match. `refresh` re-reads the libraries from Drive instead of the ~10 minute server cache. */
export function fetchLiveImageMatches(releaseId: string, editionId: string, cards: CardDatabaseRecord[], token: string, refresh = false): Promise<LiveImageMatches> {
    const body = JSON.stringify({ cards, refresh });
    return editionImagesRequest(releaseId, editionId, '/matches', { method: 'POST', body }, token);
}

export async function cancelEditionImageRender(releaseId: string, editionId: string, token: string): Promise<ReleaseImageJob> {
    const { job } = await editionImagesRequest<{ job: ReleaseImageJob }>(releaseId, editionId, '/cancel', { method: 'POST' }, token);
    return job;
}

// =============================================================================
// MARK: - API CALLS: WOTC COMPARISON
// =============================================================================

/** The original WOTC base sets a release can be benchmarked against. */
export const WOTC_BASE_SETS = ['2000', '2001', '2002', '2003', '2004', '2005'] as const;
export type WotcBaseSet = typeof WOTC_BASE_SETS[number];

// WOTC sets never change, so a browser-session cache is safe. Stores the in-flight promise so
// rapid toggling between sets doesn't fire duplicate requests.
const _wotcBaseSetCache = new Map<WotcBaseSet, Promise<CardDatabaseRecord[]>>();

/** Position composition of an original WOTC base set, used as an Algorithm blueprint. */
export type WotcSetProfile = {
    showdown_set: WotcBaseSet;
    set_size: number;
    team_count: number;
    position_targets: AlgorithmPositionTarget[];
    /** Low point buckets that bring the set's 10-100 pt card counts closer to WOTC's. */
    point_buckets: AlgorithmPointBucket[];
    /** `EVEN` for 2000/2001 (15-17 cards per team), `STRENGTH` from 2002 (5-16 per team). */
    team_weighting: AlgorithmTeamWeighting;
};

let _wotcSetProfilesRequest: Promise<WotcSetProfile[]> | null = null;

/** Profiles for every WOTC base set. Cached for the browser session since WOTC sets never change. */
export function fetchWotcSetProfiles(): Promise<WotcSetProfile[]> {
    if (!_wotcSetProfilesRequest) {
        _wotcSetProfilesRequest = fetch(`${API_BASE}/releases/algorithm/wotc_profiles`).then(async res => {
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `Failed to load WOTC set profiles: ${res.status}`);
            }
            return res.json();
        });
        _wotcSetProfilesRequest.catch(() => { _wotcSetProfilesRequest = null; });
    }
    return _wotcSetProfilesRequest;
}

/** Every card in a WOTC base set (expansion `BS` — excludes promos, Pennant Run, Trading Deadline, etc.). */
export function fetchWotcBaseSet(showdownSet: WotcBaseSet): Promise<CardDatabaseRecord[]> {
    let request = _wotcBaseSetCache.get(showdownSet);
    if (!request) {
        request = fetchCardData(CardSource.WOTC, { showdown_set: [showdownSet], expansion: ['BS'], limit: 1000 });
        request.catch(() => _wotcBaseSetCache.delete(showdownSet));
        _wotcBaseSetCache.set(showdownSet, request);
    }
    return request;
}
