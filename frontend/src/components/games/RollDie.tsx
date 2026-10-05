/**
 * @fileoverview The d20 shared by every in-game sim roll readout (`SimFieldDie` for the pitch and
 * swing, `SimRunnerRolls` for steals and extra-base sends). Same die art and toss motion as the
 * season-sim dice in `SimDiceRoll`, but neutral (white in light mode, black in dark). It tumbles
 * through the "pitch" beat, lands on its roll before the result reveals, and holds that face
 * until the beat commits.
 */
import { useEffect, useState } from "react";

import type { PlayPhase } from "../../hooks/useGamePlayback";
import { usePrefersReducedMotion } from "../../hooks/usePrefersReducedMotion";
import { D20Face } from "../team_builder/sim/SimDiceRoll";
import { rollFace, SCRAMBLE_MS } from "../team_builder/sim/dieRoll";

// The in-game toss is quicker than the season-sim one and has to be over before the result badge
// reveals. The shortest "pitch" beat is 1500ms * 0.7 (a quiet play) = 1050ms at 1x (see PHASE_MS
// in useGamePlayback), so the longest a die can run — its stagger plus its toss — leaves the
// landed dice a clear beat on screen before the result. All of it is divided by playback speed,
// exactly as the phase beats are, so the margin holds at 2x and 4x.
const FIELD_TOSS_MS = 450;
export const FIELD_STAGGER_MS = 80;
/** From this effective speed up the dice skip their motion and just show the roll — the beats are
 *  too short for a toss to read as anything but a flicker. */
const STATIC_DICE_SPEED = 4;

export default function RollDie({ value, label, playId, phase, speed = 1, staggerIndex = 0 }: {
    value: number;
    label: string;
    /** Identifies the beat being resolved; a new id restarts the toss. */
    playId: string;
    phase: PlayPhase;
    /** Effective playback speed (1, 2, 4, ... including any live catch-up boost). */
    speed?: number;
    /** Nth die of the beat: each lags the one before so a group reads as separate throws. */
    staggerIndex?: number;
}) {
    const prefersReducedMotion = usePrefersReducedMotion();
    const isStatic = prefersReducedMotion || speed >= STATIC_DICE_SPEED;
    const [scrambled, setScrambled] = useState(rollFace);
    // The beat whose toss has finished. Tracked per beat so a new one starts tumbling again, and
    // set from a timer (not an effect body) when this die's toss ends.
    const [landedFor, setLandedFor] = useState<string | null>(null);

    const delayMs = (staggerIndex * FIELD_STAGGER_MS) / speed;
    const tossMs = FIELD_TOSS_MS / speed;
    const tumbling = phase === "pitch" && !isStatic && landedFor !== playId;

    useEffect(() => {
        if (!tumbling) return;
        const interval = window.setInterval(() => setScrambled(rollFace()), SCRAMBLE_MS / speed);
        const landed = window.setTimeout(() => setLandedFor(playId), delayMs + tossMs);
        return () => { window.clearInterval(interval); window.clearTimeout(landed); };
    }, [tumbling, speed, playId, delayMs, tossMs]);

    // Keyed on the beat (not the phase), so the toss runs once and holds its landing.
    const tossKey = isStatic ? null : playId;

    return (
        <div aria-label={`${label} roll ${value}`} className="pointer-events-none flex flex-col items-center gap-0.5">
            <div className="relative h-9 w-9 @md:h-11 @md:w-11">
                <div
                    key={tossKey ?? "static"}
                    className={`absolute inset-0 drop-shadow-md ${tossKey ? "sim-die-toss" : ""}`}
                    // Overrides the 900ms in the `sim-die-toss` rule: the toss starts with the pitch
                    // beat and finishes before the result reveals.
                    style={tossKey ? { animationDuration: `${tossMs}ms`, animationDelay: `${delayMs}ms` } : undefined}
                >
                    <D20Face value={tumbling ? scrambled : value} accent="var(--die-body)" ink="var(--die-ink)" />
                </div>
            </div>
            <span className="text-[8px] font-bold uppercase tracking-[0.12em] text-(--tertiary)">{label}</span>
        </div>
    );
}
