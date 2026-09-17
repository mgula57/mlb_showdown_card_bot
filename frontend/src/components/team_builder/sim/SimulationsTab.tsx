import { useRef, useState, type ReactNode } from 'react';
import { SimLeaderboard } from './SimLeaderboard';
import { SimHistory } from './SimHistory';
import { SimChallenges } from './SimChallenges';
import { Tabs, type TabItem } from '../../shared/Tabs';
import { useAuth } from '../../auth/AuthContext';
import type { ChallengeInstance } from '../../../api/sim';
import { FaArrowRight } from 'react-icons/fa';
import { FaGear, FaListCheck, FaTrophy } from 'react-icons/fa6';

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

/** A large jump-to-section button at the top of the tab — icon, title, and an arrow affordance,
 *  matching the guided-path tiles on the My Teams welcome screen. Scrolls the given section into
 *  view rather than switching views, since challenges and the leaderboard now share one page. */
function NavTile({ icon, title, targetRef }: { icon: ReactNode; title: string; targetRef: React.RefObject<HTMLDivElement | null> }) {
    return (
        <button
            type="button"
            onClick={() => targetRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            className="group flex items-center justify-between gap-3 text-left p-4 rounded-xl border border-(--divider) bg-(--background-secondary) hover:border-(--text-tertiary) transition-colors cursor-pointer"
        >
            <span className="flex items-center gap-3">
                <span className="flex items-center justify-center w-9 h-9 rounded-lg bg-(--background-primary) text-(--secondary) text-[15px] shrink-0">
                    {icon}
                </span>
                <span className="text-[14px] font-black text-(--text-primary)">{title}</span>
            </span>
            <FaArrowRight className="text-[12px] text-(--text-tertiary) group-hover:text-(--text-secondary) group-hover:translate-x-0.5 transition-all shrink-0" />
        </button>
    );
}

/**
 * Home for Team Challenges: nav tiles, the live challenge grid, and the leaderboard all live on
 * one scrollable page — the tiles jump to a section rather than swapping the view, so the grid
 * and leaderboard are never more than a scroll apart.
 */
export function SimulationsTab({ token, horizontalPadding, onOpenSeason, onNewTeam, onUseExistingTeam, onOpenChallenge, onManageChallenges }: Props) {
    const { isAdmin } = useAuth();
    const [browseView, setBrowseView] = useState<BrowseView>('leaderboard');
    const challengesRef = useRef<HTMLDivElement>(null);
    const leaderboardRef = useRef<HTMLDivElement>(null);

    return (
        <div className={`flex flex-col gap-8 ${horizontalPadding}`}>
            {/* Nav tiles */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <NavTile icon={<FaListCheck />} title="Active Challenges" targetRef={challengesRef} />
                <NavTile icon={<FaTrophy />} title="Leaderboard" targetRef={leaderboardRef} />
            </div>

            {/* Challenges grid */}
            <div ref={challengesRef} className="flex flex-col gap-4">
                <div className="flex justify-between items-center gap-2">
                    <h3 className="text-[16px] font-black text-(--text-primary)">Active Challenges</h3>
                    {isAdmin && token && (
                        <button
                            type="button"
                            onClick={onManageChallenges}
                            className="flex gap-1 items-center text-[12px] font-bold text-(--text-tertiary) hover:text-(--text-secondary) cursor-pointer transition-colors"
                        >
                            <FaGear className="text-[10px]" /> Manage templates
                        </button>
                    )}
                </div>

                <SimChallenges
                    token={token}
                    onNewTeam={onNewTeam}
                    onUseExistingTeam={onUseExistingTeam}
                    onSelectChallenge={onOpenChallenge}
                />
            </div>

            {/* Leaderboard */}
            <div ref={leaderboardRef} className="flex flex-col gap-4">
                <div className="flex items-center justify-between gap-2">
                    <h3 className="flex items-center gap-1.5 text-[16px] font-black text-(--text-primary)">
                        <FaTrophy className="text-[13px] text-(--showdown-blue)" /> Leaderboard
                    </h3>
                    <Tabs tabs={BROWSE_TABS} value={browseView} onChange={setBrowseView} />
                </div>

                {browseView === 'leaderboard' && <SimLeaderboard token={token} onOpenSeason={onOpenSeason} />}
                {browseView === 'mine' && <SimHistory token={token} onOpenSeason={onOpenSeason} />}
            </div>
        </div>
    );
}
