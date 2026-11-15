/**
 * @fileoverview Who's in the current plate appearance and where each side stands: their cards,
 * their lines so far and the Showdown advantage split. Shared by the wide board's corner cards and
 * the narrow board's row.
 */
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import type { GameView, PlayerRef } from "../../domain/game";
import type { AdvantageSide } from "../../domain/play";
import { resolveCardKey } from "../../domain/players";

type CardMap = Record<string, ShowdownBotCardAPIResponse>;

/**
 * Share of d20 rolls that leave the pitcher with the advantage. A Showdown plate appearance
 * gives the hitter the advantage when `control + roll <= onbase`, so the pitcher keeps it on
 * `20 - (onbase - control)` of the twenty faces.
 */
const pitcherAdvantagePct = (control: number, onbase: number): number => {
    const favorable = 20 - (onbase - control);
    return Math.round((Math.max(0, Math.min(20, favorable)) / 20) * 100);
};

export type MatchupSideData = {
    label: string;
    player?: PlayerRef;
    response?: ShowdownBotCardAPIResponse;
    /** The player's box-score line so far, e.g. "2-for-4" or "5.0 IP, 3 ER". */
    summary?: string;
    /** Share of pitch rolls this side wins. Unknown until both cards load. */
    advantagePct?: number;
};

/** Both sides of the current plate appearance, or null with no one up. In replay mode
 *  (`hideStatlines`) the box-score lines are frozen at the game's current or final totals, so
 *  showing them at an earlier cursor would spoil what's still to come. */
export function resolveMatchup(game: GameView, cardMap: CardMap, hideStatlines: boolean): Record<AdvantageSide, MatchupSideData> | null {
    const situation = game.situation;
    if (!situation) return null;

    const { batter, pitcher } = situation;
    const batterResponse = cardMap[resolveCardKey(batter?.id, "H") ?? ""];
    const pitcherResponse = cardMap[resolveCardKey(pitcher?.id, "P") ?? ""];

    const battingSide = situation.isTop ? game.away : game.home;
    const fieldingSide = situation.isTop ? game.home : game.away;

    const control = pitcherResponse?.card?.chart.command;
    const onbase = batterResponse?.card?.chart.command;
    const pitcherAdvantage = control != null && onbase != null ? pitcherAdvantagePct(control, onbase) : undefined;

    return {
        pitcher: {
            label: "Pitching",
            player: pitcher,
            response: pitcherResponse,
            summary: hideStatlines ? undefined : fieldingSide.boxscore?.pitching.find((line) => line.id === pitcher?.id)?.summary,
            advantagePct: pitcherAdvantage,
        },
        hitter: {
            label: "At Bat",
            player: batter,
            response: batterResponse,
            summary: hideStatlines ? undefined : battingSide.boxscore?.batting.find((line) => line.id === batter?.id)?.summary,
            advantagePct: pitcherAdvantage != null ? 100 - pitcherAdvantage : undefined,
        },
    };
}
