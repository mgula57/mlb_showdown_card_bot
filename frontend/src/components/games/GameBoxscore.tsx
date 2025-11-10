/**
 * @fileoverview GameBoxscore - Live MLB game display and tracking component
 * 
 * Provides real-time display of MLB game information including scores, inning status,
 * team information, and player performance tracking. Integrates with MLB APIs to show
 * live game updates and connects player performance to Showdown card generation.
 * Features team colors, game status indicators, and direct links to MLB.com gameday.
 */

import { type GameBoxscore, type GameBoxscoreTeam } from "../../api/showdownBotCard"
import { enhanceColorVisibility } from "../../functions/colors";
import { FaBaseballBall } from "react-icons/fa";

/**
 * Props for the GameBoxscore component
 */
type GameBoxscoreProps = {
    /** Game boxscore data from MLB API */
    boxscore: GameBoxscore | null;
    /** Whether the component is in a loading state */
    isLoading?: boolean;
}

/**
 * GameBoxscore - Live MLB game information display
 * 
 * Renders comprehensive game information including team matchup, current score,
 * inning status, and player-specific performance data. Supports both live games
 * and completed games with different display modes. Integrates team colors and
 * provides direct navigation to official MLB game pages.
 * 
 * Features:
 * - Live score and inning display
 * - Team color integration with enhanced visibility
 * - Player performance tracking and point calculations
 * - Game status indicators (live, final, scheduled)
 * - Direct links to MLB.com gameday pages
 * - Responsive design for various screen sizes
 * 
 * @example
 * ```tsx
 * <GameBoxscore
 *   boxscore={gameData}
 *   isLoading={isLoadingGame}
 * />
 * ```
 * 
 * @param boxscore - Game data including teams, scores, and player stats
 * @param isLoading - Loading state for showing placeholders
 * @returns Game boxscore display component
 */
