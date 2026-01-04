/**
 * @fileoverview API client and TypeScript definitions for MLB Showdown card generation
 * 
 * This module provides:
 * - API functions for building custom cards and generating images
 * - Complete type definitions for card data, charts, statistics, and metadata
 * - Support for file uploads and live game integration
 * 
 * @author Matt Gula
 * @version 4.0
 */

// =============================================================================
// MARK: - CONFIGURATION & CONSTANTS
// =============================================================================

/** Base API URL - switches between production and development environments */
const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// =============================================================================
// MARK: - UTILITY TYPES
// =============================================================================

/** Primitive types accepted by the API payload */
type Primitive = string | number | boolean | File | null | undefined;

// =============================================================================
// MARK: - CARD GENERATION API
// =============================================================================

/**
 * Builds a custom MLB Showdown card with optional image upload
 * 
 * Handles both JSON payloads and multipart form data for file uploads.
 * Automatically detects if an image file is included and uses the appropriate
 * request format.
 * 
 * @param payload - Card generation parameters including player info, year, set, etc.
 * @returns Promise resolving to complete card data with statistics and image
 * @throws Error if API request fails
 * 
 * @example
 * ```typescript
 * // Basic card generation
 * const card = await buildCustomCard({
 *   name: 'Mike Piazza',
 *   year: '1997',
 *   set: '2001'
 * });
 * 
 * // With custom image upload
 * const cardWithImage = await buildCustomCard({
 *   name: 'Mike Piazza',
 *   year: '1997',
 *   set: '2001',
 *   image_upload: fileFromInput
 * });
 * ```
 */
export async function buildCustomCard(payload: Record<string, Primitive>): Promise<ShowdownBotCardAPIResponse> {
    
    // Detect file upload and use appropriate request format
    const hasFileUpload = payload.image_upload instanceof File;
    
    if (hasFileUpload) {
        // Use FormData for file uploads
        const formData = new FormData();
        
        // Add all non-null values to FormData
        Object.keys(payload).forEach(key => {
            const value = payload[key];
            if (value !== null && value !== undefined) {
                if (value instanceof File) {
                    formData.append(key, value);
                } else {
                    formData.append(key, String(value));
                }
            }
        });
        
        const res = await fetch(`${API_BASE}/build_custom_card`, {
            method: "POST",
            // Let browser set Content-Type header for FormData (includes boundary)
            body: formData,
        });
        
        if (!res.ok) {
            throw new Error(`Card build failed: ${res.status} ${res.statusText}`);
        }
        return res.json();
        
    } else {
        // Use JSON for text-only requests (remove unused image fields)
        const { image_upload, image_source, ...cleanedData } = payload;
        
        const res = await fetch(`${API_BASE}/build_custom_card`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(cleanedData),
        });

        if (!res.ok) {
            throw new Error(`Card build failed: ${res.status} ${res.statusText}`);
        }

        return res.json();
    }
}


/**
 * Generates or updates a card image using existing card data
 * 
 * Useful for applying visual changes (parallels, editions, colors) without
 * recalculating statistics. Much faster than full card regeneration.
 * 
 * @param card - Complete card response data from previous generation
 * @returns Promise resolving to updated card data with new image
 * @throws Error if API request fails
 * 
 * @example
 * ```typescript
 * // Generate new image with different parallel
 * const updatedCard = await generateCardImage({
 *   ...existingCard,
 *   card: {
 *     ...existingCard.card,
 *     image: {
 *       ...existingCard.card.image,
 *       parallel: 'foil'
 *     }
 *   }
 * });
 * ```
 */
export async function generateCardImage(card: ShowdownBotCardAPIResponse): Promise<ShowdownBotCardAPIResponse> {
    const res = await fetch(`${API_BASE}/build_image_for_card`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(card),
    });

    if (!res.ok) {
        throw new Error(`Image generation failed: ${res.status} ${res.statusText}`);
    }

    return res.json();
}

// =============================================================================
// MARK: - API RESPONSE TYPES
// =============================================================================

/**
 * Complete API response from card generation endpoints
 * 
 * Contains the generated card data plus optional contextual information
 * like career trends, in-season performance, and live game data.
 */
