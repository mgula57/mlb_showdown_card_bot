
const MLB_API_BASE = 'https://statsapi.mlb.com/api/v1';

export const gamesAPI = {
    /**
     * Get games for a specific date
     */
    getGamesByDate: async (date: string): Promise<GameScheduled[]> => {
        const response = await fetch(`${MLB_API_BASE}/schedule?date=${date}&sportId=1`);
        if (!response.ok) {
            throw new Error(`Failed to fetch games: ${response.statusText}`);
        }
        const data = await response.json();
        if (data && data.dates && data.dates.length > 0) {
            return data.dates[0].games;
        }
        return [];
    },

    /**
     * Get game boxscore
     */
    getGameBoxscore: async (gamePk: number): Promise<any> => {
        const response = await fetch(`${MLB_API_BASE}/game/${gamePk}/boxscore`);
        if (!response.ok) {
            throw new Error(`Failed to fetch boxscore: ${response.statusText}`);
        }
        return await response.json();
    },

    /**
     * Get current games
     */
    getCurrentGames: async (): Promise<GameScheduled[]> => {
        const today = new Date().toISOString().split('T')[0];
        return gamesAPI.getGamesByDate(today);
    }
};

export type GameScheduled = {
    gamePK: number;
    gameDate: string;
    officialDate: string;
    status: {
        statusCode: string;
        abstractGameState: string;
    }
    teams: {
        away: GameScheduledTeam;
        home: GameScheduledTeam;
    }
}

export type GameScheduledTeam = {
    score: number;
    team: {
        name: string;
    }
}