export function GameBoxscore({ boxscore, isLoading }: GameBoxscoreProps) {

    /** Early return if no boxscore data available */
    if (!boxscore) return null;

    // =============================================================================
    // DATA PROCESSING AND FORMATTING
    // =============================================================================

    /** Direct link to MLB.com gameday page */
    const gameLink = `https://www.mlb.com/gameday/${boxscore.game_pk}`;
    
    /** 
     * Formatted player performance summary
     * Shows different format for live vs completed games
     */
    const playerStatline: string | null = 
        boxscore.game_player_summary
            ? (boxscore.has_game_ended
                ? boxscore.game_player_summary.game_player_summary
                : `${boxscore.game_player_summary.name.split(" ", 2)[1]}: ${boxscore.game_player_summary.game_player_summary}`)
            : null;
    
    /** Player point change from this game performance */
    const gamePlayerPtsChange = boxscore.game_player_pts_change;
    /** Visual indicator for point changes (up/down arrows) */
    const gamePlayerPtsChangeSymbol = gamePlayerPtsChange ? (gamePlayerPtsChange >= 0 ? "▲" : "▼") : null;
    /** Color coding for positive/negative point changes */
    const gamePlayerPtsChangeColor = gamePlayerPtsChange ? (gamePlayerPtsChange >= 0 ? enhanceColorVisibility("text-green-600") : enhanceColorVisibility("text-red-500")) : null;

    // =============================================================================
    // TEAM DISPLAY COMPONENTS
    // =============================================================================

    /**
     * Render team information with colors and scores
     * @param team - Team data including name, colors, and score
     * @returns Team summary component
     */
    const teamSummary = (team: GameBoxscoreTeam) => {
        return (
            <div 
                className="flex flex-col gap-1 pt-1 w-20 text-nowrap"
                style={{
                    backgroundColor: team.color
                }}
            >
                {/* Score */}
                <div 
                    className={`
                        flex flex-row 
                        gap-2 items-center px-2 justify-between
                        text-white text-md
                        ${boxscore.has_game_ended ? "translate-y-0.5" : ""}
                    `}
                >
                    <span className="font-bold">{team.abbreviation}</span>
                    <span className="font-black">{team.runs}</span>
                </div>

                {/* Live game player indicator */}
                {team.player && !boxscore.has_game_ended && (
                    <span className="text-[9px] font-semibold px-2 pb-1 bg-black/10 text-white">{team.player}</span>
                )}
            </div>
        );
    };

    // =============================================================================
    // MAIN COMPONENT RENDER
    // =============================================================================

    return (
        <a 
            className={`
                flex flex-row 
                max-w-max
                rounded-xl bg-secondary overflow-clip
                ${boxscore.has_game_ended ? "" : "items-center"}
                shadow-lg hover:shadow-xl
            `}
            href={gameLink}
            target="_blank"
            rel="noopener noreferrer"
        >
            {/* Team scores section */}
            {teamSummary(boxscore.teams.away)}
            {teamSummary(boxscore.teams.home)}

            {/* Game status and details section */}
            <div className="flex gap-3 items-center px-2" >

                {/* Inning indicator or final status */}
                <div className="flex flex-col items-center gap-0 text-xs font-bold">
                    {boxscore.has_game_ended ? (
                        <>
                            <span className="text-sm">FINAL</span>
                            <span className="text-xs">{boxscore.date_short}</span>
                        </>
                    ) : (
                        <>
                            {/* Top/bottom inning indicators */}
                            <span className={` ${boxscore.isTopInning ? "text-yellow-500" : "opacity-50"}`}>
                                ▲
                            </span>
                            <span className="text-xs">
                                {boxscore.currentInningOrdinal}
                            </span>
                            <span className={`font-bold ${!boxscore.isTopInning ? "text-yellow-500" : "opacity-20"}`}>
                                ▼
                            </span>
                        </>
                    )}
                </div>

                {/* Live game situation display */}
                <div className="flex flex-col items-start gap-0">

                    {!boxscore.has_game_ended && (
                        <div className="flex flex-row gap-4 items-center">
                            {/* Baseball diamond with base runners */}
                            <div className="relative w-6 h-6 mt-1">
                                {/* Second Base */}
                                <div className={`absolute top-0 left-1/2 transform -translate-x-1/2 w-2 h-2 rotate-45 ${
                                    boxscore.offense?.second ? 'bg-yellow-400' : 'bg-gray-400'
                                }`}></div>

                                {/* Third Base */}
                                <div className={`absolute bottom-1/3 left-0 w-2 h-2 rotate-45 ${
                                    boxscore.offense?.third ? 'bg-yellow-400' : 'bg-gray-400'
                                }`}></div>

                                {/* First Base */}
                                <div className={`absolute bottom-1/3 right-0 w-2 h-2 rotate-45 ${
                                    boxscore.offense?.first ? 'bg-yellow-400' : 'bg-gray-400'
                                }`}></div>
                            </div>

                            {/* Count and Outs */}
                            <div className="flex flex-row items-center gap-3 text-xs font-bold">
                                <span>{boxscore.balls || 0} - {boxscore.strikes || 0}</span>
                                <span>{boxscore.outs || 0} OUT{boxscore.outs === 1 ? "" : "S"}</span>
                            </div>

                        </div>
                    )}

                    {/* Player Statline */}
                    {playerStatline && (
                        <div className="text-[10px] font-semibold flex gap-2 items-center">
                            <div className="flex flex-col">
                                {boxscore.has_game_ended && boxscore.game_player_summary?.name ? <span className="text-xs font-bold">{boxscore.game_player_summary?.name}</span> : null}
                                <span>{playerStatline}</span>
                            </div>
                            {gamePlayerPtsChange && (
                                <span className={`${gamePlayerPtsChangeColor}`}>
                                    {gamePlayerPtsChangeSymbol} {Math.abs(gamePlayerPtsChange)} PTS
                                </span>
                            )}
                        </div>
                    )}

                </div>

                
            </div>

            {/* Loading indicator for live game updates */}
            {isLoading && (
                <FaBaseballBall 
                    className="text-sm animate-bounce" 
                    style={{
                        animationDuration: '0.8s',
                        animationIterationCount: 'infinite'
                    }}
                />
            )}
        </a>
    );
}