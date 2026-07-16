import { useMemo, useState } from "react";
import { type RosterSlot } from "../../api/mlbAPI";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { CardDetail } from "../cards/CardDetail";
import { fetchCardById, type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { type CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import { CardSource } from "../../types/cardSource";
import { Modal } from "../shared/Modal";
import { CardChart } from "../cards/card_elements/CardChart";
import CardCommand from "../cards/card_elements/CardCommand";
import { imageForSet } from "../shared/SiteSettingsContext";
import { getContrastColor } from "../shared/Color";

const h = createColumnHelper<RosterSlot>();

const getCardMapKey = (slot: RosterSlot): string =>
    slot.is_pitcher_slot ? `${slot.person.id}-P` : String(slot.person.id);

type TeamRosterPositionTableProps = {
    position: string;
    slots: RosterSlot[];
    cardMap: Record<string, CardDatabaseRecord>;
    className?: string;
    tableClassName?: string;
};

export default function TeamRosterPositionTable({ position, slots, cardMap, className, tableClassName }: TeamRosterPositionTableProps) {

    const [selectedCard, setSelectedCard] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Card_bot rows are flat/summary only, so lazily fetch the full nested card for the detail modal
    const handleRowClick = (slot: RosterSlot) => {
        const record = cardMap[getCardMapKey(slot)];
        if (!record) {
            return;
        }
        fetchCardById(record.id, CardSource.BOT)
            .then((response) => {
                setSelectedCard(response);
                setIsModalOpen(true);
            })
            .catch((err) => console.error("Failed to fetch full card:", err));
    };

    const showdownCardColumns = useMemo((): ColumnDef<RosterSlot, any>[] => {
        const getCard = (slot: RosterSlot): CardDatabaseRecord | undefined =>
            cardMap[getCardMapKey(slot)];

        return [
    h.accessor((slot) => getCard(slot)?.name || slot.person.full_name || "-", {
        id: "name",
        header: "Name",
        cell: ({ row, getValue }) => {
            const card = getCard(row.original);
            const ptsChange = card?.points_change;
            const name = getValue();
            const year = card?.card_year || "-";
            const isWbc = card?.edition === 'WBC';
            const useLeague = isWbc && card.league && !['AL', 'NL', 'MLB'].includes(card.league);
            const team = (useLeague ? card?.league : card?.team) || "-";
            const secondaryColor = (['NYM', 'SDP'].includes(team) && !isWbc ? card?.color_secondary : card?.color_primary) || "#000000";
            return (
                <div className="flex flex-col gap-0 max-w-28 sm:max-w-40">
                    <div className="font-extrabold text-nowrap sm:text-nowrap overflow-x-scroll scrollbar-hide">
                        {name}
                    </div>
                    <div className="flex flex-row italic text-[11px] gap-1 items-center">
                        {`${year} ${team}`}
                        {ptsChange != null && ptsChange !== 0 && (
                            <span className={`not-italic text-[9px] font-bold leading-none ${ptsChange > 0 ? 'text-(--green)' : 'text-(--red)'}`}>
                                {ptsChange > 0 ? '▲' : '▼'}{Math.abs(ptsChange)}
                            </span>
                        )}
                        {card?.icons_list && (
                            <>
                                {card.icons_list.map((icon, index) => (
                                    <div 
                                        key={index} 
                                        className="
                                            text-[8px] flex w-4 h-4 
                                            items-center font-bold justify-center 
                                            rounded-full tracking-tight shrink-0
                                            border border-(--divider)
                                        " 
                                        style={{ backgroundColor: secondaryColor, color: getContrastColor(secondaryColor) }}
                                    >
                                        {icon}
                                    </div>
                                ))}
                            </>
                        )}
                    </div>
                </div>
            )
        }
    }),
    h.accessor((slot) => getCard(slot)?.team || "-", {
        id: "team",
        header: "Team",
        meta: {
            className: "hidden",
        }
    }),
    h.accessor((slot) => getCard(slot)?.points ?? "-", {
        id: "points",
        header: "PTS",
    }),
    h.accessor((slot) => getCard(slot)?.speed ?? "-", {
        id: "speed_or_ip",
        header: "SPD/IP",
        meta: {
            className: "hidden sm:table-cell",
        },
        cell: ({ row, getValue }) => {
            const card = getCard(row.original);
            const isPitcher = card?.is_pitcher;

            if (isPitcher) {
                const inningsPitched = card?.ip || "-";
                return `${inningsPitched} IP`;
            } else {
                const speed = getValue();
                const speedLetter = card?.speed_letter || "";
                const fullSpeed = `${speedLetter}(${speed})`;
                return fullSpeed;
            }
        }
    }),
    
    h.accessor((slot) => {
        return (
            getCard(slot)?.positions_and_defense_string?.replace(" +", "+") ||
            slot.position.abbreviation ||
            slot.position.code ||
            slot.position.name ||
            slot.position.description ||
            "-"
        );
    }, {
        id: "positions_and_defense_string",
        header: "Def"
    }),

    h.accessor((slot) => getCard(slot)?.command, {
        id: "command",
        header: "Ctrl/OB",
        cell: ({ row }) => {
            const card = getCard(row.original);
            if (!card) {
                return '—';
            }
            return (
                <CardCommand
                    isPitcher={card.is_pitcher}
                    primaryColor={card.color_primary || "#000000"}
                    secondaryColor={card.color_secondary || "#000000"}
                    command={card.command}
                    team={card.wbc_team || card.team}
                    className="w-10 h-10"
                />
            );
        },
    }),
    h.accessor((slot) => getCard(slot)?.chart_ranges, {
        id: "chart",
        header: "Chart",
        cell: ({ row }) => {
            const card = getCard(row.original);
            if (!card) {
                return '—';
            }
            return (
                <CardChart
                    chartRanges={card.chart_ranges}
                    showdownSet={card.showdown_set}
                    primaryColor={card.color_primary || "#000000"}
                    secondaryColor={card.color_secondary || "#000000"}
                    team={card.wbc_team || card.team}
                    cellClassName="min-w-8 max-w-11"
                    className="max-w-xl"
                />
            );
        },
    }),
    h.accessor((slot) => getCard(slot)?.showdown_set, {
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
        ];
    }, [cardMap]);

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedCard(null);
    };

    const sortedSlots = [...slots].sort((a, b) =>
        (a.person.full_name || "").localeCompare(b.person.full_name || "")
    );
    const initialSorting = position === 'PITCHER' ? [{id: "positions_and_defense_string", desc: false}, { id: "points", desc: true }] : [{ id: "points", desc: true }];

    return (
        <section className={`overflow-hidden ${className || ""}`}>
            <h3 className="px-4 py-2 text-sm font-semibold uppercase text-(--text-secondary)">
                {position}
            </h3>
            <BasicDataTable 
                data={sortedSlots}
                columns={showdownCardColumns}
                initialSorting={initialSorting}
                initialColumnPinning={{ left: ['name'] }}
                className={tableClassName || "rounded-none border-0"}
                onRowClick={handleRowClick}
            />

            <div className={isModalOpen ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={handleCloseModal} isVisible={!!selectedCard}>
                    <CardDetail
                        showdownBotCardData={selectedCard!}
                        hideTrendGraphs={true}
                        context="home"
                        parent='home'
                    />
                </Modal>
            </div>
        </section>
    );
}
