import { useEffect, useRef } from 'react';
import { fetchDraft, leagueDraftTopic, DRAFT_CHANGED_EVENT, type DraftPayload } from '../api/leagues';
import { usePageVisible } from './usePageVisible';
import { usePolling } from './usePolling';
import { useRealtimeRefresh } from './useRealtimeRefresh';

// REALTIME PINGS DRIVE UPDATES; THE POLL IS ONLY A BACKSTOP, FAST WHILE THE CHANNEL IS DOWN
const BACKSTOP_POLL_MS = 20000;
const DISCONNECTED_POLL_MS = 3000;

/**
 * A season's draft board, refetched on each Realtime "draft changed" ping with a slow poll behind
 * it. Nothing loads while `seasonNumber` is null; `live: false` stops refreshing (a finished draft).
 *
 * A hidden tab leaves the channel and stops polling - a draft can run for days, and a background
 * tab shouldn't hold a connection or poll that whole time. Coming back rejoins, and the rejoin
 * refetches the board.
 */
export function useLeagueDraft(token: string, leagueId: string, seasonNumber: number | null, live = true) {
    const isPageVisible = usePageVisible();
    const isLive = live && seasonNumber !== null && isPageVisible;
    const refreshRef = useRef<() => void>(() => {});
    const isConnected = useRealtimeRefresh(
        isLive ? leagueDraftTopic(leagueId, seasonNumber) : null,
        DRAFT_CHANGED_EVENT,
        () => refreshRef.current(),
    );
    const polling = usePolling<DraftPayload | null>(
        () => (seasonNumber === null ? Promise.resolve(null) : fetchDraft(token, leagueId, seasonNumber)),
        !isLive ? null : isConnected ? BACKSTOP_POLL_MS : DISCONNECTED_POLL_MS,
        [leagueId, seasonNumber],
    );
    const { refresh } = polling;
    useEffect(() => {
        refreshRef.current = refresh;
    }, [refresh]);
    return polling;
}
