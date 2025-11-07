/**
 * @fileoverview ChartPlayerPointsTrend - Performance trend visualization component
 * 
 * Creates dynamic area charts showing how a player's Showdown card values
 * change over time, with team-color gradients and interactive tooltips
 * displaying detailed performance metrics for each data point.
 */

import { type TrendDatapoint } from '../../api/showdownBotCard';
import { ResponsiveContainer, AreaChart, XAxis, YAxis, Tooltip, Area, CartesianGrid } from 'recharts';
import { useMemo } from 'react';
import { enhanceColorVisibility } from '../../functions/colors';

/**
 * Props for the ChartPlayerPointsTrend component
 */
type ChartPlayerPointsTrendProps = {
    /** Chart title displayed above the visualization */
    title: string;
    /** Trend data keyed by time period (year/date) */
    trendData?: Record<string, TrendDatapoint> | null;
};

/**
 * ChartPlayerPointsTrend - Performance trend visualization component
 * 
 * Creates interactive area charts showing performance trends over time with:
 * 
 * **Visual Features:**
 * - **Dynamic Gradients**: Colors change based on team affiliations over time
 * - **Area Chart**: Shows point values with filled area under the curve
 * - **Interactive Tooltips**: Detailed stats on hover for each data point
 * - **Responsive Design**: Adapts to container size
 * 
 * **Chart Types:**
 * - **Career Trends**: Year-by-year performance across player's career
 * - **Season Trends**: Within-season performance by date/month/week
 * 
 * The component handles missing data gracefully by showing placeholder
 * data with appropriate scaling and formatting for the chart type.
 * 
 * @param title - Chart title and type identifier
 * @param trendData - Performance data points keyed by time period
 * 
 * @example
 * ```tsx
 * <ChartPlayerPointsTrend 
 *   title="Career Trends"
 *   trendData={cardResponse.historical_season_trends?.yearly_trends}
 * />
 * ```
 */
