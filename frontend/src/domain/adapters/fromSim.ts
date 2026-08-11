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
};

export type SimRunnerRefJson = { id: string; name: string; base: number };

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

    for (let i = 0; i < log.length; i++) {
        const entry = log[i];
        const nextEntry = log[i + 1];
        inning = entry.inning;
        isTop = entry.is_top;
        const outs = entry.outs;

        let nextBases: Record<BaseSlot, PlayerRef | null>;
        let scored: PlayerRef[];
        let retired: RetiredRunner[];
        if (entry.bases_detail !== undefined) {
            const detailed: Record<BaseSlot, PlayerRef | null> = { ...EMPTY_BASES };
            for (const r of entry.bases_detail) {
                const slot = baseSlotFor(r.base);
                if (slot) detailed[slot] = toPlayerRef(r);
            }
            nextBases = detailed;
            scored = (entry.scored ?? []).map(toPlayerRef);
            // `retired[].base` is exact from the backend (unlike MLB's heuristic) — no guessing
            // needed for where a caught-stealing/thrown-out/forced-out sim runner was headed.
            retired = (entry.retired ?? []).map(toRetiredRunner);
        } else {
            // Legacy stored sim — occupancy only, no identity. `runnerKey`'s `anon:${slot}`
            // fallback (inside `buildRunnerMoves`) means these fade in/out per slot rather than
            // sliding, since there's no identity to track a runner across a move.
            hasRunnerIdentity = false;
            nextBases = parseSimBases(entry.bases);
            scored = [];
            retired = [];
        }

        const batter: PlayerRef = { id: entry.hitter_id || undefined, name: entry.hitter };
        const pitcher: PlayerRef = { id: entry.pitcher_id || undefined, name: entry.pitcher };
        const runsScored = entry.runs_scored ?? 0;
        const isHomeRun = entry.swing_result.toLowerCase() === "hr";

        const moves = buildRunnerMoves({ prevBases, nextBases, scored, retired, batter });
        const isHalfInningChange = !!nextEntry && (nextEntry.inning !== inning || nextEntry.is_top !== isTop);
        const isHit = ["1b", "1b+", "2b", "3b", "hr"].includes(entry.swing_result.toLowerCase());

        accumulator.apply(inning, isTop, entry.away_score, entry.home_score, isHit);
        const severity = severityFor({
            moves, runsScored, isHomeRun,
            isWalkOff: !nextEntry && runsScored > 0,
        });

        const isLastEntry = i === log.length - 1;
        const kind: FramePhaseKind = isLastEntry ? "FINAL" : "PLAY";
        const nextBatter: PlayerRef | undefined = nextEntry ? { id: nextEntry.hitter_id || undefined, name: nextEntry.hitter } : undefined;
        const nextPitcher: PlayerRef | undefined = nextEntry ? { id: nextEntry.pitcher_id || undefined, name: nextEntry.pitcher } : pitcher;

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
            outs,
            source: "SIM",
            roll: {
                pitchRoll: entry.pitch_roll, pitchResult: entry.pitch_result,
                swingRoll: entry.swing_roll, swingResult: entry.swing_result,
            },
        };

        frames.push({
            id: `sim-${i}`,
            index: frames.length,
            kind,
            source: "SIM",
            play: playEntry,
            runners: { bases: nextBases, scored, retired, batter: nextBatter },
            transition: {
                fromIndex: frames.length - 1, toIndex: frames.length,
                moves, runsScored, outsRecorded: outs, isHalfInningChange, severity,
            },
            view: baseView({
                state: kind === "FINAL" ? "FINAL" : "LIVE",
                away: { ...view.away, score: entry.away_score, isWinner: kind === "FINAL" ? view.away.isWinner : undefined },
                home: { ...view.home, score: entry.home_score, isWinner: kind === "FINAL" ? view.home.isWinner : undefined },
                linescore: accumulator.snapshot(),
                situation: {
                    inning, isTop, inningLabel: ordinal(inning), outs,
                    bases: nextBases, batter: nextBatter, pitcher: nextPitcher,
                },
                lastPlay: kind === "FINAL" ? view.lastPlay : undefined,
            }),
        });

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
                    moves: strandedRunnerMoves(nextBases), runsScored: 0, outsRecorded: 0,
                    isHalfInningChange: true, severity: "quiet",
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
        } else {
            prevBases = nextBases;
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
