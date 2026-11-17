/**
 * @fileoverview Copies of the plate appearance's dice, set where the eye goes to read what a roll
 * decided, so it never has to leave that spot to watch the roll itself: beside the commands for the
 * pitch (`PitchCompare`), on the winner's chart for the swing (`CardImageWithChart`'s and
 * `CardChart`'s die), on the center panel's meters and steps, and on the last play's tab.
 *
 * Every copy runs off the one die `GameStage` keeps for each roll (`BoardDie`): a sim's toss
 * (`useDieToss`) or a live game's hand throw (`useHandToss`), the same clock the die on the field
 * runs on. So the copies scramble while it's in the air and all land, number up, on the same
 * frame. Only the field's die makes the throw; a copy scrambles and pops in place.
 */
import type { CSSProperties, ReactNode } from "react";

import { D20Face } from "../team_builder/sim/SimDiceRoll";
import type { AdvantageSide } from "../../domain/play";
import { useScrambledFace } from "../../hooks/useScrambledFace";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { Plate } from "../shared/Plate";
import { isDieShown, restingDie, type BoardDie } from "./boardDie";

/** `card` sizes off the card it sits on (the nearest `@container`, its width), so it reads at any
 *  card size: never smaller than `md`. */
const MINI_DIE_SIZE = {
    xs: "h-4 w-4",
    sm: "h-5 w-5",
    md: "h-7 w-7",
    card: "h-[max(2.25rem,16cqw)] w-[max(2.25rem,16cqw)]",
} as const;

/** A small copy of a die: scrambling in place while the die is in the air, then popping as its
 *  number comes up. */
export function MiniDie({ die, size = "sm", className = "" }: { die: BoardDie; size?: keyof typeof MINI_DIE_SIZE; className?: string }) {
    const scrambled = useScrambledFace(die.isTumbling, die.speed);
    const isShown = isDieShown(die);
    return (
        <span
            aria-label={isShown ? `Rolled ${die.value}` : "Rolling"}
            className={`relative inline-block shrink-0 align-middle ${MINI_DIE_SIZE[size]} ${className}`}
        >
            <span
                // A new key as the number comes up, so the landing pops once per throw
                key={isShown ? `${die.key}|shown` : die.key}
                className={`absolute inset-0 drop-shadow-[0_1px_0_rgb(0_0_0/0.25)] ${isShown ? "mini-die-land" : die.isTumbling ? "mini-die-tumble" : ""}`}
            >
                {/* On a card the number has to read at a glance, so it's set large over the facets */}
                <D20Face value={isShown ? die.value : scrambled} accent="var(--die-body)" ink="var(--die-ink)" numeral={size === "card" ? "bold" : "face"} />
            </span>
        </span>
    );
}

const ADVANTAGE_PLATE = { pitcher: "navy", hitter: "red" } as const;
const ADVANTAGE_LABEL = { pitcher: "Pitcher", hitter: "Hitter" } as const;
/** The winning side of the pitch, filled in its brand color with `--roll-accent` for its flare. */
const ADVANTAGE_FILL = {
    pitcher: "bg-(--showdown-blue-fill) text-white [--roll-accent:var(--showdown-blue-fill)]",
    hitter: "bg-(--showdown-red-fill) text-white [--roll-accent:var(--showdown-red-fill)]",
} as const;

/** One side of the pitch: its numbers over a micro label. Once the winner is in it fills (or, on
 *  the losing side, shakes and dims). */
function PitchSide({ side, label, verdictKey, advantage, children }: {
    side: AdvantageSide;
    label: string;
    verdictKey: string;
    advantage?: AdvantageSide;
    children: ReactNode;
}) {
    const verdictClass = advantage == null ? "" : advantage === side ? `${ADVANTAGE_FILL[side]} roll-clash-win` : "roll-clash-lose";
    return (
        <span className={side === "pitcher" ? "pitch-compare-in-left" : "pitch-compare-in-right"}>
            <span
                // A new key as the winner comes in, so its flare plays once
                key={advantage ? verdictKey : "open"}
                className={`flex h-full flex-col items-center justify-center gap-[max(0.125rem,0.75cqw)] rounded-plate px-[max(0.375rem,2cqw)] py-[max(0.125rem,1cqw)] transition-colors ${verdictClass}`}
            >
                <span className="flex items-center gap-[max(0.25rem,1.25cqw)]">{children}</span>
                {/* design-ok: card-stat micro label, sized off the card it sits on */}
                <span className={`text-[clamp(7px,2.75cqw,10px)] font-sans font-bold uppercase tracking-wider ${advantage === side ? "" : "text-(--text-secondary)"}`}>{label}</span>
            </span>
        </span>
    );
}

