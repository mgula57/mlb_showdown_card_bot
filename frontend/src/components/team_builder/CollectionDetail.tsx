import { useEffect, useState } from 'react';
import { fetchTeamCollections, type TeamCollection, type TeamSummary } from '../../api/userTeams';
import { TeamPreviewCard } from './TeamPreviewCard';
import BackButton from '../shared/BackButton';
import { FaSpinner } from 'react-icons/fa6';

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
        return <div className="flex justify-center py-16"><FaSpinner className="animate-spin text-(--text-tertiary) text-xl" /></div>;
    }

    return (
        <div className="flex flex-col gap-4 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
            <div className={`flex items-center gap-3 ${px}`}>
                <BackButton onBack={onBack} />
                <div>
                    <h1 className="text-[20px] font-black text-(--text-primary)">
                        {collection ? `${collection.cover_emoji ? collection.cover_emoji + ' ' : ''}${collection.title}` : 'Collection not found'}
                    </h1>
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
                        <p className="text-[13px] text-(--text-tertiary) py-8">No teams in this collection yet.</p>
                    )}
                </div>
            )}
        </div>
    );
}

export default CollectionDetail;
