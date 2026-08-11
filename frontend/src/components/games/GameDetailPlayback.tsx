/**
 * @fileoverview Owns the playback cursor for one game's detail view. `useGamePlayback` can only
 * be called unconditionally within a component, and `GameDetail` needs its data (boxscore) loaded
 * before a `GameTimeline` can be built — so this exists purely as the component boundary that
 * makes that legal: it doesn't mount until `GameDetail`'s loading/error guards have already
 * passed, at which point calling the hook unconditionally in here is fine.
 *
 * A render-prop rather than just rendering its own JSX — `GameDetail`'s layout (desktop 3-column
 * grid, mobile bottom sheet, the no-field fallback) already exists and stays exactly where it is;
 * this only swaps out the `GameView`/`PlayEntry[]` values those layouts read, so none of that
 * layout code has to move.
 */
import { useMemo, type ReactNode } from "react";

import type { GameBoxscoreDetail } from "../../api/mlbAPI";
import type { SimGameResult } from "../../api/simGame";
import type { GameState, GameView } from "../../domain/game";
import type { PlayEntry } from "../../domain/play";
import { fromGamePlays, fromMlbTimeline } from "../../domain/adapters/fromMlbApi";
import { fromSimTimeline } from "../../domain/adapters/fromSim";
import {
    useGamePlayback,
    type GamePlaybackControls,
    type GamePlaybackState,
    type PlaybackMode,
} from "../../hooks/useGamePlayback";
import GamePlaybackBar from "./GamePlaybackBar";

type PlaybackRenderProps = {
    /** The reconstructed view for whatever frame the cursor is on — feed this to ScoreHeader,
     *  GameField, GameMatchup, and GameLinescore. Everything else (box score tables, defense,
     *  decisions) stays reading the raw `boxscore`/current `GameView` unchanged; those are frozen
     *  at "now" during playback rather than reconstructed per frame (see `GameTimeline.frozen`). */
    activeView: GameView;
    /** Plays revealed so far — newest-first, matching `PlayByPlayLog`'s existing convention.
     *  Scrubbing backward hides plays after the cursor; a takeover's pre-simulation real plays are
     *  always included in full (historical background, not something playback holds back). */
    activePlays: PlayEntry[];
    playbackState: GamePlaybackState;
    playbackControls: GamePlaybackControls;
    /** The transport strip, pre-built with this game's frame count/frozen flags wired in — mount
     *  it directly rather than re-deriving those props. */
    playbackBar: ReactNode;
    /** True once the cursor has been moved off the live/final edge — the signal for whether to
     *  show REPLAY chrome (a finished real game) or dim the "Watch" affordance (a sim). */
    isReplaying: boolean;
};

type GameDetailPlaybackProps = {
    boxscore: GameBoxscoreDetail;
    sportId?: number;
    /** The REAL game's state (never the sim's) — decides whether this timeline should start in
     *  "live" mode (auto-follow) or "playback" mode (static until the user presses play). */
    realState: GameState;
    simResult: SimGameResult | null;
    /** Live only — see `useGameDetailData`'s buffer. Swaps the applied boxscore for the buffered
     *  one; does NOT move the playback cursor — this component composes that with its own
     *  `playbackControls.seekToLive()` below, since the cursor is internal to this component and
     *  the caller (which owns the buffer) has no other way to reach it. */
    bufferedCount?: number;
    onApplyBuffer?: () => void;
    children: (props: PlaybackRenderProps) => ReactNode;
};

export default function GameDetailPlayback({
    boxscore, sportId, realState, simResult, bufferedCount, onApplyBuffer, children,
}: GameDetailPlaybackProps) {
    const timeline = useMemo(
        () => (simResult ? fromSimTimeline(simResult) : fromMlbTimeline(boxscore, sportId)),
        [boxscore, sportId, simResult],
    );
    // A sim's result is always a completed game (`fromSimGame` hardcodes FINAL) — only a real,
    // currently-live game auto-follows.
    const initialMode: PlaybackMode = !simResult && realState === "LIVE" ? "live" : "playback";
    const [playbackState, playbackControls] = useGamePlayback({ timeline, initialMode });

    const revealedPlays = useMemo(() => {
        const upTo = timeline.frames.slice(0, playbackState.cursor + 1);
        return upTo.map((f) => f.play).filter((p): p is PlayEntry => !!p).reverse();
    }, [timeline, playbackState.cursor]);
    // The portion of a takeover before the sim resumed — already-known history, not something
    // playback should hold back the way it holds back the simulated plays still to come.
    const trailingRealPlays = useMemo(
        () => (simResult ? fromGamePlays(simResult.real_plays) : []),
        [simResult],
    );
    const activePlays = [...revealedPlays, ...trailingRealPlays];

    // Applying the buffer only swaps WHICH data the timeline is built from; the cursor still has
    // to be told to jump to the new live edge, or it would just sit wherever it was (correct for
    // "Resume", which walks forward via `isPlaying`, but wrong for an explicit "skip" — that one
    // should be instant, no animation).
    const handleSkipToLive = onApplyBuffer
        ? () => { onApplyBuffer(); playbackControls.seekToLive(); }
        : undefined;

    const playbackBar = (
        <GamePlaybackBar
            state={playbackState}
            controls={playbackControls}
            frameCount={timeline.frames.length}
            bufferedCount={bufferedCount}
            onSkipToLive={handleSkipToLive}
            isBoxscoreFrozen={timeline.frozen.boxscore}
        />
    );

    return children({
        activeView: playbackState.frame.view,
        activePlays,
        playbackState,
        playbackControls,
        playbackBar,
        isReplaying: playbackState.cursor < timeline.liveIndex,
    });
}
