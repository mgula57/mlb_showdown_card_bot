import type { TeamSummary } from '../../api/userTeams';
import { getContrastTextColor } from '../../functions/colors';
import { useTheme } from '../shared/SiteSettingsContext';
import { useAuth } from '../auth/AuthContext';
import { FaLock, FaGlobe, FaUsers } from 'react-icons/fa6';

type TeamCardProps = {
    team: TeamSummary;
    isSelected?: boolean;
    onClick?: () => void;
};

export function TeamCard({ team, isSelected, onClick }: TeamCardProps) {
    const { isDark } = useTheme();
    const { userSettings } = useAuth();
    const primary = team.primary_color || 'rgb(0,0,0)';
    const secondary = team.secondary_color || 'rgb(255,255,255)';
    const avatarUrl = userSettings?.avatar_url;

    const rosterCount = team.roster_count ?? 0;
    const drafting = team.is_drafting;

    const borderSettings = isSelected
        ? (isDark ? 'border-2 border-white/60' : 'border-2 border-gray-700')
        : (isDark ? 'border-2 border-white/10' : 'border-2 border-gray-200');
    const borderStyle = drafting ? 'border-dotted' : 'border-solid';

    return (
        <button
            type="button"
            onClick={onClick}
            className={`
                relative w-full text-left flex items-center gap-3
                rounded-lg p-3 ${borderSettings} ${borderStyle}
                ${onClick ? 'cursor-pointer hover:opacity-90' : 'cursor-default'}
                transition-opacity
            `}
        >
            {drafting && (
                <span className="absolute top-0 right-0 text-[8px] font-black rounded-tr px-1 py-0.5 leading-none bg-red-500 text-white">
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
                    {team.is_public
                        ? <FaGlobe className="shrink-0 text-[10px] text-(--text-tertiary)" />
                        : <FaLock className="shrink-0 text-[10px] text-(--text-tertiary)" />
                    }
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                    {(team.allowed_sets ?? []).length > 0 && (
                        <span className="text-[11px] text-(--text-secondary)">
                            {(team.allowed_sets ?? []).join(', ')}
                        </span>
                    )}
                    <span
                        className="text-[9px] font-black rounded px-1 py-0.5 leading-none"
                        style={{ backgroundColor: secondary, color: getContrastTextColor(secondary) }}
                    >
                        {team.source.toUpperCase()}
                    </span>

                    <span className="flex items-center gap-0.5 text-[10px] text-(--text-tertiary)">
                        <FaUsers className="text-[9px]" />
                        {rosterCount}
                    </span>
                </div>
            </div>

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
