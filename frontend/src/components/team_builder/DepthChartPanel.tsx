import { useState } from 'react';
import type { Team, LineupSlot, PitcherAssignment, TeamRosterSlot } from '../../api/userTeams';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemFromCardDatabaseRecord } from '../cards/CardItem';
import { FaPlus, FaPencil } from 'react-icons/fa6';
import { defenseAtPosition, OF_POSITIONS, IF_POSITIONS } from '../shared/DefenseUtils';
import { type KpiTile, buildLineupKpis, buildBenchKpis, buildPitcherKpis } from './TeamKpiUtils';
import { Modal } from '../shared/Modal';
import { CardDetail } from '../cards/CardDetail';

const FIELD_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'] as const;
const ROTATION_ROLES  = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5'] as const;

type DepthChartPanelProps = {
    team: Team;
    cardMap: Record<string, CardDatabaseRecord | null>;
    onSlotClick: (position: string, slot: LineupSlot | null) => void;
    onRoleClick: (role: string, current: PitcherAssignment | null) => void;
    onBenchClick: (role: string, current: TeamRosterSlot | null) => void;
    readOnly?: boolean;
    activePosition?: string | null;
    activeRole?: string | null;
};

function PositionRow({
    label,
    card,
    onClick,
    onDetailClick,
    readOnly,
    isActive,
}: {
    label: string;
    card: CardDatabaseRecord | null | undefined;
    onClick: () => void;
    onDetailClick?: () => void;
    readOnly: boolean;
    isActive?: boolean;
}) {
    return (
        <div
            className={`
                flex items-center gap-3 min-h-9 rounded-lg
                transition-all duration-200
                ${isActive ? 'ring-1 ring-(--secondary) shadow-[0_0_8px_2px_color-mix(in_srgb,var(--secondary)_40%,transparent)] animate-pulse px-1 -mx-1' : ''}`}
                onClick={e => e.stopPropagation()}
            >
            <span className={`text-[11px] font-bold w-6 shrink-0 text-right ${isActive ? 'text-(--secondary)' : 'text-(--text-tertiary)'}`}>{label}</span>
            {card ? (
                <div className="flex-1 min-w-0 transition-transform hover:scale-[1.02] active:scale-[0.98]">
                    <CardItemFromCardDatabaseRecord
                        card={card}
                        isSelected={isActive}
                        onClick={onDetailClick}
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
                    <FaPlus className="text-[9px]" />
                    <span>Empty</span>
                </button>
            )}
        </div>
    );
}

