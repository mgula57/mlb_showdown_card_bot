/** Shared fetch helpers for the typed `/api` wrappers. */

export const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

/** Fetches `path` and parses its JSON, throwing the server's `error` (or `failure`) when it isn't ok. */
export async function request<T>(path: string, init: RequestInit, failure: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, init);
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `${failure} (${res.status})`);
    }
    return res.json();
}

export function authHeaders(token?: string): Record<string, string> {
    return token ? { Authorization: `Bearer ${token}` } : {};
}

/** `path` with a page's `next_cursor` as `?cursor=`. */
export function withCursor(path: string, cursor?: string | null): string {
    return cursor ? `${path}?cursor=${encodeURIComponent(cursor)}` : path;
}
