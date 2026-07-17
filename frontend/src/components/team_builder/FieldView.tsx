import { useState } from 'react';
import type { Lineup, LineupSlot, TeamRosterSlot, PitcherAssignment } from '../../api/userTeams';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { FaPlus, FaPencil } from 'react-icons/fa6';
import { defenseAtPosition, OF_POSITIONS, IF_POSITIONS } from '../shared/DefenseUtils';
import { type KpiTile, buildLineupKpis, buildBenchKpis, buildPitcherKpis } from './TeamKpiUtils';
import { Modal } from '../shared/Modal';
import { CardDetail } from '../cards/CardDetail';

// Percentage-based [left, top] coordinates relative to the Field.png container
const POSITION_COORDS: Record<string, [number, number]> = {
    CF:  [50, 18],
    LF:  [20, 24],
    RF:  [80, 24],
    SS:  [32, 43],
    '2B': [68, 43],
    '3B': [18, 63],
    '1B': [82, 63],
    C:   [50, 85],
    DH:  [84, 85],
};

const FIELD_POSITIONS = ['CF', 'LF', 'RF', 'SS', '2B', '3B', '1B', 'C', 'DH'] as const;
const ROTATION_ROLES = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5'] as const;

export type FieldViewRosterData = {
    roster: TeamRosterSlot[];
    rotation: PitcherAssignment[];
    benchPtsMultiplier: number;
    minBench: number;
    minBullpen: number;
    maxRotation: number;
};

type FieldViewProps = {
    lineup: Lineup;
    cardMap: Record<string, CardDatabaseRecord | null>;
    onSlotClick: (position: string, currentSlot: LineupSlot | null) => void;
    onBenchClick?: (role: string, current: TeamRosterSlot | null) => void;
    onRoleClick?: (role: string, current: PitcherAssignment | null) => void;
    readOnly?: boolean;
    activePosition?: string | null;
    rosterData?: FieldViewRosterData;
    hoveredCardId?: string | null;
    onCardHover?: (cardId: string | null) => void;
    /** True while cardMap entries are still being fetched — shows loading placeholders for filled-but-unresolved slots */
    isLoadingCards?: boolean;
};


// ---- Section header ----

