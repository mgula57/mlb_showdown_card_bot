import type { TeamIdentity } from '../../domain/team';
import type { LeagueSeasonStatus, LeagueTeam } from '../../api/leagues';

/** A league team as the shared `TeamChip` badge expects it. */
export function leagueTeamIdentity(team: Pick<LeagueTeam, 'team_id' | 'abbreviation' | 'name' | 'primary_color' | 'secondary_color'>): TeamIdentity {
    return {
        key: team.team_id,
        id: team.team_id,
        abbreviation: team.abbreviation,
        name: team.name,
        primaryColor: team.primary_color ?? undefined,
        secondaryColor: team.secondary_color ?? undefined,
    };
}

export const SEASON_STATUS_LABEL: Record<LeagueSeasonStatus, string> = {
    drafting: 'Drafting',
    setup: 'Setting lineups',
    regular: 'Regular season',
    postseason: 'Postseason',
    complete: 'Complete',
};

export function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}
