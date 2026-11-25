import type { CommentSubjectType } from "./comments";
import { authHeaders, request, withCursor } from "./http";

// =============================================================================
// MARK: - TYPES
// =============================================================================

/** What happened (`NotificationKind` in core/notifications/notifier.py). */
export type NotificationKind = 'comment_reply' | 'subject_comment' | 'release_remix';

export type AppNotification = {
    id: string;
    kind: NotificationKind;
    subject_type: CommentSubjectType;
    subject_id: string;
    /** The release or team's name. */
    subject_name: string;
    /** The comment it's about, for comment kinds. */
    comment_id: string | null;
    /** The start of that comment. */
    comment_excerpt: string | null;
    created_at: string;
    read_at: string | null;
    actor_id: string | null;
    actor_username: string | null;
    actor_avatar_url: string | null;
    actor_primary_color: string | null;
};

export type NotificationPage = {
    notifications: AppNotification[];
    /** Pass back as `cursor` for the next page, or null at the end. */
    next_cursor: string | null;
    unread_count: number;
};

/** Where a notification leads: the release or team it's about. */
export function notificationPath(notification: AppNotification): string {
    return notification.subject_type === 'release'
        ? `/release-builder/${notification.subject_id}`
        : `/teams/${notification.subject_id}`;
}

// =============================================================================
// MARK: - REQUESTS
// =============================================================================

/** A page of the signed-in user's notifications, newest first, with their unread count. */
export function fetchNotifications(token: string, cursor?: string | null): Promise<NotificationPage> {
    return request(withCursor('/notifications', cursor), { headers: authHeaders(token) }, "Couldn't load notifications.");
}

export function fetchUnreadNotificationCount(token: string): Promise<{ unread_count: number }> {
    return request('/notifications/unread_count', { headers: authHeaders(token) }, "Couldn't load notifications.");
}

/** Marks the given notifications read, or all of them without `ids`. Returns the new unread count. */
export function markNotificationsRead(token: string, ids?: string[]): Promise<{ unread_count: number }> {
    return request('/notifications/read', {
        method: 'POST',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify(ids ? { ids } : {}),
    }, "Couldn't mark notifications read.");
}
