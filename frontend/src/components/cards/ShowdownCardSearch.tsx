/**
 * @fileoverview ShowdownCardSearch - Advanced card database browser and filter system
 * 
 * This component provides a comprehensive interface for exploring the MLB Showdown card database
 * with advanced filtering, sorting, and team hierarchy navigation capabilities.
 * 
 * SOURCE-SPECIFIC FILTERING & SORTING:
 * - Filters and sort options are conditionally displayed based on the card source (BOT vs WOTC)
 * - BOT cards support real stats, multi-team seasons, chart outliers, and image classification
 * - WOTC cards only show basic Showdown attributes and position/hand filters
 * - BOT sorting includes all real stats (PA, IP, ERA, OPS, etc.)
 * - WOTC sorting includes real vs estimated points, estimated points, and original set
 * - FILTER_AVAILABILITY configuration defines which filters are available for each source
 * - getSortOptions() function returns appropriate sort options for each source
 * - Filters and sort options are automatically cleaned when switching between sources
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { type CardDatabaseRecord, fetchCardData } from "../../api/card_db/cardDatabase";
import { CardDetail } from "./CardDetail";
import { type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { Modal } from "../shared/Modal";
import { useSiteSettings } from "../shared/SiteSettingsContext";
import {
    FaFilter, FaBaseballBall, FaArrowUp, FaArrowDown, FaTimes, FaHashtag,
    FaDollarSign, FaMitten, FaCalendarAlt, FaChevronCircleRight, FaChevronCircleLeft,
    FaSort, FaTable, FaImage, FaAddressCard, FaLayerGroup, FaCheck
} from "react-icons/fa";
import { FaArrowRotateRight, FaTableList, FaXmark } from "react-icons/fa6";
import { snakeToTitleCase } from "../../functions/text";
import { FaO, FaI } from "react-icons/fa6";

// Filter components
import FormInput from "../customs/FormInput";
import MultiSelect from "../shared/MultiSelect";
import FormDropdown from "../customs/FormDropdown";
import FormSection from "../customs/FormSection";
import type { SelectOption } from '../shared/CustomSelect';
import { CardItemFromCardDatabaseRecord, CardItemFromCard } from "./CardItem";
import { FaPersonRunning } from "react-icons/fa6";
import RangeFilter from "../customs/RangeFilter";

import { TeamHierarchy } from "./TeamHierarchy";
import { fetchTeamHierarchy, type TeamHierarchyRecord } from '../../api/card_db/cardDatabase';
import { CardSource } from '../../types/cardSource';

/**
 * Props for the ShowdownCardSearch component
 */
type ShowdownCardSearchProps = {
    /** Optional initial card data to display */
    showdownCards?: CardDatabaseRecord[] | null;
    /** Additional CSS classes */
    className?: string;
    /** Source of the card data */
    source: CardSource;
};

// =============================================================================
// MARK: - FILTERS
// =============================================================================

/**
 * Complete filter selections interface for card database queries
 * 
 * Provides comprehensive filtering across multiple dimensions:
 * - Sorting and ordering
 * - Real baseball statistics (PA, IP)
 * - Showdown game mechanics (points, command, speed)
 * - Team and league hierarchies
 * - Player characteristics (position, handedness)
 * - Data quality indicators
 */
interface FilterSelections {
    // Sorting and display order
    /** Field to sort results by */
    sort_by?: string;
    /** Sort direction: "asc" or "desc" */
    sort_direction?: string;

    // Real baseball statistics filters
    /** Minimum plate appearances (hitters) */
    min_pa?: number;
    /** Maximum plate appearances (hitters) */
    max_pa?: number;
    /** Minimum innings pitched (pitchers) */
    min_real_ip?: number;
    /** Maximum innings pitched (pitchers) */
    max_real_ip?: number;
    /** Include players with limited sample sizes */
    include_small_sample_size?: string[];
    /** Awards received (e.g., ["mvp-", "false"]) */
    awards?: string[];
    is_hof?: string[];

    // Showdown game mechanics filters
    /** Minimum point value */
    min_points?: number;
    /** Maximum point value */
    max_points?: number;
    /** Minimum speed rating */
    min_speed?: number;
    /** Maximum speed rating */
    max_speed?: number;
    /** Minimum innings pitched (Showdown stat) */
    min_ip?: number;
    /** Maximum innings pitched (Showdown stat) */
    max_ip?: number;

    /** Special ability icons (e.g., ["R", "S", "HR"]) */
    icons?: string[]; 

    /** Minimum command/control rating */
    min_command?: number;
    /** Maximum command/control rating */
    max_command?: number;
    /** Minimum outs on chart */
    min_outs?: number;
    /** Maximum outs on chart */
    max_outs?: number;

    // Temporal filters
    /** Minimum season year */
    min_year?: number;
    /** Maximum season year */
    max_year?: number;

    // Organizational hierarchy filters
    /** Organizations (e.g., ["MLB", "NGL"]) */
    organization?: string[];
    /** Leagues (e.g., ["AL", "NL", "NEGRO LEAGUES"]) */
    league?: string[];
    /** Specific teams (e.g., ["NYY", "BOS"]) */
    team?: string[];
    /** Players who played for multiple teams in one season */
    is_multi_team?: string[];

