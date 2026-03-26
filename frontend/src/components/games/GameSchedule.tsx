import { type GameScheduled } from "../../api/mlbAPI";
import GameItem from "./GameItem";

type GameScheduleProps = {
    games: GameScheduled[];
    dateLabel: string;
    description?: string;
    sportId?: number;
    starredTeamIds?: Set<number>;
    onGameSelect?: (gamePk: number) => void;
};

export default function GameSchedule({ games, dateLabel, description, sportId, starredTeamIds, onGameSelect }: GameScheduleProps) {
    if (!games.length) {
        return null;
    }

    // Sort: starred-team games first, then by game state (live → upcoming → final)
    const statusOrder: Record<string, number> = { "Live": 0, "Scheduled": 1, "Final": 2 };
    const sortedGames = [...games].sort((a, b) => {
        const aStarred = starredTeamIds
            ? (starredTeamIds.has(a.teams?.away?.team?.id ?? -1) || starredTeamIds.has(a.teams?.home?.team?.id ?? -1))
            : false;
        const bStarred = starredTeamIds
            ? (starredTeamIds.has(b.teams?.away?.team?.id ?? -1) || starredTeamIds.has(b.teams?.home?.team?.id ?? -1))
            : false;
        if (aStarred !== bStarred) return aStarred ? -1 : 1;
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
                            isStarred={
                                starredTeamIds
                                    ? (starredTeamIds.has(game.teams?.away?.team?.id ?? -1) || starredTeamIds.has(game.teams?.home?.team?.id ?? -1))
                                    : false
                            }
                        />
                    );
                })}
            </div>
        </div>
    );
}
