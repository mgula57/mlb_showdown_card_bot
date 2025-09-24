import { useState, useEffect, useRef, useCallback } from "react";
import { type CardDatabaseRecord, fetchCardData } from "../../api/card_db/cardDatabase";
import { CardDetail } from "./CardDetail";
import { type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { Modal } from "../shared/Modal";
import { useSiteSettings } from "../shared/SiteSettingsContext";
import {
    FaFilter, FaBaseballBall, FaArrowUp, FaArrowDown, FaTimes,
    FaDollarSign, FaMitten,
} from "react-icons/fa";
import { snakeToTitleCase } from "../../functions/text";

// Filter components
import FormInput from "../customs/FormInput";
import MultiSelect from "../shared/MultiSelect";
import FormDropdown from "../customs/FormDropdown";
import FormSection from "../customs/FormSection";
import type { SelectOption } from '../shared/CustomSelect';
import { CardItem } from "./CardItem";
import { FaPersonRunning } from "react-icons/fa6";

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

    // Showdown Min/Max
    min_points?: number;
    max_points?: number;
    min_command?: number;
    max_command?: number;
    min_outs?: number;
    max_outs?: number;
    min_speed?: number;
    max_speed?: number;

    organization?: string[]; // e.g., ["MLB", "NGL"]
    league?: string[]; // e.g., ["MLB", "NEGRO LEAGUES"]
    team?: string[]; // e.g., ["Yankees", "Red Sox"]
    years?: number[]; // e.g., [2020, 2021]

    player_type?: string[]; // e.g., ["Hitter", "Pitcher"]
    positions?: string[]; // e.g., ["C", "1B"]
    hand?: string[]; // e.g., ["R", "L", "S"]
}

const DEFAULT_FILTER_SELECTIONS: FilterSelections = {
    min_pa: 250,
    min_real_ip: 35,
    sort_by: "points",
    sort_direction: "desc",
};

