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
    /** When the edition first went public. Once set, the owner edits it through a working copy. */
    published_at: string | null;
    card_count: number;
    /** The owner's private working copy of this published edition, while they edit it. */
    draft: ReleaseEditionDraftSummary | null;
    /** Owner only: deleted while the release is published, so it stays live until the next publish retires it. */
    pending_removal?: boolean;
};

export type ReleaseEditionDraftSummary = {
    id: string;
    name: string;
    card_count: number;
};

/** A rendered card image shown off on a release's list tile. */
export type ReleasePreviewImage = {
    /** Path in the `card_images` bucket (see `cardImagePublicUrl`). */
    thumbnail_path: string;
    /** The full-size render, for the share image. */
    storage_path?: string | null;
    name: string | null;
};

/** The release a remix was started from, for its "Remixed from" credit. */
export type ReleaseForkParent = {
    id: string;
    name: string;
    creator_username: string | null;
    /** Published, listed and not deleted, so the credit can link to it (a link-only source stays unlinked). */
    is_linkable: boolean;
};

export type Release = {
    id: string;
    name: string;
    description: string | null;
    created_by: string;
    is_official: boolean;
    /** Set on a remix: the release it was started from. */
    fork_parent_id: string | null;
    fork_parent: ReleaseForkParent | null;
    /** The owner lets others remix it (start their own release from it). On by default. */
    allow_remix: boolean;
    /** Owner-set "work in progress" label. */
    is_wip: boolean;
    slug: string;
    default_showdown_set: string | null;
    editions: ReleaseEditionSummary[];
    /** Up to 3 rendered card images — user-ranked cards (`preview_rank`) first, then first edition
     * first, then highest points. Single-release fetches draw from published editions only. */
    preview_images?: ReleasePreviewImage[];
    /** Creator's profile username (null if they haven't set one). */
    creator_username?: string | null;
    /** Distinct Showdown sets across the release's cards (published editions only in public lists).
     * List endpoints only. */
    showdown_sets?: string[];
    /** First publish time; null until the release is published. Kept when it's unpublished. */
    published_at: string | null;
    /** 0 until the first publish. Once published, edits are staged in working copies until republished. */
    published_version: number;
    /** An already-published release has unpublished edits (a changed working copy or a new edition). */
    has_pending_changes: boolean;
    /** `card_images` path of the link-preview image, rendered when the release is published. */
    share_image_path: string | null;
    /** When the current version was published (null for releases published before versions were kept). */
    version_published_at: string | null;
    view_count: number;
    like_count: number;
    /** False for a link-only release: it opens from its link but stays out of the public list and search. */
    is_listed: boolean;
    /** Single-release fetches with a signed-in viewer only. */
    liked_by_me?: boolean;
    /** Saved to the viewer's card search. Single-release fetches with a signed-in viewer, and the saved list. */
    saved_by_me?: boolean;
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
    /** Cards saved from an Algorithm run also carry how they were picked (see `AlgorithmPickFields`) */
    card_snapshot: CardDatabaseRecord & Partial<AlgorithmPickFields>;
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
    /** Set on a working copy: the published edition it will replace. */
    draft_of: string | null;
    published_at: string | null;
    cards: ReleaseCard[];
    /** Goes up with every card save; a save sends the one it was based on (`expected_cards_version`). */
    cards_version: number;
    created_at: string;
    updated_at: string;
};

/** The list-level summary of a freshly created edition. */
export const editionSummaryOf = (edition: ReleaseEdition): ReleaseEditionSummary => ({
    id: edition.id,
    name: edition.name,
    attributes: edition.attributes,
    slug: edition.slug,
    is_published: edition.is_published,
    published_at: edition.published_at,
    card_count: edition.cards.length,
    draft: null,
    pending_removal: false,
});

export type ReleaseCreatePayload = {
    name: string;
    description?: string | null;
    default_showdown_set?: string | null;
};

export type ReleaseUpdatePayload = Partial<ReleaseCreatePayload> & {
    is_listed?: boolean;
    allow_remix?: boolean;
    is_wip?: boolean;
};

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
    /** With `cards`: the `cards_version` the list was built on, so a stale tab can't overwrite newer cards. */
    expected_cards_version?: number;
};

/** A card save was refused because the edition's cards changed elsewhere (another tab or device). */
export class StaleEditionError extends Error {}

/** The error an edition save failed with: a `StaleEditionError` for the server's stale-cards 409. */
async function editionSaveError(res: Response, fallback: string): Promise<Error> {
    const err = await res.json().catch(() => ({}));
    if (res.status === 409 && err.code === 'stale_edition') return new StaleEditionError(err.error);
    return new Error(err.error || `${fallback}: ${res.status}`);
}

