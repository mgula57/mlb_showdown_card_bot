import { useEffect, useRef, useState } from "react";

import { bannerTokens, NEUTRAL_TEAM_COLOR } from "../../functions/colors";
import { ordinal } from "../../functions/formatters";
import { fromBoxscoreDetail, fromGamePlays } from "../../domain/adapters/fromMlbApi";
import { fromSimGame } from "../../domain/adapters/fromSim";
import { fetchGameSimCount, startGameSim, type SimGameRecord, type SimGameResult, type StartGameSimPayload } from "../../api/simGame";
import { useAuth } from "../auth/AuthContext";
import GameSimSetupModal from "./GameSimSetupModal";
import GameSimHistoryModal from "./GameSimHistoryModal";
import SimBoxScoreTable from "./SimBoxScoreTable";
import GameBoxScoreTabs from "./GameBoxScoreTabs";
import GameLinescore from "./GameLinescore";
import { useGameDetailData } from "./useGameDetailData";
import GameDetailPlayback from "./GameDetailPlayback";
import GameDetailSkeleton from "./GameDetailSkeleton";
import GameStage, { SimTopBarControls } from "./GameStage";
import { useGameStage } from "./useGameStage";
import BackButton from "../shared/BackButton";
import { BetaBadge } from "../shared/BetaBadge";
import { Heading } from "../shared/Heading";
import ProbableStartingPitchers from "./detail/ProbableStartingPitchers";
import BattingTable from "./detail/BattingTable";
import PitchingTable from "./detail/PitchingTable";
import GameInfo from "./detail/GameInfo";
import TopBarButton from "./detail/TopBarButton";
import { FaTerminal } from "react-icons/fa";
import { FaClockRotateLeft, FaListUl } from "react-icons/fa6";
import { buttonVariantClass } from '../shared/buttonStyles';

const OUTLINE_BUTTON_CLASS = `rounded-control px-2.5 py-1.5 ${buttonVariantClass('secondary')}`;
const FEATURE_BUTTON_CLASS = `rounded-control px-3 py-1.5 text-[15px]! ${buttonVariantClass('feature')}`;

type GameDetailProps = {
    gamePk: number;
    sportId?: number;
    season?: number;
    showdownSet?: string;
    /** When false, stops auto-refresh polling (e.g. user switched to another tab) */
    isActive?: boolean;
    /** Opens the sim/takeover setup modal as soon as the game is eligible (e.g. from a "Sim this" badge) */
    openSimSetupOnMount?: boolean;
    className?: string;
    onBack: () => void;
};

