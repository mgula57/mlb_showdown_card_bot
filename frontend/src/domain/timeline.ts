/**
 * @fileoverview A `GameTimeline` is an ordered sequence of `GameFrame`s — one per play, plus
 * synthetic pre-game / half-inning-break / final frames — each holding a complete `GameView` as
 * of that moment. Playback is a cursor over this array: every existing panel already renders a
 * `GameView`, so feeding it a different frame's view is the entire mechanism.
 *
 * `domain/adapters/fromMlbApi.ts` and `domain/adapters/fromSim.ts` build a `GameTimeline` each
 * (`fromMlbTimeline`, `fromSimTimeline`). This file holds only the source-agnostic pieces they
 * both need: the frame/transition types, the runner-identity diff, and the per-frame linescore
 * accumulator (reconstructing per-inning line score requires walking the plays in order — there
 * is no other source for it).
 */
import type { GameSource, GameView, InningLine, Linescore, PlayerRef } from "./game";
import type { PlayEntry } from "./play";
import { ordinal } from "../functions/formatters";

export type BaseSlot = "first" | "second" | "third";
/** Where a runner card can physically sit on the field. `plate` = the batter's box (pre-contact);
 *  `home` = the plate as a destination (a run scoring), which then fades out. */
export type RunnerSpot = BaseSlot | "plate" | "home";

export type RunnerSnapshot = {
    bases: Record<BaseSlot, PlayerRef | null>;
    /** Crossed the plate on the transition INTO this snapshot. */
    scored: PlayerRef[];
    /** Retired on the bases (or at the plate) on the transition INTO this snapshot. */
    retired: PlayerRef[];
    /** Who is standing in at the plate as of this frame — the NEXT play's batter, per the
     *  batter/pitcher offset described on `GameFrame`. */
    batter?: PlayerRef;
};

export type RunnerMoveKind = "advance" | "score" | "out" | "arrive";

export type RunnerMove = {
    key: string;               // runnerKey() — stable across frames
    player: PlayerRef;
    from: RunnerSpot | null;   // null = entered from off-field (extra-innings ghost runner, takeover seed)
    to: RunnerSpot | null;     // null = removed (out)
    kind: RunnerMoveKind;
};

export type TransitionSeverity = "quiet" | "notable" | "big";

export type FrameTransition = {
    fromIndex: number;
    toIndex: number;
    moves: RunnerMove[];
    runsScored: number;
    outsRecorded: number;
    isHalfInningChange: boolean;
    severity: TransitionSeverity;
};

export type FramePhaseKind = "PRE_GAME" | "PLAY" | "HALF_INNING_BREAK" | "AT_BAT" | "FINAL";

export type GameFrame = {
    /** Stable across polls/rebuilds. MLB: `mlb-${atBatIndex}`; sim: `sim-${logIndex}`; synthetic
     *  breaks: `${prevId}-break`. Playback tracks its cursor by this id, not by array index, since
     *  every poll rebuilds the frames array. */
    id: string;
    index: number;
    kind: FramePhaseKind;
    source: GameSource;
    /** The complete view as of the END of this frame — what every existing panel renders as-is. */
    view: GameView;
    /** The play this frame resolved. Absent on PRE_GAME / HALF_INNING_BREAK / AT_BAT. */
    play?: PlayEntry;
    runners: RunnerSnapshot;
    /** Precomputed at fold time — playback never recomputes it. Absent on frame 0. */
    transition?: FrameTransition;
};

export type GameTimeline = {
    gameId: number | string;
    source: GameSource;
    frames: GameFrame[];
    /** Index of the newest frame — the live edge. */
    liveIndex: number;
    /** False for a legacy stored sim with occupancy-only bases — the field degrades to fades
     *  instead of attempting (impossible, without identity) to slide a runner between bases. */
    hasRunnerIdentity: boolean;
    /** Data the timeline can't reconstruct per-frame and therefore shows as-of-now on every frame. */
    frozen: { boxscore: boolean; defense: boolean };
};

// ------------------------------------------------------------------
// RUNNER IDENTITY + MOVEMENT
// ------------------------------------------------------------------

/** A runner's identity key, stable across frames when they're an identified player, and stable
 *  only within a single base slot when they aren't (`hasRunnerIdentity === false`) — which is
 *  exactly the degradation the field needs: an anonymous occupant at first is "the same marker"
 *  only for as long as *something* occupies first, never tracked across a move to second. */
export const runnerKey = (player: PlayerRef | null | undefined, slot: RunnerSpot): string => {
    const id = player?.id;
    if (id != null && id !== "") return `p:${id}`;
    return `anon:${slot}`;
};

const idKey = (player: PlayerRef): string | null => (player.id != null && player.id !== "" ? String(player.id) : null);

const BASE_SLOTS: BaseSlot[] = ["first", "second", "third"];

