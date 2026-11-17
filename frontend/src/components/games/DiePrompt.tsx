/**
 * @fileoverview The dice of a game people play, each thrown on its own. `HandDie` is one die at its
 * dock (beside the pitcher, or at the plate) through a whole throw: the blank die the player whose
 * turn it is taps, then one short throw, a jump that rattles as it goes, starting the moment it's
 * rolled (or, for the other player's die, the moment their roll arrives). The number only shows a
 * beat after the die lands and once the roll is back; until then the face keeps scrambling.
 * `HeldDie` is a roll already made, face up. Both match `RollDie`'s size and label.
 */
import { HAND_THROW_MS } from "../../hooks/useDieToss";
import { useHandToss, type HandToss, type HandTossInput } from "../../hooks/useHandToss";
import { useScrambledFace } from "../../hooks/useScrambledFace";
import { D20Face } from "../team_builder/sim/SimDiceRoll";

const DIE_BOX = "relative h-9 w-9 @md:h-11 @md:w-11";
const DIE_FACE = "absolute inset-0 drop-shadow-[0_2px_0_rgb(0_0_0/0.25)]";
const DIE_LABEL = "text-[8px] font-bold uppercase tracking-[0.12em] text-(--tertiary)";

type HandDieProps = HandTossInput & {
    label: string;
    /** Set while it's this player's throw: the blank die takes a tap. */
    onRoll?: () => void;
};

/** A die that keeps its own throw (`useHandToss`). */
export function HandDie(props: HandDieProps) {
    const toss = useHandToss(props);
    return <HandDieFace {...props} toss={toss} />;
}

/** A die whose throw is kept by its host, so the copies of it elsewhere on the board
 *  (`RollMirrors`) run off the same throw and land with it. */
export function HandDieFace({ label, value = null, onRoll, isBusy = false, toss }: Omit<HandDieProps, "isAwaited" | "throwKey"> & { toss: HandToss }) {
    const { phase, throwCount } = toss;
    const isHidden = phase !== "rest";
    const scrambled = useScrambledFace(isHidden);

    // The other player's turn, before their roll arrives: nothing here yet.
    if (value == null && !onRoll && !isHidden) return null;

    const canTap = phase === "rest" && value == null && !!onRoll && !isBusy;
    const face = (
        <span className={DIE_BOX}>
            {canTap && <span className="die-tap-ring absolute inset-0 rounded-full" />}
            <span
                // A new key per throw, so each one runs its animation from the start
                key={phase === "throwing" ? `throw-${throwCount}` : "still"}
                className={`${DIE_FACE} ${phase === "throwing" ? "hand-die-throw" : "transition-transform duration-150 group-hover:scale-110 group-active:scale-95"}`}
                style={phase === "throwing" ? { animationDuration: `${HAND_THROW_MS}ms` } : undefined}
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
