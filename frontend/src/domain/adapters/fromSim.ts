/**
 * @fileoverview Adapter from the simulation engine's `GameResult` JSON
 * (`mlb_showdown_bot/core/simulation/models.py`, emitted via Pydantic's `model_dump_json`) into
 * the canonical `GameView`. Field names mirror the Python models exactly (snake_case), since
 * that's the wire format.
 */
import type { BoxscoreBatterLine, BoxscorePitcherLine, GameSide, GameView, Linescore, LiveSituation, PlayerRef, TeamBoxscore } from "../game";
import type { PlayEntry } from "../play";
import type { TeamIdentity } from "../team";
import { ordinal } from "../../functions/formatters";
import type { SimGameResult } from "../../api/simGame";
import {
    buildRunnerMoves,
    EMPTY_BASES,
    LinescoreAccumulator,
    severityFor,
    strandedRunnerMoves,
    type BaseSlot,
    type FramePhaseKind,
    type GameFrame,
    type GameTimeline,
    type RetiredRunner,
    type RunnerSpot,
} from "../timeline";

export type SimTeamIdentityJson = {
    abbreviation: string;
    name: string;
    primary_color?: string | null;
    secondary_color?: string | null;
    league?: string | null;
};

export type SimInningLineScoreJson = {
    num: number;
    ordinal_num: string;
    away_runs?: number | null;
    home_runs?: number | null;
};

export type SimTeamLineScoreTotalsJson = {
    runs: number;
    hits: number;
    errors: number;
    left_on_base?: number;
};

export type SimLineScoreResultJson = {
    innings: SimInningLineScoreJson[];
    scheduled_innings: number;
    away: SimTeamLineScoreTotalsJson;
    home: SimTeamLineScoreTotalsJson;
};

export type SimBoxScoreBattingStatsJson = {
    at_bats: number;
    runs: number;
    hits: number;
    doubles: number;
    triples: number;
    home_runs: number;
    rbi: number;
    base_on_balls: number;
    strike_outs: number;
    stolen_bases: number;
    caught_stealing: number;
    ground_into_double_play: number;
    plate_appearances: number;
    summary: string;
};

export type SimBoxScoreBatterJson = {
    id: string;
    name: string;
    position: string;
    batting_order: number;
    is_substitute: boolean;
    is_in_lineup: boolean;
    stats: SimBoxScoreBattingStatsJson;
};

export type SimBoxScorePitchingStatsJson = {
    innings_pitched: string;
    outs: number;
    hits: number;
    runs: number;
    earned_runs: number;
    base_on_balls: number;
    strike_outs: number;
    home_runs: number;
    batters_faced: number;
    era: number;
    summary: string;
};

export type SimBoxScorePitcherJson = {
    id: string;
    name: string;
    position: string;
    order: number;
    is_substitute: boolean;
    entered_in_inning?: number | null;
    stats: SimBoxScorePitchingStatsJson;
};

export type SimTeamBoxScoreJson = {
    team: SimTeamIdentityJson;
    batting: SimBoxScoreBatterJson[];
    pitching: SimBoxScorePitcherJson[];
};

/** One plate appearance, mirroring `GameLogEntry`. Only emitted when the sim runs with
 * `include_game_logs` — `GameResult.log` is empty otherwise. */
