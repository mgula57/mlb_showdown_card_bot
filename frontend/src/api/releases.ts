import { fetchCardData, type CardDatabaseRecord } from './card_db/cardDatabase';
import { CardSource } from '../types/cardSource';

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
    created_at: string;
    updated_at: string;
};

export type ReleaseCard = {
    id: string;
    card_number: number | null;
    source_card_id: string | null;
    source_card_type: string | null;
    card_snapshot: CardDatabaseRecord;
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
    }>;
};

export type ReleaseEditionUpdatePayload = Partial<Omit<ReleaseEditionCreatePayload, 'cards'>> & {
    cards?: ReleaseEditionCreatePayload['cards'];
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
    /** Point ranges (inclusive) with an ideal share of each player type's cards, e.g. 15% at 10-50 pts. */
    point_buckets?: AlgorithmPointBucket[];
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

// =============================================================================
// MARK: - API CALLS: WOTC COMPARISON
// =============================================================================

/** The original WOTC base sets a release can be benchmarked against. */
export const WOTC_BASE_SETS = ['2000', '2001', '2002', '2003', '2004', '2005'] as const;
export type WotcBaseSet = typeof WOTC_BASE_SETS[number];

// WOTC sets never change, so a browser-session cache is safe. Stores the in-flight promise so
// rapid toggling between sets doesn't fire duplicate requests.
const _wotcBaseSetCache = new Map<WotcBaseSet, Promise<CardDatabaseRecord[]>>();

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
