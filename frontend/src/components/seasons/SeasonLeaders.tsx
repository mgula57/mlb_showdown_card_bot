import { useState, useEffect, useRef } from "react";
import { FaTrophy } from "react-icons/fa6";
import { fetchSeasonLeaders, type LeadersGroup, type PlayerLeader } from "../../api/mlbAPI";
import { fetchCardById, type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { fetchCardData, type CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import { CardSource } from "../../types/cardSource";
import { CardItemFromCardDatabaseRecord, CardItemSkeleton } from "../cards/CardItem";
import { CardDetail } from "../cards/CardDetail";
import { Modal } from "../shared/Modal";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { Heading } from "../shared/Heading";
import { Eyebrow } from "../shared/Eyebrow";
import { Tabs, type TabItem } from "../shared/Tabs";
import { Plate } from '../shared/Plate';

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

// TODO: replace hard-coded IDs with a general two-way player detection strategy
const TWO_WAY_PLAYER_IDS = new Set([660271]); // Ohtani

/** Returns the CardMap key for a player in a given category group. */
const cardKey = (id: string, group: 'hitting' | 'pitching'): string => {
    if (TWO_WAY_PLAYER_IDS.has(Number(id))) return `${id}-${group === 'hitting' ? 'H' : 'P'}`;
    return id;
};

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

    const [leaderGroups, setLeaderGroups] = useState<LeadersGroup[]>([]);
    const [cardMap, setCardMap] = useState<Record<string, CardDatabaseRecord>>({});
    const [isLoadingLeaders, setIsLoadingLeaders] = useState(false);
    const [isLoadingCards, setIsLoadingCards] = useState(false);
    const [filterGroup, setFilterGroup] = useState<FilterGroup>('hitting');
    const [selectedModalCard, setSelectedModalCard] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [isLoadingModalCard, setIsLoadingModalCard] = useState(false);

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

        setIsLoadingCards(true);
        fetchCardData(CardSource.BOT, {
            mlb_id: uniqueIds,
            year: season,
            showdown_set: showdownSet,
            limit: 200
        })
            .then(records => {
                const map: Record<string, CardDatabaseRecord> = {};
                records.forEach(record => {
                    const id = record.mlb_id;
                    if (!id) {
                        console.warn('Record is missing mlb_id:', record);
                        return;
                    }
                    if (TWO_WAY_PLAYER_IDS.has(Number(id))) {
                        map[`${id}-${record.is_pitcher ? 'P' : 'H'}`] = record;
                    } else {
                        map[String(id)] = record;
                    }
                });
                console.log('Fetched leader cards from card_bot:', map);
                setCardMap(map);
            })
            .catch(err => console.error('Failed to fetch leader cards:', err))
            .finally(() => setIsLoadingCards(false));
    }, [leaderGroups, season, showdownSet]);

    // Lazily fetch the full nested card for the detail modal (card_bot rows are flat/summary only)
    const handleCardClick = (record: CardDatabaseRecord) => {
        if (isLoadingModalCard) return;
        setIsLoadingModalCard(true);
        fetchCardById(record.id, CardSource.BOT)
            .then(res => setSelectedModalCard(res))
            .catch(err => console.error('Failed to fetch full card:', err))
            .finally(() => setIsLoadingModalCard(false));
    };

    // ==========================================================================
    // MARK: - Render Helpers
    // ==========================================================================

    const renderLeaderCard = (entry: PlayerLeader | null, categoryDef: CategoryDef | undefined, i: number) => {
        const card = entry?.person?.id && categoryDef
            ? cardMap[cardKey(String(entry.person.id), categoryDef.group)]
            : undefined;
        const isPlaceholder = !entry;
        const statValue = entry?.value ?? '';
        const rank = entry?.rank;
        const name = entry?.person?.full_name ?? '';
        const teamAbbr = entry?.team?.abbreviation ?? '';
        
        return (
            <div key={`${entry?.value ?? i}-${entry?.person?.id ?? ''}`} className="flex flex-col gap-1.5 shrink-0 w-80 lg:w-auto">
                {/* Rank / stat row */}
                <div className="flex items-center px-1.5 space-x-1.5">
                    <span className={`text-xs font-bold tabular-nums text-(--text-tertiary)`}>
                        {rank != null ? `#${rank}` : ''}.
                    </span>
                    <div className="flex items-center gap-1 min-w-0">
                        {teamAbbr && (
                            <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>
                                {teamAbbr}
                            </span>
                        )}
                        {name && (
                            <span className={`text-xs font-semibold truncate max-w-28 text-(--text-secondary)`} title={name}>
                                {name.slice(name.indexOf(' ') + 1) || name}
                            </span>
                        )}
                        {statValue && categoryDef && (
                            <span className={`text-xs font-bold tabular-nums text-(--text-primary)`}>
                                {statValue}
                            </span>
                        )}
                    </div>
                </div>

                {/* Card */}
                {!card && isLoadingCards ? (
                    <CardItemSkeleton className="max-w-full min-w-72" />
                ) : (
                    <CardItemFromCardDatabaseRecord
                        card={card}
                        className={[
                            'max-w-96 w-full',
                            card ? 'cursor-pointer' : 'pointer-events-none',
                            isPlaceholder ? 'animate-pulse opacity-40' : '',
                            !card && isLoadingCards ? 'animate-pulse opacity-60' : '',
                        ].join(' ')}
                        onClick={card ? () => handleCardClick(card) : undefined}
                    />
                )}
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

    const filterOptions: TabItem<FilterGroup>[] = [
        // { id: 'all', label: 'All' },
        { id: 'hitting', label: 'Batting' },
        { id: 'pitching', label: 'Pitching' },
    ];

    return (
        <div className="pb-24">
            {/* Header */}
            <div className="flex items-center justify-between gap-4 mb-5 flex-wrap lg:pr-6">
                <div className="flex items-center gap-2">
                    <FaTrophy className={`text-sm text-(--gold)`} />
                    <Heading level="section">Season Leaders</Heading>
                </div>

                <Tabs size="sm" tabs={filterOptions} value={filterGroup} onChange={setFilterGroup} />
            </div>

            {/* Loading state (first load, no data yet) */}
            {isLoadingLeaders && leaderGroups.length === 0 && (
                <div className="space-y-8">
                    {visibleCategories.slice(0, 6).map((cat) => (
                        <div key={cat.id}>
                            <div className="h-4 w-32 rounded-plate mb-3 animate-pulse bg-(--background-tertiary)" />
                            <div className="flex gap-3 overflow-x-auto scrollbar-hide -mx-6 px-6 lg:mx-0 lg:px-0 lg:grid lg:grid-cols-3">
                                {[0, 1, 2].map(i => (
                                    <div
                                        key={i}
                                        className={`shrink-0 w-72 lg:w-auto h-48 rounded-card animate-pulse bg-(--background-tertiary)`}
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
                                    <Eyebrow>{catDef.label}</Eyebrow>
                                    <Plate size="sm">{catDef.abbrev}</Plate>
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
                <Modal onClose={() => setSelectedModalCard(null)} isVisible={!!selectedModalCard} size='xl'>
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