export type ShowdownBotCardAPIResponse = {
    /** Generated card data, null if generation failed */
    card: ShowdownBotCard | null;

    /** Historical season-by-season performance trends */
    historical_season_trends?: CareerTrends | null;
    
    /** Within-season performance trends for current year */
    in_season_trends?: InSeasonTrends | null;

    /** Live game box score if player is currently playing */
    latest_game_box_score?: GameBoxscore | null;

    /** Technical error message for debugging */
    error: string | null;
    
    /** User-friendly error message for display */
    error_for_user: string | null;
};

// =============================================================================
// MARK: - LIVE GAME DATA TYPES
// =============================================================================

/**
 * Live game box score data for players currently in games
 * 
 * Provides real-time game state, inning information, and player context
 * for generating dynamic card updates during active games.
 */
export type GameBoxscore = {
    /** MLB Game Primary Key identifier */
    game_pk: number;

    /** Whether the game has concluded */
    has_game_ended: boolean;

    /** Full game date (YYYY-MM-DD format) */
    date: string;
    
    /** Shortened date display */
    date_short: string;

    /** Current inning display (e.g., "Top 7th", "Bot 9th") */
    current_inning_visual: string;
    
    /** True if top of inning, false if bottom */
    isTopInning: boolean;
    
    /** Inning ordinal text (e.g., "7th", "9th") */
    currentInningOrdinal: string;
    
    /** Current outs in inning (0-2) */
    outs: number;
    
    /** Current ball count (0-3) */
    balls: number;
    
    /** Current strike count (0-2) */
    strikes: number;

    /** Home and away team information */
    teams: {
        home: GameBoxscoreTeam;
        away: GameBoxscoreTeam;
    };

    /** Base runners (if any) */
    offense: {
        first?: Record<string, any> | null;
        second?: Record<string, any> | null;
        third?: Record<string, any> | null;
    };

    /** Player-specific game summary */
    game_player_summary?: {
        name: string;
        game_player_summary: string;
    };
    
    /** Live point value change based on current game */
    game_player_pts_change?: number | null;
};

/**
 * Team information within a live game box score
 */
export type GameBoxscoreTeam = {
    /** MLB team identifier */
    id: number;
    
    /** Three-letter team abbreviation (e.g., "NYY", "LAD") */
    abbreviation: string;
    
    /** Team's primary color hex code */
    color: string;
    
    /** Current runs scored */
    runs: number;
    
    /** Specific player name (if applicable) */
    player?: string;
};

// =============================================================================
// MARK: - CORE CARD DATA TYPES
// =============================================================================

/**
 * Complete MLB Showdown card data structure
 * 
 * Contains all information needed to display and understand a generated card,
 * including statistics, chart data, accuracy breakdowns, and visual metadata.
 */
export type ShowdownBotCard = {
    /** Player's display name */
    name: string;
    
    /** Season year */
    year: string | number;
    
    /** Team abbreviation */
    team: string;

    // Baseball Reference integration
    /** Baseball Reference player ID */
    bref_id: string;
    
    /** Full Baseball Reference player URL */
    bref_url: string;

    // Core Showdown attributes
    /** Showdown set (e.g., "2001", "2005") */
    set: string;
    
    /** Baseball era classification */
    era: string;
    
    /** Total point value for draft/gameplay */
    points: number;
    
    /** Innings pitched (pitchers only) */
    ip: number | null;
    
    /** Chart generation algorithm version */
    chart_version: number;
    
    /** Speed rating and letter grade */
    speed: Speed;
    
    /** Special ability icons */
    icons: string[];
    
    /** Batting/throwing handedness */
    hand: string;

    // Positional information
    /** "HITTER" or "PITCHER" */
    player_type: string;
    
    /** Formatted positions with defensive ratings */
    positions_and_defense_string: string;

    // Visual presentation
    /** Card image styling and metadata */
    image: ShowdownBotCardImage;

    // Game mechanics
    /** Chart ranges and probabilities */
    chart: ShowdownBotCardChart;

    // Statistical analysis
    /** Comparison of real vs projected statistics */
    real_vs_projected_stats: RealVsProjectedStat[];
    
    /** Detailed accuracy analysis by command/outs combination */
    command_out_accuracy_breakdowns: Record<string, Record<string, ChartAccuracyCategoryBreakdown>>;
    
    /** Point value calculation breakdown */
    points_breakdown: PointsBreakdown;
    points_estimated?: number | null;
    points_estimated_breakdown?: PointsBreakdown | null;

    /** Stats Object */
    stats: Record<string, any>;
    stats_period: StatsPeriod;

    /** Flag indicating if the card is a WOTC card */
    is_wotc?: boolean;

    /** Data quality and edge case warnings */
    warnings: string[];
    notes?: string | null;
};

