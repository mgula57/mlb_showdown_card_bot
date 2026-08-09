import { useState, useEffect, useCallback, useRef, useMemo, type CSSProperties } from "react";
import ReactCountryFlag from "react-country-flag";
import { FaChevronLeft } from "react-icons/fa6";

import { countryCodeForTeam } from "../../functions/flags";
import { getReadableTextColor } from "../../functions/colors";
import { Modal } from "../shared/Modal";
import { BottomSheet, type SnapPoint } from "../shared/BottomSheet";
import {
    fetchGameBoxscore,
    type GameBoxscoreDetail,
    type BoxscoreTeamData,
    type BoxscoreBatter,
    type BoxscorePitcher,
    type BoxscoreDecisionPerson,
} from "../../api/mlbAPI";
import { buildCardsFromIds, type ShowdownBotCard, type ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { defenseAtPosition } from "../shared/DefenseUtils";
import { CardItemFromCard, CardItemSkeleton } from "../cards/CardItem";
import { CardDetail } from "../cards/CardDetail";
import CardIdentityCell from "../cards/card_elements/CardIdentityCell";
import PointsBadge from "../cards/card_elements/PointsBadge";
import { useIsSmallScreen } from "../../hooks/useIsSmallScreen";
import {
    useFloating, useHover, useInteractions, offset, flip, shift, autoUpdate, FloatingPortal
} from "@floating-ui/react";
import * as Tabs from '@radix-ui/react-tabs';
import { TWO_WAY_PLAYER_IDS, cardKey } from "../../domain/players";
import { fromBoxscoreDetail, fromGamePlays } from "../../domain/adapters/fromMlbApi";
import PlayByPlayLog from "./PlayByPlayLog";
import GameField from "./GameField";
import GameMatchup from "./GameMatchup";
import { BasesDiamond } from "./BasesDiamond";
import GameLinescore from "./GameLinescore";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

type GameDetailProps = {
    gamePk: number;
    sportId?: number;
    season?: number;
    showdownSet?: string;
    /** When false, stops auto-refresh polling (e.g. user switched to another tab) */
    isActive?: boolean;
    className?: string;
    onBack: () => void;
};

const cardDefenseForPosition = (card: ShowdownBotCard | undefined, position: string | null) =>
    defenseAtPosition(card?.positions_and_defense, position);

export default function GameDetail({ gamePk, sportId, season, showdownSet, isActive = true, className, onBack }: GameDetailProps) {
    const [boxscore, setBoxscore] = useState<GameBoxscoreDetail | null>(null);
    const [cardMap, setCardMap] = useState<CardMap>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isLoadingCards, setIsLoadingCards] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [selectedCard, setSelectedCard] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [isFieldExpanded, setIsFieldExpanded] = useState(false);
    const [sheetSnap, setSheetSnap] = useState<SnapPoint>('closed');
    const handleModalCardClose = () => {
        setSelectedCard(null);
    };

    // The new panels all render from the canonical GameView; the raw boxscore stays the source
    // for the batting/pitching tables and game info, which carry MLB-only detail.
    const view = useMemo(() => (boxscore ? fromBoxscoreDetail(boxscore, sportId) : null), [boxscore, sportId]);
    const plays = useMemo(() => fromGamePlays(boxscore?.plays ?? []), [boxscore]);

    const refreshBoxscore = useCallback((silent = false) => {
        if (!silent) setIsRefreshing(true);
        return fetchGameBoxscore(gamePk).then((data) => {
            setBoxscore(data);
            return data;
        }).finally(() => {
            if (!silent) setIsRefreshing(false);
        });
    }, [gamePk]);

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
    }, [boxscore, refreshBoxscore, isActive]);

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
                setCardMap(map);
            })
            .catch(() => { /* cards are supplementary – fail silently */ })
            .finally(() => { if (!cancelled) setIsLoadingCards(false); });

        return () => { cancelled = true; };
    }, [boxscore, season, showdownSet, sportId]);

    if (isLoading) {
        return (
            <div className={`flex flex-col h-[calc(100dvh-2.5rem)] overflow-hidden ${className ?? ''}`}>
                <div className="px-4 py-2.5 border-b border-(--divider) shrink-0">
                    <BackButton onBack={onBack} />
                </div>
                <div className="flex-1 flex items-center justify-center text-(--secondary) text-sm">
                    Loading boxscore…
                </div>
            </div>
        );
    }

    if (error || !boxscore || !view) {
        return (
            <div className={`flex flex-col h-[calc(100dvh-2.5rem)] overflow-hidden ${className ?? ''}`}>
                <div className="px-4 py-2.5 border-b border-(--divider) shrink-0">
                    <BackButton onBack={onBack} />
                </div>
                <div className="flex-1 flex items-center justify-center text-red-400 text-sm">
                    {error ?? "Boxscore data unavailable."}
                </div>
            </div>
        );
    }

    const away = boxscore.teams.away;
    const home = boxscore.teams.home;
    const isFinal = view.state === "FINAL";
    const isNotStarted = view.state === "PREVIEW" || view.state === "POSTPONED";
    const isInProgress = view.state === "LIVE";
    const detailedState = view.detailedState || (isFinal ? "Final" : "In Progress");

    // The field is the mobile backdrop, so it only leads the layout once there's a live
    // situation to put on it. Before first pitch and after the final out, the panels are the page.
    const hasLiveField = true;

    /* Play-by-play gets its own column on desktop (lg), so it's split out from the rest of the
       box score. It renders at natural (uncapped) height there — its column is the one that
       scrolls (`overflow-y-auto`), same as the box-score column — rather than nesting one
       scrollbar inside another. The mobile/no-field layouts keep the original height cap. */
    const playByPlayPanelDesktop = (
        <PlayByPlayLog
            key={gamePk}
            plays={plays}
            cardMap={cardMap}
            onCardSelect={setSelectedCard}
            isLoadingCards={isLoadingCards}
            maxHeightClassName="max-h-none"
        />
    );
    const playByPlayPanelMobile = (
        <PlayByPlayLog
            key={gamePk}
            plays={plays}
            cardMap={cardMap}
            onCardSelect={setSelectedCard}
            isLoadingCards={isLoadingCards}
            maxHeightClassName="max-h-[26rem]"
        />
    );

    /* Linescore, box score and game info. On desktop this is the scrolling right column; on
       mobile it rides in the bottom sheet over the field, below the play-by-play panel. */
    const boxScorePanels = (
        <div className="@container space-y-4">
            <GameLinescore game={view} />

            {isFinal && <Decisions boxscore={boxscore} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} />}

            {isNotStarted && boxscore.probable_pitchers && (
                <ProbableStartingPitchers away={away} home={home} probablePitchers={boxscore.probable_pitchers} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} />
            )}

            {/* Below @820px the container is too narrow for both teams' tables side by side, so
                they collapse into tabs; at/above it, both Tabs.Content panels are forced visible
                (via forceMount + the @[820px] override below) and sit in a 2-column grid instead. */}
            <Tabs.Root defaultValue="away">
                <Tabs.List className="@[820px]:hidden flex gap-1 rounded-lg bg-(--background-tertiary) p-1 mb-3">
                    <Tabs.Trigger
                        value="away"
                        style={{ '--tab-bg': away.team.primary_color ?? '#374151', '--tab-text': getReadableTextColor(away.team.primary_color ?? '#374151', '#ffffff') } as CSSProperties}
                        className="flex-1 px-4 py-2 text-sm font-semibold rounded-md text-(--secondary) data-[state=active]:bg-(--tab-bg) data-[state=active]:text-(--tab-text) cursor-pointer transition-colors"
                    >
                        {away.team.abbreviation}
                    </Tabs.Trigger>
                    <Tabs.Trigger
                        value="home"
                        style={{ '--tab-bg': home.team.primary_color ?? '#374151', '--tab-text': getReadableTextColor(home.team.primary_color ?? '#374151', '#ffffff') } as CSSProperties}
                        className="flex-1 px-4 py-2 text-sm font-semibold rounded-md text-(--secondary) data-[state=active]:bg-(--tab-bg) data-[state=active]:text-(--tab-text) cursor-pointer transition-colors"
                    >
                        {home.team.abbreviation}
                    </Tabs.Trigger>
                </Tabs.List>
                <div className="grid gap-4 @[820px]:grid-cols-2 min-w-0">
                    <Tabs.Content value="away" forceMount className="min-w-0 space-y-4 data-[state=inactive]:hidden @[820px]:data-[state=inactive]:block">
                        <BattingTable team={away} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} isShowingModal={selectedCard !== null} />
                        <PitchingTable team={away} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} isShowingModal={selectedCard !== null} />
                    </Tabs.Content>
                    <Tabs.Content value="home" forceMount className="min-w-0 space-y-4 data-[state=inactive]:hidden @[820px]:data-[state=inactive]:block">
                        <BattingTable team={home} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} isShowingModal={selectedCard !== null} />
                        <PitchingTable team={home} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} isShowingModal={selectedCard !== null} />
                    </Tabs.Content>
                </div>
            </Tabs.Root>

            <GameInfo away={away} home={home} />
        </div>
    );

    const scoreHeader = (
        <ScoreHeader
            away={away}
            home={home}
            linescore={boxscore.linescore}
            sportId={sportId}
            detailedState={detailedState}
            isInProgress={isInProgress}
        />
    );

    return (
        <div className={`flex flex-col h-[calc(100dvh-2.5rem)] overflow-hidden ${className ?? ''}`}>
            <div className="px-4 py-2.5 border-b border-(--divider) shrink-0 flex items-center gap-3">
                <BackButton onBack={onBack} />
                {isRefreshing && (
                    <svg className="animate-spin h-3.5 w-3.5 text-(--secondary)" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                )}
            </div>

            {hasLiveField ? (
                <>
                    <div className="flex-1 min-h-0 lg:grid lg:grid-cols-[3fr_4fr_3fr] lg:gap-4 lg:p-4 lg:overflow-hidden">

                        <div className="hidden lg:block lg:h-full lg:min-w-0 lg:overflow-y-auto lg:pb-4">
                            {boxScorePanels}
                        </div>

                        {/* Spotlight column — the whole screen on mobile, with the sheet parked over it. */}
                        <div className="h-full overflow-y-auto space-y-4 p-0 pb-[22vh] lg:p-0 lg:pb-4 lg:min-w-0">
                            {/* Grass backdrop behind the scoreboard, field and matchup as one group —
                                faded top/bottom so it blends into the page instead of a hard edge.
                                The image is the first child with no z-index of its own, and the
                                content wrapper below it is `relative` (so it's a positioned sibling
                                too) — later DOM order among same-stacking-level positioned elements
                                paints on top, with no negative z-index needed (which can end up
                                behind an ancestor's own background instead of just this image). */}
                            <div className="relative">
                                <img
                                    src="/images/games/Grass.png"
                                    alt=""
                                    className="absolute inset-0 h-full w-full object-cover pointer-events-none select-none"
                                    style={{
                                        maskImage: 'linear-gradient(to bottom, transparent 0%, black 20%, black 80%, transparent 100%)',
                                        WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, black 20%, black 80%, transparent 100%)',
                                    }}
                                />

                                <div className="relative space-y-4 p-1">
                                    {/* The field's own score bug carries this on mobile. */}
                                    <div className="hidden lg:block">{scoreHeader}</div>

                                    <GameField
                                        game={view}
                                        cardMap={cardMap}
                                        onCardSelect={setSelectedCard}
                                        expanded={isFieldExpanded}
                                        onToggleExpanded={() => setIsFieldExpanded((expanded) => !expanded)}
                                        isLoadingCards={isLoadingCards}
                                    />

                                    <GameMatchup
                                        game={view}
                                        plays={plays}
                                        cardMap={cardMap}
                                        isLoadingCards={isLoadingCards}
                                        onCardSelect={setSelectedCard}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Play-by-play column — desktop only; it rides in the bottom sheet on mobile. */}
                        <div className="hidden lg:block lg:h-full lg:min-w-0 lg:overflow-y-auto">
                            {playByPlayPanelDesktop}
                        </div>
                    </div>

                    {/* BottomSheet is lg:hidden internally, so this is the mobile half of the split.
                        Non-dismissible: the panels are the only way to reach the box score here.
                        The handle grows to include the pitcher/batter matchup once expanded — at
                        peek it's just the title, matching the desktop field's own compact bug. */}
                    <BottomSheet
                        isOpen
                        onClose={() => {}}
                        dismissible={false}
                        onSnapChange={setSheetSnap}
                        handleContent={
                            sheetSnap === 'expanded' && view.situation
                                ? <GameMatchup game={view} cardMap={cardMap} isLoadingCards={isLoadingCards} className="mt-2" isCompactCards={true} />
                                : undefined
                        }
                    >
                        <div className="px-4 pb-[calc(2rem+var(--safe-bottom))] pt-2 h-full flex flex-col">
                            <Tabs.Root defaultValue="playbyplay" className="flex flex-col h-full min-h-0">
                                <Tabs.List className="flex gap-1 rounded-lg bg-(--background-tertiary) p-1 mb-3 shrink-0">
                                    <Tabs.Trigger
                                        value="playbyplay"
                                        className="flex-1 px-4 py-2 text-sm font-semibold rounded-md text-(--secondary) data-[state=active]:bg-(--showdown-blue) data-[state=active]:text-white cursor-pointer transition-colors"
                                    >
                                        Play By Play
                                    </Tabs.Trigger>
                                    <Tabs.Trigger
                                        value="boxscore"
                                        className="flex-1 px-4 py-2 text-sm font-semibold rounded-md text-(--secondary) data-[state=active]:bg-(--showdown-blue) data-[state=active]:text-white cursor-pointer transition-colors"
                                    >
                                        Boxscore
                                    </Tabs.Trigger>
                                </Tabs.List>
                                <Tabs.Content value="playbyplay" className="data-[state=inactive]:hidden">
                                    {playByPlayPanelMobile}
                                </Tabs.Content>
                                <Tabs.Content value="boxscore" className="data-[state=inactive]:hidden">
                                    {boxScorePanels}
                                </Tabs.Content>
                            </Tabs.Root>
                        </div>
                    </BottomSheet>
                </>
            ) : (
                <div className="flex-1 overflow-y-auto">
                    <div className="space-y-4 p-4 pb-24 lg:mx-auto lg:max-w-5xl">
                        {scoreHeader}
                        {playByPlayPanelMobile}
                        {boxScorePanels}
                    </div>
                </div>
            )}

            <div className={selectedCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={handleModalCardClose} isVisible={!!selectedCard}>
                    <CardDetail
                        showdownBotCardData={selectedCard}
                        hideTrendGraphs={true}
                        context="game_detail"
                        parent='game_detail'
                    />
                </Modal>
            </div>
        </div>
    );
}


