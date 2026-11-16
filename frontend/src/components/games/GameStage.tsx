/**
 * @fileoverview The game screen's layout: the top bar, the `GameBoard` and a rail of tabs holding
 * the play-by-play, box score and game info. Purely presentational over the current playback frame,
 * so any host with a `GameTimeline` can use it. What differs between hosts arrives as slots: the
 * box score panel, the top bar's controls and anything under the bar.
 */
import { useMemo, useRef, useState, type Key, type ReactNode } from "react";
import { FaRing } from "react-icons/fa";
import { FaStar } from "react-icons/fa6";

import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { bannerTokens } from "../../functions/colors";
import type { GameView } from "../../domain/game";
import { advantageSideOf, type AdvantageSide, type PlayEntry } from "../../domain/play";
import type { GamePlaybackControls, GamePlaybackState } from "../../hooks/useGamePlayback";
import { useIsWiderThan } from "../../hooks/useIsWiderThan";
import { useMediaQuery } from "../../hooks/useMediaQuery";
import { useResizablePanel } from "../../hooks/useResizablePanel";
import { CardDetail } from "../cards/CardDetail";
import BackButton from "../shared/BackButton";
import { Heading } from "../shared/Heading";
import { Modal } from "../shared/Modal";
import { ResizeHandle } from "../shared/ResizeHandle";
import { Tabs as TabButtons, type TabItem } from "../shared/Tabs";
import { buttonVariantClass } from "../shared/buttonStyles";
import GameBoard, { NARROW_FIELD_ZOOM } from "./GameBoard";
import { LineupUpContext } from "./lineupUpContext";
import { lineupUp, withLineupDefense } from "../../domain/lineup";
import ScoreboardIsland, { type TeamAnnouncement, type TeamStatus } from "./ScoreboardIsland";
import { GameScoreTrack, LastPlayLine } from "./GameBoardPanels";
import GameField, { type RollPrompt } from "./GameField";
import GameLinescore from "./GameLinescore";
import GameMatchup, { MatchupSide } from "./GameMatchup";
import PlayByPlayLog from "./PlayByPlayLog";
import { resolveMatchup } from "./resolveMatchup";
import GameFinalSummary from "./detail/GameFinalSummary";
import ScoreHeader from "./detail/ScoreHeader";
import TopBarButton from "./detail/TopBarButton";
import type { StrategyBoardSlots } from "./strategy/strategyBoard";
import type { GameStageState, RailTab } from "./useGameStage";

/** A phone's tabs: the field, then the rail's panels, each taking the whole page. */
type PhoneTab = 'field' | RailTab;
const FIELD_TAB: TabItem<PhoneTab> = { id: 'field', label: 'Field' };

const RAIL_TABS: TabItem<RailTab>[] = [
    { id: 'playbyplay', label: 'Plays' },
    { id: 'boxscore', label: 'Box Score' },
    { id: 'info', label: 'Info' },
];

/** Room for two full cards along the bottom edge. Narrower than this the board stacks. */
const WIDE_BOARD_MIN_WIDTH = 736;

/** The rail sits beside the board from `md` up, resized by its width with the board keeping enough
 *  room to stay usable. Below that a phone swaps between them with tabs (`PhoneTab`). */
const SIDE_RAIL_QUERY = '(width >= 48rem)';
const RAIL_MIN_WIDTH = 288;
const BOARD_MIN_WIDTH = 360;
const railMaxWidth = (container: number) => Math.min(960, container - BOARD_MIN_WIDTH);

const RAIL_PANEL_CLASS = 'min-h-0 flex-1 overflow-y-auto p-4 pb-[calc(1rem+var(--safe-bottom))] scrollbar-hide';

