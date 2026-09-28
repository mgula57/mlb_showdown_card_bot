import { useEffect, useMemo, useState } from 'react';
import { fetchTeamCollections, type TeamCollection, type TeamSummary } from '../../api/userTeams';
import { matchesTeamQuery } from './teamSearch';
import { TeamPreviewCard } from './TeamPreviewCard';
import { TeamShelf, TeamShelfSkeleton } from './TeamShelf';

type FeaturedCollectionsProps = {
    onOpen: (team: TeamSummary) => void;
    onOpenCollection?: (slug: string) => void;
    horizontalPadding?: string;
    /** When set, filters every collection's teams client-side and drops empty shelves. */
    query?: string;
    /** When set, only shows teams whose `allowed_sets` includes this Showdown set. */
    showdownSet?: string;
};

/** Admin-curated collections rendered music-app style — one shelf per collection. */
export function FeaturedCollections({ onOpen, onOpenCollection, horizontalPadding, query, showdownSet }: FeaturedCollectionsProps) {
    const [collections, setCollections] = useState<TeamCollection[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const px = horizontalPadding ?? '';

    useEffect(() => {
        fetchTeamCollections()
            .then(setCollections)
            .catch(err => setError(err.message ?? 'Failed to load collections.'));
    }, []);

    const shelves = useMemo(() => {
        if (!collections) return [];
        const q = (query ?? '').trim();
        return collections
            .map(c => ({
                ...c,
                teams: (c.teams ?? [])
                    .filter(t => !showdownSet || !t.allowed_sets || t.allowed_sets.length === 0 || t.allowed_sets.includes(showdownSet))
                    .filter(t => !q || matchesTeamQuery(t, q)),
            }))
            .filter(c => c.teams.length > 0);
    }, [collections, query, showdownSet]);

    if (error) {
        return <p className={`${px} text-[12px] text-red-400`}>{error}</p>;
    }
    if (collections === null) {
        return <TeamShelfSkeleton shelves={2} className={px} />;
    }
    if (shelves.length === 0) return null;

    return (
        <>
            {shelves.map(c => (
                <TeamShelf
                    key={c.slug}
                    title={`${c.cover_emoji ? c.cover_emoji + ' ' : ''}${c.title}`}
                    subtitle={c.description ?? undefined}
                    className={px}
                    bleed
                    onSeeAll={onOpenCollection ? () => onOpenCollection(c.slug) : undefined}
                >
                    {c.teams.map(team => (
                        <TeamPreviewCard
                            key={team.team_id}
                            team={{ ...team, badge: team.subtitle ?? undefined }}
                            onClick={() => onOpen(team)}
                        />
                    ))}
                </TeamShelf>
            ))}
        </>
    );
}

export default FeaturedCollections;
