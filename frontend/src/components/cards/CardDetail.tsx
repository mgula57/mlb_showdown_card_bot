import { useState } from 'react';
import { CustomSelect } from '../shared/CustomSelect';
import { FaTable, FaPoll, FaCoins, FaBaseballBall } from 'react-icons/fa';
import { type ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';

// Images
import blankPlayer2001Dark from '../../assets/blankplayer-2001-dark.png';

// Tables
import { TableRealVsProjected } from './TableRealVsProjectedBreakdown';
import { TableChartsBreakdown } from './TableChartsBreakdown';
import { TablePointsBreakdown } from './TablePointsBreakdown';

// Trends
import ChartPlayerPointsTrend from './ChartPlayerPointsTrend';

// Live Game
import { GameBoxscore } from '../games/GameBoxscore';

/** Type for CardDetail inputs */
type CardDetailProps = {
    showdownBotCardData: ShowdownBotCardAPIResponse | null;
    isLoading?: boolean;
};

/** Shows Showdown Bot Card Details. Used in Custom card form and modals throughout UI */
export function CardDetail({ showdownBotCardData, isLoading }: CardDetailProps) {

    // Breakdown State
    const [breakdownType, setBreakdownType] = useState<string>("Stats");

    // Card Calcs
    const cardImagePath: string | null = showdownBotCardData?.card?.image ? `${showdownBotCardData.card.image.output_folder_path}/${showdownBotCardData.card.image.output_file_name}` : null;
    const cardAttributes: Record<string, string | number | null> = showdownBotCardData?.card ? {
        points: `${showdownBotCardData.card.points} PTS`,
        year: showdownBotCardData.card.year,
        era: showdownBotCardData.card.era,
        expansion: showdownBotCardData.card.image.expansion == "BS" ? null : showdownBotCardData.card.image.expansion,
        edition: showdownBotCardData.card.image.edition == "NONE" ? null : showdownBotCardData.card.image.edition,
        chart_version: showdownBotCardData.card.chart_version == 1 ? null : showdownBotCardData.card.chart_version,
        parallel: showdownBotCardData.card.image.parallel == "NONE" ? null : showdownBotCardData.card.image.parallel,
    } : {};
    const weeklyChangePoints = showdownBotCardData?.in_season_trends?.pts_change?.week || null;
    const weeklyChangePointsColor = weeklyChangePoints ? (weeklyChangePoints > 0 ? 'text-green-500' : 'text-red-500') : '';
    const weeklyChangePointsSymbol = weeklyChangePoints ? (weeklyChangePoints > 0 ? '▲' : '▼') : '';

    const renderBlankPlayerImageName = () => {
        return blankPlayer2001Dark;
    }

    const renderBreakdownTable = () => {
        switch (breakdownType) {
            case 'Stats':
                return (
                    <div className='space-y-2 overflow-y-auto'>
                        <TableRealVsProjected
                            realVsProjectedData={showdownBotCardData?.card?.real_vs_projected_stats || []}
                        />

                        {/* Footnote */}
                        <div className='flex flex-col text-xs leading-tight space-y-2'>
                            <i>* Indicates a Bot estimated value, real stat unavailable (ex: 1800's, Negro Leagues, PU/FB/GB)</i>
                            <i>** Chart category was adjusted in post-processing to increase accuracy</i>
                        </div>

                    </div>
                );
            case 'Points':
                return (
                    <div className='space-y-2 overflow-y-auto'>

                        <TablePointsBreakdown
                            pointsBreakdownData={showdownBotCardData?.card?.points_breakdown || null}
                            ip={showdownBotCardData?.card?.ip || null}
                        />

                        {/* Footnote */}
                        <div className='text-xs leading-tight'>
                            <i>* Slashlines and HR projections used for points are based on Steroid Era opponent.
                                Stats may not match projections against player's era.</i>
                        </div>

                    </div>
                );
            case 'Charts':
                return (
                    <TableChartsBreakdown
                        chartAccuracyData={showdownBotCardData?.card?.command_out_accuracy_breakdowns || {}}
                    />
                );
        }
    }

    const breakdownFirstRowHeight = 'lg:h-[500px] xl:h-[600px]';

    return (
        <div 
            className="
                w-full
                overflow-y-auto
                p-4 space-y-4
                h-full
                pb-24
            "
        >

            {/* Name and player attributes */}
            <div className="
                flex flex-wrap items-center
                gap-1 mb-2
            ">
                <a 
                    href={showdownBotCardData?.card?.bref_url || '#'} 
                    className='text-3xl font-black opacity-85 pr-2'
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    {showdownBotCardData?.card?.name.toUpperCase() || ""}
                </a>

                {/* Iterate through attributes */}
                {Object.entries(cardAttributes).map(([key, value]) => (
                    <div 
                        key={key} 
                        className={`
                            flex items-center
                            space-x-2 py-1 px-4 
                            bg-secondary rounded-2xl
                            text-sm font-semibold
                            ${value === null ? 'hidden': ''}
                        `}
                    >
                        <span>{value}</span>
                        
                        {/* Change in Points Weekly */}
                        { (weeklyChangePoints && key === "points") && (
                            <div className={`text-xs ${weeklyChangePointsColor}`}>
                                {weeklyChangePointsSymbol} {Math.abs(weeklyChangePoints)} THIS WEEK
                            </div>
                        )}

                    </div>
                ))}
            </div>

            {/* Game Boxscore */}
            <GameBoxscore boxscore={showdownBotCardData?.latest_game_box_score || null} />

            {/* Image and Breakdown Tables */}
            <div
                className={`
                    flex flex-col lg:flex-row
                    lg:items-start
                    gap-4
                `}
            >
                {/* Card Image */}
                <div className={`
                    relative
                    h-auto
                    w-full lg:w-96 xl:w-112 2xl:w-128
                    lg:flex-shrink-0
                `}>
                    <img
                        src={cardImagePath == null ? renderBlankPlayerImageName() : cardImagePath}
                        alt="Blank Player"
                        className={`
                            block mx-auto
                            ${breakdownFirstRowHeight}
                            rounded-xl
                            object-contain
                            shadow-2xl
                        `}
                    /> 

                    {/* Loading Overlay */}
                    {isLoading && (
                        <div className="
                            absolute inset-0 
                            flex items-center justify-center 
                            bg-black/20 
                            rounded-xl
                            backdrop-blur-sm
                        ">
                            <div className="
                                flex flex-col items-center 
                                bg-secondary/90 
                                px-6 py-4 
                            ">
                                <FaBaseballBall 
                                    className="
                                        text-white text-3xl mb-2
                                        animate-bounce
                                    " 
                                    style={{
                                        animationDuration: '0.8s',
                                        animationIterationCount: 'infinite'
                                    }}
                                />
                                <p className="text-white text-sm font-semibold">
                                    Generating Card...
                                </p>
                            </div>
                        </div>
                    )}
                </div>            

                {/* Card Tables */}
                <div
                    className={`
                        flex flex-col
                        w-full lg:flex-1
                        bg-secondary
                        p-4 rounded-xl
                        space-y-4
                        ${breakdownFirstRowHeight}
                    `}
                >
                    <CustomSelect
                        value={breakdownType}
                        options={[
                            { label: 'Card vs Real Stats', value: 'Stats', icon: <FaPoll /> },
                            { label: 'Points', value: 'Points', icon: <FaCoins /> },
                            { label: 'Chart', value: 'Charts', icon: <FaTable /> }
                        ]}
                        onChange={(value) => setBreakdownType(value)}
                    />

                    {/* Breakdown Table */}
                    {renderBreakdownTable()}

                </div>

            </div>

            {/* Trend Graphs */}
            <div 
                className="
                    w-full
                    flex flex-col lg:flex-row
                    space-x-4 space-y-4
                "
            >

                <ChartPlayerPointsTrend 
                    title="Career Trends" 
                    trendData={showdownBotCardData?.historical_season_trends || null} 
                />

                <ChartPlayerPointsTrend 
                    title={showdownBotCardData?.in_season_trends && showdownBotCardData?.card?.year ? `${showdownBotCardData?.card?.year} Card Evolution` : "Year Card Evolution (Available 2020+)"} 
                    trendData={showdownBotCardData?.in_season_trends?.cumulative_trends || null} 
                />

            </div>

        </div>
    );
}