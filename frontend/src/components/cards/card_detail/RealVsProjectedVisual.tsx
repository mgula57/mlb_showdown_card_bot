import { useState, useEffect } from 'react';
import { type RealVsProjectedStat } from '../../../api/showdownBotCard';
import { formatStatValue } from '../../../functions/formatters';

type StatRanges = Record<string, { min: number; max: number }>;

type RealVsProjectedVisualProps = {
    realVsProjectedData?: RealVsProjectedStat[];
    statRanges?: StatRanges | null;
    isLoading?: boolean;
    playerType?: 'HITTER' | 'PITCHER';
};

// Maps display stat names to stat_ranges keys
const STAT_TO_RANGE_KEY: Record<string, string> = {
    'BA':           'batting_avg',
    'OBP':          'onbase_perc',
    'SLG':          'slugging_perc',
    'OPS':          'onbase_plus_slugging',
    'OPS+':         'onbase_plus_slugging_plus',
    'wRC+':         'wRcPlus',
    'SPRINT SPEED': 'sprint_speed',
};

function rangeKey(stat: string): string {
    return STAT_TO_RANGE_KEY[stat] ?? stat;
}

function percentileColor(p: number): string {
    if (p >= 80) return 'rgb(220,38,38)';
    if (p >= 60) return 'rgb(249,115,22)';
    if (p >= 40) return 'rgb(148,163,184)';
    if (p >= 20) return 'rgb(100,116,139)';
    return 'rgb(59,130,246)';
}

function diffColor(diffStr: string): string {
    if (!diffStr || diffStr === '0' || diffStr === '+0') return 'opacity-40';
    return diffStr.startsWith('+') ? 'text-green-500' : 'text-red-500';
}

const GHOST_COLOR = 'rgb(148,163,184)';

// Stats where a lower value is better, keyed by player type
const INVERTED_STATS: Record<'HITTER' | 'PITCHER', Set<string>> = {
    HITTER:  new Set(['SO']),
    PITCHER: new Set(['BB', 'ERA', 'WHIP']),
};

function PercentileBar({ stat, real, statRanges, hasRanges, playerType, className }: { stat: string; real: number | null; statRanges: StatRanges; hasRanges: boolean; playerType?: 'HITTER' | 'PITCHER'; className?: string }) {
    // Compute target pct unconditionally so hooks are always called in the same order
    const key = rangeKey(stat);
    const range = (real !== null && real !== undefined) ? statRanges[key] : undefined;
    const hasValidRange = !!range && range.max !== range.min;

    const isInverted = !!playerType && INVERTED_STATS[playerType].has(stat);
    const rawPct = hasValidRange
        ? Math.round(Math.max(0, Math.min(100, ((real as number) - range!.min) / (range!.max - range!.min) * 100)))
        : 0;
    const targetPct = isInverted ? 100 - rawPct : rawPct;

    const [animatedPct, setAnimatedPct] = useState(0);

    useEffect(() => {
        if (!hasValidRange) return;
        if (animatedPct === targetPct) return; // No animation if value is unchanged
        const frame = requestAnimationFrame(() => setAnimatedPct(targetPct));
        return () => cancelAnimationFrame(frame);
    }, [targetPct, hasValidRange]);

    // Early returns after all hooks
    if (real === null || real === undefined) return <div className="flex-1" />;
    if (!hasValidRange) {
        if (!hasRanges) return (
            <div className={`flex-1 relative h-5 flex items-center opacity-25 ${className || ''}`}>
                <div className="absolute inset-x-0 h-1 rounded-full" style={{ backgroundColor: GHOST_COLOR }} />
                <div className="absolute h-4.5 w-4.5 rounded-full flex items-center justify-center text-[8px] font-black text-white" style={{ left: '-2px', backgroundColor: GHOST_COLOR }}>
                    0
                </div>
            </div>
        );
        return <div className={`flex-1 h-1 rounded-full opacity-10 ${className || ''}`} style={{ background: 'var(--form-element)' }} />;
    }

    const color = percentileColor(targetPct);
    const badgeOffset = Math.max(0, Math.min(animatedPct, 96));

    return (
        <div className={`flex-1 relative h-5 flex items-center ${className || ''}`}>
            {/* Track */}
            <div className="absolute inset-x-0 h-1 rounded-full opacity-20" style={{ backgroundColor: color }} />
            {/* Fill */}
            <div
                className="absolute left-0 h-1 rounded-full transition-all duration-700"
                style={{ width: `${animatedPct}%`, backgroundColor: color }}
            />
            {/* Badge */}
            <div
                className={`
                    absolute h-5 w-5 rounded-full flex items-center justify-center 
                    font-extrabold text-white ${targetPct.toString().length > 2 ? 'text-[8px]' : 'text-[10px]'}
                    transition-all duration-700 cursor-default group
                `}
                style={{ left: `calc(${badgeOffset}%)`, backgroundColor: color }}
            >
                {targetPct}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:flex flex-col items-center pointer-events-none z-10">
                    <div className="rounded px-2 py-1 text-[9px] font-semibold text-white whitespace-nowrap shadow-lg" style={{ backgroundColor: color }}>
                        <div className="font-black">{targetPct}th percentile</div>
                        <div className="opacity-80">Min {formatStatValue(range!.min, stat)} · Max {formatStatValue(range!.max, stat)}</div>
                    </div>
                    <div className="w-1.5 h-1.5 rotate-45 -mt-1" style={{ backgroundColor: color }} />
                </div>
            </div>
        </div>
    );
}

