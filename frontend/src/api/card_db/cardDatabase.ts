/**
 * @fileoverview API client for MLB Showdown card database operations
 * Handles fetching card data
 */

import { type ShowdownBotCard } from '../showdownBotCard';
import { type CardSource } from '../../types/cardSource';

const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// =============================================================================
// MARK: - TYPES & INTERFACES
// =============================================================================

/**
 * Represents a card record from the database with both stats and card data
 */
export type CardDatabaseRecord = {

    // From Stats Archive
    id: string;  // Composite key: {year}-{bref_id}-{(player_type_override)},
    year: number | string;
    bref_id: string;
    name: string;
    player_type: string;
    player_type_override: string;
    is_two_way: boolean;
    primary_positions: string[];
    secondary_positions: string[];
    g: number;
    gs?: number | null;
    pa?: number | null;
    real_ip?: number | null;
    lg_id?: string | null;
    team_id: string;
    team_id_list?: string[] | null;
    team_games_played_dict?: Record<string, number> | null;
    team_override?: string | null;

    // Only exists in WOTC records
    card_data?: ShowdownBotCard | null;

    // Identifiers
    card_id: string;
    card_year: string;
    showdown_set: string;
    showdown_bot_version: string;

    // Set
    expansion?: string | null;
    edition?: string | null;
    set_number?: string | null;

    // Points
    points: number;
    points_estimated: number;
    points_diff_estimated_vs_actual: number;

    // Team
    nationality: string;
    organization: string;
    league: string;
    team: string;
    color_primary?: string | null;
    color_secondary?: string | null;

    // Metadata
    positions_and_defense: any; // JSON object
    positions_and_defense_string: string;
    positions_list: string[];
    ip?: number | null;
    speed?: number | null;
    hand?: string | null;
    speed_letter?: string | null;
    speed_full?: string | null;
    speed_or_ip?: number | null;
    icons_list: string[];

    // Stats
    awards_list: string[];
    is_hof: boolean;
    is_small_sample_size: boolean;
    stat_highlights_list: any; // JSON array

    // Chart
    command: number;
    outs: number;
    is_pitcher: boolean;
    is_chart_outlier: boolean;
    chart_ranges: any; // JSON object
    chart_values: any; // JSON object

    // Card Misc
    is_errata: boolean;
    notes?: string | null;

    // Auto Images
    image_match_type: 'exact' | 'team match' | 'year match' | 'no match';
    image_ids?: string[] | null;

    // Updated
    updated_at: string;

    // Error Message
    error?: string | null;

};

export type TrendingCardRecord = {
    card_data: ShowdownBotCard;
    trending_score: number;
    player_id: string;
    views_last_week: number;
    views_this_week: number;
    wow_change: number;
    wow_percent: number;
};

export type PopularCardRecord = {
    card_data: ShowdownBotCard;
    num_creations: number;
    showdown_set: string;
};

export interface SpotlightCardRecord {
    card_data: ShowdownBotCard;
    spotlight_reason: string;
}

export type CardOfTheDayRecord = {
    card_data: ShowdownBotCard;
    date: string;
};

/**
 * Team hierarchy data structure for organizational filtering.
 * Comes from materialized view in database, helps show only relevant values depending on prior selections.
 */
export interface TeamHierarchyRecord {
    organization: string;
    league: string;
    team: string;
    min_year: number;
    max_year: number;
    cards: number;
}

// =============================================================================
// MARK: - CARD DATA API
// =============================================================================

/**
 * Fetches card database records based on filter criteria
 * 
 * @param source - Source of the card data (CardSource enum)
 * @param payload - Filter parameters (year, team, player name, etc.)
 * @returns Promise resolving to array of card records
 * @throws Error if API request fails
 * 
 * @example
 * ```typescript
 * const cards = await fetchCardData(CardSource.BOT, {
 *   name: 'Aaron Judge',
 *   year: 2023,
 *   team: 'NYY',
 *   showdown_set: '2005'
 * });
 * ```
 */
export async function fetchCardData(source: CardSource, payload: Record<string, any>) : Promise<CardDatabaseRecord[]> {

    const res = await fetch(`${API_BASE}/cards/search`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source, ...payload }),
    });

    // Handle errors
    if (!res.ok) throw new Error(`Build failed: ${res.status}`);

    // Convert to CardDatabaseRecords
    return res.json();
}

