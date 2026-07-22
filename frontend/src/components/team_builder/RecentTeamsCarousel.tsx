import { useMemo } from 'react';
import type { TeamSummary } from '../../api/userTeams';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { getContrastColor } from '../shared/Color';
import { FaCircle, FaHatWizard } from 'react-icons/fa6';

// =============================================================================
// MARK: - Recent Team Tracking
// =============================================================================

const RECENTLY_VIEWED_KEY = 'showdown_recent_teams';
const MAX_RECENT = 10;

export function trackRecentTeam(teamId: string) {
    try {
        const ids: string[] = JSON.parse(localStorage.getItem(RECENTLY_VIEWED_KEY) ?? '[]');
        const next = [teamId, ...ids.filter(id => id !== teamId)].slice(0, MAX_RECENT);
        localStorage.setItem(RECENTLY_VIEWED_KEY, JSON.stringify(next));
    } catch {}
}

function getRecentTeamIds(): string[] {
    try { return JSON.parse(localStorage.getItem(RECENTLY_VIEWED_KEY) ?? '[]'); }
    catch { return []; }
}

function toRgba(color: string, alpha: number): string {
    return color.replace('rgb(', 'rgba(').replace(')', `, ${alpha})`);
}

// =============================================================================
// MARK: - Carousel
// =============================================================================

type RecentTeamsCarouselProps = {
    teams: TeamSummary[];
    className?: string;
    onClick: (team: TeamSummary) => void;
};

export function RecentTeamsCarousel({ teams, className, onClick }: RecentTeamsCarouselProps) {
    const recentIds = useMemo(getRecentTeamIds, []);

    const recentTeams = useMemo(() => {
        const withPlayers = teams.filter(t => t.roster_count > 0);

        if (recentIds.length > 0) {
            const teamById = new Map(withPlayers.map(t => [t.team_id, t]));
            const ordered: TeamSummary[] = [];
            for (const id of recentIds) {
                const t = teamById.get(id);
                if (t) ordered.push(t);
            }
            const inOrdered = new Set(ordered.map(t => t.team_id));
            const rest = withPlayers
                .filter(t => !inOrdered.has(t.team_id))
                .sort((a, b) => (b.updated_at ?? '') > (a.updated_at ?? '') ? 1 : -1);
            return [...ordered, ...rest].slice(0, 4);
        }

        return [...withPlayers]
            .sort((a, b) => (b.updated_at ?? '') > (a.updated_at ?? '') ? 1 : -1)
            .slice(0, 8);
    }, [teams, recentIds]);

    if (recentTeams.length === 0) return null;

    return (
        <section className={`${className}`}>
            <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide px-4 mb-2">
                Recent Teams
            </div>
            <div
                className={`flex items-start gap-3 overflow-x-auto overflow-y-hidden overscroll-x-contain snap-x snap-mandatory pb-1 py-2 px-2 scrollbar-hide`}
                style={{ touchAction: 'pan-x' }}
            >

                {recentTeams.map(team => (
                    <RecentTeamCard
                        key={team.team_id}
                        team={team}
                        onClick={() => onClick(team)}
                    />
                ))}
            </div>
        </section>
    );
}

// =============================================================================
// MARK: - Team Card
// =============================================================================

type RecentTeamCardProps = {
    team: TeamSummary;
    onClick: () => void;
};

function RecentTeamCard({ team, onClick }: RecentTeamCardProps) {
    const primary = team.primary_color || 'rgb(20,20,20)';
    const secondary = team.secondary_color || 'rgb(80,80,80)';
    const onPrimary = getContrastColor(primary);
    const onSecondary = getContrastColor(secondary);

    // Top-3 players are hydrated server-side on the summary payload
    const slots: (CardDatabaseRecord | null)[] = [
        team.top_players[0] ?? null,
        team.top_players[1] ?? null,
        team.top_players[2] ?? null,
    ];

    return (
        <button
            type="button"
            onClick={onClick}
            className="
                snap-start shrink-0 relative
                w-44 md:w-52 aspect-3/4 rounded-xl
                overflow-hidden
                hover:scale-[1.025] active:scale-[0.975]
                transition-transform duration-150
                text-left border-2
                cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1
            "
            style={{
                borderColor: secondary,
            }}
        >
            {team.is_drafting && (
                <span
                    className="absolute flex items-center top-0 right-0 z-20 text-[9px] font-black rounded px-1 py-0.5 leading-none"
                    style={{
                        backgroundColor: secondary,
                        color: onSecondary,
                    }}    
                >
                    <FaCircle className="animate-pulse w-1.5 h-1.5 inline-block mr-0.5" />
                    DRAFTING
                </span>
            )}
            {/* Field background image */}
            <img
                src="/images/teams/Field.png"
                className="absolute inset-0 w-full h-full object-cover object-top select-none"
                alt=""
                aria-hidden
                draggable={false}
            />

            {/* Team primary color wash over the field (top) */}
            <div
                className="absolute inset-0"
                style={{
                    background: `linear-gradient(to bottom, ${toRgba(primary, 0.30)} 0%, ${toRgba(primary, 0.15)} 55%, transparent 75%)`,
                }}
            />

            {/* Dark gradient at the bottom for player cards readability */}
            <div
                className="absolute inset-0"
                style={{
                    background: 'linear-gradient(to top, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.70) 35%, transparent 60%)',
                }}
            />

            {/* Content */}
            <div className="relative z-10 flex flex-col h-full p-2.5 gap-1">
                {/* Team identity — top section */}
                <div className="flex-1 flex flex-col justify-start">
                    <div
                        className="text-[38px] leading-none font-black tracking-tight drop-shadow-lg"
                        style={{ color: onPrimary }}
                    >
                        {team.abbreviation}
                    </div>
                    <div
                        className="text-[10px] font-bold mt-0.5 line-clamp-1 drop-shadow opacity-85"
                        style={{ color: onPrimary }}
                    >
                        {team.name}
                    </div>
                    <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                        {team.total_points > 0 && (
                            <div
                                className="text-[10px] font-black rounded px-1.5 py-0.5 self-start leading-none"
                                style={{ backgroundColor: secondary, color: onSecondary }}
                            >
                                {team.total_points} PTS
                            </div>
                        )}
                    </div>
                    {team.allowed_card_sources && team.allowed_card_sources.length > 0 && (
                        <div className="flex items-center gap-0.5 mt-0.5">
                            {team.allowed_card_sources.map(src => (
                                <div
                                    key={src}
                                    className="flex items-center gap-0.5 text-[8px] font-bold uppercase px-1.5 py-0.5 rounded"
                                    style={{
                                        backgroundColor: 'rgba(255,255,255,0.85)',
                                        color: getContrastColor('rgba(255,255,255,0.85)'),
                                    }}
                                >
                                    {src === 'WOTC' ? <FaHatWizard className="w-2.5 h-2.5" /> : undefined}
                                    {src}
                                </div>
                            ))}
                        </div>
                    )}
                        
                </div>

                {/* Player cards — bottom section (top-3 hydrated on the payload) */}
                <div className="flex flex-col gap-0.5">
                    {slots.map((card, i) => (
                        card === null ? null : (
                            <CardItemCompactFromCardDatabaseRecord
                                key={i}
                                card={card}
                                hideDetails
                            />
                        )
                    ))}
                </div>
            </div>
        </button>
    );
}
