/**
 * @fileoverview Showdown dice for a REAL game. An MLB play has an outcome but no rolls, so this
 * works backwards from the outcome: given the batter's and pitcher's cards, pick a pitch roll and
 * a swing roll that would have produced that result on a Showdown chart. Attaching that `roll` to
 * each `PlayEntry` is all `GameField` needs — `SimFieldDie` and `advantageSideOf` already read it.
 *
 * Every roll is seeded from the game + play id, so rebuilding the timeline never re-rolls a play.
 */
import type { ShowdownBotCardAPIResponse, ShowdownBotCardChart } from "../api/showdownBotCard";
import type { PlayEntry } from "./play";
import { resolveCardKey } from "./players";
import type { GameFrame, GameTimeline } from "./timeline";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;
type Side = "pitcher" | "hitter";

const DIE_SIDES = 20;

// ------------------------------------------------------------------
// SEEDED RNG
// ------------------------------------------------------------------

/** Small deterministic PRNG (mulberry32) seeded from a string hash. */
export class SeededRandom {
    private state: number;

    constructor(seed: string) {
        let hash = 1779033703 ^ seed.length;
        for (let i = 0; i < seed.length; i++) {
            hash = Math.imul(hash ^ seed.charCodeAt(i), 3432918353);
            hash = (hash << 13) | (hash >>> 19);
        }
        this.state = hash >>> 0;
    }

    /** Uniform float in [0, 1). */
    next(): number {
        this.state = (this.state + 0x6d2b79f5) | 0;
        let t = this.state;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }

    /** Uniform pick from a non-empty list. */
    pick<T>(items: T[]): T {
        return items[Math.floor(this.next() * items.length)];
    }
}

// ------------------------------------------------------------------
// MLB EVENT -> CHART RESULT
// ------------------------------------------------------------------

/** Ordered: the first matching rule wins, so the compound events ("Strikeout Double Play",
 *  "Grounded Into DP") are caught before their looser substrings ("double"). Each rule lists the
 *  chart results that can stand for the event, best first — hitter charts have no PU, so a pop
 *  out falls back to FB there. */
const EVENT_RULES: [RegExp, string[]][] = [
    [/strikeout/, ["SO"]],
    [/walk|hit by pitch|catcher interf/, ["BB"]],
    [/home run/, ["HR"]],
    [/double play|triple play|into dp|groundout|ground out|forceout|force out|fielders? choice|field error|bunt/, ["GB"]],
    [/pop ?out/, ["PU", "FB"]],
    [/flyout|fly out|sac fly|lineout|line out/, ["FB"]],
    [/single/, ["1B", "1B+"]],
    [/double/, ["2B"]],
    [/triple/, ["3B"]],
];

const chartResultsFor = (event: string): string[] | undefined => {
    const normalized = event.toLowerCase();
    return EVENT_RULES.find(([pattern]) => pattern.test(normalized))?.[1];
};

// ------------------------------------------------------------------
// CHART LOOKUP
// ------------------------------------------------------------------

/** Roll (1-20) -> chart result. Prefers the explicit `results` map; falls back to parsing
 *  `ranges` ({ "SO": "1-2", "HR": "19+", "3B": "-" }) for cards serialized without it. */
const chartSlots = (chart: ShowdownBotCardChart): Map<number, string> => {
    const slots = new Map<number, string>();
    if (chart.results && Object.keys(chart.results).length > 0) {
        for (const [roll, result] of Object.entries(chart.results)) {
            const value = Number(roll);
            if (value >= 1 && value <= DIE_SIDES) slots.set(value, String(result));
        }
        return slots;
    }
    for (const [result, range] of Object.entries(chart.ranges ?? {})) {
        const match = /^(\d+)(?:\s*-\s*(\d+)|(\+))?$/.exec(range.trim());
        if (!match) continue;
        const start = Number(match[1]);
        const end = match[3] ? DIE_SIDES : Number(match[2] ?? match[1]);
        for (let roll = start; roll <= Math.min(end, DIE_SIDES); roll++) slots.set(roll, result);
    }
    return slots;
};

/** Rolls on `chart` that land on the first of `results` the chart actually carries. */
const matchingRolls = (chart: ShowdownBotCardChart, results: string[]): { rolls: number[]; slots: Map<number, string> } | undefined => {
    const slots = chartSlots(chart);
    for (const result of results) {
        // A single can come off either single slot — they're one outcome as far as the real play goes.
        const accepted = result === "1B" ? ["1B", "1B+"] : [result];
        const rolls = [...slots].filter(([, r]) => accepted.includes(r)).map(([roll]) => roll);
        if (rolls.length > 0) return { rolls, slots };
    }
    return undefined;
};

// ------------------------------------------------------------------
// ROLL SYNTHESIS
// ------------------------------------------------------------------

