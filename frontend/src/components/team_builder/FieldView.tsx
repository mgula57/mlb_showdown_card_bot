import type { Lineup, LineupSlot, TeamRosterSlot, PitcherAssignment } from '../../api/userTeams';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
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
};

// ---- KPI helpers ----

type KpiTile = { label: string; value: string };

function avgOf(nums: (number | null | undefined)[]): number | null {
    const valid = nums.filter((n): n is number => n != null);
    return valid.length > 0 ? valid.reduce((a, b) => a + b, 0) / valid.length : null;
}

// Max defense value for a card across non-DH, non-C positions (excludes catcher arm)
function cardMaxFieldDefense(card: CardDatabaseRecord): number | null {
    const pad = card.positions_and_defense;
    if (!pad) return null;
    const values = Object.entries(pad)
        .filter(([pos]) => pos !== 'DH' && pos !== 'C')
        .map(([, val]) => (typeof val === 'number' ? val : null))
        .filter((v): v is number => v != null);
    return values.length > 0 ? Math.max(...values) : null;
}

const fmtBat = (n: number) => n.toFixed(3).replace('0.', '.');
const fmtDef = (n: number) => (n > 0 ? `+${n}` : `${n}`);
const fmtAvg = (n: number) => Math.round(n).toString();

// ---- Section header ----

