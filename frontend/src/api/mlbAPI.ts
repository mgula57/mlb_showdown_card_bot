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

import { type ShowdownBotCard, type ShowdownBotCardCompact } from "./showdownBotCard";

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

export const fetchSeasonStandings = async (season: Season, leagues: League[], showdownSet?: string): Promise<{ [leagueAbbreviation: string]: Standings[] }> => {
    const standingsEntries = await Promise.all(
        leagues.map(async (league) => {
            const response = await fetch(`${API_BASE}/seasons/${season.season_id}/leagues/${league.id}/standings${showdownSet ? `?showdown_set=${showdownSet}` : ''}`);
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

export const fetchSeasonTeams = async (season: Season, league: League, sportId: number): Promise<Team[]> => {
    const response = await fetch(`${API_BASE}/seasons/${season.season_id}/teams?league_id=${league.id}&sport_id=${sportId}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch teams for season ${season.season_id} and league ${league.id}: ${response.statusText}`);
    }
    const data = await response.json();
    return data.teams as Team[];
}

export const fetchTeamRoster = async (season: Season, teamId: number, rosterType: string, showdownSet: string, sportId: number, teamAbbr: string): Promise<Roster> => {
    const response = await fetch(`${API_BASE}/seasons/${season.season_id}/teams/${teamId}/roster?roster_type=${rosterType}&showdown_set=${showdownSet}&sport_id=${sportId}&team_abbr=${teamAbbr}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch roster for season ${season.season_id} and team ${teamId}: ${response.statusText}`);
    }
    const data = await response.json();
    return data.roster as Roster;
}

const getUserTimeZone = (): string => Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/New_York';

const getDateInTimeZone = (timeZone: string): string => {
    const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    });
    const parts = formatter.formatToParts(new Date());
    const year = parts.find((part) => part.type === 'year')?.value;
    const month = parts.find((part) => part.type === 'month')?.value;
    const day = parts.find((part) => part.type === 'day')?.value;

    if (!year || !month || !day) {
        return new Date().toISOString().split('T')[0];
    }

    return `${year}-${month}-${day}`;
};