const ChartPlayerPointsTrend = ({ title, trendData }: ChartPlayerPointsTrendProps) => {

    /**
     * Convert trend data from object to array format for chart consumption
     * Enhances colors for better visibility and sets appropriate x-axis values
     */
    const placeholderData = title === "Career Trends" ? generic_career_data : generic_in_season_data;
    const isPlaceholderData = !trendData || Object.keys(trendData).length === 0;
    const trendArray = Object.entries(trendData || placeholderData)
        .map(([key, value]) => ({ 
            ...value,
            color: enhanceColorVisibility(value.color),
            // Use year for career trends, timestamp for season trends
            x_axis: title === "Career Trends" ? key : new Date(key).getTime(),
        }));

    /**
     * Generate unique gradient IDs to prevent conflicts between multiple chart instances
     * Each chart needs its own gradient definition in the SVG
     */
    const gradientId = useMemo(() => `gradient-${Math.random().toString(36).substr(2, 9)}`, [title]);
    const strokeGradientId = useMemo(() => `stroke-gradient-${Math.random().toString(36).substr(2, 9)}`, [title]);

    /**
     * Create horizontal gradient stops based on team colors over time
     * Each data point contributes its team color to the overall gradient
     */
    const createHorizontalGradient = useMemo(() => {
        const totalPoints = trendArray.length;
        const stops = trendArray.map((point, index) => {
            const position = (index / Math.max(totalPoints - 1, 1)) * 100; // Percentage position
            return (
                <stop 
                    key={index}
                    offset={`${position}%`} 
                    stopColor={point.color} 
                    stopOpacity={0.8} // Enhanced opacity for better color visibility
                />
            );
        });
        return stops;
    }, [trendArray]);

    /**
     * Custom tooltip component for displaying detailed point breakdown
     * Shows all MLB Showdown stat categories with proper date formatting
     * @param active - Whether tooltip is currently active
     * @param payload - Chart data payload for the hovered point
     * @param label - X-axis label (year or timestamp)
     */
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            // Format date based on chart type
            const formattedDate = title === "Career Trends" 
                ? `${label}` // Display year directly for career trends
                : new Date(label).toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric', 
                    year: 'numeric'
                  }); // Format timestamp for in-season trends

            return (
                <div className="bg-gray-900 border border-gray-700 p-3 rounded-lg shadow-lg">
                    <p className="text-white font-semibold mb-2">{formattedDate}</p>
                    <div className="space-y-1">
                        <p className="text-green-400">Overall: {data.overall}</p>
                        <p className="text-blue-400">Onbase: {data.onbase}</p>
                        <p className="text-red-400">Control: {data.control}</p>
                        <p className="text-purple-400">Speed: {data.speed}</p>
                        <p className="text-orange-400">IP: {data.ip}</p>
                        <p className="text-gray-300">Team: {data.team}</p>
                    </div>
                </div>
            );
        }
        return null;
    };

    /**
     * Format X-axis labels based on chart type
     * Career trends show years, season trends show formatted dates
     * @param value - Raw axis value (year string or timestamp)
     * @returns Formatted display string
     */
    const formatXAxisLabel = (value: string) => {
        if (title === "Career Trends") {
            // Display year directly for career progression
            return value;
        } else {
            // Format timestamps as readable dates for in-season trends
            try {
                const date = new Date(value);
                const options: Intl.DateTimeFormatOptions = { 
                    month: 'short', 
                    day: 'numeric' 
                };
                return date.toLocaleDateString('en-US', options);
            } catch (error) {
                // Graceful fallback if date parsing fails
                return value;
            }
        }
    };

    // MARK: RENDER
    return (
        <div 
            className="
                flex flex-col
                w-full p-4 
                font-bold text-sm
                rounded-xl bg-secondary
                border-2 border-form-element
                space-y-2
                relative
                select-none
            "
        >
            {/* Chart title */}
            <h2>{title}</h2>

            {/* No data overlay - shown when using placeholder data */}
            {isPlaceholderData && (
                <div className="
                    absolute inset-0 
                    flex items-center justify-center 
                    rounded-xl
                    pointer-events-none
                    z-10
                ">
                    <div className="
                        bg-table-header
                        px-4 py-2 
                        rounded-lg 
                        text-center
                        border border-gray-600
                    ">
                        <p className="text-sm font-semibold">No Data Available</p>
                        <p className="text-xs opacity-50">Showing sample data</p>
                    </div>
                </div>
            )}

            {/* Responsive area chart container */}
            <ResponsiveContainer width="100%" height={250}>
                <AreaChart 
                    data={trendArray}
                    // Disable interactions when showing placeholder data
                    onClick={isPlaceholderData ? undefined : undefined}
                    onMouseEnter={isPlaceholderData ? undefined : undefined}
                    onMouseLeave={isPlaceholderData ? undefined : undefined}
                    style={{ 
                        pointerEvents: isPlaceholderData ? 'none' : 'auto',
                        opacity: isPlaceholderData ? 0.75 : 1,
                        cursor: isPlaceholderData ? 'default' : 'pointer'
                    }}
                >
                    {/* Grid lines for visual reference */}
                    <CartesianGrid strokeDasharray="3 3" stroke='var(--table-header)'/>
                    
                    {/* X-axis configuration - adapts to chart type */}
                    <XAxis 
                        dataKey="x_axis" 
                        type={title === "Career Trends" ? "category" : "number"}
                        fontSize={12}
                        angle={-45}
                        textAnchor="end"
                        height={60}
                        domain={title === "Career Trends" ? undefined : ['dataMin', 'dataMax']}
                        tickFormatter={formatXAxisLabel}
                    />
                    
                    {/* Y-axis for point values */}
                    <YAxis 
                        fontSize={12} 
                        width={30}
                        tickFormatter={(value) => `${value}`}
                    />

                    {/* Interactive tooltip with detailed stats */}
                    <Tooltip content={CustomTooltip}/>

                    {/* SVG gradient definitions */}
                    <defs>
                        {/* Area fill gradient - horizontal team color transition */}
                        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
                            {createHorizontalGradient}
                        </linearGradient>

                        {/* Stroke gradient - same colors with full opacity */}
                        <linearGradient id={strokeGradientId} x1="0%" y1="0%" x2="100%" y2="0%">
                            {trendArray.map((point, index) => {
                                const position = (index / Math.max(trendArray.length - 1, 1)) * 100;
                                return (
                                    <stop 
                                        key={index}
                                        offset={`${position}%`} 
                                        stopColor={point.color} 
                                        stopOpacity={1.0} // Full opacity for border clarity
                                    />
                                );
                            })}
                        </linearGradient>
                    </defs>

                    {/* Main area chart with team color gradients */}
                    <Area 
                        type="monotone" 
                        dataKey="points" 
                        fill={`url(#${gradientId})`}
                        stroke={`url(#${strokeGradientId})`}
                        strokeWidth={1}
                        // Custom dots showing team colors at each point
                        dot={(props) => {
                            const { cx, cy, payload } = props;
                            return (
                                <circle
                                    cx={cx}
                                    cy={cy}
                                    r={3}
                                    fill={payload.color}
                                    stroke={payload.color}
                                    strokeWidth={1}
                                />
                            );
                        }}
                        // Highlighted dot on hover
                        activeDot={{ r: 6, stroke: 'var(--primary)', strokeWidth: 2 }}
                    />

                </AreaChart>
            </ResponsiveContainer>

        </div>
    )
}

