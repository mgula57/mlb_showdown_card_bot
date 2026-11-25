import type { AppNotification, NotificationKind } from '../../api/notifications';
import type { CommentSubjectType } from '../../api/comments';
import { relativeTime } from '../../functions/formatters';
import { UserAvatar } from '../shared/UserAvatar';

const SUBJECT_NOUN: Record<CommentSubjectType, string> = { release: 'release', team: 'team' };

/** What happened, between the actor's name and the subject's name. */
function describe(kind: NotificationKind, subjectType: CommentSubjectType): string {
    const noun = SUBJECT_NOUN[subjectType];
    switch (kind) {
        case 'comment_reply': return `replied to your comment on the ${noun}`;
        case 'subject_comment': return `commented on your ${noun}`;
        case 'release_remix': return 'remixed your release';
    }
}

type NotificationItemProps = {
    notification: AppNotification;
    onSelect: (notification: AppNotification) => void;
};

/** One row in the notifications panel: who, what and where, the comment's opening words, and when. */
export function NotificationItem({ notification, onSelect }: NotificationItemProps) {
    const isUnread = !notification.read_at;
    const actor = notification.actor_username ?? 'Someone';
    return (
        <button
            type="button"
            onClick={() => onSelect(notification)}
            className="w-full flex gap-2.5 p-2 text-left rounded-control cursor-pointer transition-colors hover:bg-(--background-tertiary)"
        >
            <UserAvatar
                name={notification.actor_username}
                avatarUrl={notification.actor_avatar_url}
                primaryColor={notification.actor_primary_color}
                size={28}
            />
            <div className="flex-1 min-w-0">
                <p className={`text-[13px] leading-snug ${isUnread ? 'text-(--text-primary)' : 'text-(--text-secondary)'}`}>
                    <span className="font-semibold">{actor}</span>
                    {` ${describe(notification.kind, notification.subject_type)} `}
                    <span className="font-semibold">{notification.subject_name}</span>
                </p>
                {notification.comment_excerpt && (
                    <p className="mt-0.5 text-[13px] leading-snug text-(--text-tertiary) line-clamp-2 break-words">
                        “{notification.comment_excerpt}”
                    </p>
                )}
                <p className="mt-1 text-xs text-(--text-tertiary)">{relativeTime(notification.created_at)}</p>
            </div>
            {isUnread && <span className="mt-1.5 w-2 h-2 shrink-0 rounded-full bg-(--showdown-blue)" aria-label="Unread" />}
        </button>
    );
}
