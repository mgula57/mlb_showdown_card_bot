import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import type { TeamSource } from '../../api/userTeams';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { getContrastTextColor } from '../../functions/colors';
import { imageForSet } from '../shared/SiteSettingsContext';
import { useAuth } from '../auth/AuthContext';
import { FaCircle, FaHatWizard, FaRobot } from 'react-icons/fa6';

// A minimal, source-agnostic shape so the same tile renders community teams (TeamSummary),
// historical MLB teams, and All-Star teams alike.
export type TeamPreviewData = {
    abbreviation: string;
    name: string;
    primary_color?: string | null;
    secondary_color?: string | null;
    total_points?: number;
    is_drafting?: boolean;
    allowed_card_sources?: string[] | null;
    /** Team provenance. */
    source?: TeamSource;
    /** Showdown set(s) this team is tied to. Rendered as set-logo icons in the top-right. */
    allowed_sets?: string[] | null;
    /** Top-3 cards, hydrated on the list payload. Optional — historical tiles have none. */
    top_players?: CardDatabaseRecord[];
    /** Small ribbon in the top-left, e.g. a year or "ALL-STAR". */
    badge?: string;
    /** Small line under the name (e.g. set name, roster count) shown when there are no points. */
    subtitle?: string;
    /** Uploaded team logo image, shown next to the abbreviation. Historical/ASG tiles have none. */
    logo_url?: string | null;
    /** Owner's user id — used to show the viewer's own avatar only on their own teams. */
    user_id?: string | null;
};

function toRgba(color: string, alpha: number): string {
    return color.replace('rgb(', 'rgba(').replace(')', `, ${alpha})`);
}

type TeamPreviewCardProps = {
    team: TeamPreviewData;
    onClick: () => void;
    /** Tile width. 'md' matches the Recent shelf; 'sm' packs more per row. */
    size?: 'sm' | 'md';
    className?: string;
};