/** The pitch as the rules read it, laid over a card zoomed to its command: the die plus the
 *  pitcher's Control squared off against the hitter's On-Base across a VS. The total counts in once
 *  the number is up, and holds there on its own (`PITCH_READ_BEAT_MS`, timed by `GameStage`) before
 *  the winner shows: its side fills in its color, the other dims, and the verdict hangs off the top.
 *  When the engine nudged the roll (fatigue, a platoon edge), so the sum alone wouldn't reach the
 *  same winner, the sum is left out rather than shown wrong. */
export function PitchCompare({ die, control, onbase, advantage }: {
    die: BoardDie;
    control?: number;
    onbase?: number;
    advantage?: AdvantageSide;
}) {
    const isShown = isDieShown(die);
    const total = isShown && control != null ? die.value + control : undefined;
    const isSumTrue = total == null || onbase == null || advantage == null || (total > onbase) === (advantage === "pitcher");
    const verdictKey = `${die.key}|${advantage}`;
    return (
        // Sized off the card it's laid over (the nearest `@container`), so it reads at any card size
        <div
            className="relative flex items-stretch rounded-card border border-(--rule-strong) bg-(--background-primary) p-[max(0.125rem,0.75cqw)] font-display-black text-[clamp(15px,8cqw,30px)] tabular-nums leading-none text-(--text-primary) shadow-overlay"
            style={{ "--roll-speed": die.speed } as CSSProperties}
        >
            {advantage && (
                <Plate
                    key={verdictKey}
                    size="sm"
                    textSize="text-[clamp(9px,3.5cqw,13px)]"
                    variant={ADVANTAGE_PLATE[advantage]}
                    className="advantage-badge-pop absolute left-1/2 top-0 z-10 -translate-x-1/2 -translate-y-1/2 whitespace-nowrap"
                >
                    {ADVANTAGE_LABEL[advantage]} Advantage
                </Plate>
            )}
            <PitchSide side="pitcher" label="Roll + Control" verdictKey={verdictKey} advantage={advantage}>
                <MiniDie die={die} size="card" />
                {control != null && <span>+{control}</span>}
                {total != null && isSumTrue && <span key={die.key} className="roll-total-pop">={total}</span>}
            </PitchSide>
            <span className="flex items-center px-[max(0.25rem,1.5cqw)]">
                {/* Slams in with the panel, and again as the number comes up */}
                <span key={isShown ? `${die.key}|shown` : die.key} className="pitch-compare-vs text-[0.85em] text-(--showdown-red)">VS</span>
            </span>
            <PitchSide side="hitter" label="On-Base" verdictKey={verdictKey} advantage={advantage}>
                <span>{onbase ?? "–"}</span>
            </PitchSide>
        </div>
    );
}

/** The plate appearance's two rolls in a line ("14 Hitter · 8 1B"), each number on its own small
 *  die, for the last play's tab. */
export function PlayRolls({ playId, pitchRoll, advantage, swingRoll, swingResult }: {
    playId: string;
    pitchRoll: number;
    advantage?: AdvantageSide;
    swingRoll: number;
    swingResult: string;
}) {
    return (
        <span className={`${CAPS_LABEL_CLASS} flex items-center justify-center gap-1 text-(--text-primary)`}>
            <MiniDie die={restingDie(`${playId}|pitch`, pitchRoll)} size="xs" />
            {advantage && ADVANTAGE_LABEL[advantage]}
            <span aria-hidden className="px-0.5">·</span>
            <MiniDie die={restingDie(`${playId}|swing`, swingRoll)} size="xs" />
            {swingResult.toUpperCase()}
        </span>
    );
}
