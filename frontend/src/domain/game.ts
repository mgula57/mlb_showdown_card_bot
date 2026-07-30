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

export type LiveSituation = {
    inning: number;
    isTop: boolean;
    inningLabel: string;
    outs: number;
    balls?: number;
    strikes?: number;
    bases: { first: boolean; second: boolean; third: boolean };
    batter?: PlayerRef;
    pitcher?: PlayerRef;
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