type GameStageProps = {
    stage: GameStageState;
    game: GameView;
    /** Plays revealed so far, newest first. */
    plays: PlayEntry[];
    playbackState: GamePlaybackState;
    playbackControls: GamePlaybackControls;
    isReplaying: boolean;
    /** Null hides the transport strip. */
    playbackBar: ReactNode;
    /** The label `ScoreHeader` shows once the game is final. */
    detailedState: string;
    cardMap: Record<string, ShowdownBotCardAPIResponse>;
    isLoadingCards: boolean;
    /** Opens parked on the first pitch (a sim, or a real game opened as a replay), so the field
     *  offers its big Play button. */
    isSim: boolean;
    /** Remounts the play log when the game changes, so its scroll position doesn't carry over. */
    gameKey: Key;
    title: string;
    /** Sits beside the title, e.g. a beta badge. */
    titleAccessory?: ReactNode;
    /** Set while a mode (a sim, a replay) owns the top bar: it fills with this color. */
    modeBarColor?: string;
    onBack: () => void;
    topBarStatus?: ReactNode;
    topBarActions?: ReactNode;
    boxScorePanels: ReactNode;
    /** The rail's Info tab. Left out, the tab is too. */
    infoPanel?: ReactNode;
    /** The player's next move, a thumb-sized button in the field's bottom-right corner beside
     *  `boardTools` on every board (a live game's roll, the same one the die on the field offers). */
    boardAction?: ReactNode;
    /** Whose turn it is, grown out of the scoreboard (`ScoreboardIsland`) under the club the game
     *  is waiting on. `key` changes with the message, so a new one pops in. */
    boardTurn?: TeamStatus | null;
    /** The field's bottom-right corner on every board, e.g. the button that opens a live game's
     *  moves. */
    boardTools?: ReactNode;
    /** What each club just did (a strategy card, a substitution), dropped from under its side of
     *  the scoreboard (see `ScoreboardIsland`). */
    teamAnnouncements?: TeamAnnouncement[];
    /** Strategy cards on the board: the hand bottom left, its tray over the field, and played cards
     *  on the matchup (see `StrategyBoardSlots`). Hidden behind the recap. */
    strategy?: StrategyBoardSlots;
    /** A live game waiting on a die: see `GameField`'s `rollPrompt`. */
    rollPrompt?: RollPrompt;
    /** A live game's dice are thrown one at a time: see `GameField`'s `isHandThrown`. */
    isHandThrown?: boolean;
    /** Who won a pitch that's been rolled but not yet swung at, highlighted until the swing resolves. */
    heldAdvantage?: AdvantageSide;
    /** Shown on the board when no one is up yet, e.g. the probable pitchers. */
    preGamePanel?: ReactNode;
    className?: string;
    /** Host-owned modals. */
    children?: ReactNode;
};

