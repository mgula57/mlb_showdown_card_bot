/**
 * @fileoverview The odds of a Showdown plate appearance, from the two cards alone. The pitcher rolls
 * a d20 and adds his Control: over the hitter's On-Base and the swing is rolled on the pitcher's
 * chart, otherwise on the hitter's. So the hitter takes the advantage on the low faces, 1 up to
 * `onbase - control`, and each outcome's chance is its share of the chart the swing lands on.
 */

export const DIE_FACES = 20;

/** Chart results in the order a chart reads, outs first. */
export const OUTCOME_ORDER = ['PU', 'SO', 'GB', 'FB', 'BB', '1B', '1B+', '2B', '3B', 'HR'];
export const OUT_RESULTS = new Set(['PU', 'SO', 'GB', 'FB']);

/** How many of the die's faces give the hitter the advantage: 1 through this many. */
export function hitterAdvantageFaces(control: number, onbase: number): number {
    return Math.max(0, Math.min(DIE_FACES, onbase - control));
}

/** Share of pitch rolls that go to the pitcher, as a whole percent. */
export function pitcherAdvantagePct(control: number, onbase: number): number {
    return Math.round(((DIE_FACES - hitterAdvantageFaces(control, onbase)) / DIE_FACES) * 100);
}

export type OutcomeOdds = { key: string; prob: number };

/** Each chart result's chance (0-1) in this matchup, in chart order (`OUTCOME_ORDER`). */
export function matchupOutcomeOdds({ control, onbase, pitcherValues, hitterValues }: {
    control: number;
    onbase: number;
    /** Each result's number of chart slots, out of `DIE_FACES`. */
    pitcherValues: Record<string, number>;
    hitterValues: Record<string, number>;
}): OutcomeOdds[] {
    const hitterChart = hitterAdvantageFaces(control, onbase) / DIE_FACES;
    const pitcherChart = 1 - hitterChart;
    const keys = Array.from(new Set([...Object.keys(hitterValues), ...Object.keys(pitcherValues)]));
    const rank = (key: string) => {
        const index = OUTCOME_ORDER.indexOf(key.toUpperCase());
        return index === -1 ? OUTCOME_ORDER.length : index;
    };
    return keys
        .map((key) => ({
            key,
            prob: hitterChart * ((hitterValues[key] ?? 0) / DIE_FACES) + pitcherChart * ((pitcherValues[key] ?? 0) / DIE_FACES),
        }))
        .filter((odds) => odds.prob > 0)
        .sort((a, b) => rank(a.key) - rank(b.key));
}
