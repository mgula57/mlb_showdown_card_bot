import type { ChallengeInstance } from '../../../api/sim';

/** `beat_team_record`'s `target_abbr` when it's a `BeatTarget` sentinel rather than a real club
 *  abbr - that club isn't known until the season is actually played, so the card can't name it
 *  ahead of time the way a fixed-abbr goal can. */
function beatTargetLabel(targetAbbr: string | undefined, year: number): string {
    if (targetAbbr === 'BEST_RECORD') return "that season's best record";
    if (targetAbbr === 'WORST_RECORD') return "that season's worst record";
    return `the ${year} ${targetAbbr ?? '?'}'s record`;
}

/** Plain-English version of a challenge's win condition, e.g. "Win at least 95 games". */
export function challengeGoalLabel(challenge: ChallengeInstance): string {
    switch (challenge.goal_type) {
        case 'made_playoffs': return 'Make the playoffs';
        case 'win_division': return 'Win the division';
        case 'win_pennant': return 'Win the pennant';
        case 'win_world_series': return 'Win the World Series';
        case 'min_wins': return `Win at least ${challenge.goal_value?.min_wins ?? '?'} games`;
        case 'beat_team_record': return `Beat ${beatTargetLabel(challenge.goal_value?.target_abbr, challenge.year)}`;
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
    if (minYear != null && minYear === maxYear) parts.push(String(minYear));
    else if (minYear != null || maxYear != null) parts.push(`${minYear ?? 'Any'}–${maxYear ?? 'Any'}`);
    const organization = pf.organization as string[] | undefined;
    if (organization?.length) parts.push(organization.join('/'));
    const league = pf.league as string[] | undefined;
    if (league?.length) parts.push(league.join('/'));
    parts.push(...hitterFilterLabels(pf));
    const required = (pf.required_players as { bref_id: string; name?: string }[] | undefined) ?? [];
    if (required.length) parts.push(`Must roster ${required.map(p => p.name ?? p.bref_id).join(' & ')}`);
    return parts.length ? parts.join(', ') : null;
}

const FIELDING_GROUP_LABELS: Record<string, string> = { if: 'IF', of: 'OF', ca: 'C' };

const SCOPE_LABELS: Record<string, string> = { hitters: 'Hitters', catchers: 'Catchers' };

/** Labels for the scoped `min_`/`max_` filters (`min_speed_hitters`, `min_fielding_if_hitters`,
 *  `min_chart_hr_hitters`, `max_fielding_ca_catchers`, ...), e.g. "Hitters 18+ SPD". */
function hitterFilterLabels(pf: Record<string, unknown>): string[] {
    const labels: string[] = [];
    for (const [key, value] of Object.entries(pf)) {
        const match = /^(min|max)_(.+)_(hitters|catchers)$/.exec(key);
        if (!match || value == null) continue;
        const [, bound, base, scope] = match;
        const amount = bound === 'min' ? `${value}+` : `≤${value}`;
        let stat: string;
        if (base === 'speed') stat = 'SPD';
        else if (base === 'fielding' || base.startsWith('fielding_')) {
            const group = FIELDING_GROUP_LABELS[base.replace('fielding_', '')];
            stat = group ? `${group} fielding` : 'fielding';
        }
        else if (base.startsWith('chart_')) stat = `${base.replace('chart_', '').toUpperCase()} chart slots`;
        else stat = base.toUpperCase();
        labels.push(`${SCOPE_LABELS[scope]} ${amount} ${stat}`);
    }
    return labels;
}
