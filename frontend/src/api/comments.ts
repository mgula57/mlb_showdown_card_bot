const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// =============================================================================
// MARK: - TYPES
// =============================================================================

/** What can be commented on (see `COMMENT_SUBJECTS` in api/comments.py). */
export type CommentSubjectType = 'release' | 'team';

export type CommentSubject = { type: CommentSubjectType; id: string };

/** The most a comment can hold (`COMMENT_MAX_LENGTH` on the server). */
export const COMMENT_MAX_LENGTH = 1000;

export type Comment = {
    id: string;
    subject_type: CommentSubjectType;
    subject_id: string;
    /** The thread's top-level comment, on a reply. Replies are one level deep. */
    parent_id: string | null;
    created_at: string;
    edited_at: string | null;
    /** Deleted, but kept as a placeholder because its thread still has replies. Its content is gone. */
    is_deleted: boolean;
    user_id: string | null;
    body: string | null;
    username: string | null;
    avatar_url: string | null;
    primary_color: string | null;
    /** On a reply to a reply: whose reply it answered. */
    reply_to_username: string | null;
};

/** A top-level comment with the start of its thread. */
export type CommentThread = Comment & {
    /** Live replies in the whole thread. */
    reply_count: number;
    /** The first few replies, oldest first. The rest load with `fetchCommentReplies`. */
    replies: Comment[];
};

export type CommentPage = {
    /** False when the subject isn't taking comments (e.g. its owner turned them off). */
    enabled: boolean;
    comments: CommentThread[];
    /** Pass back as `cursor` for the next page, or null at the end. */
    next_cursor: string | null;
    /** Live comments and replies. */
    total: number;
};

// =============================================================================
// MARK: - REQUESTS
// =============================================================================

async function request<T>(path: string, init: RequestInit, failure: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, init);
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `${failure} (${res.status})`);
    }
    return res.json();
}

function authHeaders(token?: string): Record<string, string> {
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function withCursor(path: string, cursor?: string | null): string {
    return cursor ? `${path}?cursor=${encodeURIComponent(cursor)}` : path;
}

/** A page of a subject's comments, newest first. The token lets the owner read theirs while it's private. */
export function fetchComments(subject: CommentSubject, token?: string, cursor?: string | null): Promise<CommentPage> {
    return request(withCursor(`/comments/${subject.type}/${subject.id}`, cursor), { headers: authHeaders(token) }, "Couldn't load comments.");
}

/** The rest of a thread, after the reply `cursor` points at. */
export function fetchCommentReplies(commentId: string, token?: string, cursor?: string | null): Promise<{ replies: Comment[]; next_cursor: string | null }> {
    return request(withCursor(`/comments/replies/${commentId}`, cursor), { headers: authHeaders(token) }, "Couldn't load replies.");
}

/** Posts a comment, or a reply when `parentId` is any comment in a thread. */
export function postComment(subject: CommentSubject, body: string, token: string, parentId?: string): Promise<CommentThread> {
    return request(`/comments/${subject.type}/${subject.id}`, {
        method: 'POST',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ body, parent_id: parentId ?? null }),
    }, "Couldn't post your comment.");
}

export function deleteComment(commentId: string, token: string): Promise<{ deleted: boolean }> {
    return request(`/comments/${commentId}`, { method: 'DELETE', headers: authHeaders(token) }, "Couldn't delete that comment.");
}
