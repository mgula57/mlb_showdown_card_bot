import { useEffect, useMemo, useState } from 'react';
import { fetchSimSeasonTeams } from '../../../api/sim';
import type { SeasonSimSummary, SimTeamIdentity, SimTeamRecord, SimTeamSeason, TakeoverClub } from '../../../api/sim';
import type { Standings as StandingsGroup, TeamRecords } from '../../../api/mlbAPI';

/** Standings.tsx keys teams by numeric id; sim teams only have schedule-key strings, so derive one. */
export function hashId(value: string): number {
    let hash = 0;
    for (let i = 0; i < value.length; i++) {
        hash = (hash * 31 + value.charCodeAt(i)) | 0;
    }
    return hash;
}

/** Maps a sim standings record into the shared `TeamRecords` shape Standings.tsx renders. */
function toTeamRecord(summary: SeasonSimSummary, record: SimTeamRecord): TeamRecords {
    return {
        team: {
            id: hashId(record.name),
            name: record.identity?.name ?? record.name,
            abbreviation: record.identity?.abbreviation ?? record.name,
            primary_color: record.identity?.primary_color ?? undefined,
        },
        season: summary.year,
        league_record: { wins: record.wins, losses: record.losses },
        games_back: record.games_back === null ? undefined : String(record.games_back),
        showdown_points: record.points,
    };
}

/** Best record first: win% then wins, matching the sim engine's `(win_pct, wins)` seeding sort. */
function sortByRecord(a: SimTeamRecord, b: SimTeamRecord): number {
    return b.win_pct - a.win_pct || b.wins - a.wins;
}

/** Non-division-winner playoff spots per league for a sim year, mirroring `PostseasonFormat.year_range`
 *  in `core/simulation/models.py`. Used only as a fallback when the summary carries no
 *  `playoff_seeding` (postseason not simulated, or an older persisted summary). */
function wildCardSpotsForYear(year: number): number {
    if (year >= 2022) return 3; // WILDCARD_3
    if (year >= 2012) return 2; // WILDCARD_2 (incl. 2020's simplification)
    if (year >= 1995) return 1; // WILDCARD_1
    return 0;                    // CHAMPIONSHIP_SERIES / WORLD_SERIES eras — no wild card
}

const formatWildCardGb = (halfGames: number): string => {
    if (halfGames <= 0) return '-';
    return Number.isInteger(halfGames) ? String(halfGames) : halfGames.toFixed(1);
};

/** Builds a "Wild Card" standings group per league from the sim's division standings: every
 *  non-division-winner ranked by record, with a cutoff line after the era-correct number of spots.
 *  Emits nothing for a league in an era / format with no wild card, or with fewer than two divisions. */
function buildWildCardEntries(summary: SeasonSimSummary): [string, StandingsGroup[]][] {
    const flat: { record: SimTeamRecord; divisionKey: string }[] = [];
    for (const [divisionKey, records] of Object.entries(summary.standings.divisions)) {
        for (const record of records) flat.push({ record, divisionKey });
    }
    if (flat.length === 0) return [];

    const hasSeeding = flat.some(({ record }) => record.playoff_seeding != null);

    const leagues = new Map<string, typeof flat>();
    for (const item of flat) {
        const league = item.record.league ?? item.divisionKey;
        const bucket = leagues.get(league) ?? [];
        bucket.push(item);
        leagues.set(league, bucket);
    }

    const entries: [string, StandingsGroup[]][] = [];
    for (const [league, items] of leagues) {
        const divisionKeys = new Set(items.map(i => i.divisionKey));
        if (divisionKeys.size < 2) continue; // wild card is meaningless with one division

        // Division winners: best record in each division key.
        const winners = new Set<SimTeamRecord>();
        for (const key of divisionKeys) {
            const leader = items
                .filter(i => i.divisionKey === key)
                .map(i => i.record)
                .sort(sortByRecord)[0];
            if (leader) winners.add(leader);
        }

        const contenders = items
            .map(i => i.record)
            .filter(r => !winners.has(r))
            .sort(sortByRecord);
        if (contenders.length === 0) continue;

        let cut = hasSeeding
            ? contenders.filter(r => r.playoff_seeding != null).length
            : wildCardSpotsForYear(summary.year);
        cut = Math.min(cut, contenders.length);
        if (cut === 0) continue; // eras / formats with no wild card

        const lead = contenders[0];
        const teamRecords: TeamRecords[] = contenders.map(record => ({
            ...toTeamRecord(summary, record),
            // Stored games_back is the division deficit — recompute it against the top wild card.
            games_back: formatWildCardGb(((lead.wins - record.wins) + (record.losses - lead.losses)) / 2),
        }));

        entries.push([league, [{
            standingsType: 'wildCard',
            division: { id: hashId(`${league}-wc`), name: `${league} Wild Card` },
            team_records: teamRecords,
            wildCardCutLine: cut,
        }]]);
    }
    return entries;
}

/** Reshapes sim standings into the [leagueAbbr, Standings[]][] shape the shared Standings component
 *  expects: every division card first, then both leagues' wild-card cards. */
