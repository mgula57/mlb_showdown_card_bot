/**
 * @fileoverview API client and TypeScript definitions for MLB Stats API integration
 * 
 * This module provides a comprehensive client for interacting with the MLB Stats API,
 * including fetching season data, player statistics, and game information.
 * 
 * 
 * @author Matt Gula
 * @version 4.0
 */

const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";

// ***************************
// API Client Functions
// ***************************
export const fetchSeasons = async (): Promise<Season[]> => {
    const response = await fetch(`${API_BASE}/seasons/list`);
    if (!response.ok) {
        throw new Error(`Failed to fetch seasons: ${response.statusText}`);
    }
    const data = await response.json();
    return data.seasons as Season[];
};

export const fetchSeasonSports = async (season: Season): Promise<Sport[]> => {
    const response = await fetch(`${API_BASE}/seasons/${season.season_id}/sports`);
    if (!response.ok) {
        throw new Error(`Failed to fetch sports for season ${season.season_id}: ${response.statusText}`);
    }
    const data = await response.json();
    return data.sports as Sport[];
}

export const fetchSeasonLeagues = async (season: Season, sport: Sport): Promise<League[]> => {
    const response = await fetch(`${API_BASE}/seasons/${season.season_id}/leagues?sport_id=${sport.id}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch leagues for season ${season.season_id} and sport ${sport.id}: ${response.statusText}`);
    }
    const data = await response.json();
    return data.leagues as League[];
}

export const fetchSeasonStandings = async (season: Season, leagues: League[]): Promise<{ [leagueAbbreviation: string]: Standings[] }> => {
    const standingsEntries = await Promise.all(
        leagues.map(async (league) => {
            const response = await fetch(`${API_BASE}/seasons/${season.season_id}/leagues/${league.id}/standings`);
            if (!response.ok) {
                throw new Error(`Failed to fetch standings for season ${season.season_id} and league ${league.id}: ${response.statusText}`);
            }

            const data = await response.json();
            const leagueKey = league.abbreviation ?? league.name;
            return [leagueKey, data.standings as Standings[]] as const;
        })
    );

    return Object.fromEntries(standingsEntries);
}

// ***************************
// Models
// ***************************

export interface Sport {
    id: number;
    code?: string;
    name?: string;
    abbreviation?: string;
    link?: string;
    sort_order?: number;
    active_status?: boolean;
}

export interface Season {
    season_id: string;
    regular_season_start_date: string;
    season_end_date: string;
}

export interface League {
    id: number;
    name: string;
    abbreviation?: string;
    active: boolean;
}

export interface Division {
    id: number;
    name: string;
    abbreviation?: string;
    name_short?: string;
}

export interface Team {
    id: number;
    name: string;
    abbreviation?: string;
    division?: Division;
    league?: League;
}

export interface Record {
    wins: number;
    losses: number;
    ties?: number;
    percentage?: string;
}

export interface TeamRecords {

    team: Team;
    season: number;

    league_record: Record;
}

export interface Standings {

    standingsType: 'regularSeason' | 'wildCard' | 'divisionLeaders' | 'wildCardWithLeaders' | 'firstHalf' | 'secondHalf' | 'springTraining' | 'postseason' | 'byDivision' | 'byConference' | 'byLeague' | 'byOrganization' | 'currentHalf';
    division?: Division;
    league?: League;
    team_records?: TeamRecords[];
}