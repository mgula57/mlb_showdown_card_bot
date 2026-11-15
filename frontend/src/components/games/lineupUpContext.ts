/**
 * @fileoverview Who's up for each club (`lineupUp`), shared by `GameStage` with whatever it renders
 * (the box score tabs in particular), so a host's own box score tables can mark those rows without
 * each host working it out and passing it down.
 */
import { createContext } from "react";

import type { LineupUp } from "../../domain/lineup";

export const LineupUpContext = createContext<LineupUp>({});

/** How a batting line is marked: the batter at the plate, the fielding club's next hitter, or not. */
export type LineupMark = "batter" | "next" | undefined;

/** Read `LineupUpContext` once per table and pass it in for each row. */
export function lineupMarkOf({ batterId, nextUpId }: LineupUp, id: number | string | undefined): LineupMark {
    if (id == null) return undefined;
    if (String(id) === batterId) return "batter";
    if (String(id) === nextUpId) return "next";
    return undefined;
}

/** The row tint for a marked batting line. */
export const LINEUP_ROW_CLASS: Record<NonNullable<LineupMark>, string> = {
    batter: "bg-(--live)/10",
    next: "bg-(--background-tertiary)",
};