const baseEntries = (bases: Record<BaseSlot, PlayerRef | null>): [BaseSlot, PlayerRef][] =>
    BASE_SLOTS
        .map((slot): [BaseSlot, PlayerRef | null] => [slot, bases[slot]])
        .filter((entry): entry is [BaseSlot, PlayerRef] => entry[1] != null);

/**
 * Assigns each departed base runner to `scored` or `retired`, closest-to-home first, up to
 * `runsToAssign`. This is a heuristic: the play data available today reports how many runs
 * scored on a play, not which specific runners crossed — a runner on third is far more likely to
 * be the one who scored than a runner on first, and this is right for the overwhelming majority
 * of plays. Wrong only on the rare "one runner scores while another is thrown out at the plate on
 * the same play" — exact per-runner movement (Phase 6) would remove the guesswork entirely.
 */
export const allocateScoredAndRetired = (
    departed: { slot: BaseSlot; player: PlayerRef }[],
    runsToAssign: number,
): { scored: PlayerRef[]; retired: PlayerRef[] } => {
    const closestToHomeFirst = { third: 0, second: 1, first: 2 } as const;
    const sorted = [...departed].sort((a, b) => closestToHomeFirst[a.slot] - closestToHomeFirst[b.slot]);
    const cut = Math.max(0, Math.min(sorted.length, runsToAssign));
    return {
        scored: sorted.slice(0, cut).map((d) => d.player),
        retired: sorted.slice(cut).map((d) => d.player),
    };
};

/**
 * Builds the runner movements between two consecutive base states. Both adapters call this with
 * the same shape — MLB resolves `scored`/`retired` via `allocateScoredAndRetired` against a score
 * delta, the sim resolves them exactly from the backend's per-play runner log — so the field only
 * ever has to understand one movement vocabulary regardless of source.
 *
 * The batter is passed separately, not folded into `prevBases`, because the batter/pitcher offset
 * (a frame's `situation.batter` is the NEXT play's batter) means the person about to move from the
 * plate isn't "on base" in `prevBases` at all — they're standing at the plate in the CURRENT
 * frame, about to resolve into whatever `nextBases`/`scored`/`retired` says they became. Keying
 * their plate occupant with the same `runnerKey` they'll have as a runner is what makes a single
 * or a walk render as one DOM node sliding from home to first, rather than two markers swapping.
 */
export const buildRunnerMoves = (params: {
    prevBases: Record<BaseSlot, PlayerRef | null>;
    nextBases: Record<BaseSlot, PlayerRef | null>;
    scored: PlayerRef[];
    retired: PlayerRef[];
    batter?: PlayerRef;
}): RunnerMove[] => {
    const { prevBases, nextBases, scored, retired, batter } = params;
    const moves: RunnerMove[] = [];

    const prevEntries = baseEntries(prevBases);
    const nextEntries = baseEntries(nextBases);
    const nextByKey = new Map(nextEntries.map(([slot, player]) => [runnerKey(player, slot), { slot, player }] as const));
    const scoredIds = new Set(scored.map(idKey).filter((k): k is string => k != null));
    const retiredIds = new Set(retired.map(idKey).filter((k): k is string => k != null));
    const consumedNextKeys = new Set<string>();

    // Runners who were on base and are no longer there — advanced, scored, or retired.
    for (const [slot, player] of prevEntries) {
        const key = runnerKey(player, slot);
        const next = nextByKey.get(key);
        if (next) {
            consumedNextKeys.add(key);
            if (next.slot !== slot) moves.push({ key, player, from: slot, to: next.slot, kind: "advance" });
            continue;
        }
        const id = idKey(player);
        if (id != null && scoredIds.has(id)) {
            moves.push({ key, player, from: slot, to: "home", kind: "score" });
        } else if (id != null && retiredIds.has(id)) {
            moves.push({ key, player, from: slot, to: null, kind: "out" });
        } else {
            // No positive classification (anonymous runner, or a data gap) — treat as retired so
            // the marker fades rather than lingering on screen forever un-animated.
            moves.push({ key, player, from: slot, to: null, kind: "out" });
        }
    }

    // The batter's own plate appearance.
    if (batter) {
        const key = runnerKey(batter, "plate");
        const arrived = nextByKey.get(key);
        if (arrived) {
            consumedNextKeys.add(key);
            moves.push({ key, player: batter, from: "plate", to: arrived.slot, kind: "arrive" });
        } else {
            const id = idKey(batter);
            if (id != null && scoredIds.has(id)) {
                moves.push({ key, player: batter, from: "plate", to: "home", kind: "score" });
            } else if (id != null && retiredIds.has(id)) {
                moves.push({ key, player: batter, from: "plate", to: null, kind: "out" });
            }
            // else: no resolvable outcome for the batter (shouldn't happen with consistent data)
            // — leave them mounted at the plate rather than guessing.
        }
    }

    // Anyone newly on base who wasn't already there and isn't the batter — an extra-innings ghost
    // runner, or the seed state of a takeover. `consumedNextKeys` already covers every key that
    // matched a prev-base or batter occupant, so whatever's left here has no prior occupant.
    for (const [slot, player] of nextEntries) {
        const key = runnerKey(player, slot);
        if (consumedNextKeys.has(key)) continue;
        moves.push({ key, player, from: null, to: slot, kind: "arrive" });
    }

    return moves;
};

