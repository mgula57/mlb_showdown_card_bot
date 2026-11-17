/**
 * @fileoverview The plate appearance as the rolls it's made of, in the order the engine makes them:
 * any steal before the pitch, the pitch, the swing, a double-play turn on it, and any runner sent
 * for an extra base after it. `MatchupCenterPanel` numbers them so the board reads as a sequence.
 */
import type { AdvantageSide } from "../../domain/play";
import type { RunnerRoll } from "../../domain/timeline";
import type { PendingRunnerThrow } from "./SimRunnerRolls";

export type PlateAppearanceStepKind = RunnerRoll["kind"] | "pitch" | "swing";

/** `current` is the first step not yet made: the roll the game is on (or waiting on). */
export type PlateAppearanceStepState = "done" | "current" | "upcoming";

export type PlateAppearanceStep = {
    key: string;
    kind: PlateAppearanceStepKind;
    label: string;
    state: PlateAppearanceStepState;
    /** What a throw on a runner came to, and its die. */
    isSafe?: boolean;
    roll?: number;
    /** The pitch's winner, once it's read. */
    advantage?: AdvantageSide;
    pitchRoll?: number;
    swingResult?: string;
};

const BASE_NAMES: Record<number, string> = { 2: "2nd", 3: "3rd", 4: "Home" };
const THROW_LABELS: Record<RunnerRoll["kind"], string> = { steal: "Steal", advance: "Extra Base", double_play: "Double Play" };

const throwLabel = (kind: RunnerRoll["kind"], base: number) =>
    kind === "double_play" ? THROW_LABELS[kind] : `${THROW_LABELS[kind]} ${BASE_NAMES[base + 1] ?? ""}`.trim();

/** The key a throw is known by within one plate appearance: one runner tries a base once. */
export const runnerRollKey = (roll: Pick<RunnerRoll, "kind" | "base"> & { runner: { id?: number | string } }) =>
    `${roll.kind}|${roll.runner.id ?? ""}|${roll.base}`;

export function plateAppearanceSteps({ throws, pendingThrow, pitch, swing }: {
    /** The throws on runners made so far in this plate appearance. */
    throws: RunnerRoll[];
    /** A live game's throw still to roll. */
    pendingThrow?: PendingRunnerThrow;
    pitch: { roll?: number; advantage?: AdvantageSide };
    swing: { result?: string };
}): PlateAppearanceStep[] {
    const thrown = (kind: RunnerRoll["kind"]) => throws
        .filter((roll) => roll.kind === kind)
        .map((roll): Omit<PlateAppearanceStep, "state"> & { isDone: boolean } => ({
            key: runnerRollKey(roll), kind, label: throwLabel(kind, roll.base), isSafe: roll.isSafe, roll: roll.roll, isDone: true,
        }));
    const pending = (kind: PendingRunnerThrow["kind"]) => pendingThrow?.kind === kind && !throws.some((roll) => runnerRollKey(roll) === runnerRollKey(pendingThrow))
        ? [{ key: runnerRollKey(pendingThrow), kind, label: throwLabel(kind, pendingThrow.base), isDone: false }]
        : [];

    const steps = [
        ...thrown("steal"),
        ...pending("steal"),
        { key: "pitch", kind: "pitch" as const, label: "Pitch", advantage: pitch.advantage, pitchRoll: pitch.advantage ? pitch.roll : undefined, isDone: pitch.advantage != null },
        { key: "swing", kind: "swing" as const, label: "Swing", swingResult: swing.result, isDone: swing.result != null },
        ...thrown("double_play"),
        ...thrown("advance"),
        ...pending("advance"),
    ];
    const currentIndex = steps.findIndex((step) => !step.isDone);
    return steps.map(({ isDone, ...step }, i) => ({ ...step, state: isDone ? "done" : i === currentIndex ? "current" : "upcoming" }));
}
