/**
 * @fileoverview Canonical game view model shared by real MLB games (schedule + box score) and,
 * eventually, simulated games. Replaces the ad hoc bridging that used to happen in
 * `GameItem.normalizeGame()` between `GameScheduled` and `GameBoxscoreDetail` — those two API
 * shapes, plus a future sim shape, all map into this single `GameView` at the adapter boundary.
 */
import type { TeamIdentity, TeamRecordLine } from "./team";

export type GameState = "PREVIEW" | "LIVE" | "FINAL" | "POSTPONED";
export type GameSource = "MLB" | "SIM";

export type PlayerRef = {
    id?: number | string;
    name: string;
};

export type BoxscoreBatterLine = {
    id: number | string;
    name: string;
    position: string;
    battingOrder: number;
    isSubstitute: boolean;
    isInLineup: boolean;
    atBats: number;
    runs: number;
    hits: number;
    doubles?: number;
    triples?: number;
    homeRuns: number;
    rbi: number;
    baseOnBalls: number;
    strikeOuts: number;
    stolenBases: number;
    caughtStealing?: number;
    groundIntoDoublePlay?: number;
    summary?: string;
};

export type BoxscorePitcherLine = {
    id: number | string;
    name: string;
    position?: string;
    order?: number;
    isSubstitute?: boolean;
    inningsPitched: string;
    hits: number;
    runs: number;
    earnedRuns: number;
    baseOnBalls: number;
    strikeOuts: number;
    homeRuns: number;
    battersFaced?: number;
    era?: number | string;
    summary?: string;
};

export type TeamBoxscore = {
    team: TeamIdentity;
    batting: BoxscoreBatterLine[];
    pitching: BoxscorePitcherLine[];
};

export type GameSide = {
    team: TeamIdentity;
    score?: number;
    record?: TeamRecordLine;
    isWinner?: boolean;
    probablePitcher?: PlayerRef;
    /** Present only on detail-level views (box score / game detail). */
    boxscore?: TeamBoxscore;
};

/** The nine defensive slots, keyed the way the MLB linescore reports them. Every slot is
 * optional — a defense isn't set before first pitch, and slots go briefly missing mid-substitution. */
export type DefenseAlignment = {
    pitcher?: PlayerRef;
    catcher?: PlayerRef;
    first?: PlayerRef;
    second?: PlayerRef;
    third?: PlayerRef;
    shortstop?: PlayerRef;
    left?: PlayerRef;
    center?: PlayerRef;
    right?: PlayerRef;
};

export type LiveSituation = {
    inning: number;
    isTop: boolean;
    inningLabel: string;
    outs: number;
    /** MLB only — the sim resolves a plate appearance in one pitch roll + one swing roll,
     * so it has no ball/strike count to report. */
    balls?: number;
    strikes?: number;
    /** Runner on each base, or null when the base is empty — occupancy derives as `!!bases.first`.
     * A runner whose identity isn't known (the sim tracks occupancy only) is the sentinel
     * `{ name: "" }`; render those as a plain marker rather than a named chip. */
    bases: { first: PlayerRef | null; second: PlayerRef | null; third: PlayerRef | null };
    batter?: PlayerRef;
    pitcher?: PlayerRef;
    onDeck?: PlayerRef;
    inHole?: PlayerRef;
    defense?: DefenseAlignment;
};

export type InningLine = {
    num: number;
    ordinalNum: string;
    awayRuns: number | null;
    homeRuns: number | null;
};

export type LinescoreTotals = {
    runs: number;
    hits: number;
    errors: number;
    leftOnBase?: number;
};

export type Linescore = {
    innings: InningLine[];
    scheduledInnings: number;
    away: LinescoreTotals;
    home: LinescoreTotals;
};

export type GameDecisions = {
    winner?: PlayerRef;
    loser?: PlayerRef;
    save?: PlayerRef;
};

export type GameView = {
    id: number | string;
    source: GameSource;
    date?: string;
    seriesLabel?: string;
    state: GameState;
    detailedState: string;
    away: GameSide;
    home: GameSide;
    linescore?: Linescore;
    situation?: LiveSituation;
    decisions?: GameDecisions;
    lastPlay?: string;
};
