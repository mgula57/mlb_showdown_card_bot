/**
 * @fileoverview TeamFieldView - Baseball diamond layout for 9 position player slots
 *
 * Uses a 5-column × 4-row CSS grid to place each position at its natural
 * location on the diamond.
 *
 *   col:  1    2    3    4    5
 * row 1: [ ]  [ ]  CF   [ ]  [ ]
 * row 2: [ ]  LF   [ ]  RF   [ ]
 * row 3: 3B   [ ]  SS   2B   1B
 * row 4: [ ]  [ ]  CA   [ ]  DH
 */

import TeamSlot from './TeamSlot';
import type { TeamBuilderSlot } from '../../api/teamBuilder';

interface TeamFieldViewProps {
    slotMap: Record<string, TeamBuilderSlot>;
    onSlotClick: (slotKey: string) => void;
    onSlotRemove: (slotKey: string) => void;
}

interface PositionCell {
    slotKey: string;
    col: number;
    row: number;
}

const FIELD_POSITIONS: PositionCell[] = [
    { slotKey: 'CF', col: 3, row: 1 },
    { slotKey: 'LF', col: 2, row: 2 },
    { slotKey: 'RF', col: 4, row: 2 },
    { slotKey: '3B', col: 1, row: 3 },
    { slotKey: 'SS', col: 3, row: 3 },
    { slotKey: '2B', col: 4, row: 3 },
    { slotKey: '1B', col: 5, row: 3 },
    { slotKey: 'CA', col: 3, row: 4 },
    { slotKey: 'DH', col: 5, row: 4 },
];

export default function TeamFieldView({ slotMap, onSlotClick, onSlotRemove }: TeamFieldViewProps) {
    return (
        <div className="relative w-full overflow-x-auto pb-2">
            {/* Diamond background hint */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none" aria-hidden>
                <div
                    className="w-48 h-48 border-2 border-(--divider)/40 rotate-45 rounded-sm"
                    style={{ marginTop: '1.5rem' }}
                />
            </div>

            <div className="grid grid-cols-5 grid-rows-4 gap-3 p-4 relative">
                {FIELD_POSITIONS.map(({ slotKey, col, row }) => (
                    <div
                        key={slotKey}
                        style={{ gridColumn: col, gridRow: row }}
                        className="flex items-center justify-center"
                    >
                        <TeamSlot
                            slotKey={slotKey}
                            slot={slotMap[slotKey]}
                            onClick={() => onSlotClick(slotKey)}
                            onRemove={slotMap[slotKey] ? () => onSlotRemove(slotKey) : undefined}
                            size="sm"
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}
