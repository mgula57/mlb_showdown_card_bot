import { useEffect, useState } from 'react';
import { fetchTeamCollections, type TeamCollection, type TeamSummary } from '../../api/userTeams';
import { TeamPreviewCard, TeamPreviewCardSkeleton } from './TeamPreviewCard';
import BackButton from '../shared/BackButton';

import { Heading } from '../shared/Heading';
import { EmptyState } from '../shared/EmptyState';
type CollectionDetailProps = {
    slug: string;
    onOpenTeam: (team: TeamSummary) => void;
    onBack: () => void;
    horizontalPadding?: string;
};

/** Shareable page for one curated collection — /teams/collections/<slug>. */
export function CollectionDetail({ slug, onOpenTeam, onBack, horizontalPadding }: CollectionDetailProps) {
    const [collection, setCollection] = useState<TeamCollection | null | undefined>(undefined);
    const px = horizontalPadding ?? '';

    useEffect(() => {
        fetchTeamCollections()
            .then(list => setCollection(list.find(c => c.slug === slug) ?? null))
            .catch(() => setCollection(null));
    }, [slug]);

    if (collection === undefined) {
        return (
            <div className="flex flex-col gap-4 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full animate-pulse" aria-label="Loading collection">
                <div className={px}><div className="h-7 w-64 rounded-plate bg-(--background-tertiary)" /></div>
                <div className={`flex flex-wrap gap-3 ${px}`}>
                    {Array.from({ length: 6 }, (_, i) => <TeamPreviewCardSkeleton key={i} />)}
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-4 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
            <div className={`flex items-center gap-3 ${px}`}>
                <BackButton onBack={onBack} />
                <div>
                    <Heading level="page">
                        {collection ? `${collection.cover_emoji ? collection.cover_emoji + ' ' : ''}${collection.title}` : 'Collection not found'}
                    </Heading>
                    {collection?.description && (
                        <p className="text-[12px] text-(--text-secondary)">{collection.description}</p>
                    )}
                </div>
            </div>

            {collection && (
                <div className={`flex flex-wrap gap-3 ${px}`}>
                    {(collection.teams ?? []).map(team => (
                        <TeamPreviewCard
                            key={team.team_id}
                            team={{ ...team, badge: team.subtitle ?? undefined }}
                            onClick={() => onOpenTeam(team)}
                        />
                    ))}
                    {(collection.teams ?? []).length === 0 && (
                        <EmptyState size="panel" title="Empty collection." className="w-full">No teams have been added to this collection yet.</EmptyState>
                    )}
                </div>
            )}
        </div>
    );
}

export default CollectionDetail;