const SORT_OPTIONS: SelectOption[] = [
    { value: 'points', label: 'Points', icon: <FaDollarSign /> },
    { value: 'speed', label: 'Speed', icon: <FaPersonRunning /> },
    { value: 'command', label: 'Control/Onbase' },
    { value: 'outs', label: 'Outs' },

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

// Filter Storage
const FILTERS_STORAGE_KEY = 'exploreFilters:v1';

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

    // State for Set
    const { userShowdownSet } = useSiteSettings();

    // Separate search from filters
    const [searchText, setSearchText] = useState('');
    const [debouncedSearchText, setDebouncedSearchText] = useState('');

    // Filters
    const [filters, setFilters] = useState<FilterSelections>(getInitialFilters);
    const [filtersForEditing, setFiltersForEditing] = useState<FilterSelections>(getInitialFilters);
    const filtersWithoutSorting = { ...filters, sort_by: null, sort_direction: null };

    // Defined within component to access userShowdownSet
    const selectedSortOption = SORT_OPTIONS.find(option => option.value === filters.sort_by) || null;

    // Save filters whenever they change (kept separate so it doesn't run on search or set changes)
    useEffect(() => {
        saveFilters(filters);
    }, [filters]);

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
        setSelectedCard(card);
        setShowPlayerDetailModal(true);
    };

    const handleCloseModal = () => {
        setShowPlayerDetailModal(false);
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

    const resetFilters = () => {
        setFiltersForEditing(DEFAULT_FILTER_SELECTIONS);
    }

    const filterDisplayText = (key: string, value: any) => {
        if (key.startsWith('min_')) {
            ``
            var shortKey = key.replace('min_', '');
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

            return `${shortKey} >= ${value}`;
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
    }

    // MARK: Render
    return (
        <div className={`flex flex-col ${className}`}>

            {/* Search Bar and Filters */}
            <div className="sticky top-0 z-10 flex flex-col gap-2 w-full 
                            bg-background-secondary/95 backdrop-blur p-3">

                <div className="flex items-center space-x-2">
                    {/* Search Input */}
                    <FormInput
                        label=""
                        type="text"
                        value={searchText || ''}
                        placeholder="Search for a Player..."
                        onChange={(value) => setSearchText(value || '')}
                        className="w-full sm:w-1/3"
                        isClearable={true}
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

                {/* Show selected filters with X to remove */}
                <div className="flex flex-row gap-2 overflow-x-scroll scrollbar-hide">
                    {/* Sorting Summary */}
                    {selectedSortOption && (
                        <button
                            className="flex items-center bg-[var(--background-secondary)] rounded-full px-2 py-1 text-sm max-w-84 overflow-x-clip text-nowrap"
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
                    {Object.entries(filtersWithoutSorting).map(([key, value]) => (
                        value === undefined || value === null || (Array.isArray(value) && value.length === 0) ? null :
                            <div key={key} className="flex items-center bg-[var(--background-secondary)] rounded-full px-2 py-1">
                                <span className="text-sm max-w-84 overflow-x-clip text-nowrap">{filterDisplayText(key, value)}</span>
                                <button onClick={() => setFilters((prev) => ({ ...prev, [key]: undefined }))} className="ml-1">
                                    <FaTimes />
                                </button>
                            </div>
                    ))}
                </div>

            </div>

            <div className="relative">
                <div className="py-2 px-3 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
                    {/* Iterate through showdownCards and display each card */}
                    {showdownCards?.map((cardRecord, index) => (
                        <div
                            key={cardRecord.id}
                            ref={showdownCards.length === (index + 1) ? lastCardElementRef : null}
                        >
                            <CardItem
                                card={cardRecord.card_data}
                                onClick={() => handleRowClick(cardRecord)}
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

            {/* Add Loading Indicator in the middle of the screen */}
            {isLoading && (
                <div className="
                    absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
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
                    />
                </Modal>
            )}


            {/* MARK: Filters Modal */}
            {showFiltersModal && (
                <Modal onClose={handleFilterApply}>
                    <div className="p-4 min-h-48 max-h-[70vh] md:min-h-128 md:max-h-[90vh]">
                        <div className="flex gap-3 mb-4 items-center border-b-2 border-form-element pb-2">
                            <h2 className="text-xl font-bold">Filter Options</h2>
                            <button
                                onClick={resetFilters}
                                className="
                                    px-3 py-1 
                                    text-[var(--background-primary)] text-xs 
                                    rounded-lg bg-[var(--tertiary)]
                                    hover:bg-[var(--secondary)]
                                    cursor-pointer
                                ">
                                Reset
                            </button>

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


                            <FormSection title="Leagues and Teams" isOpenByDefault={true}>
                                {/* Filters options */}

                                <MultiSelect
                                    label="Organizations"
                                    options={[
                                        { value: 'MLB', label: 'MLB' },
                                        { value: 'NGL', label: 'Negro Leagues' },
                                        { value: 'NON-MLB', label: 'Misc' },
                                    ]}
                                    selections={filtersForEditing.organization}
                                    onChange={(values) => setFiltersForEditing({ ...filtersForEditing, organization: values })}
                                />

                                <MultiSelect
                                    label="Leagues"
                                    options={[
                                        { value: 'AL', label: 'AL' },
                                        { value: 'NL', label: 'NL' },
                                        { value: 'ANL', label: 'ANL' },
                                        { value: 'ECL', label: 'ECL' },
                                        { value: 'EWL', label: 'EWL' },
                                        { value: 'FL', label: 'FL' },
                                        { value: 'NAL', label: 'NAL' },
                                        { value: 'NN2', label: 'NN2' },
                                        { value: 'NNL', label: 'NNL' },
                                        { value: 'NSL', label: 'NSL' },
                                        { value: 'PL', label: 'PL' },
                                        { value: 'UA', label: 'UA' },
                                    ]}
                                    selections={filtersForEditing.league}
                                    onChange={(values) => setFiltersForEditing({ ...filtersForEditing, league: values })}
                                />

                                <MultiSelect
                                    label="Teams"
                                    options={[
                                        { value: 'AB2', label: 'AB2' },
                                        { value: 'AB3', label: 'AB3' },
                                        { value: 'ABC', label: 'ABC' },
                                        { value: 'AC', label: 'AC' },
                                        { value: 'AG', label: 'AG' },
                                        { value: 'ALT', label: 'ALT' },
                                        { value: 'ANA', label: 'ANA' },
                                        { value: 'ARI', label: 'ARI' },
                                        { value: 'ATL', label: 'ATL' },
                                        { value: 'BAL', label: 'BAL' },
                                        { value: 'BBB', label: 'BBB' },
                                        { value: 'BBS', label: 'BBS' },
                                        { value: 'BCA', label: 'BCA' },
                                        { value: 'BE', label: 'BE' },
                                        { value: 'BEG', label: 'BEG' },
                                        { value: 'BLA', label: 'BLA' },
                                        { value: 'BLN', label: 'BLN' },
                                        { value: 'BLU', label: 'BLU' },
                                        { value: 'BOS', label: 'BOS' },
                                        { value: 'BRG', label: 'BRG' },
                                        { value: 'BRO', label: 'BRO' },
                                        { value: 'BSN', label: 'BSN' },
                                        { value: 'BTT', label: 'BTT' },
                                        { value: 'BUF', label: 'BUF' },
                                        { value: 'BWW', label: 'BWW' },
                                        { value: 'CAG', label: 'CAG' },
                                        { value: 'CAL', label: 'CAL' },
                                        { value: 'CBB', label: 'CBB' },
                                        { value: 'CBE', label: 'CBE' },
                                        { value: 'CBN', label: 'CBN' },
                                        { value: 'CBR', label: 'CBR' },
                                        { value: 'CC', label: 'CC' },
                                        { value: 'CCB', label: 'CCB' },
                                        { value: 'CCU', label: 'CCU' },
                                        { value: 'CEG', label: 'CEG' },
                                        { value: 'CEL', label: 'CEL' },
                                        { value: 'CG', label: 'CG' },
                                        { value: 'CHC', label: 'CHC' },
                                        { value: 'CHI', label: 'CHI' },
                                        { value: 'CHT', label: 'CHT' },
                                        { value: 'CHW', label: 'CHW' },
                                        { value: 'CIN', label: 'CIN' },
                                        { value: 'CKK', label: 'CKK' },
                                        { value: 'CLE', label: 'CLE' },
                                        { value: 'CLS', label: 'CLS' },
                                        { value: 'CLV', label: 'CLV' },
                                        { value: 'COB', label: 'COB' },
                                        { value: 'COG', label: 'COG' },
                                        { value: 'COL', label: 'COL' },
                                        { value: 'COR', label: 'COR' },
                                        { value: 'CPI', label: 'CPI' },
                                        { value: 'CRS', label: 'CRS' },
                                        { value: 'CS', label: 'CS' },
                                        { value: 'CSE', label: 'CSE' },
                                        { value: 'CSW', label: 'CSW' },
                                        { value: 'CT', label: 'CT' },
                                        { value: 'CTG', label: 'CTG' },
                                        { value: 'CTS', label: 'CTS' },
                                        { value: 'CUP', label: 'CUP' },
                                        { value: 'DET', label: 'DET' },
                                        { value: 'DM', label: 'DM' },
                                        { value: 'DS', label: 'DS' },
                                        { value: 'DTN', label: 'DTN' },
                                        { value: 'DTS', label: 'DTS' },
                                        { value: 'DW', label: 'DW' },
                                        { value: 'FLA', label: 'FLA' },
                                        { value: 'HAR', label: 'HAR' },
                                        { value: 'HBG', label: 'HBG' },
                                        { value: 'HG', label: 'HG' },
                                        { value: 'HIL', label: 'HIL' },
                                        { value: 'HOU', label: 'HOU' },
                                        { value: 'IA', label: 'IA' },
                                        { value: 'IAB', label: 'IAB' },
                                        { value: 'IC', label: 'IC' },
                                        { value: 'ID', label: 'ID' },
                                        { value: 'IND', label: 'IND' },
                                        { value: 'JRC', label: 'JRC' },
                                        { value: 'KCA', label: 'KCA' },
                                        { value: 'KCC', label: 'KCC' },
                                        { value: 'KCM', label: 'KCM' },
                                        { value: 'KCN', label: 'KCN' },
                                        { value: 'KCP', label: 'KCP' },
                                        { value: 'KCR', label: 'KCR' },
                                        { value: 'LAA', label: 'LAA' },
                                        { value: 'LAD', label: 'LAD' },
                                        { value: 'LOU', label: 'LOU' },
                                        { value: 'LOW', label: 'LOW' },
                                        { value: 'LRG', label: 'LRG' },
                                        { value: 'LVB', label: 'LVB' },
                                        { value: 'MB', label: 'MB' },
                                        { value: 'MGS', label: 'MGS' },
                                        { value: 'MIA', label: 'MIA' },
                                        { value: 'MIL', label: 'MIL' },
                                        { value: 'MIN', label: 'MIN' },
                                        { value: 'MLA', label: 'MLA' },
                                        { value: 'MLN', label: 'MLN' },
                                        { value: 'MON', label: 'MON' },
                                        { value: 'MRM', label: 'MRM' },
                                        { value: 'MRS', label: 'MRS' },
                                        { value: 'NBY', label: 'NBY' },
                                        { value: 'ND', label: 'ND' },
                                        { value: 'NE', label: 'NE' },
                                        { value: 'NEG', label: 'NEG' },
                                        { value: 'NEW', label: 'NEW' },
                                        { value: 'NLG', label: 'NLG' },
                                        { value: 'NS', label: 'NS' },
                                        { value: 'NYC', label: 'NYC' },
                                        { value: 'NYG', label: 'NYG' },
                                        { value: 'NYI', label: 'NYI' },
                                        { value: 'NYM', label: 'NYM' },
                                        { value: 'NYP', label: 'NYP' },
                                        { value: 'NYY', label: 'NYY' },
                                        { value: 'OAK', label: 'OAK' },
                                        { value: 'PBB', label: 'PBB' },
                                        { value: 'PBG', label: 'PBG' },
                                        { value: 'PBS', label: 'PBS' },
                                        { value: 'PC', label: 'PC' },
                                        { value: 'PHA', label: 'PHA' },
                                        { value: 'PHI', label: 'PHI' },
                                        { value: 'PHK', label: 'PHK' },
                                        { value: 'PHQ', label: 'PHQ' },
                                        { value: 'PIT', label: 'PIT' },
                                        { value: 'PK', label: 'PK' },
                                        { value: 'PRO', label: 'PRO' },
                                        { value: 'PS', label: 'PS' },
                                        { value: 'PTG', label: 'PTG' },
                                        { value: 'RIC', label: 'RIC' },
                                        { value: 'ROC', label: 'ROC' },
                                        { value: 'SDP', label: 'SDP' },
                                        { value: 'SEA', label: 'SEA' },
                                        { value: 'SEN', label: 'SEN' },
                                        { value: 'SEP', label: 'SEP' },
                                        { value: 'SFG', label: 'SFG' },
                                        { value: 'SL2', label: 'SL2' },
                                        { value: 'SL3', label: 'SL3' },
                                        { value: 'SLB', label: 'SLB' },
                                        { value: 'SLG', label: 'SLG' },
                                        { value: 'SLM', label: 'SLM' },
                                        { value: 'SLS', label: 'SLS' },
                                        { value: 'SNS', label: 'SNS' },
                                        { value: 'STL', label: 'STL' },
                                        { value: 'STP', label: 'STP' },
                                        { value: 'SYR', label: 'SYR' },
                                        { value: 'TBD', label: 'TBD' },
                                        { value: 'TBR', label: 'TBR' },
                                        { value: 'TC', label: 'TC' },
                                        { value: 'TC2', label: 'TC2' },
                                        { value: 'TEX', label: 'TEX' },
                                        { value: 'TOL', label: 'TOL' },
                                        { value: 'TOR', label: 'TOR' },
                                        { value: 'TT', label: 'TT' },
                                        { value: 'WAP', label: 'WAP' },
                                        { value: 'WAS', label: 'WAS' },
                                        { value: 'WEG', label: 'WEG' },
                                        { value: 'WHS', label: 'WHS' },
                                        { value: 'WIL', label: 'WIL' },
                                        { value: 'WMP', label: 'WMP' },
                                        { value: 'WP', label: 'WP' },
                                        { value: 'WSA', label: 'WSA' },
                                        { value: 'WSH', label: 'WSH' },
                                        { value: 'WSN', label: 'WSN' },
                                    ]}
                                    selections={filtersForEditing.team}
                                    onChange={(values) => {
                                        setFiltersForEditing({ ...filtersForEditing, team: values });
                                    }}
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
                                        { value: 'SP', label: 'SP' },
                                        { value: 'RP', label: 'RP' },
                                        { value: 'CL', label: 'CL' },
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

                                {/* Real PA */}
                                <div className="flex gap-2">
                                    <FormInput
                                        type="number"
                                        inputMode="numeric"
                                        label="Min PA"
                                        placeholder="None"
                                        value={filtersForEditing.min_pa?.toString() || ''}
                                        onChange={(value) => setFiltersForEditing({ ...filtersForEditing, min_pa: Number(value) || undefined })}
                                    />
                                    <FormInput
                                        type="number"
                                        inputMode="numeric"
                                        label="Max PA"
                                        placeholder="None"
                                        value={filtersForEditing.max_pa?.toString() || ''}
                                        onChange={(value) => setFiltersForEditing({ ...filtersForEditing, max_pa: Number(value) || undefined })}
                                    />
                                </div>

                                {/* Real IP */}
                                <div className="flex gap-2">
                                    <FormInput
                                        type="number"
                                        inputMode="numeric"
                                        label="Min Real IP"
                                        placeholder="None"
                                        value={filtersForEditing.min_real_ip?.toString() || ''}
                                        onChange={(value) => setFiltersForEditing({ ...filtersForEditing, min_real_ip: Number(value) || undefined })}
                                    />
                                    <FormInput
                                        type="number"
                                        inputMode="numeric"
                                        label="Max Real IP"
                                        placeholder="None"
                                        value={filtersForEditing.max_real_ip?.toString() || ''}
                                        onChange={(value) => setFiltersForEditing({ ...filtersForEditing, max_real_ip: Number(value) || undefined })}
                                    />
                                </div>
                            </FormSection>

                            <FormSection title="Showdown Attributes" isOpenByDefault={true}>
                                <div className="flex gap-2">
                                    <FormInput
                                        type="number"
                                        inputMode="numeric"
                                        label="Min Ctrl/OB"
                                        placeholder="None"
                                        value={filtersForEditing.min_command?.toString() || ''}
                                        onChange={(value) => setFiltersForEditing({ ...filtersForEditing, min_command: Number(value) || undefined })}
                                    />
                                    <FormInput
                                        type="number"
                                        inputMode="numeric"
                                        label="Max Ctrl/OB"
                                        placeholder="None"
                                        value={filtersForEditing.max_command?.toString() || ''}
                                        onChange={(value) => setFiltersForEditing({ ...filtersForEditing, max_command: Number(value) || undefined })}
                                    />
                                </div>

                                <div className="flex gap-2">
                                    <FormInput
                                        type="number"
                                        inputMode="numeric"
                                        label="Min PTS"
                                        placeholder="None"
                                        value={filtersForEditing.min_points?.toString() || ''}
                                        onChange={(value) => setFiltersForEditing({ ...filtersForEditing, min_points: Number(value) || undefined })}
                                    />
                                    <FormInput
                                        type="number"
                                        inputMode="numeric"
                                        label="Max PTS"
                                        placeholder="None"
                                        value={filtersForEditing.max_points?.toString() || ''}
                                        onChange={(value) => setFiltersForEditing({ ...filtersForEditing, max_points: Number(value) || undefined })}
                                    />
                                </div>

                                <div className="flex gap-2">
                                    <FormInput
                                        type="number"
                                        inputMode="numeric"
                                        label="Min Speed"
                                        placeholder="None"
                                        value={filtersForEditing.min_speed?.toString() || ''}
                                        onChange={(value) => setFiltersForEditing({ ...filtersForEditing, min_speed: Number(value) || undefined })}
                                    />
                                    <FormInput
                                        type="number"
                                        inputMode="numeric"
                                        label="Max Speed"
                                        placeholder="None"
                                        value={filtersForEditing.max_speed?.toString() || ''}
                                        onChange={(value) => setFiltersForEditing({ ...filtersForEditing, max_speed: Number(value) || undefined })}
                                    />
                                </div>


                            </FormSection>

                        </div>


                    </div>
                </Modal>
            )}
        </div>
    );
}