export type SimGameLogEntryJson = {
    inning: number;
    is_top: boolean;
    outs: number;
    /** Base occupancy, ordered THIRD, SECOND, FIRST — `Runners.base_squares_str` walks [3,2,1]. */
    bases: string;
    away_score: number;
    home_score: number;
    pitcher: string;
    hitter: string;
    /** Whatever id space the SimTeam was built with — a builder team's card_id, or an MLB player
     * id (as a string) for a real-game sim. Empty for logs produced before ids were recorded. */
    pitcher_id?: string;
    hitter_id?: string;
    pitch_roll: number;
    pitch_result: string;
    swing_roll: number;
    swing_result: string;
    /** Runs driven in on this plate appearance. */
    runs_scored?: number;
    /** Narration in the MLB feed's voice, built by the engine's `PlateAppearanceNarrator`.
     * Absent on logs produced before narration existed, which fall back to the roll labels. */
    event?: string;
    description?: string;
    detail?: string;
    summary: string;
    /** Post-play base state BY IDENTITY, plus who scored/was retired on this play — mirrors
     * `bases` above (which is occupancy-only, no identity) but lets a replay slide a named card
     * from first to second instead of fading one occupancy square out and another in. Absent on
     * logs written before this existed; `fromSimTimeline` falls back to `parseSimBases`'s
     * occupancy-only reading when so, and the field degrades to fades instead of sliding. */
    bases_detail?: SimRunnerRefJson[];
    scored?: SimRunnerRefJson[];
    retired?: SimRunnerRefJson[];
    /** Post-phase base snapshots that let a replay animate baserunning APART from the swing —
     *  the steal (before the pitch) and the extra-base send (after the ball is in play) each get
     *  their own beat. Same shape as `bases_detail`. Each is present only when that phase actually
     *  moved someone; absent on logs written before the per-beat split, where `fromSimTimeline`
     *  falls back to a single beat per plate appearance.
     *   - `bases_after_steal` — after pre-pitch steal attempts resolve
     *   - `bases_after_swing`  — after the ball-in-play advancement + any DP, before extra-base sends */
    bases_after_steal?: SimRunnerRefJson[] | null;
    bases_after_swing?: SimRunnerRefJson[] | null;
};

/** `reason` is set only on `scored` / `retired` and tells the replay which beat of the plate
 *  appearance the event belongs to — "steal" | "advance" | "forced" for a retired runner,
 *  "swing" | "advance" for one who scored. Empty on pre-split logs. */
export type SimRunnerRefJson = { id: string; name: string; base: number; reason?: string };

export type SimGameResultJson = {
    index: number;
    date: string;
    home_team: string;
    away_team: string;
    home_score: number;
    away_score: number;
    winner?: string | null;
    log: SimGameLogEntryJson[];
    home_team_identity?: SimTeamIdentityJson | null;
    away_team_identity?: SimTeamIdentityJson | null;
    linescore?: SimLineScoreResultJson | null;
    home_box_score?: SimTeamBoxScoreJson | null;
    away_box_score?: SimTeamBoxScoreJson | null;
    innings_played: number;
    is_extra_innings: boolean;
};

/** `Result` enum values (`core/simulation/result.py`) as play-log badge labels. Only a fallback —
 * the engine now sends its own `event`, worded the way the MLB feed words it. */
const SIM_EVENT_LABELS: Record<string, string> = {
    pu: "Popout", so: "Strikeout", gb: "Groundout", fb: "Flyout", bb: "Walk",
    "1b": "Single", "1b+": "Single+", "2b": "Double", "3b": "Triple", hr: "Home Run",
    out: "Out", safe: "Safe",
};

/** The sim reports base state as occupancy, not identity, so occupied bases become the
 * `{ name: "" }` sentinel that `LiveSituation.bases` documents. */
const parseSimBases = (bases: string): LiveSituation["bases"] => {
    const occupied = (index: number) => (bases[index] === "■" ? { name: "" } : null);
    return { third: occupied(0), second: occupied(1), first: occupied(2) };
};

export const fromSimTeamIdentity = (identity: SimTeamIdentityJson): TeamIdentity => ({
    key: identity.abbreviation,
    abbreviation: identity.abbreviation,
    name: identity.name || identity.abbreviation,
    primaryColor: identity.primary_color ?? undefined,
    secondaryColor: identity.secondary_color ?? undefined,
});

export const fallbackIdentity = (abbreviation: string): TeamIdentity => ({
    key: abbreviation,
    abbreviation,
    name: abbreviation,
});