// ─── Sub-components ──────────────────────────────────────────────

function BackButton({ onBack }: { onBack: () => void }) {
    return (
        <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1.5 text-sm font-semibold text-(--secondary) hover:text-(--primary) bg-(--background-secondary) p-2 rounded-lg cursor-pointer transition-colors"
        >
            <FaChevronLeft className="h-3 w-3" />
            Back to Games
        </button>
    );
}


function ScoreHeader({
    away,
    home,
    linescore,
    sportId,
    detailedState,
    isInProgress,
}: {
    away: BoxscoreTeamData;
    home: BoxscoreTeamData;
    linescore: GameBoxscoreDetail["linescore"];
    sportId?: number;
    detailedState: string;
    isInProgress?: boolean;
}) {
    const awayCode = countryCodeForTeam(sportId ?? 0, away.team.abbreviation);
    const homeCode = countryCodeForTeam(sportId ?? 0, home.team.abbreviation);
    const awayRecord = away.team.record;
    const homeRecord = home.team.record;

    const awayBadgeBg = away.team.primary_color ?? '#374151';
    const awayBadgeText = getReadableTextColor(awayBadgeBg, '#ffffff');
    const homeBadgeBg = home.team.primary_color ?? '#374151';
    const homeBadgeText = getReadableTextColor(homeBadgeBg, '#ffffff');

    const awayRuns = linescore.teams.away.runs ?? 0;
    const homeRuns = linescore.teams.home.runs ?? 0;

    const rawHalf = (linescore.inning_half || linescore.inning_state || '');
    const inningHalf = rawHalf.charAt(0).toUpperCase() + rawHalf.slice(1).toLowerCase();
    const inningOrdinal = linescore.current_inning_ordinal || linescore.current_inning || '';
    const inningStr = inningHalf && inningOrdinal ? `${inningHalf} ${inningOrdinal}` : String(inningOrdinal);

    const hasCount = linescore.balls != null && linescore.strikes != null;
    const bases = { first: linescore.offense?.first, second: linescore.offense?.second, third: linescore.offense?.third };

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary)/30 mx-2 p-4">
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
                {/* Away team - left aligned, score next to the badge rather than in the center */}
                <div className="flex flex-col gap-1">
                    {sportId === 51 && awayCode && (
                        <ReactCountryFlag countryCode={awayCode} svg style={{ width: '1.5em', height: '1.5em' }} />
                    )}
                    <div className="flex items-center gap-2.5">
                        <div
                            className="flex items-center justify-center w-10 h-10 rounded-lg font-bold text-sm leading-none shrink-0"
                            style={{ backgroundColor: awayBadgeBg, color: awayBadgeText }}
                        >{away.team.abbreviation}</div>
                        <span className="text-[32px] font-bold leading-none text-(--primary)">{awayRuns}</span>
                    </div>
                    <div className="text-[14px] hidden sm:block font-semibold text-(--primary) leading-snug">{away.team.name}</div>
                    {awayRecord && (
                        <div className="text-[12px] text-(--secondary)">{awayRecord.wins ?? 0}-{awayRecord.losses ?? 0}</div>
                    )}
                </div>

                {/* Center: game state, count and bases — the situational info, not the score */}
                <div className="flex flex-col items-center gap-2">
                    {isInProgress && inningStr ? (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-(--background-primary) border border-(--divider) text-[11px]">
                            <span className="live-pulse w-1.75 h-1.75 rounded-full bg-(--live) shrink-0" />
                            <span className="font-semibold tracking-[0.5px] text-(--live)">LIVE</span>
                            <span className="text-(--secondary) mx-0.5">·</span>
                            <span className="text-(--secondary)">{inningStr}</span>
                        </div>
                    ) : (
                        <div className="text-xs font-semibold text-(--secondary) uppercase tracking-wide">{detailedState}</div>
                    )}

                    {isInProgress && (
                        <div className="flex items-center gap-3">
                            {hasCount && (
                                <div className="text-center">
                                    <div className="text-[9px] uppercase tracking-wide text-(--secondary)">Count</div>
                                    <div className="text-[16px] font-bold leading-none text-(--primary)">{linescore.balls}–{linescore.strikes}</div>
                                </div>
                            )}
                            <BasesDiamond bases={bases} outs={linescore.outs} size="sm" />
                        </div>
                    )}
                </div>

                {/* Home team - right aligned, mirrored: score then badge so the abbreviation
                    anchors the outer edge same as away's */}
                <div className="flex flex-col items-end gap-1">
                    {sportId === 51 && homeCode && (
                        <div className="self-end">
                            <ReactCountryFlag countryCode={homeCode} svg style={{ width: '1.5em', height: '1.5em' }} />
                        </div>
                    )}
                    <div className="flex items-center gap-2.5">
                        <span className="text-[32px] font-bold leading-none text-(--primary)">{homeRuns}</span>
                        <div
                            className="flex items-center justify-center w-10 h-10 rounded-lg font-bold text-sm leading-none shrink-0"
                            style={{ backgroundColor: homeBadgeBg, color: homeBadgeText }}
                        >{home.team.abbreviation}</div>
                    </div>
                    <div className="text-[14px] hidden sm:block  font-semibold text-(--primary) leading-snug text-right">{home.team.name}</div>
                    {homeRecord && (
                        <div className="text-[12px] text-(--secondary)">{homeRecord.wins ?? 0}-{homeRecord.losses ?? 0}</div>
                    )}
                </div>
            </div>
        </div>
    );
}



