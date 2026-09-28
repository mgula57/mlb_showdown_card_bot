import type { TeamSummary } from '../../api/userTeams';

/** Matches a team by name/abbreviation or by Showdown set (e.g. "Expanded" matches allowed_sets: ["EXPANDED"]). */
export function matchesTeamQuery(team: TeamSummary, q: string): boolean {
    const needle = q.trim().toLowerCase();
    if (!needle) return true;
    if (team.name.toLowerCase().includes(needle)) return true;
    if (team.abbreviation.toLowerCase().includes(needle)) return true;
    return (team.allowed_sets ?? []).some(set => set.toLowerCase().includes(needle));
}
