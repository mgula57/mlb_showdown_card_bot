import { useEffect, useMemo, useState } from 'react';
import { fetchTeamCollections, type TeamCollection, type TeamSummary } from '../../api/userTeams';
import { matchesTeamQuery } from './teamSearch';
import { TeamPreviewCard } from './TeamPreviewCard';
import { TeamShelf } from './TeamShelf';
import { FaSpinner } from 'react-icons/fa6';

type FeaturedCollectionsProps = {
    onOpen: (team: TeamSummary) => void;
    onOpenCollection?: (slug: string) => void;
    horizontalPadding?: string;
    /** When set, filters every collection's teams client-side and drops empty shelves. */
    query?: string;
};

/** Admin-curated collections rendered music-app style — one shelf per collection. */
export function FeaturedCollections({ onOpen, onOpenCollection, horizontalPadding, query }: FeaturedCollectionsProps) {
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
                teams: q ? (c.teams ?? []).filter(t => matchesTeamQuery(t, q)) : (c.teams ?? []),
            }))
            .filter(c => c.teams.length > 0);
    }, [collections, query]);

    if (error) {
        return <p className={`${px} text-[12px] text-red-400`}>{error}</p>;
    }
    if (collections === null) {
        return <div className="flex justify-center py-8"><FaSpinner className="animate-spin text-(--text-tertiary)" /></div>;
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
                    bleedRight
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
