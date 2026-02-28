/**
 * @fileoverview CardDetail - Comprehensive card display and analysis component
 * 
 * This component provides a detailed view of generated MLB Showdown cards including:
 * - Full card visualization with dynamic styling
 * - Statistical analysis tables (real vs projected, accuracy breakdowns)
 * - Performance trends and historical data
 * - Live game integration when applicable
 * - Interactive table switching and customization options
 */

import { useState, useEffect } from 'react';
import { useTheme, useSiteSettings } from "../shared/SiteSettingsContext";
import CustomSelect from '../shared/CustomSelect';
import { FaTable, FaPoll, FaCoins, FaBaseballBall, FaUser } from 'react-icons/fa';
import { type ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';
import { enhanceColorVisibility } from '../../functions/colors';

import { imageForSet } from "../shared/SiteSettingsContext";

// Statistical analysis tables
import { TableRealVsProjected } from './TableRealVsProjectedBreakdown';
import { TableChartsBreakdown } from './TableChartsBreakdown';
import { TablePointsBreakdown } from './TablePointsBreakdown';
import { TableOpponentBreakdown } from './TableOpponentBreakdown';

// API integration
import { generateCardImage, fetchCardById } from '../../api/showdownBotCard';

// Performance visualization
import ChartPlayerPointsTrend from './ChartPlayerPointsTrend';

// Live game integration
import { GameBoxscore } from '../games/GameBoxscore';

/**
 * Props for the CardDetail component
 */
type CardDetailProps = {
    /** Complete card data with statistics and analysis */
    showdownBotCardData?: ShowdownBotCardAPIResponse | null;
    /** Card Id is passed in when loading from search */
    cardId?: string;
    /** Whether to hide trend graphs (optional for mobile/compact views) */
    hideTrendGraphs?: boolean;
    /** Loading state for the main card data */
    isLoading?: boolean;
    /** Loading state for live game data */
    isLoadingGameBoxscore?: boolean;
    /** Usage context: 'custom' for card builder, 'explore' for database browser */
    context?: 'custom' | 'explore' | 'home' | 'season' | 'roster';
    parent?: string;
};

/**
 * CardDetail - Comprehensive card display and analysis component
 * 
 * Provides a complete view of generated MLB Showdown cards with interactive
 * analysis tools. Features include:
 * 
 * - **Card Visualization**: Full card display with team colors and styling
 * - **Statistical Analysis**: Multiple comparison tables showing accuracy
 * - **Performance Trends**: Historical and seasonal performance graphs
 * - **Live Integration**: Real-time game data when applicable
 * - **Interactive Tables**: Switchable views for different analysis types
 * 
 * The component adapts its layout and features based on the usage context
 * and available data, providing both casual browsing and deep analysis capabilities.
 * 
 * @param showdownBotCardData - Complete card API response with all data
 * @param hideTrendGraphs - Hide trend charts for compact layouts
 * @param isLoading - Main loading state
 * @param isLoadingGameBoxscore - Live game data loading state
 * @param context - Usage context affecting available features
 * 
 * @example
 * ```tsx
 * <CardDetail 
 *   showdownBotCardData={cardResponse}
 *   context="explore"
 *   hideTrendGraphs={isMobile}
 * />
 * ```
 */
export function CardDetail({ showdownBotCardData, cardId, isLoading, isLoadingGameBoxscore, hideTrendGraphs=false, context='custom', parent }: CardDetailProps) {

    // =============================================================================
    // MARK: STATES
    // =============================================================================

    /**
     * Internal card data state for handling dynamic updates
     * Allows component to maintain its own copy for features like image regeneration
     */
    const [internalCardData, setInternalCardData] = useState<ShowdownBotCardAPIResponse | null | undefined>(showdownBotCardData);
    const [internalCardId, setInternalCardId] = useState<string | undefined>(cardId);
    
    // Use internal state when available, fallback to prop
    const activeCardData = internalCardData || showdownBotCardData;

    // Theme and settings
    const { isDark } = useTheme();
    const { userShowdownSet } = useSiteSettings();

    /**
     * Sync internal state with prop changes
     * Ensures component reflects updates from parent while maintaining ability
     * to handle local updates (like image regeneration)
     */
    useEffect(() => {
        // Case 1: New data provided via prop
        if (showdownBotCardData && showdownBotCardData.card) {
            // Skip if same card (by bref_id + year + set)
            const isSameCard = 
                context !== 'custom' &&
                (
                    internalCardData?.card?.bref_id === showdownBotCardData?.card?.bref_id &&
                    internalCardData?.card?.year === showdownBotCardData?.card?.year &&
                    internalCardData?.card?.set === showdownBotCardData?.card?.set
                );
            console.log("CardDetail: Checking for prop data update, isSameCard =", isSameCard);
            if (!isSameCard) {
                setInternalCardData(showdownBotCardData);
                setInternalCardId(cardId);

                // Load image if necessary
                const isDataWithoutImage = !showdownBotCardData.card?.image.output_file_name && showdownBotCardData.card;
                if (isDataWithoutImage && !isGeneratingImage) {
                    console.log("Generating image for new prop data...");
                    handleGenerateImage(showdownBotCardData);
                }            
                return;
            }
        }

        // Case 2: No data but cardId provided - fetch it from DB
        if (cardId && cardId !== internalCardId) {
            setIsLoadingFromId(true);
            fetchCardById(cardId, 'card-detail')
                .then((data) => {
                    console.log("Fetched single card data by ID:", data);
                    if (data) {
                        const cardResponse = data as ShowdownBotCardAPIResponse;
                        setInternalCardId(cardId);
                        
                        // Load image if necessary
                        const isDataWithoutImage = !cardResponse.card?.image.output_file_name && cardResponse.card;
                        if (isDataWithoutImage && !isGeneratingImage) {
                            handleGenerateImage(cardResponse);
                        } else {
                            setInternalCardData(cardResponse);
                        }                        
                    }
                })
                .catch((error) => {
                    console.error("Error fetching card by ID:", error);
                })
                .finally(() => {
                    setIsLoadingFromId(false);
                });
            
            return;
        }

    }, [showdownBotCardData, cardId]);

    // Breakdown State
    const [breakdownType, setBreakdownType] = useState<string>("Stats");

    // Image Generation State
    const [isGeneratingImage, setIsGeneratingImage] = useState<boolean>(false);
    const [isLoadingFromId, setIsLoadingFromId] = useState<boolean>(false);

    // Mark if isLoading or isGeneratingImage
    const isLoadingOverall = isLoading || isGeneratingImage || isLoadingFromId;

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

    // Card Calcs
    const cardImagePath: string | null = activeCardData?.card?.image && activeCardData.card.image.output_folder_path && activeCardData.card.image.output_file_name ? `${activeCardData.card.image.output_folder_path}/${activeCardData.card.image.output_file_name}` : null;
    const cardAttributes: Record<string, string | number | null> = activeCardData?.card ? {
        points: `${activeCardData.card.points} PTS`,
        year: activeCardData.card.year,
        stats_period_summary: activeCardData.card.stats_period.type !== "REGULAR" ? activeCardData.card.stats_period.display_text || null : null,
        expansion: activeCardData.card.image.expansion == "BS" ? null : activeCardData.card.image.expansion,
        edition: activeCardData.card.image.edition == "NONE" || activeCardData.card.image.edition == undefined ? null : activeCardData.card.image.edition,
        chart_version: activeCardData.card.chart_version === 1 || activeCardData.card.chart_version == undefined ? null : `CHART ${activeCardData.card.chart_version}`,
        parallel: activeCardData.card.image.parallel == "NONE" || activeCardData.card.image.parallel == undefined ? null : `PARALLEL: ${activeCardData.card.image.parallel}`,
        is_errata: activeCardData.card.is_errata ? 'ERRATA' : null,
    } : {};
    var weeklyChangePoints = activeCardData?.in_season_trends?.pts_change?.week || null;
    const isThisYearBeforeOct8th = activeCardData?.card?.year === String(new Date().getFullYear()) && (new Date().getMonth() < 9 || (new Date().getMonth() === 9 && new Date().getDate() < 8));
    if (isThisYearBeforeOct8th === false) {
        weeklyChangePoints = null; // Only show for current year cards
    }
    const weeklyChangePointsColor = weeklyChangePoints ? (weeklyChangePoints > 0 ? 'text-green-500' : 'text-red-500') : '';
    const weeklyChangePointsSymbol = weeklyChangePoints ? (weeklyChangePoints > 0 ? '▲' : '▼') : '';

    // Handle Image Generation
    const handleGenerateImage = (data: ShowdownBotCardAPIResponse) => {
        if (!data?.card || isGeneratingImage || context === 'custom') return;
        
        console.log("Starting image generation...", parent);
        setIsGeneratingImage(true);
        
        generateCardImage(data)
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
    };

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
        ( ['NYM', 'SDP', 'NYY'].includes(activeCardData?.card?.team || '') && isDark && !activeCardData.card.wbc_team)
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
                            isWotc={activeCardData?.card?.is_wotc || false}
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
        const setName = userShowdownSet.toLowerCase() || '2001';
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
                <div className="bg-(--warning)/5 border-2 border-(--warning) text-(--warning) p-2 rounded-md">
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

            {/* Notes */}
            {activeCardData?.card?.notes && (
                <div className="
                    bg-(--secondary)/50
                    border-2 border-(--form-element)
                    rounded-lg
                    p-3
                    text-xs
                ">
                    {activeCardData.card.notes}
                </div>
            )}

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
                        ${isLoadingFromId ? 'blur-xs' : ''}
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