// =============================================================================
// MARK: - CARD IMAGE & VISUAL TYPES
// =============================================================================

/**
 * Card image styling and metadata
 * 
 * Controls visual appearance including colors, effects, and special editions.
 * Used by the image generation system to create the final card artwork.
 */
export type ShowdownBotCardImage = {
    /** Set expansion identifier */
    expansion: string | null;
    
    /** Special edition type (e.g., "super_season", "cooperstown") */
    edition: string | null;
    
    /** Visual parallel effect (e.g., "foil", "refractor") */
    parallel: string | null;

    /** Generated filename for saved image */
    output_file_name?: string | null;
    
    /** File system path where image is saved */
    output_folder_path?: string | null;

    /** Whether card uses multiple team colors */
    is_multi_colored: boolean;
    
    /** Primary team color (hex code) */
    color_primary: string;
    
    /** Secondary team color (hex code) */
    color_secondary: string;

    /** List of statistics to highlight on card */
    stat_highlights_list?: string[] | null;

    /** Set number within the expansion */
    set_number?: number | null;
};

// =============================================================================
// MARK: - STATS
// =============================================================================

type StatsPeriodType = "REGULAR" | "DATES" | "POST" | "SPLIT";

export type StatsPeriod = {
    /** Type of stats period (e.g., "REGULAR", "DATES") */
    type: StatsPeriodType;

    /** Year or range of years */
    year: string;

    /** Summary of the stats period */
    display_text?: string | null;
}

// =============================================================================
// MARK: - CHART & GAME MECHANICS TYPES
// =============================================================================

/**
 * Showdown card chart data and game mechanics
 * 
 * Contains the core gameplay elements: command rating, outs, and the
 * probability distributions that determine in-game outcomes.
 */
export type ShowdownBotCardChart = {
    /** OnBase/Control rating (higher = better for hitters/pitchers) */
    command: number;
    
    /** Total outs on the card (includes adjustments) */
    outs_full: number;
    
    /** Base outs value */
    outs: number;

    /** Whether this is a pitcher's chart */
    is_pitcher: boolean;

    /** Dice roll ranges for each outcome (e.g., "1-5": "SO") */
    ranges: Record<string, string>;
    
    /** Probability values for each outcome type */
    values: Record<string, number>;

    /** Opponent's chart data (for accuracy calculations) */
    opponent?: ShowdownBotCardChart;
};

// =============================================================================
// MARK: - PLAYER ATTRIBUTES
// =============================================================================

/**
 * Speed rating with numeric value and letter grade
 */
export type Speed = {
    /** Numeric speed rating (typically 10-25) */
    speed: number;
    
    /** Letter grade representation (A, B, C, D, E) */
    letter: string;
};

// =============================================================================
// MARK: - POINTS
// =============================================================================

/**
 * Complete breakdown of how a card's point value is calculated
 * 
 * Shows the contribution of each statistical category and the
 * mathematical formulas used in the point value algorithm.
 */
export type PointsBreakdown = {
    /** Whether negative point contributions are allowed */
    allow_negatives: boolean;
    
    /** Point contributions by statistical category */
    breakdowns: Record<string, PointsCategoryBreakdown>;
    
    /** Multiplier applied to command/outs combination */
    command_out_multiplier: number;
    
    /** Rate at which elite performance value decays */
    decay_rate: number;
    
    /** Point threshold where decay begins */
    decay_start: number;
    
    /** Innings pitched multiplier (pitchers only) */
    ip_multiplier: number;
};

/**
 * Point contribution from a single statistical category
 */
