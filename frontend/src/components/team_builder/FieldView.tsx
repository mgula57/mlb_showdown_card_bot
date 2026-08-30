import { useState } from 'react';
import type { Lineup, LineupSlot, TeamRosterSlot, PitcherAssignment } from '../../api/userTeams';
import { ROTATION_ROLES } from '../../api/userTeams';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { FaPlus, FaPencil } from 'react-icons/fa6';
import { defenseAtPosition, OF_POSITIONS, IF_POSITIONS } from '../shared/DefenseUtils';
import { buildLineupKpis, buildBenchKpis, buildPitcherKpis } from './TeamKpiUtils';
import { SectionHeader } from '../shared/SectionHeader';
import { Modal } from '../shared/Modal';
import { CardDetail } from '../cards/CardDetail';

// Percentage-based [left, top] coordinates relative to the Field.png container
export const POSITION_COORDS: Record<string, [number, number]> = {
    CF:  [50, 20],
    LF:  [16, 26],
    RF:  [84, 26],
    SS:  [32, 45],
    '2B': [68, 45],
    '3B': [18, 65],
    '1B': [82, 65],
    C:   [50, 87],
    DH:  [84, 87],
    // Award-winner-only slots (Gold Glove Pitcher/Utility, Silver Slugger Utility)
    P:   [50, 67],
    UT:  [84, 87],
};

export const FIELD_POSITIONS = ['CF', 'LF', 'RF', 'SS', '2B', '3B', '1B', 'C', 'DH'] as const;

export type FieldViewRosterData = {
    roster: TeamRosterSlot[];
    rotation: PitcherAssignment[];
    benchPtsMultiplier: number;
    minBench: number;
    minBullpen: number;
    maxRotation: number;
    /** How many bench / bullpen rows to render (filled + trailing empty "add" placeholders).
     *  Set only while drafting/editing; omitted for read-only views, which show filled only. */
    draftSlots?: { bench: number; bullpen: number };
};

type FieldViewProps = {
    lineup: Lineup;
    cardMap: Record<string, CardDatabaseRecord | null>;
    onSlotClick: (position: string, currentSlot: LineupSlot | null) => void;
    /** Bench is free-form: `current` is the row being replaced, or null to add a new one. */
    onBenchClick?: (current: TeamRosterSlot | null) => void;
    /** Bullpen is free-form: `current` is the arm being replaced, or null to add a new one. */
    onBullpenClick?: (current: PitcherAssignment | null) => void;
    onRoleClick?: (role: string, current: PitcherAssignment | null) => void;
    readOnly?: boolean;
    activePosition?: string | null;
    rosterData?: FieldViewRosterData;
    hoveredCardId?: string | null;
    onCardHover?: (cardId: string | null) => void;
    /** True while cardMap entries are still being fetched — shows loading placeholders for filled-but-unresolved slots */
    isLoadingCards?: boolean;
    /** Which field slots to render, e.g. append 'P'/'UT' for a Gold Glove/Silver Slugger showcase. Defaults to the standard 9-man lineup. */
    positions?: readonly string[];
    /** Label shown in the header above the field (defaults to "Starting Lineup") */
    headerLabel?: string;
    /** Hides the OF/IF/CA defense badges and points totals — off by default for read-only showcases where they don't apply */
    showDefenseSummary?: boolean;
    /** Shows the total points banner above the field — off by default for read-only showcases where it doesn't apply */
    showTotalPoints?: boolean;
    /** Which detail stat to show on the cards (defaults to 'defense') */
    detailStat1Category?: 'defense' | 'hr' | 'outs';
    /** card_id -> a simulated season's statline (`SimStatLine.stats`) - when a slot's card_id has
     * an entry, the card-detail modal opened from that slot shows a SIM column (see
     * `CardDetail`'s `simStats` prop) alongside the card's projection and real-life stat. */
    simStatsMap?: Record<string, Record<string, number>>;
    /** Passed to `CardDetail`'s `tooltip` when the opened slot has a `simStatsMap` entry - see
     * `CardDetail`'s prop of the same name. */
    simStatsTooltip?: string;
};


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