    // Player characteristic filters
    /** Player types (e.g., ["Hitter", "Pitcher"]) */
    player_type?: string[];
    /** Defensive positions (e.g., ["C", "1B", "SS"]) */
    positions?: string[];
    /** Batting/throwing handedness (e.g., ["R", "L", "S"]) */
    hand?: string[];

    // Data quality filters
    /** Cards with unusual statistical profiles */
    is_chart_outlier?: string[];

    // Errata
    is_errata?: string[];

    // Image attributes
    /** Lets user filter for cards with/without images */
    image_match_type?: string[];

    // Showdown set filtering
    showdown_set?: string[];
    expansion?: string[];
    edition?: string[];
}

/**
 * Get default filter selections based on the data source
 * 
 * @param source - The data source (CardSource enum value)
 * @returns Default filter selections optimized for the specific source
 */
const getDefaultFilterSelections = (source: CardSource): FilterSelections => {
    const baseDefaults: FilterSelections = {
        include_small_sample_size: ["false"],
        sort_by: "points",
        sort_direction: "desc",
        organization: ["MLB"],
    };

    // Customize defaults based on source
    switch (source) {
        case CardSource.BOT:
            return baseDefaults;
        case CardSource.WOTC:
            return {
                sort_by: "points",
                sort_direction: "desc",
            };
        default:
            return baseDefaults;
    }
};

/**
 * Configuration for which filters are available for each card source
 */
type FilterAvailability = {
    [K in keyof FilterSelections]?: CardSource[];
};

/**
 * Defines which filters are available for which card sources
 * If a filter is not listed here, it's available for all sources
 */
const FILTER_AVAILABILITY: FilterAvailability = {
    // BOT-specific filters (not available for WOTC)
    is_multi_team: [CardSource.BOT],
    include_small_sample_size: [CardSource.BOT],
    image_match_type: [CardSource.BOT],
    
    // Real stats filters - only available for BOT since WOTC cards don't have real stats
    min_pa: [CardSource.BOT],
    max_pa: [CardSource.BOT],
    min_real_ip: [CardSource.BOT],
    max_real_ip: [CardSource.BOT],
    awards: [CardSource.BOT],

    // Organization/League filtering might not make sense for WOTC
    organization: [CardSource.BOT],
    league: [CardSource.BOT],

    // Expansion and edition filters - only for WOTC
    expansion: [CardSource.WOTC],
    edition: [CardSource.WOTC],
    showdown_set: [CardSource.WOTC],

    // Errata filtering - only for WOTC
    is_errata: [CardSource.WOTC],
};

/**
 * Check if a filter is available for the given card source
 */
const isFilterAvailable = (filterKey: keyof FilterSelections, source: CardSource): boolean => {
    const availableSources = FILTER_AVAILABILITY[filterKey];
    // If not specified in the config, it's available for all sources
    return !availableSources || availableSources.includes(source);
};

/**
 * Clean up filter selections by removing filters not available for the current source
 * Also ensures sort option is available for the new source
 */
const cleanFiltersForSource = (filters: FilterSelections, source: CardSource): FilterSelections => {
    const cleaned: FilterSelections = {};
    
    for (const [key, value] of Object.entries(filters)) {
        const filterKey = key as keyof FilterSelections;
        if (isFilterAvailable(filterKey, source)) {
            cleaned[filterKey] = value;
        }
    }
    
    // Check if the current sort option is available for this source
    if (cleaned.sort_by) {
        const availableSortOptions = getSortOptions(source);
        const isSortOptionAvailable = availableSortOptions.some(option => option.value === cleaned.sort_by);
        
        if (!isSortOptionAvailable) {
            // Reset to default sort option for this source
            const defaultFilters = getDefaultFilterSelections(source);
            cleaned.sort_by = defaultFilters.sort_by;
            cleaned.sort_direction = defaultFilters.sort_direction;
        }
    }
    
    return cleaned;
};

/**
 * Base sort options available for all card sources
 */
const BASE_SORT_OPTIONS: SelectOption[] = [
    { value: 'points', label: 'Points', icon: <FaDollarSign /> },
    { value: 'year', label: 'Year', icon: <FaCalendarAlt /> },
    { value: 'speed', label: 'Speed', icon: <FaPersonRunning /> },
    { value: 'ip', label: 'IP', icon: <FaI /> },
    { value: 'command', label: 'Control/Onbase', icon: <FaBaseballBall /> },
    { value: 'outs', label: 'Outs', icon: <FaO /> },
];

/**
 * Defensive position rating sort options (available for all sources)
 */
