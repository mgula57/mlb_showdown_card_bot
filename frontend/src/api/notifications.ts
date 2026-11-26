import { authHeaders, request, withCursor } from "./http";

// =============================================================================
// MARK: - TYPES
// =============================================================================

/** What happened (`NotificationKind` in core/notifications/notifier.py). */
export type NotificationKind =
    | 'comment_reply' | 'subject_comment' | 'release_remix'
    | 'league_join' | 'league_draft_start' | 'league_on_the_clock' | 'league_removed'
    | 'league_regular_season_end' | 'league_season_complete'
    | 'live_game_accepted' | 'live_game_final'
    | 'lobby_join' | 'lobby_start' | 'lobby_finished';

/** What a notification is about (`_NOTIFICATION_SUBJECTS` in postgres_db.py). */
export type NotificationSubjectType = 'release' | 'team' | 'league' | 'live_game' | 'sim_lobby';

export type AppNotification = {
    id: string;
    kind: NotificationKind;
    subject_type: NotificationSubjectType;
    subject_id: string;
    /** The release, team, league, game ("Away @ Home") or lobby's name. */
    subject_name: string | null;
    /** The comment it's about, for comment kinds. */
    comment_id: string | null;
    /** The start of that comment. */
    comment_excerpt: string | null;
    created_at: string;
    read_at: string | null;
    /** Who did it; null when a sim did (a season ending, a lobby finishing). */
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

/** What a user can turn off (`NotificationGroup` on the server). Everything is on until turned off. */
export type NotificationGroup = 'comments' | 'remixes' | 'leagues' | 'games' | 'lobbies';

/** `{group: false}` for each group turned off. */
export type NotificationPrefs = Partial<Record<NotificationGroup, boolean>>;

/** The groups as the Account page lists them. */
export const NOTIFICATION_GROUPS: { group: NotificationGroup; label: string; description: string }[] = [
    { group: 'comments', label: 'Comments', description: 'Replies to your comments, and comments on your releases and teams' },
    { group: 'remixes', label: 'Remixes', description: 'Someone remixes one of your releases' },
    { group: 'leagues', label: 'Leagues', description: 'Joins, drafts, your pick, and seasons ending' },
    { group: 'games', label: 'Live games', description: 'Your invite is accepted, or a game you play in is final' },
    { group: 'lobbies', label: 'Sim lobbies', description: 'Joins to your lobby, and lobby seasons starting and finishing' },
];

/** The Realtime event that pings a user's channel when they get a notification (`notifications_changed` on the server). */
export const NOTIFICATIONS_EVENT = 'notifications_changed';

/** Where a notification leads: the thing it's about (the league list once you've been removed from one). */
export function notificationPath(notification: AppNotification): string {
    const id = notification.subject_id;
    switch (notification.subject_type) {
        case 'release': return `/release-builder/${id}`;
        case 'team': return `/teams/${id}`;
        case 'league': return notification.kind === 'league_removed' ? '/leagues' : `/leagues/${id}`;
        case 'live_game': return `/teams/live/${id}`;
        case 'sim_lobby': return `/simulate/lobby/${id}`;
    }
}

// =============================================================================
// MARK: - REQUESTS
// =============================================================================

/** A page of the signed-in user's notifications, newest first, with their unread count. */
export function fetchNotifications(token: string, cursor?: string | null): Promise<NotificationPage> {
    return request(withCursor('/notifications', cursor), { headers: authHeaders(token) }, "Couldn't load notifications.");
}

/** The unread count, and the Realtime topic that pings when it changes (null when the server only supports polling). */
export function fetchUnreadNotificationCount(token: string): Promise<{ unread_count: number; realtime_topic: string | null }> {
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