export function FieldView({
    lineup, cardMap, onSlotClick, onBenchClick, onBullpenClick, onRoleClick, readOnly = false, activePosition,
    rosterData, hoveredCardId, onCardHover, isLoadingCards,
    positions = FIELD_POSITIONS, headerLabel = 'Starting Lineup', showDefenseSummary = true, showTotalPoints = false, detailStat1Category = 'defense',
    simStatsMap, simStatsTooltip,
}: FieldViewProps) {
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

    // Rotation stays slot-precise (SP1..SPn). Bench and bullpen are free-form: sorted by card
    // points descending, with a fixed number of rows (filled cards + trailing empty "add"
    // placeholders) — `rosterData.draftSlots` while editing, else just the filled count.
    const byPointsDesc = <T extends { card_id: string }>(a: T, b: T) => pts(b.card_id) - pts(a.card_id);
    const benchSlots    = (rosterData?.roster ?? []).filter(s => s.roster_position.toUpperCase() === 'BE').slice().sort(byPointsDesc);
    const rotByRole     = Object.fromEntries((rosterData?.rotation ?? []).filter(r => (ROTATION_ROLES as readonly string[]).includes(r.role)).map(r => [r.role, r]));
    const bullpenSlots  = (rosterData?.rotation ?? []).filter(r => !(ROTATION_ROLES as readonly string[]).includes(r.role)).slice().sort(byPointsDesc);

    const benchRowCount   = rosterData ? (rosterData.draftSlots?.bench   ?? benchSlots.length)   : 0;
    const bullpenRowCount = rosterData ? (rosterData.draftSlots?.bullpen ?? bullpenSlots.length) : 0;

    const lineupPts = lineup.slots.reduce((sum, slot) => sum + (cardMap[slot.card_id]?.points ?? 0), 0);
    const benchPts    = benchSlots.reduce((sum, s) => sum + Math.round(pts(s.card_id) * (rosterData?.benchPtsMultiplier ?? 1)), 0);
    const rotationPts = (ROTATION_ROLES as readonly string[]).reduce((sum, role) => { const r = rotByRole[role]; return r ? sum + pts(r.card_id) : sum; }, 0);
    const bullpenPts  = bullpenSlots.reduce((sum, r) => sum + pts(r.card_id), 0);
    const totalPts    = lineupPts + benchPts + rotationPts + bullpenPts;

    // ---- KPI computations ----

    const filledLineupCards = lineup.slots
        .map(s => cardMap[s.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const lineupKpis = buildLineupKpis(filledLineupCards, lineupPts, totalDefIF, totalDefOF);

    const filledBenchCards = benchSlots
        .map(s => cardMap[s.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const benchKpis = buildBenchKpis(filledBenchCards, rosterData?.benchPtsMultiplier ?? 1);

    const filledRotCards = (ROTATION_ROLES as readonly string[])
        .slice(0, rosterData?.maxRotation)
        .map(role => rotByRole[role])
        .filter(Boolean)
        .map(r => cardMap[r!.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const rotationKpis = buildPitcherKpis(filledRotCards, rotationPts);

    const filledBullCards = bullpenSlots
        .map(r => cardMap[r.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const bullpenKpis = buildPitcherKpis(filledBullCards, bullpenPts);

    // A single generic section shape drives all three groups. Rotation keys off its real role
    // slots; bench/bullpen key off a synthetic index (label is always the generic 'BE' / 'RP').
    const genericRoles = (n: number, prefix: string) => Array.from({ length: n }, (_, i) => `${prefix}${i + 1}`);

    const sections = rosterData ? [
        {
            label: 'Rotation', total: rotationPts, maxPlayers: rosterData.maxRotation,
            roles: [...ROTATION_ROLES].slice(0, rosterData?.maxRotation) as string[],
            placeholderLabel: undefined as string | undefined,
            kpis: rotationKpis,
            getCard:    (role: string) => { const r = rotByRole[role]; return r ? cardMap[r.card_id] : null; },
            hasAssignment: (role: string) => !!rotByRole[role],
            onItemClick: onRoleClick && !readOnly ? (role: string) => onRoleClick(role, rotByRole[role] ?? null) : undefined,
        },
        {
            label: 'Bullpen', total: bullpenPts,
            roles: genericRoles(bullpenRowCount, 'RP'),
            placeholderLabel: 'RP',
            kpis: bullpenKpis,
            getCard:    (role: string) => { const r = bullpenSlots[Number(role.slice(2)) - 1]; return r ? cardMap[r.card_id] : null; },
            hasAssignment: (role: string) => !!bullpenSlots[Number(role.slice(2)) - 1],
            onItemClick: onBullpenClick && !readOnly ? (role: string) => onBullpenClick(bullpenSlots[Number(role.slice(2)) - 1] ?? null) : undefined,
        },
        {
            label: 'Bench',
            total: benchPts,
            roles: genericRoles(benchRowCount, 'BE'),
            placeholderLabel: 'BE',
            kpis: benchKpis,
            getCard:    (role: string) => { const s = benchSlots[Number(role.slice(2)) - 1]; return s ? cardMap[s.card_id] : null; },
            hasAssignment: (role: string) => !!benchSlots[Number(role.slice(2)) - 1],
            onItemClick: onBenchClick && !readOnly ? (role: string) => onBenchClick(benchSlots[Number(role.slice(2)) - 1] ?? null) : undefined,
            ptsMultiplier: rosterData?.benchPtsMultiplier,
        },
    ] : [];

    return (
        <div className="flex flex-col @container">
            {showTotalPoints && (
                <div className="flex items-center justify-center gap-2 p-1">
                    <span className="text-[11px] font-semibold uppercase tracking-wide text-(--text-tertiary)">Total Points</span>
                    <span className="text-sm font-black tabular-nums text-(--text-primary)">{totalPts}</span>
                </div>
            )}
            <div className="relative w-full" style={{ aspectRatio: '1 / 1' }}>
                <img
                    src="/images/teams/Field.png"
                    alt="Baseball field"
                    className="w-full h-full select-none pointer-events-none"
                    draggable={false}
                />

                {showDefenseSummary && ([
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
                    <SectionHeader
                        variant="overlay"
                        label={headerLabel}
                        filledCount={lineup.slots.length}
                        maxPlayers={positions.length}
                        total={showDefenseSummary ? lineupPts : 0}
                        kpis={showDefenseSummary ? lineupKpis : undefined}
                    />
                </div>

                {positions.map(pos => {
                    // UT normally reuses DH's spot, but shifts left when both are shown together (e.g. Silver Slugger) to avoid overlapping
                    const [left, top] = pos === 'UT' && positions.includes('DH')
                        ? [16, 85]
                        : (POSITION_COORDS[pos] ?? [50, 50]);
                    const slot = slotByPosition[pos] ?? null;
                    const card = slot ? cardMap[slot.card_id] : null;
                    const isActive = activePosition === pos;
                    const isPeerHovered = !isActive && !!card && card.card_id === hoveredCardId;

                    return (
                        <div
                            key={pos}
                            className={`
                                absolute transition-all duration-200 
                                ${isActive ? 'z-10' : ''}
                                ${pos === 'CF' ? 'translate-y-[20%] @[400px]:translate-y-0' : ''}
                                ${['LF', 'RF'].includes(pos) ? 'translate-y-[10%] @[400px]:translate-y-0' : ''}
                            `}
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
                                        fieldPosition={pos}
                                        detailStat1Category={detailStat1Category}
                                        onClick={() => setDetailCard(card)}
                                        isSelected={isActive}
                                        actionButton={!readOnly ? {
                                            icon: <FaPencil />,
                                            onClick: () => onSlotClick(pos, slot),
                                            label: 'Replace card',
                                            placement: 'left'
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

            {sections.map(({ label, roles, total, kpis, getCard, hasAssignment, onItemClick, maxPlayers, ptsMultiplier, placeholderLabel }) => {
                const filledCount = roles.filter(r => getCard(r)).length;
                return (
                    <div key={label} className="border-t border-(--divider)" onClick={onItemClick ? e => e.stopPropagation() : undefined}>
                        <SectionHeader variant="overlay" label={label} filledCount={filledCount} maxPlayers={maxPlayers} total={total} kpis={kpis} />
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
                                            ptsMultiplier={ptsMultiplier}
                                            onClick={() => setDetailCard(card)}
                                            actionButton={onItemClick ? {
                                                icon: <FaPencil />,
                                                onClick: () => onItemClick(role),
                                                label: 'Replace card',
                                                placement: 'left',
                                            } : undefined}
                                        />
                                    </div>
                                ) : isPending ? (
                                    <SlotLoadingPlaceholder key={role} />
                                ) : (
                                    <PositionSlotPlaceholder
                                        key={role}
                                        position={placeholderLabel ?? role}
                                        onClick={onItemClick ? () => onItemClick(role) : undefined}
                                        isActive={isPeerHovered}
                                    />
                                );
                            })}
                        </div>
                    </div>
                );
            })}

            {/* Add padding at the end */}
            <div className="h-48" />

            <div className={detailCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={() => setDetailCard(null)} isVisible={!!detailCard} size='xl'>
                    <CardDetail
                        cardId={detailCard?.card_id}
                        context="roster"
                        simStats={detailCard ? simStatsMap?.[detailCard.card_id] : undefined}
                        tooltip={detailCard && simStatsMap?.[detailCard.card_id] ? simStatsTooltip : undefined}
                    />
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
                rounded-lg px-2 h-12 @[340px]:h-16
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
