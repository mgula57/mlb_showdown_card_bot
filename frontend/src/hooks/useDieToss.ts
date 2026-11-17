/**
 * @fileoverview Timing for one in-game d20 toss: whether it's still tumbling, and when it lands.
 * Lives apart from `RollDie` so anything choreographed around a die (e.g. `SimRunnerRolls`
 * folding the defense into the roll once it settles) runs off the exact same clock as the die.
 */
import { useEffect, useState } from "react";

import type { PlayPhase } from "./useGamePlayback";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

// The in-game toss is quicker than the season-sim one and has to be over before the result badge
// reveals. A play with dice gets a "pitch" beat of at least `SIM_PITCH_BEAT_MS` (see PHASE_MS in
// useGamePlayback), so the landed dice hold well clear of the result. All of it is divided by
// playback speed, exactly as the phase beats are, so the margin holds at 2x and 4x.
export const FIELD_TOSS_MS = 450;
/** A die thrown by hand in a game people play (`HandDie`): one rattling jump, then a still beat
 *  before its number shows. Whatever that roll decides waits for the whole of it. */
export const HAND_THROW_MS = 380;
export const HAND_REVEAL_BEAT_MS = 180;
export const HAND_DIE_REVEAL_MS = HAND_THROW_MS + HAND_REVEAL_BEAT_MS;
/** The pitch reads in two beats once its die's number is up (sim or hand thrown): first the sum
 *  against On-Base holds on its own (`PitchCompare`, with no winner yet), then the winner shows and
 *  holds on the cards' commands before anything about the swing does. */
export const PITCH_READ_BEAT_MS = 1000;
export const PITCH_VERDICT_BEAT_MS = 1000;
/** Once the swing's result lights up on the winner's chart (the die sliding to its cell, the cell
 *  landing), the field waits this long before reacting, so the eye reads the chart first and then
 *  comes back up to the field (the "read" phase in `useGamePlayback`). */
export const CHART_READ_BEAT_MS = 900;
/** A sim's whole "pitch" beat at 1x when the play has dice: the toss, then both pitch beats. */
export const SIM_PITCH_BEAT_MS = FIELD_TOSS_MS + PITCH_READ_BEAT_MS + PITCH_VERDICT_BEAT_MS;
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