function Decisions({ boxscore, cardMap, onCardSelect, isLoadingCards }: { boxscore: GameBoxscoreDetail; cardMap: CardMap; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isLoadingCards?: boolean }) {
    const { winner, loser, save: saveDecision } = boxscore.decisions;

    // Find the pitcher note (e.g. "(W, 1-0)") for each decision pitcher
    const findPitcherNote = (pitcherId?: number): string => {
        if (!pitcherId) return "";
        for (const side of ["away", "home"] as const) {
            const pitcher = boxscore.teams[side].pitching.find((p) => p.id === pitcherId);
            if (pitcher?.stats.note) return pitcher.stats.note;
        }
        return "";
    };

    // Standarize the rendering of each decision item (W/L/S) since they all follow the same pattern
    const decisionItem = (color: string, label: string, pitcher: BoxscoreDecisionPerson, card?: ShowdownBotCardAPIResponse) => (
        
        <div className="space-y-1">
            <div className="flex items-center gap-1.5">
                <span className={`font-bold ${color}`}>{label}:</span>
                <span className="font-semibold text-(--primary)">{pitcher?.full_name}</span>
                <span className="text-(--secondary) text-xs">{findPitcherNote(pitcher?.id)}</span>

                {card && card.in_season_trends?.pts_change.day != null && card.in_season_trends.pts_change.day !== 0 && (
                    <span className={`text-[9px] font-bold leading-none ${card.in_season_trends.pts_change.day > 0 ? 'text-(--green)' : 'text-(--red)'}`}>
                        {card.in_season_trends.pts_change.day > 0 ? '▲' : '▼'}{Math.abs(card.in_season_trends.pts_change.day)} PTS
                    </span>
                )}
            </div>
            {isLoadingCards && !card ? (
                <CardItemSkeleton className="w-full" />
            ) : (
                <CardItemFromCard card={card?.card} className="w-full" onClick={card ? () => onCardSelect?.(card) : undefined} />
            )}
        </div>
    );

    if (!winner && !loser) return null;

    const winnerCardData = winner?.id ? cardMap[cardKey(winner.id, 'P')] : undefined;
    const loserCardData = loser?.id ? cardMap[cardKey(loser.id, 'P')] : undefined;
    const saveCardData = saveDecision?.id ? cardMap[cardKey(saveDecision.id, 'P')] : undefined;

    return (
        <div 
            className="
                flex flex-col
                md:grid md:grid-cols-2
                p-3 gap-x-6 gap-y-2
                rounded-xl border border-(--divider) bg-(--background-secondary) 
                text-sm
            ">
                {winner && decisionItem('text-(--green)', 'W', winner, winnerCardData)}
                {loser && decisionItem('text-(--red)', 'L', loser, loserCardData)}
                {saveDecision && decisionItem('text-blue-400', 'SV', saveDecision, saveCardData)}
        </div>
    );
}

