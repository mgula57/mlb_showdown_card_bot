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

/** The small uppercase label above each section on league pages. */
export const SECTION_LABEL_CLASS = 'text-[12px] font-semibold text-(--text-secondary) uppercase tracking-wide';

/** Primary action button (Start Draft, Sim, Join...). */
export const PRIMARY_BUTTON_CLASS =
    'flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-(--secondary) text-[12px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed';

/** Secondary action button. */
export const SECONDARY_BUTTON_CLASS =
    'flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-(--background-tertiary) text-[12px] font-bold text-(--text-primary) hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed';

export const ERROR_BOX_CLASS = 'text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5';

export function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}