function SectionHeader({ label, filledCount, total, kpis }: {
    label: string;
    filledCount: number;
    total: number;
    kpis?: KpiTile[];
}) {
    return (
        <div className="pt-3 pb-1">
            <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-semibold text-(--text-secondary) uppercase tracking-widest">{label}</span>
                <span className="text-[10px] text-(--text-tertiary)">{filledCount}</span>
                {total > 0 && (
                    <span className="ml-auto text-[10px] font-semibold text-(--text-tertiary)">{total} pts</span>
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

export function DepthChartPanel({
    team,
    cardMap,
    onSlotClick,
    onRoleClick,
    onBenchClick,
    readOnly = false,
    activePosition,
    activeRole,
}: DepthChartPanelProps) {
    const [detailCard, setDetailCard] = useState<CardDatabaseRecord | null>(null);

    const lineup = team.lineups[0] ?? { name: 'Default', slots: [] };
    const slotByPos = Object.fromEntries(lineup.slots.map(s => [s.field_position, s]));
    const roleByKey = Object.fromEntries(team.rotation.map(r => [r.role, r]));

    const BENCH_ROLES = Array.from({ length: team.min_bench }, (_, i) => `BE${i + 1}`);
    const benchSlots  = team.roster.filter(s => s.roster_position.toUpperCase() === 'BE');
    const benchByRole = Object.fromEntries(BENCH_ROLES.flatMap((role, i) => benchSlots[i] ? [[role, benchSlots[i]]] : []));

    const BULLPEN_ROLES = Array.from({ length: team.min_bullpen }, (_, i) => `RP${i + 1}`);
    const bullpenSlots  = team.rotation.filter(r => !r.role.startsWith('SP'));
    const bullpenByRole = Object.fromEntries(BULLPEN_ROLES.flatMap((role, i) => bullpenSlots[i] ? [[role, bullpenSlots[i]]] : []));
    const ACTIVE_ROTATION_ROLES = ROTATION_ROLES.slice(0, team.num_starters ?? 5);

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
    const filledBenchCards = BENCH_ROLES
        .map(role => benchByRole[role])
        .filter(Boolean)
        .map(s => cardMap[s!.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const filledRotCards = ACTIVE_ROTATION_ROLES
        .map(role => roleByKey[role])
        .filter(Boolean)
        .map(r => cardMap[r!.card_id])
        .filter((c): c is CardDatabaseRecord => !!c);
    const filledBullCards = BULLPEN_ROLES
        .map(role => bullpenByRole[role])
        .filter(Boolean)
        .map(r => cardMap[r!.card_id])
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
        <div className="flex flex-col gap-1.5 px-4">
            {/* Starting Lineup */}
            <SectionHeader label="Starting Lineup" filledCount={filledLineupCards.length} total={lineupPts} kpis={lineupKpis} />
            {FIELD_POSITIONS.map(pos => {
                const slot = slotByPos[pos] ?? null;
                const card = slot ? cardMap[slot.card_id] : null;
                return (
                    <PositionRow
                        key={pos}
                        label={pos}
                        card={card}
                        onClick={() => onSlotClick(pos, slot)}
                        onDetailClick={card ? () => setDetailCard(card) : undefined}
                        readOnly={readOnly}
                        isActive={activePosition === pos}
                    />
                );
            })}

            {/* Bench */}
            <SectionHeader label="Bench" filledCount={filledBenchCards.length} total={benchPts} kpis={benchKpis} />
            {BENCH_ROLES.map(pos => {
                const slot = benchByRole[pos] ?? null;
                const card = slot ? cardMap[slot.card_id] : null;
                return (
                    <PositionRow
                        key={pos}
                        label={pos}
                        card={card}
                        onClick={() => onBenchClick(pos, slot)}
                        onDetailClick={card ? () => setDetailCard(card) : undefined}
                        readOnly={readOnly}
                        isActive={activeRole === pos}
                    />
                );
            })}

            {/* Rotation */}
            <SectionHeader label="Rotation" filledCount={filledRotCards.length} total={rotationPts} kpis={rotationKpis} />
            {ACTIVE_ROTATION_ROLES.map(role => {
                const assignment = roleByKey[role] ?? null;
                const card = assignment ? cardMap[assignment.card_id] : null;
                return (
                    <PositionRow
                        key={role}
                        label={role}
                        card={card}
                        onClick={() => onRoleClick(role, assignment)}
                        onDetailClick={card ? () => setDetailCard(card) : undefined}
                        readOnly={readOnly}
                        isActive={activeRole === role}
                    />
                );
            })}

            {/* Bullpen */}
            <SectionHeader label="Bullpen" filledCount={filledBullCards.length} total={bullpenPts} kpis={bullpenKpis} />
            {BULLPEN_ROLES.map((role, i) => {
                const assignment = bullpenByRole[role] ?? null;
                const actualRole = bullpenSlots[i]?.role ?? role;
                const card = assignment ? cardMap[assignment.card_id] : null;
                return (
                    <PositionRow
                        key={role}
                        label={actualRole}
                        card={card}
                        onClick={() => onRoleClick(actualRole, assignment)}
                        onDetailClick={card ? () => setDetailCard(card) : undefined}
                        readOnly={readOnly}
                        isActive={activeRole === actualRole}
                    />
                );
            })}

            {detailCard && (
                <Modal onClose={() => setDetailCard(null)} size="lg">
                    <CardDetail cardId={detailCard.card_id} context="roster" />
                </Modal>
            )}
        </div>
    );
}