const toSimBoxscore = (box: SimTeamBoxScoreJson): TeamBoxscore => ({
    team: fromSimTeamIdentity(box.team),
    batting: box.batting.map((batter): BoxscoreBatterLine => ({
        id: batter.id,
        name: batter.name,
        position: batter.position,
        battingOrder: batter.batting_order,
        isSubstitute: batter.is_substitute,
        isInLineup: batter.is_in_lineup,
        atBats: batter.stats.at_bats,
        runs: batter.stats.runs,
        hits: batter.stats.hits,
        doubles: batter.stats.doubles,
        triples: batter.stats.triples,
        homeRuns: batter.stats.home_runs,
        rbi: batter.stats.rbi,
        baseOnBalls: batter.stats.base_on_balls,
        strikeOuts: batter.stats.strike_outs,
        stolenBases: batter.stats.stolen_bases,
        caughtStealing: batter.stats.caught_stealing,
        groundIntoDoublePlay: batter.stats.ground_into_double_play,
        summary: batter.stats.summary,
    })),
    pitching: box.pitching.map((pitcher): BoxscorePitcherLine => ({
        id: pitcher.id,
        name: pitcher.name,
        position: pitcher.position,
        order: pitcher.order,
        isSubstitute: pitcher.is_substitute,
        inningsPitched: pitcher.stats.innings_pitched,
        hits: pitcher.stats.hits,
        runs: pitcher.stats.runs,
        earnedRuns: pitcher.stats.earned_runs,
        baseOnBalls: pitcher.stats.base_on_balls,
        strikeOuts: pitcher.stats.strike_outs,
        homeRuns: pitcher.stats.home_runs,
        battersFaced: pitcher.stats.batters_faced,
        era: pitcher.stats.era,
        summary: pitcher.stats.summary,
    })),
});

/**
 * Sim game log to play entries, newest-first to match `fromGamePlays`. Populates `roll` — the
 * sim's two d20s stand in for the pitch count a real game reports.
 */
export const fromSimPlays = (log: SimGameLogEntryJson[]): PlayEntry[] =>
    log
        .map((entry, index): PlayEntry => ({
            // Sim entries have no stable identifier of their own, so the index stands in. Prefixed
            // because a taken-over game merges these with MLB plays, whose ids are atBatIndexes
            // from the same small integer range.
            id: `sim-${index}`,
            inning: entry.inning,
            isTop: entry.is_top,
            batterId: entry.hitter_id || undefined,
            batterName: entry.hitter,
            pitcherId: entry.pitcher_id || undefined,
            pitcherName: entry.pitcher,
            event: entry.event || SIM_EVENT_LABELS[entry.swing_result] || entry.swing_result.toUpperCase(),
            description: entry.description || entry.summary || entry.detail || "",
            isScoringPlay: (entry.runs_scored ?? 0) > 0,
            outs: entry.outs,
            source: "SIM",
            roll: {
                pitchRoll: entry.pitch_roll,
                pitchResult: entry.pitch_result,
                swingRoll: entry.swing_roll,
                swingResult: entry.swing_result,
            },
        }))
        .reverse();

export const fromSimGame = (game: SimGameResultJson): GameView => {
    const linescore: Linescore | undefined = game.linescore
        ? {
            innings: game.linescore.innings.map((inning) => ({
                num: inning.num,
                ordinalNum: inning.ordinal_num,
                awayRuns: inning.away_runs ?? null,
                homeRuns: inning.home_runs ?? null,
            })),
            scheduledInnings: game.linescore.scheduled_innings,
            away: {
                runs: game.linescore.away.runs,
                hits: game.linescore.away.hits,
                errors: game.linescore.away.errors,
                leftOnBase: game.linescore.away.left_on_base,
            },
            home: {
                runs: game.linescore.home.runs,
                hits: game.linescore.home.hits,
                errors: game.linescore.home.errors,
                leftOnBase: game.linescore.home.left_on_base,
            },
        }
        : undefined;

    const toSide = (team: string, identity: SimTeamIdentityJson | null | undefined, score: number, boxScore: SimTeamBoxScoreJson | null | undefined): GameSide => ({
        team: identity ? fromSimTeamIdentity(identity) : fallbackIdentity(team),
        score,
        isWinner: game.winner === team,
        boxscore: boxScore ? toSimBoxscore(boxScore) : undefined,
    });

    // The last logged plate appearance is the game's final state. Balls/strikes and the defensive
    // alignment stay undefined — the sim models neither — which is what the field and matchup
    // components degrade against.
    const lastEntry = game.log.length > 0 ? game.log[game.log.length - 1] : undefined;
    const situation: LiveSituation | undefined = lastEntry
        ? {
            inning: lastEntry.inning,
            isTop: lastEntry.is_top,
            inningLabel: ordinal(lastEntry.inning),
            outs: lastEntry.outs,
            bases: parseSimBases(lastEntry.bases),
            batter: { name: lastEntry.hitter },
            pitcher: { name: lastEntry.pitcher },
        }
        : undefined;

    return {
        id: game.index,
        source: "SIM",
        date: game.date,
        state: "FINAL",
        detailedState: "Final",
        away: toSide(game.away_team, game.away_team_identity, game.away_score, game.away_box_score),
        home: toSide(game.home_team, game.home_team_identity, game.home_score, game.home_box_score),
        linescore,
        situation,
        lastPlay: lastEntry?.description || lastEntry?.summary,
    };
};

