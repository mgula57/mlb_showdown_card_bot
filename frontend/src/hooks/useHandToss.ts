/**
 * @fileoverview One hand-thrown die's throw in a game people play (`HandDie`): the blank die at
 * rest, one short throw the moment it's rolled (or, for the other player's die, the moment their
 * roll arrives), then landed and still a beat before its number shows. Kept apart from the die so
 * a host can run the throw once and hand it to every copy of that die on the board.
 */
import { useEffect, useState } from "react";

import { HAND_REVEAL_BEAT_MS, HAND_THROW_MS } from "./useDieToss";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

/** At rest (blank, or showing its number), in the air, or landed and waiting to show the number. */
export type HandTossPhase = "rest" | "throwing" | "landed";

export type HandToss = {
    phase: HandTossPhase;
    /** Goes up with each throw, so each one runs its animation from the start. */
    throwCount: number;
};

export type HandTossInput = {
    /** The roll, once it's made. */
    value?: number | null;
    /** This die's roll is the one being waited on (theirs or this player's). A roll that arrives
     *  after it was waited on is thrown; one that shows up any other way (on page load, or the pitch
     *  carried along with a swing's play) just sits face up. */
    isAwaited?: boolean;
    /** This die's roll is on its way to the server. */
    isBusy?: boolean;
    /** A roll that shows up without being waited on (one made while the field was still playing out
     *  the last play) is thrown when this changes to a new key with the roll in hand. */
    throwKey?: string | null;
};

export function useHandToss({ value = null, isAwaited = false, isBusy = false, throwKey = null }: HandTossInput): HandToss {
    const prefersReducedMotion = usePrefersReducedMotion();
    const [phase, setPhase] = useState<HandTossPhase>("rest");
    const [throwCount, setThrowCount] = useState(0);
    const [isWaitedOn, setIsWaitedOn] = useState(false);
    const [seenValue, setSeenValue] = useState(value);
    const [seenThrowKey, setSeenThrowKey] = useState(throwKey);

    // At most one throw starts per render, however many reasons there are for it.
    let isThrowing = phase !== "rest" || prefersReducedMotion;
    const throwNow = () => {
        if (isThrowing) return;
        isThrowing = true;
        setPhase("throwing");
        setThrowCount((count) => count + 1);
    };
    // Tapped (or rolled from the next-move button): the throw starts now, before the roll is back
    if (isBusy && value == null) throwNow();
    if (isAwaited && value == null && !isWaitedOn) setIsWaitedOn(true);
    if (value !== seenValue) {
        setSeenValue(value);
        if (value != null && isWaitedOn) {
            setIsWaitedOn(false);
            // The other player's roll: thrown as it arrives
            throwNow();
        }
    }
    // A roll that arrived unseen, thrown as it first shows
    if (throwKey !== seenThrowKey) {
        setSeenThrowKey(throwKey);
        if (throwKey != null && value != null) throwNow();
    }
    // The roll didn't go through: back to the blank die to tap again
    if (phase === "landed" && value == null && !isBusy && isAwaited) setPhase("rest");

    useEffect(() => {
        if (phase !== "throwing") return;
        const landed = window.setTimeout(() => setPhase("landed"), HAND_THROW_MS);
        return () => window.clearTimeout(landed);
    }, [phase, throwCount]);
    useEffect(() => {
        if (phase !== "landed" || value == null) return;
        const revealed = window.setTimeout(() => setPhase("rest"), HAND_REVEAL_BEAT_MS);
        return () => window.clearTimeout(revealed);
    }, [phase, value]);

    return { phase, throwCount };
}
