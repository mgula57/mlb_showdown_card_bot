/**
 * @fileoverview View state for `GameStage`. It lives in a hook on the host rather than inside the
 * stage because the stage renders under a keyed playback component: a new sim remounts that subtree,
 * and the open tab, expanded field and open card should survive it. Only the per-sim state resets,
 * through `resetForNewSim`.
 */
import { useCallback, useState } from "react";

import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";

export type MobileTab = 'field' | 'playbyplay' | 'boxscore';
// The `md`–`lg` two-column view keeps the field pinned on the left and tabs only between the two
// panels that share the right column.
export type MidTab = Exclude<MobileTab, 'field'>;

export function useGameStage() {
    const [selectedCard, setSelectedCard] = useState<ShowdownBotCardAPIResponse | null>(null);
    const [isFieldExpanded, setIsFieldExpanded] = useState(false);
    const [mobileTab, setMobileTab] = useState<MobileTab>('field');
    const [midTab, setMidTab] = useState<MidTab>('playbyplay');
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
        mobileTab, setMobileTab,
        midTab, setMidTab,
        simPlayStarted, setSimPlayStarted,
        isRecapDismissed, setIsRecapDismissed,
        resetForNewSim,
    };
}

export type GameStageState = ReturnType<typeof useGameStage>;