export function useStandingsEntries(summary: SeasonSimSummary): [string, StandingsGroup[]][] {
    return useMemo(() => {
        const divisionEntries: [string, StandingsGroup[]][] = Object.entries(summary.standings.divisions).map(([division, records]) => {
            const league = records[0]?.league ?? division;
            const standing: StandingsGroup = {
                standingsType: 'regularSeason',
                division: { id: hashId(division), name: division },
                team_records: records.map(record => toTeamRecord(summary, record)),
            };
            return [league, [standing]];
        });

        return [...divisionEntries, ...buildWildCardEntries(summary)];
    }, [summary]);
}

/** Resolve a schedule key to its branding. The takeover team's key is the club it replaced. */
export function useIdentity(summary: SeasonSimSummary) {
    return (abbr: string | null): SimTeamIdentity | null => (abbr ? summary.identities[abbr] ?? null : null);
}

export function label(identity: SimTeamIdentity | null, fallback: string): string {
    return identity?.abbreviation ?? fallback;
}

/**
 * A team's wins-per-roster-point indexed against the league average for the season, in the same
 * "100 = average" style as OPS+/ERA+: 100 means the team won at the league's typical rate for
 * what it spent, >100 means it won more per point than average (spent wisely), <100 means it took
 * more points per win than average. Every division's `TeamRecord.points` already carries the
 * built roster's point cost (bench-multiplier-adjusted), so the league baseline needs no extra
 * data beyond what the standings already report. Null when there's no meaningful baseline (e.g.
 * a season with no roster point costs at all).
 *
 * Takes the resolved focus team explicitly rather than reading `summary.team` - that field is
 * null for an open sim, where the caller resolves a team via `useClubSeason` first.
 */
export function computePtsEfficiency(summary: SeasonSimSummary, team: SimTeamSeason | null): number | null {
    if (!team || team.points <= 0) return null;

    let leagueWins = 0;
    let leaguePoints = 0;
    for (const records of Object.values(summary.standings.divisions)) {
        for (const record of records) {
            leagueWins += record.wins;
            leaguePoints += record.points;
        }
    }
    if (leaguePoints <= 0) return null;

    const leagueRate = leagueWins / leaguePoints;
    if (leagueRate <= 0) return null;

    const teamRate = team.wins / team.points;
    return Math.round((teamRate / leagueRate) * 100);
}

export type RecordComparisonEntry = {
    abbr: string;
    identity: SimTeamIdentity | null;
    simWins: number;
    simLosses: number;
    realWins: number;
    realLosses: number;
    /** Sim win% minus real win% - positive means the sim team won more than it actually did that year. */
    diff: number;
};

const RECORD_COMPARISON_LIMIT = 5;

function realWinPct(club: TakeoverClub): number {
    const games = club.wins + club.losses;
    return games > 0 ? club.wins / games : 0;
}

/**
 * Joins each division's sim standings against that year's real MLB records - fetched the same way
 * the pre-sim club picker does, via `fetchSimSeasonTeams` - to surface the clubs whose simulated
 * record diverged most from what actually happened. The team-level counterpart to
 * `summary.outliers`'s player-level OPS surprises. `SimTeamRecord.name` and
 * `TakeoverClub.abbreviation` are both built from the backend's `normalized_team_abbr` helper, so
 * a plain string join is safe.
 */
export function useRecordComparison(summary: SeasonSimSummary): { overperformers: RecordComparisonEntry[]; underperformers: RecordComparisonEntry[]; loading: boolean } {
    const [clubs, setClubs] = useState<TakeoverClub[] | null>(null);

    useEffect(() => {
        let cancelled = false;
        fetchSimSeasonTeams(summary.year)
            .then(({ teams }) => { if (!cancelled) setClubs(teams); })
            .catch(() => { if (!cancelled) setClubs([]); });
        return () => { cancelled = true; };
    }, [summary.year]);

    return useMemo(() => {
        if (clubs === null) return { overperformers: [], underperformers: [], loading: true };
        if (clubs.length === 0) return { overperformers: [], underperformers: [], loading: false };

        const realByAbbr = new Map(clubs.map(club => [club.abbreviation, club]));
        const entries: RecordComparisonEntry[] = [];
        for (const records of Object.values(summary.standings.divisions)) {
            for (const record of records) {
                const real = realByAbbr.get(record.name);
                if (!real) continue;
                entries.push({
                    abbr: record.name,
                    identity: record.identity,
                    simWins: record.wins,
                    simLosses: record.losses,
                    realWins: real.wins,
                    realLosses: real.losses,
                    diff: record.win_pct - realWinPct(real),
                });
            }
        }

        const overperformers = entries.filter(e => e.diff > 0).sort((a, b) => b.diff - a.diff).slice(0, RECORD_COMPARISON_LIMIT);
        const underperformers = entries.filter(e => e.diff < 0).sort((a, b) => a.diff - b.diff).slice(0, RECORD_COMPARISON_LIMIT);
        return { overperformers, underperformers, loading: false };
    }, [summary.standings.divisions, clubs]);
}
