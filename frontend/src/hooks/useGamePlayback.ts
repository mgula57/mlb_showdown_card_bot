/**
 * @fileoverview The playback transport: a cursor over a `GameTimeline`'s frames, plus the
 * per-play phase machine that gives each transition a beat to animate before the next one starts.
 *
 * Three modes are frame SOURCES over the same cursor, not three different mechanisms — this hook
 * never fetches, `timeline` is always a prop:
 *  - "live": the host rebuilds `timeline` on every poll; the cursor auto-follows the newest frame.
 *  - "playback": the timeline is fixed (a finished game or a stored sim); the cursor is user-owned.
 *  - "interactive": UNUSED TODAY. A future producer would append frames one at a time and pass
 *    `gate`, which SUSPENDS the phase machine in `"await-input"` before entering a frame — that's
 *    the seam a dice-roll/manager-button UI hooks into later. `gate` is never passed by any
 *    current caller, so that branch is dead code until it exists; it costs nothing to leave wired.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import type { FrameTransition, GameFrame, GameTimeline, TransitionSeverity } from "../domain/timeline";
import type { PlayEntry } from "../domain/play";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

export type PlaybackMode = "live" | "playback" | "interactive";
export type PlaybackSpeed = 0.5 | 1 | 2 | 4;
/** Non-null SUSPENDS the phase machine before the gated frame is entered. Only ever produced by
 *  a `gate` callback — nothing in this codebase passes one yet. */
export type AwaitingInput = "roll" | "manager" | null;

export type PlayPhase =
    | "idle"          // parked on a frame, nothing animating
    | "await-input"   // SUSPENDED — `submitInput` must be called before the next frame plays
    | "pitch"         // pre-result beat — matchup emphasis, a dice slot if interactive
    | "result"        // event badge reveals, log row enters
    | "runners"       // runner cards translate to their new spots
    | "settle";       // score ticks, outs update, linescore cell fills

export type GamePlaybackState = {
    frame: GameFrame;
    cursor: number;
    mode: PlaybackMode;
    phase: PlayPhase;
    awaitingInput: AwaitingInput;
    isPlaying: boolean;
    speed: PlaybackSpeed;
    /** `speed`, boosted automatically while catching up on a large backlog (live mode only) —
     *  what CSS's `--playback-speed` custom property should be set to. */
    effectiveSpeed: number;
    /** The transition being animated right now; undefined while idle. */
    transition?: FrameTransition;
    /** The play `transition` belongs to — its `event` (e.g. "Double", "Strikeout") is what a
     *  result flash reads. Set alongside `transition`, describing the frame being transitioned
     *  INTO — `frame` itself still points at the outgoing frame until `commit()` runs. */
    pendingPlay?: PlayEntry;
    isBehindLive: boolean;
    behindBy: number;
};

export type GamePlaybackControls = {
    play: () => void;
    pause: () => void;
    toggle: () => void;
    stepForward: () => void;
    stepBack: () => void;
    seek: (index: number) => void;
    seekToStart: () => void;
    seekToLive: () => void;
    setSpeed: (speed: PlaybackSpeed) => void;
    /** Interactive seam — resolves an `"await-input"` suspension. The caller is responsible for
     *  making `gate` return `null` for the pending frame (e.g. by stashing `payload` wherever
     *  `gate` reads from) before calling this; the hook itself doesn't interpret `payload`. */
    submitInput: (payload: unknown) => void;
};

const PHASE_MS: Record<"pitch" | "result" | "runners" | "settle", number> = {
    pitch: 450, result: 500, runners: 700, settle: 350,
};
const SEVERITY_SCALE: Record<TransitionSeverity, number> = { quiet: 0.7, notable: 1, big: 1.4 };
/** A live game's cursor gets a 2x boost once it's this many frames behind the live edge, so
 *  resuming from a long pause doesn't take minutes to catch up. */
const CATCH_UP_THRESHOLD = 6;
const CATCH_UP_MULTIPLIER = 2;