export default ChartPlayerPointsTrend;

// MARK: - PLACEHOLDER DATA
// Used when no real trend data is available to show chart structure

/** Generic color for placeholder data points */
const light_gray_color = 'var(--table-header)';

/** Sample career progression data spanning multiple years */
const generic_career_data: Record<string, TrendDatapoint> = {
    '2013': {'color': light_gray_color, 'points': 120, },
    '2014': {'color': light_gray_color, 'points': 160, },
    '2015': {'color': light_gray_color, 'points': 280, },
    '2016': {'color': light_gray_color, 'points': 230, },
    '2017': {'color': light_gray_color, 'points': 310, },
    '2018': {'color': light_gray_color, 'points': 320, },
    '2019': {'color': light_gray_color, 'points': 330, },
    '2020': {'color': light_gray_color, 'points': 440, },
    '2021': {'color': light_gray_color, 'points': 480, },
    '2022': {'color': light_gray_color, 'points': 520, },
    '2023': {'color': light_gray_color, 'points': 400, },
    '2024': {'color': light_gray_color, 'points': 420, },
    '2025': {'color': light_gray_color, 'points': 320, },
};

/** Sample in-season progression data with weekly intervals */
const generic_in_season_data = {
    '2025-03-30': { 'color': light_gray_color, 'points': 150 },
    '2025-04-06': { 'color': light_gray_color, 'points': 110 },
    '2025-04-13': { 'color': light_gray_color, 'points': 160 },
    '2025-04-20': { 'color': light_gray_color, 'points': 250 },
    '2025-04-27': { 'color': light_gray_color, 'points': 270 },
    '2025-05-04': { 'color': light_gray_color, 'points': 280 },
    '2025-05-11': { 'color': light_gray_color, 'points': 250 },
    '2025-05-18': { 'color': light_gray_color, 'points': 230 },
    '2025-05-25': { 'color': light_gray_color, 'points': 200 },
    '2025-06-01': { 'color': light_gray_color, 'points': 270 },
    '2025-06-08': { 'color': light_gray_color, 'points': 330 },
    '2025-06-15': { 'color': light_gray_color, 'points': 350 },
    '2025-06-22': { 'color': light_gray_color, 'points': 350 },
    '2025-06-29': { 'color': light_gray_color, 'points': 370 },
    '2025-07-06': { 'color': light_gray_color, 'points': 320 },
    '2025-07-13': { 'color': light_gray_color, 'points': 350 },
    '2025-07-20': { 'color': light_gray_color, 'points': 400 },
    '2025-07-27': { 'color': light_gray_color, 'points': 470 },
    '2025-08-03': { 'color': light_gray_color, 'points': 450 },
    '2025-08-10': { 'color': light_gray_color, 'points': 480 },
    '2025-08-17': { 'color': light_gray_color, 'points': 500 },
    '2025-08-24': { 'color': light_gray_color, 'points': 520 },
    '2025-08-31': { 'color': light_gray_color, 'points': 550 },
    '2025-09-07': { 'color': light_gray_color, 'points': 500 },
    '2025-09-14': { 'color': light_gray_color, 'points': 510 },
    '2025-09-21': { 'color': light_gray_color, 'points': 510 },
    '2025-09-28': { 'color': light_gray_color, 'points': 520 }
};
