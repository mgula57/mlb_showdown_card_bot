import { useState, type ReactNode } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import type { Comment } from '../../../api/comments';
import { formatShortDate, relativeTime } from '../../../functions/formatters';
import { UserAvatar } from '../UserAvatar';
import { Plate } from '../Plate';
import { InlineError } from '../InlineError';

type CommentItemProps = {
    comment: Comment;
    /** The subject's owner, whose comments get a Creator plate. */
    ownerId?: string | null;
    canDelete: boolean;
    onDelete: (comment: Comment) => Promise<void>;
    /** Without it there's no Reply action (e.g. signed out). */
    onReply?: (comment: Comment) => void;
    /** Replies sit under their thread with a smaller avatar. */
    isReply?: boolean;
    /** The thread's replies and reply field, under the comment's body. */
    children?: ReactNode;
};

const ACTION_CLASS = 'text-[12px] font-semibold text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer disabled:opacity-50';

/** One comment: who wrote it and when, what they said, and Reply / Delete. Delete asks once inline. */
export function CommentItem({ comment, ownerId, canDelete, onDelete, onReply, isReply = false, children }: CommentItemProps) {
    const [confirmingDelete, setConfirmingDelete] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const avatarSize = isReply ? 22 : 28;

    async function handleDelete() {
        setDeleting(true);
        setError(null);
        try {
            await onDelete(comment);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Couldn't delete that comment. Try again.");
            setDeleting(false);
            setConfirmingDelete(false);
        }
    }

    if (comment.is_deleted) {
        return (
            <div className="flex gap-2.5">
                <span aria-hidden style={{ width: avatarSize, height: avatarSize }} className="shrink-0 rounded-full bg-(--background-tertiary)" />
                <div className="flex-1 min-w-0 flex flex-col gap-2">
                    <p className="text-[13px] text-(--text-tertiary) py-1">This comment was deleted.</p>
                    {children}
                </div>
            </div>
        );
    }

    return (
        <div className="flex gap-2.5">
            <UserAvatar name={comment.username} avatarUrl={comment.avatar_url} primaryColor={comment.primary_color} size={avatarSize} className="mt-0.5" />
            <div className="flex-1 min-w-0 flex flex-col gap-1">
                <div className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-[12px]">
                    <span className="font-semibold text-(--text-primary)">{comment.username ?? 'Unknown user'}</span>
                    {ownerId && comment.user_id === ownerId && <Plate variant="outline" size="sm">Creator</Plate>}
                    <span aria-hidden className="text-(--text-tertiary)">·</span>
                    <time dateTime={comment.created_at} title={formatShortDate(comment.created_at)} className="text-(--text-tertiary)">
                        {relativeTime(comment.created_at)}
                    </time>
                </div>
                <p className="text-[13px] text-(--text-primary) whitespace-pre-wrap wrap-break-word leading-snug">
                    {comment.reply_to_username && <span className="font-semibold text-(--showdown-blue)">@{comment.reply_to_username} </span>}
                    {comment.body}
                </p>
                <div className="flex items-center gap-3 min-h-6">
                    {confirmingDelete ? (
                        <>
                            <span className="text-[12px] text-(--text-secondary)">Delete this comment?</span>
                            <button type="button" onClick={handleDelete} disabled={deleting} className={`${ACTION_CLASS} text-(--showdown-red)! flex items-center gap-1`}>
                                {deleting && <FaSpinner className="animate-spin text-[10px]" />}
                                Delete
                            </button>
                            <button type="button" onClick={() => setConfirmingDelete(false)} disabled={deleting} className={ACTION_CLASS}>Cancel</button>
                        </>
                    ) : (
                        <>
                            {onReply && <button type="button" onClick={() => onReply(comment)} className={ACTION_CLASS}>Reply</button>}
                            {canDelete && <button type="button" onClick={() => setConfirmingDelete(true)} className={ACTION_CLASS}>Delete</button>}
                        </>
                    )}
                </div>
                {error && <InlineError size="sm">{error}</InlineError>}
                {children}
            </div>
        </div>
    );
}

/** A comment-shaped placeholder while a page loads. */
export function CommentSkeleton() {
    return (
        <div className="flex gap-2.5 animate-pulse">
            <span className="w-7 h-7 shrink-0 rounded-full bg-(--background-tertiary)" />
            <div className="flex-1 flex flex-col gap-1.5 pt-0.5">
                <div className="h-3 w-28 rounded-plate bg-(--background-tertiary)" />
                <div className="h-3 w-full rounded-plate bg-(--background-tertiary)" />
                <div className="h-3 w-2/3 rounded-plate bg-(--background-tertiary)" />
            </div>
        </div>
    );
}
