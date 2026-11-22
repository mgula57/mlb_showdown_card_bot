/**
 * Visitor ids sent with logged requests and events (see `ClientContext` on the server):
 * - anon id: random, kept in localStorage, so repeat visits from this browser count as one visitor
 *   and activity before signing in can be tied to the account afterwards.
 * - session id: random, kept in sessionStorage, so it lasts as long as this tab.
 *
 * Neither is sent when the browser asks not to be tracked (Global Privacy Control or Do Not
 * Track). Storage can be blocked (private windows, cleared site data), so every access is guarded
 * and ids fall back to this page load.
 */

const ANON_ID_KEY = 'showdown.anonId';
const SESSION_ID_KEY = 'showdown.sessionId';

const memoryIds: Record<string, string> = {};
let sessionIsNew = false;

function readOrCreate(storage: () => Storage, key: string, onCreate?: () => void): string {
    try {
        const existing = storage().getItem(key);
        if (existing) return existing;
        const created = crypto.randomUUID();
        storage().setItem(key, created);
        onCreate?.();
        return created;
    } catch {
        if (!memoryIds[key]) {
            memoryIds[key] = crypto.randomUUID();
            onCreate?.();
        }
        return memoryIds[key];
    }
}

/** True when the browser has asked sites not to track it. */
export function isTrackingDisabled(): boolean {
    const nav = navigator as Navigator & { globalPrivacyControl?: boolean };
    return nav.globalPrivacyControl === true || nav.doNotTrack === '1';
}

export const getAnonId = (): string => readOrCreate(() => localStorage, ANON_ID_KEY);

export const getSessionId = (): string => readOrCreate(() => sessionStorage, SESSION_ID_KEY, () => { sessionIsNew = true; });

/** True once, for the first caller after this tab's session id was created. */
export function consumeNewSession(): boolean {
    getSessionId();
    const isNew = sessionIsNew;
    sessionIsNew = false;
    return isNew;
}

/** Headers for requests the server logs (card builds, searches, card opens). Empty when tracking is disabled. */
export function clientIdHeaders(): Record<string, string> {
    if (isTrackingDisabled()) return {};
    return {
        'X-Showdown-Anon-Id': getAnonId(),
        'X-Showdown-Session-Id': getSessionId(),
    };
}
