/**
 * @fileoverview One roll's test as the rules read it: a die plus the fielding side's rating, squared
 * off across a VS against the batting side's number. The pitch (`PitchCompare`: Control against
 * On-Base) and every throw on a runner (`SimRunnerRolls`: arm, outfield or infield against Speed)
 * are the same face-off, so they share this one look.
 *
 * The fielding side is always on the left in navy and the batting side on the right in red, as
 * the pitcher and the hitter are. The two sides slide in to meet at the VS, which slams down between
 * them (and again as the die's number comes up). Once the winner is in, its side fills in its color
 * and flares, the other shakes and dims, and the verdict hangs off the top edge in a plate.
 */
import type { CSSProperties, ReactNode } from "react";

import { Plate } from "../shared/Plate";

/** Left is the fielding club (the pitcher, the defense throwing), right the batting club. */
export type FaceoffSide = "defense" | "offense";

const SIDE_FILL: Record<FaceoffSide, string> = {
    defense: "bg-(--showdown-blue-fill) text-white [--roll-accent:var(--showdown-blue-fill)]",
    offense: "bg-(--showdown-red-fill) text-white [--roll-accent:var(--showdown-red-fill)]",
};
const SIDE_PLATE = { defense: "navy", offense: "red" } as const;

/** `card` sizes off the card it's laid over (the nearest `@container`), so it reads at any card
 *  size; `field` floats over the field at one size. */
const SIZES = {
    card: {
        root: "p-[max(0.125rem,0.75cqw)] text-[clamp(15px,8cqw,30px)]",
        side: "gap-[max(0.125rem,0.75cqw)] px-[max(0.375rem,2cqw)] py-[max(0.125rem,1cqw)]",
        row: "gap-[max(0.25rem,1.25cqw)]",
        label: "text-[clamp(7px,2.75cqw,10px)]",
        vs: "px-[max(0.25rem,1.5cqw)]",
        verdict: "text-[clamp(9px,3.5cqw,13px)]",
        footer: "mx-[max(0.25rem,1cqw)] mt-[max(0.125rem,0.5cqw)] px-[max(0.375rem,2cqw)] pt-[max(0.25rem,1cqw)] pb-[max(0.125rem,0.75cqw)] text-[clamp(8px,3cqw,11px)]",
    },
    field: {
        root: "p-1 text-[22px]",
        side: "gap-1 px-3 py-1.5",
        row: "gap-1.5",
        label: "text-[8px]",
        vs: "px-2.5",
        verdict: "text-[10px]",
        footer: "mx-1 mt-0.5 px-2 pt-1.5 pb-1 text-[10px]",
    },
} as const;

export type FaceoffSideContent = {
    /** The micro label under the side's numbers ("Roll + Control", "Speed"). */
    label: string;
    /** The numbers: the die plus the rating and their total, or the number it has to beat. */
    children: ReactNode;
};

/** One side's numbers over its label. Fills once it has won, shakes and dims once it has lost. */
function FaceoffHalf({ side, content, winner, verdictKey, sizes }: {
    side: FaceoffSide;
    content: FaceoffSideContent;
    winner?: FaceoffSide;
    verdictKey: string;
    sizes: (typeof SIZES)[keyof typeof SIZES];
}) {
    const verdictClass = winner == null ? "" : winner === side ? `${SIDE_FILL[side]} roll-clash-win` : "roll-clash-lose";
    return (
        <span className={side === "defense" ? "roll-faceoff-in-left" : "roll-faceoff-in-right"}>
            <span
                // A new key as the winner comes in, so its flare plays once
                key={winner ? verdictKey : "open"}
                className={`flex h-full flex-col items-center justify-center rounded-plate ${sizes.side} ${verdictClass}`}
            >
                <span className={`flex items-center ${sizes.row}`}>{content.children}</span>
                {/* design-ok: card-stat micro label */}
                <span className={`${sizes.label} whitespace-nowrap font-sans font-bold uppercase tracking-wider ${winner === side ? "" : "text-(--text-secondary)"}`}>{content.label}</span>
            </span>
        </span>
    );
}

export function RollFaceoff({ size, speed, throwKey, isNumberUp, defense, offense, winner, verdict, status, footer }: {
    size: keyof typeof SIZES;
    /** Playback speed: every animation here divides by it, as the phase beats do. */
    speed: number;
    /** One throw. A new one replays the VS slam and the verdict. */
    throwKey: string;
    /** The die's number is up: the VS slams again. */
    isNumberUp: boolean;
    defense: FaceoffSideContent;
    offense: FaceoffSideContent;
    /** Who won, once it's revealed. */
    winner?: FaceoffSide;
    /** The verdict in the plate hung off the top edge ("Pitcher Advantage", "Out"). */
    verdict?: string;
    /** Before there's a verdict, a quiet note in its place on the top edge ("Your throw"). */
    status?: string;
    /** A line under the face-off: what's being tested and who (a throw on a runner). */
    footer?: ReactNode;
}) {
    const sizes = SIZES[size];
    const verdictKey = `${throwKey}|${winner}`;
    return (
        <div
            className={`relative flex flex-col rounded-card border border-(--rule-strong) bg-(--background-primary)/80 backdrop-blur-sm font-display-black tabular-nums leading-none text-(--text-primary) shadow-overlay ${sizes.root}`}
            style={{ "--roll-speed": speed } as CSSProperties}
        >
            {winner && verdict && (
                <Plate
                    key={verdictKey}
                    size="sm"
                    textSize={sizes.verdict}
                    variant={SIDE_PLATE[winner]}
                    className="advantage-badge-pop absolute left-1/2 top-0 z-10 -translate-x-1/2 -translate-y-1/2 whitespace-nowrap"
                >
                    {verdict}
                </Plate>
            )}
            {!winner && status && (
                <Plate size="sm" textSize={sizes.verdict} variant="ink" className="absolute left-1/2 top-0 z-10 -translate-x-1/2 -translate-y-1/2 whitespace-nowrap">
                    {status}
                </Plate>
            )}
            <div className="flex items-stretch justify-center">
                <FaceoffHalf side="defense" content={defense} winner={winner} verdictKey={verdictKey} sizes={sizes} />
                <span className={`flex items-center ${sizes.vs}`}>
                    <span key={isNumberUp ? `${throwKey}|shown` : throwKey} className="roll-faceoff-vs text-[0.85em] text-(--showdown-red)">VS</span>
                </span>
                <FaceoffHalf side="offense" content={offense} winner={winner} verdictKey={verdictKey} sizes={sizes} />
            </div>
            {footer && (
                <div className={`flex items-center justify-center gap-1.5 whitespace-nowrap border-t border-(--divider) font-sans text-(--text-secondary) ${sizes.footer}`}>
                    {footer}
                </div>
            )}
        </div>
    );
}