/** Builds a pitch + swing roll pair consistent with a real play's outcome. Each side's chance of
 *  being the one that "produced" the result is weighted by how likely it was to win the pitch
 *  (control + d20 > on-base) times how much of its chart the result covers. Returns undefined
 *  when the play can't be expressed on either card (unmapped event, or missing cards). */
export const synthesizeRoll = (
    event: string,
    hitterChart: ShowdownBotCardChart,
    pitcherChart: ShowdownBotCardChart,
    rng: SeededRandom,
): PlayEntry["roll"] | undefined => {
    const results = chartResultsFor(event);
    if (!results) return undefined;

    const onBase = hitterChart.command;
    const control = pitcherChart.command;
    // Pitch rolls that win the pitcher the advantage: control + roll > on-base.
    const minPitcherRoll = Math.max(1, onBase - control + 1);
    const pitcherWinCount = Math.max(0, DIE_SIDES - minPitcherRoll + 1);
    const pitcherWinChance = pitcherWinCount / DIE_SIDES;

    const options: Record<Side, ReturnType<typeof matchingRolls>> = {
        pitcher: pitcherWinCount > 0 ? matchingRolls(pitcherChart, results) : undefined,
        hitter: pitcherWinCount < DIE_SIDES ? matchingRolls(hitterChart, results) : undefined,
    };
    const weights: Record<Side, number> = {
        pitcher: pitcherWinChance * (options.pitcher?.rolls.length ?? 0),
        hitter: (1 - pitcherWinChance) * (options.hitter?.rolls.length ?? 0),
    };
    const totalWeight = weights.pitcher + weights.hitter;
    if (totalWeight === 0) return undefined;

    const side: Side = rng.next() * totalWeight < weights.pitcher ? "pitcher" : "hitter";
    const swing = options[side]!;
    const pitchRoll = side === "pitcher"
        ? minPitcherRoll + Math.floor(rng.next() * pitcherWinCount)
        : 1 + Math.floor(rng.next() * (DIE_SIDES - pitcherWinCount));
    const swingRoll = rng.pick(swing.rolls);

    return {
        pitchRoll,
        pitchResult: side === "pitcher" ? "padv" : "hadv",
        swingRoll,
        swingResult: swing.slots.get(swingRoll) ?? results[0],
    };
};

const chartFor = (cardMap: CardMap, id: PlayEntry["batterId"], role: "H" | "P"): ShowdownBotCardChart | undefined =>
    cardMap[resolveCardKey(id, role) ?? ""]?.card?.chart;

/** Returns `timeline` with a synthesized `roll` on every play both cards can express. Plays
 *  that can't be expressed keep no roll — the field then shows the result without dice. */
export const withSyntheticRolls = (timeline: GameTimeline, cardMap: CardMap): GameTimeline => ({
    ...timeline,
    frames: timeline.frames.map((frame) => {
        const play = frame.play;
        if (!play || play.roll) return frame;
        const hitterChart = chartFor(cardMap, play.batterId, "H");
        const pitcherChart = chartFor(cardMap, play.pitcherId, "P");
        if (!hitterChart || !pitcherChart) return frame;
        const roll = synthesizeRoll(play.event, hitterChart, pitcherChart, new SeededRandom(`${timeline.gameId}-${play.id}`));
        return roll ? { ...frame, play: { ...play, roll } } : frame;
    }),
});

// ------------------------------------------------------------------
// SEGMENT SELECTION
// ------------------------------------------------------------------

type HalfInningSpan = { start: number; end: number; runs: number };

/** Each half-inning as a frame span: it starts on the frame that seats its leadoff hitter (the
 *  pre-game frame, or the HALF_INNING_BREAK before it) with the bases empty, and ends on the
 *  half's last play. */
const halfInningSpans = (frames: GameFrame[]): HalfInningSpan[] => {
    const starts = frames
        .map((frame, index) => (index === 0 || frame.kind === "HALF_INNING_BREAK" ? index : -1))
        .filter((index) => index >= 0);
    return starts.map((start, i) => {
        const end = (starts[i + 1] ?? frames.length) - 1;
        const runs = frames.slice(start + 1, end + 1).reduce((total, frame) => total + (frame.transition?.runsScored ?? 0), 0);
        return { start, end, runs };
    }).filter((span) => span.end > span.start);
};

/** A self-contained timeline covering one half-inning — a random one with runs in it when the
 *  game has any, so the reel always has something happening. */
export const sliceScoringHalfInning = (timeline: GameTimeline, rng: SeededRandom): GameTimeline => {
    const spans = halfInningSpans(timeline.frames);
    if (spans.length === 0) return timeline;
    const scoring = spans.filter((span) => span.runs > 0);
    const { start, end } = rng.pick(scoring.length > 0 ? scoring : spans);
    const frames = timeline.frames.slice(start, end + 1).map((frame, index) => ({ ...frame, index }));
    return { ...timeline, frames, liveIndex: frames.length - 1 };
};
