const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";


// --------------------------------
// MARK: - API CALL
// --------------------------------

// Generic type for api
type Primitive = string | number | boolean | null | undefined;

/** Sends the entire form (minus File) as JSON to /build_custom_card */
export async function buildCustomCard(payload: Record<string, Primitive>) : Promise<ShowdownBotCardAPIResponse> {
    
    // Image is sent separately, so we remove it from the payload
    const { image_upload, image_source, ...cleaned_data } = payload;

    // Fetch the API endpoint
    const res = await fetch(`${API_BASE}/build_custom_card`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cleaned_data),
    });

    // Handle errors
    if (!res.ok) throw new Error(`Build failed: ${res.status}`);

    // Convert to ShowdownBotCardAPIResponse
    return res.json();
}

// --------------------------------
// MARK: - API RESPONSE
// --------------------------------

export type ShowdownBotCardAPIResponse = {

    // Card
    card: ShowdownBotCard | null;

    // Trends
    historical_season_trends?: Record<string, TrendDatapoint> | {};
    in_season_trends?: Record<string, TrendDatapoint> | {};

    // Error
    error: string | null;
    error_for_user: string | null;

};

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
    era: string;
    points: number;
    ip: number | null;
    chart_version: number;

    // Image
    image: ShowdownBotCardImage;

    // Tables
    real_vs_projected_stats: RealVsProjectedStat[];
    command_out_accuracy_breakdowns: Record<string, Record<string, ChartAccuracyCategoryBreakdown>>;
    points_breakdown: PointsBreakdown
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

export type TrendDatapoint = {

    // Required
    points: number;
    color: string;

    // Shared across types
    year?: string | null;
    team?: string | null;
    hr?: string | null;
    outs?: number | null;

    // Type specific

    // Pitching
    control?: number | null;
    ip?: number | null;

    // Hitting
    onbase?: number | null;
    "shOPS+"?: number | null;
    defense?: string | null;
    speed?: string | null;

    // Added later, not currently included in payload
    // Would be the key of the dict, this is used when converting to array
    x_axis?: string | null;
}