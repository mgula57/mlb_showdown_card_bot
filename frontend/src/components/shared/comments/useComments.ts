import { useCallback, useEffect, useRef, useState } from 'react';
import {
    deleteComment, fetchCommentReplies, fetchComments, postComment,
    type Comment, type CommentSubject, type CommentThread,
} from '../../../api/comments';

export type CommentsState = {
    /** Null until the first page loads. */
    threads: CommentThread[] | null;
    enabled: boolean;
    total: number;
    error: string | null;
    hasMore: boolean;
    loadingMore: boolean;
    /** Thread ids whose remaining replies are loading. */
    loadingReplies: ReadonlySet<string>;
    retry: () => void;
    loadMore: () => void;
    loadReplies: (threadId: string) => void;
    /** Throws on failure, so the composer can keep the text and show why. */
    post: (body: string, replyTo?: Comment) => Promise<void>;
    remove: (comment: Comment) => Promise<void>;
};

/** One subject's comments: pages of threads, the rest of a thread on demand, and posting and deleting in
 *  place. Loads while `active` (e.g. the panel is open) and keeps what it loaded after. `onTotalChange`
 *  reports the live count so a button elsewhere can show it. */
export function useComments(subject: CommentSubject, token: string | undefined, active: boolean, onTotalChange?: (total: number) => void): CommentsState {
    const [threads, setThreads] = useState<CommentThread[] | null>(null);
    const [enabled, setEnabled] = useState(true);
    const [total, setTotal] = useState(0);
    const [nextCursor, setNextCursor] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loadingMore, setLoadingMore] = useState(false);
    const [loadingReplies, setLoadingReplies] = useState<ReadonlySet<string>>(new Set());
    const [reloadKey, setReloadKey] = useState(0);
    const subjectKey = `${subject.type}:${subject.id}`;

    const onTotalChangeRef = useRef(onTotalChange);
    useEffect(() => { onTotalChangeRef.current = onTotalChange; });
    // Mirrored in a ref so the change can be reported outside a state updater (which runs during render)
    const totalRef = useRef(0);
    const changeTotal = useCallback((update: (total: number) => number) => {
        const next = Math.max(0, update(totalRef.current));
        totalRef.current = next;
        setTotal(next);
        onTotalChangeRef.current?.(next);
    }, []);

    // A new subject starts over
    const [loadedKey, setLoadedKey] = useState(subjectKey);
    if (loadedKey !== subjectKey) {
        setLoadedKey(subjectKey);
        setThreads(null);
        setNextCursor(null);
        setError(null);
    }

    const isLoaded = threads !== null;
    useEffect(() => {
        if (!active || isLoaded) return;
        let cancelled = false;
        setError(null);
        fetchComments(subject, token)
            .then(page => {
                if (cancelled) return;
                setThreads(page.comments);
                setEnabled(page.enabled);
                setNextCursor(page.next_cursor);
                changeTotal(() => page.total);
            })
            .catch(err => { if (!cancelled) setError(err instanceof Error ? err.message : "Couldn't load comments."); });
        return () => { cancelled = true; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [active, isLoaded, subjectKey, token, reloadKey]);

    const loadMore = useCallback(() => {
        if (!nextCursor || loadingMore) return;
        setLoadingMore(true);
        fetchComments(subject, token, nextCursor)
            .then(page => {
                // A thread posted since the first page can come back again; keep the one already shown
                setThreads(prev => {
                    const seen = new Set((prev ?? []).map(t => t.id));
                    return [...(prev ?? []), ...page.comments.filter(t => !seen.has(t.id))];
                });
                setNextCursor(page.next_cursor);
            })
            .catch(err => setError(err instanceof Error ? err.message : "Couldn't load more comments."))
            .finally(() => setLoadingMore(false));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [nextCursor, loadingMore, subjectKey, token]);

    const loadReplies = useCallback((threadId: string) => {
        const thread = threads?.find(t => t.id === threadId);
        if (!thread || loadingReplies.has(threadId)) return;
        const last = thread.replies[thread.replies.length - 1];
        setLoadingReplies(prev => new Set(prev).add(threadId));
        // Pages through until the thread is all there: threads are short, and it's one tap
        (async () => {
            let cursor: string | null = last ? `${last.created_at}|${last.id}` : null;
            const more: Comment[] = [];
            do {
                const page = await fetchCommentReplies(threadId, token, cursor);
                more.push(...page.replies);
                cursor = page.next_cursor;
            } while (cursor);
            setThreads(prev => prev?.map(t => {
                if (t.id !== threadId) return t;
                const seen = new Set(t.replies.map(r => r.id));
                return { ...t, replies: [...t.replies, ...more.filter(r => !seen.has(r.id))] };
            }) ?? prev);
        })()
            .catch(err => setError(err instanceof Error ? err.message : "Couldn't load replies."))
            .finally(() => setLoadingReplies(prev => {
                const next = new Set(prev);
                next.delete(threadId);
                return next;
            }));
    }, [threads, loadingReplies, token]);

    const post = useCallback(async (body: string, replyTo?: Comment) => {
        if (!token) throw new Error('Sign in to comment.');
        const created = await postComment(subject, body, token, replyTo?.id);
        setThreads(prev => {
            if (!prev) return prev;
            if (!created.parent_id) return [created, ...prev];
            return prev.map(t => t.id === created.parent_id
                ? { ...t, reply_count: t.reply_count + 1, replies: [...t.replies, created] }
                : t);
        });
        changeTotal(n => n + 1);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [subjectKey, token, changeTotal]);

    const remove = useCallback(async (comment: Comment) => {
        if (!token) return;
        await deleteComment(comment.id, token);
        setThreads(prev => {
            if (!prev) return prev;
            if (comment.parent_id) {
                return prev
                    .map(t => t.id === comment.parent_id
                        ? { ...t, reply_count: t.reply_count - 1, replies: t.replies.filter(r => r.id !== comment.id) }
                        : t)
                    // A placeholder goes once its last reply does
                    .filter(t => !(t.is_deleted && t.reply_count === 0));
            }
            return prev.flatMap(t => {
                if (t.id !== comment.id) return [t];
                // Kept as a placeholder while it has replies, as the server does
                return t.reply_count > 0 ? [{ ...t, is_deleted: true, body: null, user_id: null, username: null, avatar_url: null }] : [];
            });
        });
        changeTotal(n => n - 1);
    }, [token, changeTotal]);

    return {
        threads, enabled, total, error,
        hasMore: !!nextCursor,
        loadingMore, loadingReplies,
        retry: () => { setThreads(null); setReloadKey(k => k + 1); },
        loadMore, loadReplies, post, remove,
    };
}