/** Stranded-runner removals for a synthesized `HALF_INNING_BREAK` frame — the bases clear without
 *  anyone advancing, scoring, or being individually retired; they just leave. */
export const strandedRunnerMoves = (bases: Record<BaseSlot, PlayerRef | null>): RunnerMove[] =>
    baseEntries(bases).map(([slot, player]) => ({ key: runnerKey(player, slot), player, from: slot, to: null, kind: "out" as const }));

export const severityFor = (params: {
    moves: RunnerMove[];
    runsScored: number;
    isHomeRun?: boolean;
    isWalkOff?: boolean;
    leadChanged?: boolean;
}): TransitionSeverity => {
    const { moves, runsScored, isHomeRun, isWalkOff, leadChanged } = params;
    if (isWalkOff || isHomeRun || runsScored >= 2 || leadChanged) return "big";
    if (runsScored > 0 || moves.some((m) => m.kind === "out" || m.kind === "score")) return "notable";
    return "quiet";
};

// ------------------------------------------------------------------
// LINESCORE RECONSTRUCTION
// ------------------------------------------------------------------

/**
 * Folds plays into a per-inning line score one play at a time, so every frame can carry a
 * spoiler-free linescore (future innings simply haven't been `apply`d yet). Shared by both
 * adapters — reconstructing "runs this half" from cumulative scores is identical either source.
 */
export class LinescoreAccumulator {
    private readonly scheduledInnings: number;
    private readonly finalErrors: { away: number; home: number };
    private readonly innings: InningLine[] = [];
    private awayHits = 0;
    private homeHits = 0;
    private lastAwayScore = 0;
    private lastHomeScore = 0;

    constructor(scheduledInnings: number, finalErrors: { away: number; home: number }) {
        this.scheduledInnings = scheduledInnings;
        this.finalErrors = finalErrors;
    }

    private ensureInning(num: number): InningLine {
        let inning = this.innings.find((i) => i.num === num);
        if (!inning) {
            inning = { num, ordinalNum: ordinal(num), awayRuns: null, homeRuns: null };
            this.innings.push(inning);
        }
        return inning;
    }

    /** Marks a half-inning as begun so it reads `0` (not blank) even before its first play. */
    startHalf(inningNum: number, isTop: boolean): void {
        const inning = this.ensureInning(inningNum);
        if (isTop) inning.awayRuns = inning.awayRuns ?? 0;
        else inning.homeRuns = inning.homeRuns ?? 0;
    }

    /** Folds one play in. `cumulativeAwayScore`/`cumulativeHomeScore` are the game totals AFTER
     *  this play — the per-half delta is derived from the previous call's totals. */
    apply(inningNum: number, isTop: boolean, cumulativeAwayScore: number, cumulativeHomeScore: number, isHit: boolean): void {
        const inning = this.ensureInning(inningNum);
        const runsThisPlay = isTop
            ? cumulativeAwayScore - this.lastAwayScore
            : cumulativeHomeScore - this.lastHomeScore;
        if (isTop) inning.awayRuns = (inning.awayRuns ?? 0) + Math.max(0, runsThisPlay);
        else inning.homeRuns = (inning.homeRuns ?? 0) + Math.max(0, runsThisPlay);

        this.lastAwayScore = cumulativeAwayScore;
        this.lastHomeScore = cumulativeHomeScore;
        if (isHit) { if (isTop) this.awayHits += 1; else this.homeHits += 1; }
    }

    /** An independent point-in-time copy — callers must NOT get a live view into the accumulator,
     *  or every earlier frame's linescore would silently mutate as later plays are folded in. */
    snapshot(): Linescore {
        return {
            innings: [...this.innings].sort((a, b) => a.num - b.num).map((inning) => ({ ...inning })),
            scheduledInnings: this.scheduledInnings,
            away: { runs: this.lastAwayScore, hits: this.awayHits, errors: this.finalErrors.away },
            home: { runs: this.lastHomeScore, hits: this.homeHits, errors: this.finalErrors.home },
        };
    }
}

// ------------------------------------------------------------------
// SHARED FRAME HELPERS
// ------------------------------------------------------------------

export const EMPTY_BASES: Record<BaseSlot, PlayerRef | null> = { first: null, second: null, third: null };
