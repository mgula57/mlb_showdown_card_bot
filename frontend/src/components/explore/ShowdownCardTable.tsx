import { useState, useEffect } from "react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type CardDatabaseRecord, fetchCardData } from "../../api/card_db/cardDatabase";
import { formatStatValue } from "../../functions/formatters";
import { CardDetail } from "../cards/CardDetail";
import { type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { Modal } from "../shared/Modal";

const h = createColumnHelper<CardDatabaseRecord>();

/** Create a column helper that tells tanstack the format of the data*/
const showdownCardColumns: ColumnDef<CardDatabaseRecord, any>[] = [
    h.accessor("name", {
        header: "Name",
        cell: ({ getValue }) => (
            <div className="font-bold">
                {getValue()}
            </div>
        )
    }),
    h.accessor("year", {
        header: "Year", 
        cell: ({ getValue }) => (
            <div className="font-bold">
                {getValue()}
            </div>
        )
    }),
    h.accessor("team", {
        header: "Team",
    }),
    h.accessor("points", {
        header: "Points",
    }),
    h.accessor("positions_and_defense_string", {
        header: "Defense",
    }),

    h.accessor("command", {
        header: "Ctrl/OB",
    }),
    h.accessor("card_data.chart", {
        header: "Chart",
        cell: ({ row }) => {
            const chartData = row.original.card_data?.chart?.ranges;
            
            if (!chartData) {
                return <div>No chart data available</div>;
            }

            const showdownSet = row.original.card_data?.set || '2000';

            // Sort the values based on manual list of keys
            const sortOrder = showdownSet === '2000' 
                                ? ['so', 'pu', 'gb', 'fb', 'bb', '1b', '1b+', '2b', '3b', 'hr']
                                : ['pu', 'so', 'gb', 'fb', 'bb', '1b', '1b+', '2b', '3b', 'hr'];
            const sortedChartData = Object.fromEntries(
                Object.entries(chartData).sort((a, b) => {
                    const indexA = sortOrder.indexOf(a[0].toLowerCase());
                    const indexB = sortOrder.indexOf(b[0].toLowerCase());
                    return (indexA === -1 ? Number.MAX_VALUE : indexA) - (indexB === -1 ? Number.MAX_VALUE : indexB);
                }
            ));

            // Use sorted data for rendering
            const chartDataToRender = sortedChartData;

            // Color mapping for different result types
            const getColorClass = (key: string, index: number) => {
                const lowerKey = key.toLowerCase();
                const primaryColor = row.original.card_data?.image.color_primary || 'rgb(0, 0, 0)';
                
                // Hitting results (typically yellow/gold)
                if (lowerKey.includes('so') || lowerKey.includes('gb') || lowerKey.includes('fb') || lowerKey.includes('pu')) {
                    return { 
                        backgroundColor: primaryColor, 
                        color: 'white',
                        className: '' // No Tailwind bg class
                    };
                }                
                // Default fallback
                return { 
                    backgroundColor: '',
                    color: '',
                    className: 'bg-[var(--background-secondary)] text-black'
                };
            };

            return (
                <div className="inline-flex rounded-lg overflow-hidden text-xs font-semibold border-2 border-form-element">
                    {Object.entries(chartDataToRender).map(([key, value], index) => {
                        const colorInfo = getColorClass(key, index);
                        
                        return (
                            <div
                                key={key}
                                className={`
                                    px-2 py-1 text-center min-w-12 text-primary
                                    ${colorInfo.className}
                                    border-r border-form-element last:border-r-0
                                `}
                                style={colorInfo.backgroundColor ? {
                                    backgroundColor: colorInfo.backgroundColor,
                                    color: colorInfo.color || ''
                                } : {}}
                            >
                                <div className="text-xs font-bold">{key}</div>
                                <div className="text-xs text-nowrap">{String(value)}</div>
                            </div>
                        );
                    })}
                </div>
            );
        },
    }),
    h.accessor("g", {
        header: "Games",
    }),
];

type ShowdownCardTableProps = {
    showdownCards?: CardDatabaseRecord[] | null;
    className?: string;
};

export default function ShowdownCardTable({ className }: ShowdownCardTableProps) {

    // State for showdown cards
    const [showdownCards, setShowdownCards] = useState<CardDatabaseRecord[] | null>(null);
    const [selectedCard, setSelectedCard] = useState<CardDatabaseRecord | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // If showdownCards is not provided, fetch from API
    useEffect(() => {
        if (!showdownCards) {
            fetchCardData({})
                .then(data => {
                    console.log("Fetched Showdown Cards:", data);
                    // Update state or perform actions with the fetched data
                    setShowdownCards(data);
                })
                .catch(err => {
                    console.error("Error fetching showdown cards:", err);
                });
        }
    }, []);

    // Handle row selection
    const handleRowClick = (card: CardDatabaseRecord) => {
        setSelectedCard(card);
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedCard(null);
    };

    return (
        <div className="p-6">

            {/* Search Bar and Filters */}


            {/* Table */}
            <BasicDataTable 
                data={showdownCards || []}
                columns={showdownCardColumns}
                className={className}
                onRowClick={handleRowClick}
            />

            {/* Modal */}
            {isModalOpen && selectedCard && (
                <Modal onClose={handleCloseModal} title={`${selectedCard.name} (${selectedCard.year})`}>
                    <CardDetail 
                        showdownBotCardData={{card: selectedCard.card_data} as ShowdownBotCardAPIResponse} 
                    />
                </Modal>
            )}
        </div>
    );
}