import { useEffect, useState } from "react";

import { rollFace, SCRAMBLE_MS } from "../components/team_builder/sim/dieRoll";

/** A d20 face that changes every `SCRAMBLE_MS` (divided by `speed`) while `isScrambling`, for a die
 *  whose number isn't up yet. */
export function useScrambledFace(isScrambling: boolean, speed = 1): number {
    const [face, setFace] = useState(rollFace);
    useEffect(() => {
        if (!isScrambling) return;
        const interval = window.setInterval(() => setFace(rollFace()), SCRAMBLE_MS / speed);
        return () => window.clearInterval(interval);
    }, [isScrambling, speed]);
    return face;
}

/** A face from 20 down to 1 and around again every `SCRAMBLE_MS` while `isSweeping`, for a marker
 *  running along a meter while its die is in the air. */
export function useSweptFace(isSweeping: boolean, speed = 1): number {
    const [face, setFace] = useState(20);
    useEffect(() => {
        if (!isSweeping) return;
        const interval = window.setInterval(() => setFace((current) => (current <= 1 ? 20 : current - 1)), SCRAMBLE_MS / speed);
        return () => window.clearInterval(interval);
    }, [isSweeping, speed]);
    return face;
}
