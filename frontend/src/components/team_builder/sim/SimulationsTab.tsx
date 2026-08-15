import { useState } from 'react';
import { SimLeaderboard } from './SimLeaderboard';
import { SimHistory } from './SimHistory';
import { SimChallenges } from './SimChallenges';
import { Tabs, type TabItem } from '../../shared/Tabs';
import type { ChallengeInstance } from '../../../api/sim';

type View = 'challenges' | 'leaderboard' | 'mine';

const VIEW_TABS: TabItem<View>[] = [
    { id: 'challenges', label: 'Challenges' },
    { id: 'leaderboard', label: 'Leaderboard' },
    { id: 'mine', label: 'My Seasons' },
];

type Props = {
    token?: string;
    horizontalPadding?: string;
    onOpenSeason: (teamId: string, jobId: string) => void;
    onQuickStart: (challenge: ChallengeInstance) => void;
    onBuildFromScratch: (challenge: ChallengeInstance) => void;
    onUseExistingTeam: (challenge: ChallengeInstance, teamId: string) => void;
};

/**
 * Home for Team Challenges: the live challenge list is the front door, with the global
 * leaderboard and the signed-in user's own history demoted to secondary views in the same
 * segmented control rather than gone — "browse everything that's been played" is still one tap
 * away, just no longer the first thing you see.
 */
export function SimulationsTab({ token, horizontalPadding, onOpenSeason, onQuickStart, onBuildFromScratch, onUseExistingTeam }: Props) {
    const [view, setView] = useState<View>('challenges');

    return (
        <div className={`flex flex-col gap-4 ${horizontalPadding}`}>
            <Tabs tabs={VIEW_TABS} value={view} onChange={setView} />

            {view === 'challenges' && (
                <SimChallenges
                    token={token}
                    onQuickStart={onQuickStart}
                    onBuildFromScratch={onBuildFromScratch}
                    onUseExistingTeam={onUseExistingTeam}
                />
            )}
            {view === 'leaderboard' && <SimLeaderboard token={token} onOpenSeason={onOpenSeason} />}
            {view === 'mine' && <SimHistory token={token} onOpenSeason={onOpenSeason} />}
        </div>
    );
}
