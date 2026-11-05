import { type ShowdownBotCardChart } from '../../../api/showdownBotCard';
import { darkenIfLowContrastOnWhite } from '../../../functions/colors';
import { CardChart, buildChartRangesFromValues } from '../card_elements/CardChart';
import { CAPS_LABEL_CLASS } from '../../shared/fieldStyles';
import { StatTile } from '../../shared/StatTile';
import { useTheme } from '../../shared/SiteSettingsContext';

const OUTS = new Set(['PU', 'SO', 'GB', 'FB']);
const TOTAL = 20;

const PLACEHOLDER_CHART: ShowdownBotCardChart = {
    command: 9, outs: 5, outs_full: 5, is_pitcher: false, 
    ranges: { },
    values: { SO: 2, GB: 2, FB: 1, BB: 5, '1B': 6, '2B': 2, HR: 2 },
    set: '2005'
};

function outcomeColor(key: string, primaryColor?: string, secondaryColor?: string): string {
    if (OUTS.has(key.toUpperCase())) return secondaryColor ?? 'var(--showdown-red)';
    if (['BB', '1B', '1B+', '2B', '3B', 'HR'].includes(key.toUpperCase())) return primaryColor ?? 'var(--showdown-blue)';
    return 'var(--rule-strong)';
}

function Bar({ label, value, color, blurred }: { label: string; value: number; color: string; blurred: boolean }) {
    const pct = Math.min((value / TOTAL) * 100, 100);
    return (
        <div className="flex items-center gap-2.5">
            <span className={`w-7 text-right shrink-0 ${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>{label}</span>
            <div className="relative flex-1 h-3.5 rounded-full overflow-hidden" style={{ background: 'color-mix(in srgb, var(--form-element) 30%, transparent)' }}>
                <div
                    className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                    style={{ width: `${pct}%`, backgroundColor: color, opacity: 0.85 }}
                />
            </div>
            <span className={`text-[11px] font-semibold w-10 shrink-0 text-right text-(--text-tertiary) tabular-nums ${blurred ? 'blur-xs' : ''}`}>
                {value % 1 === 0 ? value : value.toFixed(2)}/{TOTAL}
            </span>
        </div>
    );
}

type BaselineOpponentBreakdownProps = {
    chart?: ShowdownBotCardChart;
    primaryColor?: string;
    secondaryColor?: string;
    className?: string;
};

const RESULT_ORDER_DEFAULT = ['PU', 'SO', 'GB', 'FB', 'BB', '1B', '1B+', '2B', '3B', 'HR'];
const RESULT_ORDER_2000 = ['SO', 'PU', 'GB', 'FB', 'BB', '1B', '1B+', '2B', '3B', 'HR'];

export function BaselineOpponentBreakdown({ chart, primaryColor, secondaryColor, className }: BaselineOpponentBreakdownProps) {
    const { isDark } = useTheme();
    const isEmpty = !chart;
    const data = isEmpty ? PLACEHOLDER_CHART : chart!;

    const OUTCOME_ORDER = data.set === '2000' ? RESULT_ORDER_2000 : RESULT_ORDER_DEFAULT;

    const commandLabel = data.is_pitcher ? 'Control' : 'Onbase';
    const outcomes = Object.entries(data.values || {}).sort(([a], [b]) => {
        const ia = OUTCOME_ORDER.indexOf(a.toUpperCase());
        const ib = OUTCOME_ORDER.indexOf(b.toUpperCase());
        return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    });

    const primaryBarColor = primaryColor && !isDark ? darkenIfLowContrastOnWhite(primaryColor) : primaryColor;
    const secondaryBarColor = secondaryColor && !isDark ? darkenIfLowContrastOnWhite(secondaryColor) : secondaryColor;

    const chartDataToRender = Object.keys(data.results ?? {}).length > 0 ? data.ranges : buildChartRangesFromValues(data.values ?? {}, data.set, data.is_pitcher);

    return (
        <div className={`space-y-3 ${isEmpty ? 'opacity-25 pointer-events-none select-none' : ''} ${className ?? ''}`}>
            <div className="flex gap-2">
                <StatTile label={commandLabel} value={data.command.toFixed(2)} blurred={isEmpty} />
                <StatTile label="Outs" value={data.outs.toFixed(2)} blurred={isEmpty} />
            </div>
            <div className="flex flex-col space-y-0.5">
                <CardChart
                    chartRanges={chartDataToRender}
                    showdownSet={data.set}
                    primaryColor={'rgb(128,128,128)'}
                    secondaryColor={'rgb(0,0,0)'}
                    className="max-w-full"
                />
                <span className="text-[10px] opacity-40 ml-2">** Chart is approximation, rounded to whole numbers. Actual values used are decimals</span>
            </div>
            <div className="space-y-1.5">
                {outcomes.map(([key, value]) => (
                    <Bar key={key} label={key} value={value} color={outcomeColor(key, primaryBarColor, secondaryBarColor)} blurred={isEmpty} />
                ))}
            </div>
        </div>
    );
}