export type PointsCategoryBreakdown = {
    /** Statistical category name */
    metric: string;
    
    /** Player's actual value in this category */
    value: number | null;
    
    /** Points contributed by this category */
    points: number;
    
    /** Innings pitched adjustment (pitchers only) */
    ip_multiplier?: number | null;
    
    /** Whether higher values are better (descending sort) */
    is_desc?: boolean | null;
    
    /** Player's percentile rank in this category */
    percentile?: number | null;
    
    /** Command rating adjustment factor */
    command_multiplier?: number | null;
};

// =============================================================================
// MARK: - PROJECTION TYPES
// =============================================================================

/**
 * Comparison between real player statistics and projected card performance
 * 
 * Shows how accurately the generated card would reproduce the player's
 * actual statistical performance in simulated games.
 */
export type RealVsProjectedStat = {
    /** Statistical category name (e.g., "OBP", "SLG", "HR") */
    stat: string;
    
    /** Player's actual statistical value */
    real: number;
    
    /** Card's projected statistical value */
    projected: number;
    
    /** Numerical difference (projected - real) */
    diff: number;
    
    /** Formatted difference string with sign */
    diff_str: string;
    
    /** Decimal precision for display */
    precision: number;
    
    /** Whether real value is estimated (limited data) */
    is_real_estimated: boolean;
    
    /** Whether projection includes accuracy corrections */
    is_projected_correction: boolean;
};

/**
 * Accuracy breakdown for a specific statistical category and command/outs combination
 * 
 * Used to evaluate how well different chart configurations match real performance
 * across various statistical measures (overall accuracy, OPS, SLG, OBP, etc.).
 */
export type ChartAccuracyCategoryBreakdown = {
    /** Statistical category being analyzed */
    stat: string;
    
    /** Accuracy percentage (0-100) */
    accuracy: number;
    
    /** Actual player value */
    actual: number;
    
    /** Comparison/projected value */
    comparison: number;
    
    /** Whether this is for a pitcher's chart */
    is_pitcher: boolean;
    
    /** Additional context or explanatory notes */
    notes: string;
};

// =============================================================================
// MARK: - PERFORMANCE TRENDS
// =============================================================================

/**
 * Historical career performance trends across multiple seasons
 * 
 * Contains year-by-year data points showing how a player's Showdown
 * card values would have changed throughout their career.
 */
export type CareerTrends = {
    /** Performance data keyed by year */
    yearly_trends: Record<string | number, TrendDatapoint>;
};

/**
 * Within-season performance trends for the current year
 * 
 * Shows how a player's card values change throughout the season
 * as statistics accumulate, useful for mid-season card updates.
 */
export type InSeasonTrends = {
    /** Cumulative performance data by time period */
    cumulative_trends: Record<string, TrendDatapoint>;
    
    /** Time aggregation method ("daily", "weekly", "monthly") */
    cumulative_trends_date_aggregation: string;
    
    /** Recent point value changes by time period */
    pts_change: {
        day?: number;
        week?: number;
        month?: number;
    };
};

/**
 * Individual data point in a performance trend analysis
 * 
 * Contains the core metrics and contextual information for a specific
 * time period (season, month, etc.) in a player's career.
 */
export type TrendDatapoint = {
    // Core required fields
    /** Point value for this time period */
    points: number;
    
    /** Display color for charts/graphs */
    color: string;

    // Common contextual information
    /** Season year */
    year?: string | null;
    
    /** Team abbreviation */
    team?: string | null;
    
    /** Home runs (for reference) */
    hr?: string | null;
    
    /** Command/Control rating */
    command?: number | null;
    
    /** Command type ("OnBase" or "Control") */
    command_type?: string | null;
    
    /** Outs rating */
    outs?: number | null;

    // Pitcher-specific metrics
    /** Innings pitched */
    ip?: number | null;
    
    /** Strikeouts */
    so?: number | null;
    
    /** Doubles */
    "2b"?: number | null;

    // Hitter-specific metrics
    /** Showdown OPS+ rating */
    shOPS_plus?: number | null;
    
    /** Defensive rating string */
    defense?: string | null;
    
    /** Speed rating string */
    speed?: string | null;

    // Chart/display metadata
    /** X-axis value for chart display (derived from record key) */
    x_axis?: string | null;
};