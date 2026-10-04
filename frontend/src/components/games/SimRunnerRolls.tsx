/**
 * @fileoverview The dice behind a sim's runner-only beats — steal attempts (before the pitch) and
 * extra-base sends (after the ball is in play) — docked in the field's bottom-left corner, where
 * the plate appearance's own dice used to live. Each attempt reads top to bottom as the sim's own
 * test: the defense, plus the die, versus the runner's speed. The runner is shown as their full
 * card; SAFE / OUT is revealed once the die has landed.
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
        <div className="flex items-start gap-4 rounded-md border border-(--divider) bg-(--background-secondary)/30 px-3 py-2 backdrop-blur-sm">
            {rolls.map((attempt, index) => {
                const hasOdds = attempt.defense != null && attempt.target != null;
                return (
                    <div key={`${attempt.runner.id}-${index}`} className="flex flex-col items-center gap-2">
                        {/* Row 1: defense  +  die. Out when the total beats the runner's speed below. */}
                        <div className="flex items-center gap-3">
                            {hasOdds && (
                                <span className="flex flex-col items-center gap-0.5 rounded-md border border-(--divider) bg-(--background-primary)/60 px-2 py-1 shadow-sm">
                                    <span className="text-[8px] font-bold uppercase leading-none tracking-wider text-(--tertiary)">
                                        {attempt.kind === "steal" ? "Arm" : "OF"}
                                    </span>
                                    <span className="text-sm font-black leading-none text-(--primary)">{attempt.defense}</span>
                                </span>
                            )}
                            {hasOdds && <span className="text-sm font-black leading-none text-(--secondary)">+</span>}
                            <RollDie
                                value={attempt.roll}
                                label={`${attempt.kind === "steal" ? "Steal" : "Extra"} ${BASE_NAMES[attempt.base + 1] ?? ""}`.trim()}
                                playId={`${beatId}-${index}`}
                                phase={phase}
                                speed={speed}
                                staggerIndex={index}
                            />
                        </div>

                        {hasOdds && <span className="text-[9px] font-bold uppercase leading-none tracking-wider text-(--tertiary)">vs</span>}

                        {/* Row 2: the runner's card, and the speed (with base bonus) being tested. */}
                        <div className="flex items-center gap-2">
                            <FieldMarker
                                player={attempt.runner}
                                role="H"
                                cardMap={cardMap}
                                onCardSelect={onCardSelect}
                                isLoadingCards={isLoadingCards}
                                tone="offense"
                            />
                            {hasOdds && <span className="whitespace-nowrap text-[11px] font-black leading-none text-(--primary)">SPD {attempt.target}</span>}
                        </div>

                        <span className={`text-[9px] font-black uppercase leading-none tracking-wider ${isRevealed ? (attempt.isSafe ? "text-(--green)" : "text-(--red)") : "invisible"}`}>
                            {attempt.isSafe ? "Safe" : "Out"}
                        </span>
                    </div>
                );
            })}
        </div>
    );
}
