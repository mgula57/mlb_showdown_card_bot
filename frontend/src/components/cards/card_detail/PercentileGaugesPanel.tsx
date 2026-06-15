import { type PointsCategoryBreakdown } from '../../../api/showdownBotCard';
import { formatStatValue } from '../../../functions/formatters';

const METRIC_ALIAS: Record<string, string> = {
    "AVERAGE": "BA",
    "ONBASE": "OBP",
    "SLUGGING": "SLG",
    "HOME_RUNS": "HR",
    "SPEED": "SPD",
    "OUT_DISTRIBUTION": "OUT%",
};

const SKIP_METRICS = new Set(['DECAY', 'IPx', 'TOTAL', 'DEFENSE-CLOSER']);

const PLACEHOLDER_BREAKDOWNS: Record<string, PointsCategoryBreakdown> = {
    AVERAGE:          { metric: 'AVERAGE',          value: 0.274, points: 15, percentile: 0.72 },
    ONBASE:           { metric: 'ONBASE',           value: 0.351, points: 12, percentile: 0.65 },
    SLUGGING:         { metric: 'SLUGGING',         value: 0.489, points: 18, percentile: 0.81 },
    HOME_RUNS:        { metric: 'HOME_RUNS',        value: 27,    points: 20, percentile: 0.88 },
    SPEED:            { metric: 'SPEED',            value: 15,    points: 5,  percentile: 0.45 },
    OUT_DISTRIBUTION: { metric: 'OUT_DISTRIBUTION', value: 0.62,  points: 8,  percentile: 0.55 },
};

function percentileColor(pct: number): string {
    if (pct >= 0.75) return '#22c55e';
    if (pct >= 0.50) return '#84cc16';
    if (pct >= 0.25) return '#eab308';
    return '#ef4444';
}

type PercentileGaugesPanelProps = {
    breakdowns?: Record<string, PointsCategoryBreakdown>;
};

export default function PercentileGaugesPanel({ breakdowns }: PercentileGaugesPanelProps) {
    const isEmpty = !breakdowns || Object.keys(breakdowns).length === 0;
    const data = isEmpty ? PLACEHOLDER_BREAKDOWNS : breakdowns!;

    const items = Object.entries(data)
        .map(([key, bd]) => ({ ...bd, metric: key }))
        .filter(bd =>
            bd.percentile !== null &&
            bd.percentile !== undefined &&
            !SKIP_METRICS.has(bd.metric) &&
            !bd.metric.includes('ICON')
        )
        .sort((a, b) => b.points - a.points);

    if (items.length === 0) return null;

    return (
        <div className={`w-full ${isEmpty ? 'opacity-25 pointer-events-none select-none' : ''}`}>
            <table className="w-full text-xs">
                <thead>
                    <tr className="opacity-40 border-b border-current">
                        <th className="text-left font-semibold uppercase tracking-wide py-1 pr-2">Stat</th>
                        <th className="text-right font-semibold uppercase tracking-wide py-1 px-2">Value</th>
                        <th className="text-right font-semibold uppercase tracking-wide py-1 pl-2">Pctile</th>
                        <th className="w-24 pl-3 py-1"></th>
                    </tr>
                </thead>
                <tbody>
                    {items.map(bd => {
                        const label = METRIC_ALIAS[bd.metric] || bd.metric;
                        const pct = bd.percentile as number;
                        const color = percentileColor(pct);
                        return (
                            <tr key={bd.metric} className="border-b border-current border-opacity-10 last:border-0">
                                <td className="py-1.5 pr-2 font-semibold uppercase tracking-wide opacity-60">{label}</td>
                                <td className={`py-1.5 px-2 text-right font-bold ${isEmpty ? 'blur-xs' : ''}`}>
                                    {formatStatValue(bd.value, bd.metric)}
                                </td>
                                <td className={`py-1.5 pl-2 text-right font-black ${isEmpty ? 'blur-xs' : ''}`} style={{ color }}>
                                    {Math.round(pct * 100)}
                                </td>
                                <td className="py-1.5 pl-3">
                                    <div className="h-1.5 w-full rounded-full bg-current opacity-15 overflow-hidden">
                                        <div
                                            className="h-full rounded-full"
                                            style={{ width: `${pct * 100}%`, backgroundColor: color }}
                                        />
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
