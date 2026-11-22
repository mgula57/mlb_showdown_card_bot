/**
 * Admin-only analytics for the `/admin` dashboard. Every route is gated server-side by the admin
 * allowlist (`require_admin`); the page only shows itself when `useAuth().isAdmin` is true.
 * Queries live in `mlb_showdown_bot/core/database/admin_metrics.py`.
 */

const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:5000/api';

/** Supported reporting windows, in days. */
export const ADMIN_PERIODS = [7, 30, 90, 365] as const;
export type AdminPeriod = typeof ADMIN_PERIODS[number];

export type FeatureArea = 'Site' | 'Cards' | 'Release Builder' | 'Teams & Sims' | 'Community';

/** A label and its count, for a ranked list. */
export type CountBucket = { label: string; count: number };

// ---------------------------------------------------------------------------
// MARK: Overview
// ---------------------------------------------------------------------------

export type OverviewFeature = {
    key: string;
    label: string;
    area: FeatureArea;
    actions?: number;
    previous_actions?: number;
    users?: number;
    previous_users?: number;
    anonymous_actions?: number;
};

/** Visitor numbers from `internal.log_event`, which only covers the time since event logging shipped. */
export type AdminVisitors = {
    totals: {
        visitors: number; previous_visitors: number; signed_in_visitors: number;
        sessions: number; previous_sessions: number;
        sign_ins: number; previous_sign_ins: number;
        page_views: number;
        tracked_since: string | null;
    };
    daily: { date: string; visitors: number; sessions: number; sign_ins: number }[];
    /** Page views by top-level path ("/customs"), with distinct visitors. */
    sections: (CountBucket & { visitors: number })[];
    referrers: CountBucket[];
    devices: CountBucket[];
    campaigns: CountBucket[];
};

export type AdminOverview = {
    days: number;
    visitors: AdminVisitors;
    builds: {
        builds: number; previous_builds: number;
        failed: number; previous_failed: number;
        anonymous_builds: number; previous_anonymous_builds: number;
        signed_in_builders: number; previous_signed_in_builders: number;
    };
    accounts: {
        total_accounts: number;
        signups: number; previous_signups: number;
        /** Accounts whose latest sign-in falls in the period (Supabase keeps no sign-in history). */
        signed_in: number;
        active_accounts: number; previous_active_accounts: number;
    };
    daily: { date: string; builds: number; failed: number; anonymous_builds: number; signups: number; active_accounts: number }[];
    features: OverviewFeature[];
};

// ---------------------------------------------------------------------------
// MARK: Builder failures
// ---------------------------------------------------------------------------

export type FailureGroup = {
    signature: string;
    count: number;
    users: number;
    anonymous: number;
    first_seen: string;
    last_seen: string;
    versions: string[];
    sample_error: string | null;
    sample_error_for_user: string | null;
    /** Failures where the user saw the raw exception text rather than a written message. */
    shown_raw: number;
    sample_ids: number[];
    /** Exception classes and the build stage each failure was in (recorded since phase 2 logging). */
    error_types: string[];
    stages: Record<string, number>;
    /** Latest traceback for this group, if recorded. */
    sample_detail: string | null;
};

export type FailureBucket = { label: string; count: number; failed: number; failure_rate: number };

export type FailedBuild = {
    id: number;
    created_on: string;
    error: string | null;
    error_for_user: string | null;
    user_id: string | null;
    email: string | null;
    version: string | null;
    name: string | null;
    year: string | null;
    set: string | null;
    period: string | null;
    data_source: string | null;
    error_type: string | null;
    error_stage: string | null;
    generation_source: string | null;
    request_duration: number | null;
};

export type FailureDimension = 'set' | 'period' | 'data_source' | 'version' | 'year_bucket' | 'generation_source';

/** A build the browser reported as never getting a response. */
export type ClientBuildError = { created_at: string; message: string | null; generation_source: string | null; user_id: string | null; email: string | null };

export type AdminFailures = {
    days: number;
    totals: { builds: number; failed: number; shown_raw: number; signatures: number; client_errors: number };
    daily: { date: string; builds: number; failed: number }[];
    groups: FailureGroup[];
    by_stage: CountBucket[];
    by_type: CountBucket[];
    client_errors: ClientBuildError[];
    breakdowns: Record<FailureDimension, FailureBucket[]>;
    recent: FailedBuild[];
};

// ---------------------------------------------------------------------------
// MARK: Card trends
// ---------------------------------------------------------------------------

export type TrendDimension =
    | 'set' | 'expansion' | 'edition' | 'image_parallel' | 'period' | 'chart_version'
    | 'stat_normalizer' | 'image_source' | 'era' | 'data_source' | 'league' | 'year_bucket' | 'generation_source';

export type TrendBucket = { label: string; count: number; users: number };

export type AdminCardTrends = {
    days: number;
    flags: {
        builds: number; shuffles: number; dark_mode: number; hide_team_logo: number;
        bordered: number; own_image: number; variable_speed: number;
    };
    breakdowns: Record<TrendDimension, TrendBucket[]>;
    top_players: { bref_id: string; name: string; count: number; users: number; shuffles: number }[];
    daily_by_set: { date: string; set: string | null; count: number }[];
};

// ---------------------------------------------------------------------------
// MARK: Users
// ---------------------------------------------------------------------------

export type AdminUserRow = {
    user_id: string;
    email: string | null;
    username: string | null;
    provider: string | null;
    created_at: string;
    last_sign_in_at: string | null;
    actions: number;
    builds: number;
    features_used: number;
    last_active_at: string | null;
};

export type AdminUsers = { days: number; users: AdminUserRow[] };

export type AdminUserDetail = {
    days: number;
    profile: {
        user_id: string; email: string | null; username: string | null; avatar_url: string | null;
        provider: string | null; created_at: string; last_sign_in_at: string | null;
    };
    features: { key: string; label: string; area: FeatureArea; all_time: number; period: number; first_at: string | null; last_at: string | null }[];
    daily: { date: string; actions: number }[];
    timeline: { feature: string; at: string; detail: string | null; action: string; area: FeatureArea }[];
    recent_builds: {
        id: number; created_on: string; name: string | null; year: string | null; set: string | null;
        expansion: string | null; edition: string | null; image_parallel: string | null; period: string | null;
        error: string | null; error_for_user: string | null;
    }[];
};

// ---------------------------------------------------------------------------
// MARK: Fetch
// ---------------------------------------------------------------------------

/** Each dashboard view and the payload its route returns. */
export type AdminMetricsViews = {
    'overview': AdminOverview;
    'failures': AdminFailures;
    'card-trends': AdminCardTrends;
    'users': AdminUsers;
};

export type AdminMetricsPath = keyof AdminMetricsViews | `users/${string}`;

export async function fetchAdminMetrics<T>(path: AdminMetricsPath, token: string, days: AdminPeriod, refresh = false): Promise<T> {
    const params = new URLSearchParams({ days: String(days) });
    if (refresh) params.set('refresh', '1');
    const res = await fetch(`${API_BASE}/admin/metrics/${path}?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Couldn't load admin metrics (${res.status})`);
    }
    return res.json();
}
