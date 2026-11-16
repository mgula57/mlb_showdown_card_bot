/**
 * @fileoverview The dice of a game people play, each thrown on its own. `HandDie` is one die at its
 * dock (beside the pitcher, or at the plate) through a whole throw: the blank die the player whose
 * turn it is taps, then one short throw, a jump that rattles as it goes, starting the moment it's
 * rolled (or, for the other player's die, the moment their roll arrives). The number only shows a
 * beat after the die lands and once the roll is back; until then the face keeps scrambling.
 * `HeldDie` is a roll already made, face up. Both match `RollDie`'s size and label.
 */
import { useEffect, useState } from "react";

import { HAND_REVEAL_BEAT_MS, HAND_THROW_MS } from "../../hooks/useDieToss";
import { usePrefersReducedMotion } from "../../hooks/usePrefersReducedMotion";
import { D20Face } from "../team_builder/sim/SimDiceRoll";
import { rollFace, SCRAMBLE_MS } from "../team_builder/sim/dieRoll";

const DIE_BOX = "relative h-9 w-9 @md:h-11 @md:w-11";
const DIE_FACE = "absolute inset-0 drop-shadow-[0_2px_0_rgb(0_0_0/0.25)]";
const DIE_LABEL = "text-[8px] font-bold uppercase tracking-[0.12em] text-(--tertiary)";

/** The throw: one jump, rattling the whole way (`.hand-die-throw`). The landed die then holds still
 *  `REVEAL_BEAT_MS` before its number shows. */
const THROW_MS = HAND_THROW_MS;
const REVEAL_BEAT_MS = HAND_REVEAL_BEAT_MS;

/** At rest (blank, or showing its number), in the air, or landed and waiting to show the number. */
type ThrowPhase = "rest" | "throwing" | "landed";

type HandDieProps = {
    label: string;
    /** The roll, once it's made. */
    value?: number | null;
    /** This die's roll is the one being waited on (theirs or this player's). A roll that arrives
     *  after it was waited on is thrown; one that shows up any other way (on page load, or the pitch
     *  carried along with a swing's play) just sits face up. */
    isAwaited?: boolean;
    /** Set while it's this player's throw: the blank die takes a tap. */
    onRoll?: () => void;
    /** This die's roll is on its way to the server. */
    isBusy?: boolean;
};

export function HandDie({ label, value = null, isAwaited = false, onRoll, isBusy = false }: HandDieProps) {
    const prefersReducedMotion = usePrefersReducedMotion();
    const [phase, setPhase] = useState<ThrowPhase>("rest");
    const [throwCount, setThrowCount] = useState(0);
    const [isWaitedOn, setIsWaitedOn] = useState(false);
    const [seenValue, setSeenValue] = useState(value);

    const startThrow = () => {
        setPhase("throwing");
        setThrowCount((count) => count + 1);
    };
    // Tapped (or rolled from the next-move button): the throw starts now, before the roll is back
    if (isBusy && value == null && phase === "rest" && !prefersReducedMotion) startThrow();
    if (isAwaited && value == null && !isWaitedOn) setIsWaitedOn(true);
    if (value !== seenValue) {
        setSeenValue(value);
        if (value != null && isWaitedOn) {
            setIsWaitedOn(false);
            // The other player's roll: thrown as it arrives
            if (phase === "rest" && !prefersReducedMotion) startThrow();
        }
    }
    // The roll didn't go through: back to the blank die to tap again
    if (phase === "landed" && value == null && !isBusy && isAwaited) setPhase("rest");

    useEffect(() => {
        if (phase !== "throwing") return;
        const landed = window.setTimeout(() => setPhase("landed"), THROW_MS);
        return () => window.clearTimeout(landed);
    }, [phase, throwCount]);
    useEffect(() => {
        if (phase !== "landed" || value == null) return;
        const revealed = window.setTimeout(() => setPhase("rest"), REVEAL_BEAT_MS);
        return () => window.clearTimeout(revealed);
    }, [phase, value]);

    const isHidden = phase !== "rest";
    const [scrambled, setScrambled] = useState(rollFace);
    useEffect(() => {
        if (!isHidden) return;
        const interval = window.setInterval(() => setScrambled(rollFace()), SCRAMBLE_MS);
        return () => window.clearInterval(interval);
    }, [isHidden]);

    // The other player's turn, before their roll arrives: nothing here yet.
    if (value == null && !onRoll && !isHidden) return null;

    const canTap = phase === "rest" && value == null && !!onRoll && !isBusy;
    const face = (
        <span className={DIE_BOX}>
            {canTap && <span className="absolute inset-0 animate-ping rounded-full bg-(--showdown-blue-fill) opacity-40" />}
            <span
                // A new key per throw, so each one runs its animation from the start
                key={phase === "throwing" ? `throw-${throwCount}` : "still"}
                className={`${DIE_FACE} ${phase === "throwing" ? "hand-die-throw" : "transition-transform duration-150 group-hover:scale-110 group-active:scale-95"}`}
                style={phase === "throwing" ? { animationDuration: `${THROW_MS}ms` } : undefined}
            >
                <D20Face value={isHidden ? scrambled : value ?? "?"} accent="var(--die-body)" ink="var(--die-ink)" />
            </span>
        </span>
    );

    if (canTap) {
        return (
            <button
                type="button"
                onClick={onRoll}
                aria-label={`Roll ${label.toLowerCase()}`}
                className="group pointer-events-auto flex cursor-pointer flex-col items-center gap-0.5"
            >
                {face}
                <span className={DIE_LABEL}>Roll</span>
            </button>
        );
    }
    return (
        <div aria-label={value != null && !isHidden ? `${label} roll ${value}` : `Rolling ${label.toLowerCase()}`} className="pointer-events-none flex flex-col items-center gap-0.5">
            {face}
            <span className={DIE_LABEL}>{label}</span>
        </div>
    );
}

export function HeldDie({ value, label }: { value: number; label: string }) {
    return (
        <div aria-label={`${label} roll ${value}`} className="pointer-events-none flex flex-col items-center gap-0.5">
            <div className={`${DIE_BOX} drop-shadow-[0_2px_0_rgb(0_0_0/0.25)]`}>
                <D20Face value={value} accent="var(--die-body)" ink="var(--die-ink)" />
            </div>
            <span className={DIE_LABEL}>{label}</span>
        </div>
    );
}