export default function GameStage({
    stage, game: gameView, plays, playbackState, playbackControls, isReplaying, playbackBar, detailedState,
    cardMap, isLoadingCards, isSim, gameKey, title, titleAccessory, modeBarColor, onBack,
    topBarStatus, topBarActions, boxScorePanels, infoPanel, boardAction, boardTurn, boardTools, teamAnnouncements, strategy, rollPrompt, isHandThrown, heldAdvantage, preGamePanel, className, children,
}: GameStageProps) {
    const {
        selectedCard, setSelectedCard, isFieldExpanded, setIsFieldExpanded, railTab, setRailTab, isPhoneFieldShown, setIsPhoneFieldShown,
        simPlayStarted, setSimPlayStarted, isRecapDismissed, setIsRecapDismissed,
    } = stage;
    const [boardRef, isWideBoard] = useIsWiderThan<HTMLDivElement>(WIDE_BOARD_MIN_WIDTH);
    /* A sim or live game doesn't send its defensive alignment, so it's filled in from the box score,
       which is what puts the defense totals and the full field of fielders on the board. */
    const game = useMemo(() => withLineupDefense(gameView), [gameView]);

    // From `md` up the plays/box score rail sits beside the board and can be dragged wider by its
    // left edge. Until then it keeps its CSS width. Below `md` it's a page of its own (see `PhoneTab`).
    const panesRef = useRef<HTMLDivElement>(null);
    const isSideRail = useMediaQuery(SIDE_RAIL_QUERY);
    const railResize = useResizablePanel({ storageKey: 'gameRailWidthPct:v1', containerRef: panesRef, defaultSize: null, minSize: RAIL_MIN_WIDTH, maxSize: railMaxWidth });
    const showsBoard = isSideRail || isPhoneFieldShown;
    const showsRail = isSideRail || !isPhoneFieldShown;

    /* `ScoreHeader` and `GameScoreTrack` read `detailedState` off the `GameView` it's given, so the host's label rides
       along on a shallow-copied view rather than as a prop. It's a no-op on every non-terminal
       playback frame — those report `state: "LIVE"`, and `ScoreHeader` only reads `detailedState`
       once state is FINAL. */
    const headerView = { ...game, detailedState };

    /* The in-progress plate appearance, pinned atop the log. Only while the game is genuinely live
       at the cursor's position — a finished game has no "current" matchup, and scrubbing back to an
       earlier point (`isReplaying`) would otherwise pin that frame's on-deck batter as if it were
       happening now. */
    const currentMatchup = !isReplaying && game.state === "LIVE" && game.situation?.batter
        ? game.situation
        : undefined;

    /* The recap waits for the final frame to finish animating, so the last out still plays out on
       the field before it fades back behind the summary. */
    const isRecapAvailable = game.state === "FINAL" && !isReplaying && playbackState.phase === "idle";
    const showRecap = isRecapAvailable && !isRecapDismissed;

    /* Recap ⇄ Field toggle, docked in the center of the scoreboard under "Final". */
    const recapToggle = isRecapAvailable ? (
        <button
            type="button"
            onClick={() => setIsRecapDismissed((dismissed) => !dismissed)}
            className={`flex items-center gap-1.5 rounded-control px-2.5 py-1 text-[11px] font-semibold ${buttonVariantClass('secondary')}`}
        >
            {showRecap ? <FaRing size={10} /> : <FaStar size={10} />}
            {showRecap ? 'Show field' : 'Recap'}
        </button>
    ) : undefined;

    /* Who won the pitch roll, flagged on the matching cards from the moment the result reveals until
       the play commits — before that the dice are still in the air, and after it the cursor has
       moved on to the next plate appearance. */
    const isResultRevealed = playbackState.phase === "result" || playbackState.phase === "runners" || playbackState.phase === "settle";
    const advantage = isResultRevealed ? advantageSideOf(playbackState.pendingPlay) : playbackState.phase === "idle" ? heldAdvantage : undefined;
    const swingResult = isResultRevealed ? playbackState.pendingPlay?.roll?.swingResult : undefined;
    /* Once a plate appearance's advantage is known the matchup keeps it until the next one, so
       through a live game's separate swing toss (when `advantage` is briefly unknown again) the
       winner keeps its glow, the other card stays faded, and card images hold on the chart instead
       of zooming back out to the command. */
    const situation = game.situation;
    const matchupKey = situation ? `${situation.inning}|${situation.isTop}|${situation.batter?.id}|${situation.pitcher?.id}` : null;
    const [settled, setSettled] = useState<{ key: string | null; side: AdvantageSide } | null>(null);
    if (advantage != null && (settled?.key !== matchupKey || settled.side !== advantage)) setSettled({ key: matchupKey, side: advantage });
    const matchupAdvantage = advantage ?? (matchupKey != null && settled?.key === matchupKey ? settled.side : undefined);
    const isAdvantageSettled = matchupAdvantage != null;

    const railTabs = infoPanel ? RAIL_TABS : RAIL_TABS.filter((tab) => tab.id !== 'info');
    /* The Info tab can leave while it's open: a host hides it mid-replay to avoid spoilers. */
    const activeRailTab = railTabs.some((tab) => tab.id === railTab) ? railTab : 'playbyplay';
    const phoneTabs: TabItem<PhoneTab>[] = [FIELD_TAB, ...railTabs];
    const selectPhoneTab = (tab: PhoneTab) => {
        setIsPhoneFieldShown(tab === 'field');
        if (tab !== 'field') setRailTab(tab);
    };

    /* Field and recap share a spot, with the field faded behind. Behind the recap the field is just
       the diamond: no runners, batter or defense left standing on it. */
    const field = (
        <div className={`self-center transition-[opacity,filter] duration-500 ${showRecap ? 'opacity-40 blur-[1px] pointer-events-none' : ''}`} aria-hidden={showRecap}>
            <GameField
                game={showRecap ? { ...game, situation: undefined } : game}
                cardMap={cardMap}
                onCardSelect={setSelectedCard}
                expanded={isFieldExpanded}
                onToggleExpanded={() => setIsFieldExpanded((expanded) => !expanded)}
                isLoadingCards={isLoadingCards}
                corner={showRecap ? undefined : (boardTools || boardAction) && (
                    <>
                        {boardTools}
                        {boardAction}
                    </>
                )}
                cornerLeft={showRecap ? undefined : strategy?.hand}
                drawer={showRecap ? undefined : strategy?.tray}
                // Expanded zooms back out, so all nine fielders fit.
                zoom={isWideBoard || isFieldExpanded ? 1 : NARROW_FIELD_ZOOM}
                transition={playbackState.transition}
                pendingPlay={playbackState.pendingPlay}
                phase={playbackState.phase}
                advantage={advantage}
                playbackSpeed={playbackState.effectiveSpeed}
                rollPrompt={showRecap ? undefined : rollPrompt}
                isHandThrown={isHandThrown}
                onPlayClick={isSim && playbackState.cursor === 0 && !simPlayStarted ? () => {
                    setSimPlayStarted(true);
                    playbackControls.seekToStart();
                    playbackControls.play();
                } : undefined}
            />
        </div>
    );

    /* The tab under the middle of the scoreboard: the last play, out for a few seconds after it
       lands. Whose turn it is hangs under that club instead (`boardTurn`). */
    const lastPlay = showRecap ? undefined : plays[0];
    const islandContent = lastPlay ? <LastPlayLine play={lastPlay} /> : null;
    const islandKey = lastPlay?.id ?? '';

    const recap = showRecap ? (
        <GameFinalSummary
            game={game}
            cardMap={cardMap}
            onCardSelect={setSelectedCard}
            isLoadingCards={isLoadingCards}
            className="relative self-start"
        />
    ) : undefined;

    const matchup = resolveMatchup(game, cardMap, isReplaying);
    /* Who's up for each club, for the box score tables to mark (see `LineupUpContext`). */
    const lineup = useMemo(() => lineupUp(game, plays), [game, plays]);
    const cornerCard = (side: "pitcher" | "hitter") => matchup && (
        <MatchupSide
            side={matchup[side]}
            isLoadingCards={isLoadingCards}
            onCardSelect={setSelectedCard}
            hideTrend={isReplaying}
            hasAdvantage={matchupAdvantage === side}
            isAdvantageSettled={isAdvantageSettled}
            chartHighlight={matchupAdvantage === side ? swingResult : undefined}
            accessory={strategy?.played?.[side]}
        />
    );

    return (
        <LineupUpContext.Provider value={lineup}>
        <div className={`flex flex-col tall:h-[calc(100dvh-var(--app-nav-offset,2.5rem))] overflow-hidden ${className ?? ''}`}>
            {/* Above the board (z-10), below the app's panels (the Manager drawer, z-30; slide-overs,
                z-40+), so a panel opened from the board isn't cut off by this bar */}
            <div
                className={`relative z-20 px-4 py-1 border-b border-(--divider) shrink-0 flex items-center gap-3 ${modeBarColor ? '' : 'bg-(--background-primary)'}`}
                style={modeBarColor ? { backgroundColor: modeBarColor } : undefined}
            >
                <BackButton onBack={onBack} className="py-1" />
                <div className="flex items-center gap-2">
                    <Heading level="section" as="h1" className="hidden sm:inline" style={modeBarColor ? { color: bannerTokens(modeBarColor).fill } : undefined}>{title}</Heading>
                    {titleAccessory}
                </div>
                {topBarStatus}
                <div className="ml-auto flex min-w-0 items-center gap-2">
                    {topBarActions}
                </div>
            </div>

            {/* A phone's tabs sit right under the top bar, where they're easy to find, and each one
                takes the whole page: the field, or the plays, box score or info instead of it. */}
            {!isSideRail && (
                <div className="shrink-0 border-b border-(--divider) bg-(--background-primary)">
                    <TabButtons tabs={phoneTabs} value={isPhoneFieldShown ? 'field' : activeRailTab} onChange={selectPhoneTab} className="px-2" fullWidth />
                </div>
            )}

            {/* From `md` up the board and the rail sit side by side, so the situation never leaves
                the screen. Whether the board itself is wide is measured rather than breakpointed,
                since the sidebar takes a varying share of the width. */}
            <div ref={panesRef} className="flex min-h-0 flex-1 flex-col short:flex-none short:h-[calc(100dvh-var(--app-nav-offset,2.5rem))] md:flex-row">
                <div ref={boardRef} className={`relative min-h-0 flex-1 overflow-y-auto scrollbar-hide md:min-w-0 ${showsBoard ? '' : 'hidden'}`}>
                    <GameBoard
                        isWide={isWideBoard}
                        track={
                            <ScoreboardIsland content={islandContent} contentKey={islandKey} status={showRecap ? null : boardTurn} announcements={showRecap ? undefined : teamAnnouncements} isNarrow={!isWideBoard}>
                                {isWideBoard
                                    ? <GameScoreTrack game={headerView} centerAction={recapToggle} />
                                    : <ScoreHeader game={headerView} compact centerAction={recapToggle} />}
                            </ScoreboardIsland>
                        }
                        field={field}
                        overlay={recap}
                        footer={playbackBar && <div className={isWideBoard ? '' : 'mx-2'}>{playbackBar}</div>}
                        isFieldExpanded={isFieldExpanded}
                        bottomLeft={cornerCard("pitcher")}
                        bottomRight={cornerCard("hitter")}
                        bottomSpan={matchup ? undefined : preGamePanel}
                        below={
                            <>
                                {preGamePanel && <div className="mx-2">{preGamePanel}</div>}
                                {!showRecap && (
                                    <GameMatchup
                                        game={game}
                                        cardMap={cardMap}
                                        isLoadingCards={isLoadingCards}
                                        onCardSelect={setSelectedCard}
                                        hideStatlines={isReplaying}
                                        advantage={matchupAdvantage}
                                        isAdvantageSettled={isAdvantageSettled}
                                        swingResult={swingResult}
                                        accessories={strategy?.played}
                                    />
                                )}
                            </>
                        }
                    />
                </div>

                <div
                    className={`relative min-h-0 min-w-0 flex-1 flex-col bg-(--background-primary) md:w-80 md:flex-none md:border-l md:border-(--divider) xl:w-90 ${showsRail ? 'flex' : 'hidden'}`}
                    style={isSideRail && railResize.size !== null ? { width: railResize.size } : undefined}
                >
                    {isSideRail && (
                        <>
                            <ResizeHandle {...railResize.handleProps} label="Resize plays and box score" />
                            <div className="shrink-0">
                                <TabButtons tabs={railTabs} value={activeRailTab} onChange={setRailTab} className="px-2" fullWidth />
                            </div>
                        </>
                    )}

                    {/* All three stay mounted so each keeps its scroll position across tabs. */}
                    <div className={`${RAIL_PANEL_CLASS} ${activeRailTab === 'playbyplay' ? '' : 'hidden'}`}>
                        <PlayByPlayLog
                            key={gameKey}
                            plays={plays}
                            cardMap={cardMap}
                            onCardSelect={setSelectedCard}
                            isLoadingCards={isLoadingCards}
                            currentMatchup={currentMatchup}
                            maxHeightClassName="max-h-none"
                        />
                    </div>
                    <div className={`${RAIL_PANEL_CLASS} space-y-4 ${activeRailTab === 'boxscore' ? '' : 'hidden'}`}>
                        {/* A wide board already carries the linescore on its track. */}
                        {!isWideBoard && <GameLinescore game={game} />}
                        {boxScorePanels}
                    </div>
                    {infoPanel && (
                        <div className={`${RAIL_PANEL_CLASS} ${activeRailTab === 'info' ? '' : 'hidden'}`}>
                            {infoPanel}
                        </div>
                    )}
                </div>
            </div>

            <div className={selectedCard ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={() => setSelectedCard(null)} isVisible={!!selectedCard}>
                    <CardDetail
                        showdownBotCardData={selectedCard}
                        hideTrendGraphs={true}
                        context="game_detail"
                        parent='game_detail'
                    />
                </Modal>
            </div>

            {children}
        </div>
        </LineupUpContext.Provider>
    );
}

/** The sim transport in the top bar. The sim already opens parked on the first pitch, so the first
 *  button is a one-click "start playing": from frame 0 it reads "Watch"; once the cursor has moved
 *  it becomes "Restart" and jumps back to the top. */
export function SimTopBarControls({ cursor, controls, isMidReplay, onExit, buttonClass }: {
    cursor: number;
    controls: GamePlaybackControls;
    /** Offers the jump to the end, which resolves the final score and box score at once. */
    isMidReplay: boolean;
    onExit: () => void;
    buttonClass: string;
}) {
    return (
        <div className="flex min-w-0 items-center gap-2">
            <TopBarButton
                label={cursor === 0 ? 'Watch' : 'Restart'}
                shortLabel={cursor === 0 ? 'Play' : 'Restart'}
                onClick={() => {
                    controls.seekToStart();
                    controls.play();
                }}
                className={buttonClass}
            />
            {isMidReplay && (
                <TopBarButton label="Skip to result" shortLabel="Skip to end" onClick={() => controls.seekToLive()} className={buttonClass} />
            )}
            <TopBarButton label="Exit Sim" shortLabel="Exit" onClick={onExit} className={buttonClass} />
        </div>
    );
}
