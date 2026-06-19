import type { Lineup, LineupSlot } from '../../api/userTeams';
import type { ShowdownBotCardCompact } from '../../api/showdownBotCard';
import { CardItemCompact } from '../cards/CardItemCompact';
import { FaPlus } from 'react-icons/fa6';

// Percentage-based [left, top] coordinates relative to the Field.png container
const POSITION_COORDS: Record<string, [number, number]> = {
    CF:  [50, 15],
    LF:  [20, 24],
    RF:  [80, 24],
    SS:  [32, 43],
    '2B': [68, 43],
    '3B': [18, 63],
    '1B': [82, 63],
    C:   [50, 85],
    DH:  [88, 15],
};

const FIELD_POSITIONS = ['CF', 'LF', 'RF', 'SS', '2B', '3B', '1B', 'C'] as const;

type FieldViewProps = {
    lineup: Lineup;
    cardMap: Record<string, ShowdownBotCardCompact | null>;
    onSlotClick: (position: string, currentSlot: LineupSlot | null) => void;
    readOnly?: boolean;
    activePosition?: string | null;
};

export function FieldView({ lineup, cardMap, onSlotClick, readOnly = false, activePosition }: FieldViewProps) {
    const slotByPosition = Object.fromEntries(
        lineup.slots.map(s => [s.field_position, s])
    );

    return (
        <div className="relative w-full" style={{ aspectRatio: '1 / 1' }}>
            <img
                src="/images/teams/Field.png"
                alt="Baseball field"
                className="w-full h-full select-none pointer-events-none"
                draggable={false}
            />

            {FIELD_POSITIONS.map(pos => {
                const [left, top] = POSITION_COORDS[pos];
                const slot = slotByPosition[pos] ?? null;
                const card = slot ? cardMap[slot.card_id] : null;
                const isActive = activePosition === pos;

                return (
                    <div
                        key={pos}
                        className={`absolute transition-all duration-200 ${isActive ? 'z-10' : ''}`}
                        style={{
                            left: `${left}%`,
                            top: `${top}%`,
                            transform: 'translate(-50%, -50%)',
                            width: '25%',
                            minWidth: 70,
                        }}
                    >
                        <div className={isActive
                            ? 'rounded-lg ring-2 ring-(--secondary) shadow-[0_0_14px_4px_color-mix(in_srgb,var(--secondary)_50%,transparent)] animate-pulse'
                            : ''
                        }>
                            {card ? (
                                <CardItemCompact
                                    card={card}
                                    size="lg"
                                    fieldPosition={pos}
                                    onClick={readOnly ? undefined : () => onSlotClick(pos, slot)}
                                    isSelected={isActive}
                                />
                            ) : (
                                <PositionSlotPlaceholder
                                    position={pos}
                                    isActive={isActive}
                                    onClick={readOnly ? undefined : () => onSlotClick(pos, null)}
                                />
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}


type PlaceholderProps = {
    position: string;
    onClick?: () => void;
    isActive?: boolean;
};

function PositionSlotPlaceholder({ position, onClick, isActive }: PlaceholderProps) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`
                w-full flex items-center justify-between gap-1
                rounded-lg px-2 py-1.5
                border-2 border-dashed
                backdrop-blur-[2px]
                ${isActive
                    ? 'border-(--secondary) bg-black/30'
                    : 'border-white/30 bg-black/20 hover:bg-black/30 hover:border-white/50'
                }
                ${onClick ? 'cursor-pointer' : 'cursor-default'}
                transition-colors
            `}
        >
            <span className={`text-[11px] font-black ${isActive ? 'text-(--secondary)' : 'text-white/70'}`}>{position}</span>
            {onClick && <FaPlus className={`text-[9px] shrink-0 ${isActive ? 'text-(--secondary)' : 'text-white/50'}`} />}
        </button>
    );
}
