/**
 * @fileoverview Canonical play-by-play entry: one completed plate appearance. Designed at this
 * granularity deliberately — it's the only detail level the sim engine will ever be able to
 * produce (one pitch-roll + one swing-roll per plate appearance, never a full pitch count), so
 * the same `PlayEntry[]` can drive a sim game's log later via a different adapter, with no
 * redesign of the rendering component.
 */

export type PlayEntry = {
    id: string;              // about.atBatIndex — stable across polls
    inning: number;
    isTop: boolean;
    batterId?: number;
    batterName: string;
    pitcherId?: number;
    pitcherName: string;
    event: string;            // badge label, e.g. "Flyout", "Walk", "Home Run"
    description: string;
    isScoringPlay?: boolean;
    outs?: number;            // post-play outs in the half-inning
    roll?: {                  // SIM ONLY - unpopulated until a sim adapter exists
        pitchRoll: number;
        pitchResult: string;
        swingRoll: number;
        swingResult: string;
    };
};