// ------------------------------------------------------------------
// TIMELINE (playback) — one GameFrame per plate appearance.
// ------------------------------------------------------------------

const baseSlotFor = (base: number): BaseSlot | undefined =>
    base === 1 ? "first" : base === 2 ? "second" : base === 3 ? "third" : undefined;

/** Same as `baseSlotFor` but also covers `base: 4` ("home") — a retired runner's `base` is "the
 *  base they were retired trying to reach" (per `RunnerRef`'s doc in the backend), which can be
 *  the plate itself (thrown out at home), unlike `bases_detail`'s occupancy (never 4 — a runner
 *  who reached home scored, and isn't "on base" anymore). */
const runnerSpotFor = (base: number): RunnerSpot => (base >= 4 ? "home" : baseSlotFor(base) ?? "home");

const toPlayerRef = (r: SimRunnerRefJson): PlayerRef => ({ id: r.id, name: r.name });
const toRetiredRunner = (r: SimRunnerRefJson): RetiredRunner => ({ player: toPlayerRef(r), attemptedSpot: runnerSpotFor(r.base) });

/** A `bases_detail`-shaped list of `RunnerRef`s → the by-slot base map the timeline threads
 *  through `buildRunnerMoves`. Shared by the final post-PA state and the intermediate
 *  post-steal / post-swing snapshots. */
const mapDetailBases = (refs: SimRunnerRefJson[]): Record<BaseSlot, PlayerRef | null> => {
    const bases: Record<BaseSlot, PlayerRef | null> = { ...EMPTY_BASES };
    for (const r of refs) {
        const slot = baseSlotFor(r.base);
        if (slot) bases[slot] = toPlayerRef(r);
    }
    return bases;
};

/**
 * Reconstructs a frame-by-frame `GameTimeline` from a sim's `GameResult` log. Each `GameLogEntry`
 * already IS a post-play state snapshot (`Game.simulate` in `game.py` appends it after mutating
 * `inning.runners`/`inning.outs`), so this reads the same shape `fromSimGame` does — it just
 * folds every entry instead of only the last one.
 *
 * A takeover's pre-simulation real plays (`result.real_plays`) are NOT re-animated frame by frame
 * — the user already watched those live, or can read them in the play-by-play log's "Took over
 * here" section. Only the simulated portion gets full playback; it's seeded from
 * `setup.start_state` so the handoff doesn't invent arrivals for runners already on base.
 */
