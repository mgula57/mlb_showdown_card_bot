/**
 * @fileoverview TeamRoster - Depth chart display grouped by roster position
 */

import { useEffect, useState } from "react";
import { type Roster, type RosterSlot } from "../../api/mlbAPI";
import { CardItemFromCard } from "../cards/CardItem";
import TeamRosterPositionTable from "./TeamRosterPositionTable";

interface TeamRosterProps {
    roster: Roster | null;
}

const getTopPlayerLimit = (width: number): number => {
    if (width < 640) {
        return 3;
    }
    if (width < 1024) {
        return 4;
    }
    return 6;
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
            return 6;
        }
        return getTopPlayerLimit(window.innerWidth);
    });

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

    const orderedPositions = Object.keys(groupedByPosition).sort((a, b) => a.localeCompare(b));
    const topPlayers = [...rosterSlots]
        .filter((slot) => slot.person.showdown_card_data)
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
        </div>
    );
}

