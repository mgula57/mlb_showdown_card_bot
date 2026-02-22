/**
 * @fileoverview TeamRoster - Depth chart display grouped by roster position
 */

import { type Roster, type RosterSlot } from "../../api/mlbAPI";
import TeamRosterPositionTable from "./TeamRosterPositionTable";

interface TeamRosterProps {
    roster: Roster | null;
}

const getPositionLabel = (slot: RosterSlot): string => {
    if (typeof slot.position === "string") {
        return slot.position;
    }
    return slot.position.abbreviation || slot.position.code || slot.position.name || slot.position.description || "Unknown";
};

export default function TeamRoster({ roster }: TeamRosterProps) {
    const rosterSlots = roster?.roster ?? [];

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

    return (
        <div className="mt-6 space-y-4">
            {orderedPositions.map((position) => {
                return (
                    <TeamRosterPositionTable
                        key={position}
                        position={position}
                        slots={groupedByPosition[position]}
                    />
                );
            })}
        </div>
    );
}

