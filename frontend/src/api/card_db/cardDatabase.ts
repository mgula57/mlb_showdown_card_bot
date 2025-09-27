import { type ShowdownBotCard } from '../showdownBotCard';
const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// MARK: - Card Data

/** Sends the entire form (minus File) as JSON to /api/build_custom_card */
export async function fetchCardData(payload: Record<string, any>) : Promise<CardDatabaseRecord[]> {

    const res = await fetch(`${API_BASE}/cards/data`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    // Handle errors
    if (!res.ok) throw new Error(`Build failed: ${res.status}`);

    // Convert to CardDatabaseRecords
    return res.json();
    
}

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

    // Card
    card_data: ShowdownBotCard | null; // Full card data, nullable if not yet generated

    // From Card Data
    showdown_set: string;
    points: number;
    command: number;
    outs: number;
    nationality: string;
    team: string;
    positions_and_defense_string: string;
    ip?: number | null;
    speed?: number | null;
    speed_letter?: string | null;
    speed_full?: string | null;
    speed_or_ip?: number | null;

    // Error Message
    error?: string | null;

};

// MARK: - Team Hierarchy

export interface TeamHierarchyRecord {
    organization: string;
    league: string;
    team: string;
    min_year: number;
    max_year: number;
    cards: number;
}

const HIERARCHY_CACHE_KEY = 'teamHierarchy:v1';
const HIERARCHY_CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

interface CachedHierarchyData {
    data: TeamHierarchyRecord[];
    timestamp: number;
}

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