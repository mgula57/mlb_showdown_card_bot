/**
 * Product events (`POST /api/events` → `internal.log_event`). Call `track(event, properties)`;
 * events are queued and sent in small batches, and flushed when the tab is hidden so the last
 * page view isn't lost. The server keeps only the events and property keys it lists in
 * `ClientEventSchema` (mlb_showdown_bot/api/events.py), so add a new event there too.
 *
 * Nothing is sent when the browser asks not to be tracked (see `isTrackingDisabled`).
 */
import { supabase } from '../api/supabase';
import { clientIdHeaders, consumeNewSession, isTrackingDisabled } from './clientIds';

const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:5000/api';
const FLUSH_DELAY_MS = 2000;
const MAX_BATCH = 20;

type Scalar = string | number | boolean | null | undefined;

/** Each event and the properties it carries. Keep in sync with `ClientEventSchema.EVENTS`. */
export type TrackedEvents = {
    page_view: Record<string, never>;
    session_start: {
        referrer_host?: string; utm_source?: string; utm_medium?: string; utm_campaign?: string;
        device: 'mobile' | 'tablet' | 'desktop'; standalone: boolean; screen_width: number;
    };
    sign_in: { provider?: string };
    open_in_builder: { set?: string; is_wotc?: boolean };
    builder_client_error: { message: string; status?: number; generation_source?: string };
    release_zip_download: { card_count: number };
};

type QueuedEvent = { event: keyof TrackedEvents; route: string; properties?: Record<string, Scalar> };

let queue: QueuedEvent[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;

function sessionStartProperties(): TrackedEvents['session_start'] {
    const params = new URLSearchParams(window.location.search);
    let referrerHost: string | undefined;
    try {
        const host = document.referrer ? new URL(document.referrer).hostname : '';
        referrerHost = host && host !== window.location.hostname ? host : undefined;
    } catch {
        referrerHost = undefined;
    }
    const width = window.innerWidth;
    return {
        referrer_host: referrerHost,
        utm_source: params.get('utm_source') ?? undefined,
        utm_medium: params.get('utm_medium') ?? undefined,
        utm_campaign: params.get('utm_campaign') ?? undefined,
        device: width < 640 ? 'mobile' : width < 1024 ? 'tablet' : 'desktop',
        standalone: window.matchMedia?.('(display-mode: standalone)').matches ?? false,
        screen_width: width,
    };
}

async function flush(keepalive = false) {
    if (flushTimer) {
        clearTimeout(flushTimer);
        flushTimer = null;
    }
    if (!queue.length) return;
    const events = queue.slice(0, MAX_BATCH);
    queue = queue.slice(MAX_BATCH);
    if (queue.length) scheduleFlush();

    let token: string | undefined;
    try {
        token = (await supabase.auth.getSession()).data.session?.access_token;
    } catch {
        token = undefined;
    }
    try {
        await fetch(`${API_BASE}/events`, {
            method: 'POST',
            keepalive,
            headers: {
                'Content-Type': 'application/json',
                ...clientIdHeaders(),
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ events }),
        });
    } catch {
        // Analytics never interrupts the app; a lost batch is fine
    }
}

function scheduleFlush() {
    if (!flushTimer) flushTimer = setTimeout(() => { void flush(); }, FLUSH_DELAY_MS);
}

/** Record a product event. `route` defaults to the current path. */
export function track<E extends keyof TrackedEvents>(event: E, properties?: TrackedEvents[E], route: string = window.location.pathname) {
    if (isTrackingDisabled()) return;
    if (consumeNewSession()) {
        queue.push({ event: 'session_start', route, properties: sessionStartProperties() });
    }
    queue.push({ event, route, properties: properties as Record<string, Scalar> | undefined });
    if (queue.length >= MAX_BATCH) void flush();
    else scheduleFlush();
}

/** Record a sign-in once per tab session per account. Supabase repeats `SIGNED_IN` when a tab
 *  regains focus or refreshes its session, so the event alone overcounts. */
export function trackSignIn(userId: string, provider?: string) {
    const key = `showdown.signInTracked.${userId}`;
    try {
        if (sessionStorage.getItem(key)) return;
        sessionStorage.setItem(key, '1');
    } catch {
        // Storage blocked: record it anyway
    }
    track('sign_in', { provider });
}

// Send what's queued when the tab is hidden or closed, while the page can still make requests
if (typeof window !== 'undefined') {
    window.addEventListener('pagehide', () => { void flush(true); });
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') void flush(true);
    });
}
