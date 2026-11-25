import { useCallback, useEffect, useRef, useState } from 'react';
import {
    fetchNotifications, fetchUnreadNotificationCount, markNotificationsRead, type AppNotification,
} from '../../api/notifications';

/** How often the unread count refreshes while the tab is showing. */
const POLL_INTERVAL_MS = 60_000;

/**
 * The signed-in user's notifications: the unread count, polled while the tab is visible (and on coming
 * back to it), and the list, loaded each time `isOpen` turns on. Marking read is optimistic.
 */
export function useNotifications(token: string | undefined, isOpen: boolean) {
    const [unreadCount, setUnreadCount] = useState(0);
    const [notifications, setNotifications] = useState<AppNotification[]>([]);
    const [nextCursor, setNextCursor] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [loadingMore, setLoadingMore] = useState(false);
    const [error, setError] = useState<string | null>(null);
    // Ignores answers for a token that's no longer current (signed out, or another account)
    const tokenRef = useRef(token);
    useEffect(() => { tokenRef.current = token; }, [token]);

    const refreshCount = useCallback(async () => {
        if (!token || document.visibilityState !== 'visible') return;
        try {
            const { unread_count } = await fetchUnreadNotificationCount(token);
            if (tokenRef.current === token) setUnreadCount(unread_count);
        } catch {
            // The bell keeps its last count; the next poll tries again
        }
    }, [token]);

    useEffect(() => {
        if (!token) {
            setUnreadCount(0);
            setNotifications([]);
            setNextCursor(null);
            return;
        }
        refreshCount();
        const interval = window.setInterval(refreshCount, POLL_INTERVAL_MS);
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
