/**
 * @fileoverview The d20 shared by every in-game sim roll readout (`SimFieldDie` for the pitch and
 * swing, `SimRunnerRolls` for steals, extra-base sends and double plays). Same die art and toss
 * motion as the season-sim dice in `SimDiceRoll`, but neutral (white in light mode, black in
 * dark). It tumbles through the "pitch" beat, lands on its roll before the result reveals, and
 * holds that face until the beat commits. Timing comes from `useDieToss`.
 */
import { useEffect, useState } from "react";

import type { PlayPhase } from "../../hooks/useGamePlayback";
import { useDieToss } from "../../hooks/useDieToss";
import { D20Face } from "../team_builder/sim/SimDiceRoll";
import { rollFace, SCRAMBLE_MS } from "../team_builder/sim/dieRoll";

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
    const { isTumbling, isStatic, delayMs, tossMs } = useDieToss({ playId, phase, speed, staggerIndex });
    const [scrambled, setScrambled] = useState(rollFace);

    useEffect(() => {
        if (!isTumbling) return;
        const interval = window.setInterval(() => setScrambled(rollFace()), SCRAMBLE_MS / speed);
        return () => window.clearInterval(interval);
    }, [isTumbling, speed]);

    // Keyed on the beat (not the phase), so the toss runs once and holds its landing.
    const tossKey = isStatic ? null : playId;

    return (
        <div aria-label={`${label} roll ${value}`} className="pointer-events-none flex flex-col items-center gap-0.5">
            <div className="relative h-9 w-9 @md:h-11 @md:w-11">
                <div
                    key={tossKey ?? "static"}
                    className={`absolute inset-0 drop-shadow-[0_2px_0_rgb(0_0_0/0.25)] ${tossKey ? "sim-die-toss" : ""}`}
                    // Overrides the 900ms in the `sim-die-toss` rule: the toss starts with the pitch
                    // beat and finishes before the result reveals.
                    style={tossKey ? { animationDuration: `${tossMs}ms`, animationDelay: `${delayMs}ms` } : undefined}
                >
                    <D20Face value={isTumbling ? scrambled : value} accent="var(--die-body)" ink="var(--die-ink)" />
                </div>
            </div>
            <span className="text-[8px] font-bold uppercase tracking-[0.12em] text-(--tertiary)">{label}</span>
        </div>
    );
}
