import type { SimStatLine } from '../../../api/sim';
import { DiffBadge } from './DiffIndicator';
import { SectionCard } from './SectionCard';
import { COLUMN_LABELS, computeDiff, formatStat, HITTER_COMPARISON_COLUMNS, LOWER_IS_BETTER_KEYS, PITCHER_COMPARISON_COLUMNS } from './simStatColumns';

/** Mirrors `_stats_table`'s `is_diff_a_pct` branch (`reporting.py`): signed % delta between sim
 * and real, fed into `computeDiff` so the DIFF row renders as a colored up/down arrow. Flat inside
 * +/-0.1% avoids a noisy arrow on an effectively-tied value. Every key here is either
 * hitter-only or pitcher-only (`HITTER_COMPARISON_COLUMNS`/`PITCHER_COMPARISON_COLUMNS` don't
 * overlap), so the key alone is enough to know whether lower is better - no player-type context
 * needed the way `ops_diff` on a mixed outlier table does. */
function diffPct(key: string, sim: number, real: number) {
    const denominator = real > 0 ? real : 1;
    const pct = ((sim - real) / denominator) * 100;
    return computeDiff(pct, { lowerIsBetter: LOWER_IS_BETTER_KEYS.has(key), flatThreshold: 0.1 });
}

function ComparisonTable({ label, columns, sim, real }: { label: string; columns: string[]; sim: SimStatLine; real: SimStatLine }) {
    return (
        <div>
            <p className="text-[11px] font-semibold text-(--text-tertiary) mb-1">{label}</p>
            <div className="overflow-x-auto">
                <table className="w-full text-[12px] whitespace-nowrap">
                    <thead>
                        <tr className="text-(--text-tertiary) border-b border-(--divider)">
                            <th className="text-left font-semibold py-2 pr-3" />
                            {columns.map(key => (
                                <th key={key} className="text-right font-semibold py-2 px-2">{COLUMN_LABELS[key] ?? key.toUpperCase()}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        <tr className="border-b border-(--divider)/50">
                            <td className="py-1.5 pr-3 font-bold text-(--text-primary)">SIM</td>
                            {columns.map(key => (
                                <td key={key} className="text-right py-1.5 px-2 tabular-nums text-(--text-secondary)">{formatStat(key, sim.stats[key])}</td>
                            ))}
                        </tr>
                        <tr className="border-b border-(--divider)/50">
                            <td className="py-1.5 pr-3 font-bold text-(--text-primary)">REAL</td>
                            {columns.map(key => (
                                <td key={key} className="text-right py-1.5 px-2 tabular-nums text-(--text-secondary)">{formatStat(key, real.stats[key])}</td>
                            ))}
                        </tr>
                        <tr className="bg-(--showdown-blue)/10">
                            <td className="py-1.5 pr-3 font-semibold text-(--text-tertiary)">DIFF</td>
                            {columns.map(key => (
                                <td key={key} className="text-right py-1.5 px-2 tabular-nums">
                                    <DiffBadge diff={diffPct(key, sim.stats[key] ?? 0, real.stats[key] ?? 0)} format={abs => `${abs.toFixed(1)}%`} />
                                </td>
                            ))}
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

type Props = {
    leagueTotals: Record<string, SimStatLine>;
    realLeagueAverages: Record<string, SimStatLine>;
};

/**
 * League-wide SIM vs. REAL average stat lines — the web equivalent of the CLI's
 * `--show_real_life_comparison`. Sourced entirely from data `SeasonSimSummary` already ships
 * (`league_totals`/`real_league_averages`), so this is presentation-only, no new backend field.
 */
export function SimRealLifeComparison({ leagueTotals, realLeagueAverages }: Props) {
    const hitterSim = leagueTotals['Hitter'];
    const hitterReal = realLeagueAverages['Hitter'];
    const pitcherSim = leagueTotals['Pitcher'];
    const pitcherReal = realLeagueAverages['Pitcher'];
    if (!hitterReal && !pitcherReal) return null;

    return (
        <SectionCard
            title="Sim vs. Real Life"
            info="Sim stats won't always match real life exactly. Showdown Bot balances realism with staying true to what the original WOTC cards play like, so some drift from the real-world numbers is expected. For example 2004/2005 set hitting will be slightly better than real life."
        >
            <div className="flex flex-col gap-3">
                {hitterSim && hitterReal && <ComparisonTable label="Hitters" columns={HITTER_COMPARISON_COLUMNS} sim={hitterSim} real={hitterReal} />}
                {pitcherSim && pitcherReal && <ComparisonTable label="Pitchers" columns={PITCHER_COMPARISON_COLUMNS} sim={pitcherSim} real={pitcherReal} />}
            </div>
        </SectionCard>
    );
}
