import { useState, useEffect, useRef, useCallback } from "react";
import { type CardDatabaseRecord, fetchCardData } from "../../api/card_db/cardDatabase";
import { CardDetail } from "./CardDetail";
import { type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { Modal } from "../shared/Modal";
import { useSiteSettings } from "../shared/SiteSettingsContext";
import {
    FaFilter, FaBaseballBall, FaArrowUp, FaArrowDown, FaTimes,
    FaDollarSign, FaMitten, FaCalendarAlt, FaChevronCircleRight, FaChevronCircleLeft
} from "react-icons/fa";
import { FaArrowRotateRight } from "react-icons/fa6";
import { snakeToTitleCase } from "../../functions/text";
import { FaO, FaI } from "react-icons/fa6";

// Filter components
import FormInput from "../customs/FormInput";
import MultiSelect from "../shared/MultiSelect";
import FormDropdown from "../customs/FormDropdown";
import FormSection from "../customs/FormSection";
import type { SelectOption } from '../shared/CustomSelect';
import { CardItem } from "./CardItem";
import { FaPersonRunning } from "react-icons/fa6";
import RangeFilter from "../customs/RangeFilter";

import { TeamHierarchy } from "./TeamHierarchy";
import { fetchTeamHierarchy, type TeamHierarchyRecord } from '../../api/card_db/cardDatabase';

type ShowdownCardExploreProps = {
    showdownCards?: CardDatabaseRecord[] | null;
    className?: string;
};

// --------------------------------------------
// MARK: - Filters
// --------------------------------------------

/** State for the custom card form */
interface FilterSelections {

    // Sorting
    sort_by?: string; // e.g., "Points"
    sort_direction?: string; // "asc" or "desc"

    // Real Stats
    min_pa?: number;
    max_pa?: number;
    min_real_ip?: number;
    max_real_ip?: number;
    include_small_sample_size?: string[]; // e.g., ["true", "false"]

    // Showdown Min/Max
    min_points?: number;
    max_points?: number;
    min_speed?: number;
    max_speed?: number;
    min_ip?: number;
    max_ip?: number;

    icons?: string[]; 

    min_command?: number;
    max_command?: number;
    min_outs?: number;
    max_outs?: number;

    min_year?: number;
    max_year?: number;

    organization?: string[]; // e.g., ["MLB", "NGL"]
    league?: string[]; // e.g., ["MLB", "NEGRO LEAGUES"]
    team?: string[]; // e.g., ["Yankees", "Red Sox"]
    is_multi_team?: string[];

    player_type?: string[]; // e.g., ["Hitter", "Pitcher"]
    positions?: string[]; // e.g., ["C", "1B"]
    hand?: string[]; // e.g., ["R", "L", "S"]

    is_chart_outlier?: string[];
}

const DEFAULT_FILTER_SELECTIONS: FilterSelections = {
    include_small_sample_size: ["false"],
    sort_by: "points",
    sort_direction: "desc",
    organization: ["MLB"],
};

const SORT_OPTIONS: SelectOption[] = [
    { value: 'points', label: 'Points', icon: <FaDollarSign /> },
    { value: 'year', label: 'Year', icon: <FaCalendarAlt /> },
    { value: 'speed', label: 'Speed', icon: <FaPersonRunning /> },
    { value: 'ip', label: 'IP', icon: <FaI /> },
    { value: 'command', label: 'Control/Onbase', icon: <FaBaseballBall /> },
    { value: 'outs', label: 'Outs', icon: <FaO /> },

    { value: 'positions_and_defense_c', label: 'Defense (CA)', icon: <FaMitten /> },
    { value: 'positions_and_defense_1b', label: 'Defense (1B)', icon: <FaMitten /> },
    { value: 'positions_and_defense_2b', label: 'Defense (2B)', icon: <FaMitten /> },
    { value: 'positions_and_defense_3b', label: 'Defense (3B)', icon: <FaMitten /> },
    { value: 'positions_and_defense_ss', label: 'Defense (SS)', icon: <FaMitten /> },
    { value: 'positions_and_defense_if', label: 'Defense (IF)', icon: <FaMitten /> },
    { value: 'positions_and_defense_lf/rf', label: 'Defense (LF/RF)', icon: <FaMitten /> },
    { value: 'positions_and_defense_cf', label: 'Defense (CF)', icon: <FaMitten /> },
    { value: 'positions_and_defense_of', label: 'Defense (OF)', icon: <FaMitten /> },
];

type RangeDef = {
    label: string;
    minKey: keyof FilterSelections;
    maxKey: keyof FilterSelections;
    step?: number;
};

const SEASON_RANGE_FILTERS: RangeDef[] = [
    { label: "Year",     minKey: "min_year",    maxKey: "max_year",    step: 1 },
];

const REAL_RANGE_FILTERS: RangeDef[] = [
    { label: "PA",       minKey: "min_pa",      maxKey: "max_pa",      step: 1 },
    { label: "IP",       minKey: "min_real_ip", maxKey: "max_real_ip", step: 1 },
];

const SHOWDOWN_METADATA_RANGE_FILTERS: RangeDef[] = [
    { label: "PTS",      minKey: "min_points",  maxKey: "max_points",  step: 1 },
    { label: "Speed",    minKey: "min_speed",   maxKey: "max_speed",   step: 1 },
    { label: "IP",       minKey: "min_ip",      maxKey: "max_ip",      step: 1 },
];

const SHOWDOWN_CHART_RANGE_FILTERS: RangeDef[] = [
    { label: "Ctrl/OB",  minKey: "min_command", maxKey: "max_command", step: 1 },
    { label: "Outs",     minKey: "min_outs",    maxKey: "max_outs",    step: 1 },
];

// Filter Storage
const FILTERS_STORAGE_KEY = 'exploreFilters:v1.01';

const stripEmpty = (obj: any) =>
    Object.fromEntries(
        Object.entries(obj || {}).filter(
            ([_, v]) => !(v === undefined || v === null || (Array.isArray(v) && v.length === 0))
        )
    );

const loadSavedFilters = (): FilterSelections | null => {
    if (typeof window === 'undefined') return null;
    try {
        const raw = localStorage.getItem(FILTERS_STORAGE_KEY);
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        return { ...DEFAULT_FILTER_SELECTIONS, ...parsed } as FilterSelections;
    } catch {
        return null;
    }
};

const saveFilters = (filters: FilterSelections) => {
    if (typeof window === 'undefined') return;
    try {
        localStorage.setItem(FILTERS_STORAGE_KEY, JSON.stringify(stripEmpty(filters)));
    } catch {
        // ignore storage errors
    }
};

// Helper used for lazy init so we don't set state in an effect
const getInitialFilters = (): FilterSelections =>
  loadSavedFilters() ?? DEFAULT_FILTER_SELECTIONS;

// --------------------------------------------
// MARK: - Component
// --------------------------------------------

export default function ShowdownCardExplore({ className }: ShowdownCardExploreProps) {

    // State for showdown cards
    const [showdownCards, setShowdownCards] = useState<CardDatabaseRecord[] | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedCard, setSelectedCard] = useState<CardDatabaseRecord | null>(null);

    // Pagination state
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [isLoadingMore, setIsLoadingMore] = useState(false);

    // Modals
    const [showFiltersModal, setShowFiltersModal] = useState(false);
    const [showPlayerDetailModal, setShowPlayerDetailModal] = useState(false);
    const [showPlayerDetailSidebar, setShowPlayerDetailSidebar] = useState(false);

    // State for Set
    const { userShowdownSet } = useSiteSettings();

    // Separate search from filters
    const [searchText, setSearchText] = useState('');
    const [debouncedSearchText, setDebouncedSearchText] = useState('');

    // Filters
    const [filters, setFilters] = useState<FilterSelections>(getInitialFilters);
    const [filtersForEditing, setFiltersForEditing] = useState<FilterSelections>(getInitialFilters);
    const filtersWithoutSorting = { ...filters, sort_by: null, sort_direction: null };
    const hasCustomFiltersApplied = JSON.stringify(stripEmpty(filtersWithoutSorting)) !== JSON.stringify(stripEmpty(DEFAULT_FILTER_SELECTIONS));
    const bindRange = (minKey: keyof FilterSelections, maxKey: keyof FilterSelections) => ({
        minValue: filtersForEditing[minKey] as number | undefined,
        maxValue: filtersForEditing[maxKey] as number | undefined,
        onMinChange: (n?: number) => setFiltersForEditing(prev => ({ ...prev, [minKey]: n })),
        onMaxChange: (n?: number) => setFiltersForEditing(prev => ({ ...prev, [maxKey]: n })),
    });

    // Team hierarchy data - loaded once (daily) and cached
    const [teamHierarchyData, setTeamHierarchyData] = useState<TeamHierarchyRecord[]>([]);
    const [isHierarchyDataLoaded, setIsHierarchyDataLoaded] = useState(false);
    const [isLoadingHierarchyData, setIsLoadingHierarchyData] = useState(false);

    // Defined within component to access userShowdownSet
    const selectedSortOption = SORT_OPTIONS.find(option => option.value === filters.sort_by) || null;

    // Save filters whenever they change (kept separate so it doesn't run on search or set changes)
    useEffect(() => {
        saveFilters(filters);
    }, [filters]);

    // On initial load
    useEffect(() => {
        const loadHierarchyData = async () => {
            if (isHierarchyDataLoaded || isLoadingHierarchyData) return;
            
            setIsLoadingHierarchyData(true);
            try {
                const data = await fetchTeamHierarchy(); // This will use cache if available
                setTeamHierarchyData(data);
                setIsHierarchyDataLoaded(true);
            } catch (error) {
                console.error('Failed to load team hierarchy data:', error);
            } finally {
                setIsLoadingHierarchyData(false);
            }
        };

        loadHierarchyData();
    }, []); // Empty dependency array - only run once

    // Clear selected card when user changes showdown set
    useEffect(() => {
        setSelectedCard(null);
    }, [userShowdownSet]);

    // Reload cards when set or filters change
    useEffect(() => {

        setPage(1);
        setHasMore(true);
        setShowdownCards(null); // Clear existing cards immediately

        if (!userShowdownSet || isLoading) return;

        const timeoutId = setTimeout(() => {
            getCardsData();
        }, 100); // Small delay to prevent rapid successive calls

        return () => clearTimeout(timeoutId);
    }, [userShowdownSet, filters, debouncedSearchText]);

    // Debounce search text only
    useEffect(() => {
        if (searchText.length < 2) {
            setDebouncedSearchText('');
            return;
        }
        const timeoutId = setTimeout(() => {
            setDebouncedSearchText(searchText);
        }, 1000); // Delay 1 second

        return () => clearTimeout(timeoutId);
    }, [searchText]);

    // Create ref for intersection observer
    const observer = useRef<IntersectionObserver>(null);
    const lastCardElementRef = useCallback((node: HTMLDivElement) => {
        if (isLoading) return;
        if (observer.current) observer.current.disconnect();
        observer.current = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && hasMore && !isLoadingMore) {
                loadMoreCards();
            }
        }, {
            root: null
        });
        if (node) observer.current.observe(node);
    }, [isLoading, hasMore, isLoadingMore]);

    const getCardsData = async (pageNum: number = 1, append: boolean = false) => {

        // Loading indicators
        if (pageNum === 1) {
            setIsLoading(true);
        } else {
            setIsLoadingMore(true);
        }

        try {

            const pageLimit = 50;
            const searchFilters = debouncedSearchText ? { search: debouncedSearchText } : {};
            const combinedFilters = {
                ...filters,
                ...searchFilters,
                showdown_set: userShowdownSet,
                page: pageNum,
                limit: pageLimit // Cards per page
            };

            // Remove filters with empty arrays or undefined values
            const cleanedFilters = Object.fromEntries(
                Object.entries(combinedFilters).filter(([_, v]) => v !== undefined && v !== null && v.length !== 0)
            );
            const data = await fetchCardData(cleanedFilters);

            if (append && showdownCards) {
                setShowdownCards([...showdownCards, ...data]);
            } else {
                setShowdownCards(data);
            }

            // Check if there is more data not loaded yet
            setHasMore(data.length === pageLimit); // If less than limit, no more data

        } catch (error) {
            console.error("Error fetching showdown cards:", error);
        } finally {
            setIsLoading(false);
            setIsLoadingMore(false);
        }
    };

    // Load more cards function
    const loadMoreCards = async () => {
        if (!isLoadingMore && hasMore) {
            const nextPage = page + 1;
            setPage(nextPage);
            await getCardsData(nextPage, true); // append = true
        }
    };

    // Handle row selection
    const handleRowClick = (card: CardDatabaseRecord) => {
        if (card.id === selectedCard?.id) {
            // If clicking the same card, close the side menu (if applicable)
            handleCloseModal();
            setSelectedCard(null);
            return;
        }
        setSelectedCard(card);
        
        // Check screen size and show appropriate UI
        const isLargeScreen = window.innerWidth >= 1000; // 2xl breakpoint
        
        if (isLargeScreen) {
            setShowPlayerDetailSidebar(true);
            setShowPlayerDetailModal(false);
        } else {
            setShowPlayerDetailModal(true);
            setShowPlayerDetailSidebar(false);
        }
    };

    const handleCloseModal = () => {
        setShowPlayerDetailModal(false);
        setShowPlayerDetailSidebar(false);
        setSelectedCard(null);
    };

    const handleOpenFilters = () => {
        setFiltersForEditing(filters);
        setShowFiltersModal(true);
    }

    // Remove the getCardsData call from handleFilterApply
    const handleFilterApply = () => {
        // Check if difference between filters and filtersForEditing
        const filtersChanged = JSON.stringify(filters) !== JSON.stringify(filtersForEditing);
        if (filtersChanged) {
            setFilters(filtersForEditing);
        }
        setShowFiltersModal(false);
    }

    const resetFilters = (targets: String[]) => {
        if (targets.includes('filters')) {
            setFilters(DEFAULT_FILTER_SELECTIONS);
        }
        if (targets.includes('editing')) {
            setFiltersForEditing(DEFAULT_FILTER_SELECTIONS);
        }
    }

    const filterDisplayText = (key: string, value: any) => {
        if (key.startsWith('min_') || key.startsWith('max_')) {
            
            const comparisonOperator = key.startsWith('min_') ? '>=' : '<=';
            var shortKey = key.replace('min_', '').replace('max_', '');
            if (shortKey.length == 2) {
                shortKey = shortKey.toUpperCase();
            } else {
                shortKey = snakeToTitleCase(shortKey);
            }

            if (shortKey === 'Real Ip') {
                shortKey = 'Real IP';
            }

            if (shortKey === 'Command') {
                shortKey = 'Control/Onbase';
            }

            return `${shortKey} ${comparisonOperator} ${value}`;
        }

        if (key === 'include_small_sample_size') {
            const finalValues = value.length === 2 ? ['Yes', 'No'] : value[0] === 'true' ? ['Yes'] : ['No'];
            const finalValue = finalValues.join(',');
            return `Small Sample Sizes?: ${finalValue}`;
        }

        return `${snakeToTitleCase(key)}: ${value}`;
    }

    const renderLoadingIndicator = () => {
        return (
            <FaBaseballBall
                className="
                    text-3xl
                    animate-bounce
                "
                style={{
                    animationDuration: '0.7s',
                    animationIterationCount: 'infinite'
                }}
            />
        );
    };

    const renderResetButton = (targets: String[]) => {
        return (
            <button onClick={() => resetFilters(targets)} className="text-white flex items-center bg-[var(--showdown-gray)] rounded-full px-2 gap-1 py-1 cursor-pointer">
                <FaArrowRotateRight />
                <span className="text-sm">Reset</span>
            </button>
        );
    };

    // MARK: Render
    return (
        <div
            className={`
                flex flex-col ${className}
                md:h-[calc(100vh-theme(spacing.12))]                            /* fallback */
                md:supports-[height:100dvh]:h-[calc(100dvh-theme(spacing.12))]  /* prefer dvh */
                md:overflow-y-auto                                              /* scroller on desktop */
                md:min-h-0                                                      /* allow child to size for overflow */
            `}
        >

            {/* Search Bar and Filters */}
            <div className="sticky top-0 z-10 flex flex-col gap-2 w-full 
                            bg-background-secondary/95 backdrop-blur p-3">

                <div className="flex items-center space-x-2">

                    <div className="flex flex-1 items-center gap-2">
                        {/* Search Input */}
                        <FormInput
                            label=""
                            type="text"
                            value={searchText || ''}
                            placeholder="Search for a Player..."
                            onChange={(value) => setSearchText(value || '')}
                            className="w-full sm:w-1/3"
                            isClearable={true}
                            isTitleCase={true}
                        />

                        {/* Filters */}
                        <button
                            onClick={handleOpenFilters}
                            className="
                                px-3 h-11
                                rounded-xl bg-[var(--background-secondary)] border-2 border-form-element 
                                flex items-center gap-2
                                hover:bg-[var(--background-secondary-hover)]
                            ">
                            <FaFilter className="text-primary" />
                            <span className="hidden sm:inline">Filter</span>
                        </button>
                    </div>
                    

                    {/* If lg screen, show open button for side menu */}
                    <button
                        onClick={() => setShowPlayerDetailSidebar(true)}
                        className={`
                            items-center gap-2
                            hover:bg-[var(--background-secondary-hover)]
                            hidden lg:flex
                        `}>
                        <FaChevronCircleLeft className="text-[var(--tertiary)] w-7 h-7" />
                        <span className="text-[var(--tertiary)] text-lg font-bold">Card Detail</span>
                    </button>

                </div>

                {/* Show selected filters with X to remove */}
                <div className="relative flex flex-row gap-2">

                    <div className="flex flex-1 gap-2 overflow-x-scroll scrollbar-hide">
                        {/* Sorting Summary */}
                        {selectedSortOption && (
                            <button
                                className="flex items-center bg-[var(--background-secondary)] rounded-full px-2 py-1 text-sm text-nowrap cursor-pointer"
                                onClick={() => setFilters((prev) => ({ ...prev, sort_direction: prev.sort_direction === 'asc' ? 'desc' : 'asc' }))} // Toggle direction
                            >
                                <div className="flex flex-row gap-1 items-center">
                                    Sort:
                                    {selectedSortOption.icon && <span className="text-primary">{selectedSortOption.icon}</span>}
                                    <span>
                                        {selectedSortOption.label || "N/A"} {filters.sort_direction === 'asc' ? '↑' : '↓'}
                                    </span>
                                </div>
                            </button>
                        )}

                        {/* Selected Filters */}
                        {/* The last element should add lots of padding */}
                        {Object.entries(filtersWithoutSorting).map(([key, value]) => (
                            value === undefined || value === null || (Array.isArray(value) && value.length === 0) ? null :
                                <div key={key} className={`flex items-center bg-[var(--background-secondary)] rounded-full px-2 py-1`}>
                                    <span className="text-sm max-w-84 overflow-x-clip text-nowrap">{filterDisplayText(key, value)}</span>
                                    <button onClick={() => setFilters((prev) => ({ ...prev, [key]: undefined }))} className="ml-1 cursor-pointer">
                                        <FaTimes />
                                    </button>
                                </div>
                        ))}

                        {/* Add Blank element with width of 32 */}
                        <div className="flex-shrink-0 w-16"></div>
                    </div>

                    {/* Reset Button */}
                    {hasCustomFiltersApplied && (
                        <div className={`transition-all duration-300 ease-in-out ${showPlayerDetailSidebar ? 'lg:mr-96' : ''}`}>
                            {renderResetButton(['filters', 'editing'])}
                        </div>
                    )}
                </div>

            </div>

            {/* Flex between main content and side menu */}
            <div className="flex flex-1">

                {/* Main Content Area */}
                <div className={`
                        relative flex-1 min-w-0
                        ${showPlayerDetailSidebar ? 'lg:mr-96' : ''}
                        transition-all duration-300 ease-in-out
                        md:overflow-y-auto
                    `}>
                    <div className="py-2 px-3 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-3 md:gap-4">
                        {/* Iterate through showdownCards and display each card */}
                        {showdownCards?.map((cardRecord, index) => (
                            <div
                                key={cardRecord.id}
                                ref={showdownCards.length === (index + 1) ? lastCardElementRef : null}
                            >
                                <CardItem
                                    card={cardRecord.card_data}
                                    onClick={() => handleRowClick(cardRecord)}
                                    isSelected={selectedCard?.id === cardRecord.id}
                                />
                            </div>

                        ))}
                    </div>

                    {/* Loading more indicator at bottom */}
                    {isLoadingMore && (
                        <div className="flex justify-center py-4">
                            {renderLoadingIndicator()}
                        </div>
                    )}

                    {/* No more results indicator */}
                    {!hasMore && showdownCards && showdownCards.length > 50 && (
                        <div className="flex justify-center p-6 text-secondary">
                            <span className="text-sm">No more cards to load</span>
                        </div>
                    )}

                </div>

                
                {/* Right Sidebar with Slide Animation */}
                <div className={`
                    fixed right-0 top-12 bottom-0 w-96 z-30
                    bg-primary border-l-2 border-t-2 border-form-element 
                    transform transition-transform duration-300 ease-in-out
                    ${showPlayerDetailSidebar ? 'translate-x-0' : 'translate-x-full'}
                    hidden lg:block
                    shadow-xl
                `}>

                    {/* Sidebar Content */}
                    <div className="h-full flex flex-col">

                        {/* Stick header with close button */}
                        <div className="py-8 h-12 flex items-center space-x-2 p-2 border-b border-form-element">
                            <button 
                                onClick={() => setShowPlayerDetailSidebar(false)}>
                                <FaChevronCircleRight className="text-[var(--tertiary)] w-7 h-7" />
                            </button>
                            <h2 className="text-[var(--tertiary)] text-lg font-bold">Card Detail</h2>
                        </div>
                        

                        {/* Scrollable Content */}
                        <div className="flex-1 overflow-y-auto min-h-0">
                            <CardDetail
                                showdownBotCardData={{ card: selectedCard?.card_data } as ShowdownBotCardAPIResponse}
                                hideTrendGraphs={true}
                                context='explore'
                            />
                        </div>
                    </div>
                </div>
                

            </div>

            {/* Add Loading Indicator in the middle of the screen */}
            {isLoading && (
                <div className="
                    fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                    bg-[var(--primary)]/10 backdrop-blur 
                    p-4 rounded-2xl
                    flex items-center space-x-2
                ">
                    {renderLoadingIndicator()}
                </div>
            )}

            {/* Player Detail Modal */}
            {showPlayerDetailModal && selectedCard && (
                <Modal onClose={handleCloseModal}>
                    <CardDetail
                        showdownBotCardData={{ card: selectedCard.card_data } as ShowdownBotCardAPIResponse}
                        hideTrendGraphs={true}
                        context='explore'
                    />
                </Modal>
            )}

            {/* MARK: Filters Modal */}
            {showFiltersModal && (
                <Modal onClose={handleFilterApply}>
                    <div className="p-4 min-h-48 max-h-[80vh] md:min-h-128 md:max-h-[90vh]">
                        <div className="flex gap-3 mb-4 items-center border-b-2 border-form-element pb-2">
                            <h2 className="text-xl font-bold">Filter Options</h2>
                            {renderResetButton(['editing'])}
                        </div>

                        <div className="flex flex-col gap-4 pb-12">

                            {/* Sorting */}
                            <FormSection title="Sorting" isOpenByDefault={true}>

                                <FormDropdown
                                    label="Sort Category"
                                    options={SORT_OPTIONS}
                                    selectedOption={filtersForEditing.sort_by || 'points'}
                                    onChange={(value) => setFiltersForEditing({ ...filtersForEditing, sort_by: value })}
                                />

                                <FormDropdown
                                    label="Sort Direction"
                                    options={[
                                        { value: 'asc', label: 'Ascending', icon: <FaArrowUp /> },
                                        { value: 'desc', label: 'Descending', icon: <FaArrowDown /> },
                                    ]}
                                    selectedOption={filtersForEditing.sort_direction || 'asc'}
                                    onChange={(value) => setFiltersForEditing({ ...filtersForEditing, sort_direction: value })}
                                />

                            </FormSection>


                            <FormSection title="Seasons and Teams" isOpenByDefault={true}>
                                {/* Filters options */}

                                {SEASON_RANGE_FILTERS.map(def => (
                                    <RangeFilter
                                        key={def.minKey as string}
                                        label={def.label}
                                        {...bindRange(def.minKey, def.maxKey)}
                                    />
                                ))}

                                <TeamHierarchy
                                    hierarchyData={teamHierarchyData}
                                    selectedOrganizations={filtersForEditing.organization}
                                    selectedLeagues={filtersForEditing.league}
                                    selectedTeams={filtersForEditing.team}
                                    onOrganizationChange={(values) => setFiltersForEditing({ ...filtersForEditing, organization: values })}
                                    onLeagueChange={(values) => setFiltersForEditing({ ...filtersForEditing, league: values })}
                                    onTeamChange={(values) => setFiltersForEditing({ ...filtersForEditing, team: values })}
                                />

                                <MultiSelect
                                    label="Multi-Team Season?"
                                    options={[
                                        { value: 'true', label: 'Yes' },
                                        { value: 'false', label: 'No' },
                                    ]}
                                    selections={filtersForEditing.is_multi_team}
                                    onChange={(values) => setFiltersForEditing({ ...filtersForEditing, is_multi_team: values })}
                                />

                            </FormSection>


                            <FormSection title="Positions and Hand" isOpenByDefault={true}>
                                <MultiSelect
                                    label="Player Type"
                                    options={[
                                        { value: 'HITTER', label: 'Hitter' },
                                        { value: 'PITCHER', label: 'Pitcher' },
                                    ]}
                                    selections={filtersForEditing.player_type}
                                    onChange={(values) => setFiltersForEditing({ ...filtersForEditing, player_type: values })}
                                />

                                <MultiSelect
                                    label="Positions"
                                    options={[
                                        { value: 'C', label: 'CA' },
                                        { value: '1B', label: '1B' },
                                        { value: '2B', label: '2B' },
                                        { value: '3B', label: '3B' },
                                        { value: 'SS', label: 'SS' },
                                        { value: 'LF/RF', label: 'LF/RF' },
                                        { value: 'CF', label: 'CF' },
                                        { value: 'DH', label: 'DH' },
                                        { value: 'STARTER', label: 'SP' },
                                        { value: 'RELIEVER', label: 'RP' },
                                        { value: 'CLOSER', label: 'CL' },
                                    ]}
                                    selections={filtersForEditing.positions || []}
                                    onChange={(values) => setFiltersForEditing({ ...filtersForEditing, positions: values })}
                                />

                                <MultiSelect
                                    label="Hand"
                                    options={[
                                        { value: 'L', label: 'Left' },
                                        { value: 'R', label: 'Right' },
                                        { value: 'S', label: 'Switch' },
                                    ]}
                                    selections={filtersForEditing.hand || []}
                                    onChange={(values) => setFiltersForEditing({ ...filtersForEditing, hand: values })}
                                />
                            </FormSection>

                            <FormSection title="Real Stats" isOpenByDefault={true}>

                                {REAL_RANGE_FILTERS.map(def => (
                                    <RangeFilter
                                        key={def.minKey as string}
                                        label={def.label}
                                        {...bindRange(def.minKey, def.maxKey)}
                                    />
                                ))}

                                <MultiSelect
                                    label="Include Small Sample Sizes?"
                                    labelDescription="Defined as PA&lt;250 for Hitters, IP&lt;75 for Starters, IP&lt;35 for Relievers"
                                    options={[
                                        { value: 'true', label: 'Yes' },
                                        { value: 'false', label: 'No' },
                                    ]}
                                    selections={filtersForEditing.include_small_sample_size || []}
                                    onChange={(values) => setFiltersForEditing({ ...filtersForEditing, include_small_sample_size: values })}
                                />
                            </FormSection>

                            <FormSection title="Showdown Attributes" isOpenByDefault={true}>
                                {SHOWDOWN_METADATA_RANGE_FILTERS.map(def => (
                                    <RangeFilter
                                        key={def.minKey as string}
                                        label={def.label}
                                        {...bindRange(def.minKey, def.maxKey)}
                                    />
                                ))}

                                <MultiSelect
                                    label="Icons"
                                    options={[
                                            { value: 'V', label: 'V' },
                                            { value: 'S', label: 'S' },
                                            { value: 'G', label: 'G' },
                                            { value: 'HR', label: 'HR' },
                                            { value: 'SB', label: 'SB' },
                                            { value: 'CY', label: 'CY' },
                                            { value: '20', label: '20' },
                                            { value: 'K', label: 'K' },
                                            { value: 'RP', label: 'RP' },
                                            { value: 'R', label: 'R' },
                                            { value: 'RY', label: 'RY' }
                                    ]}
                                    selections={filtersForEditing.icons || []}
                                    onChange={(values) => setFiltersForEditing({ ...filtersForEditing, icons: values })}
                                />
                            </FormSection>

                            <FormSection title="Showdown Chart" isOpenByDefault={true}>
                                <MultiSelect
                                    label="Chart Outlier?"
                                    options={[
                                        { value: 'true', label: 'Yes' },
                                        { value: 'false', label: 'No' },
                                    ]}
                                    selections={filtersForEditing.is_chart_outlier ? filtersForEditing.is_chart_outlier.map(String) : []}
                                    onChange={(values) => setFiltersForEditing({ ...filtersForEditing, is_chart_outlier: values.length > 0 ? values : undefined })}
                                />
                
                                {SHOWDOWN_CHART_RANGE_FILTERS.map(def => (
                                    <RangeFilter
                                        key={def.minKey as string}
                                        label={def.label}
                                        {...bindRange(def.minKey, def.maxKey)}
                                    />
                                ))}
                            </FormSection>

                        </div>


                    </div>
                </Modal>
            )}
        </div>
    );
}