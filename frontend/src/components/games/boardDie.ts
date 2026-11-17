/** @fileoverview A plate-appearance die as the board's copies of it see it (`RollMirrors`). */
import type { PlayEntry } from "../../domain/play";
import type { HandTossInput } from "../../hooks/useHandToss";
import type { RollPrompt } from "./GameField";

/** One of the plate appearance's dice as the board sees it. */
export type BoardDie = {
    /** One throw. A new one replays a copy's landing. */
    key: string;
    /** The roll, once it's back. */
    value: number | null;
    /** In the air, or landed but its number not up yet: the face scrambles. */
    isTumbling: boolean;
    /** Playback speed, so a copy scrambles as fast as the die it copies. */
    speed: number;
};

/** The die's number is up. */
export const isDieShown = (die?: BoardDie): die is BoardDie & { value: number } => !!die && !die.isTumbling && die.value != null;

/** A roll already made, for a copy that only shows its number. */
export const restingDie = (key: string, value: number): BoardDie => ({ key, value, isTumbling: false, speed: 1 });

/** What each of a game people play's two dice is doing, from the roll waited on and the play being
 *  resolved: the input to its throw (`useHandToss`). A prompt only stands in while nothing is
 *  animating; once a play resolves the toss takes over, and the pitch die just holds its face. */
export function handTossInputs(rollPrompt: RollPrompt | undefined, pendingPlay: PlayEntry | undefined): Record<"pitch" | "swing", HandTossInput> {
    const prompt = pendingPlay ? undefined : rollPrompt;
    return {
        pitch: {
            value: prompt ? prompt.heldPitch ?? null : pendingPlay?.roll?.pitchRoll ?? null,
            isAwaited: prompt?.kind === "pitch" || prompt?.kind === "steal",
            isBusy: prompt?.kind === "pitch" && !!prompt.isBusy,
            throwKey: prompt?.heldPitchThrowKey ?? null,
        },
        swing: {
            value: pendingPlay?.roll?.swingRoll ?? null,
            isAwaited: prompt?.kind === "swing",
            isBusy: prompt?.kind === "swing" && !!prompt.isBusy,
        },
    };
}