export function useGamePlayback(options: {
    timeline: GameTimeline;
    initialMode: PlaybackMode;
    gate?: (frame: GameFrame) => AwaitingInput;
    onFrameEnter?: (frame: GameFrame, transition?: FrameTransition) => void;
}): [GamePlaybackState, GamePlaybackControls] {
    const { timeline, initialMode, gate, onFrameEnter } = options;
    const frames = timeline.frames;
    if (frames.length === 0) throw new Error("useGamePlayback: timeline has no frames");

    const prefersReducedMotion = usePrefersReducedMotion();

    const [cursorId, setCursorId] = useState<string | undefined>(undefined);
    const [mode, setMode] = useState<PlaybackMode>(initialMode);
    const [phase, setPhase] = useState<PlayPhase>("idle");
    const [awaitingInput, setAwaitingInput] = useState<AwaitingInput>(null);
    const [isPlaying, setIsPlaying] = useState(initialMode === "live" || initialMode === "interactive");
    const [speed, setSpeedState] = useState<PlaybackSpeed>(1);
    const [transition, setTransition] = useState<FrameTransition | undefined>(undefined);
    const [pendingPlay, setPendingPlay] = useState<PlayEntry | undefined>(undefined);

    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const initializedRef = useRef(false);

    // Cursor tracked by frame ID, not index — every poll rebuilds `frames`, and an index would
    // silently point at the wrong play once the array underneath it changes shape.
    const cursorIndex = useMemo(() => {
        if (!cursorId) return frames.length - 1;
        const idx = frames.findIndex((f) => f.id === cursorId);
        return idx === -1 ? frames.length - 1 : idx;
    }, [frames, cursorId]);

    const behindBy = Math.max(0, frames.length - 1 - cursorIndex);
    const isBehindLive = mode === "live" && behindBy > 0;
    const catchUpBoost = mode === "live" && isPlaying && behindBy > CATCH_UP_THRESHOLD ? CATCH_UP_MULTIPLIER : 1;
    const effectiveSpeed = speed * catchUpBoost;

    // Initial placement is ALWAYS the live edge, regardless of mode — opening a live game or a
    // finished one both show its current/final state immediately, matching what the page looked
    // like before playback existed. "playback" mode only differs in starting `isPlaying: false`
    // (a finished game doesn't auto-replay itself) and in `commit()` auto-pausing once scrubbing
    // forward reaches the true end; reviewing earlier plays is always an explicit `seek`/`play`.
    useEffect(() => {
        if (initializedRef.current) return;
        initializedRef.current = true;
        setCursorId(frames[frames.length - 1].id);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current); }, []);

    function scheduleAdvance() {
        const nextIndex = cursorIndex + 1;
        const nextFrame = frames[nextIndex];
        if (!nextFrame) return;

        const gateResult = gate?.(nextFrame) ?? null;
        if (gateResult) {
            setAwaitingInput(gateResult);
            setPhase("await-input");
            return;
        }

        const severity = nextFrame.transition?.severity ?? "quiet";
        const scale = SEVERITY_SCALE[severity];
        const speedNow = effectiveSpeed;
        const reducedMotionMultiplier = prefersReducedMotion ? 0.001 : 1;
        const durationFor = (p: keyof typeof PHASE_MS) => (PHASE_MS[p] * scale * reducedMotionMultiplier) / speedNow;

        setTransition(nextFrame.transition);
        setPendingPlay(nextFrame.play);

        const runPhase = (p: keyof typeof PHASE_MS) => {
            setPhase(p);
            timerRef.current = setTimeout(() => {
                if (p === "pitch") runPhase("result");
                else if (p === "result") runPhase("runners");
                else if (p === "runners") runPhase("settle");
                else commit();
            }, durationFor(p));
        };

        const commit = () => {
            setCursorId(nextFrame.id);
            setPhase("idle");
            setTransition(undefined);
            setPendingPlay(undefined);
            onFrameEnter?.(nextFrame, nextFrame.transition);
            const reachedEnd = nextIndex >= frames.length - 1;
            if (reachedEnd && mode !== "live" && mode !== "interactive") setIsPlaying(false);
        };

        runPhase("pitch");
    }

    // The one advance trigger — fires on user actions (`play()`) and on the live timeline
    // growing. `phase !== "idle"` is what prevents this from double-firing mid-sequence: a phase
    // sequence sets `phase` away from "idle" synchronously at its start, so a concurrent render of
    // this effect (from either source) sees the guard and no-ops until the current step settles.
    useEffect(() => {
        if (!initializedRef.current) return;
        if (!isPlaying) return;
        if (phase !== "idle") return;
        if (cursorIndex >= frames.length - 1) return;
        scheduleAdvance();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isPlaying, phase, cursorIndex, frames.length]);

    const clearTimer = () => { if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null; } };

    // Interrupting a scheduled phase sequence must always land the machine back at "idle" on
    // whatever frame is still current (nothing has been `commit()`-ed yet) — clearing the timer
    // without also resetting `phase` would leave it stuck on a non-idle value forever, since
    // nothing else ever transitions it back and the advance effect's `phase !== "idle"` guard
    // would then block every future `play()`/`stepForward()` permanently.
    const interrupt = () => {
        clearTimer();
        setPhase("idle");
        setAwaitingInput(null);
        setTransition(undefined);
        setPendingPlay(undefined);
    };

    const controls: GamePlaybackControls = {
        play: () => setIsPlaying(true),
        pause: () => { setIsPlaying(false); interrupt(); },
        toggle: () => setIsPlaying((prev) => !prev),
        stepForward: () => {
            setIsPlaying(false);
            interrupt();
            if (cursorIndex < frames.length - 1) scheduleAdvance();
        },
        stepBack: () => {
            setIsPlaying(false);
            interrupt();
            const prevIndex = Math.max(0, cursorIndex - 1);
            setCursorId(frames[prevIndex].id);
        },
        seek: (index: number) => {
            setIsPlaying(false);
            interrupt();
            const clamped = Math.min(Math.max(0, index), frames.length - 1);
            setCursorId(frames[clamped].id);
        },
        seekToStart: () => controls.seek(0),
        seekToLive: () => {
            interrupt();
            setMode("live");
            setCursorId(frames[frames.length - 1].id);
            setIsPlaying(true);
        },
        setSpeed: (next: PlaybackSpeed) => setSpeedState(next),
        submitInput: () => {
            if (phase !== "await-input") return;
            setAwaitingInput(null);
            scheduleAdvance();
        },
    };

    const state: GamePlaybackState = {
        frame: frames[cursorIndex] ?? frames[frames.length - 1],
        cursor: cursorIndex,
        mode,
        phase,
        awaitingInput,
        isPlaying,
        speed,
        effectiveSpeed,
        transition,
        pendingPlay,
        isBehindLive,
        behindBy,
    };

    return [state, controls];
}