function ProbableStartingPitchers({
    away, home, probablePitchers, cardMap, onCardSelect, isLoadingCards
}: {
    away: BoxscoreTeamData;
    home: BoxscoreTeamData;
    probablePitchers: NonNullable<GameBoxscoreDetail["probable_pitchers"]>;
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
}) {
    const pitcherItem = (team: BoxscoreTeamData, pitcher?: { id?: number; full_name?: string }) => {
        const card = pitcher?.id ? cardMap[cardKey(pitcher.id, 'P')] : undefined;
        const badgeBg = team.team.primary_color ?? '#374151';
        const badgeText = getReadableTextColor(badgeBg, '#ffffff');
        return (
            <div className="space-y-1.5">
                <div className="flex items-center gap-1.5">
                    <span
                        className="inline-flex items-center justify-center rounded font-bold text-[11px] px-1.5 py-0.5"
                        style={{ backgroundColor: badgeBg, color: badgeText }}
                    >{team.team.abbreviation}</span>
                    <span className="font-semibold text-(--primary) text-sm">{pitcher?.full_name ?? 'TBD'}</span>
                    {card && card.in_season_trends?.pts_change.day != null && card.in_season_trends.pts_change.day !== 0 && (
                        <span className={`text-[9px] font-bold leading-none ${card.in_season_trends.pts_change.day > 0 ? 'text-(--green)' : 'text-(--red)'}`}>
                            {card.in_season_trends.pts_change.day > 0 ? '▲' : '▼'}{Math.abs(card.in_season_trends.pts_change.day)} PTS
                        </span>
                    )}
                </div>
                {isLoadingCards && !card ? (
                    <CardItemSkeleton className="w-full" />
                ) : (
                    <CardItemFromCard card={card?.card} className="w-full" onClick={card ? () => onCardSelect?.(card) : undefined} />
                )}
            </div>
        );
    };

    return (
        <div className="flex flex-col md:grid md:grid-cols-2 p-3 gap-x-6 gap-y-2 rounded-xl border border-(--divider) bg-(--background-secondary) text-sm">
            <div className="col-span-full mb-1">
                <span className="text-xs font-bold uppercase tracking-wide text-(--secondary)">Probable Starting Pitchers</span>
            </div>
            {pitcherItem(away, probablePitchers.away)}
            {pitcherItem(home, probablePitchers.home)}
        </div>
    );
}

