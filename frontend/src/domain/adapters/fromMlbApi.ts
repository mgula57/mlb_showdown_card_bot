/**
 * @fileoverview Adapters from the real-MLB API response shapes (`api/mlbAPI.ts`) into the
 * canonical `domain/` view models. `fromBoxscoreDetail` replaces `GameItem.normalizeGame()` —
 * unlike that adapter, this one is lossless: it keeps the box score instead of discarding it.
 */
import { countryCodeForTeam } from "../../functions/flags";
import { ordinal } from "../../functions/formatters";
import type {
    GameBoxscoreDetail,
    GameScheduled,
    GameStatus,
    HistoricalTeam,
    LeaderTeam,
    MostRecentPlay,
    BoxscoreTeamInfo,
    BoxscoreTeamData,
    Team as MlbTeam,
} from "../../api/mlbAPI";
import type {
    BoxscoreBatterLine,
    BoxscorePitcherLine,
    DefenseAlignment,
    GameSide,
    GameState,
    GameView,
    Linescore,
    LiveSituation,
    PlayerRef,
    TeamBoxscore,
} from "../game";
import type { PlayEntry } from "../play";
import type { TeamIdentity } from "../team";
import {
    allocateScoredAndRetired,
    buildRunnerMoves,
    EMPTY_BASES,
    LinescoreAccumulator,
    runnerKey,
    severityFor,
    strandedRunnerMoves,
    type BaseSlot,
    type FramePhaseKind,
    type GameFrame,
    type GameTimeline,
} from "../timeline";

// ------------------------------------------------------------------
// TEAM IDENTITY
// ------------------------------------------------------------------

export const fromMlbTeam = (team: MlbTeam, sportId?: number): TeamIdentity => ({
    key: `${team.id}-${team.season ?? ""}`,
    id: team.id,
    abbreviation: team.abbreviation || team.name,
    name: team.name,
    primaryColor: team.primary_color,
    secondaryColor: team.secondary_color,
    countryCode: sportId != null ? countryCodeForTeam(sportId, team.abbreviation || team.name) : null,
});

export const fromBoxscoreTeamInfo = (team: BoxscoreTeamInfo, sportId?: number): TeamIdentity => ({
    key: String(team.id),
    id: team.id,
    abbreviation: team.abbreviation || team.name,
    name: team.name,
    primaryColor: team.primary_color,
    secondaryColor: team.secondary_color,
    countryCode: sportId != null ? countryCodeForTeam(sportId, team.abbreviation || team.name) : null,
});

export const fromLeaderTeam = (team: LeaderTeam): TeamIdentity => ({
    key: String(team.id ?? team.abbreviation ?? team.name ?? ""),
    id: team.id,
    abbreviation: team.abbreviation || team.name || "",
    name: team.name || team.abbreviation || "",
});

export const fromHistoricalTeam = (team: HistoricalTeam): TeamIdentity => ({
    key: `${team.team_id}-${team.season}`,
    id: team.team_id,
    abbreviation: team.abbreviation,
    name: team.name,
    primaryColor: team.primary_color ?? undefined,
    secondaryColor: team.secondary_color ?? undefined,
});

// ------------------------------------------------------------------
// GAME STATE
// ------------------------------------------------------------------

const deriveGameState = (status?: GameStatus): { state: GameState; detailedState: string } => {
    const codedGameState = status?.coded_game_state;
    const detailedState = status?.detailed_state ?? "";
    const isFinal = codedGameState === "F" || status?.status_code === "F";
    const isNotStarted = codedGameState === "P" || codedGameState === "S";
    const isPostponed = codedGameState === "D";
    const state: GameState = isFinal ? "FINAL" : isPostponed ? "POSTPONED" : isNotStarted ? "PREVIEW" : "LIVE";
    return { state, detailedState };
};

const personRef = (id: number | string | undefined, name: string | undefined): PlayerRef | undefined =>
    name ? { id, name } : undefined;

/** Same as `personRef` but for base slots, where "no runner" is a meaningful value rather than
 * an absent field — `LiveSituation.bases` uses null so occupancy reads as `!!bases.first`. */
const runnerRef = (slot: { id?: number; full_name?: string } | null | undefined): PlayerRef | null =>
    slot?.full_name ? { id: slot.id, name: slot.full_name } : null;

