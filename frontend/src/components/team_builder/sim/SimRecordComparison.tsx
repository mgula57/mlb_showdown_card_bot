import type { SeasonSimSummary } from '../../../api/sim';
import { DiffBadge } from './DiffIndicator';
import { SectionCard } from './SectionCard';
import { useRecordComparison, type RecordComparisonEntry } from './simStandings';
import { computeDiff } from './simStatColumns';

/** Batting-average-style formatting for a win% delta's magnitude, e.g. `.087`. */
function formatWinPctDiff(abs: number): string {
    return abs.toFixed(3).replace(/^0/, '');
}

function RecordTable({ entries, focusAbbr }: { entries: RecordComparisonEntry[]; focusAbbr: string }) {
    return (
        <div className="overflow-x-auto rounded-xl border border-(--divider)">
            <table className="w-full text-[12px] whitespace-nowrap">
                <thead>
                    <tr className="text-(--text-tertiary) border-b border-(--divider)">
                        <th className="text-left font-semibold py-2 pl-3 pr-3">Team</th>
                        <th className="text-right font-semibold py-2 px-2">Real</th>
                        <th className="text-right font-semibold py-2 px-2">Sim</th>
                        <th className="text-right font-semibold py-2 px-2 pr-3">Diff</th>
                    </tr>
                </thead>
                <tbody>
                    {entries.map(entry => (
                        <tr key={entry.abbr} className={`border-b border-(--divider)/50 ${entry.abbr === focusAbbr ? 'bg-(--showdown-blue)/10 font-bold' : ''}`}>
                            <td className="py-1.5 pl-3 pr-3 text-left text-(--text-primary)">{entry.identity?.abbreviation ?? entry.abbr}</td>
                            <td className="text-right py-1.5 px-2 tabular-nums text-(--text-secondary)">{entry.realWins}-{entry.realLosses}</td>
                            <td className="text-right py-1.5 px-2 tabular-nums text-(--text-secondary)">{entry.simWins}-{entry.simLosses}</td>
                            <td className="text-right py-1.5 px-2 pr-3 tabular-nums">
                                <DiffBadge diff={computeDiff('win_pct', entry.diff)} format={formatWinPctDiff} />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

type Props = {
    summary: SeasonSimSummary;
    /** The viewer's own club - its row is highlighted when it lands in either list. */
    focusAbbr: string;
};

/**
 * Team-level counterpart to `SimOutliers`: which clubs' simulated record diverged most from what
 * they actually did in real life that season, split into over/underperformers by win% delta.
 */
export function SimRecordComparison({ summary, focusAbbr }: Props) {
    const { overperformers, underperformers, loading } = useRecordComparison(summary);
    if (loading || (overperformers.length === 0 && underperformers.length === 0)) return null;

    return (
        <SectionCard title="Team Records: Sim vs. Real Life">
            <div className="flex flex-col lg:flex-row gap-4">
                {overperformers.length > 0 && (
                    <div className='lg:w-1/2'>
                        <p className="text-[11px] font-bold text-(--success) uppercase tracking-wide mb-1.5">Overperformed Real Life</p>
                        <RecordTable entries={overperformers} focusAbbr={focusAbbr} />
                    </div>
                )}
                {underperformers.length > 0 && (
                    <div className='lg:w-1/2'>
                        <p className="text-[11px] font-bold text-(--error) uppercase tracking-wide mb-1.5">Underperformed Real Life</p>
                        <RecordTable entries={underperformers} focusAbbr={focusAbbr} />
                    </div>
                )}
            </div>
        </SectionCard>
    );
}
