/**
 * @fileoverview The dice behind a sim's baserunning tests — steal attempts (before the pitch),
 * extra-base sends (after the ball is in play) and double-play turns (on the swing) — floated
 * over the middle of the diamond. Each is the same face-off as the pitch (`RollFaceoff`): the die
 * plus the defense (arm / OF / IF) on the left, against the runner's Speed (base bonus included)
 * on the right. The total pops in as the die lands; on the result beat the winner fills (navy for
 * the defense's Out, red for the runner's Safe) and the verdict hangs off the top.
 *
 * All motion runs off the die's own clock (`useDieToss`) and is divided by playback speed; at high
 * speed or with reduced motion every step simply shows its final state.
 *
 * In a game people play, a throw waits on the fielding club's roll first: `PendingRunnerRoll` sets
 * out the same face-off with the die still to roll.
 */
import type { ReactNode } from "react";

import type { PlayerRef } from "../../domain/game";
import type { RunnerRoll } from "../../domain/timeline";
import type { PlayPhase } from "../../hooks/useGamePlayback";
import { useDieToss } from "../../hooks/useDieToss";
import { HandDie } from "./DiePrompt";
import { RollFaceoff, type FaceoffSideContent } from "./RollFaceoff";
import { MiniDie, RollSum } from "./RollMirrors";

const BASE_NAMES: Record<number, string> = { 1: "1st", 2: "2nd", 3: "3rd", 4: "Home" };
const DEFENSE_LABELS: Record<RunnerRoll["kind"], string> = { steal: "Arm", advance: "OF", double_play: "IF" };

/** A throw on the bases before its die is rolled. */
export type PendingRunnerThrow = Omit<RunnerRoll, "kind" | "roll" | "isSafe"> & { kind: "steal" | "advance" };

const titleFor = (attempt: Pick<RunnerRoll, "kind" | "base">): string =>
    attempt.kind === "double_play"
        ? "Double Play"
        : `${attempt.kind === "steal" ? "Steal" : "Extra base to"} ${BASE_NAMES[attempt.base + 1] ?? ""}`;

/** Who's running and what they're trying, under the face-off. */
function ThrowFooter({ attempt, runner }: { attempt: Pick<RunnerRoll, "kind" | "base">; runner: PlayerRef }) {
    return (
        <>
            <span className="max-w-36 truncate font-semibold text-(--text-primary)">{runner.name}</span>
            <span>{titleFor(attempt)}</span>
        </>
    );
}

/** The runner's side: the Speed the throw has to beat. */
const runnerSide = (target?: number): FaceoffSideContent => ({ label: "Speed", children: <span>{target ?? "–"}</span> });

function RunnerRollRow({ attempt, index, beatId, phase, speed, plateDice }: {
    attempt: RunnerRoll;
    index: number;
    beatId: string;
    phase: PlayPhase;
    speed: number;
    plateDice: number;
}) {
    const playId = `${beatId}-${index}`;
    // A DP turn rides the swing beat, so its die waits for the beat's pitch and swing dice to land first.
    const staggerIndex = index + (attempt.kind === "double_play" ? plateDice : 0);
    const { isTumbling } = useDieToss({ playId, phase, speed, staggerIndex });
    // The outcome is a spoiler until the dice have landed; the result beat onward reveals it, with
    // the rest of the field, once the swing has been read off the chart (the "read" beat).
    const isRevealed = phase !== "pitch" && phase !== "read";
    const die = { key: playId, value: attempt.roll, isTumbling, speed };
    const total = attempt.defense != null && !isTumbling ? attempt.defense + attempt.roll : undefined;
    const winner = !isRevealed ? undefined : attempt.isSafe ? "offense" : "defense";

    return (
        <RollFaceoff
            size="field"
            speed={speed}
            throwKey={playId}
            isNumberUp={!isTumbling}
            winner={winner}
            verdict={attempt.isSafe ? "Safe" : "Out"}
            defense={{
                label: `Roll + ${DEFENSE_LABELS[attempt.kind]}`,
                children: <RollSum die={<MiniDie die={die} size="lg" />} rating={attempt.defense} total={total} throwKey={playId} />,
            }}
            offense={runnerSide(attempt.target)}
            footer={<ThrowFooter attempt={attempt} runner={attempt.runner} />}
        />
    );
}

/** A throw the game is waiting on: who's running and what the die has to beat. On this player's
 *  throw the die takes a tap (as the next-move button rolls it too); on the other club's it's a blank. */
export function PendingRunnerRoll({ attempt, onRoll, isBusy }: {
    attempt: PendingRunnerThrow;
    onRoll?: () => void;
    isBusy?: boolean;
}) {
    const die: ReactNode = onRoll || isBusy
        ? <HandDie label="Throw" isAwaited onRoll={onRoll} isBusy={isBusy} isLabelHidden />
        : <span className="text-(--text-secondary)">?</span>;
    return (
        <RollFaceoff
            size="field"
            speed={1}
            throwKey={`pending-${attempt.runner.id}-${attempt.base}`}
            isNumberUp={false}
            defense={{ label: `Roll + ${DEFENSE_LABELS[attempt.kind]}`, children: <RollSum die={die} rating={attempt.defense} throwKey="pending" /> }}
            offense={runnerSide(attempt.target)}
            status={onRoll ? "Your throw" : "Throwing"}
            footer={<ThrowFooter attempt={attempt} runner={attempt.runner} />}
        />
    );
}

export default function SimRunnerRolls({ rolls, beatId, phase, speed = 1, plateDice = 2 }: {
    rolls?: RunnerRoll[];
    /** How many of the beat's pitch and swing dice are tossed ahead of a double play's: both in a
     *  sim, none in a game people play, where each die is thrown on its own. */
    plateDice?: number;
    /** Identifies the beat so every new one re-tosses. */
    beatId: string;
    phase: PlayPhase;
    speed?: number;
}) {
    if (!rolls?.length) return null;

    return (
        // Gapped so each face-off's verdict plate, hung off its top edge, clears the one above
        <div className="flex flex-col gap-3">
            {rolls.map((attempt, index) => (
                <RunnerRollRow
                    // Keyed on the beat too, so a new beat remounts the row and replays the whole sequence.
                    key={`${beatId}-${attempt.runner.id}-${index}`}
                    attempt={attempt}
                    index={index}
                    beatId={beatId}
                    phase={phase}
                    speed={speed}
                    plateDice={plateDice}
                />
            ))}
        </div>
    );
}
