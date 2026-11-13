/**
 * @fileoverview Owns the playback cursor over one `GameTimeline`. `useGamePlayback` can only be
 * called unconditionally within a component, and a host usually needs its data loaded before it can
 * build a timeline — so this exists as the component boundary that makes that legal: it doesn't
 * mount until the host's loading/error guards have already passed, at which point calling the hook
 * unconditionally in here is fine.
 *
 * Knows nothing about where the timeline came from, so a real MLB game, a sim of one, and a sim
 * between two builder teams all play back through it. A render-prop rather than its own JSX, since
 * the layout belongs to the host: this only supplies the `GameView`/`PlayEntry[]` values it reads.
 */
import { useMemo, type ReactNode } from "react";

import type { GameView } from "../../domain/game";
import type { PlayEntry } from "../../domain/play";
import type { GameTimeline } from "../../domain/timeline";
import {
    useGamePlayback,
    type GamePlaybackControls,
    type GamePlaybackState,
    type PlaybackMode,
} from "../../hooks/useGamePlayback";
import GamePlaybackBar from "./GamePlaybackBar";

export type PlaybackRenderProps = {
    /** The reconstructed view for whatever frame the cursor is on — feed this to ScoreHeader,
     *  GameField, GameMatchup, and GameLinescore. Everything else (box score tables, defense,
     *  decisions) stays reading the raw `boxscore`/current `GameView` unchanged; those are frozen
     *  at "now" during playback rather than reconstructed per frame (see `GameTimeline.frozen`). */
    activeView: GameView;
    /** Plays revealed so far — newest-first, matching `PlayByPlayLog`'s existing convention.
     *  Scrubbing backward hides plays after the cursor; `trailingPlays` are always included in full. */
    activePlays: PlayEntry[];
    playbackState: GamePlaybackState;
    playbackControls: GamePlaybackControls;
    /** The transport strip, pre-built with this game's frame count/frozen flags wired in — mount
     *  it directly rather than re-deriving those props. */
    playbackBar: ReactNode;
    /** False when the timeline carries a per-frame box score (a sim with player ids on its log),
     *  so the box score panels can follow `activeView` instead of hiding until the end. */
    isBoxscoreFrozen: boolean;
    /** True once the cursor has been moved off the live/final edge — the signal for whether to
     *  show REPLAY chrome (a finished real game) or dim the "Watch" affordance (a sim). */
    isReplaying: boolean;
};

type TimelinePlaybackProps = {
    timeline: GameTimeline;
    initialMode: PlaybackMode;
    /** "start" parks on the first pitch with the result hidden, for a sim the user plays through.
     *  "live" opens on the current/final state. */
    initialCursor: "live" | "start";
    /** Already-known history before the timeline's first frame (a takeover's real plays), which
     *  playback shouldn't hold back the way it holds back the plays still to come. */
    trailingPlays?: PlayEntry[];
    /** Live only — see `useGameDetailData`'s buffer. Swaps the applied boxscore for the buffered
     *  one; does NOT move the playback cursor — this component composes that with its own
     *  `playbackControls.seekToLive()` below, since the cursor is internal to this component and
     *  the caller (which owns the buffer) has no other way to reach it. */
    bufferedCount?: number;
    onApplyBuffer?: () => void;
    /** Whether the bar should caveat a frozen box score. A host that rebuilds its box score per
     *  frame or hides it mid-replay turns this off, since the caveat never applies there. */
    showFrozenBoxscoreCaveat: boolean;
    children: (props: PlaybackRenderProps) => ReactNode;
};

export default function TimelinePlayback({
    timeline, initialMode, initialCursor, trailingPlays, bufferedCount, onApplyBuffer, showFrozenBoxscoreCaveat, children,
}: TimelinePlaybackProps) {
    const [playbackState, playbackControls] = useGamePlayback({ timeline, initialMode, initialCursor });

    const revealedPlays = useMemo(() => {
        const upTo = timeline.frames.slice(0, playbackState.cursor + 1);
        return upTo.map((f) => f.play).filter((p): p is PlayEntry => !!p).reverse();
    }, [timeline, playbackState.cursor]);
    const activePlays = [...revealedPlays, ...(trailingPlays ?? [])];

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
            isBoxscoreFrozen={timeline.frozen.boxscore && showFrozenBoxscoreCaveat}
        />
    );

    return children({
        activeView: playbackState.frame.view,
        activePlays,
        playbackState,
        playbackControls,
        playbackBar,
        isBoxscoreFrozen: timeline.frozen.boxscore,
        isReplaying: playbackState.cursor < timeline.liveIndex,
    });
}
