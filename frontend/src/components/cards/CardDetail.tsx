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

import { useState, useEffect, memo, type CSSProperties } from 'react';
import { useTheme, useSiteSettings } from "../shared/SiteSettingsContext";
import { FaBaseballBall } from 'react-icons/fa';
import { type ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';
import { enhanceColorVisibility } from '../../functions/colors';

import { imageForSet } from "../shared/SiteSettingsContext";

// Chart accuracy table (kept as table — compact and precise)
import { ChartSelectionBreakdown } from './card_detail/ChartSelectionBreakdown';
import { BaselineOpponentBreakdown } from './card_detail/BaselineOpponentBreakdown';

// API integration
import { generateCardImage, fetchCardById, fetchSeasonStatRanges } from '../../api/showdownBotCard';

// Performance visualization
import ChartPlayerPointsTrend from './card_detail/ChartPlayerPointsTrend';

// Live game integration
import GameItem from '../games/GameItem';

// Visual breakdown panels
import OutcomeProbability from './card_detail/OutcomeProbability';
import RealVsProjectedVisual from './card_detail/RealVsProjectedVisual';
import PercentileGaugesPanel from './card_detail/PercentileGaugesPanel';
import PointsContributionBars from './card_detail/PointsContributionBars';
import { CardComps } from './card_detail/CardComps';

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
    /** Usage context: 'custom' for card builder, 'explore' for database browser */
    context?: 'custom' | 'explore' | 'home' | 'season' | 'roster' | 'game_detail';
    parent?: string;
};