/** `blocker` stops a publish; `check` is worth a look; `polish` is a nudge. */
export type ReleaseReviewLevel = 'blocker' | 'check' | 'polish';

/** Where the builder opens to fix a review item. `details` is the release's own name/description. */
export type ReleaseReviewFixTarget = {
    step: 'pool' | 'images' | 'style' | 'details';
    /** The edition to open; null for `details`. */
    edition_id: string | null;
    /** Pre-filters the Images step to this status. */
    image_status: Extract<ReleaseCardImageStatus, 'missing' | 'stale' | 'failed'> | null;
};

/** One line of the pre-publish checklist (`ReleaseReview` on the backend). */
export type ReleaseReviewItem = {
    id: string;
    level: ReleaseReviewLevel;
    /** Null for release-wide items. */
    edition_id: string | null;
    title: string;
    detail: string | null;
    /** A check that found nothing to fix, shown as a quiet tick. */
    passed: boolean;
    fix: ReleaseReviewFixTarget | null;
};

export type ReleaseCardChange = {
    name: string;
    detail: string;
    /** Saved teams holding the live card (removed and changed cards). */
    team_count: number;
};

/** What republishing changes in one edition (its working copy against the live edition). */
export type ReleaseEditionChanges = {
    /** The edition being edited: the working copy, or a new edition itself. */
    edition_id: string;
    name: string;
    renamed_from: string | null;
    is_new: boolean;
    /** A published edition the owner deleted: publishing retires it, so every card counts as removed. */
    is_removed: boolean;
    added: ReleaseCardChange[];
    removed: ReleaseCardChange[];
    changed: ReleaseCardChange[];
    renumbered: number;
    /** Tags, cover picks and per-card style tweaks. */
    details_changed: number;
    settings_changed: boolean;
    has_changes: boolean;
};

export type ReleaseChanges = {
    editions: ReleaseEditionChanges[];
    removed_team_count: number;
    changed_team_count: number;
    has_changes: boolean;
};

