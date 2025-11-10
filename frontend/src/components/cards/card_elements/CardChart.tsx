import { type ShowdownBotCard } from "../../../api/showdownBotCard";
import { getContrastColor } from "../../shared/Color";

/**
 * Props for the CardChart component
 */
type CardChartProps = {
    /** Complete card data containing chart ranges and styling information */
    card: ShowdownBotCard;
    /** Optional CSS class name for customizing cell sizing */
    cellClassName?: string;
};

/**
 * CardChart - Displays the dice roll ranges for MLB Showdown card outcomes
 * 
 * This component renders the core gameplay element of Showdown cards - the chart
 * that maps dice roll results (1-20) to baseball outcomes like hits, walks, and outs.
 * The chart is visually styled with team colors and follows set-specific result ordering.
 * 
 * @param card - ShowdownBotCard data containing chart ranges and styling
 * @param cellClassName - Optional CSS class for customizing cell appearance
 * 
 * @example
 * ```tsx
 * <CardChart 
 *   card={cardData} 
 *   cellClassName="min-w-12" 
 * />
 * ```
 */
export default function CardChart({ card, cellClassName }: CardChartProps) {
    // Extract chart data with fallback to empty object
    const chartData = card?.chart.ranges || {};
    const showdownSet = card?.set || '2000';

    /**
     * Sort chart results based on set-specific ordering
     * 
     * Different Showdown sets display results in different orders:
     * - 2000 set: SO first, then PU
     * - Other sets: PU first, then SO
     * 
     * Results are ordered from worst to best outcomes for the hitter:
     * Outs (SO, PU, GB, FB) → Walk (BB) → Hits (1B, 1B+, 2B, 3B, HR)
     */
    const sortOrder = showdownSet === '2000' 
        ? ['so', 'pu', 'gb', 'fb', 'bb', '1b', '1b+', '2b', '3b', 'hr']
        : ['pu', 'so', 'gb', 'fb', 'bb', '1b', '1b+', '2b', '3b', 'hr'];
    
    const sortedChartData = Object.fromEntries(
        Object.entries(chartData).sort((a, b) => {
            const indexA = sortOrder.indexOf(a[0].toLowerCase());
            const indexB = sortOrder.indexOf(b[0].toLowerCase());
            // Put unknown results at the end
            return (indexA === -1 ? Number.MAX_VALUE : indexA) - (indexB === -1 ? Number.MAX_VALUE : indexB);
        })
    );

    // Use sorted data for rendering
    const chartDataToRender = sortedChartData;

    /**
     * Determines color styling for chart cells based on result type
     * 
     * @param key - The result type (e.g., 'SO', 'HR', '1B')
     * @returns Object containing styling information (backgroundColor, color, className)
     */
    const getColorClass = (key: string, _: number) => {
        const lowerKey = key.toLowerCase();
        
        // Use secondary color for certain teams (NYM, SDP) for better contrast
        const color = (['NYM', 'SDP'].includes(card.team) 
            ? card.image.color_secondary 
            : card.image.color_primary) || 'rgb(0, 0, 0)';
        
        // Out results get team color background with contrasting text
        if (lowerKey.includes('so') || lowerKey.includes('gb') || 
            lowerKey.includes('fb') || lowerKey.includes('pu')) {
            return {
                backgroundColor: color,
                color: getContrastColor(color),
                className: '' // No Tailwind classes when using inline styles
            };
        }
        
        // Positive results (hits, walks) use default theme colors
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
                        {/* Result type label (e.g., "SO", "HR") */}
                        <div className="text-[11px] sm:text-xs font-black">{key}</div>
                        {/* Dice roll range (e.g., "1-5", "16-20") */}
                        <div className="text-[10px] sm:text-[11px] font-bold text-nowrap">{String(value)}</div>
                    </div>
                );
            })}
        </div>
    );
};
