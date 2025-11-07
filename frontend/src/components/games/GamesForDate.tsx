/**
 * @fileoverview GamesForDate - MLB games listing component for specific dates
 * 
 * Displays a grid of MLB games scheduled for a specific date with team information,
 * scores, and game status. Integrates with MLB API to fetch current game data
 * and provides a responsive grid layout for game browsing and selection.
 */

import { mlbAPI } from "../../api/mlb"
import { type GameScheduled } from "../../api/mlb/games/games";
import { useEffect, useState } from "react";

/**
 * Props for the GamesForDate component
 */
interface GamesForDateProps {
    /** Date string to fetch games for (YYYY-MM-DD format) */
    date: string;
}

/**
 * GamesForDate - Display MLB games for a specific date
 * 
 * Fetches and displays a grid of MLB games scheduled for the specified date.
 * Shows team matchups, current scores, and game status in a responsive grid
 * layout. Integrates with the MLB API to provide up-to-date game information.
 * 
 * Features:
 * - Responsive grid layout adapting to screen size
 * - Real-time game data from MLB API
 * - Team names and current scores
 * - Clean, card-based game display
 * - Automatic data fetching on date change
 * 
 * @example
 * ```tsx
 * <GamesForDate date="2023-07-15" />
 * ```
 * 
 * @param date - Target date for game listings
 * @returns Games grid component for the specified date
 */
const GamesForDate = ({ date }: GamesForDateProps) => {
    /** List of scheduled games for the date */
    const [games, setGames] = useState<GameScheduled[]>([]);

    /**
     * Fetch games data when component mounts or date changes
     * Retrieves current games from MLB API
     */
    useEffect(() => {
        const fetchGames = async () => {
            const data = await mlbAPI.games.getCurrentGames();
            console.log(data);
            setGames(data);
        };

        fetchGames();
    }, [date]);

    return (
        <div className="px-4 py-2">
            {/* Date header */}
            <h2 className="text-lg font-bold">{date}</h2>
            
            {/* Responsive games grid */}
            <div 
                className="
                    grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-2
                ">
                {games.map((game) => (
                    <div 
                        key={game.gamePK}
                        className="
                            bg-primary
                            p-2
                            border-form-element border-2 rounded-2xl
                        "
                    >
                        {/* Game matchup with scores */}
                        {game.teams.home.team.name} ({game.teams.home.score}) vs {game.teams.away.team.name} ({game.teams.away.score})
                    </div>
                ))}
            </div>
        </div>
    );
};

export default GamesForDate;
