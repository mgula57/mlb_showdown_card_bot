import { useMemo } from 'react';
import type { TeamSummary } from '../../api/userTeams';
import { TeamPreviewCard } from './TeamPreviewCard';

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
                className={`flex gap-3 overflow-x-auto overflow-y-hidden pb-1 py-2 px-2 scrollbar-hide`}
            >
                {recentTeams.map(team => (
                    <TeamPreviewCard
                        key={team.team_id}
                        team={team}
                        onClick={() => onClick(team)}
                    />
                ))}
            </div>
        </section>
    );
}
