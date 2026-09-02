import { useState, type CSSProperties } from "react";

import { bannerTokens, getReadableTextColor } from "../../functions/colors";
import { ordinal } from "../../functions/formatters";
import { Modal } from "../shared/Modal";
import { ModeBanner } from "../shared/ModeBanner";
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { CardDetail } from "../cards/CardDetail";
import * as Tabs from '@radix-ui/react-tabs';
import { Tabs as TabButtons, type TabItem } from '../shared/Tabs';
import { fromBoxscoreDetail, fromGamePlays } from "../../domain/adapters/fromMlbApi";
import { fromSimGame } from "../../domain/adapters/fromSim";
import { startGameSim, type SimGameResult, type StartGameSimPayload } from "../../api/simGame";
import { useAuth } from "../auth/AuthContext";
import GameSimSetupModal from "./GameSimSetupModal";
import SimBoxScoreTable from "./SimBoxScoreTable";
import PlayByPlayLog from "./PlayByPlayLog";
import GameField from "./GameField";
import GameMatchup from "./GameMatchup";
import GameLinescore from "./GameLinescore";
import { useGameDetailData } from "./useGameDetailData";
import GameDetailPlayback from "./GameDetailPlayback";
import BackButton from "../shared/BackButton";
import ScoreHeader from "./detail/ScoreHeader";
import Decisions from "./detail/Decisions";
import ProbableStartingPitchers from "./detail/ProbableStartingPitchers";
import BattingTable from "./detail/BattingTable";
import PitchingTable from "./detail/PitchingTable";
import GameInfo from "./detail/GameInfo";
import { FaTerminal, FaRing, FaTable, FaList } from "react-icons/fa";
import { FaClockRotateLeft } from "react-icons/fa6";

type MobileTab = 'field' | 'playbyplay' | 'boxscore';

const MOBILE_TABS: TabItem<MobileTab>[] = [
    { id: 'field', label: 'Field View', icon: <FaRing />},
    { id: 'playbyplay', label: 'Play By Play', icon: <FaList /> },
    { id: 'boxscore', label: 'Boxscore', icon: <FaTable /> },
];

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

