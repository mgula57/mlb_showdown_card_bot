import { useState } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { FaRegBell, FaSpinner } from 'react-icons/fa6';
import { notificationPath, type AppNotification } from '../../api/notifications';
import { useAuth } from '../auth/AuthContext';
import { buttonClass } from '../shared/buttonStyles';
import { CornerCount } from '../shared/CornerCount';
import { EmptyState } from '../shared/EmptyState';
import { InlineError } from '../shared/InlineError';
import { RetryableError } from '../shared/RetryableError';
import { RightPanel } from '../shared/RightPanel';
import { CommentSkeleton } from '../shared/comments/CommentItem';
import { requestOpenComments } from '../shared/comments/openRequest';
import { NotificationItem } from './NotificationItem';
import { useNotifications } from './useNotifications';

/** The header bell for signed-in users: the unread count on the button, and the notifications in a
 *  `RightPanel`. Choosing one marks it read and opens what it's about (with its comments, for a comment). */
export function NotificationBell() {
    const { session } = useAuth();
    const token = session?.access_token;
    const [isOpen, setIsOpen] = useState(false);
    const navigate = useNavigate();
    const inbox = useNotifications(token, isOpen);

    if (!token) return null;

    const handleSelect = (notification: AppNotification) => {
        inbox.markRead([notification.id]);
        if (notification.comment_id) {
            requestOpenComments({ type: notification.subject_type, id: notification.subject_id });
        }
        setIsOpen(false);
        navigate(notificationPath(notification));
    };

    const renderBody = () => {
        if (inbox.loading && inbox.notifications.length === 0) {
            return (
                <div className="flex flex-col gap-5 p-2">
                    {Array.from({ length: 4 }, (_, i) => <CommentSkeleton key={i} />)}
                </div>
            );
        }
        if (inbox.error && inbox.notifications.length === 0) {
            return <RetryableError onRetry={inbox.retry}>{inbox.error}</RetryableError>;
        }
        if (inbox.notifications.length === 0) {
            return <EmptyState size="panel" title="All caught up.">Replies, comments and remixes on your work show up here.</EmptyState>;
        }
        return (
            <div className="flex flex-col gap-3">
                {inbox.unreadCount > 0 && (
                    <button type="button" onClick={() => inbox.markRead()} className={buttonClass('ghost', 'sm', 'self-end')}>
                        Mark all read
                    </button>
                )}
                <ul className="flex flex-col gap-1 -mx-2">
                    {inbox.notifications.map(notification => (
                        <li key={notification.id}>
                            <NotificationItem notification={notification} onSelect={handleSelect} />
                        </li>
                    ))}
                </ul>
                {inbox.error && <InlineError size="sm">{inbox.error}</InlineError>}
                {inbox.hasMore && (
                    <button type="button" onClick={inbox.loadMore} disabled={inbox.loadingMore} className={buttonClass('secondary', 'sm', 'self-center')}>
                        {inbox.loadingMore && <FaSpinner className="animate-spin text-[11px]" />}
                        Show more
                    </button>
                )}
            </div>
        );
    };

    const label = inbox.unreadCount > 0 ? `Notifications, ${inbox.unreadCount} unread` : 'Notifications';
    return (
        <>
            <button
                type="button"
                onClick={() => setIsOpen(open => !open)}
                aria-label={label}
                aria-expanded={isOpen}
                title="Notifications"
                className="relative inline-flex items-center justify-center w-8 h-8 rounded-control cursor-pointer text-(--text-secondary) transition-colors hover:text-(--text-primary) hover:bg-(--background-secondary)"
            >
                <FaRegBell className="w-4 h-4" />
                <CornerCount count={inbox.unreadCount} />
            </button>
            {/* Out of the header, whose sticky stacking context would trap the panel under other overlays */}
            {createPortal(
                <RightPanel isOpen={isOpen} onClose={() => setIsOpen(false)} title="Notifications">
                    {renderBody()}
                </RightPanel>,
                document.body,
            )}
        </>
    );
}