const slotRef = (slot: { id?: number; full_name?: string } | null | undefined): PlayerRef | undefined =>
    slot?.full_name ? { id: slot.id, name: slot.full_name } : undefined;

/** Builds the nine-slot defense, or undefined when no slot is populated (pre-first-pitch). */
const toDefenseAlignment = (
    defense: Partial<Record<keyof DefenseAlignment, { id?: number; full_name?: string } | null>> | undefined,
): DefenseAlignment | undefined => {
    if (!defense) return undefined;
    const alignment: DefenseAlignment = {
        pitcher: slotRef(defense.pitcher),
        catcher: slotRef(defense.catcher),
        first: slotRef(defense.first),
        second: slotRef(defense.second),
        third: slotRef(defense.third),
        shortstop: slotRef(defense.shortstop),
        left: slotRef(defense.left),
        center: slotRef(defense.center),
        right: slotRef(defense.right),
    };
    return Object.values(alignment).some(Boolean) ? alignment : undefined;
};

// ------------------------------------------------------------------
// SCHEDULED GAME (schedule / ticker / game tile)
// ------------------------------------------------------------------

export const fromScheduledGame = (game: GameScheduled, sportId?: number): GameView => {
    const { state, detailedState } = deriveGameState(game.status);
    const awayLine = game.teams?.away;
    const homeLine = game.teams?.home;

    const toSide = (line: typeof awayLine): GameSide => ({
        team: line?.team ? fromMlbTeam(line.team, sportId) : { key: "unknown", abbreviation: "?", name: "Unknown" },
        score: line?.score,
        record: line?.league_record
            ? { wins: line.league_record.wins ?? 0, losses: line.league_record.losses ?? 0 }
            : undefined,
        isWinner: line?.is_winner,
        probablePitcher: personRef(line?.probable_pitcher?.id, line?.probable_pitcher?.full_name),
    });

    const ls = game.linescore;
    const linescore: Linescore | undefined = ls
        ? {
            innings: (ls.innings ?? []).map((inning) => ({
                num: inning.num ?? 0,
                ordinalNum: inning.ordinal_num ?? "",
                awayRuns: inning.away?.runs ?? null,
                homeRuns: inning.home?.runs ?? null,
            })),
            scheduledInnings: ls.scheduled_innings ?? 9,
            away: {
                runs: ls.teams?.away?.runs ?? 0,
                hits: ls.teams?.away?.hits ?? 0,
                errors: ls.teams?.away?.errors ?? 0,
                leftOnBase: ls.teams?.away?.left_on_base,
            },
            home: {
                runs: ls.teams?.home?.runs ?? 0,
                hits: ls.teams?.home?.hits ?? 0,
                errors: ls.teams?.home?.errors ?? 0,
                leftOnBase: ls.teams?.home?.left_on_base,
            },
        }
        : undefined;

    const situation: LiveSituation | undefined = ls?.current_inning != null
        ? {
            inning: ls.current_inning,
            isTop: ls.is_top_inning ?? true,
            inningLabel: ls.current_inning_ordinal ?? String(ls.current_inning),
            outs: ls.outs ?? 0,
            balls: ls.balls,
            strikes: ls.strikes,
            bases: {
                first: runnerRef(ls.offense?.first),
                second: runnerRef(ls.offense?.second),
                third: runnerRef(ls.offense?.third),
            },
            batter: personRef(ls.offense?.batter?.id, ls.offense?.batter?.full_name),
            pitcher: personRef(ls.defense?.pitcher?.id, ls.defense?.pitcher?.full_name),
            onDeck: slotRef(ls.offense?.on_deck),
            inHole: slotRef(ls.offense?.in_hole),
            defense: toDefenseAlignment(ls.defense),
        }
        : undefined;

    return {
        id: game.game_pk,
        source: "MLB",
        date: game.game_date,
        seriesLabel: game.series_description || game.description || undefined,
        state,
        detailedState,
        away: toSide(awayLine),
        home: toSide(homeLine),
        linescore,
        situation,
        decisions: game.decisions
            ? {
                winner: personRef(game.decisions.winner?.id, game.decisions.winner?.full_name),
                loser: personRef(game.decisions.loser?.id, game.decisions.loser?.full_name),
                save: personRef(game.decisions.save?.id, game.decisions.save?.full_name),
            }
            : undefined,
    };
};

