import { type GameScheduled } from "../../api/mlbAPI";
import GameItem from "./GameItem";

type GameScheduleProps = {
    games: GameScheduled[];
    dateLabel: string;
    description?: string;
    sportId?: number;
    onGameSelect?: (gamePk: number) => void;
};

export default function GameSchedule({ games, dateLabel, description, sportId, onGameSelect }: GameScheduleProps) {
    if (!games.length) {
        return null;
    }

    // Sort games, putting live games first, then games that havent started, and lastly completed games
    const sortedGames = [...games].sort((a, b) => {
        const statusOrder: Record<string, number> = { "Live": 0, "Scheduled": 1, "Final": 2 };
        return (statusOrder[a.status?.abstract_game_state || ""] ?? 3) - (statusOrder[b.status?.abstract_game_state || ""] ?? 3);
    });

    return (
        <div className="space-y-3">
            <div>
                <div className="text-lg font-extrabold text-(--text-primary)">{dateLabel}</div>
                {description && (
                    <div className="text-sm font-semibold text-(--text-secondary)">{description}</div>
                )}
            </div>

            <div className="grid grid-cols-[repeat(auto-fit,minmax(270px,1fr))] gap-4">
                {sortedGames.map((game) => {
                    return (
                        <GameItem
                            key={game.game_pk}
                            game={game}
                            sportId={sportId}
                            onSelect={onGameSelect}
                        />
                    );
                })}
            </div>
        </div>
    );
}
