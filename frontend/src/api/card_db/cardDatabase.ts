import { type ShowdownBotCard } from '../showdownBotCard';
const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// MARK: - API Calls

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

// MARK: - Types

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