export async function fetchTotalCardCount(): Promise<number> {
    const res = await fetch(`${API_BASE}/cards/total_count`, {
        method: "GET",
        headers: {
            'Content-Type': 'application/json',
        }
    });

    // Handle errors
    if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
    
    const data = await res.json();
    return data?.total_count ?? 0;
}

export async function fetchTrendingPlayers(showdownSet: string): Promise<TrendingCardRecord[]> {
    const res = await fetch(`${API_BASE}/cards/trending`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ set: showdownSet }),
    });

    // Handle errors
    if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
    
    const data = await res.json();
    console.log("Trending players data:", data);
    return data?.trending_cards ?? [];
}

export async function fetchPopularCards(showdownSet: string): Promise<PopularCardRecord[]> {
    const res = await fetch(`${API_BASE}/cards/popular`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ set: showdownSet }),
    });
    
    // Handle errors
    if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
    const data = await res.json();
    return data?.popular_cards ?? [];
}

export async function fetchSpotlightCards(showdownSet: string): Promise<SpotlightCardRecord[]> {
    const res = await fetch(`${API_BASE}/cards/spotlight`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ set: showdownSet }),
    });
    
    // Handle errors
    if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
    const data = await res.json();
    return data?.spotlight_cards ?? [];
}

export async function fetchCardOfTheDay(showdownSet: string): Promise<CardOfTheDayRecord | null> {
    const res = await fetch(`${API_BASE}/cards/card_of_the_day`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ set: showdownSet }),
    });
    
    // Handle errors
    if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
    const data = await res.json();
    return data?.card_of_the_day ?? null;
}

// =============================================================================
// MARK: - TEAM HIERARCHY API WITH CACHING
// =============================================================================

// Cache configuration
const HIERARCHY_CACHE_KEY = 'teamHierarchy:v2';
const HIERARCHY_CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Cached hierarchy data structure
 * @private
 */
interface CachedHierarchyData {
    data: TeamHierarchyRecord[];
    timestamp: number;
}

/**
 * Loads team hierarchy from localStorage cache if valid
 * @private
 * @returns Cached data or null if not found/expired
 */
const loadCachedHierarchyData = (): TeamHierarchyRecord[] | null => {
    if (typeof window === 'undefined') return null;
    
    try {
        const cached = localStorage.getItem(HIERARCHY_CACHE_KEY);
        if (!cached) return null;
        
        const { data, timestamp }: CachedHierarchyData = JSON.parse(cached);
        if (Date.now() - timestamp > HIERARCHY_CACHE_DURATION) {
            localStorage.removeItem(HIERARCHY_CACHE_KEY);
            return null;
        }
        
        return data;
    } catch {
        localStorage.removeItem(HIERARCHY_CACHE_KEY);
        return null;
    }
};

/**
 * Saves team hierarchy data to localStorage cache
 * @private
 * @param data - Hierarchy data to cache
 */
const saveCachedHierarchyData = (data: TeamHierarchyRecord[]): void => {
    if (typeof window === 'undefined') return;
    
    try {
        const cachedData: CachedHierarchyData = {
            data,
            timestamp: Date.now()
        };
        localStorage.setItem(HIERARCHY_CACHE_KEY, JSON.stringify(cachedData));
    } catch {
        // Ignore storage errors
    }
};

/**
 * Fetches team hierarchy data with automatic caching
 * 
 * Uses localStorage to cache results for 24 hours to reduce API calls.
 * Falls back to empty array on error to prevent UI breakage.
 * 
 * @returns Promise resolving to array of team hierarchy records
 * 
 * @example
 * ```typescript
 * const teams = await fetchTeamHierarchy();
 * const organizations = [...new Set(teams.map(t => t.organization))];
 * ```
 */
export const fetchTeamHierarchy = async (): Promise<TeamHierarchyRecord[]> => {
    // Try cache first
    const cachedData = loadCachedHierarchyData();
    if (cachedData) {
        console.log('Loaded team hierarchy from cache');
        return cachedData;
    }

    // Fetch from API if not cached
    try {
        const response = await fetch(`${API_BASE}/teams/data`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data: TeamHierarchyRecord[] = await response.json();
        
        // Cache the data
        saveCachedHierarchyData(data);
        
        return data;
    } catch (error) {
        console.error('Error fetching team hierarchy:', error);
        return [];
    }
};