// Shared by the season-sim dice (`SimDiceRoll`) and the in-game field dice (`SimFieldDie`) so the
// two tosses stay in step. An MLB Showdown at-bat is two twenty-sided rolls.
const SIDES = 20;

/** Face-change cadence mid-air. Fast enough to read as a tumble, slow enough not to strobe. */
export const SCRAMBLE_MS = 70;
/** The swing die lags the pitch die so the pair reads as two throws, not one mirrored animation. */
export const STAGGER_MS = 170;

/** Duration of one toss. MUST MATCH the `sim-die-toss` / `sim-die-shadow` durations in index.css
 *  (the in-game dice override it inline with their own, shorter toss). */
export const TOSS_MS = 900;

export const rollFace = () => 1 + Math.floor(Math.random() * SIDES);
