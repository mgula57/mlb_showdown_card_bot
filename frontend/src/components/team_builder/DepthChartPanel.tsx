import { useState } from 'react';
import type { Team, LineupSlot, PitcherAssignment, TeamRosterSlot, TeamUpdatePayload } from '../../api/userTeams';
import { ROTATION_ROLES } from '../../api/userTeams';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemFromCardDatabaseRecord, CardItemSkeleton } from '../cards/CardItem';
import { FaPlus, FaPencil, FaChevronUp, FaChevronDown } from 'react-icons/fa6';
import { defenseAtPosition, OF_POSITIONS, IF_POSITIONS } from '../shared/DefenseUtils';
import { effectiveBenchBullpenMinimums, benchBullpenSlotCounts } from '../../domain/roster';
import { buildLineupKpis, buildBenchKpis, buildPitcherKpis } from './TeamKpiUtils';
import { Modal } from '../shared/Modal';
import { SectionHeader } from '../shared/SectionHeader';
import { CardDetail } from '../cards/CardDetail';

const FIELD_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'] as const;

type DepthChartPanelProps = {
    team: Team;
    cardMap: Record<string, CardDatabaseRecord | null>;
    onSlotClick: (position: string, slot: LineupSlot | null) => void;
    onRoleClick: (role: string, current: PitcherAssignment | null) => void;
    /** Bullpen is free-form: `current` is the arm being replaced, or null to add a new one. */
    onBullpenClick: (current: PitcherAssignment | null) => void;
    /** Bench is free-form: `current` is the row being replaced, or null to add a new one. */
    onBenchClick: (current: TeamRosterSlot | null) => void;
    /** Called when a rotation reorder changes the roster. Partial update merged into the team. */
    onReorder?: (updates: Pick<TeamUpdatePayload, 'roster' | 'rotation'>) => void;
    readOnly?: boolean;
    activePosition?: string | null;
    activeRole?: string | null;
    hoveredCardId?: string | null;
    onCardHover?: (cardId: string | null) => void;
    /** True while cardMap entries are still being fetched — shows a skeleton for filled-but-unresolved slots */
    isLoadingCards?: boolean;
};

function PositionRow({
    label,
    card,
    isPending,
    onClick,
    onDetailClick,
    readOnly,
    isActive,
    isPeerHovered,
    onMouseEnter,
    onMouseLeave,
    ptsMultiplier,
    onMoveUp,
    onMoveDown,
}: {
    label: string;
    card: CardDatabaseRecord | null | undefined;
    isPending?: boolean;
    onClick: () => void;
    onDetailClick?: () => void;
    readOnly: boolean;
    isActive?: boolean;
    isPeerHovered?: boolean;
    onMouseEnter?: () => void;
    onMouseLeave?: () => void;
    ptsMultiplier?: number;
    onMoveUp?: () => void;
    onMoveDown?: () => void;
}) {
    if (!card && isPending) {
        return (
            <div className="flex items-center gap-3 min-h-9 shrink-0">
                <span className="text-[11px] font-bold w-6 shrink-0 text-right text-(--text-tertiary)">{label}</span>
                <CardItemSkeleton className="flex-1 min-w-0" />
            </div>
        );
    }

    return (
        <div
            className={`
                flex items-center gap-3 min-h-9 rounded-lg shrink-0
                transition-all duration-200
                ${isActive ? 'ring-1 ring-(--secondary) shadow-[0_0_8px_2px_color-mix(in_srgb,var(--secondary)_40%,transparent)] animate-pulse px-1 -mx-1' : ''}`}
                onClick={e => e.stopPropagation()}
                onMouseEnter={onMouseEnter}
                onMouseLeave={onMouseLeave}
            >
            <span className={`text-[11px] font-bold w-6 shrink-0 text-right ${isActive ? 'text-(--secondary)' : 'text-(--text-tertiary)'}`}>{label}</span>
            {card ? (
                <div className={`flex-1 min-w-0 transition-transform ${isPeerHovered ? 'scale-[1.02]' : 'hover:scale-[1.02]'} active:scale-[0.98]`}>
                    <CardItemFromCardDatabaseRecord
                        card={card}
                        isSelected={isActive}
                        onClick={onDetailClick}
                        cardPtsMultiplier={ptsMultiplier}
                        actionButton={!readOnly ? {
                            icon: <FaPencil className="w-2.5 h-2.5" />,
                            onClick,
                            label: 'Replace card',
                        } : undefined}
                    />
                </div>
            ) : (
                <button
                    type="button"
                    onClick={onClick}
                    disabled={readOnly}
                    className={`flex-1 flex items-center gap-1.5 px-3 h-18 rounded-lg border border-dashed
                        text-[11px] disabled:pointer-events-none disabled:opacity-40 transition-colors
                        ${isActive
                            ? 'border-(--secondary)/70 text-(--secondary) hover:border-(--secondary) hover:text-(--secondary)'
                            : 'border-(--divider) text-(--text-tertiary) hover:border-(--secondary)/50 hover:text-(--secondary)'
                        }`}
                >
                    {!readOnly && <FaPlus className="text-[9px]" />}
                    <span>Empty</span>
                </button>
            )}
            {/* Reorder controls (rotation / bullpen only) */}
            {(onMoveUp || onMoveDown) && !readOnly && card && (
                <div className="flex flex-col shrink-0">
                    <button type="button" onClick={onMoveUp} disabled={!onMoveUp}
                        className="text-(--text-tertiary) hover:text-(--text-secondary) disabled:opacity-20 cursor-pointer">
                        <FaChevronUp className="text-[8px]" />
                    </button>
                    <button type="button" onClick={onMoveDown} disabled={!onMoveDown}
                        className="text-(--text-tertiary) hover:text-(--text-secondary) disabled:opacity-20 cursor-pointer">
                        <FaChevronDown className="text-[8px]" />
                    </button>
                </div>
            )}
        </div>
    );
}

