import { useState } from 'react';
import { SimLeaderboard } from './SimLeaderboard';
import { SimHistory } from './SimHistory';
import { SimChallenges } from './SimChallenges';
import BackButton from '../../shared/BackButton';
import { Tabs, type TabItem } from '../../shared/Tabs';
import { useAuth } from '../../auth/AuthContext';
import type { ChallengeInstance } from '../../../api/sim';
import { FaArrowRight } from 'react-icons/fa';
import { FaGear } from 'react-icons/fa6';

type BrowseView = 'leaderboard' | 'mine';

const BROWSE_TABS: TabItem<BrowseView>[] = [
    { id: 'leaderboard', label: 'Leaderboard' },
    { id: 'mine', label: 'My Attempts' },
];

type Props = {
    token?: string;
    horizontalPadding?: string;
    onOpenSeason: (teamId: string, jobId: string) => void;
    onNewTeam: (challenge: ChallengeInstance) => void;
    onUseExistingTeam: (challenge: ChallengeInstance, teamId: string) => void;
    /** Navigates to the challenge's own shareable page (`/teams/challenges/:id`), owned by
     *  TeamBuilder since that's where the route lives. */
    onOpenChallenge: (challenge: ChallengeInstance) => void;
    /** Admin only: open the challenge-template manager (`/teams/admin/challenges`). */
    onManageChallenges: () => void;
};

/**
 * Home for Team Challenges. The live challenge list is the only front door — no subtabs — and
 * clicking a challenge's "Leaderboard" link navigates to that instance's own page. The global
 * "every sim ever played" leaderboard and the signed-in user's full history don't map onto any
 * single challenge, so they're demoted to a quiet "Browse all sims" escape hatch rather than
 * removed outright.
 */
export function SimulationsTab({ token, horizontalPadding, onOpenSeason, onNewTeam, onUseExistingTeam, onOpenChallenge, onManageChallenges }: Props) {
    const { isAdmin } = useAuth();
    const [browsing, setBrowsing] = useState(false);
    const [browseView, setBrowseView] = useState<BrowseView>('leaderboard');

    if (browsing) {
        return (
            <div className={`flex flex-col gap-4 ${horizontalPadding}`}>
                <div className="flex items-center justify-between gap-2">
                    <BackButton onBack={() => setBrowsing(false)} label="Challenges" />
                    <Tabs tabs={BROWSE_TABS} value={browseView} onChange={setBrowseView} />
                </div>

                {browseView === 'leaderboard' && <SimLeaderboard token={token} onOpenSeason={onOpenSeason} />}
                {browseView === 'mine' && <SimHistory token={token} onOpenSeason={onOpenSeason} />}
            </div>
        );
    }

    return (
        <div className={`flex flex-col gap-4 ${horizontalPadding}`}>
            {/* Header */}
            <div className="flex justify-between items-center gap-2">
                <h3 className="text-[16px] font-black text-(--text-primary)">Active Challenges</h3>
                <div className="flex items-center gap-3">
                    {isAdmin && token && (
                        <button
                            type="button"
                            onClick={onManageChallenges}
                            className="flex gap-1 items-center text-[12px] font-bold text-(--text-tertiary) hover:text-(--text-secondary) cursor-pointer transition-colors"
                        >
                            <FaGear className="text-[10px]" /> Manage templates
                        </button>
                    )}
                    <button
                        type="button"
                        onClick={() => setBrowsing(true)}
                        className="flex gap-1 items-center text-[12px] font-bold text-(--text-tertiary) hover:text-(--text-secondary) cursor-pointer transition-colors"
                    >
                        See full leaderboard <FaArrowRight/>
                    </button>
                </div>
            </div>

            {/* Challenges grid */}
            <SimChallenges
                token={token}
                onNewTeam={onNewTeam}
                onUseExistingTeam={onUseExistingTeam}
                onSelectChallenge={onOpenChallenge}
            />

        </div>
    );
}
