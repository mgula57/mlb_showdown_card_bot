import { type GameScheduled } from "../../api/mlbAPI";
import GameItem from "./GameItem";

type GameScheduleProps = {
    games: GameScheduled[];
    dateLabel: string;
    description?: string;
    sportId?: number;
};

export default function GameSchedule({ games, dateLabel, description, sportId }: GameScheduleProps) {
    if (!games.length) {
        return null;
    }

    return (
        <div className="space-y-3">
            <div>
                <div className="text-lg font-extrabold text-(--text-primary)">{dateLabel}</div>
                {description && (
                    <div className="text-sm font-semibold text-(--text-secondary)">{description}</div>
                )}
            </div>

            <div className="grid grid-cols-[repeat(auto-fit,minmax(270px,1fr))] gap-4">
                {games.map((game) => {
                    return (
                        <GameItem
                            key={game.game_pk}
                            game={game}
                            sportId={sportId}
                        />
                    );
                })}
            </div>
        </div>
    );
}