export const fromSimTimeline = (result: SimGameResult): GameTimeline => {
    const view = fromSimGame(result.game);
    const log = result.game.log ?? [];
    const startState = result.setup.start_state;

    const scheduledInnings = view.linescore?.scheduledInnings ?? 9;
    const finalErrors = { away: view.linescore?.away.errors ?? 0, home: view.linescore?.home.errors ?? 0 };
    const accumulator = new LinescoreAccumulator(scheduledInnings, finalErrors);
    const baseView = (overrides: Partial<GameView>): GameView => ({ ...view, isReplay: true, ...overrides });

    const frames: GameFrame[] = [];
    let prevBases: Record<BaseSlot, PlayerRef | null> = EMPTY_BASES;
    let inning = 1;
    let isTop = true;
    let hasRunnerIdentity = true;

    if (startState) {
        inning = startState.inning;
        isTop = startState.is_top;
        const seeded: Record<BaseSlot, PlayerRef | null> = { ...EMPTY_BASES };
        for (const runner of startState.runners.runners) {
            const slot = baseSlotFor(runner.base);
            if (slot) seeded[slot] = { id: runner.id, name: runner.name };
        }
        prevBases = seeded;
    }
    accumulator.startHalf(inning, isTop);

    // FRAME 0 — the sim's starting point (game start, or the takeover resume point).
    {
        const firstEntry = log[0];
        const batter: PlayerRef | undefined = firstEntry ? { id: firstEntry.hitter_id || undefined, name: firstEntry.hitter } : undefined;
        const pitcher: PlayerRef | undefined = firstEntry ? { id: firstEntry.pitcher_id || undefined, name: firstEntry.pitcher } : undefined;
        frames.push({
            id: "sim-pregame",
            index: 0,
            kind: log.length === 0 ? "FINAL" : "PRE_GAME",
            source: "SIM",
            runners: { bases: prevBases, scored: [], retired: [], batter },
            view: baseView({
                state: "LIVE",
                away: { ...view.away, score: startState?.away.runs_scored ?? 0, isWinner: undefined },
                home: { ...view.home, score: startState?.home.runs_scored ?? 0, isWinner: undefined },
                linescore: accumulator.snapshot(),
                situation: {
                    inning, isTop, inningLabel: ordinal(inning), outs: startState?.outs ?? 0,
                    bases: prevBases, batter, pitcher,
                },
            }),
        });
    }

    // Outs in the current half-inning as each plate appearance begins — the prior PA's ending
    // count, reset to 0 on a half-inning flip. Lets a pre-pitch steal beat show the right out
    // total rather than the post-PA one.
    let carryOuts = startState?.outs ?? 0;

    for (let i = 0; i < log.length; i++) {
        const entry = log[i];
        const nextEntry = log[i + 1];
        inning = entry.inning;
        isTop = entry.is_top;

        const entryBatter: PlayerRef = { id: entry.hitter_id || undefined, name: entry.hitter };
        const entryPitcher: PlayerRef = { id: entry.pitcher_id || undefined, name: entry.pitcher };
        const nextBatter: PlayerRef | undefined = nextEntry ? { id: nextEntry.hitter_id || undefined, name: nextEntry.hitter } : undefined;
        const nextPitcher: PlayerRef | undefined = nextEntry ? { id: nextEntry.pitcher_id || undefined, name: nextEntry.pitcher } : entryPitcher;

        const runsScored = entry.runs_scored ?? 0;
        const swingResult = entry.swing_result.toLowerCase();
        const isHomeRun = swingResult === "hr";
        const isHit = ["1b", "1b+", "2b", "3b", "hr"].includes(swingResult);
        const swingIsEmpty = swingResult === "na"; // a pure steal/CS that ended the half-inning
        const isHalfInningChange = !!nextEntry && (nextEntry.inning !== inning || nextEntry.is_top !== isTop);
        const isLastEntry = i === log.length - 1;
        const outsStart = carryOuts;

        // Final post-PA base state. Identity comes from the backend (`bases_detail`); a legacy
        // occupancy-only sim degrades to per-slot fades (no split beats either — the snapshots
        // that drive them are absent).
        let finalBases: Record<BaseSlot, PlayerRef | null>;
        let hasDetail: boolean;
        if (entry.bases_detail !== undefined) {
            hasDetail = true;
            finalBases = mapDetailBases(entry.bases_detail);
        } else {
            hasDetail = false;
            hasRunnerIdentity = false;
            finalBases = parseSimBases(entry.bases);
        }

        const scoredWhere = (pred: (r: SimRunnerRefJson) => boolean): PlayerRef[] =>
            (entry.scored ?? []).filter(pred).map(toPlayerRef);
        const retiredWhere = (reasons: string[]): RetiredRunner[] =>
            (entry.retired ?? []).filter((r) => reasons.includes(r.reason ?? "")).map(toRetiredRunner);

        // Split the plate appearance into up to three beats: the pre-pitch steal, the swing
        // result, then the post-hit extra-base send — each animated on its own, rather than one
        // transition where a steal plays on top of the hit. The two intermediate base snapshots
        // are only present when that phase actually moved someone (see the backend), so a plain
        // PA collapses back to the single result beat below.
        const canSplit = hasDetail && !swingIsEmpty;
        const stealSnap = canSplit ? entry.bases_after_steal ?? null : null;
        const swingSnap = canSplit ? entry.bases_after_swing ?? null : null;

        const advanceScored = scoredWhere((r) => r.reason === "advance");
        const advanceRuns = advanceScored.length;
        const advanceOuts = retiredWhere(["advance"]).length;
        const swingRuns = Math.max(0, runsScored - advanceRuns);
        // Batting-side cumulative score after the swing but before any extra-base send scores.
        const awayAfterSwing = isTop ? entry.away_score - advanceRuns : entry.away_score;
        const homeAfterSwing = isTop ? entry.home_score : entry.home_score - advanceRuns;

        const playEntry: PlayEntry = {
            id: `sim-${i}`,
            inning, isTop,
            batterId: entry.hitter_id || undefined,
            batterName: entry.hitter,
            pitcherId: entry.pitcher_id || undefined,
            pitcherName: entry.pitcher,
            event: entry.event || SIM_EVENT_LABELS[entry.swing_result] || entry.swing_result.toUpperCase(),
            description: entry.description || entry.summary || entry.detail || "",
            isScoringPlay: runsScored > 0,
            outs: entry.outs,
            source: "SIM",
            roll: {
                pitchRoll: entry.pitch_roll, pitchResult: entry.pitch_result,
                swingRoll: entry.swing_roll, swingResult: entry.swing_result,
            },
        };

        type SimLeg = {
            id: string;
            bases: Record<BaseSlot, PlayerRef | null>;
            scored: PlayerRef[];
            retired: RetiredRunner[];
            /** Only the swing beat carries a `play` — steal/advance beats animate without adding
             *  a play-by-play row (`GameDetailPlayback` filters on `frame.play`). */
            play?: PlayEntry;
            /** Batter identity fed to `buildRunnerMoves` — only the swing beat resolves a batter. */
            moveBatter?: PlayerRef;
            /** Who stands in the box on this frame. The steal beat keeps the current hitter there;
             *  the swing/advance beats use the offset next hitter, as every frame does today. */
            standingBatter?: PlayerRef;
            pitcher?: PlayerRef;
            outs: number;
            away: number;
            home: number;
            runs: number;
            isHomeRun: boolean;
        };

        const legs: SimLeg[] = [];

        if (stealSnap != null) {
            const stealRetired = retiredWhere(["steal"]);
            legs.push({
                id: `sim-${i}-steal`,
                bases: mapDetailBases(stealSnap),
                scored: [],
                retired: stealRetired,
                standingBatter: entryBatter,
                pitcher: entryPitcher,
                outs: outsStart + stealRetired.length,
                away: isTop ? entry.away_score - runsScored : entry.away_score,
                home: isTop ? entry.home_score : entry.home_score - runsScored,
                runs: 0,
                isHomeRun: false,
            });
        }

        const hasAdvanceLeg = swingSnap != null;
        legs.push({
            id: `sim-${i}`,
            bases: hasAdvanceLeg ? mapDetailBases(swingSnap) : finalBases,
            scored: swingIsEmpty ? (entry.scored ?? []).map(toPlayerRef) : scoredWhere((r) => (r.reason ?? "") !== "advance"),
            retired: swingIsEmpty ? (entry.retired ?? []).map(toRetiredRunner) : retiredWhere(["forced", ""]),
            play: playEntry,
            moveBatter: entryBatter,
            standingBatter: nextBatter,
            pitcher: nextPitcher,
            outs: hasAdvanceLeg ? entry.outs - advanceOuts : entry.outs,
            away: hasAdvanceLeg ? awayAfterSwing : entry.away_score,
            home: hasAdvanceLeg ? homeAfterSwing : entry.home_score,
            runs: hasAdvanceLeg ? swingRuns : runsScored,
            isHomeRun,
        });

        if (hasAdvanceLeg) {
            legs.push({
                id: `sim-${i}-adv`,
                bases: finalBases,
                scored: advanceScored,
                retired: retiredWhere(["advance"]),
                standingBatter: nextBatter,
                pitcher: nextPitcher,
                outs: entry.outs,
                away: entry.away_score,
                home: entry.home_score,
                runs: advanceRuns,
                isHomeRun: false,
            });
        }

        let legCursor = prevBases;
        for (let li = 0; li < legs.length; li++) {
            const leg = legs[li];
            const isLastLeg = li === legs.length - 1;
            // Fold runs into the linescore beat by beat: the swing beat gets what scored on the
            // swing, the extra-base-send beat gets what scored going the extra base. An earlier
            // steal beat still shows the pre-PA linescore (no apply).
            if (leg.play || (isLastLeg && hasAdvanceLeg)) {
                accumulator.apply(inning, isTop, leg.away, leg.home, leg.play ? isHit : false);
            }

            const moves = buildRunnerMoves({
                prevBases: legCursor, nextBases: leg.bases, scored: leg.scored, retired: leg.retired, batter: leg.moveBatter,
            });
            const legKind: FramePhaseKind = isLastEntry && isLastLeg ? "FINAL" : "PLAY";
            const severity = severityFor({
                moves, runsScored: leg.runs, isHomeRun: leg.isHomeRun,
                isWalkOff: !nextEntry && isLastLeg && runsScored > 0,
            });

            frames.push({
                id: leg.id,
                index: frames.length,
                kind: legKind,
                source: "SIM",
                play: leg.play,
                runners: { bases: leg.bases, scored: leg.scored, retired: leg.retired, batter: leg.standingBatter },
                transition: {
                    fromIndex: frames.length - 1, toIndex: frames.length,
                    moves, runsScored: leg.runs, outsRecorded: leg.outs,
                    isHalfInningChange: isLastLeg && isHalfInningChange, severity,
                },
                view: baseView({
                    state: legKind === "FINAL" ? "FINAL" : "LIVE",
                    away: { ...view.away, score: leg.away, isWinner: legKind === "FINAL" ? view.away.isWinner : undefined },
                    home: { ...view.home, score: leg.home, isWinner: legKind === "FINAL" ? view.home.isWinner : undefined },
                    linescore: accumulator.snapshot(),
                    situation: {
                        inning, isTop, inningLabel: ordinal(inning), outs: leg.outs,
                        bases: leg.bases, batter: leg.standingBatter, pitcher: leg.pitcher,
                    },
                    lastPlay: legKind === "FINAL" ? view.lastPlay : undefined,
                }),
            });
            legCursor = leg.bases;
        }

        if (isHalfInningChange && nextEntry) {
            const breakInning = nextEntry.inning;
            const breakIsTop = nextEntry.is_top;
            accumulator.startHalf(breakInning, breakIsTop);
            frames.push({
                id: `sim-${i}-break`,
                index: frames.length,
                kind: "HALF_INNING_BREAK",
                source: "SIM",
                runners: { bases: EMPTY_BASES, scored: [], retired: [], batter: nextBatter },
                transition: {
                    fromIndex: frames.length - 1, toIndex: frames.length,
                    moves: strandedRunnerMoves(finalBases), runsScored: 0, outsRecorded: 0,
                    isHalfInningChange: true, severity: "quiet",
                    halfInningBreak: { fromInning: inning, fromIsTop: isTop, toInning: breakInning, toIsTop: breakIsTop },
                },
                view: baseView({
                    state: "LIVE",
                    away: { ...view.away, score: entry.away_score, isWinner: undefined },
                    home: { ...view.home, score: entry.home_score, isWinner: undefined },
                    linescore: accumulator.snapshot(),
                    situation: {
                        inning: breakInning, isTop: breakIsTop, inningLabel: ordinal(breakInning), outs: 0,
                        bases: EMPTY_BASES, batter: nextBatter, pitcher: nextPitcher,
                    },
                }),
            });
            prevBases = EMPTY_BASES;
            carryOuts = 0;
        } else {
            prevBases = finalBases;
            carryOuts = entry.outs;
        }
    }

    return {
        gameId: result.game_pk,
        source: "SIM",
        frames,
        liveIndex: frames.length - 1,
        hasRunnerIdentity,
        frozen: { boxscore: true, defense: true },
    };
};
