import { type ShowdownBotCard } from "../../../api/showdownBotCard";
import { getContrastColor } from "../../shared/Color";

type CardChartProps = {
    card: ShowdownBotCard
    cellClassName?: string
};

export default function CardChart({ card, cellClassName }: CardChartProps) {

    const chartData = card?.chart.ranges || {};
    const showdownSet = card?.set || '2000';

    // Sort the values based on manual list of keys
    const sortOrder = showdownSet === '2000' 
                        ? ['so', 'pu', 'gb', 'fb', 'bb', '1b', '1b+', '2b', '3b', 'hr']
                        : ['pu', 'so', 'gb', 'fb', 'bb', '1b', '1b+', '2b', '3b', 'hr'];
    const sortedChartData = Object.fromEntries(
        Object.entries(chartData).sort((a, b) => {
            const indexA = sortOrder.indexOf(a[0].toLowerCase());
            const indexB = sortOrder.indexOf(b[0].toLowerCase());
            return (indexA === -1 ? Number.MAX_VALUE : indexA) - (indexB === -1 ? Number.MAX_VALUE : indexB);
        }
    ));

    // Use sorted data for rendering
    const chartDataToRender = sortedChartData;

    // Color mapping for different result types
    const getColorClass = (key: string, _: number) => {
        const lowerKey = key.toLowerCase();
        const color = (['NYM', 'SDP'].includes(card.team) ? card.image.color_secondary : card.image.color_primary) || 'rgb(0, 0, 0)';
        
        // Hitting results (typically yellow/gold)
        if (lowerKey.includes('so') || lowerKey.includes('gb') || lowerKey.includes('fb') || lowerKey.includes('pu')) {
            return {
                backgroundColor: color,
                color: getContrastColor(color),
                className: '' // No Tailwind bg class
            };
        }                
        // Default fallback
        return { 
            backgroundColor: '',
            color: '',
            className: 'bg-[var(--background-secondary)] text-black'
        };
    };

    return (
        <div className="inline-flex rounded-lg overflow-hidden text-xs font-semibold border-2 border-form-element">
            {Object.entries(chartDataToRender).map(([key, value], index) => {
                const colorInfo = getColorClass(key, index);
                
                return (
                    <div
                        key={key}
                        className={`
                            ${cellClassName || 'min-w-8 sm:min-w-11'}
                            px-1 py-1 text-center text-primary
                            ${colorInfo.className}
                            border-r border-form-element last:border-r-0
                        `}
                        style={colorInfo.backgroundColor ? {
                            backgroundColor: colorInfo.backgroundColor,
                            color: colorInfo.color || ''
                        } : {}}
                    >
                        <div className="text-[11px] sm:text-xs font-black">{key}</div>
                        <div className="text-[10px] sm:text-[11px] font-bold text-nowrap">{String(value)}</div>
                    </div>
                );
            })}
        </div>
    );
};
