import { useState } from 'react';
import type { Lineup, LineupSlot } from '../../api/userTeams';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { FaPlus, FaTrash, FaPencil, FaCheck } from 'react-icons/fa6';

type LineupPanelProps = {
    lineups: Lineup[];
    cardMap: Record<string, CardDatabaseRecord | null>;
    onLineupsChange: (lineups: Lineup[]) => void;
    onSlotClick: (lineupIndex: number, position: string, currentSlot: LineupSlot | null) => void;
    readOnly?: boolean;
};

const BATTING_ORDER_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'SP', 'DH'] as const;

export function LineupPanel({ lineups, cardMap, onLineupsChange, onSlotClick, readOnly = false }: LineupPanelProps) {
    const [activeIndex, setActiveIndex] = useState(0);
    const [editingName, setEditingName] = useState<number | null>(null);
    const [draftName, setDraftName] = useState('');

    const activeLineup = lineups[activeIndex] ?? null;

    function addLineup() {
        const newLineup: Lineup = { name: `Lineup ${lineups.length + 1}`, slots: [] };
        onLineupsChange([...lineups, newLineup]);
        setActiveIndex(lineups.length);
    }

    function removeLineup(index: number) {
        const updated = lineups.filter((_, i) => i !== index);
        onLineupsChange(updated);
        setActiveIndex(Math.min(activeIndex, updated.length - 1));
    }

    function startRename(index: number) {
        setEditingName(index);
        setDraftName(lineups[index].name);
    }

    function commitRename(index: number) {
        if (!draftName.trim()) return;
        const updated = lineups.map((ln, i) => i === index ? { ...ln, name: draftName.trim() } : ln);
        onLineupsChange(updated);
        setEditingName(null);
    }

    if (lineups.length === 0) {
        return (
            <div className="flex flex-col items-center gap-3 py-10 text-(--text-tertiary)">
                <p className="text-[13px]">No lineups yet.</p>
                {!readOnly && (
                    <button
                        type="button"
                        onClick={addLineup}
                        className="flex items-center gap-1.5 text-[12px] font-semibold text-(--secondary) hover:opacity-80"
                    >
                        <FaPlus className="text-[10px]" /> Add Lineup
                    </button>
                )}
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-4">
            {/* Lineup tabs */}
            <div className="flex items-center gap-2 flex-wrap">
                {lineups.map((ln, i) => (
                    <div key={i} className="flex items-center gap-1">
                        {editingName === i ? (
                            <div className="flex items-center gap-1">
                                <input
                                    autoFocus
                                    value={draftName}
                                    onChange={e => setDraftName(e.target.value)}
                                    onKeyDown={e => { if (e.key === 'Enter') commitRename(i); }}
                                    className="text-[12px] bg-(--background-secondary) border border-(--divider) rounded px-1.5 py-0.5 w-28"
                                />
                                <button type="button" onClick={() => commitRename(i)}>
                                    <FaCheck className="text-[10px] text-(--secondary)" />
                                </button>
                            </div>
                        ) : (
                            <button
                                type="button"
                                onClick={() => setActiveIndex(i)}
                                className={`text-[12px] font-semibold px-2 py-1 rounded border transition-colors
                                    ${i === activeIndex
                                        ? 'border-(--secondary) text-(--secondary)'
                                        : 'border-(--divider) text-(--text-secondary) hover:border-(--secondary)/50'
                                    }`}
                            >
                                {ln.name}
                            </button>
                        )}
                        {!readOnly && i === activeIndex && editingName !== i && (
                            <button type="button" onClick={() => startRename(i)} className="text-(--text-tertiary) hover:text-(--text-secondary)">
                                <FaPencil className="text-[9px]" />
                            </button>
                        )}
                        {!readOnly && lineups.length > 1 && i === activeIndex && (
                            <button type="button" onClick={() => removeLineup(i)} className="text-(--text-tertiary) hover:text-red-400">
                                <FaTrash className="text-[9px]" />
                            </button>
                        )}
                    </div>
                ))}
                {!readOnly && (
                    <button
                        type="button"
                        onClick={addLineup}
                        className="flex items-center gap-1 text-[11px] text-(--text-tertiary) hover:text-(--secondary) transition-colors px-1"
                    >
                        <FaPlus className="text-[9px]" /> Add
                    </button>
                )}
            </div>

            {/* Active lineup slots */}
            {activeLineup && (
                <div className="flex flex-col gap-1">
                    {BATTING_ORDER_POSITIONS.map(pos => {
                        const slot = activeLineup.slots.find(s => s.field_position === pos) ?? null;
                        const card = slot ? cardMap[slot.card_id] : null;
                        const order = slot?.batting_order;

                        return (
                            <div key={pos} className="flex items-center gap-2">
                                <div className="w-6 text-center text-[11px] font-black text-(--text-tertiary)">
                                    {order ?? pos}
                                </div>
                                {card ? (
                                    <CardItemCompactFromCardDatabaseRecord
                                        card={card}
                                        className="flex-1"
                                        onClick={readOnly ? undefined : () => onSlotClick(activeIndex, pos, slot)}
                                    />
                                ) : (
                                    <button
                                        type="button"
                                        onClick={readOnly ? undefined : () => onSlotClick(activeIndex, pos, null)}
                                        className={`
                                            flex-1 flex items-center gap-1.5 px-2 py-1.5
                                            rounded-lg border-2 border-dashed border-(--divider)
                                            text-[11px] text-(--text-tertiary)
                                            ${!readOnly ? 'hover:border-(--secondary)/50 hover:text-(--secondary) cursor-pointer' : 'cursor-default'}
                                        `}
                                    >
                                        <FaPlus className="text-[9px]" /> {pos}
                                    </button>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
