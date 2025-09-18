import { useState, useEffect } from "react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type CardDatabaseRecord, fetchCardData } from "../../api/card_db/cardDatabase";
import { CardDetail } from "./CardDetail";
import { type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { Modal } from "../shared/Modal";
import CardChart from "./card_elements/CardChart";
import CardCommand from "./card_elements/CardCommand";
import { imageForSet, useSiteSettings } from "../shared/SiteSettingsContext";
import { FaCompass, FaFilter, FaGripHorizontal, FaTable } from "react-icons/fa";

// Filter components
import FormInput from "../customs/FormInput";
import MultiSelect from "../shared/MultiSelect";
import CustomSelect from "../shared/CustomSelect";
import { CardItem } from "./CardItem";

// --------------------------------------------
// MARK: - Table column defs
// --------------------------------------------

const h = createColumnHelper<CardDatabaseRecord>();

/** Create a column helper that tells tanstack the format of the data*/
const showdownCardColumns: ColumnDef<CardDatabaseRecord, any>[] = [
    h.accessor("name", {
        header: "Name/Year",
        cell: ({ row }) => {
            const name = row.original.name.toUpperCase();
            const year = row.original.year;
            const team = row.original.team;
            return (
                <div className="flex flex-col max-w-28 sm:max-w-40">
                    <div className="font-extrabold text-nowrap sm:text-nowrap overflow-x-hidden">
                        {name}
                    </div>
                    <div className="italic text-[11px]">
                        {year} {team}
                    </div>
                </div>
                
            );
        }
    }),
    h.accessor("showdown_set", {
        header: "Set",
        cell: ({ getValue }) => {
            const set = getValue();
            const setImage = imageForSet(set);
            return (
                <div className="font-bold w-12">
                    {setImage && <img src={setImage} alt={set} className="inline object-contain align-middle" />}
                    {/* Fallback to showing the set string if no image is found */}
                    {!setImage && set}
                </div>
            );
        },
        meta: {
            className: "hidden sm:table-cell",
        }
    }),
    h.accessor("team", {
        header: "Team",
        meta: {
            className: "hidden",
        }
    }),
    h.accessor("points", {
        header: "PTS",
        meta: {
            className: "hidden sm:table-cell",
        }
    }),
    h.accessor("positions_and_defense_string", {
        header: "Defense",
        cell: ({ getValue }) => {
            // Clean up the value by removing spaces before +/-
            // Prevents awkward line breaks in table
            const value = (getValue() as string).replaceAll(' +', '+').replaceAll(' -', '-');
            return (
                <div className="max-w-18"> {value} </div>
            );
        },
        meta: {
            className: "hidden sm:table-cell",
        }
    }),
    h.accessor("speed_or_ip", {
        header: "SPD/IP",
        cell: ({ row }) => {
            if (!row.original.card_data) {
                return '—';
            }
            const value = row.original.player_type === "HITTER" 
                            ? `${row.original.card_data.speed.letter}(${row.original.card_data.speed.speed})` 
                            : `IP ${row.original.card_data.ip}`;
            return (
                <div >
                    {value}
                </div>
            );
        },
        meta: {
            className: "hidden sm:table-cell",
        }
    }),

    h.accessor("command", {
        header: "Ctrl/OB",
        cell: ({ row }) => {
            if (!row.original.card_data) {
                return '—';
            }
            return (
                <CardCommand card={row.original.card_data} className="w-8 h-8 sm:w-10 sm:h-10" />
            );
        },
        meta: {
            className: "max-w-15",
        }
    }),
    h.accessor("card_data.chart", {
        header: "Chart",
        cell: ({ row }) => {

            if (!row.original.card_data) {
                return '—';
            }
            return <CardChart card={row.original.card_data} />
        },
    }),
];

type ShowdownCardTableProps = {
    showdownCards?: CardDatabaseRecord[] | null;
    className?: string;
};

const CardDisplayFormat = {
    TABLE: "table",
    GRID: "grid",
} as const;

type CardDisplayFormat = typeof CardDisplayFormat[keyof typeof CardDisplayFormat];

// --------------------------------------------
// MARK: - Filters
// --------------------------------------------

/** State for the custom card form */
interface FilterSelections {

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
};

// --------------------------------------------
// MARK: - Component
// --------------------------------------------

export default function ShowdownCardTable({ className }: ShowdownCardTableProps) {

    // State for showdown cards
    const [showdownCards, setShowdownCards] = useState<CardDatabaseRecord[] | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedCard, setSelectedCard] = useState<CardDatabaseRecord | null>(null);

    // Display
    const [cardDisplayType, setCardDisplayType] = useState<CardDisplayFormat>(CardDisplayFormat.GRID);

    // Modals
    const [showFiltersModal, setShowFiltersModal] = useState(false);
    const [showPlayerDetailModal, setShowPlayerDetailModal] = useState(false);

    // State for Set
    const { userShowdownSet } = useSiteSettings();

    // Separate search from filters
    const [searchText, setSearchText] = useState('');
    const [debouncedSearchText, setDebouncedSearchText] = useState('');

    // Filters
    const [filters, setFilters] = useState<FilterSelections>(DEFAULT_FILTER_SELECTIONS);
    const [filtersForEditing, setFiltersForEditing] = useState<FilterSelections>(DEFAULT_FILTER_SELECTIONS);

    // Refetch the cards if filters or set are changed
    useEffect(() => {
        if (userShowdownSet) {
            getCardsData();
        }
    }, [userShowdownSet, filters, debouncedSearchText]);

    // Debounce search text only
    useEffect(() => {
        if (searchText.length === 0) {
            setDebouncedSearchText('');
            return;
        }
        const timeoutId = setTimeout(() => {
            setDebouncedSearchText(searchText);
        }, 300); // Shorter delay for search

        return () => clearTimeout(timeoutId);
    }, [searchText]);

    const getCardsData = async () => {
        setIsLoading(true);
        try {
            const searchFilters = debouncedSearchText ? { search: debouncedSearchText } : {};
            const combinedFilters = { ...filters, ...searchFilters, showdown_set: userShowdownSet };
            // Remove filters with empty arrays or undefined values
            const cleanedFilters = Object.fromEntries(
                Object.entries(combinedFilters).filter(([_, v]) => v !== undefined && v !== null && v.length !== 0)
            );
            const data = await fetchCardData(cleanedFilters);
            if (data.length > 0) {
                console.log(data[0]);
            }
            setShowdownCards(data);
        } catch (error) {
            console.error("Error fetching showdown cards:", error);
        } finally {
            setIsLoading(false);
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
            // Just update the filters - useEffect will handle the API call
            setFilters(filtersForEditing);
        }
        setShowFiltersModal(false);
    }

    const resetFilters = () => {
        setFiltersForEditing(DEFAULT_FILTER_SELECTIONS);
    }

    return (
        <div className={`flex flex-col ${className}`}>

            {/* Search Bar and Filters */}
            <div className="sticky top-0 z-10 flex flex-col gap-2 w-full 
                            bg-background-secondary/95 backdrop-blur p-3">
                <div className="flex items-center space-x-2 px-2 text-lg">
                    <FaCompass className="text-primary" />
                    <span className="font-bold text-2xl text-nowrap">Explore Cards</span>
                </div>

                <div className="flex items-center space-x-2">
                    {/* Search Input */}
                    <FormInput
                        label=""
                        type="text"
                        value={searchText || ''}
                        placeholder="Search..."
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
                            flex items-center space-x-2
                            hover:bg-[var(--background-secondary-hover)]
                        ">
                            <FaFilter className="text-primary" />
                            <span>Filter</span>
                    </button>

                    <CustomSelect
                        value={cardDisplayType}
                        onChange={(value) => setCardDisplayType(value as CardDisplayFormat)}
                        options={[
                            { value: CardDisplayFormat.GRID, label: "Grid", icon: <FaGripHorizontal /> },
                            { value: CardDisplayFormat.TABLE, label: "Table", icon: <FaTable /> },
                        ]}
                        className="w-24"
                    />

                </div>

            </div>

            <div className="relative">
                {cardDisplayType === CardDisplayFormat.GRID && (
                    <div className="py-2 px-3 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
                        {/* Iterate through showdownCards and display each card */}
                        {showdownCards?.map((cardRecord) => (
                            <CardItem key={cardRecord.id} card={cardRecord.card_data} onClick={() => handleRowClick(cardRecord)} />
                        ))}
                    </div>
                )}

                {cardDisplayType === CardDisplayFormat.TABLE && (
                    <BasicDataTable 
                        data={showdownCards || []}
                        columns={showdownCardColumns}
                        className="text-xs md:text-sm mx-3 mb-3"
                        onRowClick={handleRowClick}
                    />
                )}
            </div>

            

            {/* Player Detail Modal */}
            {showPlayerDetailModal && selectedCard && (
                <Modal onClose={handleCloseModal}>
                    <CardDetail 
                        showdownBotCardData={{card: selectedCard.card_data} as ShowdownBotCardAPIResponse} 
                    />
                </Modal>
            )}

            {/* Filters Modal */}
            {showFiltersModal && (
                <Modal onClose={handleFilterApply}>
                    <div className="p-4 min-h-72">
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
                        <div className="grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-4">
                            {/* Filters options */}

                            <MultiSelect
                                label="Organizations"
                                options={[
                                    { value: 'MLB', label: 'MLB' },
                                    { value: 'NGL', label: 'Negro Leagues' },
                                    { value: 'NON-MLB', label: 'Misc' },
                                ]}
                                selections={filtersForEditing.organization}
                                onChange={(values) => setFiltersForEditing({...filtersForEditing, organization: values})}
                            />

                            <MultiSelect
                                label="Leagues"
                                options={[
                                    { value: 'AL', label: 'AL' },
                                    { value: 'NL', label: 'NL' },
                                ]}
                                selections={filtersForEditing.league}
                                onChange={(values) => setFiltersForEditing({...filtersForEditing, league: values})}
                            />

                            <MultiSelect
                                label="Teams"
                                options={[
                                    { value: 'NYY', label: 'NYY' },
                                    { value: 'BOS', label: 'BOS' },
                                ]}
                                selections={filtersForEditing.team}
                                onChange={(values) => {
                                    setFiltersForEditing({...filtersForEditing, team: values});
                                }}
                            />

                            <MultiSelect
                                label="Player Type"
                                options={[
                                    { value: 'HITTER', label: 'Hitter' },
                                    { value: 'PITCHER', label: 'Pitcher' },
                                ]}
                                selections={filtersForEditing.player_type}
                                onChange={(values) => setFiltersForEditing({...filtersForEditing, player_type: values})}
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
                                onChange={(values) => setFiltersForEditing({...filtersForEditing, positions: values})}
                            />

                            <MultiSelect
                                label="Hand"
                                options={[
                                    { value: 'L', label: 'Left' },
                                    { value: 'R', label: 'Right' },
                                    { value: 'S', label: 'Switch' },
                                ]}
                                selections={filtersForEditing.hand || []}
                                onChange={(values) => setFiltersForEditing({...filtersForEditing, hand: values})}
                            />

                            {/* Real PA */}
                            <div className="flex gap-2">
                                <FormInput
                                    type="number"
                                    inputMode="numeric"
                                    label="Min PA"
                                    placeholder="None"
                                    value={filtersForEditing.min_pa?.toString() || ''}
                                    onChange={(value) => setFiltersForEditing({...filtersForEditing, min_pa: Number(value) || undefined})}
                                />
                                <FormInput
                                    type="number"
                                    inputMode="numeric"
                                    label="Max PA"
                                    placeholder="None"
                                    value={filtersForEditing.max_pa?.toString() || ''}
                                    onChange={(value) => setFiltersForEditing({...filtersForEditing, max_pa: Number(value) || undefined})}
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
                                    onChange={(value) => setFiltersForEditing({...filtersForEditing, min_real_ip: Number(value) || undefined})}
                                />
                                <FormInput
                                    type="number"
                                    inputMode="numeric"
                                    label="Max Real IP"
                                    placeholder="None"
                                    value={filtersForEditing.max_real_ip?.toString() || ''}
                                    onChange={(value) => setFiltersForEditing({...filtersForEditing, max_real_ip: Number(value) || undefined})}
                                />
                            </div>

                            <div className="flex gap-2">
                                <FormInput
                                    type="number"
                                    inputMode="numeric"
                                    label="Min Ctrl/OB"
                                    placeholder="None"
                                    value={filtersForEditing.min_command?.toString() || ''}
                                    onChange={(value) => setFiltersForEditing({...filtersForEditing, min_command: Number(value) || undefined})}
                                />
                                <FormInput
                                    type="number"
                                    inputMode="numeric"
                                    label="Max Ctrl/OB"
                                    placeholder="None"
                                    value={filtersForEditing.max_command?.toString() || ''}
                                    onChange={(value) => setFiltersForEditing({...filtersForEditing, max_command: Number(value) || undefined})}
                                />
                            </div>

                            <div className="flex gap-2">
                                <FormInput
                                    type="number"
                                    inputMode="numeric"
                                    label="Min PTS"
                                    placeholder="None"
                                    value={filtersForEditing.min_points?.toString() || ''}
                                    onChange={(value) => setFiltersForEditing({...filtersForEditing, min_points: Number(value) || undefined})}
                                />
                                <FormInput
                                    type="number"
                                    inputMode="numeric"
                                    label="Max PTS"
                                    placeholder="None"
                                    value={filtersForEditing.max_points?.toString() || ''}
                                    onChange={(value) => setFiltersForEditing({...filtersForEditing, max_points: Number(value) || undefined})}
                                />
                            </div>

                            <div className="flex gap-2">
                                <FormInput
                                    type="number"
                                    inputMode="numeric"
                                    label="Min Speed"
                                    placeholder="None"
                                    value={filtersForEditing.min_speed?.toString() || ''}
                                    onChange={(value) => setFiltersForEditing({...filtersForEditing, min_speed: Number(value) || undefined})}
                                />
                                <FormInput
                                    type="number"
                                    inputMode="numeric"
                                    label="Max Speed"
                                    placeholder="None"
                                    value={filtersForEditing.max_speed?.toString() || ''}
                                    onChange={(value) => setFiltersForEditing({...filtersForEditing, max_speed: Number(value) || undefined})}
                                />
                            </div>
                            

                        </div>
                    </div>
                </Modal>
            )}
        </div>
    );
}