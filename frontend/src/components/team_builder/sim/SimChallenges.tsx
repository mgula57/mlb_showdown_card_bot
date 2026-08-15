import { useEffect, useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import { fetchChallenges, type ChallengeInstance } from '../../../api/sim';
import { ChallengeCard } from './ChallengeCard';

type Props = {
    token?: string;
    onQuickStart: (challenge: ChallengeInstance) => void;
    onBuildFromScratch: (challenge: ChallengeInstance) => void;
    onUseExistingTeam: (challenge: ChallengeInstance, teamId: string) => void;
};

/** The live, auto-generated list of Team Challenges — the default view of the Team Challenges tab. */
export function SimChallenges({ token, onQuickStart, onBuildFromScratch, onUseExistingTeam }: Props) {
    const [challenges, setChallenges] = useState<ChallengeInstance[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let stale = false;
        fetchChallenges(token)
            .then(data => { if (!stale) setChallenges(data); })
            .catch(err => { if (!stale) setError(err instanceof Error ? err.message : 'Failed to load challenges.'); });
        return () => { stale = true; };
    }, [token]);

    if (error) {
        return (
            <div className="mx-4 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                {error}
            </div>
        );
    }

    if (challenges === null) {
        return (
            <div className="flex justify-center py-12">
                <FaSpinner className="animate-spin text-(--text-tertiary) text-xl" />
            </div>
        );
    }

    if (challenges.length === 0) {
        return (
            <p className="text-[13px] text-(--text-tertiary) py-8 text-center">
                No challenges are live right now — check back soon.
            </p>
        );
    }

    return (
        <div className="flex flex-col gap-3">
            {challenges.map(challenge => (
                <ChallengeCard
                    key={challenge.instance_id}
                    challenge={challenge}
                    token={token}
                    onQuickStart={onQuickStart}
                    onBuildFromScratch={onBuildFromScratch}
                    onUseExistingTeam={onUseExistingTeam}
                />
            ))}
        </div>
    );
}
