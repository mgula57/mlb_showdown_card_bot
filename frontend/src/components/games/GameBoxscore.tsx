import { type GameBoxscore, type GameBoxscoreTeam } from "../../api/showdownBotCard"

/** Props for the GameBoxscore component */
type GameBoxscoreProps = {
    boxscore: GameBoxscore | null;
}

export function GameBoxscore({ boxscore }: GameBoxscoreProps) {

    // Early return if no boxscore data is available
    if (!boxscore) return null;

    const gameLink = `https://www.mlb.com/gameday/${boxscore.game_pk}`;
    const playerNameAndStatline: string | null = 
        boxscore.game_player_summary
            ? `${boxscore.game_player_summary.name.split(" ", 2)[1]}: ${boxscore.game_player_summary.game_player_summary}`
            : null;
    const gamePlayerPtsChange = boxscore.game_player_pts_change;
    const gamePlayerPtsChangeSymbol = gamePlayerPtsChange ? (gamePlayerPtsChange >= 0 ? "▲" : "▼") : null;
    const gamePlayerPtsChangeColor = gamePlayerPtsChange ? (gamePlayerPtsChange >= 0 ? "text-green-500" : "text-red-500") : null;

    // Team Summary
    const teamSummary = (team: GameBoxscoreTeam) => {
        return (
            <div 
                className={`
                    flex flex-row gap-2 items-center px-2 py-1 text-white
                `}
                style={{
                    backgroundColor: team.color
                }}
            >
                <span className="font-semibold">{team.abbreviation}</span>
                <span className="font-bold">{team.runs}</span>
            </div>
        );
    };

    return (
        <a 
            className="
                flex flex-row 
                max-w-max
                rounded-xl items-center bg-secondary overflow-clip
                shadow-lg hover:shadow-xl
            "
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
            <div className="flex gap-3 items-center px-3" >

                {/* Inning and Date */}
                <div className="flex items-center gap-2">
                    <span className="font-bold">{boxscore.current_inning_visual}</span>
                    {boxscore.has_game_ended && (
                        <span className="text-xs">{boxscore.date_short}</span>
                    )}
                </div>

                {/* Player Statline */}
                {playerNameAndStatline && (
                    <div className="flex gap-2 items-center">
                        <span className="text-sm font-medium">{playerNameAndStatline}</span>
                        {gamePlayerPtsChange && (
                            <span className={`text-xs ${gamePlayerPtsChangeColor}`}>
                                {gamePlayerPtsChangeSymbol} {Math.abs(gamePlayerPtsChange)} PTS
                            </span>
                        )}
                    </div>
                )}
            </div>

            
        </a>
    );
}