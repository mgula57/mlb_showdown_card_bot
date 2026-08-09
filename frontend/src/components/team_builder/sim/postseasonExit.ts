import type { SeasonSimSummary } from '../../../api/sim';
import { roundLabel } from './roundLabel';

// Mirrors PostseasonRound in models.py (oldest to newest) — same order SimBracket groups by.
const ROUND_ORDER = ['WC', 'DIV', 'CS', 'WS'];

export type PostseasonExit = { round: string; roundLabel: string; opponentAbbr: string };

/**
 * The furthest postseason series the team lost, for the one-line "Lost NLDS to LAD" headline —
 * `null` when they never lost a series (didn't make the playoffs, or won it all).
 */
export function describePostseasonExit(summary: SeasonSimSummary, teamKey: string): PostseasonExit | null {
    if (!teamKey) return null;

    const losses = summary.postseason.filter(
        s => (s.home_team === teamKey || s.away_team === teamKey) && s.winner != null && s.winner !== teamKey,
    );
    if (losses.length === 0) return null;

    const furthest = losses.reduce((best, s) => (
        ROUND_ORDER.indexOf(s.round) > ROUND_ORDER.indexOf(best.round) ? s : best
    ));
    const opponentKey = furthest.home_team === teamKey ? furthest.away_team : furthest.home_team;

    return {
        round: furthest.round,
        roundLabel: roundLabel(furthest.round, furthest.league),
        opponentAbbr: summary.identities[opponentKey]?.abbreviation ?? opponentKey,
    };
}
