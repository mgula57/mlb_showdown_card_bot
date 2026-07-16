import { useState, useEffect, useMemo } from "react";
import { type GameScheduled } from "../../api/mlbAPI";
import { fetchCardData, type CardDatabaseRecord } from "../../api/card_db/cardDatabase";
import { CardSource } from "../../types/cardSource";
import { FaArrowsRotate } from "react-icons/fa6";
import GameItem from "./GameItem";

type CardMap = Record<string, CardDatabaseRecord>;

// TODO: replace hard-coded IDs with a general two-way player detection strategy
const TWO_WAY_PLAYER_IDS = new Set([660271]); // Ohtani

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

    // Derive a stable key from only the IDs relevant to each game's current state,
    // so the card-fetch effect only re-runs when those IDs actually change.
    // Two-way players are encoded with a role suffix (e.g. "660271-H" vs "660271-P")
    // so the key changes when their on-field role changes.
    const idsKey = useMemo(() => {
        const ids = new Set<string>();
        const encodeId = (id: number, role: 'H' | 'P'): string =>
            TWO_WAY_PLAYER_IDS.has(id) ? `${id}-${role}` : String(id);

        for (const game of games) {
            const coded = game.status?.coded_game_state;
            const isFinal = coded === 'F' || game.status?.status_code === 'F';
            const isNotStarted = coded === 'P' || coded === 'S';
            const isInProgress = !isFinal && !isNotStarted;

            if (isFinal) {
                const winner = game.decisions?.winner?.id;
                const loser = game.decisions?.loser?.id;
                if (winner != null) ids.add(encodeId(winner, 'P'));
                if (loser != null) ids.add(encodeId(loser, 'P'));
            } else if (isInProgress) {
                const batter = game.linescore?.offense?.batter?.id;
                const pitcher = game.linescore?.defense?.pitcher?.id;
                if (batter != null) ids.add(encodeId(batter, 'H'));
                if (pitcher != null) ids.add(encodeId(pitcher, 'P'));
            } else {
                const awayPitcher = game.teams?.away?.probable_pitcher?.id;
                const homePitcher = game.teams?.home?.probable_pitcher?.id;
                if (awayPitcher != null) ids.add(encodeId(awayPitcher, 'P'));
                if (homePitcher != null) ids.add(encodeId(homePitcher, 'P'));
            }
        }
        return [...ids].sort().join(',');
    }, [games]);

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
                    if (TWO_WAY_PLAYER_IDS.has(Number(id))) {
                        map[`${id}-${record.is_pitcher ? "P" : "H"}`] = record;
                    } else {
                        map[String(id)] = record;
                    }
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
