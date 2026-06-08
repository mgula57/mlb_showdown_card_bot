/**
 * @fileoverview TeamSlot - Individual position slot in a team (empty or card-filled)
 */

import { FaPlus, FaTimes } from 'react-icons/fa';
import { CardItem } from '../cards/CardItem';
import type { TeamBuilderSlot } from '../../api/teamBuilder';

interface TeamSlotProps {
    slotKey: string;
    slot: TeamBuilderSlot | undefined;
    onClick: () => void;
    onRemove?: () => void;
    className?: string;
    size?: 'sm' | 'md';
}

const SLOT_LABELS: Record<string, string> = {
    CA: 'C', '1B': '1B', '2B': '2B', '3B': '3B', SS: 'SS',
    LF: 'LF', CF: 'CF', RF: 'RF', DH: 'DH',
};

function getSlotLabel(slotKey: string): string {
    if (SLOT_LABELS[slotKey]) return SLOT_LABELS[slotKey];
    if (slotKey.startsWith('SP')) return `SP${slotKey.slice(2)}`;
    if (slotKey.startsWith('RP')) return `RP${slotKey.slice(2)}`;
    if (slotKey.startsWith('BE')) return `BE${slotKey.slice(2)}`;
    return slotKey;
}

export default function TeamSlot({ slotKey, slot, onClick, onRemove, className = '', size = 'md' }: TeamSlotProps) {
    const snap = slot?.card_snapshot;
    const label = getSlotLabel(slotKey);
    const minW = size === 'sm' ? 'min-w-[120px]' : 'min-w-[150px]';

    if (!snap) {
        return (
            <button
                type="button"
                onClick={onClick}
                className={`
                    flex flex-col items-center justify-center gap-1 rounded-xl
                    border-2 border-dashed border-(--divider) bg-(--background-secondary)
                    hover:border-(--showdown-blue) hover:bg-(--background-tertiary) transition-colors
                    cursor-pointer py-4 px-2 ${minW} min-h-[80px] ${className}
                `}
            >
                <span className="text-xs font-bold text-(--text-secondary) uppercase tracking-wide">{label}</span>
                <FaPlus className="text-(--text-tertiary) w-3 h-3" />
            </button>
        );
    }

    const primaryColor = (['NYM', 'SDP'].includes(snap.team || '') ? snap.color_secondary : snap.color_primary) || 'rgb(0,0,0)';
    const secondaryColor = (['NYM', 'SDP'].includes(snap.team || '') ? snap.color_primary : snap.color_secondary) || 'rgb(0,0,0)';

    return (
        <div className={`relative ${className}`}>
            <CardItem
                cardName={snap.name}
                cardYear={String(snap.year)}
                cardTeam={snap.team}
                cardSet={snap.showdown_set}
                cardPoints={snap.points}
                cardCommand={snap.command}
                cardOuts={snap.outs}
                cardIsPitcher={snap.is_pitcher}
                cardSpeed={snap.speed ?? undefined}
                cardIp={snap.ip ?? undefined}
                cardPositionsAndDefenseString={snap.positions_and_defense_string ?? undefined}
                cardPrimaryColor={primaryColor}
                cardSecondaryColor={secondaryColor}
                onClick={onClick}
                className={`${minW}`}
            />
            <span className="absolute bottom-1 left-1 rounded px-1 py-0.5 text-[9px] font-bold bg-black/60 text-white uppercase leading-none">
                {label}
            </span>
            {onRemove && (
                <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); onRemove(); }}
                    className="absolute top-1 right-1 rounded-full bg-black/60 hover:bg-red-700 p-0.5 cursor-pointer"
                    aria-label={`Remove ${label}`}
                >
                    <FaTimes className="text-white w-2.5 h-2.5" />
                </button>
            )}
        </div>
    );
}