// ------------------------------------------------------------------
// BOX SCORE DETAIL (game detail page) — replaces GameItem.normalizeGame()
// ------------------------------------------------------------------

const toBoxscore = (data: BoxscoreTeamData, sportId?: number): TeamBoxscore => ({
    team: fromBoxscoreTeamInfo(data.team, sportId),
    batting: data.batting.map((batter): BoxscoreBatterLine => ({
        id: batter.id,
        name: batter.name,
        position: batter.position,
        battingOrder: Number(batter.batting_order) || 0,
        isSubstitute: batter.is_substitute,
        isInLineup: batter.is_in_lineup,
        atBats: batter.stats.at_bats,
        runs: batter.stats.runs,
        hits: batter.stats.hits,
        homeRuns: batter.stats.home_runs,
        rbi: batter.stats.rbi,
        baseOnBalls: batter.stats.base_on_balls,
        strikeOuts: batter.stats.strike_outs,
        stolenBases: batter.stats.stolen_bases,
        summary: batter.stats.summary,
    })),
    pitching: data.pitching.map((pitcher): BoxscorePitcherLine => ({
        id: pitcher.id,
        name: pitcher.name,
        inningsPitched: pitcher.stats.innings_pitched,
        hits: pitcher.stats.hits,
        runs: pitcher.stats.runs,
        earnedRuns: pitcher.stats.earned_runs,
        baseOnBalls: pitcher.stats.base_on_balls,
        strikeOuts: pitcher.stats.strike_outs,
        homeRuns: pitcher.stats.home_runs,
        battersFaced: pitcher.stats.batters_faced,
        summary: pitcher.stats.summary,
    })),
});

export const fromBoxscoreDetail = (game: GameBoxscoreDetail, sportId?: number): GameView => {
    const { state, detailedState } = deriveGameState(game.status);
    const ls = game.linescore;
    const awayRuns = ls?.teams?.away?.runs;
    const homeRuns = ls?.teams?.home?.runs;
    const awayWins = awayRuns != null && homeRuns != null && awayRuns > homeRuns;
    const homeWins = awayRuns != null && homeRuns != null && homeRuns > awayRuns;

    const linescore: Linescore = {
        innings: (ls?.innings ?? []).map((inning) => ({
            num: inning.num,
            ordinalNum: inning.ordinal_num ?? "",
            awayRuns: inning.away.runs ?? null,
            homeRuns: inning.home.runs ?? null,
        })),
        scheduledInnings: ls?.scheduled_innings ?? 9,
        away: { runs: ls?.teams.away.runs ?? 0, hits: ls?.teams.away.hits ?? 0, errors: ls?.teams.away.errors ?? 0 },
        home: { runs: ls?.teams.home.runs ?? 0, hits: ls?.teams.home.hits ?? 0, errors: ls?.teams.home.errors ?? 0 },
    };

    const situation: LiveSituation | undefined = ls?.current_inning != null
        ? {
            inning: ls.current_inning,
            isTop: ls.is_top_inning ?? true,
            inningLabel: ls.current_inning_ordinal ?? String(ls.current_inning),
            outs: ls.outs ?? 0,
            balls: ls.balls,
            strikes: ls.strikes,
            bases: {
                first: runnerRef(ls.offense?.first),
                second: runnerRef(ls.offense?.second),
                third: runnerRef(ls.offense?.third),
            },
            batter: slotRef(ls.offense?.batter),
            pitcher: slotRef(ls.defense?.pitcher),
            onDeck: slotRef(ls.offense?.on_deck),
            inHole: slotRef(ls.offense?.in_hole),
            defense: toDefenseAlignment(ls.defense),
        }
        : undefined;

    return {
        id: game.game_pk,
        source: "MLB",
        date: game.datetime?.date_time,
        state,
        detailedState,
        away: {
            team: fromBoxscoreTeamInfo(game.teams.away.team, sportId),
            score: awayRuns,
            record: game.teams.away.team.record
                ? { wins: game.teams.away.team.record.wins ?? 0, losses: game.teams.away.team.record.losses ?? 0 }
                : undefined,
            isWinner: awayWins,
            probablePitcher: personRef(game.probable_pitchers?.away?.id, game.probable_pitchers?.away?.full_name),
            boxscore: toBoxscore(game.teams.away, sportId),
        },
        home: {
            team: fromBoxscoreTeamInfo(game.teams.home.team, sportId),
            score: homeRuns,
            record: game.teams.home.team.record
                ? { wins: game.teams.home.team.record.wins ?? 0, losses: game.teams.home.team.record.losses ?? 0 }
                : undefined,
            isWinner: homeWins,
            probablePitcher: personRef(game.probable_pitchers?.home?.id, game.probable_pitchers?.home?.full_name),
            boxscore: toBoxscore(game.teams.home, sportId),
        },
        linescore,
        situation,
        decisions: game.decisions
            ? {
                winner: personRef(game.decisions.winner?.id, game.decisions.winner?.full_name),
                loser: personRef(game.decisions.loser?.id, game.decisions.loser?.full_name),
                save: personRef(game.decisions.save?.id, game.decisions.save?.full_name),
            }
            : undefined,
        lastPlay: game.most_recent_play?.result?.description,
    };
};

