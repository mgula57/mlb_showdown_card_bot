import { type TrendDatapoint } from '../../api/showdownBotCard';
import { ResponsiveContainer, AreaChart, XAxis, YAxis, Tooltip, Area, CartesianGrid } from 'recharts';
import { useMemo } from 'react';

type ChartPlayerPointsTrendProps = {
    title: string;
    trendData?: Record<string, TrendDatapoint> | null;
};

// Adjust color for theme
const enhanceColorVisibility = (color: string) => {
    const isDarkMode = document.documentElement.classList.contains('dark');
    
    // Simple brightness adjustment
    if (isDarkMode) {
        // Add some brightness and saturation for dark mode
        return `color-mix(in srgb, ${color} 70%, white 30%)`;
    } else {
        // Slightly darken for light mode
        return `color-mix(in srgb, ${color} 85%, black 15%)`;
    }
};

const ChartPlayerPointsTrend = ({ title, trendData }: ChartPlayerPointsTrendProps) => {

    // Convert trendData to array format
    const placeholderData = title === "Career Trends" ? generic_career_data : generic_in_season_data;
    const isPlaceholderData = !trendData || Object.keys(trendData).length === 0;
    const trendArray = Object.entries(trendData || placeholderData)
                            .map(([key, value]) => ({ 
                                ...value,
                                color: enhanceColorVisibility(value.color),
                                x_axis: title === "Career Trends" ? key : new Date(key).getTime(), // Use year or date as x_axis
                            }))

    // Create unique id for each chart instance
    const gradientId = useMemo(() => `gradient-${Math.random().toString(36).substr(2, 9)}`, [title]);
    const strokeGradientId = useMemo(() => `stroke-gradient-${Math.random().toString(36).substr(2, 9)}`, [title]);

    // Create horizontal gradient stops based on data colors
    const createHorizontalGradient = useMemo(() => {
        const totalPoints = trendArray.length;
        const stops = trendArray.map((point, index) => {
            const position = (index / Math.max(totalPoints - 1, 1)) * 100; // Percentage position
            return (
                <stop 
                    key={index}
                    offset={`${position}%`} 
                    stopColor={point.color} 
                    stopOpacity={0.8} // Increased opacity to see colors better
                />
            );
        });
        return stops;
    }, [trendArray]);

    const CustomTooltip = ({ active, payload, label }: any) => {
        const isVisible = active && payload && payload.length;
        const card = payload[0]?.payload as TrendDatapoint;
        return (
            <div className="bg-primary p-2 rounded-lg" style={{ visibility: isVisible ? 'visible' : 'hidden' }}>
            {isVisible && (
                <div className="flex flex-col text-xs">

                    {/* POINTS */}
                    <p className="font-black border-b border-gray-600">{`${formatXAxisLabel(label)} ${card.team}: ${card.points} PTS`}</p>

                    {/* COMMAND/OUTS */}
                    <p className="label pt-1">{`${card.command} ${card.command_type?.toUpperCase() === 'ONBASE' ? 'OB' : 'CO'} | ${card.outs} OUTS`}</p>

                    {/* PITCHING */}
                    {card.so && <p className="label">{`${card.so} SO`}</p>}
                    {card.ip && <p className="label">{`${card.ip} IP`}</p>}
                    
                    {/* HITTING */}
                    {card.hr && <p className="label">{`${card.hr} HR`}</p>}
                    {card.defense && <p className="label">{`${card.defense}`}</p>}
                    {card.speed && <p className="label">{`${card.speed} SPD`}</p>}
                    {card["2b"] && <p className="label">{`${card["2b"]} 2B`}</p>}

                    {/* SHOPS+ */}
                    {card.shOPS_plus && <p className="label">{`${card.shOPS_plus} shOPS+`}</p>}

                </div>
            )}
            </div>
        );
    };

    // Format X-axis labels based on title
    const formatXAxisLabel = (value: string) => {
        if (title === "Career Trends") {
            // For career trends, just return the year as-is
            return value;
        } else {
            // For dates, format as "Apr 1", "Apr 11", etc.
            try {
                const date = new Date(value);
                const options: Intl.DateTimeFormatOptions = { 
                    month: 'short', 
                    day: 'numeric' 
                };
                return date.toLocaleDateString('en-US', options);
            } catch (error) {
                // Fallback to original value if date parsing fails
                return value;
            }
        }
    };

    // MARK: MAIN CONTENT
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
            "
        >
            {/* Title */}
            <h2>{title}</h2>

            {/* Placeholder overlay */}
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

            {/* Graph */}
            <ResponsiveContainer width="100%" height={250}>
                {/* Add your chart component here, using trendData as needed */}
                <AreaChart 
                    data={trendArray}
                    onClick={isPlaceholderData ? undefined : undefined} // Disable click
                    onMouseEnter={isPlaceholderData ? undefined : undefined} // Disable mouse enter
                    onMouseLeave={isPlaceholderData ? undefined : undefined} // Disable mouse leave
                    style={{ 
                        pointerEvents: isPlaceholderData ? 'none' : 'auto',
                        opacity: isPlaceholderData ? 0.75 : 1,
                        cursor: isPlaceholderData ? 'default' : 'pointer'
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" stroke='var(--table-header)'/>
                    
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
                    
                    <YAxis 
                        fontSize={12} 
                        width={30}
                        tickFormatter={(value) => `${value}`}
                    />

                    <Tooltip content={CustomTooltip}/>

                    {/* Horizontal gradient definition */}
                    <defs>
                        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
                            {createHorizontalGradient}
                        </linearGradient>

                        {/* Stroke gradient (same colors, full opacity) */}
                        <linearGradient id={strokeGradientId} x1="0%" y1="0%" x2="100%" y2="0%">
                            {trendArray.map((point, index) => {
                                const position = (index / Math.max(trendArray.length - 1, 1)) * 100;
                                return (
                                    <stop 
                                        key={index}
                                        offset={`${position}%`} 
                                        stopColor={point.color} 
                                        stopOpacity={1.0} // Full opacity for stroke
                                    />
                                );
                            })}
                        </linearGradient>

                    </defs>

                    <Area 
                        type="monotone" 
                        dataKey="points" 
                        fill={`url(#${gradientId})`}
                        stroke={`url(#${strokeGradientId})`}
                        strokeWidth={1}
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
                        activeDot={{ r: 6, stroke: 'var(--primary)', strokeWidth: 2 }}
                    />

                </AreaChart>
            </ResponsiveContainer>

        </div>
    )
}

export default ChartPlayerPointsTrend;

// MARK: - Placeholder Data

let light_gray_color = 'var(--table-header)';

let generic_career_data: Record<string, TrendDatapoint> = {
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
let generic_in_season_data = {
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
