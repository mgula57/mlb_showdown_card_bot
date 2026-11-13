import { type StatNormalizerSummary } from '../../../api/showdownBotCard';
import { formatAsPct, formatStatValue } from '../../../functions/formatters';
import { CAPS_LABEL_CLASS } from '../../shared/fieldStyles';

type StatNormalizerBreakdownProps = {
    summary: StatNormalizerSummary;
    playerType?: 'HITTER' | 'PITCHER';
};

/** "2023-2025" for consecutive seasons, otherwise a comma list ("2021, 2023") */
function formatYears(years?: number[] | null): string | null {
    if (!years?.length) return null;
    if (years.length === 1) return String(years[0]);
    const isConsecutive = years.every((year, i) => i === 0 || year === years[i - 1] + 1);
    return isConsecutive ? `${years[0]}–${years[years.length - 1]}` : years.join(', ');
}

function formatRate(value: number, stat: string): string {
    return stat === 'K%' ? formatAsPct(value) : formatStatValue(value, stat);
}

/**
 * StatNormalizerBreakdown - How much of a normalized card came from the player's real sample vs
 * the normalizer's baseline: a split bar of the two shares, then each rate stat for the real
 * sample, the baseline, and the blend the card was built from.
 */
export default function StatNormalizerBreakdown({ summary, playerType }: StatNormalizerBreakdownProps) {
    const realPct = Math.round(summary.real_weight * 100);
    const isFullSample = realPct >= 100;
    const years = formatYears(summary.baseline_years);

    return (
        <div className="space-y-3">
            {/* Real vs baseline share */}
            <div className="space-y-1">
                <div className="flex h-2 rounded-plate overflow-hidden bg-(--background-tertiary)">
                    <div className="bg-(--showdown-blue-fill)" style={{ width: `${realPct}%` }} />
                </div>
                <div className={`flex justify-between gap-3 ${CAPS_LABEL_CLASS}`}>
                    <span className="text-(--showdown-blue) tabular-nums">
                        {realPct}% Real
                        <span className="normal-case font-normal text-(--text-tertiary)"> ({Math.round(summary.real_pa)} of {Math.round(summary.full_sample_pa)} PA)</span>
                    </span>
                    <span className="text-(--text-secondary) tabular-nums text-right">
                        {100 - realPct}% {summary.label}
                        {years && <span className="normal-case font-normal text-(--text-tertiary)"> ({years})</span>}
                    </span>
                </div>
            </div>

            {isFullSample ? (
                <div className="text-xs text-(--text-tertiary)">Full sample. Real stats are used as-is.</div>
            ) : (
                <div className="space-y-1">
                    <div className={`flex items-center gap-2 ${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>
                        <span className="w-14 shrink-0">Stat</span>
                        <span className="flex-1 text-right">Real</span>
                        <span className="flex-1 text-right">Baseline</span>
                        <span className="flex-1 text-right">Card Uses</span>
                    </div>
                    {summary.stats.map(({ stat, real, baseline, blended }) => (
                        <div key={stat} className="flex items-center gap-2 text-[12px] tabular-nums">
                            <span className="w-14 shrink-0 font-bold opacity-70">{stat}</span>
                            <span className="flex-1 text-right font-semibold opacity-60">{formatRate(real, stat)}</span>
                            <span className="flex-1 text-right font-semibold opacity-60">{formatRate(baseline, stat)}</span>
                            <span className="flex-1 text-right font-bold">{formatRate(blended, stat)}</span>
                        </div>
                    ))}
                    {playerType === 'PITCHER' && (
                        <div className="text-[10px] opacity-40 pt-1">
                            <i>Rates are against. Baseline WHIP uses his real batters faced per inning.</i>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