// ------------------------------------------------------------------
// PLAY-BY-PLAY LOG
// ------------------------------------------------------------------

/** Feed order is oldest-first and includes the in-progress at-bat (no result yet, already
 * covered by MatchupStrip) — this drops incomplete plays. Chronological order is what the
 * timeline fold below needs; `fromGamePlays` reverses this to the newest-first order the log
 * renders in. Kept as two functions (rather than one that reverses) so there is exactly one place
 * that maps a raw play to a `PlayEntry` — a second mapper here would be a standing invitation for
 * the two to drift apart on some future field. */
export const fromGamePlaysChronological = (plays: MostRecentPlay[]): PlayEntry[] =>
    plays
        .filter((play) => !!play.result?.event)
        .map((play, index): PlayEntry => ({
            id: String(play.about?.atBatIndex ?? index),
            inning: play.about?.inning ?? 0,
            isTop: play.about?.isTopInning ?? play.about?.halfInning === 'top',
            batterId: play.matchup?.batter?.id,
            batterName: play.matchup?.batter?.fullName ?? 'Unknown',
            pitcherId: play.matchup?.pitcher?.id,
            pitcherName: play.matchup?.pitcher?.fullName ?? 'Unknown',
            event: play.result?.event ?? '',
            description: play.result?.description ?? '',
            isScoringPlay: play.about?.isScoringPlay,
            outs: play.count?.outs,
            source: "MLB",
        }));

export const fromGamePlays = (plays: MostRecentPlay[]): PlayEntry[] =>
    [...fromGamePlaysChronological(plays)].reverse();

// ------------------------------------------------------------------
// TIMELINE (playback) — one GameFrame per play, each holding a complete GameView.
// ------------------------------------------------------------------

const matchupRef = (person?: { id: number; fullName?: string } | null): PlayerRef | undefined =>
    person ? { id: person.id, name: person.fullName ?? "" } : undefined;

const postOnRef = (person?: { id: number; fullName?: string } | null): PlayerRef | null =>
    person ? { id: person.id, name: person.fullName ?? "" } : null;

/** Bases the plate result itself awards — feeds `allocateScoredAndRetired`'s "attempted one base
 *  beyond standard" heuristic for a runner who didn't score or stay on base. 0 (the default for
 *  every out) is exactly right for a force play — the attempted base is just the next one over. */
const HIT_BASES: Record<string, number> = { single: 1, double: 2, triple: 3, home_run: 4 };

/**
 * Reconstructs a frame-by-frame `GameTimeline` from the same untrimmed play data
 * `fromBoxscoreDetail` already has — the backend's `_extract_play` passes `result`/`matchup`/
 * `about`/`count` through whole, so `matchup.postOnFirst/Second/Third` (post-play base occupancy
 * WITH identity) and `result.awayScore/homeScore` are already on the wire; this just reads more
 * of what was already there. No backend change needed for real MLB games.
 *
 * The batter shown at each frame's plate is the NEXT play's batter (a two-pass-in-one-loop fold,
 * via `rawPlays[i + 1]`) — see `buildRunnerMoves`'s doc comment for why that offset is what makes
 * the field's batter-runs-to-first animation work.
 */
