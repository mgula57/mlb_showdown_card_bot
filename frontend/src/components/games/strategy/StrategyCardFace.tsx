/**
 * @fileoverview A strategy card's face, at two sizes:
 *  - `hand`: the whole card, as it sits in the hand tray (kind band, name, when it plays, its text);
 *  - `mini`: one line for a card on the table, beside the hitter's or pitcher's card or popping out
 *    of the scoreboard island, with the text a hover away.
 * The kind is the card's color, the way the printed cards did it: offense red, defense navy,
 * utility silver.
 */
import type { ReactNode } from "react";

import { STRATEGY_KIND_LABEL, STRATEGY_TIMING_LABEL, type StrategyCard, type StrategyKind } from "../../../domain/strategy";
import { Plate, type PlateVariant } from "../../shared/Plate";

const KIND_PLATE: Record<StrategyKind, PlateVariant> = { offense: "red", defense: "navy", utility: "ink" };

/** The left edge of a mini card, in its kind's color. */
const KIND_EDGE: Record<StrategyKind, string> = {
    offense: "border-l-(--showdown-red-fill)",
    defense: "border-l-(--showdown-blue-fill)",
    utility: "border-l-(--rule-strong)",
};

type StrategyCardFaceProps = {
    card: StrategyCard;
    size?: "hand" | "mini";
    /** Under the text on a hand card: why it can't be played now, or that it can. */
    footer?: ReactNode;
    /** A mini card's tag after the name, e.g. "In play" for one carried over from an earlier at-bat. */
    tag?: ReactNode;
    className?: string;
};

export function StrategyCardFace({ card, size = "hand", footer, tag, className = "" }: StrategyCardFaceProps) {
    if (size === "mini") {
        return (
            <div
                title={`${card.name}: ${card.text}`}
                className={`flex min-w-0 items-center gap-1.5 rounded-control border border-l-4 border-(--divider) bg-(--background-secondary) px-1.5 py-0.5 ${KIND_EDGE[card.kind]} ${className}`}
            >
                <span className="truncate font-display-upright text-[12px] uppercase leading-4 text-(--text-primary)">{card.name}</span>
                {tag}
            </div>
        );
    }

    return (
        <div className={`flex w-36 shrink-0 flex-col overflow-hidden rounded-card border border-(--divider) bg-(--background-secondary) text-left ${className}`}>
            <Plate variant={KIND_PLATE[card.kind]} size="sm" className="w-full justify-between rounded-none">
                <span>{STRATEGY_KIND_LABEL[card.kind]}</span>
                {card.staysInPlay && <span>Stays</span>}
            </Plate>
            <div className="flex flex-1 flex-col gap-1 px-2 pb-2 pt-1.5">
                <span className="font-display text-[15px] uppercase leading-4 text-(--text-primary)">{card.name}</span>
                <span className="text-[10px] font-semibold uppercase tracking-[0.06em] text-(--text-tertiary)">{STRATEGY_TIMING_LABEL[card.timing]}</span>
                <p className="text-[11px] leading-snug text-(--text-secondary)">{card.text}</p>
                {footer && <div className="mt-auto pt-1">{footer}</div>}
            </div>
        </div>
    );
}
