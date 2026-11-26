import type { IconType } from 'react-icons';
import { FaBaseball, FaClock, FaFlagCheckered, FaTrophy } from 'react-icons/fa6';
import type { AppNotification, NotificationKind, NotificationSubjectType } from '../../api/notifications';
import { relativeTime } from '../../functions/formatters';
import { UserAvatar } from '../shared/UserAvatar';

/** One notification as a sentence: the actor's name (when a person did it), `lead`, the subject's name, `tail`. */
type Sentence = { actor: boolean; lead: string; tail?: string };

const SUBJECT_NOUN: Record<NotificationSubjectType, string> = {
    release: 'release', team: 'team', league: 'league', live_game: 'game', sim_lobby: 'sim lobby',
};

function sentence(kind: NotificationKind, subjectType: NotificationSubjectType): Sentence {
    const noun = SUBJECT_NOUN[subjectType];
    switch (kind) {
        case 'comment_reply': return { actor: true, lead: `replied to your comment on the ${noun}` };
        case 'subject_comment': return { actor: true, lead: `commented on your ${noun}` };
        case 'release_remix': return { actor: true, lead: 'remixed your release' };
        case 'league_join': return { actor: true, lead: 'joined your league' };
        case 'league_draft_start': return { actor: true, lead: 'started the draft in' };
        case 'league_on_the_clock': return { actor: false, lead: "You're on the clock in" };
        case 'league_removed': return { actor: true, lead: 'removed you from' };
        case 'league_regular_season_end': return { actor: false, lead: 'The regular season is over in' };
        case 'league_season_complete': return { actor: false, lead: 'The season is over in' };
        case 'live_game_accepted': return { actor: true, lead: 'accepted your invite to' };
        case 'live_game_final': return { actor: false, lead: 'Final:' };
        case 'lobby_join': return { actor: true, lead: 'joined your sim lobby' };
        case 'lobby_start': return { actor: true, lead: 'started the sim lobby' };
        case 'lobby_finished': return { actor: false, lead: 'The sim lobby', tail: ' finished' };
    }
}

/** The mark beside a notification nobody in particular sent (a sim finished something, your pick is up). */
const KIND_ICON: Partial<Record<NotificationKind, IconType>> = {
    league_on_the_clock: FaClock,
    league_regular_season_end: FaFlagCheckered,
    league_season_complete: FaTrophy,
    live_game_final: FaBaseball,
    lobby_finished: FaFlagCheckered,
};

type NotificationItemProps = {
    notification: AppNotification;
    onSelect: (notification: AppNotification) => void;
};

/** One row in the notifications panel: who, what and where, the comment's opening words, and when. */
export function NotificationItem({ notification, onSelect }: NotificationItemProps) {
    const isUnread = !notification.read_at;
    const { actor, lead, tail } = sentence(notification.kind, notification.subject_type);
    const Icon = KIND_ICON[notification.kind] ?? FaTrophy;
    const subjectName = notification.subject_name ?? `your ${SUBJECT_NOUN[notification.subject_type]}`;
    return (
        <button
            type="button"
            onClick={() => onSelect(notification)}
            className="w-full flex gap-2.5 p-2 text-left rounded-control cursor-pointer transition-colors hover:bg-(--background-tertiary)"
        >
            {actor ? (
                <UserAvatar
                    name={notification.actor_username}
                    avatarUrl={notification.actor_avatar_url}
                    primaryColor={notification.actor_primary_color}
                    size={28}
                />
            ) : (
                <span aria-hidden className="w-7 h-7 shrink-0 flex items-center justify-center rounded-plate bg-(--background-tertiary) text-(--text-secondary)">
                    <Icon className="w-3.5 h-3.5" />
                </span>
            )}
            <div className="flex-1 min-w-0">
                <p className={`text-[13px] leading-snug ${isUnread ? 'text-(--text-primary)' : 'text-(--text-secondary)'}`}>
                    {actor && <span className="font-semibold">{notification.actor_username ?? 'Someone'} </span>}
                    {`${lead} `}
                    <span className="font-semibold">{subjectName}</span>
                    {tail}
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