function TablePointsSummary({ totalPoints, pointsChange, backgroundColor }: { totalPoints: number; pointsChange: number; backgroundColor?: string }) {
    if (totalPoints === 0) return null;
    
    return (
        <>
            <div className="ml-auto text-[10px] font-bold text-(--quaternary) flex gap-x-2">
                <span className={`${pointsChange < 0 ? 'text-(--red)' : pointsChange > 0 ? 'text-(--green)' : ''}`}>{pointsChange > 0 ? '▲' : pointsChange < 0 ? '▼' : ''}{pointsChange !== 0 ? Math.abs(pointsChange) : ''}</span>
                <PointsBadge points={totalPoints} bg_color={backgroundColor} className="text-[10px]"/>
            </div>
        </>
    );
}

function BattingTable({ team, sportId, cardMap, onCardSelect, isShowingModal, isLoadingCards, hasGameStarted }: { team: BoxscoreTeamData; sportId?: number; cardMap: CardMap; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isShowingModal?: boolean; isLoadingCards?: boolean; hasGameStarted?: boolean }) {
    const countryCode = countryCodeForTeam(sportId ?? 0, team.team.abbreviation);
    const badgeBg = team.team.primary_color ?? '#374151';
    const badgeBgSecondary = team.team.secondary_color ?? '#4b5563';
    const badgeText = getReadableTextColor(badgeBg, '#ffffff');
    const hasCards = Object.keys(cardMap).length > 0;

    const sortedBatters = [...team.batting]
        .filter((b) => b.batting_order != null && b.batting_order !== "")
        .sort((a, b) => {
            const orderA = a.batting_order ? parseInt(a.batting_order, 10) : 9999;
            const orderB = b.batting_order ? parseInt(b.batting_order, 10) : 9999;
            return orderA - orderB;
        });

    // PTS
    const totalPoints = hasCards
        ? sortedBatters.reduce((sum, b) => sum + (cardMap[cardKey(b.id, 'H')]?.card?.points ?? 0), 0)
        : 0;
    const totalPointsChange = hasCards && hasGameStarted
        ? sortedBatters.reduce((sum, b) => sum + (cardMap[cardKey(b.id, 'H')]?.in_season_trends?.pts_change.day ?? 0), 0)
        : 0;
    
    // CURRENT DEFENSE
    const INFIELD = new Set(['1B', '2B', '3B', 'SS']);
    const OUTFIELD = new Set(['LF', 'CF', 'RF']);
    const defTotals = hasCards
        ? sortedBatters.filter((b) => b.is_in_lineup).reduce(
            (acc, b) => {
                const card = cardMap[cardKey(b.id, 'H')]?.card ?? undefined;
                const pos = b.position.replaceAll('PH-', '');
                const val = cardDefenseForPosition(card, pos ?? null);
                if (val == null) return acc;
                if (pos === 'C')                  acc.catcher += val;
                else if (INFIELD.has(pos ?? ''))  acc.infield += val;
                else if (OUTFIELD.has(pos ?? '')) acc.outfield += val;
                return acc;
            },
            { infield: 0, outfield: 0, catcher: 0 }
        )
        : null;

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) overflow-hidden">
            <div className="px-3 py-2 border-b border-(--divider) flex items-center gap-2">
                {sportId === 51 && countryCode && (
                    <ReactCountryFlag countryCode={countryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
                )}
                <span
                    className="inline-flex items-center justify-center rounded font-bold text-[11px] px-1.5 py-0.5"
                    style={{ backgroundColor: badgeBg, color: badgeText }}
                >{team.team.abbreviation}</span>
                <span className="text-xs text-(--secondary) font-semibold">Batting</span>
                {defTotals && (
                    <div className="ml-auto flex items-center gap-x-3">
                        <span className="text-[10px] text-(--secondary)">C {defTotals.catcher >= 0 ? '+' : ''}{defTotals.catcher}</span>
                        <span className="text-[10px] text-(--secondary)">IF {defTotals.infield >= 0 ? '+' : ''}{defTotals.infield}</span>
                        <span className="text-[10px] text-(--secondary)">OF {defTotals.outfield >= 0 ? '+' : ''}{defTotals.outfield}</span>
                    </div>
                )}
                {hasCards && totalPoints > 0 && (
                    <TablePointsSummary totalPoints={totalPoints} pointsChange={totalPointsChange} backgroundColor={badgeBgSecondary} />
                )}
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-xs">
                    <thead>
                        <tr className="border-b border-(--divider) text-(--secondary) font-semibold text-[10px] tracking-[0.5px] uppercase">
                            <th className="pl-3 pr-2 py-2 text-left min-w-36">Batters</th>
                            <th className="px-2 py-2 text-right">AB</th>
                            <th className="px-2 py-2 text-right">R</th>
                            <th className="px-2 py-2 text-right">H</th>
                            <th className="px-2 py-2 text-right">RBI</th>
                            <th className="px-2 py-2 text-right">BB</th>
                            <th className="px-2 py-2 text-right">HR</th>
                            <th className="px-2 py-2 text-right">AVG</th>
                            <th className="px-2 py-2 text-right pr-3">OPS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedBatters.map((batter) => (
                            <BatterRow key={batter.id} batter={batter} cardResponse={cardMap[cardKey(batter.id, 'H')]} onCardSelect={onCardSelect} isShowingModal={isShowingModal} isLoadingCards={isLoadingCards} />
                        ))}
                        {sortedBatters.length === 0 && (
                            <tr>
                                <td colSpan={9} className="px-3 py-4 text-center text-(--secondary)">
                                    No batting data available.
                                </td>
                            </tr>
                        )}
                        <tr className="border-t border-(--divider) font-bold">
                            <td className="pl-3 pr-2 py-2 text-left text-(--primary)">Totals</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.at_bats}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.runs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.hits}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.rbi}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.base_on_balls}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.batting_totals.home_runs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)" />
                            <td className="px-2 py-2 text-right pr-3 text-(--primary)" />
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function BatterRow({ batter, cardResponse, onCardSelect, isShowingModal, isLoadingCards }: { batter: BoxscoreBatter; cardResponse?: ShowdownBotCardAPIResponse; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isShowingModal?: boolean; isLoadingCards?: boolean }) {
    const [isOpen, setIsOpen] = useState(false);
    const isSmallScreen = useIsSmallScreen();
    const { refs, floatingStyles, context } = useFloating({
        open: isOpen,
        onOpenChange: setIsOpen,
        placement: "right",           // start right, auto-flips if near edge
        middleware: [offset(8), flip(), shift({ padding: 8 })],
        whileElementsMounted: autoUpdate,
    });
    const hover = useHover(context, { delay: { open: 300, close: 100 } }); // 300ms open delay prevents flicker
    const { getReferenceProps, getFloatingProps } = useInteractions([hover]);

    const card = cardResponse?.card ?? undefined;
    const indent = batter.is_substitute;
    const hasHit = (batter.stats.hits ?? 0) > 0;

    return (
        <tr
            className={`
                border-b border-(--divider)/50 hover:bg-(--background-primary)/50 
                ${cardResponse ? 'cursor-pointer' : ''}
            `}
            onClick={cardResponse ? () => onCardSelect?.(cardResponse) : undefined}
        >
            <td 
                ref={refs.setReference} {...getReferenceProps()} 
                className={`
                    pl-3 pr-2 py-1.5 text-left
                    ${indent ? 'pl-8' : ''}
                    ${!batter.is_in_lineup ? 'opacity-60' : ''}
                `} >
                    <CardIdentityCell
                        name={batter.name} position={batter.position} hasCard={!!card}
                        isPitcher={card?.chart.is_pitcher} primaryColor={card?.image.color_primary} secondaryColor={card?.image.color_secondary}
                        command={card?.chart.command} team={card?.team} points={card?.points} positionsAndDefense={card?.positions_and_defense}
                        ptsChange={cardResponse?.in_season_trends?.pts_change.day} isLoadingCard={isLoadingCards && !cardResponse}
                    />
            </td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{batter.stats.at_bats}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{batter.stats.runs}</td>
            <td className={`px-2 py-1.5 text-right font-semibold ${hasHit ? 'text-(--primary)' : 'text-(--secondary)'}`}>{batter.stats.hits}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{batter.stats.rbi}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{batter.stats.base_on_balls}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{batter.stats.home_runs}</td>
            <td className="px-2 py-1.5 text-right text-(--secondary)">{batter.season_stats.avg}</td>
            <td className="px-2 py-1.5 text-right pr-3 text-(--secondary)">{batter.season_stats.ops}</td>
            {isOpen && card && !isShowingModal && !isSmallScreen && (
                <FloatingPortal>
                    <div
                        ref={refs.setFloating}
                        style={floatingStyles}
                        className="z-50 w-48"
                        {...getFloatingProps()}
                    >
                        <CardItemFromCard card={card} className="min-w-xs max-w-md" />
                    </div>
                </FloatingPortal>
            )}
        </tr>
    );
}

