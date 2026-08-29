import { useEffect, useState, type ReactNode } from 'react';
import { fetchPublicTeams, type TeamSummary } from '../../api/userTeams';
import { TeamShelf } from './TeamShelf';
import { TeamPreviewCard, TeamPreviewCardSkeleton } from './TeamPreviewCard';
import {
    FaPlus, FaArrowRight, FaChevronRight,
    FaGlobe, FaClockRotateLeft,
} from 'react-icons/fa6';

type WelcomeTab = 'simulations' | 'community' | 'historical';

type TeamBuilderWelcomeProps = {
    /** Horizontal padding class shared with the rest of the Team Builder page. */
    px: string;
    /** Opens the New Team modal. */
    onCreate: () => void;
    /** Switches the Team Builder to another tab. */
    onGoToTab: (tab: WelcomeTab) => void;
    /** Opens a community team in the editor (read-only). */
    onOpenTeam: (team: TeamSummary) => void;
};

type Path = {
    tab: WelcomeTab;
    icon: ReactNode;
    title: string;
    blurb: string;
};

const PATHS: Path[] = [
    {
        tab: 'community',
        icon: <FaGlobe />,
        title: 'Explore Community Teams',
        blurb: 'Browse rosters other managers have built and fork your favorites.',
    },
    {
        tab: 'historical',
        icon: <FaClockRotateLeft />,
        title: 'Browse Historical Rosters',
        blurb: 'Turn any real MLB team or All-Star squad into a Showdown lineup.',
    },
];

/**
 * First-run experience for the "My Teams" tab when a signed-in user has no teams yet.
 * A gradient hero with the primary "create" action, three guided paths into the other
 * tabs, and a shelf of community teams for inspiration (clickable straight into the editor).
 */
export function TeamBuilderWelcome({ px, onCreate, onGoToTab, onOpenTeam }: TeamBuilderWelcomeProps) {
    const [inspiration, setInspiration] = useState<TeamSummary[] | null>(null);

    useEffect(() => {
        let cancelled = false;
        fetchPublicTeams('user', 24, 0)
            .then(list => {
                if (cancelled) return;
                const picks = list
                    .filter(t => !t.is_drafting && t.roster_count > 0)
                    .sort((a, b) => b.total_points - a.total_points)
                    .slice(0, 10);
                setInspiration(picks);
            })
            .catch(() => { if (!cancelled) setInspiration([]); });
        return () => { cancelled = true; };
    }, []);

    return (
        <div className="flex flex-col gap-6">
            {/* Hero */}
            <div className={px}>
                <div
                    className="relative overflow-hidden rounded-2xl border-4 border-transparent p-6 sm:p-8"
                    style={{
                        backgroundImage:
                            'linear-gradient(var(--background-secondary), var(--background-secondary)), linear-gradient(135deg, rgb(59,130,246), rgb(239,68,68))',
                        backgroundOrigin: 'border-box',
                        backgroundClip: 'padding-box, border-box',
                    }}
                >
                    <img
                        src="/images/teams/Field.png"
                        alt=""
                        aria-hidden
                        draggable={false}
                        className="pointer-events-none absolute inset-x-0 top-0 w-full h-[calc(100%+10rem)] object-cover object-top opacity-15 -translate-y-18"
                    />
                    <div className="relative flex flex-col gap-4 max-w-xl">
                        <div>
                            <h2 className="text-[22px] sm:text-[26px] font-black text-(--text-primary) leading-tight">
                                Your dugout is empty
                            </h2>
                            <p className="text-[13px] text-(--text-secondary) mt-1.5">
                                Draft a roster using ANY player and ANY season in MLB History. Start from a blank slate or take inspiration from the
                                community below.
                            </p>
                        </div>
                        <button
                            type="button"
                            onClick={onCreate}
                            className="self-start flex items-center gap-2 px-5 py-3 rounded-xl text-[14px] font-black text-white bg-linear-to-r from-blue-500 to-red-500 hover:opacity-90 transition-opacity cursor-pointer"
                        >
                            <FaPlus className="text-[12px]" />
                            Create your first team
                        </button>
                    </div>
                </div>
            </div>

            {/* Guided paths */}
            <div className={`grid grid-cols-1 sm:grid-cols-2 gap-3 ${px}`}>
                {PATHS.map(path => (
                    <button
                        key={path.tab}
                        type="button"
                        onClick={() => onGoToTab(path.tab)}
                        className="group flex flex-col gap-2 text-left p-4 rounded-xl border border-(--divider) bg-(--background-secondary) hover:border-(--text-tertiary) transition-colors cursor-pointer"
                    >
                        <div className="flex items-center justify-between">
                            <span className="flex items-center justify-center w-9 h-9 rounded-lg bg-(--background-primary) text-(--secondary) text-[15px]">
                                {path.icon}
                            </span>
                            <FaArrowRight className="text-[12px] text-(--text-tertiary) group-hover:text-(--text-secondary) group-hover:translate-x-0.5 transition-all" />
                        </div>
                        <h3 className="text-[14px] font-black text-(--text-primary)">{path.title}</h3>
                        <p className="text-[12px] text-(--text-secondary)">{path.blurb}</p>
                    </button>
                ))}
            </div>

            {/* Inspiration shelf */}
            {inspiration === null ? (
                <TeamShelf title="Get Inspired" subtitle="Popular community teams" className={px}>
                    {Array.from({ length: 6 }).map((_, i) => <TeamPreviewCardSkeleton key={i} />)}
                </TeamShelf>
            ) : inspiration.length > 0 ? (
                <TeamShelf
                    title="Get Inspired"
                    subtitle="Popular community teams"
                    className={px}
                    onSeeAll={() => onGoToTab('community')}
                >
                    {inspiration.map(team => (
                        <TeamPreviewCard key={team.team_id} team={team} onClick={() => onOpenTeam(team)} />
                    ))}
                </TeamShelf>
            ) : (
                <button
                    type="button"
                    onClick={() => onGoToTab('community')}
                    className={`flex items-center gap-1.5 text-[12px] font-bold text-(--text-secondary) hover:text-(--text-primary) cursor-pointer ${px}`}
                >
                    Browse community teams <FaChevronRight className="text-[9px]" />
                </button>
            )}
        </div>
    );
}

export default TeamBuilderWelcome;
