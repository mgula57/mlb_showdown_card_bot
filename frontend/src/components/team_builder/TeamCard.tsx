import type { TeamSummary } from '../../api/userTeams';
import { getContrastTextColor } from '../../functions/colors';
import { useTheme, imageForSet } from '../shared/SiteSettingsContext';
import { useAuth } from '../auth/AuthContext';
import { FaLock, FaUsers } from 'react-icons/fa6';
import PointsBadge from '../cards/card_elements/PointsBadge';

type TeamCardProps = {
    team: TeamSummary;
    isSelected?: boolean;
    onClick?: () => void;
};

export function TeamCard({ team, isSelected, onClick }: TeamCardProps) {
    const { isDark } = useTheme();
    const { userSettings, username } = useAuth();
    const primary = team.primary_color || 'rgb(0,0,0)';
    const secondary = team.secondary_color || 'rgb(255,255,255)';
    const avatarUrl = userSettings?.avatar_url;
    const allowedSets = team.allowed_sets ?? [];

    const rosterCount = team.roster_count ?? 0;
    const drafting = team.is_drafting;

    const borderSettings = isSelected
        ? (isDark ? 'border-3 border-white/60' : 'border-3 border-gray-700')
        : (isDark ? 'border-3 border-white/10' : 'border-3 border-gray-200');
    const borderStyle = drafting ? 'border-dotted' : 'border-solid';

    return (
        <button
            type="button"
            onClick={onClick}
            style={{ 
                backgroundColor: `color-mix(in srgb, ${primary} 14%, var(--background-secondary))`, 
            }}
            className={`
                relative w-full text-left flex items-center gap-3
                rounded-lg p-3 ${borderSettings} ${borderStyle}
                ${onClick ? 'cursor-pointer hover:opacity-90' : 'cursor-default'}
                transition-opacity
            `}
        >
            {drafting && (
                <span className="absolute top-0 right-0 text-[9px] font-black rounded-tr px-1 py-0.5 leading-none bg-red-500 text-white">
                    DRAFTING
                </span>
            )}
            {/* Team logo (left of the abbreviation badge) */}
            <div className="shrink-0 flex items-center gap-1.5">
                {team.logo_url ? (
                    <img
                        src={team.logo_url}
                        alt={`${team.abbreviation} logo`}
                        className="w-10 h-10 rounded-md object-cover shrink-0"
                    />
                ) : (
                    <div
                        className="w-10 h-10 rounded-md flex items-center justify-center text-[11px] font-black shrink-0"
                        style={{ backgroundColor: primary, color: getContrastTextColor(primary) }}
                    >
                        {team.abbreviation}
                    </div>
                )}
            </div>

            <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                    <span className="text-[13px] font-bold text-(--text-primary) truncate">
                        {team.name}
                    </span>
                    {!team.is_public && <FaLock className="shrink-0 text-[10px] text-(--text-tertiary)" />}
                </div>
                {username && (
                    <div className="text-[11px] text-(--text-tertiary) truncate">
                        @{username}
                    </div>
                )}
                <div className="flex items-center gap-2 mt-0.5">
                    <span className="flex items-center gap-0.5 text-[10px] text-(--text-tertiary)">
                        <FaUsers className="text-[9px]" />
                        {rosterCount}
                    </span>
                    <PointsBadge points={team.total_points} bg_color={secondary} />
                </div>
            </div>

            {/* Allowed showdown sets, as a grid of icons to the left of the owner's avatar */}
            {allowedSets.length > 0 && (
                <div className={`shrink-0 content-center ml-auto ${allowedSets.length < 2 ? 'flex items-center' : 'grid grid-cols-3 gap-1'}`}>
                    {allowedSets.map(set => {
                        const useAbbreviated = allowedSets.length >= 2;
                        const image = imageForSet(set, useAbbreviated);
                        const heightClass = useAbbreviated ? 'h-4.5' : 'h-5.5';
                        return image ? (
                            <img key={set} src={image} alt={set} className={`${heightClass} w-auto object-contain`} />
                        ) : null;
                    })}
                </div>
            )}

            {/* Owner's avatar, on the far right of the card */}
            {avatarUrl && (
                <img
                    src={avatarUrl}
                    alt="Your avatar"
                    className="w-7 h-7 rounded-full object-cover shrink-0"
                />
            )}
        </button>
    );
}
