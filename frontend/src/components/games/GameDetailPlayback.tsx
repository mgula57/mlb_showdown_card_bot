/**
 * @fileoverview Builds the timeline for the game page, where one screen plays back either a real
 * MLB game or a stored sim of it, then hands off to `TimelinePlayback`.
 */
import { useMemo, type ReactNode } from "react";

import type { GameBoxscoreDetail } from "../../api/mlbAPI";
import type { SimGameResult } from "../../api/simGame";
import type { GameState } from "../../domain/game";
import { fromGamePlays, fromMlbTimeline } from "../../domain/adapters/fromMlbApi";
import { fromSimTimeline } from "../../domain/adapters/fromSim";
import TimelinePlayback, { type PlaybackRenderProps } from "./TimelinePlayback";

type GameDetailPlaybackProps = {
    boxscore: GameBoxscoreDetail;
    sportId?: number;
    /** The REAL game's state (never the sim's) — decides whether this timeline should start in
     *  "live" mode (auto-follow) or "playback" mode (static until the user presses play). */
    realState: GameState;
    simResult: SimGameResult | null;
    bufferedCount?: number;
    onApplyBuffer?: () => void;
    children: (props: PlaybackRenderProps) => ReactNode;
};

export default function GameDetailPlayback({
    boxscore, sportId, realState, simResult, bufferedCount, onApplyBuffer, children,
}: GameDetailPlaybackProps) {
    const timeline = useMemo(
        () => (simResult
            ? fromSimTimeline(simResult.game, simResult.game_pk, simResult.setup.start_state)
            : fromMlbTimeline(boxscore, sportId)),
        [boxscore, sportId, simResult],
    );
    // The portion of a takeover before the sim resumed.
    const trailingPlays = useMemo(
        () => (simResult ? fromGamePlays(simResult.real_plays) : []),
        [simResult],
    );

    return (
        <TimelinePlayback
            timeline={timeline}
            // A sim's result is always a completed game (`fromSimGame` hardcodes FINAL) — only a
            // real, currently-live game auto-follows.
            initialMode={!simResult && realState === "LIVE" ? "live" : "playback"}
            // A sim opens parked on the first pitch with its result hidden — the user plays through
            // to it. A real game (live or final) still opens on its current/final state.
            initialCursor={simResult ? "start" : "live"}
            trailingPlays={trailingPlays}
            bufferedCount={bufferedCount}
            onApplyBuffer={onApplyBuffer}
            // A sim either rebuilds its box score per frame or hides it mid-replay (see GameDetail).
            showFrozenBoxscoreCaveat={!simResult}
        >
            {children}
        </TimelinePlayback>
    );
}