const SectionPanel = ({ title, subtitle, isLoading, children }: { title: string; subtitle?: string; isLoading?: boolean; children: React.ReactNode }) => (
    <div className={`bg-secondary rounded-xl p-4 border-2 border-form-element space-y-3 overflow-y-scroll ${isLoading ? 'blur-xs' : ''}`}>
        <div className="flex flex-col gap-0.5">
            <div className="text-[12px] font-semibold opacity-40 uppercase tracking-widest">{title}</div>
            {subtitle && <div className="text-[10px] font-semibold opacity-30 uppercase tracking-widest">{subtitle}</div>}
        </div>
        {children}
    </div>
);

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
export const CardDetail = memo(function CardDetail({ showdownBotCardData, cardId, isLoading, hideTrendGraphs=false, context='custom', parent }: CardDetailProps) {

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

    // Extras when card is loaded - stat ranges for real vs projected table
    const [seasonStatRanges, setSeasonStatRanges] = useState<Record<string, { min: number; max: number }> | null>(null);
    const [isRangesLoading, setIsRangesLoading] = useState(false);

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
                    (internalCardData?.card?.bref_id || internalCardData?.card?.mlb_id) === (showdownBotCardData?.card?.bref_id || showdownBotCardData?.card?.mlb_id) &&
                    internalCardData?.card?.year === showdownBotCardData?.card?.year &&
                    internalCardData?.card?.set === showdownBotCardData?.card?.set
                );
            console.log("CardDetail: Checking for prop data update, isSameCard =", isSameCard);
            if (!isSameCard) {
                setInternalCardData(showdownBotCardData);
                setInternalCardId(cardId);

                // Load image if necessary
                console.log("Image Output Filename:", showdownBotCardData.card);
                const isDataWithoutImage = !showdownBotCardData.card?.image.output_file_name && showdownBotCardData.card;
                if (isDataWithoutImage && !isGeneratingImage) {
                    console.log("Generating image for new prop data...");
                    handleGenerateImage(showdownBotCardData);
                }
                
                // Fetch season stat ranges for real vs projected table if not already present
                if (showdownBotCardData.card) {
                    const maxYear = Math.max(...(showdownBotCardData.card.stats_period.year_list || []));
                    setIsRangesLoading(true);
                    setSeasonStatRanges(null);
                    fetchSeasonStatRanges(maxYear, showdownBotCardData.card.player_type.toUpperCase() as "HITTER" | "PITCHER")
                        .then((response) => {
                            console.log("Fetched season stat ranges:", response);
                            setSeasonStatRanges(response?.ranges ?? null);
                        })
                        .catch((error) => {
                            console.error("Error fetching season stat ranges:", error);
                        })
                        .finally(() => {
                            setIsRangesLoading(false);
                        });
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
            const dateStr = activeCardData.latest_game_box_score.datetime.official_date || "1970-01-01";
            const [year, month, day] = dateStr.split('-').map(Number);
            
            // Create date object in local timezone (no conversion)
            const gameDate = new Date(year, month - 1, day, 12); // month is 0-indexed
            const now = new Date();
            const oneDayAgo = new Date(now.getTime() - (24 * 60 * 60 * 1000)); // 24 hours ago

            return gameDate >= oneDayAgo;
        } catch (error) {
            console.error('Invalid date format:', activeCardData.latest_game_box_score.datetime.official_date);
            return false;
        }
    };

    // --------------------------------
    // MARK: - EFFECTS
    // --------------------------------

    // Card Calcs
    const image = activeCardData?.card?.image ?? null;
    const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
    const cardImagePath: string | null = image?.storage_path
        ? `${supabaseUrl}/storage/v1/object/public/card_images/${image.storage_path}`
        : image?.output_folder_path && image?.output_file_name
            ? `${image.output_folder_path}/${image.output_file_name}`
            : null;
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
    const isValidStatsPeriodType = activeCardData?.card?.stats_period && ['REGULAR', 'PRESEASON', 'POSTSEASON'].includes(activeCardData.card.stats_period.type);
    if (isThisYearBeforeOct8th === false || !isValidStatsPeriodType) {
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

    // Team colors for visual panels (NYM/SDP swap for better contrast)
    const team = activeCardData?.card?.wbc_team || activeCardData?.card?.team;
    const rawPrimary = activeCardData?.card?.image.color_primary || 'rgb(0,0,0)';
    const rawSecondary = activeCardData?.card?.image.color_secondary || 'rgb(0,0,0)';
    const mechPrimaryColor = ['NYM', 'SDP'].includes(team || '') ? rawSecondary : rawPrimary;
    const mechSecondaryColor = ['NYM', 'SDP'].includes(team || '') ? rawPrimary : rawSecondary;

    const getBlankPlayerImageName = (): string => {
        const setName = userShowdownSet.toLowerCase() || '2001';
        const appearance = isDark ? 'dark' : 'light';
        return `/images/blank_players/blankplayer-${setName}-${appearance}.png`;
    };

    const cardImageMaxHeight = '@xl:max-h-[600px] @xl:overflow-hidden @3xl:max-h-[700px]';

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
                    {/* Game Boxscore — on mobile sits above card, hidden here on xl (shown in right col) */}
                    {showGameBoxscore() && activeCardData?.latest_game_box_score && (
                        <div className='@xl:hidden mb-3'>
                            <GameItem
                                game={activeCardData.latest_game_box_score}
                                playerIdForLinescoreHighlight={activeCardData?.card?.mlb_id ?? undefined}
                            />
                        </div>
                    )}
                    <img
                        src={cardImagePath == null ? getBlankPlayerImageName() : cardImagePath}
                        alt="Blank Player"
                        key={activeCardData?.card?.image.output_file_name || (isDark ? 'blank-dark' : 'blank-light')}
                        className={`
                            block
                            @2xl:mx-auto
                            ${cardImageMaxHeight}
                            rounded-2xl overflow-hidden
                            object-contain
                            fade-in
                            ${isLoadingOverall ? 'blur-xs' : ''}
                            ${activeCardData?.card?.image ? 'card-glow-pulse' : ''}
                        `}
                        style={activeCardData?.card?.image ? {
                            '--card-glow-lo': addOpacityToRGB(teamGlowColor, 0.52),
                            '--card-glow-md': addOpacityToRGB(teamGlowColor, 0.66),
                            '--card-glow-hi': addOpacityToRGB(teamGlowColor, 0.85),
                        } as CSSProperties : {
                            boxShadow: `0 0 10px color-mix(in srgb, var(--tertiary) 33%, transparent),
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

                {/* Right column */}
                <div className={`flex flex-col gap-3 ${cardImageMaxHeight}`}>
                    {/* Game Boxscore — desktop only */}
                    {showGameBoxscore() && activeCardData?.latest_game_box_score && (
                        <div className='hidden @xl:block'>
                            <GameItem
                                game={activeCardData.latest_game_box_score}
                                playerIdForLinescoreHighlight={activeCardData?.card?.mlb_id ?? undefined}
                            />
                        </div>
                    )}

                    {/* Card vs Real Stats */}
                    <SectionPanel isLoading={isLoadingOverall} title="Card vs Real Stats" subtitle='Compares projected card outcomes vs real stats'>
                            
                        <RealVsProjectedVisual
                            realVsProjectedData={activeCardData?.card?.real_vs_projected_stats}
                            statRanges={seasonStatRanges}
                            isLoading={isRangesLoading}
                            playerType={activeCardData?.card?.player_type?.toUpperCase() as 'HITTER' | 'PITCHER'}
                        />
                        <div className="flex flex-col text-[10px] opacity-40 space-y-0.5 pt-1">
                            <i>* Real stat is estimated (limited data, adjusted era, etc.)</i>
                            <i>** Projection includes post-processing accuracy correction</i>
                        </div>
                    </SectionPanel>

                </div>{/* end right column */}

            </div>

            {/* Below-fold grid: analysis panels + trend graphs */}
            <div className="w-full grid grid-cols-1 @xl:grid-cols-2 gap-4">

                {/* Points Breakdown */}
                {!activeCardData?.card?.is_wotc && (
                    <SectionPanel isLoading={isLoadingOverall} title="Points Breakdown">
                        <PointsContributionBars
                            pointsBreakdownData={activeCardData?.card?.points_breakdown}
                            ip={activeCardData?.card?.ip}
                        />
                        <i className="text-[10px] opacity-40">* Slashlines/HR projections based on Steroid Era opponent.</i>
                    </SectionPanel>
                )}

                {/* Chart Accuracy */}
                {!activeCardData?.card?.is_wotc && (
                    <SectionPanel isLoading={isLoadingOverall} title={`Chart Selection - Version ${activeCardData?.card?.chart_version || '1'}`}>
                        <ChartSelectionBreakdown
                            chartAccuracyData={activeCardData?.card?.command_out_accuracy_breakdowns}
                            commandOutAccuraciesData={activeCardData?.card?.command_out_accuracies}
                            selectedChartVersion={activeCardData?.card?.chart_version || 1}
                        />
                    </SectionPanel>
                )}

                {/* Opponent Breakdown */}
                <SectionPanel 
                    isLoading={isLoadingOverall} 
                    title="Baseline Opponent"
                    subtitle={`The avg opposing pitcher/hitter used to create the card. Adjusted to reflect run scoring environment of the ${activeCardData?.card?.era}`}
                >
                    <BaselineOpponentBreakdown
                        chart={activeCardData?.card?.chart?.opponent}
                        primaryColor={mechPrimaryColor}
                        secondaryColor={mechSecondaryColor}
                    />
                </SectionPanel>

                {/* Outcome Distribution */}
                <SectionPanel isLoading={isLoadingOverall} title="Outcome Probabilities" subtitle="Use baseline or search for a specific opponent">
                    <OutcomeProbability
                        chart={activeCardData?.card?.chart}
                        primaryColor={mechPrimaryColor}
                        secondaryColor={mechSecondaryColor}
                        set={activeCardData?.card?.set}
                    />
                </SectionPanel>                

                {/* Trend Graphs */}
                {!hideTrendGraphs && (
                    <>
                        <SectionPanel isLoading={isLoadingOverall} title="Career Trends">
                            <ChartPlayerPointsTrend
                                title="Career Trends"
                                trendData={activeCardData?.historical_season_trends?.yearly_trends || null}
                            />
                        </SectionPanel>
                        <SectionPanel isLoading={isLoadingOverall} title={activeCardData?.in_season_trends && activeCardData?.card?.year ? `${activeCardData?.card?.year} Card Evolution` : "Year Card Evolution (Available 2020+)"}>
                            <ChartPlayerPointsTrend
                                title={activeCardData?.in_season_trends && activeCardData?.card?.year ? `${activeCardData?.card?.year} Card Evolution` : "Year Card Evolution (Available 2020+)"}
                                trendData={activeCardData?.in_season_trends?.cumulative_trends || null}
                            />
                        </SectionPanel>
                    </>
                )}

                {/* Most Similar WOTC Cards */}
                <SectionPanel
                    isLoading={isLoadingOverall}
                    title="Most Similar WOTC Cards"
                    subtitle={`Top matches by chart similarity`}
                >
                    <CardComps
                        card={activeCardData?.card ?? null}
                        isLoading={isLoadingOverall}
                    />
                </SectionPanel>

            </div>

        </div>
    );
});