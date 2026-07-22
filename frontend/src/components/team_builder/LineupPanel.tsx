import { useState, useRef } from 'react';
import type { Lineup } from '../../api/userTeams';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { FaPlus, FaTrash, FaPencil, FaCheck, FaChevronUp, FaChevronDown, FaCopy } from 'react-icons/fa6';

const DEFAULT_LINEUP_NAME = 'Default';

type LineupPanelProps = {
    lineups: Lineup[];
    cardMap: Record<string, CardDatabaseRecord | null>;
    /** Called when the user modifies user-created lineups. Only non-Default lineups are included. */
    onLineupsChange: (lineups: Lineup[]) => void;
    readOnly?: boolean;
};

export function LineupPanel({ lineups, cardMap, onLineupsChange, readOnly = false }: LineupPanelProps) {
    const [activeIndex, setActiveIndex] = useState(0);
    const [editingTabIndex, setEditingTabIndex] = useState<number | null>(null);
    const [draftName, setDraftName] = useState('');
    const [dragIndex, setDragIndex] = useState<number | null>(null);
    const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
    const dragId = useRef<string | null>(null);

    const defaultLineup = lineups.find(ln => ln.name === DEFAULT_LINEUP_NAME) ?? null;
    const userLineups = lineups.filter(ln => ln.name !== DEFAULT_LINEUP_NAME);
    // All tabs: Default first (always), then user-created
    const allTabs: Lineup[] = [...(defaultLineup ? [defaultLineup] : []), ...userLineups];
    const activeLineup = allTabs[activeIndex] ?? null;
    const isDefault = activeLineup?.name === DEFAULT_LINEUP_NAME;

    function emitChange(updated: Lineup[]) {
        onLineupsChange(updated.filter(ln => ln.name !== DEFAULT_LINEUP_NAME));
    }

    function addLineup() {
        const newLineup: Lineup = {
            name: `Lineup ${userLineups.length + 1}`,
            index: userLineups.length + 1,
            slots: activeLineup?.slots ? [...activeLineup.slots] : [],
        };
        const next = [...userLineups, newLineup];
        emitChange([...(defaultLineup ? [defaultLineup] : []), ...next]);
        setActiveIndex(allTabs.length); // point to new tab
    }

    function copyDefault() {
        if (!defaultLineup) return;
        const newLineup: Lineup = {
            name: `Lineup ${userLineups.length + 1}`,
            index: userLineups.length + 1,
            slots: defaultLineup.slots.map(s => ({ ...s })),
        };
        const next = [...userLineups, newLineup];
        emitChange([...(defaultLineup ? [defaultLineup] : []), ...next]);
        setActiveIndex(allTabs.length);
    }

    function removeLineup(tabIndex: number) {
        const lineup = allTabs[tabIndex];
        if (!lineup || lineup.name === DEFAULT_LINEUP_NAME) return;
        const next = userLineups.filter(ln => ln !== lineup);
        emitChange([...(defaultLineup ? [defaultLineup] : []), ...next]);
        setActiveIndex(Math.min(activeIndex, allTabs.length - 2));
    }

    function startRename(tabIndex: number) {
        setEditingTabIndex(tabIndex);
        setDraftName(allTabs[tabIndex]?.name ?? '');
    }

    function commitRename(tabIndex: number) {
        const name = draftName.trim();
        if (!name || name === DEFAULT_LINEUP_NAME) { setEditingTabIndex(null); return; }
        const lineup = allTabs[tabIndex];
        if (!lineup) return;
        const next = userLineups.map(ln => ln === lineup ? { ...ln, name } : ln);
        emitChange([...(defaultLineup ? [defaultLineup] : []), ...next]);
        setEditingTabIndex(null);
    }

    // -------------------------------------------------------------------------
    // Batting order mutations — only for user-created lineups
    // -------------------------------------------------------------------------

    function moveSlot(fromOrder: number, toOrder: number) {
        if (isDefault || !activeLineup) return;
        const sorted = [...activeLineup.slots].sort((a, b) => a.batting_order - b.batting_order);
        const fromIdx = sorted.findIndex(s => s.batting_order === fromOrder);
        const toIdx   = sorted.findIndex(s => s.batting_order === toOrder);
        if (fromIdx === -1 || toIdx === -1 || fromIdx === toIdx) return;
        const reordered = [...sorted];
        const [moved] = reordered.splice(fromIdx, 1);
        reordered.splice(toIdx, 0, moved);
        const renumbered = reordered.map((s, i) => ({ ...s, batting_order: i + 1 }));
        const next = userLineups.map(ln =>
            ln === activeLineup ? { ...ln, slots: renumbered } : ln
        );
        emitChange([...(defaultLineup ? [defaultLineup] : []), ...next]);
    }

    // -------------------------------------------------------------------------
    // Drag-and-drop (native HTML5)
    // -------------------------------------------------------------------------

    function handleDragStart(order: number, cardId: string) {
        setDragIndex(order);
        dragId.current = cardId;
    }

    function handleDragOver(e: React.DragEvent, order: number) {
        e.preventDefault();
        if (order !== dragIndex) setDragOverIndex(order);
    }

    function handleDrop(toOrder: number) {
        if (dragIndex !== null && dragIndex !== toOrder) moveSlot(dragIndex, toOrder);
        setDragIndex(null);
        setDragOverIndex(null);
        dragId.current = null;
    }

    // -------------------------------------------------------------------------
    // Render
    // -------------------------------------------------------------------------

    const sortedSlots = activeLineup
        ? [...activeLineup.slots].sort((a, b) => a.batting_order - b.batting_order)
        : [];

    return (
        <div className="flex flex-col gap-4 px-4 py-2">
            {/* Tab strip */}
            <div className="flex items-center gap-2 flex-wrap">
                {allTabs.map((ln, i) => (
                    <div key={`${ln.name}-${i}`} className="flex items-center gap-1">
                        {editingTabIndex === i ? (
                            <div className="flex items-center gap-1">
                                <input
                                    autoFocus
                                    value={draftName}
                                    onChange={e => setDraftName(e.target.value)}
                                    onKeyDown={e => { if (e.key === 'Enter') commitRename(i); if (e.key === 'Escape') setEditingTabIndex(null); }}
                                    className="text-[12px] bg-(--background-secondary) border border-(--divider) rounded px-1.5 py-0.5 w-28"
                                />
                                <button type="button" onClick={() => commitRename(i)} className="cursor-pointer">
                                    <FaCheck className="text-[10px] text-(--secondary)" />
                                </button>
                            </div>
                        ) : (
                            <button
                                type="button"
                                onClick={() => setActiveIndex(i)}
                                className={`text-[12px] font-semibold px-2 py-1 rounded border transition-colors cursor-pointer
                                    ${i === activeIndex
                                        ? 'border-(--secondary) text-(--secondary)'
                                        : 'border-(--divider) text-(--text-secondary) hover:border-(--secondary)/50'
                                    }`}
                            >
                                {ln.name}
                            </button>
                        )}
                        {/* Rename / delete — user-created tabs only, edit mode */}
                        {!readOnly && ln.name !== DEFAULT_LINEUP_NAME && i === activeIndex && editingTabIndex !== i && (
                            <>
                                <button type="button" onClick={() => startRename(i)} className="text-(--text-tertiary) hover:text-(--text-secondary) cursor-pointer">
                                    <FaPencil className="text-[9px]" />
                                </button>
                                {userLineups.length > 0 && (
                                    <button type="button" onClick={() => removeLineup(i)} className="text-(--text-tertiary) hover:text-red-400 cursor-pointer">
                                        <FaTrash className="text-[9px]" />
                                    </button>
                                )}
                            </>
                        )}
                    </div>
                ))}

                {!readOnly && (
                    <button
                        type="button"
                        onClick={addLineup}
                        className="flex items-center gap-1 text-[11px] text-(--text-tertiary) hover:text-(--secondary) transition-colors px-1 cursor-pointer"
                        title="Add new lineup"
                    >
                        <FaPlus className="text-[9px]" /> Add
                    </button>
                )}
            </div>

            {/* Default read-only notice + copy CTA */}
            {isDefault && !readOnly && (
                <div className="flex items-center justify-between px-1">
                    <p className="text-[11px] text-(--text-tertiary)">
                        Auto-calculated · updates when roster changes
                    </p>
                    <button
                        type="button"
                        onClick={copyDefault}
                        className="flex items-center gap-1 text-[11px] font-semibold text-(--secondary) hover:opacity-80 cursor-pointer"
                    >
                        <FaCopy className="text-[9px]" /> Copy as new lineup
                    </button>
                </div>
            )}

            {/* Slots */}
            {sortedSlots.length === 0 ? (
                <p className="text-[13px] text-(--text-tertiary) py-4 text-center">
                    {isDefault ? 'Draft at least 9 lineup spots to see the batting order.' : 'No slots yet.'}
                </p>
            ) : (
                <div className="flex flex-col gap-1">
                    {sortedSlots.map((slot, idx) => {
                        const card = cardMap[slot.card_id] ?? null;
                        const isBeingDragged = dragIndex === slot.batting_order;
                        const isDropTarget = dragOverIndex === slot.batting_order;
                        const canReorder = !isDefault && !readOnly;

                        return (
                            <div
                                key={slot.card_id}
                                draggable={canReorder}
                                onDragStart={canReorder ? () => handleDragStart(slot.batting_order, slot.card_id) : undefined}
                                onDragOver={canReorder ? e => handleDragOver(e, slot.batting_order) : undefined}
                                onDrop={canReorder ? () => handleDrop(slot.batting_order) : undefined}
                                onDragEnd={() => { setDragIndex(null); setDragOverIndex(null); }}
                                className={`flex items-center gap-2 rounded-lg transition-all
                                    ${isBeingDragged ? 'opacity-40' : ''}
                                    ${isDropTarget ? 'ring-1 ring-(--secondary)' : ''}
                                `}
                            >
                                {/* Batting order number */}
                                <div className="w-5 text-center text-[11px] font-black text-(--text-tertiary) shrink-0">
                                    {slot.batting_order}
                                </div>

                                {/* Position badge */}
                                <div className="text-[10px] font-bold text-(--text-tertiary) w-7 shrink-0 text-center">
                                    {slot.field_position}
                                </div>

                                {/* Card */}
                                <div className="flex-1 min-w-0">
                                    {card ? (
                                        <CardItemCompactFromCardDatabaseRecord card={card} />
                                    ) : (
                                        <div className="text-[11px] text-(--text-tertiary) px-2">—</div>
                                    )}
                                </div>

                                {/* Up/down reorder (keyboard-friendly alternative to drag) */}
                                {canReorder && (
                                    <div className="flex flex-col shrink-0">
                                        <button
                                            type="button"
                                            disabled={idx === 0}
                                            onClick={() => moveSlot(slot.batting_order, sortedSlots[idx - 1].batting_order)}
                                            className="text-(--text-tertiary) hover:text-(--text-secondary) disabled:opacity-30 cursor-pointer"
                                        >
                                            <FaChevronUp className="text-[8px]" />
                                        </button>
                                        <button
                                            type="button"
                                            disabled={idx === sortedSlots.length - 1}
                                            onClick={() => moveSlot(slot.batting_order, sortedSlots[idx + 1].batting_order)}
                                            className="text-(--text-tertiary) hover:text-(--text-secondary) disabled:opacity-30 cursor-pointer"
                                        >
                                            <FaChevronDown className="text-[8px]" />
                                        </button>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
