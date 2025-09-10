const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";


// --------------------------------
// MARK: - API CALL
// --------------------------------

// Generic type for api
type Primitive = string | number | boolean | File | null | undefined;

/** Sends the entire form (minus File) as JSON to /api/build_custom_card */
export async function buildCustomCard(payload: Record<string, Primitive>) : Promise<ShowdownBotCardAPIResponse> {
    
    // Check if we have a file upload
    const hasFileUpload = payload.image_upload instanceof File;
    
    if (hasFileUpload) {
        // Use FormData for file uploads
        const formData = new FormData();
        
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
            // Don't set Content-Type header - let browser handle it for FormData
            body: formData,
        });
        
        if (!res.ok) throw new Error(`Build failed: ${res.status}`);
        return res.json();
        
    } else {
        // Use existing JSON approach (no file upload)
        const { image_upload, image_source, ...cleaned_data } = payload;
        
        const res = await fetch(`${API_BASE}/build_custom_card`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(cleaned_data),
        });

        // Handle errors
        if (!res.ok) throw new Error(`Build failed: ${res.status}`);

        // Convert to ShowdownBotCardAPIResponse
        return res.json();
    }
}

// --------------------------------
// MARK: - API RESPONSE
// --------------------------------

export type ShowdownBotCardAPIResponse = {

    // Card
    card: ShowdownBotCard | null;

    // Trends
    historical_season_trends?: CareerTrends | null;
    in_season_trends?: InSeasonTrends | null;

    // LIVE GAME
    latest_game_box_score?: GameBoxscore | null;

    // Error
    error: string | null;
    error_for_user: string | null;

};

// --------------------------------
// MARK: - LIVE GAME
// --------------------------------

export type GameBoxscore = {

    // Metadata
    game_pk: number;

    // Game State
    has_game_ended: boolean;

    // Game Date
    date: string;
    date_short: string;

    // Inning
    current_inning_visual: string;
    isTopInning: boolean;
    currentInningOrdinal: string;
    outs: number;
    balls: number;
    strikes: number;

    // Teams
    teams: {
        home: GameBoxscoreTeam;
        away: GameBoxscoreTeam;
    }

    // Offense/Defense
    offense: {
        first?: Record<string, any> | null;
        second?: Record<string, any> | null;
        third?: Record<string, any> | null;
    }

    // Player Summary (Optional)
    game_player_summary?: {
        name: string;
        game_player_summary: string;
    };
    game_player_pts_change?: number | null;
}

export type GameBoxscoreTeam = {
    id: number;
    abbreviation: string;
    color: string;
    runs: number;
    player?: string;
}

// --------------------------------
// MARK: - CARD
// --------------------------------

export type ShowdownBotCard = {
    name: string;
    year: string | number;
    team: string;

    // Bref Info
    bref_id: string;
    bref_url: string;

    // Showdown Attributes
    set: string;
    era: string;
    points: number;
    ip: number | null;
    chart_version: number;

    // Image
    image: ShowdownBotCardImage;

    // Chart
    chart: ShowdownBotCardChart;

    // Tables
    real_vs_projected_stats: RealVsProjectedStat[];
    command_out_accuracy_breakdowns: Record<string, Record<string, ChartAccuracyCategoryBreakdown>>;
    points_breakdown: PointsBreakdown

    // Warnings
    warnings: string[];
};

// --------------------------------
// MARK: - IMAGE
// --------------------------------

/** Stores Showdown Bot Card Image metadata */
type ShowdownBotCardImage = {
    
    expansion: string | null;
    edition: string | null;
    parallel: string | null;

    output_file_name: string;
    output_folder_path: string;

    is_multi_colored: boolean;
    color_primary: string;
    color_secondary: string;
};

// --------------------------------
// MARK: - IMAGE
// --------------------------------

/** Stores Showdown Bot Card Image metadata */
type ShowdownBotCardChart = {
    
    ranges: Record<string, string>;
};

// --------------------------------
// MARK: - POINTS
// --------------------------------

export type PointsBreakdown = {
    allow_negatives: boolean;
    breakdowns: Record<string, PointsCategoryBreakdown>;
    command_out_multiplier: number;
    decay_rate: number;
    decay_start: number;
    ip_multiplier: number;
}

export type PointsCategoryBreakdown = {
    metric: string;
    value: number | null;
    points: number;
    ip_multiplier?: number | null;
    is_desc?: boolean | null;
    percentile?: number | null;
    command_multiplier?: number | null;
}

// --------------------------------
// MARK: - TABLE BREAKDOWNS
// --------------------------------

export type RealVsProjectedStat = {
    stat: string;
    real: number;
    projected: number;
    diff: number;
    diff_str: string;
    precision: number;
    is_real_estimated: boolean;
    is_projected_correction: boolean;
};

/** Shows accuracy breakdown a category (ex: OVERALL, OPS, SLG, OBP) within a command out combination */
export type ChartAccuracyCategoryBreakdown = {
    stat: string;
    accuracy: number;
    actual: number;
    comparison: number;
    is_pitcher: boolean;
    notes: string;
};

// --------------------------------
// MARK: - TREND GRAPHS
// --------------------------------

export type CareerTrends = {
    yearly_trends: Record<string | number, TrendDatapoint>;
}

export type InSeasonTrends = {
    cumulative_trends: Record<string, TrendDatapoint>;
    cumulative_trends_date_aggregation: string;
    pts_change: {
        day?: number;
        week?: number;
        month?: number;
    }
}

export type TrendDatapoint = {

    // Required
    points: number;
    color: string;

    // Shared across types
    year?: string | null;
    team?: string | null;
    hr?: string | null;
    command?: number | null;
    command_type?: string | null;
    outs?: number | null;

    // Type specific

    // Pitching
    ip?: number | null;
    so?: number | null;
    "2b"?: number | null;

    // Hitting
    shOPS_plus?: number | null;
    defense?: string | null;
    speed?: string | null;

    // Added later, not currently included in payload
    // Would be the key of the dict, this is used when converting to array
    x_axis?: string | null;
}