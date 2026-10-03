import { type ChartAccuracyCategoryBreakdown, type CommandOutSelection } from '../../../api/showdownBotCard';
import { formatSlashlineValue } from '../../../functions/formatters';
import CardCommand from '../card_elements/CardCommand';

const PLACEHOLDER_CHART_ACCURACY: Record<string, Record<string, ChartAccuracyCategoryBreakdown>> = {
    '10-5': { OVERALL: { stat: 'OVERALL', accuracy: 0.9421, actual: 0.840, comparison: 0.851, is_pitcher: false, notes: '' } },
    '9-5': { OVERALL: { stat: 'OVERALL', accuracy: 0.9187, actual: 0.840, comparison: 0.862, is_pitcher: false, notes: '' } },
    '8-5': { OVERALL: { stat: 'OVERALL', accuracy: 0.9043, actual: 0.840, comparison: 0.875, is_pitcher: false, notes: '' } },
    '7-5': { OVERALL: { stat: 'OVERALL', accuracy: 0.8876, actual: 0.840, comparison: 0.888, is_pitcher: false, notes: '' } },
    '6-5': { OVERALL: { stat: 'OVERALL', accuracy: 0.8654, actual: 0.840, comparison: 0.901, is_pitcher: false, notes: '' } },
};

function KpiTile({ label, value, blurred }: { label: string; value: string | number; blurred: boolean }) {
    return (
        <div 
            className="@container flex-1 flex flex-col items-center justify-center gap-1 rounded-lg py-2.5 px-3 bg-tertiary" 
        >
            <span className={`text-xl @[80px]:text-2xl font-black leading-none tabular-nums ${blurred ? 'blur-xs' : ''}`}>
                {value}
            </span>
            <span className="text-[8px] @[80px]:text-[10px] font-semibold uppercase tracking-widest opacity-50">{label}</span>
        </div>
    );
}

type ChartRow = ChartAccuracyCategoryBreakdown & { chart: string; rank: number; accuracyRank: number };

const MAX_RANKED_ROWS = 5;
const PICKED_COLOR = 'rgb(96,165,250)';
const OUTLIER_COLOR = 'rgb(234,179,8)';

/** Small label pinned inside an accuracy bar. Collapses to `shortLabel` in narrow bars */
function BarBadge({ label, shortLabel, color }: { label: string; shortLabel: string; color: string }) {
    return (
        <span className="flex items-center text-[8px] h-3.5 font-black uppercase tracking-wide leading-none px-1 rounded" style={{ color, background: 'rgba(0,0,0,0.45)' }}>
            <span className="@max-[60px]:hidden">{label}</span>
            <span className="@[60px]:hidden">{shortLabel}</span>
        </span>
    );
}

function AccuracyBar({ row, blurred, isSelected, isPicked, barFloor }: { row: ChartRow; blurred: boolean; isSelected: boolean; isPicked: boolean; barFloor: number }) {
    const barPct = Math.max(0, Math.min((row.accuracy - barFloor) / (1 - barFloor), 1)) * 100;
    const [cmd, outs] = row.chart.split('-');
    const label = outs ? `${cmd}-${outs}` : row.chart;
    const isOutlier = row.notes?.includes('OUTLIER');
    return (
        <div className={`flex items-center gap-2.5 rounded-md transition-colors ${isSelected ? '-mx-1.5 px-1.5 py-0.5' : ''}`} style={isSelected ? { background: 'color-mix(in srgb, var(--form-element) 25%, transparent)' } : undefined}>
            <div className="flex items-center gap-0.5">
                <div className="w-1.5 h-1.5 rounded-full shrink-0 translate-x-0.5" style={{ backgroundColor: isSelected ? 'rgb(34,197,94)' : 'transparent' }} />
                <span className={`text-[12px] font-black w-14 text-right shrink-0 tabular-nums ${isSelected ? 'opacity-100' : 'opacity-60'}`}>{row.rank}. {label}</span>
            </div>
            <div className="@container relative flex-1 h-3.5 rounded-full overflow-hidden" style={{ background: 'color-mix(in srgb, var(--form-element) 30%, transparent)' }}>
                <div
                    className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                    style={{ width: `${barPct}%`, backgroundColor: 'rgb(156,163,175)', opacity: 0.85 }}
                />
                {(isPicked || isOutlier) && (
                    <div className="absolute inset-y-0 left-0 flex items-center gap-1 pointer-events-none">
                        {isPicked && <BarBadge label="picked" shortLabel="pk" color={PICKED_COLOR} />}
                        {isOutlier && <BarBadge label="outlier" shortLabel="ol" color={OUTLIER_COLOR} />}
                    </div>
                )}
            </div>
            <span className={`text-[12px] font-semibold w-10 shrink-0 text-right opacity-60 tabular-nums ${blurred ? 'blur-xs' : ''}`}>
                {(row.accuracy * 100).toFixed(1)}%
            </span>
            <span className={`text-[12px] font-semibold w-10 shrink-0 text-right opacity-60 tabular-nums ${blurred ? 'blur-xs' : ''}`}>
                {formatSlashlineValue(row.comparison)}
            </span>
            <span className={`text-[12px] font-semibold w-10 shrink-0 text-right opacity-60 tabular-nums ${blurred ? 'blur-xs' : ''}`}>
                {formatSlashlineValue(row.actual)}
            </span>
        </div>
    );
}

