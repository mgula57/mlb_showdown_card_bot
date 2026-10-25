import { DEFAULT_PRIMARY_COLOR } from '../../api/userSettings';
import { getContrastTextColor } from '../../functions/colors';
import { userInitials } from '../../functions/formatters';

type UserAvatarProps = {
    /** Username (or email) — drives the initials fallback and the alt text. */
    name?: string | null;
    avatarUrl?: string | null;
    /** The user's own default primary color, the flat fill behind their initials. */
    primaryColor?: string | null;
    /** Diameter in px. */
    size?: number;
    className?: string;
};

/** Any user's avatar — their uploaded image, or initials on their default primary color when
 *  they haven't set one. Presentational only; `AccountAvatar` wraps it as the signed-in user's button. */
export function UserAvatar({ name, avatarUrl, primaryColor, size = 24, className = '' }: UserAvatarProps) {
    const dimensions = { width: size, height: size };
    if (avatarUrl) {
        return <img src={avatarUrl} alt={name ? `${name}'s avatar` : 'avatar'} style={dimensions} className={`shrink-0 rounded-full object-cover ${className}`} />;
    }
    const fill = primaryColor ?? DEFAULT_PRIMARY_COLOR;
    return (
        <span
            aria-hidden
            style={{
                ...dimensions,
                fontSize: Math.round(size * 0.4),
                backgroundColor: fill,
                color: getContrastTextColor(fill),
            }}
            className={`inline-flex shrink-0 select-none items-center justify-center rounded-full font-semibold ${className}`}
        >
            {userInitials(name)}
        </span>
    );
}
