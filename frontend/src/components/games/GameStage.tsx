/**
 * @fileoverview The game screen's layout: top bar, scoreboard, field, recap, matchup, box score and
 * play-by-play, across the mobile / two-column / three-column breakpoints. Purely presentational over
 * the current playback frame, so any host with a `GameTimeline` can use it. What differs between
 * hosts arrives as slots: the box score panel, the top bar's controls and anything under the bar.
 */
import type { CSSProperties, Key, ReactNode } from "react";
import { FaList, FaRing, FaTable } from "react-icons/fa";
import { FaStar } from "react-icons/fa6";

import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { bannerTokens } from "../../functions/colors";
import type { GameView } from "../../domain/game";
import { advantageSideOf, type PlayEntry } from "../../domain/play";
import type { GamePlaybackControls, GamePlaybackState } from "../../hooks/useGamePlayback";
import { CardDetail } from "../cards/CardDetail";
import BackButton from "../shared/BackButton";
import { Heading } from "../shared/Heading";
import { Modal } from "../shared/Modal";
import { Tabs as TabButtons, type TabItem } from "../shared/Tabs";
import { buttonVariantClass } from "../shared/buttonStyles";
import GameField from "./GameField";
import GameMatchup from "./GameMatchup";
import PlayByPlayLog from "./PlayByPlayLog";
import GameFinalSummary from "./detail/GameFinalSummary";
import ScoreHeader from "./detail/ScoreHeader";
import TopBarButton from "./detail/TopBarButton";
import type { GameStageState, MidTab, MobileTab } from "./useGameStage";

const MOBILE_TABS: TabItem<MobileTab>[] = [
    { id: 'field', label: 'Field View', icon: <FaRing />},
    { id: 'boxscore', label: 'Boxscore', icon: <FaTable /> },
    { id: 'playbyplay', label: 'Play By Play', icon: <FaList /> },
];

const MID_TABS = MOBILE_TABS.filter((tab): tab is TabItem<MidTab> => tab.id !== 'field');

const GRASS_MASK = 'linear-gradient(to bottom, transparent 0%, black 20%, black 80%, transparent 100%)';
const GRASS_MASK_STYLE: CSSProperties = { maskImage: GRASS_MASK, WebkitMaskImage: GRASS_MASK };

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
    /** A sim opens parked on the first pitch, so the field offers its big Play button. */
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
    /** Under the transport strip, above the current matchup. */
    belowPlaybackBar?: ReactNode;
    className?: string;
    /** Host-owned modals. */
    children?: ReactNode;
};

