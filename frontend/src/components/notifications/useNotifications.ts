import { useCallback, useEffect, useRef, useState } from 'react';
import {
    NOTIFICATIONS_EVENT, fetchNotifications, fetchUnreadNotificationCount, markNotificationsRead, type AppNotification,
} from '../../api/notifications';
import { useRealtimeRefresh } from '../../hooks/useRealtimeRefresh';

/** How often the unread count refreshes while the tab is showing: often without Realtime, rarely as a backstop with it. */
const POLL_INTERVAL_MS = 60_000;
const REALTIME_POLL_INTERVAL_MS = 5 * 60_000;

/**
 * The signed-in user's notifications: the unread count, refreshed on each Realtime ping (when the server
 * has a channel for this user), polled while the tab is visible and on coming back to it, and the list,
 * loaded each time `isOpen` turns on (and on a ping while it's open). Marking read is optimistic.
 */
export function useNotifications(token: string | undefined, isOpen: boolean) {
    const [unreadCount, setUnreadCount] = useState(0);
    const [notifications, setNotifications] = useState<AppNotification[]>([]);
    const [nextCursor, setNextCursor] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [loadingMore, setLoadingMore] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [realtimeTopic, setRealtimeTopic] = useState<string | null>(null);
    // Ignores answers for a token that's no longer current (signed out, or another account)
    const tokenRef = useRef(token);
    useEffect(() => { tokenRef.current = token; }, [token]);

    const refreshCount = useCallback(async () => {
        if (!token || document.visibilityState !== 'visible') return;
        try {
            const { unread_count, realtime_topic } = await fetchUnreadNotificationCount(token);
            if (tokenRef.current !== token) return;
            setUnreadCount(unread_count);
            setRealtimeTopic(realtime_topic);
        } catch {
            // The bell keeps its last count; the next poll tries again
        }
    }, [token]);

    // Keeps the poll's effect from restarting (and refetching) when Realtime connects or drops
    const isConnectedRef = useRef(false);

    useEffect(() => {
        if (!token) {
            setUnreadCount(0);
            setNotifications([]);
            setNextCursor(null);
            setRealtimeTopic(null);
            return;
        }
        refreshCount();
        let lastPoll = Date.now();
        // Ticks every minute, but waits out the longer interval while Realtime is connected
        const interval = window.setInterval(() => {
            const wait = isConnectedRef.current ? REALTIME_POLL_INTERVAL_MS : POLL_INTERVAL_MS;
            if (Date.now() - lastPoll < wait) return;
            lastPoll = Date.now();
            refreshCount();
        }, POLL_INTERVAL_MS);
        document.addEventListener('visibilitychange', refreshCount);
        return () => {
            window.clearInterval(interval);
            document.removeEventListener('visibilitychange', refreshCount);
        };
    }, [token, refreshCount]);

    const load = useCallback(async () => {
        if (!token) return;
        setLoading(true);
        setError(null);
        try {
            const page = await fetchNotifications(token);
            if (tokenRef.current !== token) return;
            setNotifications(page.notifications);
            setNextCursor(page.next_cursor);
            setUnreadCount(page.unread_count);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Couldn't load notifications.");
        } finally {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => {
        if (isOpen) load();
    }, [isOpen, load]);

    const isOpenRef = useRef(isOpen);
    useEffect(() => { isOpenRef.current = isOpen; }, [isOpen]);
    const isConnected = useRealtimeRefresh(token ? realtimeTopic : null, NOTIFICATIONS_EVENT, () => {
        if (isOpenRef.current) load();
        else refreshCount();
    });
    useEffect(() => { isConnectedRef.current = isConnected; }, [isConnected]);

    const loadMore = useCallback(async () => {
        if (!token || !nextCursor) return;
        setLoadingMore(true);
        try {
            const page = await fetchNotifications(token, nextCursor);
            if (tokenRef.current !== token) return;
            setNotifications(current => [...current, ...page.notifications]);
            setNextCursor(page.next_cursor);
            setUnreadCount(page.unread_count);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Couldn't load notifications.");
        } finally {
            setLoadingMore(false);
        }
    }, [token, nextCursor]);

    const markRead = useCallback(async (ids?: string[]) => {
        if (!token) return;
        const now = new Date().toISOString();
        const isTarget = (n: AppNotification) => !n.read_at && (!ids || ids.includes(n.id));
        const newlyRead = notifications.filter(isTarget).length;
        if (ids && newlyRead === 0) return;
        setNotifications(current => current.map(n => isTarget(n) ? { ...n, read_at: now } : n));
        setUnreadCount(count => ids ? Math.max(0, count - newlyRead) : 0);
        try {
            const { unread_count } = await markNotificationsRead(token, ids);
            if (tokenRef.current === token) setUnreadCount(unread_count);
        } catch {
            // Shown read here either way; the next poll brings back the server's count
        }
    }, [token, notifications]);

    return {
        unreadCount, notifications, hasMore: !!nextCursor, loading, loadingMore, error,
        retry: load, loadMore, markRead,
    };
}
