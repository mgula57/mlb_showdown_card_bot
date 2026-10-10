/**
 * @fileoverview Timing for one in-game d20 toss: whether it's still tumbling, and when it lands.
 * Lives apart from `RollDie` so anything choreographed around a die (e.g. `SimRunnerRolls`
 * folding the defense into the roll once it settles) runs off the exact same clock as the die.
 */
import { useEffect, useState } from "react";

import type { PlayPhase } from "./useGamePlayback";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

// The in-game toss is quicker than the season-sim one and has to be over before the result badge
// reveals. The shortest "pitch" beat is 1500ms * 0.7 (a quiet play) = 1050ms at 1x (see PHASE_MS
// in useGamePlayback), so the longest a die can run — its stagger plus its toss — leaves the
// landed dice a clear beat on screen before the result. All of it is divided by playback speed,
// exactly as the phase beats are, so the margin holds at 2x and 4x.
export const FIELD_TOSS_MS = 450;
export const FIELD_STAGGER_MS = 80;
/** From this effective speed up the dice skip their motion and just show the roll — the beats are
 *  too short for a toss to read as anything but a flicker. */
const STATIC_DICE_SPEED = 4;

export type DieToss = {
    /** True while the die is in the air — the face shown should be scrambled. */
    isTumbling: boolean;
    /** No motion at all (reduced motion, or too fast to read) — show final states directly. */
    isStatic: boolean;
    delayMs: number;
    tossMs: number;
};

export function useDieToss({ playId, phase, speed = 1, staggerIndex = 0 }: {
    /** Identifies the beat being resolved; a new id restarts the toss. */
    playId: string;
    phase: PlayPhase;
    /** Effective playback speed (1, 2, 4, ... including any live catch-up boost). */
    speed?: number;
    /** Nth die of the beat: each lags the one before so a group reads as separate throws. */
    staggerIndex?: number;
}): DieToss {
    const prefersReducedMotion = usePrefersReducedMotion();
    const isStatic = prefersReducedMotion || speed >= STATIC_DICE_SPEED;
    // The beat whose toss has finished. Tracked per beat so a new one starts tumbling again, and
    // set from a timer (not an effect body) when this die's toss ends.
    const [landedFor, setLandedFor] = useState<string | null>(null);

    const delayMs = (staggerIndex * FIELD_STAGGER_MS) / speed;
    const tossMs = FIELD_TOSS_MS / speed;
    const isTumbling = phase === "pitch" && !isStatic && landedFor !== playId;

    useEffect(() => {
        if (!isTumbling) return;
        const landed = window.setTimeout(() => setLandedFor(playId), delayMs + tossMs);
        return () => window.clearTimeout(landed);
    }, [isTumbling, playId, delayMs, tossMs]);

    return { isTumbling, isStatic, delayMs, tossMs };
}
