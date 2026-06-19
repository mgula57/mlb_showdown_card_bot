import type { Lineup, LineupSlot, TeamRosterSlot, PitcherAssignment } from '../../api/userTeams';
import type { ShowdownBotCardCompact } from '../../api/showdownBotCard';
import { CardItemCompact } from '../cards/CardItemCompact';
import { FaPlus } from 'react-icons/fa6';
import { defenseAtPosition, OF_POSITIONS, IF_POSITIONS } from '../shared/DefenseUtils';

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
const ROTATION_ROLES = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5'] as const;
const BULLPEN_ROLES  = ['RP', 'CL'] as const;

export type FieldViewRosterData = {
    roster: TeamRosterSlot[];
    rotation: PitcherAssignment[];
    benchPtsMultiplier: number;
    minBench: number;
    minBullpen: number;
};

type FieldViewProps = {
    lineup: Lineup;
    cardMap: Record<string, ShowdownBotCardCompact | null>;
    onSlotClick: (position: string, currentSlot: LineupSlot | null) => void;
    onBenchClick?: (role: string, current: TeamRosterSlot | null) => void;
    onRoleClick?: (role: string, current: PitcherAssignment | null) => void;
    readOnly?: boolean;
    activePosition?: string | null;
    rosterData?: FieldViewRosterData;
};

function sumGroupDefense(positions: readonly string[], slotByPosition: Record<string, LineupSlot>, cardMap: Record<string, ShowdownBotCardCompact | null>): number | null {
    let total = 0;
    for (const pos of positions) {
        const slot = slotByPosition[pos];
        const card = slot ? cardMap[slot.card_id] : null;
        const val = defenseAtPosition(card?.positions_and_defense, pos) || 0;
        total += val;
    }
    return total;
}

