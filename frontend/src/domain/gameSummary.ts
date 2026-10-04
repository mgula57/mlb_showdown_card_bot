/**
 * @fileoverview Post-game summary derivations off the canonical `GameView` — currently the
 * Player of the Game. Reads only the normalized box score lines, so a real MLB final and a
 * Showdown sim pick their standout the same way.
 */
import type { BoxscoreBatterLine, BoxscorePitcherLine, GameView } from "./game";

export type PlayerOfTheGame = {
    side: "away" | "home";
    role: "H" | "P";
    line: BoxscoreBatterLine | BoxscorePitcherLine;
    score: number;
};

/** "5.2" → 17. Innings pitched are written as full innings plus a thirds digit. */
const outsFromInningsPitched = (ip: string): number => {
    const [full, thirds] = ip.split(".");
    return (Number(full) || 0) * 3 + (Number(thirds) || 0);
};

/** Bases-and-production score: total bases, runs created around them, and a little for the walk
 *  and the steal. A two-homer, four-RBI night lands ~14; a 2-for-4 with a solo shot ~8. */
const batterScore = (b: BoxscoreBatterLine): number => {
    const extraBases = (b.doubles ?? 0) + 2 * (b.triples ?? 0) + 3 * b.homeRuns;
    return b.hits + extraBases + b.runs + b.rbi + 0.5 * b.baseOnBalls + 0.5 * b.stolenBases;
};

/** Same scale as `batterScore`: a nine-inning, eight-strikeout shutout lands ~15; seven innings of
 *  one-run ball ~8. Runs and baserunners pull it down, so a long but leaky start won't win it. */
const pitcherScore = (p: BoxscorePitcherLine): number =>
    0.5 * outsFromInningsPitched(p.inningsPitched)
    + 0.5 * p.strikeOuts
    - 2 * p.earnedRuns
    - 0.5 * p.hits
    - 0.5 * p.baseOnBalls;

/**
 * The winning club's top performer — the award goes to the side that won, as it does on a
 * broadcast. Returns undefined until the game is final with a winner and box score lines.
 */
export const playerOfTheGame = (game: GameView): PlayerOfTheGame | undefined => {
    if (game.state !== "FINAL") return undefined;
    const side: "away" | "home" | undefined = game.away.isWinner ? "away" : game.home.isWinner ? "home" : undefined;
    if (!side) return undefined;
    const box = game[side].boxscore;
    if (!box) return undefined;

    const candidates: PlayerOfTheGame[] = [
        ...box.batting.map((line) => ({ side, role: "H" as const, line, score: batterScore(line) })),
        ...box.pitching.map((line) => ({ side, role: "P" as const, line, score: pitcherScore(line) })),
    ];
    return candidates.reduce<PlayerOfTheGame | undefined>(
        (best, c) => (!best || c.score > best.score ? c : best),
        undefined,
    );
};
