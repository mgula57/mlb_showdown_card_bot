import { mlbAPI } from "../../api/mlb"
import { type GameScheduled } from "../../api/mlb/games/games";
import { useEffect, useState } from "react";

const GamesForDate = ({ date }: { date: string }) => {
    const [games, setGames] = useState<GameScheduled[]>([]);

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
            <h2 className="text-lg font-bold">{date}</h2>
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
                        {game.teams.home.team.name} ({game.teams.home.score}) vs {game.teams.away.team.name} ({game.teams.away.score})
                    </div>
                ))}
            </div>
        </div>
    );
};

export default GamesForDate;
