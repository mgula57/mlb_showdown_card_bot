import { useMemo } from 'react';
import type { SeasonSimSummary, SimTeamIdentity } from '../../../api/sim';
import type { Standings as StandingsGroup, TeamRecords } from '../../../api/mlbAPI';

/** Standings.tsx keys teams by numeric id; sim teams only have schedule-key strings, so derive one. */
export function hashId(value: string): number {
    let hash = 0;
    for (let i = 0; i < value.length; i++) {
        hash = (hash * 31 + value.charCodeAt(i)) | 0;
    }
    return hash;
}

/** Reshapes sim standings into the [leagueAbbr, Standings[]][] shape the shared Standings component expects. */
export function useStandingsEntries(summary: SeasonSimSummary): [string, StandingsGroup[]][] {
    return useMemo(() => (
        Object.entries(summary.standings.divisions).map(([division, records]) => {
            const league = records[0]?.league ?? division;
            const teamRecords: TeamRecords[] = records.map(record => ({
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
            }));
            const standing: StandingsGroup = {
                standingsType: 'regularSeason',
                division: { id: hashId(division), name: division },
                team_records: teamRecords,
            };
            return [league, [standing]];
        })
    ), [summary]);
}

/** Resolve a schedule key to its branding. The takeover team's key is the club it replaced. */
export function useIdentity(summary: SeasonSimSummary) {
    return (abbr: string | null): SimTeamIdentity | null => (abbr ? summary.identities[abbr] ?? null : null);
}

export function label(identity: SimTeamIdentity | null, fallback: string): string {
    return identity?.abbreviation ?? fallback;
}