export type ReleaseReview = {
    items: ReleaseReviewItem[];
    /** The release as its list tile shows it to others (preview images, sets). */
    tile: Release | null;
    /** What republishing would change; null before the first publish, when everything is new. */
    changes: ReleaseChanges | null;
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
    /** Sets for every card, or only hitters when `pitcher_showdown_sets` is set. */
    showdown_sets: string[];
    /** Sets for pitchers, e.g. 2000 hitters with 2001 pitchers. Null to use `showdown_sets` for everyone. */
    pitcher_showdown_sets?: string[] | null;
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

/** How a card got into an Algorithm run's set (mirrors the backend's `SelectionReason`) */
export type AlgorithmSelectionReason = 'WEIGHTED' | 'MANUAL' | 'LEGEND' | 'TEAM_MINIMUM' | 'POINTS_SWAP';

/** Added to each player an Algorithm run picks, and saved on the card's snapshot. */
export type AlgorithmPickFields = {
    /** 0-100: quality, volume and career ranked within the player's type and weighted by the run's settings */
    algorithm_match_score: number | null;
    algorithm_selection_reason: AlgorithmSelectionReason | null;
    /** The full selection score (match score plus team balance and points fit) when picked; can pass 100 */
    algorithm_pick_score: number | null;
    /** Best pick score left out of the card's slot group when it filled; null when nobody was left out */
    algorithm_cut_line: number | null;
};

/** A selection score split into its parts, on the match score's scale (`total` = the three summed) */
export type AlgorithmScoreBreakdown = {
    match: number;
    team_balance: number;
    points_fit: number;
    total: number;
};

/** A player on either side of a cut line, with their score in the state they were judged in */
export type AlgorithmCutLinePlayer = {
    /** The `card_bot` row id; for picks, the preview player's id */
    id: string;
    name: string;
    year: number;
    team: string;
    points: number | null;
    breakdown: AlgorithmScoreBreakdown | null;
};

/** One slot group's closest call: the best player left out when its last slot filled */
export type AlgorithmCutLine = {
    /** A position (with position targets), a player type, or 'ANY' for the final catch-all fill */
    group: string;
    player_subtype: 'POSITION_PLAYER' | 'STARTING_PITCHER' | 'RELIEF_PITCHER' | null;
    pick_score: number;
    name: string;
    year: number;
    team: string;
    /** Cards the group ended up with */
    slot_count?: number;
    /** The group's lowest scoring picks, lowest first */
    picks?: (AlgorithmCutLinePlayer & { selection_reason: AlgorithmSelectionReason | null })[];
    /** The closest calls left out when the last slot filled, best first (the first is the line itself) */
    near_misses?: AlgorithmCutLinePlayer[];
    /** Picks a point bucket swap took the slot from, scored as they were when picked */
    swapped_out?: (AlgorithmCutLinePlayer & { replaced_by: string })[];
};

export type AlgorithmPreviewPlayer = CardDatabaseRecord & AlgorithmPickFields & { algorithm_set_number: number | null };

export type AlgorithmPreviewResult = {
    players: AlgorithmPreviewPlayer[];
    summary: {
        requested_set_size: number;
        actual_count: number;
        warnings: string[];
        /** Per slot group, the best player left out when it filled */
        cut_lines: AlgorithmCutLine[];
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

/** Other users' published releases the viewer saved, most recently saved first. */
export async function fetchSavedReleases(token: string): Promise<Release[]> {
    const res = await fetch(`${API_BASE}/releases/saved`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Failed to fetch saved releases: ${res.status}`);
    return res.json();
}

export type PublicReleaseSort = 'popular' | 'new';

export type PublicReleaseQuery = {
    /** `official` (curated) or `community` (everyone else's); both when left out. */
    section?: 'official' | 'community';
    /** Most recently updated first when left out. */
    sort?: PublicReleaseSort;
    /** Matches the release name or its creator's username. */
    search?: string;
};

export async function fetchPublicReleases(limit = 50, offset = 0, query: PublicReleaseQuery = {}): Promise<Release[]> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (query.section) params.set('section', query.section);
    if (query.sort) params.set('sort', query.sort);
    if (query.search?.trim()) params.set('q', query.search.trim());
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

/** One published version, from `internal.release_versions`. */
export type ReleaseVersion = {
    version: number;
    note: string | null;
    /** Per edition that changed: counts of added / removed / changed cards (see `EditionChanges.summary`). */
    changes: Array<{ name: string; renamed_from: string | null; is_new: boolean; is_removed?: boolean; added: number; removed: number; changed: number; renumbered: number }>;
    published_at: string | null;
};

export async function fetchReleaseVersions(releaseId: string, token?: string): Promise<ReleaseVersion[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/releases/${releaseId}/versions`, { headers });
    if (!res.ok) throw new Error(`Failed to load version history: ${res.status}`);
    return res.json();
}

export async function toggleReleaseLike(releaseId: string, token: string): Promise<{ liked: boolean; like_count: number }> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/like`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to like the release: ${res.status}`);
    }
    return res.json();
}

/** Saves someone else's release (or unsaves it) so its cards show in the Card Explorer's Releases tab. */
export async function toggleReleaseSave(releaseId: string, token: string): Promise<{ saved: boolean }> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/save`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to save the release: ${res.status}`);
    }
    return res.json();
}

/** Counts a visit. Fire-and-forget: `.catch(() => {})` it, a failure must never block the page. */
export async function recordReleaseView(releaseId: string, token?: string): Promise<void> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    await fetch(`${API_BASE}/releases/${releaseId}/view`, { method: 'POST', headers });
}

/** The release behind a short link (`/r/<slug>`). */
export async function fetchReleaseBySlug(slug: string, token?: string): Promise<Release> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/releases/by-slug/${encodeURIComponent(slug)}`, { headers });
    if (!res.ok) throw new Error(res.status === 404 ? 'Release not found' : `Failed to fetch release: ${res.status}`);
    return res.json();
}

/** The release's link-preview image path, rendered on the spot if it's missing or out of date. */
export async function ensureReleaseShareImage(releaseId: string): Promise<string> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/share_image`, { method: 'POST' });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to make the preview image: ${res.status}`);
    }
    return (await res.json()).share_image_path;
}

/** The short link to share a release by, or one of its editions, or one card (by release card id,
 *  which stays the same through renumbering and republishing). */
export const releaseShareUrl = (slug: string, editionSlug?: string | null, releaseCardId?: string | null): string =>
    `${window.location.origin}/r/${slug}${editionSlug ? `/${editionSlug}${releaseCardId ? `/${releaseCardId}` : ''}` : ''}`;

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

/** Start a new release owned by the caller from someone else's published one: its live editions,
 *  cards, card styles and algorithm settings, unpublished and credited to the source. */
export async function remixRelease(releaseId: string, payload: ReleaseCreatePayload, token: string): Promise<Release> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/remix`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to remix release: ${res.status}`);
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

export async function fetchReleaseReview(releaseId: string, token: string): Promise<ReleaseReview> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/review`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to load the review: ${res.status}`);
    }
    return res.json();
}

/** Publishes or unpublishes every edition at once. Publishing is refused while a review blocker is
 * open; on an already-published release it folds the working copies in as a new version, with `note`. */
export async function setReleasePublished(releaseId: string, published: boolean, token: string, note?: string): Promise<Release> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/${published ? 'publish' : 'unpublish'}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(published && note ? { note } : {}),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to ${published ? 'publish' : 'unpublish'} release: ${res.status}`);
    }
    return res.json();
}

