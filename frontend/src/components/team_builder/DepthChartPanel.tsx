import type { Team, LineupSlot, PitcherAssignment, TeamRosterSlot } from '../../api/userTeams';
import type { ShowdownBotCardCompact } from '../../api/showdownBotCard';
import { CardItemCompact } from '../cards/CardItemCompact';
import { FaPlus } from 'react-icons/fa6';

const FIELD_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'] as const;
const ROTATION_ROLES  = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5'] as const;

type DepthChartPanelProps = {
    team: Team;
    cardMap: Record<string, ShowdownBotCardCompact | null>;
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
    readOnly,
    isActive,
}: {
    label: string;
    card: ShowdownBotCardCompact | null | undefined;
    onClick: () => void;
    readOnly: boolean;
    isActive?: boolean;
}) {
    return (
        <div className={`flex items-center gap-3 min-h-9 rounded-lg transition-all duration-200 ${isActive ? 'ring-1 ring-(--secondary) shadow-[0_0_8px_2px_color-mix(in_srgb,var(--secondary)_40%,transparent)] animate-pulse px-1 -mx-1' : ''}`} onClick={e => e.stopPropagation()}>
            <span className={`text-[11px] font-bold w-10 shrink-0 text-right ${isActive ? 'text-(--secondary)' : 'text-(--text-tertiary)'}`}>{label}</span>
            {card ? (
                <div className="flex-1 min-w-0" onClick={readOnly ? undefined : onClick}>
                    <CardItemCompact card={card} isSelected={isActive} />
                </div>
            ) : (
                <button
                    type="button"
                    onClick={onClick}
                    disabled={readOnly}
                    className={`flex-1 flex items-center gap-1.5 px-3 h-9 rounded-lg border border-dashed
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

function SectionHeader({ label }: { label: string }) {
    return (
        <div className="text-[10px] font-semibold text-(--text-secondary) uppercase tracking-widest pt-3 pb-1">
            {label}
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
    const lineup = team.lineups[0] ?? { name: 'Default', slots: [] };
    const slotByPos = Object.fromEntries(lineup.slots.map(s => [s.field_position, s]));
    const roleByKey = Object.fromEntries(team.rotation.map(r => [r.role, r]));

    const BENCH_ROLES = ["BE1", "BE2", "BE3", "BE4", "BE5",].slice(0, team.min_bench);
    const benchByRole = Object.fromEntries(
        team.roster
            .filter(s => BENCH_ROLES.includes(s.roster_position.toUpperCase()))
            .map(s => [s.roster_position.toUpperCase(), s])
    );

    const BULLPEN_ROLES = ["RP1", "RP2", "RP3", "RP4", "RP5",].slice(0, team.min_bullpen);

    return (
        <div className="flex flex-col gap-0.5 p-4">
            {/* Starting Lineup */}
            <SectionHeader label="Starting Lineup" />
            {FIELD_POSITIONS.map(pos => {
                const slot = slotByPos[pos] ?? null;
                return (
                    <PositionRow
                        key={pos}
                        label={pos}
                        card={slot ? cardMap[slot.card_id] : null}
                        onClick={() => onSlotClick(pos, slot)}
                        readOnly={readOnly}
                        isActive={activePosition === pos}
                    />
                );
            })}

            {/* Bench */}
            <SectionHeader label="Bench" />
            {BENCH_ROLES.map(pos => {
                const slot = benchByRole[pos] ?? null;
                return (
                    <PositionRow
                        key={pos}
                        label={pos}
                        card={slot ? cardMap[slot.card_id] : null}
                        onClick={() => onBenchClick(pos, slot)}
                        readOnly={readOnly}
                        isActive={activeRole === pos}
                    />
                );
            })}

            {/* Rotation */}
            <SectionHeader label="Rotation" />
            {ROTATION_ROLES.map(role => {
                const assignment = roleByKey[role] ?? null;
                return (
                    <PositionRow
                        key={role}
                        label={role}
                        card={assignment ? cardMap[assignment.card_id] : null}
                        onClick={() => onRoleClick(role, assignment)}
                        readOnly={readOnly}
                        isActive={activeRole === role}
                    />
                );
            })}

            {/* Bullpen */}
            <SectionHeader label="Bullpen" />
            {BULLPEN_ROLES.map(role => {
                const assignment = roleByKey[role] ?? null;
                return (
                    <PositionRow
                        key={role}
                        label={role}
                        card={assignment ? cardMap[assignment.card_id] : null}
                        onClick={() => onRoleClick(role, assignment)}
                        readOnly={readOnly}
                        isActive={activeRole === role}
                    />
                );
            })}
        </div>
    );
}
