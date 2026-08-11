/**
 * @fileoverview Data plumbing for GameDetail: the initial fetch, the live-polling loop (with a
 * pause/buffer for the "watch it catch up" control), and the Showdown card lookup for everyone in
 * the boxscore. Split out of GameDetail.tsx so that file can stay about layout and playback.
 */
import { useState, useEffect, useCallback, useRef } from "react";

import {
    fetchGameBoxscore,
    type GameBoxscoreDetail,
} from "../../api/mlbAPI";
import { buildCardsFromIds, type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { TWO_WAY_PLAYER_IDS } from "../../domain/players";
import type { SimGameResult } from "../../api/simGame";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

export function useGameDetailData({
    gamePk, sportId, season, showdownSet, isActive, simResult,
}: {
    gamePk: number;
    sportId?: number;
    season?: number;
    showdownSet?: string;
    isActive: boolean;
    simResult: SimGameResult | null;
}) {
    const [boxscore, setBoxscore] = useState<GameBoxscoreDetail | null>(null);
    const [cardMap, setCardMap] = useState<CardMap>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isLoadingCards, setIsLoadingCards] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Pausing a live game doesn't stop polling — it stops the fetched data from reaching the
    // screen. Plays keep landing in `bufferedBoxscore` so resuming can animate through them
    // instead of jumping straight to whatever arrived while paused.
    const [isLivePaused, setIsLivePausedState] = useState(false);
    const isLivePausedRef = useRef(false);
    const [bufferedBoxscore, setBufferedBoxscoreState] = useState<GameBoxscoreDetail | null>(null);
    // Mirrors `bufferedBoxscore` synchronously so `applyBuffer` can read the latest value without
    // waiting on a render — a plain `useState` setter's previous value isn't available until the
    // next render, and `applyBuffer` needs it immediately.
    const bufferedRef = useRef<GameBoxscoreDetail | null>(null);
    const setBufferedBoxscore = useCallback((data: GameBoxscoreDetail | null) => {
        bufferedRef.current = data;
        setBufferedBoxscoreState(data);
    }, []);

    const setLivePaused = useCallback((paused: boolean) => {
        isLivePausedRef.current = paused;
        setIsLivePausedState(paused);
    }, []);

    /** Resume: the buffered snapshot becomes the live one. The playback cursor (tracked by frame
     *  id, not index) stays where it was, so `useGamePlayback` sees new frames appended and can
     *  walk forward through them instead of snapping. */
    const applyBuffer = useCallback(() => {
        if (!bufferedRef.current) return;
        setBoxscore(bufferedRef.current);
        setBufferedBoxscore(null);
    }, [setBufferedBoxscore]);

    /** Drop whatever is buffered without applying it — e.g. staying paused and letting the next
     *  poll start a fresh buffer rather than accumulating an ever-larger one. */
    const discardBuffer = useCallback(() => setBufferedBoxscore(null), [setBufferedBoxscore]);

    const refreshBoxscore = useCallback((silent = false) => {
        if (!silent) setIsRefreshing(true);
        return fetchGameBoxscore(gamePk).then((data) => {
            if (isLivePausedRef.current) setBufferedBoxscore(data);
            else setBoxscore(data);
            return data;
        }).finally(() => {
            if (!silent) setIsRefreshing(false);
        });
    }, [gamePk, setBufferedBoxscore]);

    // Initial fetch
    useEffect(() => {
        let cancelled = false;
        setIsLoading(true);
        setError(null);

        refreshBoxscore(true /* silent – initial load uses isLoading */)
            .catch((err) => {
                if (!cancelled) setError(err.message ?? "Failed to load boxscore");
            })
            .finally(() => {
                if (!cancelled) setIsLoading(false);
            });

        return () => { cancelled = true; };
    }, [refreshBoxscore]);

    // Auto-refresh every 30s while the game is in progress and tab is visible
    const isInProgressRef = useRef(false);
    useEffect(() => {
        const codedState = boxscore?.status?.coded_game_state;
        const isFinal = codedState === "F";
        const isNotStarted = codedState === "P" || codedState === "S";
        isInProgressRef.current = !!boxscore && !isFinal && !isNotStarted;
    }, [boxscore]);

    useEffect(() => {
        if (!boxscore) return;
        if (!isInProgressRef.current) return;
        if (!isActive) return;
        // A simulation has replaced the panels, so refreshing the real game would only churn
        // state nothing on screen is reading.
        if (simResult) return;

        let timer: ReturnType<typeof setInterval> | null = null;

        const startPolling = () => {
            if (timer) return;
            timer = setInterval(() => {
                if (isInProgressRef.current) {
                    refreshBoxscore().catch(() => {});
                }
            }, 30_000);
        };

        const stopPolling = () => {
            if (timer) { clearInterval(timer); timer = null; }
        };

        const onVisibility = () => {
            if (document.hidden) {
                stopPolling();
            } else if (isInProgressRef.current) {
                // Refresh immediately when tab becomes visible again, then resume polling
                refreshBoxscore().catch(() => {});
                startPolling();
            }
        };

        document.addEventListener("visibilitychange", onVisibility);
        if (!document.hidden) startPolling();

        return () => {
            document.removeEventListener("visibilitychange", onVisibility);
            stopPolling();
        };
    }, [boxscore, refreshBoxscore, isActive, simResult]);

    // Fetch Showdown cards for all players in the boxscore
    useEffect(() => {
        if (!boxscore || !season || !showdownSet) return;
        let cancelled = false;

        const allIds = new Set<string>();
        for (const side of ["away", "home"] as const) {
            for (const b of boxscore.teams[side].batting) allIds.add(String(b.id));
            for (const p of boxscore.teams[side].pitching) allIds.add(String(p.id));
        }
        // Include probable starters for pre-game state
        if (boxscore.probable_pitchers) {
            for (const side of ["away", "home"] as const) {
                const id = boxscore.probable_pitchers[side]?.id;
                if (id != null) allIds.add(String(id));
            }
        }
        // A simulation can use bench and bullpen players the real boxscore never lists, so their
        // cards have to be fetched too or the sim's play log and box score fall back to bare names.
        if (simResult) {
            for (const side of ["away", "home"] as const) {
                for (const option of simResult.setup[side].position_players) allIds.add(option.player_id);
                for (const option of simResult.setup[side].bullpen) allIds.add(option.player_id);
            }
        }

        // Override the team for each ID based on the boxscore data, to ensure we get the correct card even if the player is now on a new team
        const overrides: Record<number, Record<string, unknown>> = {};
        for (const side of ["away", "home"] as const) {
            const teamAbbreviation = boxscore.teams[side].team.abbreviation;
            for (const b of boxscore.teams[side].batting) {
                overrides[b.id] = { team: teamAbbreviation };
            }
            for (const p of boxscore.teams[side].pitching) {
                overrides[p.id] = { team: teamAbbreviation };
            }
            // Also override probable pitchers
            const probableId = boxscore.probable_pitchers?.[side]?.id;
            if (probableId != null) {
                overrides[probableId] = { team: teamAbbreviation };
            }
        }

        // Check if sport is not WBC and date is before May 1st of that season, if so subtract 1 from the season to use last year's cards
        const isCurrentSeason = new Date().getFullYear() === season;
        const useLastYear = new Date().getMonth() < 3; // Months are 0-indexed
        const adjustedSeason = (sportId === 1 && isCurrentSeason && useLastYear) ? season - 1 : season;
        const gameDate = new Date(boxscore.datetime.official_date ?? "") || new Date();
        const yesterday = new Date(gameDate);
        yesterday.setDate(yesterday.getDate() - 1);

        const cardSettings = {
            year: adjustedSeason,
            set: showdownSet,
            stat_highlights_type: "ALL",
            stats_period_type: "DATES",
            start_date: `${gameDate.getFullYear()}-03-01`, // Pull stats from the start of the season to ensure we have data for early-season games
            end_date: boxscore.datetime.official_date,
            in_season_trends_range_start_date: yesterday.toISOString().split("T")[0], // Notes the end date to start with to speed up processing
            in_season_trends_end_date: boxscore.datetime.official_date,
        }
        // No need to reload if all IDs are already in the map
        if ([...allIds].every(id => cardMap[id])) {
            return;
        }
        setIsLoadingCards(true);
        buildCardsFromIds([...allIds], adjustedSeason, cardSettings)
            .then((response) => {
                if (cancelled) return;
                const map: CardMap = {};
                for (const entry of response.cards ?? []) {
                    if (entry.card?.mlb_id != null) {
                        const id = entry.card.mlb_id;
                        if (TWO_WAY_PLAYER_IDS.has(id)) {
                            const suffix = entry.card.player_type === "Pitcher" ? "P" : "H";
                            map[`${id}-${suffix}`] = entry;
                        } else {
                            map[String(id)] = entry;
                        }
                    }
                }
                // Merge rather than replace — a mid-game substitution should add the new
                // player's card without invalidating every marker already resolved from the map.
                setCardMap((prev) => ({ ...prev, ...map }));
            })
            .catch(() => { /* cards are supplementary – fail silently */ })
            .finally(() => { if (!cancelled) setIsLoadingCards(false); });

        return () => { cancelled = true; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [boxscore, season, showdownSet, sportId, simResult]);

    return {
        boxscore, bufferedBoxscore, cardMap,
        isLoading, isRefreshing, isLoadingCards, error,
        refresh: refreshBoxscore,
        isLivePaused, setLivePaused, applyBuffer, discardBuffer,
    };
}
