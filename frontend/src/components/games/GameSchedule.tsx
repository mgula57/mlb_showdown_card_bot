import { useState, useEffect, useMemo } from "react";
import { type GameScheduled } from "../../api/mlbAPI";
import { fetchCardData, type CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import { CardSource } from "../../types/cardSource";
import { FaArrowsRotate } from "react-icons/fa6";
import { fromScheduledGame } from "../../domain/adapters/fromMlbApi";
import { cardKey } from "../../domain/players";
import type { GameState } from "../../domain/game";
import GameItem from "./GameItem";

type CardMap = Record<string, CardDatabaseRecord>;

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

const STATE_SORT_ORDER: Record<GameState, number> = { LIVE: 0, PREVIEW: 1, FINAL: 2, POSTPONED: 3 };

export default function GameSchedule({ games, dateLabel, description, sportId, season, showdownSet, starredTeamIds, onGameSelect, onRefresh }: GameScheduleProps) {
    const [cardMap, setCardMap] = useState<CardMap>({});
    const [isLoadingCards, setIsLoadingCards] = useState(false);

    const gameViews = useMemo(() => games.map((game) => fromScheduledGame(game, sportId)), [games, sportId]);

    // Derive a stable key from only the IDs relevant to each game's current state,
    // so the card-fetch effect only re-runs when those IDs actually change.
    const idsKey = useMemo(() => {
        const ids = new Set<string>();
        for (const game of gameViews) {
            if (game.state === 'FINAL') {
                const winner = game.decisions?.winner?.id;
                const loser = game.decisions?.loser?.id;
                if (typeof winner === 'number') ids.add(cardKey(winner, 'P'));
                if (typeof loser === 'number') ids.add(cardKey(loser, 'P'));
            } else if (game.state === 'LIVE') {
                const batter = game.situation?.batter?.id;
                const pitcher = game.situation?.pitcher?.id;
                if (typeof batter === 'number') ids.add(cardKey(batter, 'H'));
                if (typeof pitcher === 'number') ids.add(cardKey(pitcher, 'P'));
            } else {
                const awayPitcher = game.away.probablePitcher?.id;
                const homePitcher = game.home.probablePitcher?.id;
                if (typeof awayPitcher === 'number') ids.add(cardKey(awayPitcher, 'P'));
                if (typeof homePitcher === 'number') ids.add(cardKey(homePitcher, 'P'));
            }
        }
        return [...ids].sort().join(',');
    }, [gameViews]);

    useEffect(() => {
        if (!season || !showdownSet || !idsKey) return;
        let cancelled = false;

        // Strip role suffixes (e.g. "660271-H" → "660271") to get plain IDs for the API call.
        const allIds = [...new Set(idsKey.split(',').map(k => k.split('-')[0]))];

        // Apply same season adjustment as GameDetail (use prior year's cards before May 1st)
        const isCurrentSeason = new Date().getFullYear() === season;
        const useLastYear = new Date().getMonth() < 3;
        const adjustedSeason = (sportId === 1 && isCurrentSeason && useLastYear) ? season - 1 : season;

        setIsLoadingCards(true);
        fetchCardData(CardSource.BOT, {
            mlb_id: allIds,
            year: String(adjustedSeason),
            showdown_set: showdownSet,
            limit: allIds.length * 2, // Two-way players return both a hitter and pitcher record
        })
            .then((records) => {
                if (cancelled) return;
                const map: CardMap = {};
                for (const record of records) {
                    const id = record.mlb_id;
                    if (id == null) continue;
                    if (typeof id === 'number' || !Number.isNaN(Number(id))) {
                        map[cardKey(Number(id), record.is_pitcher ? "P" : "H")] = record;
                    }
                    map[String(id)] = record;
                }
                setCardMap(map);
            })
            .catch(() => {})
            .finally(() => { if (!cancelled) {
                setIsLoadingCards(false);
            }});

        return () => { cancelled = true; };
    }, [idsKey, season, showdownSet, sportId]);

    if (!games.length) {
        return null;
    }

    // Sort: starred-team games first, then by game state (live → upcoming → final → postponed)
    const sortedGames = [...gameViews].sort((a, b) => {
        const aStarred = starredTeamIds
            ? (starredTeamIds.has(Number(a.away.team.id) || -1) || starredTeamIds.has(Number(a.home.team.id) || -1))
            : false;
        const bStarred = starredTeamIds
            ? (starredTeamIds.has(Number(b.away.team.id) || -1) || starredTeamIds.has(Number(b.home.team.id) || -1))
            : false;
        if (aStarred !== bStarred) return aStarred ? -1 : 1;
        return STATE_SORT_ORDER[a.state] - STATE_SORT_ORDER[b.state];
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
                            key={game.id}
                            game={game}
                            onSelect={onGameSelect}
                            showMatchupDetails={true}
                            cardMap={cardMap}
                            isLoadingCards={isLoadingCards}
                            isStarred={
                                starredTeamIds
                                    ? (starredTeamIds.has(Number(game.away.team.id) || -1) || starredTeamIds.has(Number(game.home.team.id) || -1))
                                    : false
                            }
                        />
                    );
                })}
            </div>
        </div>
    );
}