export default function GameDetail({ gamePk, sportId, season, showdownSet, isActive = true, className, onBack }: GameDetailProps) {
    const [selectedCard, setSelectedCard] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [isFieldExpanded, setIsFieldExpanded] = useState(false);
    const [mobileTab, setMobileTab] = useState<MobileTab>('field');
    // The transport strip (play/pause/scrub) is opt-in — collapsed by default so a plain live or
    // finished-game view isn't cluttered with controls most visits never touch.
    const [showPlaybackControls, setShowPlaybackControls] = useState(false);
    const handleModalCardClose = () => {
        setSelectedCard(null);
    };

    // Showdown simulation of this game. Non-null once one has been run; the panels then render it
    // instead of the real game until the user switches back.
    const { session } = useAuth();
    const [showSimSetup, setShowSimSetup] = useState(false);
    const [simResult, setSimResult] = useState<SimGameResult | null>(null);
    const [simError, setSimError] = useState<string | null>(null);

    const {
        boxscore, bufferedBoxscore, cardMap, isLoading, isRefreshing, isLoadingCards, error,
        setLivePaused, applyBuffer,
    } = useGameDetailData({ gamePk, sportId, season, showdownSet, isActive, simResult });

    // The new panels all render from the canonical GameView; the raw boxscore stays the source
    // for the batting/pitching tables and game info, which carry MLB-only detail. The actual
    // play-by-play log rendered on screen is playback-aware (`activePlays`, from
    // `GameDetailPlayback` below) — `realPlays` here is only used to size the live-pause buffer badge.
    const realView = boxscore ? fromBoxscoreDetail(boxscore, sportId) : null;
    const realPlays = fromGamePlays(boxscore?.plays ?? []);

    const simView = simResult ? fromSimGame(simResult.game) : null;
    const view = simView ?? realView;

    if (isLoading) {
        return (
            <div className={`flex flex-col md:h-[calc(100dvh-2.5rem)] overflow-hidden ${className ?? ''}`}>
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
            <div className={`flex flex-col md:h-[calc(100dvh-2.5rem)] overflow-hidden ${className ?? ''}`}>
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
    const detailedState = simResult
        ? `Simulated Final${simResult.is_takeover ? " · Taken Over" : ""}`
        : view.detailedState || (isFinal ? "Final" : "In Progress");

    // Whether the real game still has innings left to play. A finished game can only be re-watched.
    const realState = realView?.state;
    const canSimulate = realState === "PREVIEW" || realState === "LIVE";
    // const canSimulate = false; // TODO: Enable simulation when appropriate

    // "Replay mode" = the transport bar is open. Entering it freezes a live game's
    // cursor so you can scrub back; the colored REPLAY banner then shows and its
    // "Exit Replay" is the only way out (the toolbar button hides while it's on),
    // so users always know where they are. Exiting resumes live and flushes the
    // plays that buffered while paused.
    const isLiveReal = !simResult && realView?.state === "LIVE";
    const enterReplay = () => {
        setShowPlaybackControls(true);
        if (isLiveReal) setLivePaused(true);
    };
    const exitReplay = () => {
        setShowPlaybackControls(false);
        if (isLiveReal) {
            if (bufferedBoxscore) applyBuffer();
            setLivePaused(false);
        }
    };

    async function handleStartSim(payload: StartGameSimPayload) {
        const token = session?.access_token;
        if (!token) throw new Error("Sign in to simulate a game.");
        const { result } = await startGameSim(gamePk, payload, token);
        setSimResult(result);
        setSimError(null);
        setShowSimSetup(false);
    }

    /* Mode strip in the team builder's idiom, coloured by the two clubs so it reads as this
       game's own. Full-bleed at the top of the page rather than inside a panel — it is a
       statement about the whole view, not about the box score. */
    const simBannerTokens = bannerTokens(home.team.secondary_color ?? '#374151');

    // The field is the mobile backdrop, so it only leads the layout once there's a live
    // situation to put on it. Before first pitch and after the final out, the panels are the page.
    const hasLiveField = true;

    /* Linescore, box score and game info. On desktop this is the scrolling right column; on
       mobile it rides in the bottom sheet over the field, below the play-by-play panel. Box score
       tables stay reading the raw, CURRENT boxscore regardless of playback position — the
       timeline freezes them (see `GameTimeline.frozen`) rather than reconstructing per-play
       cumulative stats, so there's nothing playback-aware to swap in here. */
    const boxScorePanels = (activeView: typeof view) => (
        <div className="@container space-y-4">
            <GameLinescore game={activeView} />

            {/* Decisions and probables come off the real feed, so they only make sense for it. */}
            {!simResult && isFinal && <Decisions boxscore={boxscore} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} />}

            {!simResult && isNotStarted && boxscore.probable_pitchers && (
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
                    {(['away', 'home'] as const).map((side) => {
                        const team = side === 'away' ? away : home;
                        const simSide = view[side].boxscore;
                        return (
                            <Tabs.Content key={side} value={side} forceMount className="min-w-0 space-y-4 data-[state=inactive]:hidden @[820px]:data-[state=inactive]:block">
                                {simResult && simSide ? (
                                    <SimBoxScoreTable boxscore={simSide} cardMap={cardMap} onCardSelect={setSelectedCard} />
                                ) : (
                                    <>
                                        <BattingTable team={team} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} isShowingModal={selectedCard !== null} />
                                        <PitchingTable team={team} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} isShowingModal={selectedCard !== null} />
                                    </>
                                )}
                            </Tabs.Content>
                        );
                    })}
                </div>
            </Tabs.Root>

            <GameInfo away={away} home={home} />
        </div>
    );

    return (
        <GameDetailPlayback
            key={gamePk}
            boxscore={boxscore}
            sportId={sportId}
            realState={realView?.state ?? "PREVIEW"}
            simResult={simResult}
            bufferedCount={bufferedBoxscore ? fromGamePlays(bufferedBoxscore.plays ?? []).length - realPlays.length : 0}
            onApplyBuffer={bufferedBoxscore ? applyBuffer : undefined}
        >
            {({ activeView, activePlays, playbackBar, playbackControls, playbackState, isReplaying }) => {
                /* `ScoreHeader` reads `detailedState` off the `GameView` it's given, so the sim/
                   finished-game label computed above rides along on a shallow-copied view rather
                   than as a prop. It's a no-op on every non-terminal playback frame — those report
                   `state: "LIVE"`, and `ScoreHeader` only reads `detailedState` once state is FINAL. */
                const headerView = { ...activeView, detailedState };
                const scoreHeader = <ScoreHeader game={headerView} />;

                const playByPlayPanelDesktop = (
                    <PlayByPlayLog
                        key={gamePk}
                        plays={activePlays}
                        cardMap={cardMap}
                        onCardSelect={setSelectedCard}
                        isLoadingCards={isLoadingCards}
                        maxHeightClassName="max-h-none"
                    />
                );
                const playByPlayPanelMobile = (
                    <PlayByPlayLog
                        key={gamePk}
                        plays={activePlays}
                        cardMap={cardMap}
                        onCardSelect={setSelectedCard}
                        isLoadingCards={isLoadingCards}
                        maxHeightClassName="max-h-[26rem]"
                    />
                );

                const panels = boxScorePanels(activeView);

                /* Mode strip: sim banner gets a "Watch" button that jumps to the first pitch and
                   starts playback; a finished real game under active review gets its own REPLAY strip
                   with an "Exit Replay" action that jumps back to the live/final edge. Only one of
                   the two is ever relevant at once — a sim result is never mid-live-review. */
                const modeBanner = simResult ? (
                    <ModeBanner
                        primaryColor={away.team.primary_color ?? '#374151'}
                        secondaryColor={home.team.secondary_color ?? '#374151'}
                        label={simResult.is_takeover ? 'TAKEOVER SIM' : 'SHOWDOWN SIM'}
                        detail={
                            simResult.is_takeover && simResult.setup.start_state
                                ? `— took over in the ${simResult.setup.start_state.is_top ? 'top' : 'bottom'} of the ${ordinal(simResult.setup.start_state.inning)}`
                                : '— played from the first pitch'
                        }
                    >
                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                onClick={() => { playbackControls.seekToStart(); playbackControls.play(); }}
                                className={`flex items-center gap-1 rounded-lg px-2 py-1 h-7 text-[11px] font-bold cursor-pointer transition-colors ${simBannerTokens.btnClass}`}
                            >
                                Watch
                            </button>
                            <button
                                type="button"
                                onClick={() => setSimResult(null)}
                                className={`flex items-center gap-1 rounded-lg px-2 py-1 h-7 text-[11px] font-bold cursor-pointer transition-colors ${simBannerTokens.btnClass}`}
                            >
                                Exit Sim
                            </button>
                        </div>
                    </ModeBanner>
                ) : (isReplaying || showPlaybackControls) ? (
                    <ModeBanner
                        primaryColor={away.team.primary_color ?? '#374151'}
                        secondaryColor={home.team.secondary_color ?? '#374151'}
                        label="REPLAY"
                        detail={
                            isReplaying
                                ? "— reviewing an earlier point in the game"
                                : isLiveReal
                                    ? "— live updates paused while you scrub"
                                    : "— playback controls open"
                        }
                    >
                        <button
                            type="button"
                            onClick={() => { playbackControls.seekToLive(); exitReplay(); }}
                            className={`flex items-center gap-1 rounded-lg px-2 py-1 h-7 text-[11px] font-bold cursor-pointer transition-colors ${simBannerTokens.btnClass}`}
                        >
                            Exit Replay
                        </button>
                    </ModeBanner>
                ) : null;

                return (
                    <div className={`flex flex-col md:h-[calc(100dvh-2.5rem)] overflow-hidden ${className ?? ''}`}>
                        <div className="relative z-50 px-4 py-2 border-b border-(--divider) bg-(--background-primary) shrink-0 flex items-center gap-3">
                            <BackButton onBack={onBack} />
                            {canSimulate && !simResult && (
                                <button
                                    type="button"
                                    onClick={() => { setSimError(null); setShowSimSetup(true); }}
                                    className="flex items-center gap-x-1 cursor-pointer rounded-lg bg-(--secondary) px-3 py-1.5 text-[11px] font-bold text-(--background-primary) transition-opacity hover:opacity-90"
                                >
                                    <FaTerminal />
                                    {realState === "LIVE" ? "Take Over" : "Simulate"}
                                </button>
                            )}
                            {simError && <span className="text-[11px] text-(--red)">{simError}</span>}
                            {isRefreshing && (
                                <svg className="animate-spin h-3.5 w-3.5 text-(--secondary)" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                            )}
                            <div className="ml-auto flex items-center gap-2">
                                {/* Enters replay: reveals the transport bar and, on a live game,
                                    freezes the live cursor so you can scrub back. Once active the
                                    colored REPLAY banner takes over — its "Exit Replay" is the way
                                    out — so this button hides to keep a single, obvious control. */}
                                {!isReplaying && !showPlaybackControls && (
                                    <button
                                        type="button"
                                        onClick={enterReplay}
                                        className="flex items-center gap-x-1 cursor-pointer rounded-lg border border-(--divider) px-2.5 py-1.5 text-[11px] font-bold text-(--secondary) hover:text-(--primary) transition-colors"
                                    >
                                        <FaClockRotateLeft size={12} />
                                        Replay
                                    </button>
                                )}
                            </div>
                        </div>

                        {modeBanner}

                        {hasLiveField ? (
                            <>
                                {/* Mobile: one tab strip swaps between the three columns that sit
                                    side-by-side on desktop. Above `lg` the strip is hidden and all
                                    three columns show at once. */}
                                <div className="lg:hidden shrink-0">
                                    <TabButtons tabs={MOBILE_TABS} value={mobileTab} onChange={setMobileTab} className="px-2" fullWidth />
                                </div>

                                <div className="flex-1 min-h-0 lg:grid lg:grid-cols-[3fr_4fr_3fr] lg:gap-4 lg:px-4 lg:overflow-hidden">

                                    <div className={`${mobileTab === 'boxscore' ? 'block' : 'hidden'} h-full min-w-0 overflow-y-auto p-4 pb-[calc(6rem+var(--safe-bottom))] scrollbar-hide lg:block lg:py-4 lg:px-0 lg:pb-4`}>
                                        {panels}
                                    </div>

                                    {/* Spotlight column — field, playback bar and matchup. */}
                                    <div className={`${mobileTab === 'field' ? 'block' : 'hidden'} h-full overflow-y-auto space-y-4 p-0 pb-[calc(6rem+var(--safe-bottom))] scrollbar-hide lg:block lg:py-4 lg:px-0 lg:min-w-0`}>
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
                                                {/* Scoreboard bleeds over the grass on both breakpoints — compact
                                                    (no records, smaller type) on mobile, full-size on desktop. */}
                                                <ScoreHeader game={headerView} compact className="lg:hidden" />
                                                <div className="hidden lg:block">{scoreHeader}</div>

                                                <GameField
                                                    game={activeView}
                                                    cardMap={cardMap}
                                                    onCardSelect={setSelectedCard}
                                                    expanded={isFieldExpanded}
                                                    onToggleExpanded={() => setIsFieldExpanded((expanded) => !expanded)}
                                                    isLoadingCards={isLoadingCards}
                                                    transition={playbackState.transition}
                                                    pendingPlay={playbackState.pendingPlay}
                                                    phase={playbackState.phase}
                                                    lastPlay={activePlays[0]}
                                                />

                                                {/* A takeover sim is a finished game the user will want to scrub
                                                    through play by play, so its transport strip is shown up front
                                                    rather than hidden behind the Replay toggle. */}
                                                {(showPlaybackControls || simResult?.is_takeover) && playbackBar}

                                                <GameMatchup
                                                    game={activeView}
                                                    plays={activePlays}
                                                    cardMap={cardMap}
                                                    isLoadingCards={isLoadingCards}
                                                    onCardSelect={setSelectedCard}
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Play-by-play column */}
                                    <div className={`${mobileTab === 'playbyplay' ? 'block' : 'hidden'} h-full min-w-0 overflow-y-auto p-4 pb-[calc(6rem+var(--safe-bottom))] scrollbar-hide lg:block lg:py-4 lg:px-0 lg:pb-0`}>
                                        {playByPlayPanelDesktop}
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="flex-1 overflow-y-auto">
                                <div className="space-y-4 p-4 pb-[calc(6rem+var(--safe-bottom))] lg:mx-auto lg:max-w-5xl">
                                    {scoreHeader}
                                    {playByPlayPanelMobile}
                                    {panels}
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

                        {showSimSetup && (
                            <GameSimSetupModal
                                gamePk={gamePk}
                                showdownSet={showdownSet ?? '2000'}
                                onCancel={() => setShowSimSetup(false)}
                                onStart={handleStartSim}
                            />
                        )}
                    </div>
                );
            }}
        </GameDetailPlayback>
    );
}
