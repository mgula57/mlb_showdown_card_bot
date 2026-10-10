/**
 * @fileoverview The dice behind a sim's runner-only beats — steal attempts (before the pitch) and
 * extra-base sends (after the ball is in play) — docked in the field's bottom-left corner, where
 * the plate appearance's own dice used to live. Each attempt reads top to bottom as the sim's own
 * test: the defense, plus the die, versus the runner's card (with the speed being tested pinned
 * inside it). SAFE / OUT is revealed in the header once the die has landed.
 */
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import type { RunnerRoll } from "../../domain/timeline";
import type { PlayPhase } from "../../hooks/useGamePlayback";
import FieldMarker from "./FieldMarker";
import RollDie from "./RollDie";

const BASE_NAMES: Record<number, string> = { 1: "1st", 2: "2nd", 3: "3rd", 4: "Home" };

export default function SimRunnerRolls({ rolls, beatId, phase, speed, cardMap, onCardSelect, isLoadingCards }: {
    rolls?: RunnerRoll[];
    /** Identifies the beat so every new one re-tosses. */
    beatId: string;
    phase: PlayPhase;
    speed?: number;
    cardMap: Record<string, ShowdownBotCardAPIResponse>;
    onCardSelect?: (card: ShowdownBotCardAPIResponse) => void;
    isLoadingCards?: boolean;
}) {
    if (!rolls?.length) return null;

    // The outcome is a spoiler until the dice have landed; the result beat onward reveals it.
    const isRevealed = phase !== "pitch";

    return (
        <div className="flex flex-col divide-y divide-(--divider) rounded-lg border border-(--divider) bg-(--background-secondary)/80 shadow-lg backdrop-blur-sm">
            {rolls.map((attempt, index) => {
                const hasOdds = attempt.defense != null && attempt.target != null;
                const title = `${attempt.kind === "steal" ? "Steal" : "Extra Base"} · ${BASE_NAMES[attempt.base + 1] ?? ""}`;
                return (
                    <div key={`${attempt.runner.id}-${index}`} className="flex flex-col gap-1.5 px-2.5 py-2">
                        {/* Header: what's being attempted, and the verdict once the die has landed. */}
                        <div className="flex items-center justify-between gap-3">
                            <span className="text-[9px] font-bold uppercase leading-none tracking-wider text-(--text-secondary)">{title}</span>
                            <span
                                className={`
                                    rounded px-1.5 py-0.5 text-[9px] font-black uppercase leading-none tracking-wider text-white
                                    ${attempt.isSafe ? "bg-(--green)" : "bg-(--red)"}
                                    ${isRevealed ? "" : "invisible"}
                                `}
                            >
                                {attempt.isSafe ? "Safe" : "Out"}
                            </span>
                        </div>

                        {/* The test: defense + die vs the runner's speed (base bonus included, shown on their card). */}
                        <div className="flex items-center gap-2">
                            {hasOdds && (
                                <>
                                    <span className="flex flex-col items-center gap-0.5 rounded-md bg-(--background-primary)/60 px-1.5 py-1">
                                        <span className="text-[7px] font-bold uppercase leading-none tracking-wider text-(--tertiary)">
                                            {attempt.kind === "steal" ? "Arm" : "OF"}
                                        </span>
                                        <span className="text-xs font-black leading-none text-(--text-primary)">{attempt.defense}</span>
                                    </span>
                                    <span className="text-xs font-black leading-none text-(--tertiary)">+</span>
                                </>
                            )}
                            <RollDie
                                value={attempt.roll}
                                label="Roll"
                                playId={`${beatId}-${index}`}
                                phase={phase}
                                speed={speed}
                                staggerIndex={index}
                            />
                            <span className="text-[9px] font-bold uppercase leading-none tracking-wider text-(--tertiary)">vs</span>
                            <FieldMarker
                                player={attempt.runner}
                                role="H"
                                cardMap={cardMap}
                                onCardSelect={onCardSelect}
                                isLoadingCards={isLoadingCards}
                                tone="offense"
                                statBadge={hasOdds ? { label: "Spd", value: attempt.target! } : undefined}
                            />
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
