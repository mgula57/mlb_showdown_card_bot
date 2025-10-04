import { useState, useEffect, useCallback } from 'react';
import { useTheme, useSiteSettings } from "../shared/SiteSettingsContext";
import CustomSelect from '../shared/CustomSelect';
import { FaTable, FaPoll, FaCoins, FaBaseballBall, FaUser } from 'react-icons/fa';
import { type ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';
import { enhanceColorVisibility } from '../../functions/colors';

import { imageForSet } from "../shared/SiteSettingsContext";

// Tables
import { TableRealVsProjected } from './TableRealVsProjectedBreakdown';
import { TableChartsBreakdown } from './TableChartsBreakdown';
import { TablePointsBreakdown } from './TablePointsBreakdown';
import { TableOpponentBreakdown } from './TableOpponentBreakdown';

// API
import { generateCardImage } from '../../api/showdownBotCard';

// Trends
import ChartPlayerPointsTrend from './ChartPlayerPointsTrend';

// Live Game
import { GameBoxscore } from '../games/GameBoxscore';

/** Type for CardDetail inputs */
type CardDetailProps = {
    showdownBotCardData: ShowdownBotCardAPIResponse | null;
    hideTrendGraphs?: boolean;
    isLoading?: boolean;
    isLoadingGameBoxscore?: boolean;
};

/** Shows Showdown Bot Card Details. Used in Custom card form and modals throughout UI */
export function CardDetail({ showdownBotCardData, isLoading, isLoadingGameBoxscore, hideTrendGraphs=false }: CardDetailProps) {

    // MARK: STATES

    // Card
    const [internalCardData, setInternalCardData] = useState<ShowdownBotCardAPIResponse | null>(showdownBotCardData);
    // Use internal state instead of prop throughout component
    const activeCardData = internalCardData || showdownBotCardData;

    // Theme
    const { isDark } = useTheme();

    const { userShowdownSet } = useSiteSettings();

    // Update internal state when prop changes
    useEffect(() => {
        // Skip if no new data
        if (!showdownBotCardData) {
            return;
        }

        // Skip if same card (by bref_id + year + set)
        if (
            internalCardData?.card?.bref_id === showdownBotCardData?.card?.bref_id &&
            internalCardData?.card?.year === showdownBotCardData?.card?.year &&
            internalCardData?.card?.set === showdownBotCardData?.card?.set
        ) {
            return;
        }

        setInternalCardData(showdownBotCardData);
    }, [showdownBotCardData]);

    // Breakdown State
    const [breakdownType, setBreakdownType] = useState<string>("Stats");

    // Image Generation State
    const [isGeneratingImage, setIsGeneratingImage] = useState<boolean>(false);

    // Mark if isLoading or isGeneratingImage
    const isLoadingOverall = isLoading || isGeneratingImage;

    // Game
    const showGameBoxscore = (): boolean => {
        if (!activeCardData?.latest_game_box_score) return false;
        
        try {
            // Parse the date string without timezone conversion
            const dateStr = activeCardData.latest_game_box_score.date;
            const [year, month, day] = dateStr.split('-').map(Number);
            
            // Create date object in local timezone (no conversion)
            const gameDate = new Date(year, month - 1, day, 12); // month is 0-indexed
            const now = new Date();
            const oneDayAgo = new Date(now.getTime() - (24 * 60 * 60 * 1000)); // 24 hours ago

            return gameDate >= oneDayAgo;
        } catch (error) {
            console.error('Invalid date format:', activeCardData.latest_game_box_score.date);
            return false;
        }
    };

    // --------------------------------
    // MARK: - EFFECTS
    // --------------------------------

    // Flag if image is undefined but data is populated
    const isDataWithoutImage = !activeCardData?.card?.image.output_file_name && activeCardData?.card;

    // Card Calcs
    const cardImagePath: string | null = activeCardData?.card?.image && activeCardData.card.image.output_folder_path && activeCardData.card.image.output_file_name ? `${activeCardData.card.image.output_folder_path}/${activeCardData.card.image.output_file_name}` : null;
    const cardAttributes: Record<string, string | number | null> = activeCardData?.card ? {
        points: `${activeCardData.card.points} PTS`,
        year: activeCardData.card.year,
        expansion: activeCardData.card.image.expansion == "BS" ? null : activeCardData.card.image.expansion,
        edition: activeCardData.card.image.edition == "NONE" ? null : activeCardData.card.image.edition,
        chart_version: activeCardData.card.chart_version == 1 ? null : `CHART ${activeCardData.card.chart_version}`,
        parallel: activeCardData.card.image.parallel == "NONE" ? null : `PARALLEL: ${activeCardData.card.image.parallel}`,
    } : {};
    const weeklyChangePoints = activeCardData?.in_season_trends?.pts_change?.week || null;
    const weeklyChangePointsColor = weeklyChangePoints ? (weeklyChangePoints > 0 ? 'text-green-500' : 'text-red-500') : '';
    const weeklyChangePointsSymbol = weeklyChangePoints ? (weeklyChangePoints > 0 ? '▲' : '▼') : '';

    // Remove the useEffect and move logic to a separate function
    const handleGenerateImage = useCallback(() => {
        if (!activeCardData?.card || isGeneratingImage) return;
        
        console.log("Starting image generation...");
        setIsGeneratingImage(true);
        
        generateCardImage(activeCardData)
            .then((data) => {
                console.log("Received card data with image:", data);
                if (data) {
                    setInternalCardData(data as ShowdownBotCardAPIResponse);
                }
            })
            .catch((error) => {
                console.error("Error generating card image:", error);
            })
            .finally(() => {
                setIsGeneratingImage(false);
            });
    }, [activeCardData, isGeneratingImage]);

    // Use useEffect only to trigger the function once
    useEffect(() => {
        if (isDataWithoutImage && !isGeneratingImage) {
            const timer = setTimeout(() => {
                handleGenerateImage();
            }, 100); // Small delay to prevent rapid calls
            
            return () => clearTimeout(timer);
        }
    }, [isDataWithoutImage, handleGenerateImage, isGeneratingImage]);

    // Changing opacity of color
    const addOpacityToRGB = (rgbColor: string, opacity: number) => {
        // Extract numbers from rgb(r, g, b) format
        const match = rgbColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (match) {
            const [, r, g, b] = match;
            return `rgba(${r}, ${g}, ${b}, ${opacity})`;
        }
        return rgbColor; // fallback if parsing fails
    };

    const teamGlowColor = activeCardData?.card?.image ? (
        ( ['NYM', 'SDP', 'NYY'].includes(activeCardData?.card?.team || '') && isDark )
            ? enhanceColorVisibility(activeCardData?.card?.image?.color_secondary) 
            : enhanceColorVisibility(activeCardData?.card?.image?.color_primary)
    ) : 'rgb(0, 0, 0)';

    // MARK: BREAKDOWN TABLES
    const renderBreakdownTable = () => {
        switch (breakdownType) {
            case 'Stats':
                return (
                    <div className='space-y-2 overflow-y-auto'>
                        <TableRealVsProjected
                            realVsProjectedData={activeCardData?.card?.real_vs_projected_stats || []}
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
                            pointsBreakdownData={activeCardData?.card?.points_breakdown || null}
                            ip={activeCardData?.card?.ip || null}
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
                        chartAccuracyData={activeCardData?.card?.command_out_accuracy_breakdowns || {}}
                    />
                );
            case 'Opponent':
                return (
                    <TableOpponentBreakdown
                        chart={activeCardData?.card?.chart?.opponent}
                    />
                );
        }
    }

    const getBlankPlayerImageName = (): string => {
        const setName = userShowdownSet.toLowerCase() || '2000';
        const appearance = isDark ? 'dark' : 'light';
        return `/images/blank_players/blankplayer-${setName}-${appearance}.png`;
    };

    const breakdownFirstRowHeight = '@xl:max-h-[500px] @xl:overflow-hidden @3xl:max-h-[600px] @6xl:max-h-[700px]';

    // MARK: MAIN CONTENT
    return (
        <div 
            className="
                @container
                w-full
                overflow-visible @2xl:overflow-y-auto
                p-4 space-y-4
                h-full
                pb-24
            "
        >

            {/* Warnings */}
            {activeCardData?.card?.warnings && activeCardData.card.warnings.length > 0 && (
                <div className="bg-[var(--warning)]/5 border-2 border-[var(--warning)] text-[var(--warning)] p-2 rounded-md">
                    <h4 className="font-semibold">Warnings</h4>
                    <ul className="list-disc list-inside">
                        {activeCardData.card.warnings.map((warning, index) => (
                            <li key={index}>{warning}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Name and player attributes */}
            <div className="
                flex flex-wrap items-center
                gap-1 mb-2
            ">
                <a 
                    href={activeCardData?.card?.bref_url || '#'} 
                    className='text-3xl font-black opacity-85 pr-2'
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    {activeCardData?.card?.name.toUpperCase() || ""}
                </a>

                {/* Card Set */}
                {imageForSet(activeCardData?.card?.set || '') && (
                    <img 
                        src={imageForSet(activeCardData?.card?.set || '') || ''}
                        alt={activeCardData?.card?.set || ''}
                        className="inline object-contain align-middle h-7"
                    />
                )}

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
                        { (weeklyChangePoints && key === "points" && String(new Date().getFullYear()) === String(activeCardData?.card?.year || "n/a")) && (
                            <div className={`text-xs ${weeklyChangePointsColor}`}>
                                {weeklyChangePointsSymbol} {Math.abs(weeklyChangePoints)} THIS WEEK
                            </div>
                        )}

                    </div>
                ))}
            </div>

            {/* Game Boxscore */}
            {showGameBoxscore() &&  (
                <GameBoxscore 
                    boxscore={activeCardData?.latest_game_box_score || null} 
                    isLoading={isLoadingGameBoxscore} 
                />
            )}
            

            {/* Image and Breakdown Tables */}
            <div
                className={`
                    grid grid-cols-1 @xl:grid-cols-[11fr_9fr]
                    gap-4
                    pt-2
                `}
            >
                {/* Card Image */}
                <div className={`
                    relative
                    h-auto
                    w-full
                    px-0 @md:px-3 @xl:px-0
                `}>
                    <img
                        src={cardImagePath == null ? getBlankPlayerImageName() : cardImagePath}
                        alt="Blank Player"
                        key={activeCardData?.card?.image.output_file_name || (isDark ? 'blank-dark' : 'blank-light')}
                        className={`
                            block 
                            @2xl:mx-auto
                            ${breakdownFirstRowHeight}
                            rounded-2xl overflow-hidden
                            object-contain
                            fade-in
                            ${isLoadingOverall ? 'blur-xs' : ''}
                        `}
                        style={{
                            boxShadow: activeCardData?.card?.image
                                ? `0 0 10px ${addOpacityToRGB(teamGlowColor, 0.66)},
                                   0 0 20px ${addOpacityToRGB(teamGlowColor, 0.52)},
                                   0 0 40px ${addOpacityToRGB(teamGlowColor, 0.66)},
                                   0 0 80px ${addOpacityToRGB(teamGlowColor, 0.66)}`
                                : `0 0 10px color-mix(in srgb, var(--tertiary) 33%, transparent),
                                   0 0 20px color-mix(in srgb, var(--tertiary) 44%, transparent),
                                   0 0 30px color-mix(in srgb, var(--tertiary) 34%, transparent)`
                       }}
                    /> 

                    {/* Loading Overlay */}
                    {isLoadingOverall && (
                        <div className={`
                            absolute inset-0 
                            flex items-center justify-center 
                        `}>
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
                                    Generating {isGeneratingImage ? 'Image...' : 'Card...'}
                                </p>
                            </div>
                        </div>
                    )}
                </div>            

                {/* Card Tables */}
                <div
                    className={`
                        flex flex-col
                        w-full
                        bg-secondary
                        p-4 rounded-xl
                        space-y-4
                        border-2 border-form-element
                        ${breakdownFirstRowHeight}
                    `}
                >
                    <CustomSelect
                        value={breakdownType}
                        options={[
                            { label: 'Card vs Real Stats', value: 'Stats', icon: <FaPoll /> },
                            { label: 'Points', value: 'Points', icon: <FaCoins /> },
                            { label: 'Chart', value: 'Charts', icon: <FaTable /> },
                            { label: 'Opponent', value: 'Opponent', icon: <FaUser /> }
                        ]}
                        onChange={(value) => setBreakdownType(value)}
                    />

                    {/* Breakdown Table */}
                    {renderBreakdownTable()}

                </div>

            </div>

            {/* Trend Graphs */}
            {!hideTrendGraphs && (
                <div 
                    className="
                        w-full
                        grid grid-cols-1 @xl:grid-cols-2
                        gap-4
                    "
                >
                    <ChartPlayerPointsTrend 
                        title="Career Trends" 
                        trendData={activeCardData?.historical_season_trends?.yearly_trends || null} 
                    />

                    <ChartPlayerPointsTrend 
                        title={activeCardData?.in_season_trends && activeCardData?.card?.year ? `${activeCardData?.card?.year} Card Evolution` : "Year Card Evolution (Available 2020+)"} 
                        trendData={activeCardData?.in_season_trends?.cumulative_trends || null} 
                    />

                </div>
            )}

        </div>
    );
}