export const fromMlbTimeline = (game: GameBoxscoreDetail, sportId?: number): GameTimeline => {
    const liveView = fromBoxscoreDetail(game, sportId);
    const rawPlays = (game.plays ?? []).filter((play) => !!play.result?.event);
    const playEntries = fromGamePlaysChronological(game.plays ?? []);
    const isGameFinal = liveView.state === "FINAL";

    const scheduledInnings = liveView.linescore?.scheduledInnings ?? 9;
    const finalErrors = { away: liveView.linescore?.away.errors ?? 0, home: liveView.linescore?.home.errors ?? 0 };
    const accumulator = new LinescoreAccumulator(scheduledInnings, isGameFinal ? finalErrors : { away: 0, home: 0 });

    const baseView = (overrides: Partial<GameView>): GameView => ({ ...liveView, isReplay: true, ...overrides });

    const frames: GameFrame[] = [];
    let prevBases: Record<BaseSlot, PlayerRef | null> = EMPTY_BASES;
    let awayScore = 0;
    let homeScore = 0;
    let inning = rawPlays[0]?.about?.inning ?? 1;
    let isTop = rawPlays[0]?.about?.isTopInning ?? true;

    accumulator.startHalf(inning, isTop);

    // FRAME 0 — pre-game.
    {
        const firstPlay = rawPlays[0];
        const batter = matchupRef(firstPlay?.matchup?.batter);
        const pitcher = matchupRef(firstPlay?.matchup?.pitcher);
        frames.push({
            id: "mlb-pregame",
            index: 0,
            kind: rawPlays.length === 0 ? "FINAL" : "PRE_GAME",
            source: "MLB",
            runners: { bases: EMPTY_BASES, scored: [], retired: [], batter },
            view: baseView({
                state: rawPlays.length === 0 && isGameFinal ? "FINAL" : "LIVE",
                away: { ...liveView.away, score: 0, isWinner: undefined },
                home: { ...liveView.home, score: 0, isWinner: undefined },
                decisions: undefined,
                linescore: accumulator.snapshot(),
                situation: {
                    inning, isTop, inningLabel: ordinal(inning), outs: 0,
                    bases: EMPTY_BASES, batter, pitcher,
                    defense: rawPlays.length === 0 ? liveView.situation?.defense : undefined,
                },
            }),
        });
    }

    for (let i = 0; i < rawPlays.length; i++) {
        const play = rawPlays[i];
        const nextPlay = rawPlays[i + 1];
        inning = play.about?.inning ?? inning;
        isTop = play.about?.isTopInning ?? isTop;
        const outs = play.count?.outs ?? 0;

        const nextBases: Record<BaseSlot, PlayerRef | null> = {
            first: postOnRef(play.matchup?.postOnFirst),
            second: postOnRef(play.matchup?.postOnSecond),
            third: postOnRef(play.matchup?.postOnThird),
        };

        const battingSide: "away" | "home" = isTop ? "away" : "home";
        const newAway = play.result?.awayScore ?? awayScore;
        const newHome = play.result?.homeScore ?? homeScore;
        const battingScoreBefore = battingSide === "away" ? awayScore : homeScore;
        const battingScoreAfter = battingSide === "away" ? newAway : newHome;
        const runsScored = Math.max(0, battingScoreAfter - battingScoreBefore);

        const eventType = (play.result?.eventType ?? "").toLowerCase();
        const isHomeRun = eventType === "home_run" || (play.result?.event ?? "").toLowerCase() === "home run";
        const batter = matchupRef(play.matchup?.batter);

        // Departed base runners: on base before this play, gone afterward — candidates for
        // having scored or been retired (see `allocateScoredAndRetired`'s doc comment).
        const departed = (["first", "second", "third"] as BaseSlot[])
            .filter((slot) => {
                const player = prevBases[slot];
                if (!player) return false;
                const key = runnerKey(player, slot);
                return !(["first", "second", "third"] as BaseSlot[]).some((s) => {
                    const nextPlayer = nextBases[s];
                    return nextPlayer != null && runnerKey(nextPlayer, s) === key;
                });
            })
            .map((slot) => ({ slot, player: prevBases[slot] as PlayerRef }));
        const runsForOthers = isHomeRun ? Math.max(0, runsScored - 1) : runsScored;
        const hitBases = HIT_BASES[eventType] ?? 0;
        const { scored: othersScored, retired } = allocateScoredAndRetired(departed, runsForOthers, hitBases);
        const scored = isHomeRun && batter ? [...othersScored, batter] : othersScored;

        const moves = buildRunnerMoves({ prevBases, nextBases, scored, retired, batter });
        const isHalfInningChange = !!nextPlay && (nextPlay.about?.inning !== inning || nextPlay.about?.isTopInning !== isTop);
        const isHit = ["single", "double", "triple", "home_run"].includes(eventType);

        accumulator.apply(inning, isTop, newAway, newHome, isHit);
        const severity = severityFor({
            moves, runsScored, isHomeRun,
            isWalkOff: isGameFinal && !nextPlay && runsScored > 0,
        });

        const isLastPlay = i === rawPlays.length - 1;
        const kind: FramePhaseKind = isLastPlay && isGameFinal ? "FINAL" : "PLAY";
        const nextBatter = matchupRef(nextPlay?.matchup?.batter);
        const nextPitcher = matchupRef(nextPlay?.matchup?.pitcher) ?? matchupRef(play.matchup?.pitcher);

        frames.push({
            id: `mlb-${play.about?.atBatIndex ?? i}`,
            index: frames.length,
            kind,
            source: "MLB",
            play: playEntries[i],
            runners: { bases: nextBases, scored, retired, batter: nextBatter },
            transition: {
                fromIndex: frames.length - 1, toIndex: frames.length,
                moves, runsScored, outsRecorded: outs, isHalfInningChange, severity,
            },
            view: baseView({
                state: kind === "FINAL" ? "FINAL" : "LIVE",
                away: { ...liveView.away, score: newAway, isWinner: kind === "FINAL" ? liveView.away.isWinner : undefined },
                home: { ...liveView.home, score: newHome, isWinner: kind === "FINAL" ? liveView.home.isWinner : undefined },
                decisions: kind === "FINAL" ? liveView.decisions : undefined,
                linescore: accumulator.snapshot(),
                situation: {
                    inning, isTop, inningLabel: ordinal(inning), outs,
                    balls: play.count?.balls, strikes: play.count?.strikes,
                    bases: nextBases, batter: nextBatter, pitcher: nextPitcher,
                    defense: kind === "FINAL" ? liveView.situation?.defense : undefined,
                },
                lastPlay: kind === "FINAL" ? liveView.lastPlay : undefined,
            }),
        });

        if (isHalfInningChange && nextPlay) {
            const breakInning = nextPlay.about?.inning ?? inning;
            const breakIsTop = nextPlay.about?.isTopInning ?? !isTop;
            accumulator.startHalf(breakInning, breakIsTop);
            frames.push({
                id: `mlb-${play.about?.atBatIndex ?? i}-break`,
                index: frames.length,
                kind: "HALF_INNING_BREAK",
                source: "MLB",
                runners: { bases: EMPTY_BASES, scored: [], retired: [], batter: nextBatter },
                transition: {
                    fromIndex: frames.length - 1, toIndex: frames.length,
                    moves: strandedRunnerMoves(nextBases), runsScored: 0, outsRecorded: 0,
                    isHalfInningChange: true, severity: "quiet",
                },
                view: baseView({
                    state: "LIVE",
                    away: { ...liveView.away, score: newAway, isWinner: undefined },
                    home: { ...liveView.home, score: newHome, isWinner: undefined },
                    decisions: undefined,
                    linescore: accumulator.snapshot(),
                    situation: {
                        inning: breakInning, isTop: breakIsTop, inningLabel: ordinal(breakInning), outs: 0,
                        bases: EMPTY_BASES, batter: nextBatter, pitcher: nextPitcher,
                    },
                }),
            });
            prevBases = EMPTY_BASES;
            inning = breakInning;
            isTop = breakIsTop;
        } else {
            prevBases = nextBases;
        }

        awayScore = newAway;
        homeScore = newHome;
    }

    // Trailing AT_BAT frame for a game still in progress — the live ground truth, verbatim, so
    // the live edge can never regress versus what the page shows today.
    if (!isGameFinal) {
        frames.push({
            id: "mlb-live",
            index: frames.length,
            kind: "AT_BAT",
            source: "MLB",
            runners: {
                bases: {
                    first: liveView.situation?.bases.first ?? null,
                    second: liveView.situation?.bases.second ?? null,
                    third: liveView.situation?.bases.third ?? null,
                },
                scored: [],
                retired: [],
                batter: liveView.situation?.batter,
            },
            view: liveView,
        });
    }

    return {
        gameId: game.game_pk,
        source: "MLB",
        frames,
        liveIndex: frames.length - 1,
        hasRunnerIdentity: true,
        frozen: { boxscore: true, defense: true },
    };
};
