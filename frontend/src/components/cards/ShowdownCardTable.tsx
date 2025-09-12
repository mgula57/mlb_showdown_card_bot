import { useState, useEffect } from "react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type CardDatabaseRecord, fetchCardData } from "../../api/card_db/cardDatabase";
import { CardDetail } from "./CardDetail";
import { type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { Modal } from "../shared/Modal";
import CardChart from "./card_elements/CardChart";
import CardCommand from "./card_elements/CardCommand";

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
        cell: ({ row }) => {
            if (!row.original.card_data) {
                return '—';
            }
            return <CardCommand card={row.original.card_data} className="w-10 h-10" />
        },
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