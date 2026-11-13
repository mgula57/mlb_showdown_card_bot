import { useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import type { Comment, CommentSubject, CommentThread } from '../../../api/comments';
import { buttonClass } from '../buttonStyles';
import { EmptyState } from '../EmptyState';
import { InlineError } from '../InlineError';
import { RetryableError } from '../RetryableError';
import { SignInPrompt } from '../SignInPrompt';
import { CommentComposer } from './CommentComposer';
import { CommentItem, CommentSkeleton } from './CommentItem';
import { useComments } from './useComments';

export type CommentsSectionProps = {
    subject: CommentSubject;
    token?: string;
    viewerId?: string;
    /** The subject's owner: their comments get a Creator plate, and they can delete anyone's. */
    ownerId?: string | null;
    /** Admins can delete anyone's comment too. */
    isAdmin?: boolean;
    /** Loads while true, e.g. while its panel is open. Keeps what it loaded after. */
    active?: boolean;
    /** The live comment count, for a button elsewhere that shows it. */
    onTotalChange?: (total: number) => void;
};

/** Any subject's comments: a field for a new one, then threads newest first, each a comment with its
 *  replies (one level deep) oldest first. Works for anything in `CommentSubjectType`. */
export function CommentsSection({ subject, token, viewerId, ownerId, isAdmin = false, active = true, onTotalChange }: CommentsSectionProps) {
    const comments = useComments(subject, token, active, onTotalChange);
    // The thread with an open reply field, and the comment it answers
    const [replyingTo, setReplyingTo] = useState<{ threadId: string; comment: Comment } | null>(null);
    const canModerate = isAdmin || (!!viewerId && viewerId === ownerId);
    const canDelete = (comment: Comment) => !!viewerId && (comment.user_id === viewerId || canModerate);
    const onReply = token ? (threadId: string) => (comment: Comment) => setReplyingTo({ threadId, comment }) : undefined;

    if (comments.threads === null) {
        return comments.error ? (
            <RetryableError onRetry={comments.retry}>{comments.error}</RetryableError>
        ) : (
            <div className="flex flex-col gap-5" aria-label="Loading comments">
                {Array.from({ length: 3 }, (_, i) => <CommentSkeleton key={i} />)}
            </div>
        );
    }

    if (!comments.enabled) {
        return <EmptyState size="inline">Comments are turned off.</EmptyState>;
    }

    function renderThread(thread: CommentThread) {
        const hiddenReplies = thread.reply_count - thread.replies.length;
        const replyField = replyingTo?.threadId === thread.id ? replyingTo : null;
        return (
            <li key={thread.id}>
                <CommentItem
                    comment={thread}
                    ownerId={ownerId}
                    canDelete={canDelete(thread)}
                    onDelete={comments.remove}
                    onReply={onReply?.(thread.id)}
                >
                    {(thread.replies.length > 0 || hiddenReplies > 0 || replyField) && (
                        <div className="flex flex-col gap-3 mt-2 pl-3 border-l border-(--divider)">
                            {thread.replies.map(reply => (
                                <CommentItem
                                    key={reply.id}
                                    comment={reply}
                                    ownerId={ownerId}
                                    canDelete={canDelete(reply)}
                                    onDelete={comments.remove}
                                    onReply={onReply?.(thread.id)}
                                    isReply
                                />
                            ))}
                            {hiddenReplies > 0 && (
                                <button
                                    type="button"
                                    onClick={() => comments.loadReplies(thread.id)}
                                    disabled={comments.loadingReplies.has(thread.id)}
                                    className="self-start flex items-center gap-1.5 text-[12px] font-semibold text-(--showdown-blue) hover:underline cursor-pointer disabled:opacity-50"
                                >
                                    {comments.loadingReplies.has(thread.id) && <FaSpinner className="animate-spin text-[10px]" />}
                                    Show {hiddenReplies} more repl{hiddenReplies === 1 ? 'y' : 'ies'}
                                </button>
                            )}
                            {replyField && (
                                <CommentComposer
                                    key={replyField.comment.id}
                                    placeholder="Write a reply…"
                                    submitLabel="Reply"
                                    context={replyField.comment.username ? `Replying to @${replyField.comment.username}` : undefined}
                                    onSubmit={body => comments.post(body, replyField.comment)}
                                    onCancel={() => setReplyingTo(null)}
                                    autoFocus
                                />
                            )}
                        </div>
                    )}
                </CommentItem>
            </li>
        );
    }

    return (
        <div className="flex flex-col gap-5">
            {token ? (
                <CommentComposer onSubmit={body => comments.post(body)} />
            ) : (
                <SignInPrompt size="panel" title="Join the conversation." message="Sign in to comment and reply." />
            )}

            {comments.threads.length === 0 ? (
                <EmptyState size="panel" title="Be the first.">No comments yet.</EmptyState>
            ) : (
                <ul className="flex flex-col gap-5">
                    {comments.threads.map(renderThread)}
                </ul>
            )}

            {comments.error && <InlineError size="sm">{comments.error}</InlineError>}
            {comments.hasMore && (
                <button type="button" onClick={comments.loadMore} disabled={comments.loadingMore} className={buttonClass('secondary', 'sm', 'self-center')}>
                    {comments.loadingMore && <FaSpinner className="animate-spin text-[11px]" />}
                    Show more comments
                </button>
            )}
        </div>
    );
}