const DEFENSE_SORT_OPTIONS: SelectOption[] = [
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

/**
 * Chart values sort options (available for all sources)
 */
const CHART_VALUES_SORT_OPTIONS: SelectOption[] = [
    { value: 'chart_values_pu', label: 'Chart Values (PU)', icon: <FaTableList /> },
    { value: 'chart_values_so', label: 'Chart Values (SO)', icon: <FaTableList /> },
    { value: 'chart_values_gb', label: 'Chart Values (GB)', icon: <FaTableList /> },
    { value: 'chart_values_fb', label: 'Chart Values (FB)', icon: <FaTableList /> },
    { value: 'chart_values_bb', label: 'Chart Values (BB)', icon: <FaTableList /> },
    { value: 'chart_values_1b', label: 'Chart Values (1B)', icon: <FaTableList /> },
    { value: 'chart_values_1b+', label: 'Chart Values (1B+)', icon: <FaTableList /> },
    { value: 'chart_values_2b', label: 'Chart Values (2B)', icon: <FaTableList /> },
    { value: 'chart_values_3b', label: 'Chart Values (3B)', icon: <FaTableList /> },
    { value: 'chart_values_hr', label: 'Chart Values (HR)', icon: <FaTableList /> },
];

/**
 * Real stats sort options (BOT only)
 */
const REAL_STATS_SORT_OPTIONS: SelectOption[] = [
    { value: 'real_stats_pa', label: 'Real Stats (PA)', icon: <FaHashtag /> },
    { value: 'real_stats_ip', label: 'Real Stats (IP)', icon: <FaHashtag /> },
    { value: 'real_stats_G', label: 'Real Stats (G)', icon: <FaHashtag /> },
    { value: 'real_stats_bWAR', label: 'Real Stats (bWAR)', icon: <FaHashtag /> },
    { value: 'real_stats_dWAR', label: 'Real Stats (dWAR)', icon: <FaHashtag /> },

    { value: 'real_stats_batting_avg', label: 'Real Stats (BA)', icon: <FaHashtag /> },
    { value: 'real_stats_onbase_perc', label: 'Real Stats (OBP)', icon: <FaHashtag /> },
    { value: 'real_stats_slugging_perc', label: 'Real Stats (SLG)', icon: <FaHashtag /> },
    { value: 'real_stats_onbase_plus_slugging', label: 'Real Stats (OPS)', icon: <FaHashtag /> },
    { value: 'real_stats_onbase_plus_slugging_plus', label: 'Real Stats (OPS+)', icon: <FaHashtag /> },

    { value: 'real_stats_earned_run_avg', label: 'Real Stats (ERA)', icon: <FaHashtag /> },
    { value: 'real_stats_whip', label: 'Real Stats (WHIP)', icon: <FaHashtag /> },
    
    { value: 'real_stats_H', label: 'Real Stats (H)', icon: <FaHashtag /> },
    { value: 'real_stats_1B', label: 'Real Stats (1B)', icon: <FaHashtag /> },
    { value: 'real_stats_2B', label: 'Real Stats (2B)', icon: <FaHashtag /> },
    { value: 'real_stats_3B', label: 'Real Stats (3B)', icon: <FaHashtag /> },
    { value: 'real_stats_HR', label: 'Real Stats (HR)', icon: <FaHashtag /> },
    { value: 'real_stats_SB', label: 'Real Stats (SB)', icon: <FaHashtag /> },

    { value: 'real_stats_SO', label: 'Real Stats (SO)', icon: <FaHashtag /> },
    { value: 'real_stats_BB', label: 'Real Stats (BB)', icon: <FaHashtag /> },
    { value: 'real_stats_W', label: 'Real Stats (W)', icon: <FaHashtag /> },
    { value: 'real_stats_SV', label: 'Real Stats (SV)', icon: <FaHashtag /> },
];

/**
 * WOTC-specific sort options
 */
const WOTC_SPECIFIC_SORT_OPTIONS: SelectOption[] = [
    { value: 'points_diff_estimated_vs_actual', label: 'Points Diff: Estimated vs Original', icon: <FaDollarSign /> },
    { value: 'points_estimated', label: 'Estimated Points', icon: <FaDollarSign /> },
];

/**
 * Get available sort options based on the card source
 */
const getSortOptions = (source: CardSource): SelectOption[] => {
    const baseOptions = [
        ...BASE_SORT_OPTIONS,
        ...DEFENSE_SORT_OPTIONS,
        ...CHART_VALUES_SORT_OPTIONS,
    ];

    switch (source) {
        case CardSource.BOT:
            return [
                ...baseOptions,
                ...REAL_STATS_SORT_OPTIONS,
            ];
        case CardSource.WOTC:
            return [
                ...WOTC_SPECIFIC_SORT_OPTIONS,
                ...baseOptions,
            ];
        default:
            return baseOptions;
    }
};

/**
 * Configuration for range filter UI components
 */
type RangeDef = {
    /** Display label for the range filter */
    label: string;
    /** FilterSelections key for minimum value */
    minKey: keyof FilterSelections;
    /** FilterSelections key for maximum value */
    maxKey: keyof FilterSelections;
    /** Step size for range inputs */
    step?: number;
};

/** Season-based range filters */
const SEASON_RANGE_FILTERS: RangeDef[] = [
    { label: "Year", minKey: "min_year", maxKey: "max_year", step: 1 },
];

/** Real baseball statistics range filters */
const REAL_RANGE_FILTERS: RangeDef[] = [
    { label: "PA", minKey: "min_pa", maxKey: "max_pa", step: 1 },
    { label: "IP", minKey: "min_real_ip", maxKey: "max_real_ip", step: 1 },
];

/** Showdown game metadata range filters */
const SHOWDOWN_METADATA_RANGE_FILTERS: RangeDef[] = [
    { label: "PTS", minKey: "min_points", maxKey: "max_points", step: 1 },
    { label: "Speed", minKey: "min_speed", maxKey: "max_speed", step: 1 },
    { label: "IP", minKey: "min_ip", maxKey: "max_ip", step: 1 },
];

/** Showdown chart mechanics range filters */
const SHOWDOWN_CHART_RANGE_FILTERS: RangeDef[] = [
    { label: "Ctrl/OB", minKey: "min_command", maxKey: "max_command", step: 1 },
    { label: "Outs", minKey: "min_outs", maxKey: "max_outs", step: 1 },
];

// =============================================================================
// MARK: - FILTER PERSISTENCE & UTILITIES
// =============================================================================

/** localStorage key for persisting filter selections across sessions */
const FILTERS_STORAGE_KEY = 'exploreFilters:v1.01';

/**
 * Removes empty/null/undefined values from filter objects
 * @param obj - Filter object to clean
 * @returns Cleaned object with only meaningful values
 */
const stripEmpty = (obj: any) =>
    Object.fromEntries(
        Object.entries(obj || {}).filter(
            ([_, v]) => !(v === undefined || v === null || (Array.isArray(v) && v.length === 0))
        )
    );

/**
 * Loads previously saved filter selections from localStorage
 * @returns Saved filters merged with defaults, or null if none exist
 */
const loadSavedFilters = (source: CardSource): FilterSelections | null => {
    if (typeof window === 'undefined') return null;
    try {
        const raw = localStorage.getItem(FILTERS_STORAGE_KEY + ':' + source);
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        return { ...getDefaultFilterSelections(source), ...parsed } as FilterSelections;
    } catch {
        return null;
    }
};

const saveFilters = (filters: FilterSelections, source: CardSource) => {
    if (typeof window === 'undefined') return;
    try {
        localStorage.setItem(FILTERS_STORAGE_KEY + ':' + source, JSON.stringify(stripEmpty(filters)));
    } catch {
        // ignore storage errors
    }
};

// Helper used for lazy init so we don't set state in an effect
const getInitialFilters = (source: CardSource): FilterSelections =>
  loadSavedFilters(source) ?? getDefaultFilterSelections(source);

// --------------------------------------------
// MARK: - Component
// --------------------------------------------

/**
 * ShowdownCardSearch - Advanced card database browser with filtering and search
 * 
 * This is the main card exploration interface providing:
 * - Advanced multi-dimensional filtering system
 * - Team hierarchy navigation 
 * - Infinite scroll pagination
 * - Real-time search and sorting
 * - Detailed card previews and full detail modals
 * - Filter persistence across sessions
 * - Responsive design for mobile and desktop
 * 
 * The component manages a complex state system for filters, pagination, and UI interactions
 * while providing smooth performance through debounced searches and lazy loading.
 * 
 * @param className - Additional CSS classes for the container
 * @param source - Source of the card data (CardSource enum)
 */
export default function ShowdownCardSearch({ className, source = CardSource.BOT }: ShowdownCardSearchProps) {
    // =============================================================================
    // CORE STATE MANAGEMENT
    // =============================================================================

    /** Main card data state */
    const [showdownCards, setShowdownCards] = useState<CardDatabaseRecord[] | null>(null);
    /** Loading state for initial data fetch */
    const [isLoading, setIsLoading] = useState(false);
    /** Currently selected card for detail view */
    const [selectedCardForModal, setSelectedCardForModal] = useState<CardDatabaseRecord | null>(null);
    const [selectedCardForSidebar, setSelectedCardForSidebar] = useState<CardDatabaseRecord | null>(null);
    const selectedCard = window.innerWidth >= 1000 ? selectedCardForSidebar : selectedCardForModal;

    // Pagination state management
    /** Current page number for infinite scroll */
    const [page, setPage] = useState(1);
    /** Whether more cards are available to load */
    const [hasMore, setHasMore] = useState(true);
    /** Loading state for pagination requests */
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    /** No result found messaging */
    const [warningMessage, setWarningMessage] = useState<string | null>(null);

    // UI modal visibility state
    /** Show/hide filters modal on mobile */
    const [showFiltersModal, setShowFiltersModal] = useState(false);
    /** Show/hide player detail modal */
    const [showPlayerDetailModal, setShowPlayerDetailModal] = useState(false);
    /** Show/hide player detail sidebar */
    const [showPlayerDetailSidebar, setShowPlayerDetailSidebar] = useState(false);

    // Global application state
    /** Current user's selected Showdown set */
    const { userShowdownSet } = useSiteSettings();

    // Separate search from filters
    const [searchText, setSearchText] = useState('');
    const [debouncedSearchText, setDebouncedSearchText] = useState('');

    // Filters
    const [filters, setFilters] = useState<FilterSelections>(getInitialFilters(source));
    const [filtersForEditing, setFiltersForEditing] = useState<FilterSelections>(getInitialFilters(source));
    const filtersWithoutSorting = { ...filters, sort_by: null, sort_direction: null };
    const filtersWithoutSortingForEditing = { ...filtersForEditing, sort_by: null, sort_direction: null };
    const hasCustomFiltersApplied = JSON.stringify(stripEmpty(filtersWithoutSorting)) !== JSON.stringify(stripEmpty(getDefaultFilterSelections(source)));
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

    // Get sort options based on source and find selected option
    const sortOptions = getSortOptions(source);
    const selectedSortOption = sortOptions.find(option => option.value === filters.sort_by) || null;
    const selectedSortOptionForEditing = sortOptions.find(option => option.value === filtersForEditing.sort_by) || null;

    // Ref for scrollable main content area
    const cardScrollParentRef = useRef<HTMLDivElement>(null);

    // Save filters whenever they change (kept separate so it doesn't run on search or set changes)
    useEffect(() => {
        saveFilters(filters, source);
    }, [filters]);

    // Clean filters when source changes to remove unavailable filters
    useEffect(() => {
        const cleanedFilters = cleanFiltersForSource(filters, source);
        const cleanedForEditing = cleanFiltersForSource(filtersForEditing, source);
        
        // Only update if there are actual changes
        if (JSON.stringify(cleanedFilters) !== JSON.stringify(filters)) {
            setFilters(cleanedFilters);
        }
        if (JSON.stringify(cleanedForEditing) !== JSON.stringify(filtersForEditing)) {
            setFiltersForEditing(cleanedForEditing);
        }
    }, [source]);

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

    // Note: We don't clear selected card when showdown set changes anymore
    // Instead, we let getCardsData handle checking if the card exists in the new results

    // Reload cards when set or filters change
    useEffect(() => {

        setPage(1);
        setHasMore(true);
        setShowdownCards(null); // Clear existing cards immediately

        if (!userShowdownSet || isLoading) return;

        const timeoutId = setTimeout(() => {
            getCardsData();
        }, 200); // Small delay to prevent rapid successive calls

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

            // Only include userShowdownSet if filters.showdown_set is not already populated
        const showdownSetFilter = filters.showdown_set && filters.showdown_set.length > 0 
            ? {} 
            : { showdown_set: userShowdownSet };

            const combinedFilters = {
                ...filters,
                ...searchFilters,
                ...showdownSetFilter,
                page: pageNum,
                limit: pageLimit // Cards per page
            };

            // Remove filters with empty arrays or undefined values
            const cleanedFilters = Object.fromEntries(
                Object.entries(combinedFilters).filter(([_, v]) => v !== undefined && v !== null && v.length !== 0)
            );
            const data = await fetchCardData(source, cleanedFilters);

            let newCardData;
            if (append && showdownCards) {
                newCardData = [...showdownCards, ...data];
                setShowdownCards(newCardData);
            } else {
                newCardData = data;
                setShowdownCards(newCardData);
            }

            // Check if there is more data not loaded yet
            setHasMore(data.length === pageLimit); // If less than limit, no more data

            // Check for warning message using the new data instead of state
            if (newCardData.length === 0 && pageNum === 1) {
                setWarningMessage("No results found for the given filters/search.");
            } else {
                setWarningMessage(null);
            }

            // If we have a selected card and this is the first page (new data load),
            // check if the selected card still exists in the new results
            if (selectedCardForSidebar && pageNum === 1 && newCardData.length > 0) {
                const cardStillExists = newCardData.find(card => card.id === selectedCardForSidebar.id);
                if (cardStillExists) {
                    // Card exists in new results, update the selected card with new data
                    setSelectedCardForSidebar(cardStillExists);
                } else {
                    // Card no longer exists, clear selection
                    setSelectedCardForSidebar(null);
                    setShowPlayerDetailSidebar(false);
                }
            }

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
        
        const isLargeScreen = window.innerWidth >= 1000; // 2xl breakpoint
        
        console.log("Card clicked:", card);
        if (card.id === selectedCard?.id) {
            // If clicking the same card, close the side menu (if applicable)
            if (isLargeScreen) {
                handleCloseSidebar();
            } else {
                handleCloseModal();
            }
            return;
        }
        if (isLargeScreen) {
            setSelectedCardForSidebar(card);
        } else {
            setSelectedCardForModal(card);
        }
        
        // Check screen size and show appropriate UI
        const isSidebarAlreadyOpen = showPlayerDetailSidebar;
        
        if (isLargeScreen) {
            setShowPlayerDetailSidebar(true);
            
            if (!isSidebarAlreadyOpen) {
                // Auto-scroll to the selected card after the sidebar animation completes
                setTimeout(() => {
                    const selectedElement = document.querySelector(`[data-card-id="${card.id}"]`);
                    if (selectedElement) {
                        selectedElement.scrollIntoView({
                            behavior: 'smooth',
                            block: 'center',
                            inline: 'nearest'
                        });
                    }
                }, 350); // Wait for sidebar animation (300ms + small buffer)
            }
        } else {
            setShowPlayerDetailModal(true);
        }
    };

    const handleCloseModal = () => {
        setShowPlayerDetailModal(false);
        setSelectedCardForModal(null);
    };

    const handleCloseSidebar = () => {
        setShowPlayerDetailSidebar(false);
        setSelectedCardForSidebar(null);
    }

    const handleOpenFilters = () => {
        setFiltersForEditing(filters);
        setShowFiltersModal(true);
    }

    const hasFiltersChanged = JSON.stringify(filters) !== JSON.stringify(filtersForEditing);

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
            setFilters(getDefaultFilterSelections(source));
        }
        if (targets.includes('editing')) {
            setFiltersForEditing(getDefaultFilterSelections(source));
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

        if (key === 'showdown_set') {
            const finalValue = Array.isArray(value) ? value.map(s => s.toUpperCase()).join(', ') : value.toUpperCase();
            return `Set: ${finalValue}`;
        }

        const keysWithValuesToTitleCase = ['image_match_type']
        if (keysWithValuesToTitleCase.includes(key)) {
            const finalValue = Array.isArray(value) ? value.map(snakeToTitleCase).join(', ') : snakeToTitleCase(value);
            return `${snakeToTitleCase(key)}: ${finalValue}`;
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
            <button onClick={() => resetFilters(targets)} className="text-[var(--background-primary)] font-bold flex items-center bg-[var(--showdown-gray)] rounded-full px-2 gap-1 py-1 cursor-pointer">
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
                md:h-[calc(100vh-theme(spacing.24))]                            /* fallback */
                md:supports-[height:100dvh]:h-[calc(100dvh-theme(spacing.24))]  /* prefer dvh */
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
                            className="w-full sm:w-1/3 font-bold"
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
                        {Object.entries(filtersWithoutSorting)
                            .filter(([_, value]) => !(value === undefined || value === null || (Array.isArray(value) && value.length === 0)))
                            .map(([key, value]) => (
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
                <div 
                    ref={cardScrollParentRef}
                    className={`
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
                                data-card-id={cardRecord.id}
                                ref={showdownCards.length === (index + 1) ? lastCardElementRef : null}
                            >
                                {source === CardSource.WOTC && (
                                    <CardItemFromCard
                                        card={cardRecord.card_data}
                                        onClick={() => handleRowClick(cardRecord)}
                                        isSelected={selectedCard?.id === cardRecord.id}
                                    />
                                )}
                                {source === CardSource.BOT && (
                                    <CardItemFromCardDatabaseRecord
                                        card={cardRecord}
                                        onClick={() => handleRowClick(cardRecord)}
                                        isSelected={selectedCard?.id === cardRecord.id}
                                    />
                                )}
                            </div>

                        ))}
                    </div>

                    {/* No results found message */}
                    {warningMessage && (
                        <div className="flex justify-center p-6 text-secondary bg-[var(--primary)]/10 rounded-xl m-10">
                            <span className="text-sm">{warningMessage}</span>
                        </div>
                    )}

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
                    fixed right-0 top-24 bottom-0 w-96 z-30
                    bg-primary border-l-2 border-form-element 
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
                                onClick={handleCloseSidebar}>
                                <FaChevronCircleRight className="text-[var(--tertiary)] w-7 h-7" />
                            </button>
                            <h2 className="text-[var(--tertiary)] text-lg font-bold">Card Detail</h2>
                        </div>
                        

                        {/* Scrollable Content */}
                        <div className="flex-1 overflow-y-auto min-h-0">
                            <CardDetail
                                showdownBotCardData={{ card: selectedCardForSidebar?.card_data } as ShowdownBotCardAPIResponse}
                                cardId={selectedCardForSidebar?.card_id}
                                hideTrendGraphs={true}
                                context='explore'
                                parent="sidebar"
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
            <div className={showPlayerDetailModal && selectedCardForModal ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={handleCloseModal} isVisible={showPlayerDetailModal && !!selectedCardForModal}>
                    <CardDetail
                        showdownBotCardData={selectedCardForModal ? { card: selectedCardForModal.card_data } as ShowdownBotCardAPIResponse : undefined}
                        cardId={selectedCardForModal?.card_id}
                        hideTrendGraphs={true}
                        context='explore'
                        parent="modal"
                    />
                </Modal>
            </div>

            {/* MARK: Filters Modal */}
            {showFiltersModal && (
                <Modal onClose={handleFilterApply} disableCloseButton={true}>

                    <div className="min-h-48 max-h-[80vh] md:min-h-128 md:max-h-[90vh]">

                        {/* Header */}
                        <div 
                            className="
                                sticky top-0 flex flex-col
                                gap-y-1 mb-4 px-4 pb-3 pt-4 z-10
                                border-b-2 border-form-element 
                                bg-background-secondary/95 backdrop-blur
                            ">
                            
                            <div className="flex items-center gap-2">
                                <h2 className="text-xl font-bold">Filter Options</h2>

                                <div className="absolute text-sm flex gap-x-6 right-0 p-4 text-[var(--background-primary)]">
                                    {/* Reset button */}
                                    {renderResetButton(['editing'])}

                                    {/* Apply or Close Button */}
                                    {hasFiltersChanged ? (
                                        <button
                                            onClick={handleFilterApply}
                                            className="bg-[var(--success)] rounded-full flex items-center px-2 gap-1 py-1 cursor-pointer"
                                        >
                                            <FaCheck />
                                            <span className="font-bold">Apply</span>
                                        </button>
                                    ) : (
                                        <button
                                            onClick={handleFilterApply}
                                            className="bg-[var(--warning)] rounded-full flex items-center px-3 gap-1 py-1 cursor-pointer"
                                        >
                                            <FaXmark />
                                            <span className="font-bold">Exit</span>
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Filters Summary */}
                            <div className="flex flex-1 gap-2 overflow-x-scroll scrollbar-hide">

                                {selectedSortOptionForEditing && (
                                    <button
                                        className="flex items-center bg-[var(--background-secondary)] rounded-full px-2 py-1 text-sm text-nowrap cursor-pointer"
                                        onClick={() => setFiltersForEditing((prev) => ({ ...prev, sort_direction: prev.sort_direction === 'asc' ? 'desc' : 'asc' }))} // Toggle direction
                                    >
                                        <div className="flex flex-row gap-1 items-center">
                                            Sort:
                                            {selectedSortOptionForEditing.icon && <span className="text-primary">{selectedSortOptionForEditing.icon}</span>}
                                            <span>
                                                {selectedSortOptionForEditing.label || "N/A"} {filtersForEditing.sort_direction === 'asc' ? '↑' : '↓'}
                                            </span>
                                        </div>
                                    </button>
                                )}

                                {Object.entries(filtersWithoutSortingForEditing)
                                    .filter(([_, value]) => !(value === undefined || value === null || (Array.isArray(value) && value.length === 0)))
                                    .map(([key, value]) => (
                                        <div key={key} className={`flex items-center bg-[var(--background-secondary)] rounded-full px-2 py-1`}>
                                            <span className="text-sm max-w-84 overflow-x-clip text-nowrap">{filterDisplayText(key, value)}</span>
                                            <button onClick={() => setFiltersForEditing((prev) => ({ ...prev, [key]: undefined }))} className="ml-1 cursor-pointer">
                                                <FaTimes />
                                            </button>
                                        </div>
                                ))}
                            </div>
                        </div>

                        {/* Filters */}
                        <div className="flex flex-col gap-4 pb-12 px-4">

                            {/* Sorting */}
                            <FormSection title="Sorting" icon={<FaSort />} isOpenByDefault={true}>

                                <FormDropdown
                                    label="Sort Category"
                                    options={sortOptions}
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

                            {/* Set */}
                            {isFilterAvailable('showdown_set', source) && (

                                <FormSection title="Showdown Set" icon={<FaLayerGroup />} isOpenByDefault={true}>

                                    {/* Set */}
                                    <MultiSelect
                                        label="Set"
                                        labelDescription={`Overrides your selected Showdown set above (${userShowdownSet?.toUpperCase()}).`}
                                        className="col-span-full" // FULL WIDTH
                                        options={[
                                            { value: '2000', label: '2000' },
                                            { value: '2001', label: '2001' },
                                            { value: '2002', label: '2002' },
                                            { value: '2003', label: '2003' },
                                            { value: '2004', label: '2004' },
                                            { value: '2005', label: '2005' },
                                        ]}
                                        selections={filtersForEditing.showdown_set || []}
                                        onChange={(values) => setFiltersForEditing({ ...filtersForEditing, showdown_set: values })}
                                    />

                                    {/* Expansion */}
                                    <MultiSelect
                                        label="Expansion"
                                        options={[
                                            { value: 'BS', label: 'BASE SET' },
                                            { value: 'TD', label: 'TRADING DEADLINE' },
                                            { value: 'PR', label: 'PENNANT RUN' },
                                            { value: 'PM', label: 'PROMO' },
                                            { value: 'ASG', label: 'ALL-STAR GAME' },
                                        ]}
                                        selections={filtersForEditing.expansion || []}
                                        onChange={(values) => setFiltersForEditing({ ...filtersForEditing, expansion: values })}
                                    />

                                    {/* Edition */}
                                    <MultiSelect
                                        label="Edition"
                                        options={[
                                            { value: 'NONE', label: 'None' },
                                            { value: 'CC', label: 'Cooperstown Collection' },
                                            { value: 'SS', label: 'Super Season' },
                                            { value: 'RS', label: 'Rookie Season' },
                                            { value: 'ASG', label: 'All-Star' },
                                        ]}
                                        selections={filtersForEditing.edition || []}
                                        onChange={(values) => setFiltersForEditing({ ...filtersForEditing, edition: values })}
                                    />
                                
                                </FormSection>
                            )}


                            <FormSection title="Seasons and Teams" icon={<FaCalendarAlt />} isOpenByDefault={true}>
                                {/* Filters options */}

                                {SEASON_RANGE_FILTERS.map(def => (
                                    <RangeFilter
                                        key={def.minKey as string}
                                        label={def.label}
                                        {...bindRange(def.minKey, def.maxKey)}
                                    />
                                ))}

                                {isFilterAvailable('organization', source) && (
                                    <TeamHierarchy
                                        hierarchyData={teamHierarchyData}
                                        selectedOrganizations={filtersForEditing.organization}
                                        selectedLeagues={filtersForEditing.league}
                                        selectedTeams={filtersForEditing.team}
                                        onOrganizationChange={(values) => setFiltersForEditing({ ...filtersForEditing, organization: values })}
                                        onLeagueChange={(values) => setFiltersForEditing({ ...filtersForEditing, league: values })}
                                        onTeamChange={(values) => setFiltersForEditing({ ...filtersForEditing, team: values })}
                                    />
                                )}

                                {isFilterAvailable('is_multi_team', source) && (
                                    <MultiSelect
                                        label="Multi-Team Season?"
                                        options={[
                                            { value: 'true', label: 'Yes' },
                                            { value: 'false', label: 'No' },
                                        ]}
                                        selections={filtersForEditing.is_multi_team}
                                        onChange={(values) => setFiltersForEditing({ ...filtersForEditing, is_multi_team: values })}
                                    />
                                )}

                            </FormSection>


                            <FormSection title="Positions and Hand" icon={<FaMitten />} isOpenByDefault={true}>
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

                            {isFilterAvailable('min_pa', source) && (
                                <FormSection title="Real Stats and Awards" icon={<FaHashtag />} isOpenByDefault={true}>

                                    {REAL_RANGE_FILTERS.map(def => (
                                        <RangeFilter
                                            key={def.minKey as string}
                                            label={def.label}
                                            {...bindRange(def.minKey, def.maxKey)}
                                        />
                                    ))}

                                    {isFilterAvailable('include_small_sample_size', source) && (
                                        <MultiSelect
                                            label="Include Small Sample Sizes?"
                                            labelDescription="Defined as PA&lt;250 for Hitters, IP&lt;75 for Starters, IP&lt;30 for Relievers"
                                            options={[
                                                { value: 'true', label: 'Yes' },
                                                { value: 'false', label: 'No' },
                                            ]}
                                            selections={filtersForEditing.include_small_sample_size || []}
                                            onChange={(values) => setFiltersForEditing({ ...filtersForEditing, include_small_sample_size: values })}
                                        />
                                    )}

                                    {isFilterAvailable('awards', source) && (
                                        <MultiSelect
                                            label="Awards"
                                            options={[
                                                { value: 'MVP-1', label: 'MVP' },
                                                { value: 'CYA-1', label: 'Cy Young' },
                                                { value: 'ROY-1', label: 'Rookie of the Year' },
                                                { value: 'GG', label: 'Gold Glove' },
                                                { value: 'SS', label: 'Silver Slugger' },
                                                { value: 'AS', label: 'All-Star' },
                                                { value: 'MVP-*', label: 'MVP Votes' },
                                                { value: 'CYA-*', label: 'Cy Young Votes' },
                                                { value: 'ROY-*', label: 'Rookie of the Year Votes' },
                                            ]}
                                            selections={filtersForEditing.awards || []}
                                            onChange={(values) => setFiltersForEditing({ ...filtersForEditing, awards: values })}
                                        />
                                    )}

                                    {isFilterAvailable('is_hof', source) && (
                                        <MultiSelect
                                            label="HOF?"
                                            options={[
                                                { value: 'true', label: 'Yes' },
                                                { value: 'false', label: 'No' },
                                            ]}
                                            selections={filtersForEditing.is_hof ? filtersForEditing.is_hof.map(String) : []}
                                            onChange={(values) => setFiltersForEditing({ ...filtersForEditing, is_hof: values.length > 0 ? values : undefined })}
                                        />
                                    )}
                                </FormSection>
                            )}

                            <FormSection title="Showdown Attributes" icon={<FaAddressCard />} isOpenByDefault={true}>
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

                            <FormSection title="Showdown Chart" icon={<FaTable />} isOpenByDefault={true}>
                                {isFilterAvailable('is_chart_outlier', source) && (
                                    <MultiSelect
                                        label="Chart Outlier?"
                                        options={[
                                            { value: 'true', label: 'Yes' },
                                            { value: 'false', label: 'No' },
                                        ]}
                                        selections={filtersForEditing.is_chart_outlier ? filtersForEditing.is_chart_outlier.map(String) : []}
                                        onChange={(values) => setFiltersForEditing({ ...filtersForEditing, is_chart_outlier: values.length > 0 ? values : undefined })}
                                    />
                                )}

                                {isFilterAvailable('is_errata', source) && (
                                    <MultiSelect
                                        label="Errata?"
                                        options={[
                                            { value: 'true', label: 'Yes' },
                                            { value: 'false', label: 'No' },
                                        ]}
                                        selections={filtersForEditing.is_errata ? filtersForEditing.is_errata.map(String) : []}
                                        onChange={(values) => setFiltersForEditing({ ...filtersForEditing, is_errata: values.length > 0 ? values : undefined })}
                                    />
                                )}
                
                                {SHOWDOWN_CHART_RANGE_FILTERS.map(def => (
                                    <RangeFilter
                                        key={def.minKey as string}
                                        label={def.label}
                                        {...bindRange(def.minKey, def.maxKey)}
                                    />
                                ))}


                            </FormSection>

                            {isFilterAvailable('image_match_type', source) && (
                                <FormSection title="Image Attributes" icon={<FaImage />} isOpenByDefault={true}>
                                    <MultiSelect
                                        label="Auto Image Classification"
                                        options={[
                                            { value: 'exact', label: 'Exact Match (Year + Team)' },
                                            { value: 'team match', label: 'Team Match (Different Year)' },
                                            { value: 'year match', label: 'Year Match (Different Team)' },
                                            { value: 'no match', label: 'No Match' },
                                        ]}
                                        selections={filtersForEditing.image_match_type}
                                        onChange={(values) => setFiltersForEditing({ ...filtersForEditing, image_match_type: values })}
                                    />
                                </FormSection>
                            )}

                        </div>


                    </div>
                </Modal>
            )}
        </div>
    );
}