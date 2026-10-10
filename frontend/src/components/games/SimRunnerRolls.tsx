/**
 * @fileoverview The dice behind a sim's baserunning tests — steal attempts (before the pitch),
 * extra-base sends (after the ball is in play) and double-play turns (on the swing) — floated
 * over the middle of the diamond. Each attempt plays out as the sim's own math:
 *
 *   1. the die tumbles beside the defense rating (arm / OF / IF),
 *   2. when it lands, the two fold together into one total that counts up from the defense,
 *   3. on the result beat the total squares off against the runner's speed — the comparator snaps
 *      in (">" out, "≤" safe), the winning side flares and the losing side shakes and dims.
 *
 * All motion runs off the die's own clock (`useDieToss`) and is divided by playback speed; at high
 * speed or with reduced motion every step simply shows its final state.
 */
import { useEffect, useState, type CSSProperties, type ReactNode } from "react";

import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import type { RunnerRoll } from "../../domain/timeline";
import type { PlayPhase } from "../../hooks/useGamePlayback";
import { useDieToss } from "../../hooks/useDieToss";
import FieldMarker from "./FieldMarker";
import RollDie from "./RollDie";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

const BASE_NAMES: Record<number, string> = { 1: "1st", 2: "2nd", 3: "3rd", 4: "Home" };
const DEFENSE_LABELS: Record<RunnerRoll["kind"], string> = { steal: "Arm", advance: "OF", double_play: "IF" };
/** How long the fold + count-up takes at 1x — short enough to finish inside the "pitch" beat. */
const FOLD_MS = 280;
/** Out = the defense won; safe = the runner did. */
const OUT_ACCENT = "var(--red)";
const SAFE_ACCENT = "var(--green)";

const titleFor = (attempt: RunnerRoll): string =>
    attempt.kind === "double_play"
        ? "Double Play"
        : `${attempt.kind === "steal" ? "Steal" : "Extra Base"} · ${BASE_NAMES[attempt.base + 1] ?? ""}`;

/** Counts from `from` up to `to` over `durationMs`, starting when the component mounts. */
function useCountUp(from: number, to: number, durationMs: number, isStatic: boolean): number {
    const [value, setValue] = useState(isStatic ? to : from);
    useEffect(() => {
        if (isStatic) return;
        let frame = 0;
        const start = performance.now();
        const tick = (now: number) => {
            const t = Math.min(1, (now - start) / durationMs);
            // Ease-out so the last few numbers land with a little weight.
            setValue(Math.round(from + (to - from) * (1 - Math.pow(1 - t, 3))));
            if (t < 1) frame = requestAnimationFrame(tick);
        };
        frame = requestAnimationFrame(tick);
        return () => cancelAnimationFrame(frame);
    }, [from, to, durationMs, isStatic]);
    return isStatic ? to : value;
}

function StatChip({ label, children, className = "", style }: { label: string; children: ReactNode; className?: string; style?: CSSProperties }) {
    return (
        <span className={`relative flex flex-col items-center gap-0.5 rounded-md bg-(--background-primary)/60 px-1.5 py-1 ${className}`} style={style}>
            <span className="text-[7px] font-bold uppercase leading-none tracking-wider text-(--tertiary)">{label}</span>
            <span className="text-xs font-black leading-none tabular-nums text-(--text-primary)">{children}</span>
        </span>
    );
}

/** The folded total — mounts when the die lands, so its pop and count-up play exactly once. */
function RollTotal({ from, to, isStatic, speed, verdictClass, accent }: {
    from: number; to: number; isStatic: boolean; speed: number; verdictClass: string; accent?: string;
}) {
    const value = useCountUp(from, to, FOLD_MS / speed, isStatic);
    return (
        <span className={isStatic ? "" : "roll-total-pop"}>
            <StatChip label="Total" className={`min-w-8 ring-1 ring-(--live)/50 ${verdictClass}`} style={accent ? { "--roll-accent": accent } as CSSProperties : undefined}>
                {value}
                {!isStatic && <span aria-hidden className="roll-total-ring" />}
            </StatChip>
        </span>
    );
}

