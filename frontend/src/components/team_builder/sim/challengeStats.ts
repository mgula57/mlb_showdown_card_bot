import type { ChallengeInstance } from '../../../api/sim';

/** How many distinct teams have cleared a challenge, out of how many have tried — plus a
 *  rounded percentage for display. Null until at least one team has entered (nothing to
 *  rate), so callers can simply skip the stat. */
export function challengeSuccessRate(challenge: ChallengeInstance): { passes: number; entrants: number; pct: number } | null {
    const entrants = challenge.entrants ?? 0;
    if (entrants <= 0) return null;
    const passes = challenge.passes ?? 0;
    return { passes, entrants, pct: Math.round((passes / entrants) * 100) };
}