function FieldViewSectionHeader({ label, filledCount, maxPlayers, total, kpis }: {
    label: string;
    filledCount: number;
    maxPlayers?: number;
    total: number;
    kpis?: KpiTile[];
}) {
    return (
        <div className="px-3 py-1.5 backdrop-blur-xs bg-(--background)/40">
            <div className="flex items-center gap-1.5 opacity-75">
                <span className="text-[11px] font-bold text-(--text-secondary) uppercase tracking-wide">{label}</span>
                <span className="text-[10px] text-(--text-tertiary)">{filledCount}{maxPlayers !== undefined ? `/${maxPlayers}` : ''}</span>
                {total > 0 && (
                    <span className="ml-auto text-[11px] font-semibold text-(--text-tertiary)">{total} pts</span>
                )}
            </div>
            {kpis && kpis.length > 0 && (
                <div className="flex items-center gap-3 mt-1.5 overflow-x-auto pb-0.5">
                    {kpis.map(({ label: kLabel, value }) => (
                        <div key={kLabel} className="flex flex-col items-center shrink-0">
                            <span className="text-[8px] text-(--text-tertiary) uppercase tracking-wider opacity-75">{kLabel}</span>
                            <span className="text-[11px] font-bold text-(--text-secondary)">{value}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function sumGroupDefense(positions: readonly string[], slotByPosition: Record<string, LineupSlot>, cardMap: Record<string, CardDatabaseRecord | null>): number | null {
    let total = 0;
    for (const pos of positions) {
        const slot = slotByPosition[pos];
        const card = slot ? cardMap[slot.card_id] : null;
        const val = defenseAtPosition(card?.positions_and_defense, pos) || 0;
        total += val;
    }
    return total;
}

export function FieldView({ lineup, cardMap, onSlotClick, onBenchClick, onRoleClick, readOnly = false, activePosition, rosterData, hoveredCardId, onCardHover, isLoadingCards }: FieldViewProps) {
    const [detailCard, setDetailCard] = useState<CardDatabaseRecord | null>(null);

    const slotByPosition = Object.fromEntries(
        lineup.slots.map(s => [s.field_position, s])
    );

    // Outfield Defense
    const totalDefOF = sumGroupDefense(OF_POSITIONS, slotByPosition, cardMap);
    const totalCountOfFilledOF = OF_POSITIONS.filter(pos => slotByPosition[pos]).length;
    const avgDefOF = totalCountOfFilledOF > 0 ? (totalDefOF! / totalCountOfFilledOF) : null;
    const colorDefOF = avgDefOF !== null ? (avgDefOF > 1.75 ? 'text-(--green)' : avgDefOF > 1 ? 'text-(--warning)' : 'text-(--red)') : 'text-primary';

    // Infield Defense
    const totalDefIF = sumGroupDefense(IF_POSITIONS, slotByPosition, cardMap);
    const totalCountOfFilledIF = IF_POSITIONS.filter(pos => slotByPosition[pos]).length;
    const avgDefIF = totalCountOfFilledIF > 0 ? (totalDefIF! / totalCountOfFilledIF) : null;
    const colorDefIF = avgDefIF !== null ? (avgDefIF >= 2.5 ? 'text-(--green)' : avgDefIF >= 1.75 ? 'text-(--warning)' : 'text-(--red)') : 'text-primary';

    // Catcher Arm
    const cSlot = slotByPosition['C'];
    const cCard = cSlot ? cardMap[cSlot.card_id] : null;
    const armC = defenseAtPosition(cCard?.positions_and_defense, 'C');
    const colorArmC = armC ? (armC > 7 ? 'text-(--green)' : armC > 3 ? 'text-(--warning)' : 'text-(--red)') : 'text-primary';

    const pts = (cardId: string) => cardMap[cardId]?.points ?? 0;

    // Build role-indexed maps so each slot renders in order (filled or placeholder)
    const benchRoles    = rosterData ? Array.from({ length: rosterData.minBench },   (_, i) => `BE${i + 1}`) : [];
    const bullpenRoles  = rosterData ? Array.from({ length: rosterData.minBullpen }, (_, i) => `RP${i + 1}`) : [];
    const benchSlots    = (rosterData?.roster ?? []).filter(s => s.roster_position.toUpperCase() === 'BE');
    const benchByRole   = Object.fromEntries(benchRoles.flatMap((role, i) => benchSlots[i] ? [[role, benchSlots[i]]] : []));
    const rotByRole     = Object.fromEntries((rosterData?.rotation ?? []).filter(r => (ROTATION_ROLES as readonly string[]).includes(r.role)).map(r => [r.role, r]));
    const bullpenSlots  = (rosterData?.rotation ?? []).filter(r => !(ROTATION_ROLES as readonly string[]).includes(r.role));
    const bullByRole    = Object.fromEntries(bullpenRoles.flatMap((role, i) => bullpenSlots[i] ? [[role, bullpenSlots[i]]] : []));

    const lineupPts = lineup.slots.reduce((sum, slot) => sum + (cardMap[slot.card_id]?.points ?? 0), 0);
    const benchPts    = benchRoles.reduce((sum, role) => { const s = benchByRole[role]; return s ? sum + Math.round(pts(s.card_id) * (rosterData?.benchPtsMultiplier ?? 1)) : sum; }, 0);
    const rotationPts = (ROTATION_ROLES as readonly string[]).reduce((sum, role) => { const r = rotByRole[role]; return r ? sum + pts(r.card_id) : sum; }, 0);
    const bullpenPts  = bullpenRoles.reduce((sum, role) => { const r = bullByRole[role]; return r ? sum + pts(r.card_id) : sum; }, 0);

    // ---- KPI computations ----

    const filledLineupCards = lineup.slots
        .map(s => cardMap[s.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const lineupKpis = buildLineupKpis(filledLineupCards, lineupPts, totalDefIF, totalDefOF);

    const filledBenchCards = benchRoles
        .map(role => benchByRole[role])
        .filter(Boolean)
        .map(s => cardMap[s!.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const benchKpis = buildBenchKpis(filledBenchCards, rosterData?.benchPtsMultiplier ?? 1);

    const filledRotCards = (ROTATION_ROLES as readonly string[])
        .slice(0, rosterData?.maxRotation)
        .map(role => rotByRole[role])
        .filter(Boolean)
        .map(r => cardMap[r!.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const rotationKpis = buildPitcherKpis(filledRotCards, rotationPts);

    const filledBullCards = bullpenRoles
        .map(role => bullByRole[role])
        .filter(Boolean)
        .map(r => cardMap[r!.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const bullpenKpis = buildPitcherKpis(filledBullCards, bullpenPts);

    const sections = rosterData ? [
        {
            label: 'Rotation', total: rotationPts, maxPlayers: rosterData.maxRotation,
            roles: [...ROTATION_ROLES].slice(0, rosterData?.maxRotation) as string[],
            kpis: rotationKpis,
            getCard:    (role: string) => { const r = rotByRole[role]; return r ? cardMap[r.card_id] : null; },
            hasAssignment: (role: string) => !!rotByRole[role],
            onItemClick: onRoleClick && !readOnly ? (role: string) => onRoleClick(role, rotByRole[role] ?? null) : undefined,
        },
        {
            label: 'Bullpen', total: bullpenPts,
            roles: bullpenRoles,
            kpis: bullpenKpis,
            getCard:    (role: string) => { const r = bullByRole[role]; return r ? cardMap[r.card_id] : null; },
            hasAssignment: (role: string) => !!bullByRole[role],
            onItemClick: onRoleClick && !readOnly ? (role: string) => onRoleClick(role, bullByRole[role] ?? null) : undefined,
        },
        {
            label: 'Bench',
            total: benchPts,
            roles: benchRoles,
            kpis: benchKpis,
            getCard:    (role: string) => { const s = benchByRole[role]; return s ? cardMap[s.card_id] : null; },
            hasAssignment: (role: string) => !!benchByRole[role],
            onItemClick: onBenchClick && !readOnly ? (role: string) => onBenchClick(role, benchByRole[role] ?? null) : undefined,
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
                    { label: 'TOTAL OF', value: totalDefOF, color: colorDefOF, top: 80, left: 15 },
                    { label: 'TOTAL IF', value: totalDefIF, color: colorDefIF, top: 84, left: 15 },
                    { label: 'CA ARM',   value: armC,       color: colorArmC,  top: 88, left: 15 },
                ] as const).map(({ label, value, color, top, left }) => value !== null && (
                    <div
                        key={label}
                        className="absolute -translate-x-1/2 flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-black/50 backdrop-blur-sm pointer-events-none select-none"
                        style={{ top: `${top}%`, left: `${left}%` }}
                    >
                        <span className="text-[10px] font-semibold text-white/60 uppercase tracking-wide">{label}</span>
                        <span className={`text-xs font-black ${color}`}>
                            {value > 0 ? `+${value}` : value}
                        </span>
                    </div>
                ))}

                <div className="absolute inset-0" >
                    <FieldViewSectionHeader label="Starting Lineup" filledCount={lineup.slots.length} maxPlayers={9} total={lineupPts} kpis={lineupKpis} />
                </div>

                {FIELD_POSITIONS.map(pos => {
                    const [left, top] = POSITION_COORDS[pos];
                    const slot = slotByPosition[pos] ?? null;
                    const card = slot ? cardMap[slot.card_id] : null;
                    const isActive = activePosition === pos;
                    const isPeerHovered = !isActive && !!card && card.card_id === hoveredCardId;

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
                            onMouseEnter={card ? () => onCardHover?.(card.card_id) : undefined}
                            onMouseLeave={() => onCardHover?.(null)}
                        >
                            <div className={isActive ? 'rounded-lg ring-2 ring-(--secondary) shadow-[0_0_14px_4px_color-mix(in_srgb,var(--secondary)_50%,transparent)] animate-pulse' : ''}>
                                {card ? (
                                    <CardItemCompactFromCardDatabaseRecord
                                        card={card}
                                        className={`${isPeerHovered ? 'scale-[1.05]' : 'hover:scale-[1.05]'} active:scale-[0.975] transition-transform`}
                                        size="lg"
                                        fieldPosition={pos}
                                        onClick={() => setDetailCard(card)}
                                        isSelected={isActive}
                                        actionButton={!readOnly ? {
                                            icon: <FaPencil className="w-2.5 h-2.5" />,
                                            onClick: () => onSlotClick(pos, slot),
                                            label: 'Replace card',
                                        } : undefined}
                                    />
                                ) : slot && isLoadingCards ? (
                                    <PositionSlotLoadingPlaceholder position={pos} />
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

            {sections.map(({ label, roles, total, kpis, getCard, hasAssignment, onItemClick, maxPlayers }) => {
                const filledCount = roles.filter(r => getCard(r)).length;
                return (
                    <div key={label} className="border-t border-(--divider)" onClick={onItemClick ? e => e.stopPropagation() : undefined}>
                        <FieldViewSectionHeader label={label} filledCount={filledCount} maxPlayers={maxPlayers} total={total} kpis={kpis} />
                        <div className="grid grid-cols-2 gap-1.5 px-3 pb-3">
                            {roles.map(role => {
                                const card = getCard(role);
                                const isPeerHovered = !!card && card.card_id === hoveredCardId;
                                const isPending = !card && hasAssignment(role) && isLoadingCards;
                                return card ? (
                                    <div
                                        key={role}
                                        onMouseEnter={() => onCardHover?.(card.card_id)}
                                        onMouseLeave={() => onCardHover?.(null)}
                                    >
                                        <CardItemCompactFromCardDatabaseRecord
                                            card={card}
                                            className={`${isPeerHovered ? 'scale-[1.025]' : 'hover:scale-[1.025]'} active:scale-[0.975] transition-transform`}
                                            size="lg"
                                            onClick={() => setDetailCard(card)}
                                            actionButton={onItemClick ? {
                                                icon: <FaPencil className="w-2.5 h-2.5" />,
                                                onClick: () => onItemClick(role),
                                                label: 'Replace card',
                                            } : undefined}
                                        />
                                    </div>
                                ) : isPending ? (
                                    <SlotLoadingPlaceholder key={role} />
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
            <div className={detailCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={() => setDetailCard(null)} isVisible={!!detailCard}>
                    <CardDetail cardId={detailCard?.card_id} context="roster" />
                </Modal>
            </div>
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

const LoadingDots = ({ dotClassName }: { dotClassName: string }) => (
    <span className="flex items-center gap-1 shrink-0">
        <span className={`w-1 h-1 rounded-full animate-bounce ${dotClassName}`} style={{ animationDelay: '0ms' }} />
        <span className={`w-1 h-1 rounded-full animate-bounce ${dotClassName}`} style={{ animationDelay: '150ms' }} />
        <span className={`w-1 h-1 rounded-full animate-bounce ${dotClassName}`} style={{ animationDelay: '300ms' }} />
    </span>
);

function PositionSlotLoadingPlaceholder({ position }: { position: string }) {
    return (
        <div className="w-full flex items-center justify-between gap-1 rounded-lg px-2 h-12 border-2 border-dashed border-white/30 bg-black/20 backdrop-blur-[2px]">
            <span className="text-[11px] font-black text-white/70">{position}</span>
            <LoadingDots dotClassName="bg-white/60" />
        </div>
    );
}

function SlotLoadingPlaceholder() {
    return (
        <div className="flex items-center justify-center h-9 rounded-lg border border-dashed border-(--divider)">
            <LoadingDots dotClassName="bg-(--text-tertiary)" />
        </div>
    );
}