/** Spotify-style "album cover" tile for a team: gradient border, field art, identity, and top-3 cards. */
export function TeamPreviewCard({ team, onClick, size = 'md', className = '' }: TeamPreviewCardProps) {
    const { user, userSettings } = useAuth();
    const primary = team.primary_color || 'rgb(20,20,20)';
    const secondary = team.secondary_color || 'rgb(80,80,80)';
    const onPrimary = getContrastTextColor(primary);
    const onSecondary = getContrastTextColor(secondary);
    const avatarUrl = user && team.user_id === user.id ? userSettings?.avatar_url : null;

    const widthClass = size === 'sm' ? 'w-40' : 'w-52';

    const slots: (CardDatabaseRecord | null)[] = [
        team.top_players?.[0] ?? null,
        team.top_players?.[1] ?? null,
        team.top_players?.[2] ?? null,
    ];
    const hasCards = slots.some(Boolean);

    const allowedSets = team.allowed_sets ?? [];
    const showSetGrid = allowedSets.length > 0;

    return (
        <button
            type="button"
            onClick={onClick}
            className={`
                snap-start shrink-0 relative
                ${widthClass} aspect-3/4 rounded-xl
                overflow-hidden
                hover:scale-[1.025] active:scale-[0.975]
                transition-transform duration-150
                text-left border-4 border-transparent
                cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1
                ${className}
            `}
            style={{
                backgroundImage: `linear-gradient(${primary}, ${primary}), linear-gradient(135deg, ${secondary}, ${primary})`,
                backgroundOrigin: 'border-box',
                backgroundClip: 'padding-box, border-box',
            }}
        >
            <div className="absolute top-0 right-0 z-20 flex flex-col items-end gap-0.5">
                {team.badge && (
                    <span
                        className="text-[9px] font-black rounded-bl-md px-1.5 py-0.5 leading-none uppercase tracking-wide"
                        style={{ backgroundColor: secondary, color: onSecondary }}
                    >
                        {team.badge}
                    </span>
                )}
                {team.is_drafting && (
                    <span
                        className="flex items-center text-[9px] font-black rounded-bl-md px-1 py-0.5 leading-none"
                        style={{ backgroundColor: secondary, color: onSecondary }}
                    >
                        <FaCircle className="animate-pulse w-1.5 h-1.5 inline-block mr-0.5" />
                        DRAFTING
                    </span>
                )}
                {showSetGrid && (
                    <div
                        className="rounded-bl-md p-1 flex flex-wrap items-center justify-end gap-0.5 max-w-24"
                        style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
                    >
                        {allowedSets.map(set => {
                            const useAbbreviated = allowedSets.length >= 2;
                            const image = imageForSet(set, useAbbreviated);
                            const heightClass = useAbbreviated ? 'h-3.5' : 'h-4.5';
                            return image ? (
                                <img key={set} src={image} alt={set} className={`${heightClass} w-auto object-contain`} />
                            ) : null;
                        })}
                    </div>
                )}
            </div>

            {/* Field background image */}
            <img
                src="/images/teams/Field.png"
                className="absolute -translate-y-25 w-full h-full object-cover object-top select-none opacity-30"
                alt=""
                aria-hidden
                draggable={false}
            />

            {/* Team primary color wash over the field (top) */}
            <div
                className="absolute inset-0"
                style={{ background: `linear-gradient(to bottom, ${toRgba(primary, 0.30)} 0%, ${toRgba(primary, 0.15)} 55%, transparent 75%)` }}
            />

            {/* Dark gradient at the bottom for readability */}
            <div
                className="absolute inset-0"
                style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.70) 35%, transparent 60%)' }}
            />

            {/* Content */}
            <div className="relative z-10 flex flex-col h-full p-2.5 gap-1">
                <div className="flex-1 flex flex-col justify-start min-h-0">
                    <div className="flex items-center gap-1.5 min-w-0">
                        {team.logo_url && (
                            <img
                                src={team.logo_url}
                                alt=""
                                className="w-7 h-7 rounded-md object-cover shrink-0 ring-1 ring-white/20"
                            />
                        )}
                        <div className="text-[38px] leading-none font-black tracking-tight drop-shadow-lg truncate" style={{ color: onPrimary }}>
                            {team.abbreviation}
                        </div>
                        {avatarUrl && (
                            <img
                                src={avatarUrl}
                                alt="Your avatar"
                                className="w-6 h-6 rounded-full object-cover shrink-0 ring-1 ring-white/30"
                            />
                        )}
                    </div>
                    <div className="text-[10px] font-bold mt-0.5 line-clamp-1 drop-shadow opacity-85" style={{ color: onPrimary }}>
                        {team.name}
                    </div>
                    <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                        {team.total_points && team.total_points > 0 ? (
                            <div className="text-[10px] font-black rounded px-1.5 py-0.5 self-start leading-none" style={{ backgroundColor: secondary, color: onSecondary }}>
                                {team.total_points} PTS
                            </div>
                        ) : team.subtitle ? (
                            <div className="text-[10px] font-bold rounded px-1.5 py-0.5 self-start leading-none" style={{ backgroundColor: secondary, color: onSecondary }}>
                                {team.subtitle}
                            </div>
                        ) : null}
                    </div>
                    {team.allowed_card_sources && team.allowed_card_sources.length > 0 && (
                        <div className="flex items-center gap-0.5 mt-0.5">
                            {team.allowed_card_sources.map(src => (
                                <div
                                    key={src}
                                    className="flex items-center gap-0.5 text-[8px] font-bold uppercase px-1.5 py-0.5 rounded"
                                    style={{ backgroundColor: 'rgba(255,255,255,0.85)', color: getContrastTextColor('rgba(255,255,255,0.85)') }}
                                >
                                    {src === 'WOTC' ? <FaHatWizard className="w-2.5 h-2.5" /> : undefined}
                                    {src === 'BOT' ? <FaRobot className="w-2.5 h-2.5" /> : undefined}
                                    {src}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {hasCards && (
                    <div className="flex flex-col gap-0.5">
                        {slots.map((card, i) => (
                            card === null ? null : (
                                <CardItemCompactFromCardDatabaseRecord key={i} card={card} hideDetails />
                            )
                        ))}
                    </div>
                )}
            </div>
        </button>
    );
}

/** Loading placeholder sized to match TeamPreviewCard, for shelves that are still fetching. */
export function TeamPreviewCardSkeleton({ size = 'md', className = '' }: { size?: 'sm' | 'md'; className?: string }) {
    const widthClass = size === 'sm' ? 'w-40' : 'w-52';
    return (
        <div
            aria-hidden
            className={`snap-start shrink-0 ${widthClass} aspect-3/4 rounded-xl bg-(--background-secondary) animate-pulse ${className}`}
        />
    );
}

export default TeamPreviewCard;
