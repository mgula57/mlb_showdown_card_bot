import { useMemo, useState } from "react";
import { type RosterSlot } from "../../api/mlbAPI";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { CardDetail } from "../cards/CardDetail";
import { type ShowdownBotCard, type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { Modal } from "../shared/Modal";
import CardChart from "../cards/card_elements/CardChart";
import CardCommand from "../cards/card_elements/CardCommand";
import { imageForSet } from "../shared/SiteSettingsContext";
import { getContrastColor } from "../shared/Color";

const h = createColumnHelper<RosterSlot>();

const getCardMapKey = (slot: RosterSlot): string =>
    slot.is_pitcher_slot ? `${slot.person.id}-P` : String(slot.person.id);

type TeamRosterPositionTableProps = {
    position: string;
    slots: RosterSlot[];
    cardMap: Record<string, ShowdownBotCardAPIResponse>;
    className?: string;
    tableClassName?: string;
};

export default function TeamRosterPositionTable({ position, slots, cardMap, className, tableClassName }: TeamRosterPositionTableProps) {

    const [selectedCard, setSelectedCard] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleRowClick = (slot: RosterSlot) => {
        const response = cardMap[getCardMapKey(slot)];
        if (!response) {
            return;
        }
        setSelectedCard(response);
        setIsModalOpen(true);
    };

    const showdownCardColumns = useMemo((): ColumnDef<RosterSlot, any>[] => {
        const getCard = (slot: RosterSlot): ShowdownBotCard | undefined =>
            cardMap[getCardMapKey(slot)]?.card ?? undefined;

        return [
    h.accessor((slot) => getCard(slot)?.name || slot.person.full_name || "-", {
        id: "name",
        header: "Name",
        cell: ({ row, getValue }) => {
            const card = getCard(row.original);
            const name = getValue();
            const year = card?.year || "-";
            const isWbc = card?.image.edition === 'WBC';
            const useLeague = isWbc && card.league && !['AL', 'NL', 'MLB'].includes(card.league);
            const team = (useLeague ? card?.league : card?.team) || "-";
            const secondaryColor = (['NYM', 'SDP'].includes(team) && !isWbc ? card?.image.color_secondary : card?.image.color_primary) || "#000000";
            const isReplacement = card?.stats_period?.type === "REPLACEMENT";
            return (
                <div className="flex flex-col gap-0 max-w-28 sm:max-w-40">
                    <div className="font-extrabold text-nowrap sm:text-nowrap overflow-x-scroll">
                        {name}
                    </div>
                    <div className="flex flex-row italic text-[11px] gap-1">
                        {isReplacement ? "-" : `${year} ${team}`}
                        {card?.icons && (
                            <>
                                {card.icons.map((icon, index) => (
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
    h.accessor((slot) => getCard(slot)?.speed.speed ?? "-", {
        id: "speed_or_ip",
        header: "SPD/IP",
        meta: {
            className: "hidden sm:table-cell",
        },
        cell: ({ row, getValue }) => {
            const card = getCard(row.original);
            const isPitcher = card?.chart.is_pitcher;

            if (isPitcher) {
                const inningsPitched = card?.ip || "-";
                return `${inningsPitched} IP`;
            } else {
                const speed = getValue();
                const speedLetter = card?.speed?.letter || "";
                const fullSpeed = `${speedLetter}(${speed})`;
                return fullSpeed;
            }
        }
    }),
    
    h.accessor((slot) => {
        return (
            getCard(slot)?.positions_and_defense_string.replace(" +", "+") ||
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

    h.accessor((slot) => getCard(slot)?.chart?.command, {
        id: "command",
        header: "Ctrl/OB",
        cell: ({ row }) => {
            const card = getCard(row.original);
            if (!card) {
                return '—';
            }
            return (
                <CardCommand
                    isPitcher={card.chart.is_pitcher}
                    primaryColor={card.image.color_primary}
                    secondaryColor={card.image.color_secondary}
                    command={card.chart.command}
                    team={card.wbc_team || card.team}
                    className="w-10 h-10"
                />
            );
        },
    }),
    h.accessor((slot) => getCard(slot)?.chart?.ranges, {
        id: "chart",
        header: "Chart",
        cell: ({ row }) => {
            const card = getCard(row.original);
            if (!card) {
                return '—';
            }
            return (
                <CardChart
                    chartRanges={card.chart.ranges}
                    showdownSet={card.set}
                    primaryColor={card.image.color_primary}
                    secondaryColor={card.image.color_secondary}
                    team={card.wbc_team || card.team}
                    cellClassName="min-w-8 max-w-11"
                    className="max-w-xl"
                />
            );
        },
    }),
    h.accessor((slot) => getCard(slot)?.set, {
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