const PLACEHOLDER_STATS = [
    { stat: 'BA',  real: 0.274, projected: 0.268, diff: -0.006, diff_str: '-.006', precision: 3 },
    { stat: 'OBP', real: 0.351, projected: 0.344, diff: -0.007, diff_str: '-.007', precision: 3 },
    { stat: 'SLG', real: 0.489, projected: 0.501, diff:  0.012, diff_str: '+.012', precision: 3 },
    { stat: 'OPS', real: 0.840, projected: 0.845, diff:  0.005, diff_str: '+.005', precision: 3 },
    { stat: 'OPS+',real: 135,   projected: 140,   diff:  5,     diff_str: '+5',    precision: 0 },
    { stat: 'PA',  real: 582,   projected: 582,   diff:  0,     diff_str: '+0',    precision: 0 },
    { stat: 'AB',  real: 480,   projected: 480,   diff:  0,     diff_str: '+0',    precision: 0 },
    { stat: '1B',  real: 10,    projected:  10,   diff:  0,     diff_str: '+0',    precision: 0 },
    { stat: '2B',  real: 10,    projected:  10,   diff:  0,     diff_str: '+0',    precision: 0 },
    { stat: '3B',  real: 10,    projected:  10,   diff:  0,     diff_str: '+0',    precision: 0 },
    { stat: 'HR',  real: 27,    projected: 29,    diff:  2,     diff_str: '+2',    precision: 0 },
    { stat: 'BB',  real: 61,    projected: 58,    diff: -3,     diff_str: '-3',    precision: 0 },
    { stat: 'SO',  real: 114,   projected: 118,   diff:  4,     diff_str: '+4',    precision: 0 },
    { stat: 'SB',  real: 15,    projected: 18,    diff:  3,     diff_str: '+3',    precision: 0 },
    { stat: 'SPRINT SPEED', real: 28.5, projected: 28.0, diff: -0.5, diff_str: '-0.5', precision: 1 },
    { stat: 'WAR', real: 5.2, projected: 5.0, diff: -0.2, diff_str: '-0.2', precision: 1 },
] as RealVsProjectedStat[];

export default function RealVsProjectedVisual({ realVsProjectedData, statRanges, isLoading, playerType }: RealVsProjectedVisualProps) {
    const isEmpty = !realVsProjectedData?.length;
    const data = isEmpty ? PLACEHOLDER_STATS : realVsProjectedData!.filter(stat => !['GB', 'FB', 'PU', 'SF'].includes(stat.stat)); // these adjusted metrics are less intuitive to interpret without context, so exclude from visual

    return (
        <div className={`space-y-2 ${isEmpty ? 'opacity-25 pointer-events-none select-none' : ''}`}>
            {/* Header */}
            <div className="flex items-center gap-2 text-[9px] font-semibold uppercase tracking-widest opacity-40 mb-0.5">
                <span className="w-14 shrink-0">Stat</span>
                <span className="w-12 shrink-0 text-right">Card</span>
                <span className="w-12 shrink-0 text-right">Real</span>
                <span className="flex-1 text-center">Percentile</span>
                <span className="w-12 shrink-0 text-right">Diff</span>
            </div>

            {data.map((stat) => {
                const cleanStat = stat.stat.replace(/\*+/g, '');
                const suffix = stat.is_real_estimated ? ' *' : stat.is_projected_correction ? '**' : '';

                return (
                    <div key={stat.stat} className="flex items-center gap-2">
                        <span className="text-[12px] font-bold w-14 shrink-0 opacity-70 leading-tight">
                            {cleanStat}{suffix && <span className="text-[9px] opacity-50">{suffix}</span>}
                        </span>
                        <span className={`text-[12px] font-black w-12 shrink-0 text-right tabular-nums ${isEmpty ? 'blur-xs' : ''}`}>
                            {formatStatValue(stat.projected, cleanStat)}
                        </span>
                        <span className={`text-[12px] font-semibold w-12 shrink-0 text-right tabular-nums opacity-60 ${isEmpty ? 'blur-xs' : ''}`}>
                            {formatStatValue(stat.real, cleanStat)}
                        </span>

                        <PercentileBar className="py-2" stat={cleanStat} real={stat.real} statRanges={statRanges || {}} hasRanges={!!statRanges} playerType={playerType} />

                        <span className={`text-[12px] font-bold w-14 shrink-0 text-right tabular-nums ${isEmpty ? 'blur-xs' : diffColor(stat.diff_str)}`}>
                            {stat.diff_str}
                        </span>
                    </div>
                );
            })}
        </div>
    );
}
