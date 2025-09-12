import { type ShowdownBotCard } from "../../../api/showdownBotCard";

type CardChartProps = {
    card: ShowdownBotCard
};

export default function CardChart({ card }: CardChartProps) {

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
        const primaryColor = card.image.color_primary || 'rgb(0, 0, 0)';
        
        // Hitting results (typically yellow/gold)
        if (lowerKey.includes('so') || lowerKey.includes('gb') || lowerKey.includes('fb') || lowerKey.includes('pu')) {
            return { 
                backgroundColor: primaryColor, 
                color: 'white',
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
                            px-2 py-1 text-center min-w-12 text-primary
                            ${colorInfo.className}
                            border-r border-form-element last:border-r-0
                        `}
                        style={colorInfo.backgroundColor ? {
                            backgroundColor: colorInfo.backgroundColor,
                            color: colorInfo.color || ''
                        } : {}}
                    >
                        <div className="text-xs font-bold">{key}</div>
                        <div className="text-xs text-nowrap">{String(value)}</div>
                    </div>
                );
            })}
        </div>
    );
};
