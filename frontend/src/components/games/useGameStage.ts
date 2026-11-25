/**
 * @fileoverview View state for `GameStage`. It lives in a hook on the host rather than inside the
 * stage because the stage renders under a keyed playback component: a new sim remounts that subtree,
 * and the open tab, expanded field and open card should survive it. Only the per-sim state resets,
 * through `resetForNewSim`.
 */
import { useCallback, useState } from "react";

import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";

export type RailTab = 'playbyplay' | 'boxscore' | 'info';
/** Which side of the board the rail sits on from `md` up. Remembered on this device. */
export type RailSide = 'left' | 'right';

const RAIL_SIDE_KEY = 'gameRailSide:v1';

const loadRailSide = (): RailSide => {
    try {
        return localStorage.getItem(RAIL_SIDE_KEY) === 'left' ? 'left' : 'right';
    } catch {
        return 'right';
    }
};

export function useGameStage() {
    const [selectedCard, setSelectedCard] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [isFieldExpanded, setIsFieldExpanded] = useState(false);
    const [railTab, setRailTab] = useState<RailTab>('playbyplay');
    const [railSide, setRailSide] = useState<RailSide>(loadRailSide);
    const swapRailSide = useCallback(() => {
        setRailSide((side) => {
            const next = side === 'right' ? 'left' : 'right';
            try {
                localStorage.setItem(RAIL_SIDE_KEY, next);
            } catch {
                // Storage unavailable: the side just isn't remembered.
            }
            return next;
        });
    }, []);
    // A phone has no room for the rail beside the field, so its tabs swap the whole page between
    // the field and one of the rail's panels. Opens on the field.
    const [isPhoneFieldShown, setIsPhoneFieldShown] = useState(true);
    // Tracks whether the field's big Play button has been pressed for the CURRENT sim result.
    // `playbackState.cursor === 0` alone isn't enough to hide it on click — the cursor doesn't
    // advance to frame 1 until the first animation beat lands, which would leave the button
    // visible (and clickable again) for a beat after it's already been pressed.
    const [simPlayStarted, setSimPlayStarted] = useState(false);
    // The post-game recap covers the field once a game is final; the scoreboard's center toggle
    // tucks it away until the user brings it back (or loads a different sim, which earns a fresh recap).
    const [isRecapDismissed, setIsRecapDismissed] = useState(false);

    const resetForNewSim = useCallback(() => {
        setSimPlayStarted(false);
        setIsRecapDismissed(false);
    }, []);

    return {
        selectedCard, setSelectedCard,
        isFieldExpanded, setIsFieldExpanded,
        railTab, setRailTab,
        railSide, swapRailSide,
        isPhoneFieldShown, setIsPhoneFieldShown,
        simPlayStarted, setSimPlayStarted,
        isRecapDismissed, setIsRecapDismissed,
        resetForNewSim,
    };
}

export type GameStageState = ReturnType<typeof useGameStage>;
