import { DEFAULT_PRIMARY_COLOR, DEFAULT_SECONDARY_COLOR } from '../../api/userSettings';
import { userInitials } from '../../functions/formatters';

type UserAvatarProps = {
    /** Username (or email) — drives the initials fallback and the alt text. */
    name?: string | null;
    avatarUrl?: string | null;
    /** The user's own default colors, for the initials gradient (matches `AccountAvatar`). */
    primaryColor?: string | null;
    secondaryColor?: string | null;
    /** Diameter in px. */
    size?: number;
    className?: string;
};

/** Any user's avatar — their uploaded image, or initials over their default-color gradient when
 *  they haven't set one. Presentational only; `AccountAvatar` is the signed-in user's own button. */
export function UserAvatar({ name, avatarUrl, primaryColor, secondaryColor, size = 24, className = '' }: UserAvatarProps) {
    const dimensions = { width: size, height: size };
    if (avatarUrl) {
        return <img src={avatarUrl} alt={name ? `${name}'s avatar` : 'avatar'} style={dimensions} className={`shrink-0 rounded-full object-cover ${className}`} />;
    }
    return (
        <span
            aria-hidden
            style={{
                ...dimensions,
                fontSize: Math.round(size * 0.4),
                background: `linear-gradient(to right, ${primaryColor ?? DEFAULT_PRIMARY_COLOR} 15%, ${secondaryColor ?? DEFAULT_SECONDARY_COLOR} 85%)`,
            }}
            className={`inline-flex shrink-0 select-none items-center justify-center rounded-full font-semibold text-white ${className}`}
        >
            {userInitials(name)}
        </span>
    );
}
