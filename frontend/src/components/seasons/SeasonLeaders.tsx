import { useState, useEffect, useRef } from "react";
import { FaTrophy } from "react-icons/fa6";
import { fetchSeasonLeaders, type LeadersGroup, type PlayerLeader } from "../../api/mlbAPI";
import { buildCardsFromIds, type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { CardItemFromCard } from "../cards/CardItem";
import { CardDetail } from "../cards/CardDetail";
import { Modal } from "../shared/Modal";
import { useTheme } from "../shared/SiteSettingsContext";

// =============================================================================
// MARK: - Category Definitions
// =============================================================================

type CategoryDef = {
    id: string;
    /** Exact camelCase value returned by the MLB Stats API leaderCategory field */
    apiKey: string;
    label: string;
    abbrev: string;
    group: 'hitting' | 'pitching';
};

const BATTING_CATEGORIES: CategoryDef[] = [
    { id: 'ON_BASE_PLUS_SLUGGING',        apiKey: 'onBasePlusSlugging',          label: 'OPS',             abbrev: 'OPS',  group: 'hitting' },
    { id: 'HOME_RUNS',                    apiKey: 'homeRuns',                    label: 'Home Runs',       abbrev: 'HR',   group: 'hitting' },
    { id: 'BATTING_AVERAGE',              apiKey: 'battingAverage',              label: 'Batting Average', abbrev: 'AVG',  group: 'hitting' },
    { id: 'ON_BASE_PERCENTAGE',           apiKey: 'onBasePercentage',            label: 'On-Base %',       abbrev: 'OBP',  group: 'hitting' },
    { id: 'SLUGGING_PERCENTAGE',          apiKey: 'sluggingPercentage',          label: 'Slugging %',      abbrev: 'SLG',  group: 'hitting' },
    { id: 'HITS',                         apiKey: 'hits',                        label: 'Hits',            abbrev: 'H',    group: 'hitting' },
    { id: 'STOLEN_BASES',                 apiKey: 'stolenBases',                 label: 'Stolen Bases',    abbrev: 'SB',   group: 'hitting' },
    { id: 'RUNS',                         apiKey: 'runs',                        label: 'Runs Scored',     abbrev: 'R',    group: 'hitting' },
    { id: 'DOUBLES',                      apiKey: 'doubles',                     label: 'Doubles',         abbrev: '2B',   group: 'hitting' },
    { id: 'EXTRA_BASE_HITS',              apiKey: 'extraBaseHits',               label: 'Extra-Base Hits', abbrev: 'XBH',  group: 'hitting' },
    { id: 'TOTAL_BASES',                  apiKey: 'totalBases',                  label: 'Total Bases',     abbrev: 'TB',   group: 'hitting' },
    { id: 'WALKS',                        apiKey: 'walks',                       label: 'Walks',           abbrev: 'BB',   group: 'hitting' },
    { id: 'RUNS_BATTED_IN',               apiKey: 'runsBattedIn',                label: 'RBI',             abbrev: 'RBI',  group: 'hitting' },
];

const PITCHING_CATEGORIES: CategoryDef[] = [
    { id: 'EARNED_RUN_AVERAGE',           apiKey: 'earnedRunAverage',            label: 'ERA',             abbrev: 'ERA',  group: 'pitching' },
    { id: 'WALKS_HITS_PER_INNING_PITCHED',apiKey: 'walksAndHitsPerInningPitched',label: 'WHIP',            abbrev: 'WHIP', group: 'pitching' },
    { id: 'STRIKEOUTS',                   apiKey: 'strikeouts',                  label: 'Strikeouts',      abbrev: 'K',    group: 'pitching' },
    { id: 'BASEBALL_WINS',                apiKey: 'wins',                        label: 'Wins',            abbrev: 'W',    group: 'pitching' },
    { id: 'SAVES',                        apiKey: 'saves',                       label: 'Saves',           abbrev: 'SV',   group: 'pitching' },
    { id: 'INNINGS_PITCHED',              apiKey: 'inningsPitched',              label: 'Innings Pitched', abbrev: 'IP',   group: 'pitching' },
    { id: 'STRIKEOUTS_PER_9_INN',         apiKey: 'strikeoutsPer9Inn',           label: 'K/9',             abbrev: 'K/9',  group: 'pitching' },
    { id: 'STRIKEOUT_WALK_RATIO',         apiKey: 'strikeoutWalkRatio',          label: 'K/BB Ratio',      abbrev: 'K/BB', group: 'pitching' },
];

const ALL_CATEGORIES: CategoryDef[] = [...BATTING_CATEGORIES, ...PITCHING_CATEGORIES];

type FilterGroup = 'all' | 'hitting' | 'pitching';

// =============================================================================
// MARK: - Props
// =============================================================================

type SeasonLeadersProps = {
    seasonId: string;
    season: number;
    showdownSet: string;
    sportId?: number;
    isActive: boolean;
};

// =============================================================================
// MARK: - Component
// =============================================================================

export default function SeasonLeaders({ seasonId, season, showdownSet, sportId, isActive }: SeasonLeadersProps) {
    const { isDark } = useTheme();

    const [leaderGroups, setLeaderGroups] = useState<LeadersGroup[]>([]);
    const [cardMap, setCardMap] = useState<Record<string, ShowdownBotCardAPIResponse>>({});
    const [isLoadingLeaders, setIsLoadingLeaders] = useState(false);
    const [isLoadingCards, setIsLoadingCards] = useState(false);
    const [filterGroup, setFilterGroup] = useState<FilterGroup>('hitting');
    const [selectedModalCard, setSelectedModalCard] = useState<ShowdownBotCardAPIResponse | null>(null);

    const hasLoadedRef = useRef(false);
    const lastSeasonIdRef = useRef<string | null>(null);

    // Fetch leaders when tab first becomes active or season/sport changes
    useEffect(() => {
        if (!isActive) return;

        const seasonChanged = lastSeasonIdRef.current !== seasonId;
        if (hasLoadedRef.current && !seasonChanged) return;

        lastSeasonIdRef.current = seasonId;
        hasLoadedRef.current = false;

        setLeaderGroups([]);
        setCardMap({});
        setIsLoadingLeaders(true);

        const hittingCategoryIds = BATTING_CATEGORIES.map(c => c.id);
        const pitchingCategoryIds = PITCHING_CATEGORIES.map(c => c.id);

        Promise.all([
            fetchSeasonLeaders(seasonId, hittingCategoryIds, ['hitting'], 5),
            fetchSeasonLeaders(seasonId, pitchingCategoryIds, ['pitching'], 5),
        ])
            .then(([hittingRes, pitchingRes]) => {
                const combined = [...hittingRes.leaders, ...pitchingRes.leaders];
                // Deduplicate by leader_category
                const seen = new Set<string>();
                const deduped = combined.filter(g => {
                    const key = g.leader_category ?? '';
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                });
                setLeaderGroups(deduped);
                console.log('Fetched season leaders:', deduped);
                hasLoadedRef.current = true;
            })
            .catch(err => {
                console.error('Failed to fetch season leaders:', err);
                hasLoadedRef.current = true;
            })
            .finally(() => setIsLoadingLeaders(false));
    }, [isActive, seasonId, sportId]);

    // Build card map when leader groups or showdown set changes
    useEffect(() => {
        if (leaderGroups.length === 0) return;

        const allEntries: PlayerLeader[] = leaderGroups.flatMap(g => g.leaders ?? []);
        const uniqueIds = Array.from(
            new Set(allEntries.map(e => String(e.person?.id)).filter(Boolean))
        );
        if (uniqueIds.length === 0) return;

        const cardSettings = {
            year: season,
            set: showdownSet,
            stat_highlights_type: 'ALL',
        };

        setIsLoadingCards(true);
        buildCardsFromIds(uniqueIds, season, cardSettings, true)
            .then(res => {
                if (!res.cards) return;
                const map: Record<string, ShowdownBotCardAPIResponse> = {};
                res.cards.forEach(cardRes => {
                    if (cardRes.card?.mlb_id) {
                        map[String(cardRes.card.mlb_id)] = cardRes;
                    }
                });
                console.log('Built leader cards:', map);
                setCardMap(map);
            })
            .catch(err => console.error('Failed to build leader cards:', err))
            .finally(() => setIsLoadingCards(false));
    }, [leaderGroups, showdownSet]);

    // ==========================================================================
    // MARK: - Render Helpers
    // ==========================================================================

    const renderLeaderCard = (entry: PlayerLeader | null, categoryDef: CategoryDef | undefined, i: number) => {
        const cardResponse = entry?.person?.id ? cardMap[String(entry.person.id)] : undefined;
        const card = cardResponse?.card ?? undefined;
        const isPlaceholder = !entry;
        const statValue = entry?.value ?? '';
        const rank = entry?.rank;
        const name = entry?.person?.full_name ?? '';
        const teamAbbr = entry?.team?.abbreviation ?? '';
        
        return (
            <div key={entry?.rank ?? i} className="flex flex-col gap-1.5 shrink-0 w-80 lg:w-auto">
                {/* Rank / stat row */}
                <div className="flex items-center px-1.5 space-x-1.5">
                    <span className={`text-xs font-bold tabular-nums ${isDark ? 'text-neutral-400' : 'text-neutral-500'}`}>
                        {rank != null ? `#${rank}` : ''}.
                    </span>
                    <div className="flex items-center gap-1 min-w-0">
                        {teamAbbr && (
                            <span className={`text-[10px] font-semibold uppercase tracking-wide ${isDark ? 'text-neutral-500' : 'text-neutral-400'}`}>
                                {teamAbbr}
                            </span>
                        )}
                        {name && (
                            <span className={`text-xs font-semibold truncate max-w-28 ${isDark ? 'text-neutral-300' : 'text-neutral-600'}`} title={name}>
                                {name.split(' ').at(-1)}
                            </span>
                        )}
                        {statValue && categoryDef && (
                            <span className={`text-xs font-black tabular-nums ${isDark ? 'text-white' : 'text-black'}`}>
                                {statValue}
                            </span>
                        )}
                    </div>
                </div>

                {/* Card */}
                <CardItemFromCard
                    card={card}
                    className={[
                        'max-w-full w-full',
                        card ? 'cursor-pointer' : 'pointer-events-none',
                        isPlaceholder ? 'animate-pulse opacity-40' : '',
                        !card && isLoadingCards ? 'animate-pulse opacity-60' : '',
                    ].join(' ')}
                    onClick={card ? () => setSelectedModalCard(cardResponse!) : undefined}
                />
            </div>
        );
    };

    const visibleCategories = ALL_CATEGORIES.filter(
        c => filterGroup === 'all' || c.group === filterGroup
    );

    const groupsByCategory = Object.fromEntries(
        leaderGroups.map(g => [g.leader_category ?? '', g])
    );

    // ==========================================================================
    // MARK: - Render
    // ==========================================================================

    const filterOptions: { value: FilterGroup; label: string }[] = [
        // { value: 'all', label: 'All' },
        { value: 'hitting', label: 'Batting' },
        { value: 'pitching', label: 'Pitching' },
    ];

    return (
        <div className="pb-24">
            {/* Header */}
            <div className="flex items-center justify-between gap-4 mb-5 flex-wrap lg:pr-6">
                <div className="flex items-center gap-2">
                    <FaTrophy className={`text-sm ${isDark ? 'text-yellow-400' : 'text-yellow-500'}`} />
                    <span className={`text-sm font-bold uppercase tracking-wide ${isDark ? 'text-neutral-400' : 'text-neutral-500'}`}>
                        Season Leaders
                    </span>
                </div>

                {/* Filter pills */}
                <div className={`flex items-center gap-1 p-1 rounded-lg ${isDark ? 'bg-neutral-800' : 'bg-neutral-100'}`}>
                    {filterOptions.map(opt => (
                        <button
                            key={opt.value}
                            type="button"
                            onClick={() => setFilterGroup(opt.value)}
                            className={[
                                'px-3 py-1 text-xs font-semibold rounded-md transition cursor-pointer',
                                filterGroup === opt.value
                                    ? isDark
                                        ? 'bg-(--background-primary) text-white shadow'
                                        : 'bg-white text-black shadow'
                                    : isDark
                                        ? 'text-neutral-400 hover:text-neutral-200'
                                        : 'text-neutral-500 hover:text-neutral-800',
                            ].join(' ')}
                        >
                            {opt.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Loading state (first load, no data yet) */}
            {isLoadingLeaders && leaderGroups.length === 0 && (
                <div className="space-y-8">
                    {visibleCategories.slice(0, 6).map((cat) => (
                        <div key={cat.id}>
                            <div className={`h-4 w-32 rounded mb-3 animate-pulse ${isDark ? 'bg-neutral-700' : 'bg-neutral-200'}`} />
                            <div className="flex gap-3 overflow-x-auto scrollbar-hide -mx-6 px-6 lg:mx-0 lg:px-0 lg:grid lg:grid-cols-3">
                                {[0, 1, 2].map(i => (
                                    <div
                                        key={i}
                                        className={`shrink-0 w-72 lg:w-auto h-48 rounded-xl animate-pulse ${isDark ? 'bg-neutral-800' : 'bg-neutral-200'}`}
                                    />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Category sections */}
            {!isLoadingLeaders && (
                <div className="space-y-8">
                    {visibleCategories.map((catDef) => {
                        const group = groupsByCategory[catDef.apiKey];
                        // Show placeholder entries while loading or if no data for this category
                        const entries: (PlayerLeader | null)[] = group
                            ? (group.leaders ?? []).slice(0, 6)
                            : [null, null, null];

                        // Pad to 3 if fewer entries
                        while (entries.length < 3) entries.push(null);

                        return (
                            <div key={catDef.id}>
                                {/* Category header */}
                                <div className="flex items-center gap-2 mb-3 lg:pr-6">
                                    <span className={`text-xs font-bold uppercase tracking-wide ${isDark ? 'text-neutral-400' : 'text-neutral-500'}`}>
                                        {catDef.label}
                                    </span>
                                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${isDark ? 'bg-neutral-700 text-neutral-400' : 'bg-neutral-100 text-neutral-500'}`}>
                                        {catDef.abbrev}
                                    </span>
                                </div>

                                {/* 3 cards */}
                                <div className="flex gap-3 overflow-x-scroll scrollbar-hide -mx-6 px-6 lg:mx-0 lg:px-0">
                                    {entries.map((entry, i) => renderLeaderCard(entry, catDef, i))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Modal for selected card */}
            <div className={selectedModalCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={() => setSelectedModalCard(null)} isVisible={!!selectedModalCard}>
                    <CardDetail
                        showdownBotCardData={selectedModalCard!}
                        hideTrendGraphs={true}
                        context="home"
                        parent='home'
                    />
                </Modal>
            </div>
            
        </div>
    );
}