export function FieldView({ lineup, cardMap, onSlotClick, onBenchClick, onRoleClick, readOnly = false, activePosition, rosterData }: FieldViewProps) {
    const slotByPosition = Object.fromEntries(
        lineup.slots.map(s => [s.field_position, s])
    );

    const totalOF = sumGroupDefense(OF_POSITIONS, slotByPosition, cardMap);
    const totalIF = sumGroupDefense(IF_POSITIONS, slotByPosition, cardMap);

    const pts = (cardId: string) => cardMap[cardId]?.points ?? 0;

    // Build role-indexed maps so each slot renders in order (filled or placeholder)
    const benchRoles    = rosterData ? Array.from({ length: rosterData.minBench },   (_, i) => `BE${i + 1}`) : [];
    const bullpenRoles  = rosterData ? (BULLPEN_ROLES as readonly string[]).slice(0, rosterData.minBullpen) : [];
    const benchByRole   = Object.fromEntries((rosterData?.roster ?? []).filter(s => /^BE\d+$/.test(s.roster_position.toUpperCase())).map(s => [s.roster_position.toUpperCase(), s]));
    const rotByRole     = Object.fromEntries((rosterData?.rotation ?? []).filter(r => (ROTATION_ROLES as readonly string[]).includes(r.role)).map(r => [r.role, r]));
    const bullByRole    = Object.fromEntries((rosterData?.rotation ?? []).filter(r => (BULLPEN_ROLES as readonly string[]).includes(r.role)).map(r => [r.role, r]));

    const benchPts    = benchRoles.reduce((sum, role) => { const s = benchByRole[role]; return s ? sum + Math.round(pts(s.card_id) * (rosterData?.benchPtsMultiplier ?? 1)) : sum; }, 0);
    const rotationPts = (ROTATION_ROLES as readonly string[]).reduce((sum, role) => { const r = rotByRole[role]; return r ? sum + pts(r.card_id) : sum; }, 0);
    const bullpenPts  = bullpenRoles.reduce((sum, role) => { const r = bullByRole[role]; return r ? sum + pts(r.card_id) : sum; }, 0);

    const sections = rosterData ? [
        {
            label: 'Bench', total: benchPts,
            roles: benchRoles,
            getCard:    (role: string) => { const s = benchByRole[role]; return s ? cardMap[s.card_id] : null; },
            onItemClick: onBenchClick && !readOnly ? (role: string) => onBenchClick(role, benchByRole[role] ?? null) : undefined,
        },
        {
            label: 'Rotation', total: rotationPts,
            roles: [...ROTATION_ROLES] as string[],
            getCard:    (role: string) => { const r = rotByRole[role]; return r ? cardMap[r.card_id] : null; },
            onItemClick: onRoleClick && !readOnly ? (role: string) => onRoleClick(role, rotByRole[role] ?? null) : undefined,
        },
        {
            label: 'Bullpen', total: bullpenPts,
            roles: bullpenRoles,
            getCard:    (role: string) => { const r = bullByRole[role]; return r ? cardMap[r.card_id] : null; },
            onItemClick: onRoleClick && !readOnly ? (role: string) => onRoleClick(role, bullByRole[role] ?? null) : undefined,
        },
    ] : [];

    return (
        <div className="flex flex-col">
            <div className="relative w-full" style={{ aspectRatio: '1 / 1' }}>
                <img
                    src="/images/teams/Field.png"
                    alt="Baseball field"
                    className="w-full h-full select-none pointer-events-none"
                    draggable={false}
                />

                {([
                    { label: 'OF', value: totalOF, top: 25 },
                    { label: 'IF', value: totalIF, top: 53 },
                ] as const).map(({ label, value, top }) => value !== null && (
                    <div
                        key={label}
                        className="absolute left-1/2 -translate-x-1/2 flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-black/50 backdrop-blur-sm pointer-events-none select-none"
                        style={{ top: `${top}%` }}
                    >
                        <span className="text-[10px] font-semibold text-white/60 uppercase tracking-wide">{label}</span>
                        <span className={`text-xs font-black ${value > 0 ? 'text-green-400' : value < 0 ? 'text-red-400' : 'text-white/80'}`}>
                            {value > 0 ? `+${value}` : value}
                        </span>
                    </div>
                ))}

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
                            onClick={e => e.stopPropagation()}
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

            {sections.map(({ label, roles, total, getCard, onItemClick }) => {
                const filledCount = roles.filter(r => getCard(r)).length;
                return (
                    <div key={label} className="border-t border-(--divider)" onClick={onItemClick ? e => e.stopPropagation() : undefined}>
                        <div className="flex items-center gap-1.5 px-3 py-1.5">
                            <span className="text-[11px] font-bold text-(--text-secondary) uppercase tracking-wide">{label}</span>
                            <span className="text-[10px] text-(--text-tertiary)">{filledCount}</span>
                            {total > 0 && (
                                <span className="ml-auto text-[11px] font-semibold text-(--text-tertiary)">{total} pts</span>
                            )}
                        </div>
                        <div className="grid grid-cols-2 gap-1.5 px-3 pb-3">
                            {roles.map(role => {
                                const card = getCard(role);
                                return card ? (
                                    <CardItemCompact
                                        key={role}
                                        card={card}
                                        size="lg"
                                        onClick={onItemClick ? () => onItemClick(role) : undefined}
                                    />
                                ) : (
                                    <button
                                        key={role}
                                        type="button"
                                        onClick={onItemClick ? () => onItemClick(role) : undefined}
                                        disabled={!onItemClick}
                                        className="flex items-center justify-center gap-1.5 h-9 rounded-lg border border-dashed
                                            text-[11px] transition-colors disabled:pointer-events-none disabled:opacity-40
                                            border-(--divider) text-(--text-tertiary) hover:border-(--secondary)/50 hover:text-(--secondary)"
                                    >
                                        <FaPlus className="text-[9px]" />
                                        <span>Empty</span>
                                    </button>
                                );
                            })}
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
                rounded-lg px-2 h-12
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
