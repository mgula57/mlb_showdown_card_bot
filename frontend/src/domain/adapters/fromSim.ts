/**
 * @fileoverview Adapter from the simulation engine's `GameResult` JSON
 * (`mlb_showdown_bot/core/simulation/models.py`, emitted via Pydantic's `model_dump_json`) into
 * the canonical `GameView`. No UI consumes this yet — it exists to prove the `GameView`
 * abstraction holds for a second source before any sim UI is built. Field names mirror the
 * Python models exactly (snake_case), since that's the wire format.
 */
import type { BoxscoreBatterLine, BoxscorePitcherLine, GameSide, GameView, Linescore, LiveSituation, TeamBoxscore } from "../game";
import type { PlayEntry } from "../play";
import type { TeamIdentity } from "../team";

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
    /** Names only; the sim's log doesn't carry player ids, so sim plays can't resolve cards yet. */
    pitcher: string;
    hitter: string;
    pitch_roll: number;
    pitch_result: string;
    swing_roll: number;
    swing_result: string;
    detail?: string;
    summary: string;
};

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

/** `Result` enum values (`core/simulation/result.py`) as play-log badge labels. */
const SIM_EVENT_LABELS: Record<string, string> = {
    pu: "Popout", so: "Strikeout", gb: "Groundout", fb: "Flyout", bb: "Walk",
    "1b": "Single", "1b+": "Single+", "2b": "Double", "3b": "Triple", hr: "Home Run",
    out: "Out", safe: "Safe",
};

const ORDINAL_SUFFIXES: Record<number, string> = { 1: "st", 2: "nd", 3: "rd" };
const ordinal = (n: number): string => {
    const suffix = n % 100 >= 11 && n % 100 <= 13 ? "th" : ORDINAL_SUFFIXES[n % 10] ?? "th";
    return `${n}${suffix}`;
};

/** The sim reports base state as occupancy, not identity, so occupied bases become the
 * `{ name: "" }` sentinel that `LiveSituation.bases` documents. */
const parseSimBases = (bases: string): LiveSituation["bases"] => {
    const occupied = (index: number) => (bases[index] === "■" ? { name: "" } : null);
    return { third: occupied(0), second: occupied(1), first: occupied(2) };
};

const fromSimTeamIdentity = (identity: SimTeamIdentityJson): TeamIdentity => ({
    key: identity.abbreviation,
    abbreviation: identity.abbreviation,
    name: identity.name || identity.abbreviation,
    primaryColor: identity.primary_color ?? undefined,
    secondaryColor: identity.secondary_color ?? undefined,
});

const fallbackIdentity = (abbreviation: string): TeamIdentity => ({
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
        .map((entry, index): PlayEntry => {
            const previous = log[index - 1];
            const runsBefore = previous ? previous.away_score + previous.home_score : 0;
            return {
                id: String(index),
                inning: entry.inning,
                isTop: entry.is_top,
                batterName: entry.hitter,
                pitcherName: entry.pitcher,
                event: SIM_EVENT_LABELS[entry.swing_result] ?? entry.swing_result.toUpperCase(),
                description: entry.summary || entry.detail || "",
                isScoringPlay: entry.away_score + entry.home_score > runsBefore,
                outs: entry.outs,
                roll: {
                    pitchRoll: entry.pitch_roll,
                    pitchResult: entry.pitch_result,
                    swingRoll: entry.swing_roll,
                    swingResult: entry.swing_result,
                },
            };
        })
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
        lastPlay: lastEntry?.summary,
    };
};
