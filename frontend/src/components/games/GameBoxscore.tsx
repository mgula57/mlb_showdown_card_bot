import { type GameBoxscore, type GameBoxscoreTeam } from "../../api/showdownBotCard"
import { enhanceColorVisibility } from "../../functions/colors";

/** Props for the GameBoxscore component */
type GameBoxscoreProps = {
    boxscore: GameBoxscore | null;
}

export function GameBoxscore({ boxscore }: GameBoxscoreProps) {

    // Early return if no boxscore data is available
    if (!boxscore) return null;

    const gameLink = `https://www.mlb.com/gameday/${boxscore.game_pk}`;
    const playerStatline: string | null = 
        boxscore.game_player_summary
            ? (boxscore.has_game_ended
                ? boxscore.game_player_summary.game_player_summary
                : `${boxscore.game_player_summary.name.split(" ", 2)[1]}: ${boxscore.game_player_summary.game_player_summary}`)
            : null;
    const gamePlayerPtsChange = boxscore.game_player_pts_change;
    const gamePlayerPtsChangeSymbol = gamePlayerPtsChange ? (gamePlayerPtsChange >= 0 ? "▲" : "▼") : null;
    const gamePlayerPtsChangeColor = gamePlayerPtsChange ? (gamePlayerPtsChange >= 0 ? enhanceColorVisibility("text-green-600") : enhanceColorVisibility("text-red-500")) : null;

    // Team Summary
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
                

                {/* Player Pitching/Hitting */}
                {team.player && !boxscore.has_game_ended && (
                    <span className="text-[9px] font-semibold px-2 pb-1 bg-black/10 text-white">{team.player}</span>
                )}
            </div>
        );
    };

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
            {/* Scores */}
            
            {/* Away Team */}
            {teamSummary(boxscore.teams.away)}

            {/* Home Team */}
            {teamSummary(boxscore.teams.home)}

            {/* Right Side */}
            <div className="flex gap-3 items-center px-2" >

                {/* Inning and Date */}
                <div className="flex flex-col items-center gap-0 text-xs font-bold">
                    {boxscore.has_game_ended ? (
                        <>
                            <span className="text-sm">FINAL</span>
                            <span className="text-xs">{boxscore.date_short}</span>
                        </>
                    ) : (
                        <>
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

                {/* Situation and Player Statline */}
                <div className="flex flex-col items-start gap-0">

                    {!boxscore.has_game_ended && (
                        <div className="flex flex-row gap-4 items-center">
                            {/* Baseball Bases */}
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

            
        </a>
    );
}