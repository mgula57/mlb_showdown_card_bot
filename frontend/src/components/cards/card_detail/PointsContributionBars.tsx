import { type PointsBreakdown, type PointsCategoryBreakdown } from '../../../api/showdownBotCard';
import { formatStatValue } from '../../../functions/formatters';

const METRIC_ALIAS: Record<string, string> = {
    "AVERAGE": "BA*",
    "ONBASE": "OBP*",
    "SLUGGING": "SLG*",
    "HOME_RUNS": "HR*",
    "SPEED": "SPD",
    "DEFENSE-CLOSER": "CL BONUS",
    "OUT_DISTRIBUTION": "OUT DIST",
};

const SKIP_METRICS = new Set(['DECAY', 'IPx', 'TOTAL']);

const PLACEHOLDER_BREAKDOWN: PointsBreakdown = {
    allow_negatives: false,
    command_out_multiplier: 1.0,
    decay_rate: 1.0,
    decay_start: 0,
    ip_multiplier: 1.0,
    breakdowns: {
        AVERAGE:          { metric: 'AVERAGE',          value: 0.274, points: 15, percentile: 0.72 },
        ONBASE:           { metric: 'ONBASE',           value: 0.351, points: 12, percentile: 0.65 },
        SLUGGING:         { metric: 'SLUGGING',         value: 0.489, points: 18, percentile: 0.81 },
        HOME_RUNS:        { metric: 'HOME_RUNS',        value: 27,    points: 20, percentile: 0.88 },
        SPEED:            { metric: 'SPEED',            value: 15,    points: 5,  percentile: 0.45 },
        OUT_DISTRIBUTION: { metric: 'OUT_DISTRIBUTION', value: 0.62,  points: 8,  percentile: 0.55 },
    },
};

function percentileColor(pct: number | null | undefined): string {
    if (pct == null) return 'rgb(156,163,175)';
    if (pct >= 0.75) return '#22c55e';
    if (pct >= 0.50) return '#84cc16';
    if (pct >= 0.25) return '#eab308';
    return '#ef4444';
}

type PointsContributionBarsProps = {
    pointsBreakdownData?: PointsBreakdown | null;
    ip?: number | null;
};

export default function PointsContributionBars({ pointsBreakdownData, ip }: PointsContributionBarsProps) {
    const isEmpty = !pointsBreakdownData;
    const data = isEmpty ? PLACEHOLDER_BREAKDOWN : pointsBreakdownData!;

    const rows: (PointsCategoryBreakdown & { metric: string })[] = Object.entries(data.breakdowns || {})
        .map(([key, bd]) => ({ ...bd, metric: key }))
        .filter(bd => !SKIP_METRICS.has(bd.metric))
        .sort((a, b) => b.points - a.points);

    if (rows.length === 0) return null;

    const maxPoints = Math.max(...rows.map(r => Math.abs(r.points)), 1);

    const specialRows: { label: string; display: string }[] = [];
    const ipMultiplier = data.ip_multiplier || 1.0;
    if (ipMultiplier !== 1.0) {
        specialRows.push({ label: 'IPx', display: `IP ${ip ?? '—'}  ×${ipMultiplier}` });
    }
    const decayRate = data.decay_rate || 1.0;
    if (decayRate !== 1.0) {
        specialRows.push({ label: 'DECAY', display: `${decayRate}x (from ${data.decay_start})` });
    }

    const totalPoints = rows.reduce((sum, r) => sum + (r.points || 0), 0);

    return (
        <div className={`space-y-1.5 ${isEmpty ? 'opacity-25 pointer-events-none select-none' : ''}`}>
            {rows.map(bd => {
                const label = bd.metric.includes('DEFENSE') && !bd.metric.includes('CLOSER')
                    ? bd.metric.replace('DEFENSE', 'DEF')
                    : (METRIC_ALIAS[bd.metric] || bd.metric);
                const barPct = (Math.abs(bd.points) / maxPoints) * 100;
                const color = percentileColor(bd.percentile);

                return (
                    <div key={bd.metric} className="flex items-center gap-2.5">
                        <span className="text-sm font-bold w-20 shrink-0 opacity-70 truncate">{label}</span>
                        <span className={`text-sm font-medium w-14 shrink-0 opacity-70 truncate ${isEmpty ? 'blur-xs' : ''}`}>
                            {formatStatValue(bd.value, bd.metric)}
                        </span>
                        <div className="relative flex-1 h-3 rounded-full overflow-hidden" style={{ background: 'color-mix(in srgb, var(--form-element) 30%, transparent)' }}>
                            <div
                                className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                                style={{ width: `${barPct}%`, backgroundColor: color, opacity: 0.8 }}
                            />
                        </div>
                        <span className={`text-sm font-semibold w-16 shrink-0 text-right tabular-nums opacity-70 ${isEmpty ? 'blur-xs' : ''}`}>
                            {bd.points > 0 ? '+' : ''}{Math.round(bd.points)} pts
                        </span>
                    </div>
                );
            })}

            {specialRows.map(row => (
                <div key={row.label} className="flex items-center gap-2.5 opacity-50">
                    <span className="text-sm font-bold w-20 shrink-0">{row.label}</span>
                    <span className="text-sm flex-1">{row.display}</span>
                </div>
            ))}

            <div className="flex items-center gap-2.5 pt-1 mt-1 border-t border-(--form-element) opacity-80">
                <span className="text-sm font-black w-20 shrink-0">TOTAL</span>
                <div className="flex-1" />
                <span className={`text-sm font-black w-20 shrink-0 text-right tabular-nums ${isEmpty ? 'blur-xs' : ''}`}>
                    {Math.round(totalPoints)} pts
                </span>
            </div>
        </div>
    );
}