export default function GameDetail({ gamePk, sportId, season, showdownSet, isActive = true, openSimSetupOnMount, className, onBack }: GameDetailProps) {
    const stage = useGameStage();
    const { selectedCard, setSelectedCard, resetForNewSim } = stage;
    // The transport strip (play/pause/scrub) is opt-in — collapsed by default so a plain live or
    // finished-game view isn't cluttered with controls most visits never touch.
    const [showPlaybackControls, setShowPlaybackControls] = useState(false);

    // Showdown simulation of this game. Non-null once one has been run; the panels then render it
    // instead of the real game until the user switches back.
    const { session } = useAuth();
    const [showSimSetup, setShowSimSetup] = useState(false);
    const [showSimHistory, setShowSimHistory] = useState(false);
    const [simResult, setSimResult] = useState<SimGameResult | null>(null);
    const [simError, setSimError] = useState<string | null>(null);
    // Bumped on every sim run. Keys `GameDetailPlayback` so a re-sim of the same game remounts the
    // playback cursor — otherwise it would keep the previous run's position (the end) and the new
    // result would show straight away instead of parking on the first pitch.
    const [simRunId, setSimRunId] = useState(0);
    // Stored sims of this game, for the badge on "Past Sims". Null until loaded (or if it fails -
    // the badge is a nicety, so a failed count just leaves it off).
    const [simCount, setSimCount] = useState<number | null>(null);
    useEffect(() => {
        let isCancelled = false;
        fetchGameSimCount(gamePk)
            .then((count) => { if (!isCancelled) setSimCount(count); })
            .catch(() => { if (!isCancelled) setSimCount(null); });
        return () => { isCancelled = true; };
    }, [gamePk]);

    // A loaded sim shows the cards it was played with (possibly another user's set), not the viewer's.
    const cardShowdownSet = simResult?.showdown_set ?? showdownSet;
    const {
        boxscore, bufferedBoxscore, cardMap, isLoading, isRefreshing, isLoadingCards, error,
        setLivePaused, applyBuffer,
    } = useGameDetailData({ gamePk, sportId, season, showdownSet: cardShowdownSet, isActive, simResult });

    // Deep-linked from a "Sim this" badge — open the setup modal as soon as we know the game is
    // still simulatable. Guarded by a ref (not just the prop) since the caller clears the
    // triggering query param right after navigating, which would otherwise re-run this on every
    // boxscore refresh.
    const hasAutoOpenedSimSetupRef = useRef(false);
    useEffect(() => {
        if (!openSimSetupOnMount || hasAutoOpenedSimSetupRef.current || !boxscore) return;
        hasAutoOpenedSimSetupRef.current = true;
        const state = fromBoxscoreDetail(boxscore, sportId).state;
        if (state === "PREVIEW" || state === "LIVE") {
            setShowSimSetup(true);
        }
    }, [openSimSetupOnMount, boxscore, sportId]);

    // The new panels all render from the canonical GameView; the raw boxscore stays the source
    // for the batting/pitching tables and game info, which carry MLB-only detail. The actual
    // play-by-play log rendered on screen is playback-aware (`activePlays`, from
    // `GameDetailPlayback` below) — `realPlays` here is only used to size the live-pause buffer badge.
    const realView = boxscore ? fromBoxscoreDetail(boxscore, sportId) : null;
    const realPlays = fromGamePlays(boxscore?.plays ?? []);

    const simView = simResult ? fromSimGame(simResult.game) : null;
    const view = simView ?? realView;

    if (isLoading) {
        return <GameDetailSkeleton className={className} onBack={onBack} />;
    }

    if (error || !boxscore || !view) {
        return (
            <div className={`flex flex-col md:tall:h-[calc(100dvh-2.5rem)] overflow-hidden ${className ?? ''}`}>
                <div className="px-4 py-2.5 border-b border-(--divider) shrink-0">
                    <BackButton onBack={onBack} />
                </div>
                <div className="flex-1 flex items-center justify-center text-(--red) text-sm">
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
    // cursor so you can scrub back; the top bar then turns into the colored REPLAY strip and its
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
        setSimCount((count) => (count ?? 0) + 1);
        setSimError(null);
        setShowSimSetup(false);
        setSimRunId((n) => n + 1);
        resetForNewSim();
        // The sim opens parked on the first pitch (see GameDetailPlayback) with its result hidden,
        // so the transport strip needs to be visible for the user to play through it.
        setShowPlaybackControls(true);
    }

    /** Reopens a previously stored sim of this same game, exactly as if it had just been run. */
    function handleSelectSim(record: SimGameRecord) {
        if (!record.result) {
            setSimError("That simulation could not be loaded.");
            return;
        }
        setSimResult(record.result);
        setSimError(null);
        setShowSimHistory(false);
        setSimRunId((n) => n + 1);
        resetForNewSim();
        setShowPlaybackControls(true);
    }

    /* Mode strip in the team builder's idiom: a flat fill in the away club's color (the side
       the title sits on) so it reads as this game's own. Full-bleed at the top of the page
       rather than inside a panel — it is a statement about the whole view, not the box score. */
    const modeBarColor = away.team.primary_color ?? NEUTRAL_TEAM_COLOR;
    const simBarTokens = bannerTokens(modeBarColor);

    /* Linescore, box score and game info. On desktop this is the scrolling right column; on
       mobile it rides in the bottom sheet over the field, below the play-by-play panel. A real
       game's tables read the raw, CURRENT boxscore regardless of playback position (the MLB
       timeline freezes them — see `GameTimeline.frozen`); a sim's read `activeView`, which carries
       a box score rebuilt per frame. */
    const boxScorePanels = (activeView: typeof view, hideResult: boolean) => (
        <div className="@container space-y-4">
            <GameLinescore game={activeView} />

            {/* Probables come off the real feed, so they only make sense for it. (W/L/SV live in
                the post-game recap over the field.) */}
            {!simResult && isNotStarted && boxscore.probable_pitchers && (
                <ProbableStartingPitchers away={away} home={home} probablePitchers={boxscore.probable_pitchers} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} />
            )}

            {/* A sim's box score is rebuilt play by play (it rides on `activeView`), except for a
                legacy log with no player ids — that one is frozen at the final line, so while the
                user is watching the replay we hide it outright rather than spoil the result. */}
            {hideResult ? (
                <div className="rounded-card border border-(--divider) bg-(--background-secondary)/30 p-6 text-center">
                    <Heading level="panel" as="div">Box score hidden during replay</Heading>
                    <div className="mt-1 text-[12px] text-(--text-secondary)">
                        The full line reveals when the replay reaches the end — or use “Skip to result” to jump ahead.
                    </div>
                </div>
            ) : (
                <GameBoxScoreTabs
                    awayLabel={away.team.abbreviation}
                    homeLabel={home.team.abbreviation}
                    renderSide={(side) => {
                        const team = side === 'away' ? away : home;
                        const simSide = activeView[side].boxscore;
                        return simResult && simSide ? (
                            <SimBoxScoreTable boxscore={simSide} cardMap={cardMap} onCardSelect={setSelectedCard} />
                        ) : (
                            <>
                                <BattingTable team={team} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} isShowingModal={selectedCard !== null} />
                                <PitchingTable team={team} sportId={sportId} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} hasGameStarted={!isNotStarted} isShowingModal={selectedCard !== null} />
                            </>
                        );
                    }}
                />
            )}

            {/* The real feed's game notes - hidden only alongside a frozen sim box score above. */}
            {!hideResult && <GameInfo away={away} home={home} />}
        </div>
    );

    return (
        <GameDetailPlayback
            key={`${gamePk}:${simRunId}`}
            boxscore={boxscore}
            sportId={sportId}
            realState={realView?.state ?? "PREVIEW"}
            simResult={simResult}
            bufferedCount={bufferedBoxscore ? fromGamePlays(bufferedBoxscore.plays ?? []).length - realPlays.length : 0}
            onApplyBuffer={bufferedBoxscore ? applyBuffer : undefined}
        >
            {({ activeView, activePlays, playbackBar, playbackControls, playbackState, isReplaying, isBoxscoreFrozen }) => {
                /* A sim whose cursor hasn't reached the end yet — the user is still playing through
                   it and shouldn't see the final score or box score. `isReplaying` goes false only
                   once the cursor sits on the last frame (played to the end, or "Skip to result"). */
                const simMidReplay = !!simResult && isReplaying;

                /* A live game that's merely catching up on new plays (cursor trailing the live edge
                   while auto-following) isn't a replay the user opened — flashing the REPLAY strip
                   for a few seconds each time a poll lands would just be noise. Only treat the
                   trailing cursor as a review once the user has opened the transport bar. */
                const isReviewing = isReplaying && !(isLiveReal && !showPlaybackControls);

                /* Sim and replay both take over the page's own top bar as their mode strip rather
                   than adding a separate banner, so only the label and controls are built here. */
                const isReplayMode = !simResult && (isReviewing || showPlaybackControls);
                const isModeBar = !!simResult || isReplayMode;
                const modeLabel = simResult
                    ? (simResult.is_takeover ? 'TAKEOVER SIM' : 'SHOWDOWN SIM')
                    : isReplayMode ? 'REPLAY' : null;
                const modeDetail = simResult
                    ? (simResult.is_takeover && simResult.setup.start_state
                        ? `— took over in the ${simResult.setup.start_state.is_top ? 'top' : 'bottom'} of the ${ordinal(simResult.setup.start_state.inning)}`
                        : '— played from the first pitch')
                    : isReplayMode
                        ? (isReviewing
                            ? '— reviewing an earlier point in the game'
                            : isLiveReal
                                ? '— live updates paused while you scrub'
                                : '— playback controls open')
                        : null;
                const modeButtonClass = `rounded-control px-2 py-1 h-7 ${simBarTokens.btnClass}`;

                return (
                    <GameStage
                        stage={stage}
                        game={activeView}
                        plays={activePlays}
                        playbackState={playbackState}
                        playbackControls={playbackControls}
                        isReplaying={isReplaying}
                        // A takeover sim is a finished game the user will want to scrub through play
                        // by play, so its transport strip is shown up front rather than hidden behind
                        // the Replay toggle.
                        playbackBar={showPlaybackControls || simResult ? playbackBar : null}
                        detailedState={detailedState}
                        cardMap={cardMap}
                        isLoadingCards={isLoadingCards}
                        isSim={!!simResult}
                        gameKey={gamePk}
                        title="Showdown Live"
                        titleAccessory={<BetaBadge />}
                        modeBarColor={isModeBar ? modeBarColor : undefined}
                        onBack={onBack}
                        topBarStatus={
                            <>
                                {modeLabel && (
                                    <span className="hidden min-w-0 truncate whitespace-nowrap text-[11px] font-bold" style={{ color: simBarTokens.fill }}>
                                        {modeLabel}
                                        <span className="hidden md:inline font-normal ml-4">{modeDetail}</span>
                                    </span>
                                )}

                                {simError && <span className="text-[11px] text-(--red)">{simError}</span>}
                                {isRefreshing && (
                                    <svg className="animate-spin h-3.5 w-3.5 text-(--secondary)" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                )}
                            </>
                        }
                        topBarActions={
                            <>
                                {simResult && (
                                    <SimTopBarControls
                                        cursor={playbackState.cursor}
                                        controls={playbackControls}
                                        isMidReplay={simMidReplay}
                                        onExit={() => { setSimResult(null); setShowPlaybackControls(false); stage.setIsRecapDismissed(false); }}
                                        buttonClass={modeButtonClass}
                                    />
                                )}
                                {isReplayMode && (
                                    <TopBarButton
                                        label="Exit Replay"
                                        shortLabel="Exit"
                                        onClick={() => { playbackControls.seekToLive(); exitReplay(); }}
                                        className={modeButtonClass}
                                    />
                                )}

                                {/* Enters replay: reveals the transport bar and, on a live game,
                                    freezes the live cursor so you can scrub back. Once active the
                                    colored REPLAY top bar takes over — its "Exit Replay" is the way
                                    out — so this button hides to keep a single, obvious control. */}
                                {!isReviewing && !showPlaybackControls && !isNotStarted && (
                                    <TopBarButton label="Replay" icon={<FaClockRotateLeft size={12} />} onClick={enterReplay} className={OUTLINE_BUTTON_CLASS} />
                                )}
                                {/* Independent of `canSimulate` - a finished game can still have
                                    sims run against it while it was live/upcoming, worth revisiting. */}
                                {!isModeBar && (
                                    <TopBarButton
                                        label="Past Sims"
                                        icon={<FaListUl size={12} />}
                                        badge={simCount ?? undefined}
                                        onClick={() => { setSimError(null); setShowSimHistory(true); }}
                                        className={OUTLINE_BUTTON_CLASS}
                                    />
                                )}
                                {canSimulate && !isModeBar && (
                                    <TopBarButton
                                        label="Simulate"
                                        icon={<FaTerminal />}
                                        onClick={() => { setSimError(null); setShowSimSetup(true); }}
                                        className={FEATURE_BUTTON_CLASS}
                                    />
                                )}
                            </>
                        }
                        boxScorePanels={boxScorePanels(activeView, simMidReplay && isBoxscoreFrozen)}
                        belowPlaybackBar={!simResult && isNotStarted && boxscore.probable_pitchers && (
                            <ProbableStartingPitchers away={away} home={home} probablePitchers={boxscore.probable_pitchers} cardMap={cardMap} onCardSelect={setSelectedCard} isLoadingCards={isLoadingCards} />
                        )}
                        className={className}
                    >
                        {showSimSetup && (
                            <GameSimSetupModal
                                gamePk={gamePk}
                                showdownSet={showdownSet ?? '2000'}
                                onCancel={() => setShowSimSetup(false)}
                                onStart={handleStartSim}
                            />
                        )}

                        {showSimHistory && (
                            <GameSimHistoryModal
                                gamePk={gamePk}
                                onClose={() => setShowSimHistory(false)}
                                onSelect={handleSelectSim}
                            />
                        )}
                    </GameStage>
                );
            }}
        </GameDetailPlayback>
    );
}