export function DepthChartPanel({
    team,
    cardMap,
    onSlotClick,
    onRoleClick,
    onBullpenClick,
    onBenchClick,
    onReorder,
    readOnly = false,
    activePosition,
    activeRole,
    hoveredCardId,
    onCardHover,
    isLoadingCards,
}: DepthChartPanelProps) {
    const [detailCard, setDetailCard] = useState<CardDatabaseRecord | null>(null);

    const lineup = team.lineups[0] ?? { name: 'Default', index: 0, slots: [] };
    const slotByPos = Object.fromEntries(lineup.slots.map(s => [s.field_position, s]));
    const roleByKey = Object.fromEntries(team.rotation.map(r => [r.role, r]));

    const ACTIVE_ROTATION_ROLES = ROTATION_ROLES.slice(0, team.num_starters ?? 5);

    // Bench and bullpen are free-form: sorted by card points descending, with a fixed number
    // of rows (filled cards + trailing empty "add" placeholders). The placeholder count comes
    // from `benchBullpenSlotCounts` while editing; a read-only view just shows the filled rows.
    const pts = (cardId: string) => cardMap[cardId]?.points ?? 0;
    const byPointsDesc = <T extends { card_id: string }>(a: T, b: T) => pts(b.card_id) - pts(a.card_id);
    const { bench: benchMin, bullpen: bullpenMin } = effectiveBenchBullpenMinimums(team);
    const benchSlots   = team.roster.filter(s => s.roster_position.toUpperCase() === 'BE').slice().sort(byPointsDesc);
    const bullpenSlots = team.rotation.filter(r => !r.role.startsWith('SP')).slice().sort(byPointsDesc);

    const filledStarters = ACTIVE_ROTATION_ROLES.filter(role => roleByKey[role]).length;
    const draftRows = readOnly ? null : benchBullpenSlotCounts({
        rosterSize: team.roster_size,
        rosterCount: team.roster.length,
        lineup: { filled: lineup.slots.length, target: 9 },
        rotation: { filled: filledStarters, target: team.num_starters ?? 5 },
        bench: { filled: benchSlots.length, target: benchMin },
        bullpen: { filled: bullpenSlots.length, target: bullpenMin },
    });
    const benchRowCount   = draftRows ? draftRows.bench   : benchSlots.length;
    const bullpenRowCount  = draftRows ? draftRows.bullpen : bullpenSlots.length;

    // -------------------------------------------------------------------------
    // Reorder helpers (rotation only — bench/bullpen order is always by points)
    // -------------------------------------------------------------------------

    function swapRotation(roleA: string, roleB: string) {
        if (!onReorder) return;
        // Swap the roster_position values of the two SP slots.
        const roster = team.roster.map(s => {
            if (s.roster_position === roleA) return { ...s, roster_position: roleB };
            if (s.roster_position === roleB) return { ...s, roster_position: roleA };
            return s;
        });
        onReorder({ roster });
    }

    // Defense totals for lineup KPIs
    const totalDefOF = OF_POSITIONS.reduce((sum, pos) => {
        const slot = slotByPos[pos];
        const card = slot ? cardMap[slot.card_id] : null;
        return sum + (defenseAtPosition(card?.positions_and_defense, pos) ?? 0);
    }, 0);
    const totalDefIF = IF_POSITIONS.reduce((sum, pos) => {
        const slot = slotByPos[pos];
        const card = slot ? cardMap[slot.card_id] : null;
        return sum + (defenseAtPosition(card?.positions_and_defense, pos) ?? 0);
    }, 0);

    // Filled card lists for KPI builders
    const filledLineupCards = lineup.slots
        .map(s => cardMap[s.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const filledBenchCards = benchSlots
        .map(s => cardMap[s.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const filledRotCards = ACTIVE_ROTATION_ROLES
        .map(role => roleByKey[role])
        .filter(Boolean)
        .map(r => cardMap[r!.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const filledBullCards = bullpenSlots
        .map(r => cardMap[r.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);

    // Point totals
    const lineupPts   = filledLineupCards.reduce((sum, c) => sum + (c.points ?? 0), 0);
    const benchPts    = filledBenchCards.reduce((sum, c) => sum + Math.round((c.points ?? 0) * (team.bench_pts_multiplier ?? 1)), 0);
    const rotationPts = filledRotCards.reduce((sum, c) => sum + (c.points ?? 0), 0);
    const bullpenPts  = filledBullCards.reduce((sum, c) => sum + (c.points ?? 0), 0);

    // KPI tiles
    const lineupKpis   = buildLineupKpis(filledLineupCards, lineupPts, totalDefIF, totalDefOF);
    const benchKpis    = buildBenchKpis(filledBenchCards, team.bench_pts_multiplier ?? 1);
    const rotationKpis = buildPitcherKpis(filledRotCards, rotationPts);
    const bullpenKpis  = buildPitcherKpis(filledBullCards, bullpenPts);

    return (
        <div className="@container flex flex-col h-full min-h-0 px-4">
            <div className="flex flex-col @field-split:flex-row flex-1 min-h-0 gap-4">
                {/* Column 1: Position Players + Bench */}
                <div className="flex flex-col gap-1.5 @field-split:flex-1 @field-split:min-w-0 @field-split:min-h-0 @field-split:overflow-y-auto @field-split:pr-4 @field-split:border-r @field-split:border-(--divider)">
                    <div className="shrink-0"><SectionHeader label="Starting Lineup" filledCount={filledLineupCards.length} total={lineupPts} kpis={lineupKpis} /></div>
                    {FIELD_POSITIONS.map(pos => {
                        const slot = slotByPos[pos] ?? null;
                        const card = slot ? cardMap[slot.card_id] : null;
                        return (
                            <PositionRow
                                key={pos}
                                label={pos}
                                card={card}
                                isPending={!card && !!slot && isLoadingCards}
                                onClick={() => onSlotClick(pos, slot)}
                                onDetailClick={card ? () => setDetailCard(card) : undefined}
                                readOnly={readOnly}
                                isActive={activePosition === pos}
                                isPeerHovered={!!card && card.card_id === hoveredCardId}
                                onMouseEnter={card ? () => onCardHover?.(card.card_id) : undefined}
                                onMouseLeave={() => onCardHover?.(null)}
                            />
                        );
                    })}

                    <div className="shrink-0"><SectionHeader label="Bench" filledCount={filledBenchCards.length} total={benchPts} kpis={benchKpis} /></div>
                    {Array.from({ length: benchRowCount }).map((_, i) => {
                        const slot = benchSlots[i] ?? null;
                        const card = slot ? cardMap[slot.card_id] : null;
                        return (
                            <PositionRow
                                key={`bench-${i}`}
                                label="BE"
                                card={card}
                                isPending={!card && !!slot && isLoadingCards}
                                onClick={() => onBenchClick(slot)}
                                onDetailClick={card ? () => setDetailCard(card) : undefined}
                                readOnly={readOnly}
                                isActive={!card && activeRole === 'BE'}
                                isPeerHovered={!!card && card.card_id === hoveredCardId}
                                onMouseEnter={card ? () => onCardHover?.(card.card_id) : undefined}
                                onMouseLeave={() => onCardHover?.(null)}
                                ptsMultiplier={team.bench_pts_multiplier}
                            />
                        );
                    })}
                </div>

                {/* Column 2: Rotation + Bullpen */}
                <div className="flex flex-col gap-1.5 @field-split:flex-1 @field-split:min-w-0 @field-split:min-h-0 @field-split:overflow-y-auto">
                    <div className="shrink-0"><SectionHeader label="Rotation" filledCount={filledRotCards.length} total={rotationPts} kpis={rotationKpis} /></div>
                    {ACTIVE_ROTATION_ROLES.map((role, idx) => {
                        const assignment = roleByKey[role] ?? null;
                        const card = assignment ? cardMap[assignment.card_id] : null;
                        const prevRole = idx > 0 ? ACTIVE_ROTATION_ROLES[idx - 1] : null;
                        const nextRole = idx < ACTIVE_ROTATION_ROLES.length - 1 ? ACTIVE_ROTATION_ROLES[idx + 1] : null;
                        return (
                            <PositionRow
                                key={role}
                                label={role}
                                card={card}
                                isPending={!card && !!assignment && isLoadingCards}
                                onClick={() => onRoleClick(role, assignment)}
                                onDetailClick={card ? () => setDetailCard(card) : undefined}
                                readOnly={readOnly}
                                isActive={activeRole === role}
                                isPeerHovered={!!card && card.card_id === hoveredCardId}
                                onMouseEnter={card ? () => onCardHover?.(card.card_id) : undefined}
                                onMouseLeave={() => onCardHover?.(null)}
                                onMoveUp={prevRole ? () => swapRotation(role, prevRole) : undefined}
                                onMoveDown={nextRole ? () => swapRotation(role, nextRole) : undefined}
                            />
                        );
                    })}

                    <div className="shrink-0"><SectionHeader label="Bullpen" filledCount={filledBullCards.length} total={bullpenPts} kpis={bullpenKpis} /></div>
                    {Array.from({ length: bullpenRowCount }).map((_, i) => {
                        const assignment = bullpenSlots[i] ?? null;
                        const card = assignment ? cardMap[assignment.card_id] : null;
                        return (
                            <PositionRow
                                key={`bullpen-${i}`}
                                label="RP"
                                card={card}
                                isPending={!card && !!assignment && isLoadingCards}
                                onClick={() => onBullpenClick(assignment)}
                                onDetailClick={card ? () => setDetailCard(card) : undefined}
                                readOnly={readOnly}
                                isActive={!card && activeRole === 'RP'}
                                isPeerHovered={!!card && card.card_id === hoveredCardId}
                                onMouseEnter={card ? () => onCardHover?.(card.card_id) : undefined}
                                onMouseLeave={() => onCardHover?.(null)}
                            />
                        );
                    })}
                </div>
            </div>

            <div className={detailCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={() => setDetailCard(null)} isVisible={!!detailCard}>
                    <CardDetail
                        cardId={detailCard?.card_id}
                        context="roster"
                    />
                </Modal>
            </div>

        </div>
    );
}