type ChartSelectionBreakdownProps = {
    chartAccuracyData?: Record<string, Record<string, ChartAccuracyCategoryBreakdown>>;
    commandOutAccuraciesData?: Record<string, number>;
    selectedChartVersion?: number;
    /** Command/outs of the card's chart (ex: '13-8'). Falls back to ranking by chart version when missing (older cards) */
    selectedChart?: string | null;
    /** Curated combo applied to the card, if any */
    selection?: CommandOutSelection | null;
    className?: string;
};

export function ChartSelectionBreakdown({ chartAccuracyData, commandOutAccuraciesData, selectedChartVersion, selectedChart, selection, className }: ChartSelectionBreakdownProps) {
    const isEmpty = !chartAccuracyData || Object.keys(chartAccuracyData).length === 0;
    const data = isEmpty ? PLACEHOLDER_CHART_ACCURACY : chartAccuracyData!;

    const byAccuracy: ChartRow[] = Object.entries(data)
        .flatMap(([chart, perStatRecord]) =>
            Object.entries(perStatRecord)
                .filter(([, item]) => item.stat.toUpperCase() === 'OVERALL')
                .map(([, item]) => ({
                    ...item,
                    accuracy: commandOutAccuraciesData?.[chart] ?? 0,
                    chart,
                    rank: 0,
                    accuracyRank: 0,
                }))
        )
        .sort((a, b) => b.accuracy - a.accuracy)
        .map((row, index) => ({ ...row, accuracyRank: index + 1 }));

    // A CURATED COMBO IS PROMOTED TO VERSION 1, PUSHING THE REST DOWN (MATCHES BACKEND CHART VERSION ORDER)
    const pickedChart = selection ? `${selection.command}-${selection.outs}` : null;
    const allRanked: ChartRow[] = [
        ...byAccuracy.filter(row => row.chart === pickedChart),
        ...byAccuracy.filter(row => row.chart !== pickedChart),
    ].map((row, index) => ({ ...row, rank: index + 1 }));

    const selectedVersion = (selectedChart && allRanked.find(row => row.chart === selectedChart))
        || allRanked.find(row => row.rank === (selectedChartVersion ?? 1))
        || allRanked[0];

    // TOP CHARTS, PLUS THE SELECTED CHART WHEN IT FALLS OUTSIDE OF THEM
    const ranked = allRanked.slice(0, MAX_RANKED_ROWS);
    if (selectedVersion && !ranked.includes(selectedVersion)) {
        ranked.push(selectedVersion);
    }

    const barFloor = ranked.length > 0 ? Math.min(0.85, ...ranked.map(row => row.accuracy)) : 0.85;
    const isPicked = !!pickedChart && selectedVersion?.chart === pickedChart;

    return (
        <div className={`space-y-3 ${isEmpty ? 'opacity-25 pointer-events-none select-none' : ''} ${className ?? ''}`}>
            {selectedVersion && (
                <div className="grid grid-cols-3 items-center gap-2">
                    <div className="@container flex gap-2 items-center bg-tertiary rounded-lg py-2.5 px-1 w-full justify-center">
                        <CardCommand 
                            isPitcher={selectedVersion.is_pitcher} 
                            command={Number(selectedVersion.chart.split('-')[0])} 
                            primaryColor='#ffffff' 
                            secondaryColor='#ffffff' 
                            className="w-5 h-5 @[10px]:w-7 @[10px]:h-7 @[100px]:w-11 @[100px]:h-11" 
                        />
                        <span className="text-sm md:text-md font-semibold uppercase tracking-wide opacity-90 gap-0 flex flex-col items-center">
                            {(selectedVersion.chart.split('-')[1] || '0') === '0' ? '0' : `1-${selectedVersion.chart.split('-')[1]}`}
                            <span className='text-[9px] @[80px]:text-xs opacity-70'> Out</span>
                        </span>
                    </div>
                    <KpiTile label="Card OPS" value={formatSlashlineValue(selectedVersion.comparison)} blurred={isEmpty} />
                    <KpiTile label="Real OPS" value={formatSlashlineValue(selectedVersion.actual)} blurred={isEmpty} />
                </div>
            )}
            {isPicked && (
                <div className="flex items-center gap-2 rounded-lg px-2.5 py-2 text-[11px] leading-snug" style={{ background: `color-mix(in srgb, ${PICKED_COLOR} 12%, transparent)` }}>
                    <span className="shrink-0 text-[9px] font-black uppercase tracking-wide px-1.5 py-0.5 rounded" style={{ color: PICKED_COLOR, background: 'rgba(0,0,0,0.35)' }}>
                        Curated
                    </span>
                    <span className="opacity-70">
                        {selection?.note || 'Chart chosen manually instead of the most accurate combo.'}
                    </span>
                </div>
            )}
            <div className="space-y-1.5">
                <div className="flex items-center gap-2.5 pb-0.5  border-opacity-10">
                    <span className="text-[10px] font-semibold uppercase tracking-wide opacity-40 w-16 text-right shrink-0">Chart</span>
                    <div className="flex-1" />
                    {['SCORE', 'CARD', 'REAL'].map(label => (
                        <span key={label} className="text-[10px] font-semibold uppercase tracking-wide opacity-40 w-10 text-right shrink-0">{label}</span>
                    ))}
                </div>
                {ranked.map((row) => (
                    <AccuracyBar key={row.chart} row={row} blurred={isEmpty} isSelected={row.chart === selectedVersion?.chart} isPicked={row.chart === pickedChart} barFloor={barFloor} />
                ))}
            </div>
        </div>
    );
}