function FieldViewSectionHeader({ label, filledCount, maxPlayers, total, kpis }: {
    label: string;
    filledCount: number;
    maxPlayers?: number;
    total: number;
    kpis?: KpiTile[];
}) {
    return (
        <div className="px-3 py-1.5 backdrop-blur-sm bg-(--background)/40">
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

export function FieldView({ lineup, cardMap, onSlotClick, onBenchClick, onRoleClick, readOnly = false, activePosition, rosterData }: FieldViewProps) {
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
    const colorDefIF = avgDefIF !== null ? (avgDefIF > 3 ? 'text-(--green)' : avgDefIF >= 1.75 ? 'text-(--warning)' : 'text-(--red)') : 'text-primary';

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

    // Lineup KPIs
    const filledLineupCards = lineup.slots
        .map(s => cardMap[s.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const lineupFilledCount = filledLineupCards.length;
    const lineupAvgPts      = lineupFilledCount > 0 ? lineupPts / lineupFilledCount : null;
    const lineupAvgOps      = avgOf(filledLineupCards.map(c => c.real_onbase_plus_slugging));
    const lineupAvgObp      = avgOf(filledLineupCards.map(c => c.real_onbase_perc));
    const lineupAvgSpeed    = avgOf(filledLineupCards.map(c => c.speed));
    const lineupTotalDef    = (totalDefIF ?? 0) + (totalDefOF ?? 0);
    const lineupKpis: KpiTile[] = [
        lineupAvgPts  != null              ? { label: 'Avg PTS',  value: fmtAvg(lineupAvgPts) }       : null,
        lineupAvgOps  != null              ? { label: 'Exp OPS',  value: fmtBat(lineupAvgOps) }        : null,
        lineupAvgSpeed != null             ? { label: 'Avg SPD',  value: fmtAvg(lineupAvgSpeed) }      : null,
        lineupAvgObp  != null              ? { label: 'Avg OB',   value: fmtBat(lineupAvgObp) }        : null,
        lineupTotalDef !== 0               ? { label: 'DEF',      value: fmtDef(lineupTotalDef) }      : null,
    ].filter(Boolean) as KpiTile[];

    // Bench KPIs
    const filledBenchCards = benchRoles
        .map(role => benchByRole[role])
        .filter(Boolean)
        .map(s => cardMap[s!.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const benchFilledCount = filledBenchCards.length;
    const benchRawPts      = filledBenchCards.reduce((sum, c) => sum + (c.points ?? 0), 0);
    const benchAvgPts      = benchFilledCount > 0 ? benchRawPts / benchFilledCount : null;
    const benchTotalDef    = filledBenchCards.reduce((sum, c) => sum + (cardMaxFieldDefense(c) ?? 0), 0);
    const benchMultiplier  = rosterData?.benchPtsMultiplier ?? 1;
    const benchKpis: KpiTile[] = [
        benchAvgPts    != null         ? { label: 'Avg PTS',    value: fmtAvg(benchAvgPts) }         : null,
        benchMultiplier !== 1          ? { label: 'Multiplier', value: `${benchMultiplier}x` }        : null,
        benchTotalDef  !== 0           ? { label: 'DEF',        value: fmtDef(benchTotalDef) }       : null,
    ].filter(Boolean) as KpiTile[];

    // Rotation KPIs
    const filledRotCards = (ROTATION_ROLES as readonly string[])
        .slice(0, rosterData?.maxRotation)
        .map(role => rotByRole[role])
        .filter(Boolean)
        .map(r => cardMap[r!.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const rotFilledCount  = filledRotCards.length;
    const rotAvgPts       = rotFilledCount > 0 ? rotationPts / rotFilledCount : null;
    const rotAvgEra       = avgOf(filledRotCards.map(c => c.real_earned_run_avg));
    const rotAvgWhip      = avgOf(filledRotCards.map(c => c.real_whip));
    const rotAvgControl   = avgOf(filledRotCards.map(c => c.command));
    const rotAvgOuts      = avgOf(filledRotCards.map(c => c.outs));
    const rotationKpis: KpiTile[] = [
        rotAvgPts     != null ? { label: 'Avg PTS',  value: fmtAvg(rotAvgPts) }        : null,
        rotAvgEra     != null ? { label: 'Exp ERA',  value: rotAvgEra.toFixed(2) }      : null,
        rotAvgWhip    != null ? { label: 'Exp WHIP', value: rotAvgWhip.toFixed(2) }     : null,
        rotAvgControl != null ? { label: 'Avg CTL',  value: rotAvgControl.toFixed(1) }  : null,
        rotAvgOuts    != null ? { label: 'Avg OUTS', value: rotAvgOuts.toFixed(1) }     : null,
    ].filter(Boolean) as KpiTile[];

    // Bullpen KPIs
    const filledBullCards = bullpenRoles
        .map(role => bullByRole[role])
        .filter(Boolean)
        .map(r => cardMap[r!.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const bullFilledCount  = filledBullCards.length;
    const bullAvgPts       = bullFilledCount > 0 ? bullpenPts / bullFilledCount : null;
    const bullAvgEra       = avgOf(filledBullCards.map(c => c.real_earned_run_avg));
    const bullAvgWhip      = avgOf(filledBullCards.map(c => c.real_whip));
    const bullAvgControl   = avgOf(filledBullCards.map(c => c.command));
    const bullAvgOuts      = avgOf(filledBullCards.map(c => c.outs));
    const bullpenKpis: KpiTile[] = [
        bullAvgPts     != null ? { label: 'Avg PTS',  value: fmtAvg(bullAvgPts) }        : null,
        bullAvgEra     != null ? { label: 'Exp ERA',  value: bullAvgEra.toFixed(2) }      : null,
        bullAvgWhip    != null ? { label: 'Exp WHIP', value: bullAvgWhip.toFixed(2) }     : null,
        bullAvgControl != null ? { label: 'Avg CTL',  value: bullAvgControl.toFixed(1) }  : null,
        bullAvgOuts    != null ? { label: 'Avg OUTS', value: bullAvgOuts.toFixed(1) }     : null,
    ].filter(Boolean) as KpiTile[];

    const sections = rosterData ? [
        {
            label: 'Bench',
            total: benchPts,
            roles: benchRoles,
            kpis: benchKpis,
            getCard:    (role: string) => { const s = benchByRole[role]; return s ? cardMap[s.card_id] : null; },
            onItemClick: onBenchClick && !readOnly ? (role: string) => onBenchClick(role, benchByRole[role] ?? null) : undefined,
        },
        {
            label: 'Rotation', total: rotationPts, maxPlayers: rosterData.maxRotation,
            roles: [...ROTATION_ROLES].slice(0, rosterData?.maxRotation) as string[],
            kpis: rotationKpis,
            getCard:    (role: string) => { const r = rotByRole[role]; return r ? cardMap[r.card_id] : null; },
            onItemClick: onRoleClick && !readOnly ? (role: string) => onRoleClick(role, rotByRole[role] ?? null) : undefined,
        },
        {
            label: 'Bullpen', total: bullpenPts,
            roles: bullpenRoles,
            kpis: bullpenKpis,
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
                    { label: 'OF', value: totalDefOF, color: colorDefOF, top: 25, left: 50 },
                    { label: 'IF', value: totalDefIF, color: colorDefIF, top: 53, left: 50 },
                    { label: 'C Arm', value: armC, color: colorArmC, top: 83, left: 25 },
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
                                    <CardItemCompactFromCardDatabaseRecord
                                        card={card}
                                        className="hover:scale-[1.05] active:scale-[0.975] transition-transform"
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

            {sections.map(({ label, roles, total, kpis, getCard, onItemClick, maxPlayers }) => {
                const filledCount = roles.filter(r => getCard(r)).length;
                return (
                    <div key={label} className="border-t border-(--divider)" onClick={onItemClick ? e => e.stopPropagation() : undefined}>
                        <FieldViewSectionHeader label={label} filledCount={filledCount} maxPlayers={maxPlayers} total={total} kpis={kpis} />
                        <div className="grid grid-cols-2 gap-1.5 px-3 pb-3">
                            {roles.map(role => {
                                const card = getCard(role);
                                return card ? (
                                    <CardItemCompactFromCardDatabaseRecord
                                        key={role}
                                        card={card}
                                        className="hover:scale-[1.025] active:scale-[0.975] transition-transform"
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
