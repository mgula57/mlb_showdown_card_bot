/**
 * @fileoverview `userTeams.Team` is already the canonical roster on both sides of this app —
 * `fetchShowdownTeam` returns it for a real MLB/WBC roster, persisted user teams round-trip it,
 * and the sim's `SimTeam.from_builder_team` consumes the same shape for tournament mode. This
 * file does not invent a new roster type; it just gives that type a domain-facing name and a
 * `TeamIdentity` projection so a roster and an MLB team can render through the same `TeamChip`.
 */
import type { Team } from "../api/userTeams";
import type { TeamIdentity } from "./team";

export type RosterView = Team;

export const toTeamIdentity = (team: RosterView): TeamIdentity => ({
    key: team.team_id,
    id: team.team_id,
    abbreviation: team.abbreviation,
    name: team.name,
    primaryColor: team.primary_color,
    secondaryColor: team.secondary_color,
});

const LINEUP_SLOTS = 9;

/**
 * roster_size may exceed the fixed minimums (9 lineup + num_starters + min_bench +
 * min_bullpen); autofill fills that slack as extra bench/bullpen spots, split in the same
 * ratio as their configured minimums. Mirrors `_split_extra_roster_slots` in
 * mlb_showdown_bot/core/card/team_builder/autofill.py — keep the two in sync.
 */
export function effectiveBenchBullpenMinimums(team: {
    roster_size: number;
    num_starters: number;
    min_bench: number;
    min_bullpen: number;
}): { bench: number; bullpen: number } {
    const baseMin = LINEUP_SLOTS + team.num_starters + team.min_bench + team.min_bullpen;
    const extra = Math.max(0, team.roster_size - baseMin);
    if (extra === 0) return { bench: team.min_bench, bullpen: team.min_bullpen };

    const total = team.min_bench + team.min_bullpen;
    const bullpenExtra = total > 0
        ? Math.min(extra, Math.round((extra * team.min_bullpen) / total))
        : Math.floor(extra / 2);
    const benchExtra = extra - bullpenExtra;

    return { bench: team.min_bench + benchExtra, bullpen: team.min_bullpen + bullpenExtra };
}