function RunnerRollRow({ attempt, index, beatId, phase, speed, cardMap, onCardSelect, isLoadingCards }: {
    attempt: RunnerRoll;
    index: number;
    beatId: string;
    phase: PlayPhase;
    speed: number;
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
}) {
    const playId = `${beatId}-${index}`;
    // A DP turn rides the swing beat, so its die waits for the pitch and swing dice to land first.
    const staggerIndex = index + (attempt.kind === "double_play" ? 2 : 0);
    const { isTumbling, isStatic } = useDieToss({ playId, phase, speed, staggerIndex });
    // The outcome is a spoiler until the dice have landed; the result beat onward reveals it.
    const isRevealed = phase !== "pitch";
    const hasOdds = attempt.defense != null && attempt.target != null;
    const isFolded = hasOdds && !isTumbling;
    const total = (attempt.defense ?? 0) + attempt.roll;
    const accent = attempt.isSafe ? SAFE_ACCENT : OUT_ACCENT;
    const animate = (className: string) => (isStatic ? "" : className);

    // Who won the face-off, once it's revealed: the total (defense) on an out, the runner on safe.
    const totalVerdict = !isRevealed ? "" : attempt.isSafe ? animate("roll-clash-lose") || "opacity-55" : animate("roll-clash-win");
    const runnerVerdict = !isRevealed ? "" : attempt.isSafe ? animate("roll-clash-win") : animate("roll-clash-lose") || "opacity-55";

    return (
        <div className="flex flex-col gap-1.5 px-2.5 py-2" style={{ "--roll-speed": speed } as CSSProperties}>
            {/* Header: what's being attempted, and the verdict once the die has landed. */}
            <div className="flex items-center justify-between gap-3">
                <span className="text-[9px] font-bold uppercase leading-none tracking-wider text-(--text-secondary)">{titleFor(attempt)}</span>
                <span
                    className={`
                        rounded px-1.5 py-0.5 text-[9px] font-black uppercase leading-none tracking-wider text-white
                        ${attempt.isSafe ? "bg-(--green)" : "bg-(--red)"}
                        ${isRevealed ? animate("result-pop") : "invisible"}
                    `}
                >
                    {attempt.isSafe ? "Safe" : "Out"}
                </span>
            </div>

            {/* The test: defense + die = total, vs the runner's speed (base bonus included, shown on their card). */}
            <div className="flex items-center gap-1.5">
                {hasOdds && (
                    <>
                        <StatChip label={DEFENSE_LABELS[attempt.kind]} className={isFolded ? animate("roll-fold-left") || "opacity-45" : ""}>
                            {attempt.defense}
                        </StatChip>
                        <span className={`text-xs font-black leading-none text-(--tertiary) ${isFolded ? "opacity-45" : ""}`}>+</span>
                    </>
                )}
                <span className={isFolded ? animate("roll-fold-right") || "opacity-45" : ""}>
                    <RollDie value={attempt.roll} label="Roll" playId={playId} phase={phase} speed={speed} staggerIndex={staggerIndex} />
                </span>

                {hasOdds && (
                    <>
                        <span className={`text-xs font-black leading-none text-(--tertiary) ${isFolded ? "" : "invisible"}`}>=</span>
                        {/* Holds the total's width while the die is in the air, so nothing shifts when it lands. */}
                        {isFolded ? (
                            <RollTotal from={attempt.defense!} to={total} isStatic={isStatic} speed={speed} verdictClass={totalVerdict} accent={isRevealed && !attempt.isSafe ? accent : undefined} />
                        ) : (
                            <span className="invisible"><StatChip label="Total" className="min-w-8">{total}</StatChip></span>
                        )}
                    </>
                )}

                {/* "vs" until the reveal, then the comparator that decided it: out when total > speed. */}
                <span
                    key={isRevealed ? "cmp" : "vs"}
                    className={`min-w-4 text-center leading-none ${isRevealed && hasOdds ? `text-sm font-black ${animate("result-pop")}` : "text-[9px] font-bold uppercase tracking-wider text-(--tertiary)"}`}
                    style={isRevealed && hasOdds ? { color: accent } : undefined}
                >
                    {isRevealed && hasOdds ? (attempt.isSafe ? "≤" : ">") : "vs"}
                </span>

                <span className={`rounded-lg ${runnerVerdict}`} style={isRevealed && attempt.isSafe ? { "--roll-accent": accent } as CSSProperties : undefined}>
                    <FieldMarker
                        player={attempt.runner}
                        role="H"
                        cardMap={cardMap}
                        onCardSelect={onCardSelect}
                        isLoadingCards={isLoadingCards}
                        tone="offense"
                        statBadge={hasOdds ? { label: "Spd", value: attempt.target! } : undefined}
                    />
                </span>
            </div>
        </div>
    );
}

export default function SimRunnerRolls({ rolls, beatId, phase, speed = 1, cardMap, onCardSelect, isLoadingCards }: {
    rolls?: RunnerRoll[];
    /** Identifies the beat so every new one re-tosses. */
    beatId: string;
    phase: PlayPhase;
    speed?: number;
    cardMap: CardMap;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
}) {
    if (!rolls?.length) return null;

    return (
        <div className="flex flex-col divide-y divide-(--divider) rounded-lg border border-(--divider) bg-(--background-secondary)/80 shadow-lg backdrop-blur-sm">
            {rolls.map((attempt, index) => (
                <RunnerRollRow
                    // Keyed on the beat too, so a new beat remounts the row and replays the whole sequence.
                    key={`${beatId}-${attempt.runner.id}-${index}`}
                    attempt={attempt}
                    index={index}
                    beatId={beatId}
                    phase={phase}
                    speed={speed}
                    cardMap={cardMap}
                    onCardSelect={onCardSelect}
                    isLoadingCards={isLoadingCards}
                />
            ))}
        </div>
    );
}