export default function GameStage({
    stage, game, plays, playbackState, playbackControls, isReplaying, playbackBar, detailedState,
    cardMap, isLoadingCards, isSim, gameKey, title, titleAccessory, modeBarColor, onBack,
    topBarStatus, topBarActions, boxScorePanels, belowPlaybackBar, className, children,
}: GameStageProps) {
    const {
        selectedCard, setSelectedCard, isFieldExpanded, setIsFieldExpanded, mobileTab, setMobileTab,
        midTab, setMidTab, simPlayStarted, setSimPlayStarted, isRecapDismissed, setIsRecapDismissed,
    } = stage;

    /* `ScoreHeader` reads `detailedState` off the `GameView` it's given, so the host's label rides
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
    const advantage = isResultRevealed ? advantageSideOf(playbackState.pendingPlay) : undefined;
    const swingResult = isResultRevealed ? playbackState.pendingPlay?.roll?.swingResult : undefined;

    return (
        <div className={`flex flex-col md:tall:h-[calc(100dvh-2.5rem)] overflow-hidden ${className ?? ''}`}>
            <div
                className={`relative z-50 px-4 py-2 border-b border-(--divider) shrink-0 flex items-center gap-3 ${modeBarColor ? '' : 'bg-(--background-primary)'}`}
                style={modeBarColor ? { backgroundColor: modeBarColor } : undefined}
            >
                <BackButton onBack={onBack} />
                <div className="flex items-center gap-2">
                    <Heading level="section" as="h1" className="hidden sm:inline" style={modeBarColor ? { color: bannerTokens(modeBarColor).fill } : undefined}>{title}</Heading>
                    {titleAccessory}
                </div>
                {topBarStatus}
                <div className="ml-auto flex min-w-0 items-center gap-2">
                    {topBarActions}
                </div>
            </div>

            {/* Below `md`: one strip swaps between all three columns. `md`–`lg`: a 50/50 split — the
                field pinned left, `MID_TABS` (box score / play-by-play) swapping on the right.
                `lg`+: the strip is gone and all three columns show at once. */}
            <div className="md:hidden shrink-0">
                <TabButtons tabs={MOBILE_TABS} value={mobileTab} onChange={setMobileTab} className="px-2" fullWidth />
            </div>

            <div className="flex-1 min-h-0 md:grid md:grid-cols-2 md:gap-4 md:px-4 md:overflow-hidden md:short:flex-none md:short:h-[calc(100dvh-2.5rem)] lg:grid-cols-[3fr_4fr_3fr]">

                {/* Spotlight column — field, playback bar and matchup. Pinned left from `md` up;
                    `lg:order-2` slides it back to the centre once the box score gets its own column
                    again. */}
                <div className={`${mobileTab === 'field' ? 'block' : 'hidden'} h-full overflow-y-auto space-y-4 p-0 pb-[calc(6rem+var(--safe-bottom))] scrollbar-hide md:block md:order-1 md:py-4 md:px-0 md:min-w-0 lg:order-2`}>
                    {/* Grass backdrop behind the scoreboard, field and matchup as one group — faded
                        top/bottom so it blends into the page instead of a hard edge. The image is
                        the first child with no z-index of its own, and the content wrapper below it
                        is `relative` (so it's a positioned sibling too) — later DOM order among
                        same-stacking-level positioned elements paints on top, with no negative
                        z-index needed (which can end up behind an ancestor's own background instead
                        of just this image). */}
                    <div className="relative">
                        <img
                            src="/images/games/Grass Backdrop.png"
                            alt=""
                            className="absolute inset-0 h-full w-full object-cover pointer-events-none select-none"
                            style={GRASS_MASK_STYLE}
                        />

                        {/* `isolate` keeps the field's own mowed-grass backdrop (painted at `-z-10`
                            inside GameField, so it sits under the scoreboard and matchup too) above
                            the Grass.png fill behind this group. */}
                        <div className="relative isolate space-y-4 p-1">
                            {/* Scoreboard bleeds over the grass on both breakpoints — compact (no
                                records, smaller type) on mobile, full-size on desktop. */}
                            <ScoreHeader game={headerView} compact centerAction={recapToggle} className="lg:hidden" />
                            <div className="hidden lg:block"><ScoreHeader game={headerView} centerAction={recapToggle} /></div>

                            {/* Field and recap share one grid cell, so the cell sizes to the taller
                                of the two and the field sits faded behind the recap rather than
                                pushing it down the column. */}
                            <div className="grid *:col-start-1 *:row-start-1">
                                <div className={`self-center transition-[opacity,filter] duration-500 ${showRecap ? 'opacity-40 blur-[1px] pointer-events-none' : ''}`} aria-hidden={showRecap}>
                                    {/* Behind the recap the field is just the diamond — no runners,
                                        batter or defense left standing on it. */}
                                    <GameField
                                        game={showRecap ? { ...game, situation: undefined } : game}
                                        cardMap={cardMap}
                                        onCardSelect={setSelectedCard}
                                        expanded={isFieldExpanded}
                                        onToggleExpanded={() => setIsFieldExpanded((expanded) => !expanded)}
                                        isLoadingCards={isLoadingCards}
                                        showGrassBackdrop
                                        transition={playbackState.transition}
                                        pendingPlay={playbackState.pendingPlay}
                                        phase={playbackState.phase}
                                        lastPlay={showRecap ? undefined : plays[0]}
                                        advantage={advantage}
                                        playbackSpeed={playbackState.effectiveSpeed}
                                        onPlayClick={isSim && playbackState.cursor === 0 && !simPlayStarted ? () => {
                                            setSimPlayStarted(true);
                                            playbackControls.seekToStart();
                                            playbackControls.play();
                                        } : undefined}
                                    />
                                </div>
                                {showRecap && (
                                    <GameFinalSummary
                                        game={game}
                                        cardMap={cardMap}
                                        onCardSelect={setSelectedCard}
                                        isLoadingCards={isLoadingCards}
                                        className="relative self-start"
                                    />
                                )}
                            </div>

                            {playbackBar}
                            {belowPlaybackBar}

                            {/* The last matchup of a finished game is stale once the recap is up —
                                it already names who mattered. */}
                            {!showRecap && (
                                <GameMatchup
                                    game={game}
                                    cardMap={cardMap}
                                    isLoadingCards={isLoadingCards}
                                    onCardSelect={setSelectedCard}
                                    hideStatlines={isReplaying}
                                    advantage={advantage}
                                    swingResult={swingResult}
                                />
                            )}
                        </div>
                    </div>
                </div>

                {/* Right column — box score + play-by-play. `contents` below `md` (each panel just
                    obeys the mobile strip); a real flex column with its own `MID_TABS` strip between
                    `md` and `lg`; `contents` again at `lg` so both panels rejoin the outer grid as
                    their own columns. */}
                <div className="contents md:flex md:flex-col md:order-2 md:min-h-0 md:min-w-0 md:overflow-hidden lg:contents">
                    <div className="hidden md:block lg:hidden shrink-0 pt-4">
                        <TabButtons tabs={MID_TABS} value={midTab} onChange={setMidTab} fullWidth />
                    </div>

                    <div className={`${mobileTab === 'boxscore' ? 'block' : 'hidden'} ${midTab === 'boxscore' ? 'md:block' : 'md:hidden'} h-full min-w-0 overflow-y-auto p-4 pb-[calc(6rem+var(--safe-bottom))] scrollbar-hide md:h-auto md:flex-1 md:min-h-0 md:py-4 md:px-0 md:pb-4 lg:block lg:h-full lg:order-1`}>
                        {boxScorePanels}
                    </div>

                    <div className={`${mobileTab === 'playbyplay' ? 'block' : 'hidden'} ${midTab === 'playbyplay' ? 'md:block' : 'md:hidden'} h-full min-w-0 overflow-y-auto p-4 pb-[calc(6rem+var(--safe-bottom))] scrollbar-hide md:h-auto md:flex-1 md:min-h-0 md:py-4 md:px-0 md:pb-0 lg:block lg:h-full lg:order-3`}>
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
