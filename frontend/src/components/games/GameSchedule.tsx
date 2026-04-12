import { useState, useEffect } from "react";
import { type GameScheduled } from "../../api/mlbAPI";
import { buildCardsFromIds, type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { FaArrowsRotate } from "react-icons/fa6";
import GameItem from "./GameItem";

type CardMap = Record<number, ShowdownBotCardAPIResponse>;

type GameScheduleProps = {
    games: GameScheduled[];
    dateLabel: string;
    description?: string;
    sportId?: number;
    season?: number;
    showdownSet?: string;
    starredTeamIds?: Set<number>;
    onGameSelect?: (gamePk: number) => void;
    onRefresh?: () => void;
};

export default function GameSchedule({ games, dateLabel, description, sportId, season, showdownSet, starredTeamIds, onGameSelect, onRefresh }: GameScheduleProps) {
    const [cardMap, setCardMap] = useState<CardMap>({});
    const [isLoadingCards, setIsLoadingCards] = useState(false);

    useEffect(() => {
        if (!season || !showdownSet || games.length === 0) return;
        let cancelled = false;

        const allIds = new Set<string>();
        for (const game of games) {
            const candidates = [
                game.teams?.away?.probable_pitcher?.id,
                game.teams?.home?.probable_pitcher?.id,
                game.linescore?.defense?.pitcher?.id,
                game.linescore?.offense?.batter?.id,
                game.decisions?.winner?.id,
                game.decisions?.loser?.id,
            ];
            for (const id of candidates) {
                if (id != null) allIds.add(String(id));
            }
        }

        if (allIds.size === 0) return;

        // Apply same season adjustment as GameDetail (use prior year's cards before May 1st)
        const isCurrentSeason = new Date().getFullYear() === season;
        const useLastYear = new Date().getMonth() < 3;
        const adjustedSeason = (sportId === 1 && isCurrentSeason && useLastYear) ? season - 1 : season;

        const cardSettings = {
            year: adjustedSeason,
            set: showdownSet,
            stat_highlights_type: "ALL",
        };

        setIsLoadingCards(true);
        buildCardsFromIds([...allIds], adjustedSeason, cardSettings, true)
            .then((response) => {
                if (cancelled) return;
                const map: CardMap = {};
                for (const entry of response.cards ?? []) {
                    if (entry.card?.mlb_id != null) {
                        map[entry.card.mlb_id] = entry;
                    }
                }
                setCardMap(map);
            })
            .catch(() => {})
            .finally(() => { if (!cancelled) setIsLoadingCards(false); });

        return () => { cancelled = true; };
    }, [games, season, showdownSet, sportId]);

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
            <div className="flex justify-between items-center">
                <div>
                    <div className="text-lg font-extrabold text-(--text-primary)">{dateLabel}</div>
                    {description && (
                        <div className="text-sm font-semibold text-(--text-secondary)">{description}</div>
                    )}
                </div>
                
                {/* Refresh button */}
                {onRefresh && (
                    <button
                        className="
                            hidden md:flex ml-4 px-4 py-2 items-center gap-1
                            bg-(--showdown-blue) text-white rounded-lg
                            hover:bg-(--showdown-blue)/50 transition-colors
                            cursor-pointer
                        "
                        onClick={onRefresh}
                    >
                        <FaArrowsRotate className="inline-block mr-1" />
                        Refresh
                    </button>
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
                            showMatchupDetails={true}
                            cardMap={cardMap}
                            isLoadingCards={isLoadingCards}
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
