import type { ChallengeInstance } from '../../../api/sim';

/** Plain-English version of a challenge's win condition, e.g. "Win at least 95 games". */
export function challengeGoalLabel(challenge: ChallengeInstance): string {
    switch (challenge.goal_type) {
        case 'made_playoffs': return 'Make the playoffs';
        case 'win_division': return 'Win the division';
        case 'win_pennant': return 'Win the pennant';
        case 'win_world_series': return 'Win the World Series';
        case 'min_wins': return `Win at least ${challenge.goal_value?.min_wins ?? '?'} games`;
        case 'beat_team_record': return `Beat the ${challenge.year} ${challenge.goal_value?.target_abbr ?? '?'}'s record`;
        default: return 'Clear the bar';
    }
}

/** Whole days until a challenge instance rotates out, floored at 0. */
export function challengeDaysLeft(challenge: ChallengeInstance): number {
    return Math.max(0, Math.ceil((new Date(challenge.expires_at).getTime() - Date.now()) / 86_400_000));
}

/** Short human-readable summary of a challenge's player_filters, e.g. "NYM/NYY, L bats,
 *  1990–2000" — null when the challenge has no player restrictions. */
export function challengeRestrictionsLabel(challenge: ChallengeInstance): string | null {
    const pf = challenge.player_filters;
    if (!pf) return null;
    const parts: string[] = [];
    const team = pf.team as string[] | undefined;
    if (team?.length) parts.push(team.join('/'));
    const hand = pf.hand as string[] | undefined;
    if (hand?.length) parts.push(`${hand.join('/')} bats`);
    const minYear = pf.min_year as number | undefined;
    const maxYear = pf.max_year as number | undefined;
    if (minYear != null || maxYear != null) parts.push(`${minYear ?? 'Any'}–${maxYear ?? 'Any'}`);
    const organization = pf.organization as string[] | undefined;
    if (organization?.length) parts.push(organization.join('/'));
    const league = pf.league as string[] | undefined;
    if (league?.length) parts.push(league.join('/'));
    return parts.length ? parts.join(', ') : null;
}
