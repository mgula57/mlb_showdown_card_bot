import { useMemo } from 'react';
import type { Team } from '../../api/userTeams';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { useCardMap } from '../../hooks/useCardMap';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { getContrastColor } from '../shared/Color';

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

// =============================================================================
// MARK: - Helpers
// =============================================================================

function getTop3Slots(team: Team): { card_id: string; card_source: Team['roster'][0]['card_source'] }[] {
    const lineupSlots = (team.lineups[0]?.slots ?? [])
        .slice()
        .sort((a, b) => (a.batting_order ?? 99) - (b.batting_order ?? 99));
    const all = [...lineupSlots, ...team.rotation];
    const seen = new Set<string>();
    const result: { card_id: string; card_source: Team['roster'][0]['card_source'] }[] = [];
    for (const s of all) {
        if (!seen.has(s.card_id)) {
            seen.add(s.card_id);
            result.push({ card_id: s.card_id, card_source: s.card_source });
        }
        if (result.length >= 3) break;
    }
    return result;
}

// =============================================================================
// MARK: - Carousel
// =============================================================================

type RecentTeamsCarouselProps = {
    teams: Team[];
    className?: string;
    onClick: (team: Team) => void;
};

export function RecentTeamsCarousel({ teams, className, onClick }: RecentTeamsCarouselProps) {
    const recentIds = useMemo(getRecentTeamIds, []);

    const recentTeams = useMemo(() => {
        const withPlayers = teams.filter(
            t => t.roster.length > 0 || t.lineups.some(l => l.slots.length > 0) || t.rotation.length > 0
        );

        if (recentIds.length > 0) {
            const teamById = new Map(withPlayers.map(t => [t.team_id, t]));
            const ordered: Team[] = [];
            for (const id of recentIds) {
                const t = teamById.get(id);
                if (t) ordered.push(t);
            }
            const inOrdered = new Set(ordered.map(t => t.team_id));
            const rest = withPlayers
                .filter(t => !inOrdered.has(t.team_id))
                .sort((a, b) => (b.updated_at ?? '') > (a.updated_at ?? '') ? 1 : -1);
            return [...ordered, ...rest].slice(0, 8);
        }

        return [...withPlayers]
            .sort((a, b) => (b.updated_at ?? '') > (a.updated_at ?? '') ? 1 : -1)
            .slice(0, 8);
    }, [teams, recentIds]);

    const allSlots = useMemo(
        () => recentTeams.flatMap(t => getTop3Slots(t)).filter((s, i, arr) => arr.findIndex(x => x.card_id === s.card_id) === i),
        [recentTeams],
    );
    const { cardMap, loading: cardsLoading } = useCardMap(allSlots);

    if (recentTeams.length === 0) return null;

    return (
        <section className={`${className}`}>
            <div className="text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide px-4 mb-2">
                Recent Teams
            </div>
            <div className={`flex gap-3 overflow-x-auto pb-1 py-2 px-2 scrollbar-hide`}>
                {recentTeams.map(team => (
                    <RecentTeamCard
                        key={team.team_id}
                        team={team}
                        playerCards={getTop3Slots(team).map(s => cardMap[s.card_id] ?? null)}
                        cardsLoading={cardsLoading}
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
    team: Team;
    playerCards: (CardDatabaseRecord | null)[];
    cardsLoading: boolean;
    onClick: () => void;
};

function RecentTeamCard({ team, playerCards, cardsLoading, onClick }: RecentTeamCardProps) {
    const primary = team.primary_color || 'rgb(20,20,20)';
    const secondary = team.secondary_color || 'rgb(80,80,80)';
    const onPrimary = getContrastColor(primary);
    const onSecondary = getContrastColor(secondary);

    // Ensure we always render exactly 3 slots
    const slots: (CardDatabaseRecord | null)[] = [
        playerCards[0] ?? null,
        playerCards[1] ?? null,
        playerCards[2] ?? null,
    ];
    const hasAnyCardIds = slots.some(() => true); // will always be true for 3 slots

    return (
        <button
            type="button"
            onClick={onClick}
            className="
                snap-start shrink-0 relative
                w-44 md:w-56 xl:w-64 rounded-xl overflow-hidden
                hover:scale-[1.025] active:scale-[0.975]
                transition-transform duration-150
                text-left border-2
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1
            "
            style={{
                aspectRatio: '3/4',
                borderColor: secondary,
            }}
        >
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
                    background: `linear-gradient(to bottom, ${primary}EE 0%, ${primary}AA 50%, transparent 70%)`,
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
                    {team.total_points > 0 && (
                        <div
                            className="text-[8px] font-black mt-1.5 rounded px-1.5 py-0.5 self-start leading-none"
                            style={{ backgroundColor: secondary, color: onSecondary }}
                        >
                            {team.total_points} PTS
                        </div>
                    )}
                </div>

                {/* Player cards — bottom section */}
                <div className="flex flex-col gap-0.5">
                    {slots.map((card, i) => {
                        const isSlotLoading = cardsLoading && card === null;
                        if (!cardsLoading && card === null && !hasAnyCardIds) {
                            return (
                                <div
                                    key={i}
                                    className="h-8 rounded-lg bg-white/10 border border-white/10"
                                />
                            );
                        }
                        return (
                            <CardItemCompactFromCardDatabaseRecord
                                key={i}
                                card={card ?? undefined}
                                size="sm"
                                isLoading={isSlotLoading}
                            />
                        );
                    })}
                </div>
            </div>
        </button>
    );
}
