import { useMemo } from 'react';
import type { SeasonSimSummary, SimGameLine, SimStatLine, SimTeamRecord, SimTeamSeason } from '../../../api/sim';

export type ClubSeason = {
    team: SimTeamSeason | null;
    games: SimGameLine[];
    players: SimStatLine[];
};

/** Direct port of `SeasonSummaryBuilder._longest_streaks` (summary.py). */
function longestStreaks(games: SimGameLine[]): [number, number] {
    let bestWin = 0;
    let bestLoss = 0;
    let run = 0;
    let last: boolean | null = null;
    for (const game of games) {
        run = game.is_win === last ? run + 1 : 1;
        last = game.is_win;
        if (game.is_win) bestWin = Math.max(bestWin, run);
        else bestLoss = Math.max(bestLoss, run);
    }
    return [bestWin, bestLoss];
}

/** Direct port of `SeasonSummaryBuilder._build_games`, reading from `season_games` (every game,
 *  once) instead of a per-team list. `opponent_identity` is left null - nothing in this codebase
 *  reads it; identity is resolved separately via `useIdentity(summary)` wherever it's needed. */
function buildGames(summary: SeasonSimSummary, abbr: string): SimGameLine[] {
    const seasonGames = summary.season_games ?? [];
    const [seededWins, seededLosses] = summary.seeded_records?.[abbr] ?? [0, 0];
    let wins = seededWins;
    let losses = seededLosses;
    const lines: SimGameLine[] = [];
    for (const game of seasonGames) {
        const isHome = game.home_team === abbr;
        if (!isHome && game.away_team !== abbr) continue;
        const scored = isHome ? game.home_score : game.away_score;
        const allowed = isHome ? game.away_score : game.home_score;
        const isWin = scored > allowed;
        if (isWin) wins += 1;
        else losses += 1;
        lines.push({
            date: game.date,
            opponent: isHome ? game.away_team : game.home_team,
            opponent_identity: null,
            is_home: isHome,
            runs_scored: scored,
            runs_allowed: allowed,
            is_win: isWin,
            wins,
            losses,
        });
    }
    return lines;
}

/** Direct port of `SeasonSummaryBuilder._find_record` + `_build_team_season`. */
function buildTeam(summary: SeasonSimSummary, abbr: string, games: SimGameLine[]): SimTeamSeason {
    let record: SimTeamRecord | null = null;
    let division: string | null = null;
    let rank: number | null = null;
    let size: number | null = null;
    for (const [divisionName, records] of Object.entries(summary.standings.divisions)) {
        const index = records.findIndex(r => r.name === abbr);
        if (index !== -1) {
            record = records[index];
            division = divisionName;
            rank = index + 1;
            size = records.length;
            break;
        }
    }

    const postseasonTeams = new Set(summary.postseason.flatMap(series => [series.home_team, series.away_team]));
    const [longestWinStreak, longestLosingStreak] = longestStreaks(games);

    if (!record) {
        return {
            identity: null, replaced_abbr: abbr, wins: 0, losses: 0, win_pct: 0, points: 0,
            division: null, division_rank: null, division_size: null, games_back: null, playoff_seeding: null,
            made_playoffs: false, is_champion: false,
            longest_win_streak: longestWinStreak, longest_losing_streak: longestLosingStreak,
        };
    }

    return {
        identity: record.identity,
        replaced_abbr: abbr,
        wins: record.wins,
        losses: record.losses,
        win_pct: record.win_pct,
        points: record.points,
        division,
        division_rank: rank,
        division_size: size,
        games_back: record.games_back,
        playoff_seeding: record.playoff_seeding,
        made_playoffs: postseasonTeams.has(abbr),
        is_champion: summary.champion === abbr,
        longest_win_streak: longestWinStreak,
        longest_losing_streak: longestLosingStreak,
    };
}

/**
 * Derives one club's team/games/players from an open-sim summary, entirely client-side — the
 * summary already covers every club, so switching the focus club never needs a refetch.
 *
 * Falls back to the summary's own team-scoped fields (`team`/`games`/`players`) whenever this
 * isn't an open sim (`season_games` is empty or absent) — a takeover/challenge run, where
 * `players` is already filtered by roster card_id rather than by team and must not be re-derived.
 */
export function useClubSeason(summary: SeasonSimSummary, abbr: string): ClubSeason {
    return useMemo(() => {
        const seasonGames = summary.season_games ?? [];
        if (seasonGames.length === 0) {
            return { team: summary.team, games: summary.games, players: summary.players };
        }
        const games = buildGames(summary, abbr);
        const team = buildTeam(summary, abbr, games);
        const players = summary.players.filter(player => player.team === abbr);
        return { team, games, players };
    }, [summary, abbr]);
}
