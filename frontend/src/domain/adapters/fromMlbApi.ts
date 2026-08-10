/**
 * @fileoverview Adapters from the real-MLB API response shapes (`api/mlbAPI.ts`) into the
 * canonical `domain/` view models. `fromBoxscoreDetail` replaces `GameItem.normalizeGame()` —
 * unlike that adapter, this one is lossless: it keeps the box score instead of discarding it.
 */
import { countryCodeForTeam } from "../../functions/flags";
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
 * covered by MatchupStrip) — this drops incomplete plays and reverses to newest-first. */
export const fromGamePlays = (plays: MostRecentPlay[]): PlayEntry[] => {
    return plays
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
        }))
        .reverse();
};