export const fetchSchedule = async (sportId: number, season: Season, date?: string, league?: League, showdownSet?: string): Promise<Schedule> => {
    var url = `${API_BASE}/schedule?season=${season.season_id}&sport_id=${sportId}`;
    const userTimeZone = getUserTimeZone();
    url += `&tz_name=${encodeURIComponent(userTimeZone)}`;
    if (date) {
        url += `&date=${encodeURIComponent(date)}`;
    }
    if (league) {
        url += `&league_id=${encodeURIComponent(league.id.toString())}`;
    }
    if (showdownSet) {
        url += `&showdown_set=${encodeURIComponent(showdownSet)}`;
    }
    url += `&include_probable_pitchers=true`;
    url += `&include_linescore=true`;
    url += `&include_decisions=true`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Failed to fetch games for season ${season.season_id}: ${response.statusText}`);
    }
    const data = await response.json();
    return data.schedule as Schedule;
}

export const fetchTodaysSchedule = async (sportId: number, season: Season, league?: League, showdownSet?: string): Promise<Schedule> => {
    const userTimeZone = getUserTimeZone();
    const today = getDateInTimeZone(userTimeZone);
    return fetchSchedule(sportId, season, today, league, showdownSet);
}

export const fetchGameBoxscore = async (gamePk: number): Promise<GameBoxscoreDetail> => {
    const response = await fetch(`${API_BASE}/game/${gamePk}/boxscore`);
    if (!response.ok) {
        throw new Error(`Failed to fetch boxscore for game ${gamePk}: ${response.statusText}`);
    }
    return (await response.json()) as GameBoxscoreDetail;
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
    team_code?: string;

    season?: number | string;
    division?: Division;
    league?: League;

    active?: boolean;

    primary_color?: string;
    secondary_color?: string;
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
    
    // Optional Showdown Card Data
    showdown_points?: number;
}

export interface Standings {

    standingsType: 'regularSeason' | 'wildCard' | 'divisionLeaders' | 'wildCardWithLeaders' | 'firstHalf' | 'secondHalf' | 'springTraining' | 'postseason' | 'byDivision' | 'byConference' | 'byLeague' | 'byOrganization' | 'currentHalf';
    division?: Division;
    league?: League;
    team_records?: TeamRecords[];
}

export type GameType =
    | 'S' // Spring Training
    | 'R' // Regular Season
    | 'F' // Wild Card
    | 'D' // Division Series
    | 'L' // League Championship Series
    | 'W' // World Series
    | 'C' // Championship
    | 'N' // Nineteenth Century Series
    | 'P' // Playoffs
    | 'A' // All-Star Game
    | 'I' // Intrasquad
    | 'E'; // Exhibition

export interface GameStatus {
    abstract_game_state?: string;
    coded_game_state?: string;
    detailed_state?: string;
    status_code?: string;
    start_time_tbd?: boolean;
    abstract_game_code?: string;
}

export interface GameLeagueRecord {
    wins?: number;
    losses?: number;
    pct?: string;
}

export interface GameTeamLine {
    team?: Team;
    league_record?: GameLeagueRecord;
    score?: number;
    is_winner?: boolean;
    split_squad?: boolean;
    series_number?: number;

    probable_pitcher?: {
        id?: number;
        full_name?: string;
        link?: string;

        card?: ShowdownBotCardCompact;
    }
}

export interface GameTeams {
    away?: GameTeamLine;
    home?: GameTeamLine;
}

export interface GameVenue {
    id: number;
    name?: string;
    link?: string;
}

export interface GameContent {
    link?: string;
}

export interface GameLinescoreStatLine {
    runs?: number;
    hits?: number;
    errors?: number;
    left_on_base?: number;
}

export interface GameLinescoreInning {
    num?: number;
    ordinal_num?: string;
    home?: GameLinescoreStatLine;
    away?: GameLinescoreStatLine;
}

export interface GameLinescoreTeams {
    home?: GameLinescoreStatLine;
    away?: GameLinescoreStatLine;
}

export interface GameLinescorePerson {
    id?: number;
    full_name?: string;
    link?: string;
    card?: ShowdownBotCardCompact;
}

export interface GameLinescoreTeamRef {
    id?: number;
    name?: string;
    link?: string;
}

export interface GameLinescoreAlignment {
    pitcher?: GameLinescorePerson;
    catcher?: GameLinescorePerson;
    first?: GameLinescorePerson;
    second?: GameLinescorePerson;
    third?: GameLinescorePerson;
    shortstop?: GameLinescorePerson;
    left?: GameLinescorePerson;
    center?: GameLinescorePerson;
    right?: GameLinescorePerson;
    batter?: GameLinescorePerson;
    on_deck?: GameLinescorePerson;
    in_hole?: GameLinescorePerson;
    batting_order?: number;
    team?: GameLinescoreTeamRef;
}

export interface GameLinescore {
    current_inning?: number;
    current_inning_ordinal?: string;
    inning_state?: string;
    inning_half?: string;
    is_top_inning?: boolean;
    scheduled_innings?: number;

    innings?: GameLinescoreInning[];
    teams?: GameLinescoreTeams;
    defense?: GameLinescoreAlignment;
    offense?: GameLinescoreAlignment;

    balls?: number;
    strikes?: number;
    outs?: number;
}

export interface GameDecisionPitcher {
    id?: number;
    full_name?: string;
    link?: string;
    card?: ShowdownBotCardCompact;
}

export interface GameDecisions {
    winner?: GameDecisionPitcher;
    loser?: GameDecisionPitcher;
    save?: GameDecisionPitcher;
}

export interface GameScheduled {
    game_pk: number;
    game_guid?: string;
    link?: string;
    game_type?: GameType;
    season?: string;
    game_date?: string;
    official_date?: string;

    status?: GameStatus;
    teams?: GameTeams;
    venue?: GameVenue;
    content?: GameContent;
    linescore?: GameLinescore;
    decisions?: GameDecisions;

    is_tie?: boolean;
    game_number?: number;
    public_facing?: boolean;
    double_header?: string;
    gameday_type?: string;
    tiebreaker?: string;
    calendar_event_id?: string;
    season_display?: string;
    day_night?: string;
    description?: string;
    scheduled_innings?: number;
    reverse_home_away_status?: boolean;
    inning_break_length?: number;
    games_in_series?: number;
    series_game_number?: number;
    series_description?: string;
    record_source?: string;
    if_necessary?: string;
    if_necessary_description?: string;
}

export interface Schedule {
    total_items?: number;
    total_events?: number;
    total_games?: number;
    total_games_in_progress?: number;

    date?: string;
    dates?: Schedule[];
    games?: GameScheduled[];
}

export interface Roster {

    roster_type: 'active' | '40Man' | 'fullSeason' | 'fullRoster' | 'gameday' | 'depthChart';
    team_id?: number;
    roster?: RosterSlot[];
}

export interface RosterSlot {
    person: Player;
    position: {
        code?: string;
        name?: string;
        type?: string;
        abbreviation?: string;
        description?: string;
    };
    status?: string | {
        code?: string;
        description?: string;
    };
    jersey_number?: string;
    parent_team_id?: number;
}

export interface Player {

    id: number;
    full_name: string;
    first_name?: string;
    last_name?: string;

    // Optional Showdown Card Data
    points?: number;
    showdown_card_data?: ShowdownBotCard;
}

// ***************************
// Game Boxscore Detail Types
// ***************************

export interface BoxscoreBattingStats {
    summary?: string;
    at_bats: number;
    runs: number;
    hits: number;
    rbi: number;
    base_on_balls: number;
    strike_outs: number;
    home_runs: number;
    stolen_bases: number;
    left_on_base: number;
}

export interface BoxscoreBattingSeasonStats {
    avg: string;
    obp: string;
    ops: string;
}

export interface BoxscoreBatter {
    id: number;
    name: string;
    jersey_number: string;
    position: string;
    batting_order: string;
    is_substitute: boolean;
    is_in_lineup: boolean;
    stats: BoxscoreBattingStats;
    season_stats: BoxscoreBattingSeasonStats;
}

export interface BoxscorePitchingStats {
    summary?: string;
    note?: string;
    innings_pitched: string;
    hits: number;
    runs: number;
    earned_runs: number;
    base_on_balls: number;
    strike_outs: number;
    home_runs: number;
    pitches_thrown: number;
    strikes: number;
    batters_faced: number;
}

export interface BoxscorePitchingSeasonStats {
    era: string;
    wins: number;
    losses: number;
}

export interface BoxscorePitcher {
    id: number;
    name: string;
    jersey_number: string;
    stats: BoxscorePitchingStats;
    season_stats: BoxscorePitchingSeasonStats;
}

export interface BoxscoreBattingTotals {
    at_bats: number;
    runs: number;
    hits: number;
    rbi: number;
    base_on_balls: number;
    strike_outs: number;
    home_runs: number;
    stolen_bases: number;
    left_on_base: number;
    avg: string;
    ops: string;
}

export interface BoxscorePitchingTotals {
    innings_pitched: string;
    hits: number;
    runs: number;
    earned_runs: number;
    base_on_balls: number;
    strike_outs: number;
    home_runs: number;
    pitches_thrown: number;
    strikes: number;
    era: string;
}

export interface BoxscoreInfoField {
    label: string;
    value: string;
}

export interface BoxscoreInfoSection {
    title: string;
    fieldList: BoxscoreInfoField[];
}

export interface BoxscoreTeamRecord {
    wins?: number;
    losses?: number;
    pct?: string;
}

export interface BoxscoreTeamInfo {
    id: number;
    name: string;
    abbreviation: string;
    record?: BoxscoreTeamRecord;
}

export interface BoxscoreTeamData {
    team: BoxscoreTeamInfo;
    batting: BoxscoreBatter[];
    pitching: BoxscorePitcher[];
    batting_totals: BoxscoreBattingTotals;
    pitching_totals: BoxscorePitchingTotals;
    info: BoxscoreInfoSection[];
    note: string;
}

export interface BoxscoreLinescoreInning {
    num: number;
    ordinal_num?: string;
    away: { runs?: number };
    home: { runs?: number };
}

export interface BoxscoreLinescoreTeamTotals {
    runs: number;
    hits: number;
    errors: number;
}

export interface BoxscoreLinescoreTeams {
    away: BoxscoreLinescoreTeamTotals;
    home: BoxscoreLinescoreTeamTotals;
}

export interface BoxscoreLinescoreOffense {
    batter?: string;
    batter_id?: number;
    on_deck?: string;
    first?: string;
    second?: string;
    third?: string;
}

export interface BoxscoreLinescoreDefense {
    pitcher?: string;
    pitcher_id?: number;
}

export interface BoxscoreLinescore {
    current_inning?: number;
    current_inning_ordinal?: string;
    inning_state?: string;
    inning_half?: string;
    is_top_inning?: boolean;
    scheduled_innings?: number;
    outs?: number;
    balls?: number;
    strikes?: number;
    offense?: BoxscoreLinescoreOffense;
    defense?: BoxscoreLinescoreDefense;
    innings: BoxscoreLinescoreInning[];
    teams: BoxscoreLinescoreTeams;
}

export interface BoxscoreDecisionPerson {
    id: number;
    full_name: string;
    link?: string;
}

export interface BoxscoreDecisions {
    winner?: BoxscoreDecisionPerson;
    loser?: BoxscoreDecisionPerson;
    save?: BoxscoreDecisionPerson;
}

export interface GameBoxscoreDetail {
    game_pk: number;
    status: GameStatus;
    datetime: {
        date_time?: string;
        official_date?: string;
    };
    teams: {
        away: BoxscoreTeamData;
        home: BoxscoreTeamData;
    };
    linescore: BoxscoreLinescore;
    decisions: BoxscoreDecisions;
}

