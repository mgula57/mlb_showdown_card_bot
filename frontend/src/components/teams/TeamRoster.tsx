/**
 * @fileoverview TeamRoster - Depth chart display grouped by roster position
 */

import { useEffect, useState } from "react";
import { type Roster, type RosterSlot } from "../../api/mlbAPI";
import { CardItemFromCard } from "../cards/CardItem";
import TeamRosterPositionTable from "./TeamRosterPositionTable";
import { Modal } from "../shared/Modal";
import { CardDetail } from "../cards/CardDetail";
import type { ShowdownBotCard, ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
interface TeamRosterProps {
    roster: Roster | null;
}

const getTopPlayerLimit = (width: number): number => {
    if (width < 640) {
        return 3;
    }
    if (width < 1280) {
        return 4;
    }
    if (width < 1536) {
        return 6;
    }
    return 8;
};

const getPositionLabel = (slot: RosterSlot): string => {
    if (typeof slot.position === "string") {
        return slot.position;
    }
    return slot.position.type || slot.position.abbreviation || slot.position.code || slot.position.name || "Unknown";
};

export default function TeamRoster({ roster }: TeamRosterProps) {
    const rosterSlots = roster?.roster ?? [];
    const [topPlayerLimit, setTopPlayerLimit] = useState<number>(() => {
        if (typeof window === "undefined") {
            return 3; // Default for server-side rendering
        }
        return getTopPlayerLimit(window.innerWidth);
    });
    const [selectedCard, setSelectedCard] = useState<ShowdownBotCard | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleRowClick = (slot: RosterSlot) => {
        if (!slot.person.showdown_card_data) {
            return;
        }
        setSelectedCard(slot.person.showdown_card_data);
        setIsModalOpen(true);
    }

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedCard(null);
    };

    useEffect(() => {
        const handleResize = () => {
            setTopPlayerLimit(getTopPlayerLimit(window.innerWidth));
        };

        handleResize();
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    if (rosterSlots.length === 0) {
        return (
            <div className="mt-6 text-sm text-(--text-secondary)">
                No roster data available.
            </div>
        );
    }

    const groupedByPosition = rosterSlots.reduce<Record<string, RosterSlot[]>>((groups, slot) => {
        const positionKey = getPositionLabel(slot);
        if (!groups[positionKey]) {
            groups[positionKey] = [];
        }
        groups[positionKey].push(slot);
        return groups;
    }, {});

    const orderedPositions = Object.keys(groupedByPosition)
        .sort((a, b) => a.localeCompare(b));
    const topPlayers = [...rosterSlots]
        .filter((slot) => slot.person.showdown_card_data)
        .sort((a, b) => (b.person.showdown_card_data?.stats_period.type === "REPLACEMENT" ? -1 : 0) - (a.person.showdown_card_data?.stats_period?.type === "REPLACEMENT" ? -1 : 0))
        .sort((a, b) => (b.person.showdown_card_data?.points || 0) - (a.person.showdown_card_data?.points || 0))
        .slice(0, topPlayerLimit);

    return (
        <div className="mt-6 space-y-8">
            <section className="bg-(--background-secondary) rounded-lg border border-(--divider) overflow-hidden">
                <h3 className="px-4 py-2 text-sm font-semibold uppercase text-(--text-secondary) bg-(--background-quaternary)">
                    Top Players
                </h3>
                {topPlayers.length === 0 ? (
                    <div className="px-4 py-3 text-sm text-(--text-secondary)">No showdown card data available.</div>
                ) : (
                    <div className="p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-2">
                        {topPlayers.map((slot) => {
                            const card = slot.person.showdown_card_data;
                            return (
                                <CardItemFromCard
                                    key={slot.person.id}
                                    card={card}
                                    className="w-full"
                                    onClick={() => handleRowClick(slot)}
                                />
                            );
                        })}
                    </div>
                )}
            </section>

            <div className="bg-(--background-secondary) rounded-lg border border-(--divider) overflow-hidden">
                <h3 className="px-4 py-2 text-sm font-semibold uppercase text-(--text-secondary) bg-(--background-quaternary)">
                    Roster
                </h3>
                {orderedPositions.map((position) => {
                    return (
                        
                        <TeamRosterPositionTable
                            key={position}
                            position={position}
                            slots={groupedByPosition[position]}
                            className="p-3"
                        />
                    );
                })}
            </div>

            <div className={isModalOpen ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={handleCloseModal} isVisible={!!selectedCard}>
                    <CardDetail
                        showdownBotCardData={{ card: selectedCard } as ShowdownBotCardAPIResponse} 
                        hideTrendGraphs={true}
                        context="home"
                        parent='home'
                    />
                </Modal>
            </div>
        </div>
    );
}