function PitchingTable({ team, sportId, cardMap, onCardSelect, isShowingModal, isLoadingCards, hasGameStarted }: { team: BoxscoreTeamData; sportId?: number; cardMap: CardMap; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isShowingModal?: boolean; isLoadingCards?: boolean; hasGameStarted?: boolean }) {
    const countryCode = countryCodeForTeam(sportId ?? 0, team.team.abbreviation);
    const badgeBg = team.team.primary_color ?? '#374151';
    const badgeBgSecondary = team.team.secondary_color ?? '#4b5563';
    const badgeText = getReadableTextColor(badgeBg, '#ffffff');

    const hasCards = Object.keys(cardMap).length > 0;

    const totalPoints = hasCards
        ? team.pitching.reduce((sum, p) => sum + (cardMap[cardKey(p.id, 'P')]?.card?.points ?? 0), 0)
        : 0;
    const totalPointsChange = hasCards && hasGameStarted
        ? team.pitching.reduce((sum, p) => sum + (cardMap[cardKey(p.id, 'P')]?.in_season_trends?.pts_change.day ?? 0), 0)
        : 0;

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) overflow-hidden">
            <div className="px-3 py-2 border-b border-(--divider) flex items-center gap-2">
                {sportId === 51 && countryCode && (
                    <ReactCountryFlag countryCode={countryCode} svg style={{ width: '1.25em', height: '1.25em' }} />
                )}
                <span
                    className="inline-flex items-center justify-center rounded font-bold text-[11px] px-1.5 py-0.5"
                    style={{ backgroundColor: badgeBg, color: badgeText }}
                >{team.team.abbreviation}</span>
                <span className="text-xs text-(--secondary) font-semibold">Pitching</span>
                {hasCards && totalPoints > 0 && (
                    <TablePointsSummary totalPoints={totalPoints} pointsChange={totalPointsChange} backgroundColor={badgeBgSecondary} />
                )}
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-xs">
                    <thead>
                        <tr className="border-b border-(--divider) text-(--secondary) font-semibold text-[10px] tracking-[0.5px] uppercase">
                            <th className="pl-3 pr-2 py-2 text-left min-w-36">Pitchers</th>
                            <th className="px-2 py-2 text-right">IP</th>
                            <th className="px-2 py-2 text-right">H</th>
                            <th className="px-2 py-2 text-right">R</th>
                            <th className="px-2 py-2 text-right">ER</th>
                            <th className="px-2 py-2 text-right">BB</th>
                            <th className="px-2 py-2 text-right">K</th>
                            <th className="px-2 py-2 text-right">HR</th>
                            <th className="px-2 py-2 text-right">P-S</th>
                            <th className="px-2 py-2 text-right pr-3">ERA</th>
                        </tr>
                    </thead>
                    <tbody>
                        {team.pitching.map((pitcher) => (
                            <PitcherRow key={pitcher.id} pitcher={pitcher} cardResponse={cardMap[cardKey(pitcher.id, 'P')]} onCardSelect={onCardSelect} isShowingModal={isShowingModal} isLoadingCards={isLoadingCards} />
                        ))}
                        {team.pitching.length === 0 && (
                            <tr>
                                <td colSpan={10} className="px-3 py-4 text-center text-(--secondary)">
                                    No pitching data available.
                                </td>
                            </tr>
                        )}
                        <tr className="border-t border-(--divider) font-bold">
                            <td className="pl-3 pr-2 py-2 text-left text-(--primary)">Totals</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.innings_pitched}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.hits}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.runs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.earned_runs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.base_on_balls}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.strike_outs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">{team.pitching_totals.home_runs}</td>
                            <td className="px-2 py-2 text-right text-(--primary)">
                                {team.pitching_totals.pitches_thrown}-{team.pitching_totals.strikes}
                            </td>
                            <td className="px-2 py-2 text-right pr-3 text-(--primary)" />
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function PitcherRow({ pitcher, cardResponse, onCardSelect, isShowingModal, isLoadingCards }: { pitcher: BoxscorePitcher; cardResponse?: ShowdownBotCardAPIResponse; onCardSelect?: (card: ShowdownBotCardAPIResponse) => void; isShowingModal?: boolean; isLoadingCards?: boolean }) {

    const [isOpen, setIsOpen] = useState(false);
    const isSmallScreen = useIsSmallScreen();
    const { refs, floatingStyles, context } = useFloating({
        open: isOpen,
        onOpenChange: setIsOpen,
        placement: "right",           // start right, auto-flips if near edge
        middleware: [offset(8), flip(), shift({ padding: 8 })],
        whileElementsMounted: autoUpdate,
    });
    const hover = useHover(context, { delay: { open: 300, close: 100 } }); // 300ms open delay prevents flicker
    const { getReferenceProps, getFloatingProps } = useInteractions([hover]);

    const card = cardResponse?.card ?? undefined;
    return (
        <tr
            className={`border-b border-(--divider)/50 hover:bg-(--background-primary)/50 ${cardResponse ? 'cursor-pointer' : ''}`}
            onClick={cardResponse ? () => onCardSelect?.(cardResponse) : undefined}
        >
            <td ref={refs.setReference} {...getReferenceProps()} className="pl-3 pr-2 py-1.5 text-left" >
                <CardIdentityCell
                    name={pitcher.name} position={'P'} hasCard={!!card}
                    isPitcher={card?.chart.is_pitcher} primaryColor={card?.image.color_primary} secondaryColor={card?.image.color_secondary}
                    command={card?.chart.command} team={card?.team} points={card?.points} positionsAndDefense={card?.positions_and_defense}
                    ptsChange={cardResponse?.in_season_trends?.pts_change.day} isLoadingCard={isLoadingCards && !cardResponse}
                />
            </td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.innings_pitched}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.hits}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.runs}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.earned_runs}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.base_on_balls}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.strike_outs}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">{pitcher.stats.home_runs}</td>
            <td className="px-2 py-1.5 text-right text-(--primary)">
                {pitcher.stats.pitches_thrown}-{pitcher.stats.strikes}
            </td>
            <td className="px-2 py-1.5 text-right pr-3 text-(--secondary)">{pitcher.season_stats.era}</td>
            {isOpen && card && !isShowingModal && !isSmallScreen && (
                <FloatingPortal>
                    <div
                        ref={refs.setFloating}
                        style={floatingStyles}
                        className="z-50 w-48"
                        {...getFloatingProps()}
                    >
                        <CardItemFromCard card={card} className="min-w-xs max-w-md" />
                    </div>
                </FloatingPortal>
            )}
        </tr>
    );
}

function GameInfo({ away, home }: { away: BoxscoreTeamData; home: BoxscoreTeamData }) {
    const allInfo = [...away.info, ...home.info];

    if (allInfo.length === 0) return null;

    return (
        <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3 space-y-3">
            <div className="font-black text-sm text-(--primary)">Game Info</div>
            {allInfo.map((section, idx) => (
                <div key={idx} className="space-y-1">
                    <div className="text-xs font-bold text-(--secondary) uppercase tracking-wide">{section.title}</div>
                    {section.fieldList.map((field, fidx) => (
                        <div key={fidx} className="flex gap-2 text-xs">
                            <span className="font-bold text-(--primary) shrink-0">{field.label}:</span>
                            <span className="text-(--secondary)">{field.value}</span>
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
}
