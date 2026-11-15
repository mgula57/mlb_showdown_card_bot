/**
 * @fileoverview Where each club is in its batting order: who's at the plate, who's coming up after
 * them, and who leads off for the club in the field when it next bats. Reads the box score's
 * batting lines, so a real game and a sim answer the same way.
 */
import type { BoxscoreBatterLine, DefenseAlignment, GameView } from "./game";
import type { PlayEntry } from "./play";

/** The lineup spot (1-9) a batting line belongs to. The MLB feed numbers spots 100, 200, ... with
 *  a sub in the same spot at 101, 102; a sim numbers them 1-9 and marks subs separately. */
const spotOf = (line: BoxscoreBatterLine) =>
    line.battingOrder >= 100 ? Math.floor(line.battingOrder / 100) : line.battingOrder;

const sameId = (a: number | string | undefined, b: number | string | undefined) =>
    a != null && b != null && String(a) === String(b);

/** The lineup in batting order, each spot held by whoever is in it now (the last sub into it). */
export function lineupSpots(batting: BoxscoreBatterLine[]): BoxscoreBatterLine[] {
    const bySpot = new Map<number, BoxscoreBatterLine>();
    for (const line of batting) {
        const spot = spotOf(line);
        if (spot < 1) continue;
        const held = bySpot.get(spot);
        // Whoever's in the game wins the spot; between equals, the later (a sub) does.
        const rank = (entry: BoxscoreBatterLine) => (entry.isInLineup ? 1 : 0);
        if (!held || rank(line) > rank(held) || (rank(line) === rank(held) && line.battingOrder >= held.battingOrder)) {
            bySpot.set(spot, line);
        }
    }
    return [...bySpot.entries()].sort(([a], [b]) => a - b).map(([, line]) => line);
}

/** The hitters due after `batterId`, in order and wrapping around the lineup, up to `count`. Empty
 *  when the batter isn't in the lineup the box score knows about. */
export function hittersAfter(batting: BoxscoreBatterLine[], batterId: number | string | undefined, count: number): { line: BoxscoreBatterLine; spot: number }[] {
    const spots = lineupSpots(batting);
    const index = spots.findIndex((line) => sameId(line.id, batterId));
    if (index < 0) return [];
    return Array.from({ length: Math.min(count, spots.length - 1) }, (_, k) => {
        const line = spots[(index + 1 + k) % spots.length];
        return { line, spot: spotOf(line) };
    });
}

/** Who's up for each club: the batter at the plate, and the hitter who leads off for the club in
 *  the field when it next bats. Both unset outside a game in progress. */
export type LineupUp = {
    batterId?: string;
    nextUpId?: string;
};

/** `plays` newest first. The fielding club's next hitter is the one after the last batter it sent
 *  up, or its leadoff man before it has batted. */
export function lineupUp(game: GameView, plays: PlayEntry[]): LineupUp {
    const situation = game.situation;
    if (game.state !== "LIVE" || !situation) return {};

    const fielding = situation.isTop ? game.home : game.away;
    const spots = lineupSpots(fielding.boxscore?.batting ?? []);
    const lastPlay = plays.find((play) => play.isTop !== situation.isTop && play.batterId != null);
    const lastIndex = lastPlay ? spots.findIndex((line) => sameId(line.id, lastPlay.batterId)) : -1;
    const nextUp = !lastPlay ? spots[0] : lastIndex >= 0 ? spots[(lastIndex + 1) % spots.length] : undefined;

    return {
        batterId: situation.batter?.id != null ? String(situation.batter.id) : undefined,
        nextUpId: nextUp ? String(nextUp.id) : undefined,
    };
}

/** The defensive slot each box score position fills. A sim calls its catcher "CA", the MLB feed
 *  "C"; a player who moved lists every position he played ("LF-CF"), and the last is where he is. */
const SLOT_BY_POSITION: Record<string, keyof DefenseAlignment> = {
    C: "catcher", CA: "catcher", "1B": "first", "2B": "second", "3B": "third", SS: "shortstop",
    LF: "left", CF: "center", RF: "right",
};

/** `game` with its fielding club's alignment filled in from the box score lineup and the pitcher
 *  on the mound, when the feed doesn't send one (a sim, a live game). That's what lets the board
 *  show the defense totals and put every fielder on the field. Unchanged when there's already an
 *  alignment or no lineup to read. */
export function withLineupDefense(game: GameView): GameView {
    const situation = game.situation;
    if (!situation || situation.defense) return game;

    const fielding = situation.isTop ? game.home : game.away;
    const defense: DefenseAlignment = {};
    for (const line of lineupSpots(fielding.boxscore?.batting ?? [])) {
        const slot = SLOT_BY_POSITION[line.position.split("-").at(-1)?.trim().toUpperCase() ?? ""];
        if (slot && !defense[slot]) defense[slot] = { id: line.id, name: line.name };
    }
    if (Object.keys(defense).length === 0) return game;
    if (situation.pitcher) defense.pitcher = situation.pitcher;

    return { ...game, situation: { ...situation, defense } };
}
