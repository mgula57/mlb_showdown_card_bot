/**
 * @fileoverview One of the sim's two plate-appearance d20s, docked beside the player it belongs
 * to: the pitch die to the left of the pitcher, the swing die to the left of the hitter. Renders
 * nothing when the play being resolved carries no roll (real MLB games, half-inning breaks,
 * runner-only beats — those get `SimRunnerRolls` instead).
 */
import type { PlayEntry } from "../../domain/play";
import type { PlayPhase } from "../../hooks/useGamePlayback";
import RollDie from "./RollDie";

export default function SimFieldDie({ kind, pendingPlay, phase, speed }: {
    kind: "pitch" | "swing";
    pendingPlay?: PlayEntry;
    phase: PlayPhase;
    speed?: number;
}) {
    const roll = pendingPlay?.roll;
    if (!roll || !pendingPlay) return null;

    const isPitch = kind === "pitch";
    return (
        <RollDie
            value={isPitch ? roll.pitchRoll : roll.swingRoll}
            label={isPitch ? "Pitch" : "Swing"}
            playId={pendingPlay.id}
            phase={phase}
            speed={speed}
            // The swing die lags the pitch die so the pair reads as two throws.
            staggerIndex={isPitch ? 0 : 1}
        />
    );
}