/** Opens (or, with `discard`, throws away) the owner's working copies of a published release. */
export async function releaseDraftRequest(releaseId: string, action: 'start' | 'discard', token: string): Promise<Release> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/draft`, {
        method: action === 'start' ? 'POST' : 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to ${action === 'start' ? 'start editing' : 'discard changes'}: ${res.status}`);
    }
    return res.json();
}

/** Deletes the release. One that was ever published, or has cards on teams, is retired instead
 *  (`retired: true`): gone from every list, link and search, with teams keeping its cards as retired. */
export async function deleteRelease(releaseId: string, token: string): Promise<{ retired: boolean }> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to delete release: ${res.status}`);
    }
    return res.json();
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
    if (!res.ok) throw await editionSaveError(res, 'Failed to update edition');
    return res.json();
}

/** The release card fields a patch can change; anything else saves the full card list. */
export const PATCHABLE_CARD_FIELDS = ['card_number', 'tags', 'preview_rank', 'card_overrides'] as const;
export type ReleaseCardPatch = { source_card_id: string } & Partial<Pick<ReleaseCard, typeof PATCHABLE_CARD_FIELDS[number]>>;

/** Saves just the changed fields of some cards (numbers, tags, cover picks, style overrides),
 *  instead of re-sending every card snapshot with `updateEdition`. Returns the new `cards_version`. */
export async function patchEditionCards(releaseId: string, editionId: string, cards: ReleaseCardPatch[], expectedCardsVersion: number, token: string): Promise<number> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}/cards`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ cards, expected_cards_version: expectedCardsVersion }),
    });
    if (!res.ok) throw await editionSaveError(res, 'Failed to save changes');
    return (await res.json()).cards_version;
}

/** How deleting an edition went: a published one is `staged` until the next publish; a
 *  never-published one is `deleted`, or `retired` when some of its cards are on teams. */
export type EditionDeleteOutcome = 'staged' | 'deleted' | 'retired';

export async function deleteEdition(releaseId: string, editionId: string, token: string): Promise<{ outcome: EditionDeleteOutcome; release: Release }> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to delete edition: ${res.status}`);
    }
    return res.json();
}

/** Undoes a published edition's staged removal. Returns the updated release. */
export async function restoreEdition(releaseId: string, editionId: string, token: string): Promise<Release> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}/restore`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to restore edition: ${res.status}`);
    }
    return res.json();
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

/** `BASE` gives every team a foil (its best card) and stronger teams more; `EXPANSION` takes the season's standouts anywhere. */
export type FoilSetType = 'BASE' | 'EXPANSION';

export type FoilSuggestion = {
    source_card_id: string;
    /** 0-100 */
    score: number;
    /** Why it was picked, best first (e.g. "Team leader", "MVP", "Saves leader"). */
    reasons: string[];
};

export type FoilSuggestionResult = {
    /** Foils the edition should end up with (about 15%), existing FOIL tags included. */
    target: number;
    existing_count: number;
    suggestions: FoilSuggestion[];
};

/** Cards to tag FOIL, picked from the edition's saved cards. Doesn't persist — apply them as tags. */
export async function suggestEditionFoils(releaseId: string, editionId: string, setType: FoilSetType, token: string): Promise<FoilSuggestionResult> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}/foils/suggest`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ set_type: setType }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to suggest foils: ${res.status}`);
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

/** The release card snapshot of one of the user's Custom Card Builder cards (date ranges,
 * multi-year cards, etc.), with the full card embedded. Doesn't persist — save the returned
 * snapshot through `updateEdition`. */
export async function customEditionCard(releaseId: string, editionId: string, customCardId: string, token: string): Promise<CardDatabaseRecord> {
    const res = await fetch(`${API_BASE}/releases/${releaseId}/editions/${editionId}/cards/custom`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ custom_card_id: customCardId }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Failed to add custom card: ${res.status}`);
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
