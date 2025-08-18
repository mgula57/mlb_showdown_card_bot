import { type TrendDatapoint } from '../../api/showdownBotCard';
import { ResponsiveContainer, AreaChart, XAxis, YAxis, Tooltip, Area, CartesianGrid } from 'recharts';
import { useMemo } from 'react';

type ChartPlayerPointsTrendProps = {
    title: string;
    trendData?: Record<string, TrendDatapoint> | null;
};

const ChartPlayerPointsTrend = ({ title, trendData }: ChartPlayerPointsTrendProps) => {

    // Convert trendData to array format
    const placeholderData = title === "Career Trends" ? generic_career_data : generic_in_season_data;
    const isPlaceholderData = !trendData || Object.keys(trendData).length === 0;
    const trendArray = Object.entries(trendData || placeholderData).map(([key, value]) => ({ x_axis: key, ...value }) );

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
        return (
            <div className="bg-primary p-2" style={{ visibility: isVisible ? 'visible' : 'hidden' }}>
            {isVisible && (
                <>
                    <p className="label">{`${formatXAxisLabel(label)} : ${payload[0].value} PTS`}</p>
                </>
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

    return (
        <div 
            className="
                flex flex-col
                w-full p-4 
                font-bold text-sm
                rounded-xl bg-secondary shadow-lg
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
                    bg-black/20 
                    rounded-xl
                    pointer-events-none
                    z-10
                ">
                    <div className="
                        bg-gray-800/90 
                        text-white 
                        px-4 py-2 
                        rounded-lg 
                        text-center
                        border border-gray-600
                    ">
                        <p className="text-sm font-semibold">No Data Available</p>
                        <p className="text-xs text-gray-300">Showing sample data</p>
                    </div>
                </div>
            )}

            {/* Graph */}
            <ResponsiveContainer width="100%" height={250}>
                {/* Add your chart component here, using trendData as needed */}
                <AreaChart data={trendArray}>
                    <CartesianGrid strokeDasharray="3 3" stroke='rgba(255, 255, 255, 0.2)'/>
                    
                    <XAxis 
                        dataKey="x_axis" 
                        fontSize={12}
                        tickFormatter={formatXAxisLabel}
                        angle={-45}
                        textAnchor="end"
                        height={60}
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
                        activeDot={{ r: 6, stroke: 'white', strokeWidth: 2 }}
                    />

                </AreaChart>
            </ResponsiveContainer>

        </div>
    )
}

export default ChartPlayerPointsTrend;

// MARK: - Placeholder Data

let light_gray_color = 'rgba(250, 200, 200, 0.3)';

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
