import { useMemo, useState } from 'react';
import { FaArrowRight } from 'react-icons/fa6';
import type { SeasonSimSummary, SimOffseasonMove } from '../../../api/sim';
import { TeamChip } from '../../shared/TeamChip';
import { Plate } from '../../shared/Plate';
import { choiceClass } from '../../shared/choiceStyles';
import { fromSimTeamIdentity, fallbackIdentity } from '../../../domain/adapters/fromSim';
import { useIdentity } from './simStandings';
import { SectionCard } from './SectionCard';
import { DiffBadge } from './DiffIndicator';
import { COLUMN_LABELS, LOWER_IS_BETTER_KEYS, computeDiff, formatStat } from './simStatColumns';

// Stats that read the same without league context (the real line has none, so no OPS+/wRC+).
const HITTER_MOVE_COLUMNS = ['pa', 'ba', 'obp', 'slg', 'ops', 'hr', 'rbi', 'sb'];
const PITCHER_MOVE_COLUMNS = ['ip', 'era', 'whip', 'so9', 'hr', 'wins', 'sv'];
// Rate stats get an arrow against last season; counting stats don't, since a partial or shortened
// sim (or a different role) makes their totals incomparable. Value: the gap that reads as unchanged.
const RATE_FLAT_THRESHOLD: Record<string, number> = { ba: 0.002, obp: 0.002, slg: 0.002, ops: 0.002, era: 0.05, whip: 0.01, so9: 0.1 };

type Scope = 'club' | 'league';

type Props = {
    summary: SeasonSimSummary;
    /** Schedule key the result screen is focused on. */
    teamKey: string;
};

/** Playing time, so the regulars lead each table. */
function volume(move: SimOffseasonMove, isPitcher: boolean): number {
    return move.sim?.stats[isPitcher ? 'ip' : 'pa'] ?? -1;
}

function columnLabel(key: string): string {
    return COLUMN_LABELS[key] ?? (key === 'ba' ? 'AVG' : key === 'so9' ? 'K/9' : key.toUpperCase());
}

/**
 * How the offseason's movers played in this sim: every player who started on a new club (a real
 * trade or signing, or a free agent this run placed), with each stat's change from his real line
 * last season as a green/red arrow on each rate stat. Scoped to the focus club's moves in and out, or the whole league.
 */
export function SimOffseasonMovesTab({ summary, teamKey }: Props) {
    const identityFor = useIdentity(summary);
    const [scope, setScope] = useState<Scope>('club');

    const moves = useMemo(() => {
        const all = summary.offseason_moves ?? [];
        return scope === 'league' ? all : all.filter(move => move.to_team === teamKey || move.from_team === teamKey);
    }, [summary.offseason_moves, scope, teamKey]);

    const teamChip = (key: string | null) => {
        if (!key) return <span className="text-(--text-tertiary)">—</span>;
        const identity = identityFor(key);
        return <TeamChip team={identity ? fromSimTeamIdentity(identity) : fallbackIdentity(key)} size="sm" />;
    };

    const renderTable = (isPitcher: boolean) => {
        const rows = moves
            .filter(move => (move.player_type === 'Pitcher') === isPitcher)
            .sort((a, b) => volume(b, isPitcher) - volume(a, isPitcher));
        const columns = isPitcher ? PITCHER_MOVE_COLUMNS : HITTER_MOVE_COLUMNS;
        return (
            <SectionCard
                title={isPitcher ? 'Pitchers' : 'Hitters'}
                count={rows.length || undefined}
                info="Each stat is this sim's line. Arrows compare rate stats with the player's real line from the season his card is built on; hover any stat for the real value."
            >
                {rows.length > 0 ? (
                    <div className="overflow-x-auto scrollbar-hide">
                        <table className="w-full text-[12px] whitespace-nowrap">
                            <thead>
                                <tr className="text-(--text-tertiary) border-b border-(--divider)">
                                    <th className="text-left font-semibold py-2 pr-3">Player</th>
                                    <th className="text-left font-semibold py-2 pr-3">Move</th>
                                    {columns.map(key => (
                                        <th key={key} className="text-right font-semibold py-2 px-2">{columnLabel(key)}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {rows.map(move => (
                                    <tr key={`${move.player_id}-${move.to_team}`} className="border-b border-(--divider)/50 align-top">
                                        <td className="py-1.5 pr-3">
                                            <div className="flex items-center gap-1.5">
                                                <span className="font-bold text-(--text-primary)">{move.player_name}</span>
                                                {move.position && <span className="text-(--text-tertiary)">{move.position}</span>}
                                            </div>
                                            {move.is_sim_signing && <Plate size="xs" variant="outline" className="mt-1">Sim signing</Plate>}
                                        </td>
                                        <td className="py-1.5 pr-3">
                                            <span className="inline-flex items-center gap-1.5">
                                                {teamChip(move.from_team)}
                                                <FaArrowRight className="text-[9px] text-(--text-tertiary)" />
                                                {teamChip(move.to_team)}
                                            </span>
                                        </td>
                                        {move.sim ? columns.map(key => {
                                            const simValue = move.sim?.stats[key];
                                            const realValue = move.real?.stats[key];
                                            const flatThreshold = RATE_FLAT_THRESHOLD[key];
                                            const diff = flatThreshold !== undefined && simValue !== undefined && realValue !== undefined
                                                ? computeDiff(simValue - realValue, { lowerIsBetter: LOWER_IS_BETTER_KEYS.has(key), flatThreshold })
                                                : null;
                                            return (
                                                <td key={key} className="py-1.5 px-2 text-right tabular-nums" title={realValue !== undefined ? `Real: ${formatStat(key, realValue)}` : undefined}>
                                                    <div className="text-(--text-primary)">{formatStat(key, simValue)}</div>
                                                    {diff && <div className="text-[10px]"><DiffBadge diff={diff} format={magnitude => formatStat(key, magnitude)} /></div>}
                                                </td>
                                            );
                                        }) : (
                                            <td colSpan={columns.length} className="py-1.5 px-2 text-right text-(--text-tertiary)">Didn't play</td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-[13px] text-(--text-tertiary) py-1">
                        No {isPitcher ? 'pitchers' : 'hitters'} moved {scope === 'club' ? 'to or from this club' : 'this offseason'}.
                    </p>
                )}
            </SectionCard>
        );
    };

    return (
        <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
                <button type="button" onClick={() => setScope('club')} className={choiceClass(scope === 'club', 'sm')}>This club</button>
                <button type="button" onClick={() => setScope('league')} className={choiceClass(scope === 'league', 'sm')}>All clubs</button>
            </div>
            {renderTable(false)}
            {renderTable(true)}
        </div>
    );
}
