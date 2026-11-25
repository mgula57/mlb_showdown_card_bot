import { useEffect, useRef } from 'react';
import type { CommentSubject } from '../../../api/comments';

/**
 * Asks a page to open its comments once it shows a subject (a notification about a comment does this
 * before navigating). Kept outside the router's location state because pages rewrite their URL as they
 * load (the Release Builder adds the edition slug), which drops that state. A request that no page
 * picks up soon after is ignored, so it can't open comments on a later visit.
 */

const REQUEST_TTL_MS = 30_000;

let pending: { key: string; at: number } | null = null;
const listeners = new Set<() => void>();

const subjectKey = (subject: CommentSubject) => `${subject.type}:${subject.id}`;

export function requestOpenComments(subject: CommentSubject): void {
    pending = { key: subjectKey(subject), at: Date.now() };
    listeners.forEach(listener => listener());
}

/** Calls `open` when comments on `subject` are requested while `enabled` (the page shows it and it takes
 *  comments), including a request made just before the page mounted. */
export function useOpenRequestedComments(subject: CommentSubject, enabled: boolean, open: () => void): void {
    const key = subjectKey(subject);
    const openRef = useRef(open);
    useEffect(() => { openRef.current = open; }, [open]);

    useEffect(() => {
        if (!enabled) return;
        const check = () => {
            if (pending?.key !== key) return;
            const isFresh = Date.now() - pending.at < REQUEST_TTL_MS;
            pending = null;
            if (isFresh) openRef.current();
        };
        check();
        listeners.add(check);
        return () => { listeners.delete(check); };
    }, [enabled, key]);
}
