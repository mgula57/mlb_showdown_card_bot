import { useRef, useState, type ReactNode } from 'react';
import { SimLeaderboard } from './SimLeaderboard';
import { SimHistory } from './SimHistory';
import { RecentSims } from './RecentSims';
import { SimChallenges } from './SimChallenges';
import { Tabs, type TabItem } from '../../shared/Tabs';
import { useAuth } from '../../auth/AuthContext';
import { SimulationGuideModal } from '../../simulate/SimulationGuideModal';
import type { ChallengeInstance, SimLeaderboardSort } from '../../../api/sim';
import { FaArrowDown } from 'react-icons/fa';
import { FaBook, FaClockRotateLeft, FaGear, FaTrophy, FaQuestion } from 'react-icons/fa6';

type BrowseView = 'leaderboard' | 'mine';

const BROWSE_TABS: TabItem<BrowseView>[] = [
    { id: 'leaderboard', label: 'Leaderboard' },
    { id: 'mine', label: 'My Attempts' },
];

// Only meaningful within the leaderboard view — sits alongside BROWSE_TABS in the same header
// row rather than in its own, since "how it's sorted" and "which list you're looking at" are
// both framing for the same section and read as one control group.
const SORT_TABS: TabItem<SimLeaderboardSort>[] = [
    { id: 'wins', label: 'Best Record', title: 'Ranked by wins' },
    { id: 'efficiency', label: 'Best GM', title: 'Ranked by wins per roster point spent' },
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
    /** Same destination as `onOpenChallenge`, but from a leaderboard row that only has the
     *  instance id on hand (no full `ChallengeInstance` to warm-start with). */
    onOpenChallengeLeaderboard: (instanceId: string) => void;
    /** Admin only: open the challenge-template manager (`/teams/admin/challenges`). */
    onManageChallenges: () => void;
};

/** A large button at the top of the tab — icon, title, and a trailing affordance, matching the
 *  guided-path tiles on the My Teams welcome screen. Either jumps a section into view or (via
 *  `onClick`) triggers something else entirely, like opening the simulation guide. Stacked
 *  (icon over title over affordance) rather than a horizontal row so three of these keep fitting
 *  side by side down to phone widths — a row layout crowds or truncates once titles like
 *  "How do sims work?" share a third of the screen. */
function NavTile({ icon, title, trailingIcon, onClick }: { icon: ReactNode; title: string; trailingIcon?: ReactNode; onClick: () => void }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className="group flex flex-col items-center justify-center gap-1.5 text-center p-2 sm:p-3 rounded-xl border border-(--divider) bg-(--background-secondary) hover:border-(--text-tertiary) transition-colors cursor-pointer"
        >
            <span className="flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-lg bg-(--background-primary) text-(--secondary) text-[13px] sm:text-[15px] shrink-0">
                {icon}
            </span>
            <span className="text-[10px] sm:text-[14px] font-black text-(--text-primary) leading-tight">{title}</span>
            {trailingIcon ?? <FaArrowDown className="text-[10px] sm:text-[12px] text-(--text-tertiary) group-hover:text-(--text-secondary) group-hover:translate-y-0.5 transition-all shrink-0" />}
        </button>
    );
}

/** Jump-to-section tile: scrolls the given section into view rather than switching views, since
 *  challenges and the leaderboard share one page. */
function SectionNavTile({ icon, title, targetRef }: { icon: ReactNode; title: string; targetRef: React.RefObject<HTMLDivElement | null> }) {
    return <NavTile icon={icon} title={title} onClick={() => targetRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })} />;
}

/**
 * Home for Team Challenges: nav tiles, the live challenge grid, and the leaderboard all live on
 * one scrollable page — the tiles jump to a section rather than swapping the view, so the grid
 * and leaderboard are never more than a scroll apart.
 */
export function SimulationsTab({ token, horizontalPadding, onOpenSeason, onNewTeam, onUseExistingTeam, onOpenChallenge, onOpenChallengeLeaderboard, onManageChallenges }: Props) {
    const { isAdmin } = useAuth();
    const [browseView, setBrowseView] = useState<BrowseView>('leaderboard');
    const [sort, setSort] = useState<SimLeaderboardSort>('wins');
    // Once a view has loaded, keep it mounted (just hidden) rather than tearing it down — toggling
    // back would otherwise refetch from scratch and, worse, collapse this whole section down to a
    // loading state's height and back every time, which reads as the page truncating itself.
    // Adjusted during render (not an effect) per React's "you might not need an effect" guidance,
    // since this is purely derived from `browseView` with no external system to synchronize.
    const [visitedBrowseViews, setVisitedBrowseViews] = useState<Set<BrowseView>>(() => new Set([browseView]));
    if (!visitedBrowseViews.has(browseView)) {
        setVisitedBrowseViews(prev => new Set(prev).add(browseView));
    }
    const recentSimsRef = useRef<HTMLDivElement>(null);
    const leaderboardRef = useRef<HTMLDivElement>(null);
    const [showGuide, setShowGuide] = useState(false);

    return (
        <div className={`flex flex-col gap-8 ${horizontalPadding}`}>
            {/* Nav tiles */}
            <div className="grid grid-cols-3 gap-3">
                <SectionNavTile icon={<FaClockRotateLeft />} title="Recent Sims" targetRef={recentSimsRef} />
                <SectionNavTile icon={<FaTrophy />} title="Leaderboard" targetRef={leaderboardRef} />
                <NavTile
                    icon={<FaBook />}
                    title="How do sims work?"
                    trailingIcon={<FaQuestion className="text-[10px] sm:text-[12px] text-(--text-tertiary) group-hover:text-(--text-secondary) group-hover:translate-y-0.5 transition-all shrink-0" />}
                    onClick={() => setShowGuide(true)}
                />
            </div>

            {showGuide && <SimulationGuideModal onClose={() => setShowGuide(false)} />}

            {/* Challenges grid */}
            <div className="flex flex-col gap-4">
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

            {/* Recent Sims — quick snapshot of your own and the community's latest runs */}
            <div ref={recentSimsRef}>
                <RecentSims token={token} onOpenSeason={onOpenSeason} />
            </div>

            {/* Leaderboard */}
            <div ref={leaderboardRef} className="flex flex-col gap-4">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                    <h3 className="flex items-center gap-1.5 text-[16px] font-black text-(--text-primary)">
                        <FaTrophy className="text-[13px] text-(--showdown-blue)" /> Leaderboard
                    </h3>
                    <div className="flex items-center gap-3">
                        <Tabs tabs={SORT_TABS} value={sort} onChange={setSort} size="sm" />
                        <Tabs tabs={BROWSE_TABS} value={browseView} onChange={setBrowseView} />
                    </div>
                </div>

                <div hidden={browseView !== 'leaderboard'}>
                    {visitedBrowseViews.has('leaderboard') && (
                        <SimLeaderboard token={token} onOpenSeason={onOpenSeason} onOpenChallenge={onOpenChallengeLeaderboard} sort={sort} />
                    )}
                </div>
                <div hidden={browseView !== 'mine'}>
                    {visitedBrowseViews.has('mine') && <SimHistory token={token} onOpenSeason={onOpenSeason} sort={sort} />}
                </div>
            </div>
        </div>
    );
}
