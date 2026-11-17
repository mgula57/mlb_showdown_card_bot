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
import type { ReactNode } from "react";

import { D20Face } from "../team_builder/sim/SimDiceRoll";
import type { AdvantageSide } from "../../domain/play";
import { useScrambledFace } from "../../hooks/useScrambledFace";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { isDieShown, restingDie, type BoardDie } from "./boardDie";
import { RollFaceoff } from "./RollFaceoff";

/** `card` sizes off the card it sits on (the nearest `@container`, its width), so it reads at any
 *  card size: never smaller than `md`. */
const MINI_DIE_SIZE = {
    xs: "h-4 w-4",
    sm: "h-5 w-5",
    md: "h-7 w-7",
    lg: "h-9 w-9",
    xl: "h-12 w-12",
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
                <D20Face value={isShown ? die.value : scrambled} accent="var(--die-body)" ink="var(--die-ink)" numeral={size === "card" || size === "lg" || size === "xl" ? "bold" : "face"} />
            </span>
        </span>
    );
}

const ADVANTAGE_LABEL = { pitcher: "Pitcher", hitter: "Hitter" } as const;
const FACEOFF_SIDE = { pitcher: "defense", hitter: "offense" } as const;

/** The pitch as the rules read it, laid over a card zoomed to its command: the die plus the
 *  pitcher's Control against the hitter's On-Base (`RollFaceoff`). The total counts in once the
 *  number is up, and holds there on its own (`PITCH_READ_BEAT_MS`, timed by `GameStage`) before the
 *  winner shows. When the engine nudged the roll (fatigue, a platoon edge), so the sum alone
 *  wouldn't reach the same winner, the sum is left out rather than shown wrong. */
export function PitchCompare({ die, control, onbase, advantage }: {
    die: BoardDie;
    control?: number;
    onbase?: number;
    advantage?: AdvantageSide;
}) {
    const isShown = isDieShown(die);
    const total = isShown && control != null ? die.value + control : undefined;
    const isSumTrue = total == null || onbase == null || advantage == null || (total > onbase) === (advantage === "pitcher");
    return (
        <RollFaceoff
            size="card"
            speed={die.speed}
            throwKey={die.key}
            isNumberUp={isShown}
            winner={advantage && FACEOFF_SIDE[advantage]}
            verdict={advantage && `${ADVANTAGE_LABEL[advantage]} Advantage`}
            defense={{
                label: "Roll + Control",
                children: <RollSum die={<MiniDie die={die} size="card" />} rating={control} total={isSumTrue ? total : undefined} throwKey={die.key} />,
            }}
            offense={{ label: "On-Base", children: <span>{onbase ?? "–"}</span> }}
        />
    );
}

/** The die plus a rating, and their total popping in once the number is up: the fielding side of
 *  a `RollFaceoff`. */
export function RollSum({ die, rating, total, throwKey }: { die: ReactNode; rating?: number; total?: number; throwKey: string }) {
    return (
        <>
            {die}
            {rating != null && <span>+{rating}</span>}
            {total != null && <span key={throwKey} className="roll-total-pop">={total}</span>}
        </>
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
